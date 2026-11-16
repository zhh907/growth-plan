"""
    0010 llm-as-judge : 用模型给 evidence 打分,对照人评校准

    实验问题:judge 会不会自发核对引用行号(素材 E2 混入了无关行号)?
    prompt 故意不说"请核对行号" —— 测自发查证行为。
    素材来自 0009 case_b 的三次真实运行输出。
    退出码:0=完成,2=流程失败。
"""

import json
import os
import sys

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(
    base_url=os.environ["ANTHROPIC_BASE_URL"],
    auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"],
)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

JUDGE_PROMPT = """
    You are grading the quality of code-review evidence.
    You will receive a Python file and three pieces of evidence (E1, E2, E3).
    Each piece tries to refute an auditor's claim:
    "transfer() does not validate that amount is positive."

    Before scoring, list what EACH cited line actually contains in the file.
For each cited line answer yes/no: does this line itself help refute the claim?
A score above 3 requires EVERY cited line to be yes.

    
    Grade each piece 1-5:
    5 = conclusion correct, cited lines accurate and relevant, covers guard definition and call site
    3 = conclusion correct but cited lines partially wrong/incomplete, or coverage clearly thin
    1 = cited lines mostly wrong or describe logic not in the file

    Submit ONLY via the submit_grades tool. Free text is not accepted.
"""

GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "grades": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "enum": ["E1", "E2", "E3"]},
                    "score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "reasoning": {"type": "string"},
                },
                "required": ["id", "score", "reasoning"],
            },
        },
    },
    "required": ["grades"],
}

TOOLS = [{
    "name": "submit_grades",
    "description": "Submit grades for the three pieces of evidence.",
    "input_schema": GRADE_SCHEMA,
}]
TOOL_CHOICE = {"type": "tool", "name": "submit_grades"}

# 素材:0009 case_b 的三次真实输出(行号原样保留,包括错的)
EVIDENCES = [
    {"id": "E1", "lines": [21, 9, 10, 11, 12, 13, 14, 15],
     "text": "Line 21 calls validate_amount(amount) unconditionally at the start of transfer(). "
             "validate_amount (lines 8-16) raises TypeError for non-numeric input, ValueError if "
             "amount < MIN_AMOUNT (0.01, line 10-11), and ValueError if amount > MAX_AMOUNT."},
    {"id": "E2", "lines": [21, 23, 6, 10],
     "text": "Line 21 in transfer() calls validate_amount(amount). validate_amount (lines 6-15) "
             "raises ValueError if amount < MIN_AMOUNT (0.01, line 10), so positivity/minimum "
             "validation exists and is enforced in the transfer path."},
    {"id": "E3", "lines": [21],
     "text": "Line 21 of transfer() calls validate_amount(amount), which (lines 10-18) raises "
             "TypeError for non-numeric input, ValueError for amount < MIN_AMOUNT (0.01) and for "
             "amount > MAX_AMOUNT. Thus positivity/range validation is present."},
]

# 人评基准(导师标注):E2 引用了 23(余额检查,无关)和 6(常量定义,沾边)—— 行号真实存在但相关度差
HUMAN_BASELINE = {"E1": 4, "E2": 2, "E3": 3}


def validate_grades(payload) -> tuple[dict | None, str | None]:
    """确定性校验:三条、id 齐、分数 1-5。"""
    if not isinstance(payload, dict):
        return None, "payload is not an object"
    grades = payload.get("grades")
    if not isinstance(grades, list) or len(grades) != 3:
        return None, "grades must be a list of 3"
    out = {}
    for g in grades:
        if not isinstance(g, dict) or set(g) != {"id", "score", "reasoning"}:
            return None, f"bad grade entry: {g!r}"
        if g["id"] not in ("E1", "E2", "E3"):
            return None, f"bad id: {g['id']!r}"
        if not isinstance(g["score"], int) or not (1 <= g["score"] <= 5):
            return None, f"score out of range: {g['id']}={g['score']!r}"
        out[g["id"]] = g
    return out, None


def read_file(path: str) -> str:
    with open(os.path.join(SCRIPT_DIR, path), "r", encoding="utf-8") as f:
        return f.read()


def main():
    file_text = read_file("fixtures/case_b.py")
    evidences_block = json.dumps(EVIDENCES, ensure_ascii=False, indent=2)

    messages = [{
        "role": "user",
        "content": f"=== FILE ===\n{file_text}\n\n=== EVIDENCES ===\n{evidences_block}",
    }]

    total_in = total_out = 0
    for attempt in range(1, 3):                     # 首次 + 1 次重试
        resp = client.messages.create(
            model="deepseek-chat",
            system=[{"type": "text", "text": JUDGE_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            max_tokens=2000,
            messages=messages,
            tools=TOOLS,
            tool_choice=TOOL_CHOICE,
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens

        tool_block = next((b for b in resp.content if b.type == "tool_use"), None)
        if tool_block is None:
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": "Call submit_grades."})
            continue

        grades, err = validate_grades(tool_block.input)
        if err is None:
            print(f"{'素材':<6}{'judge 分':<10}{'人评':<6}理由")
            for eid in ("E1", "E2", "E3"):
                g = grades[eid]
                mark = "一致" if g["score"] == HUMAN_BASELINE[eid] else "偏差"
                print(f"{eid:<6}{g['score']:<12}{HUMAN_BASELINE[eid]:<6}{g['reasoning'][:80]}")
                print(f"{'':<6}({mark})")
            print(f"\n总用量: in={total_in} out={total_out}")
            sys.exit(0)

        print(f"校验失败: {err},回喂重试", file=sys.stderr)
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": tool_block.id,
            "content": f"REJECTED: {err}. Call submit_grades again.",
        }]})

    print("流程失败: 两次尝试均未拿到合规裁决", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
