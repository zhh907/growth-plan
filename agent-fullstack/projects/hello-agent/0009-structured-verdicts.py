"""
    0009 structured verdicts : 用强制工具调用替掉字符串解析

    教学目标:程序拿到"机器可校验"的评审裁决,算术权归 Python。
    上游审计员的 findings 是本课刻意模拟的输入,不重建整条流水线。
    退出码:0=干净,1=有真 bug,2=流程失败(拿不到合规裁决)。
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

CRITIC_PROMPT = """
    You are a senior Python code reviewer adjudicating findings from junior auditors.
    You receive the COMPLETE file plus all auditor findings.

    For EACH finding:
    1. Check the cited lines against the actual code.
    2. If the finding claims protective logic is MISSING, search the WHOLE FILE first -
       the guard may live outside the auditor's slice.
    3. Verdict: VERIFIED (real bug) or REFUTED (cite the exact lines that refute it).

    Submit your verdict ONLY by calling the submit_verdict tool. Free text is not accepted.
"""

# ---- 洞1:JSON Schema(形状契约) ----
# 单一真相源:verdict 合法值只在这一处定义,schema 与校验器都引用它。
# (破坏性测试的教训:枚举写两份必然漂移——schema 说合法、校验器说非法)
ALLOWED_VERDICTS = ("VERIFIED", "REFUTED")

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "verdict": {
                        "type": "string",
                        "enum": list(ALLOWED_VERDICTS),   # 枚举:只允许这两个值
                    },
                    "lines": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    "evidence": {"type": "string"},
                },
                "required": ["id", "verdict", "lines", "evidence"],
            },
        },
    },
    "required": ["findings"],
    # 注意:故意没有 survived_count —— 算术权归 Python
}

# ---- 洞2:把 schema 变成强制契约 ----
TOOLS = [
    {
        "name": "submit_verdict",
        "description": "Submit the final adjudication for each auditor finding.",
        "input_schema": VERDICT_SCHEMA,
    },
]
TOOL_CHOICE = {"type": "tool", "name": "submit_verdict"}


def resolve_path(path: str) -> str:
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR, path)
    return path


def read_file(path: str) -> str:
    with open(resolve_path(path), "r", encoding="utf-8") as f:
        return f.read()


def validate_verdict(payload) -> tuple[list | None, str | None]:
    """确定性校验:只查形状,不猜语义。返回 (findings, error)。"""
    if not isinstance(payload, dict):
        return None, f"payload is not an object: {type(payload).__name__}"
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return None, "missing or non-list field: findings"
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            return None, f"findings[{i}] is not an object"
        for key in ("id", "verdict", "lines", "evidence"):
            if key not in f:
                return None, f"findings[{i}] missing key: {key}"
        if f["verdict"] not in ALLOWED_VERDICTS:
            return None, f"findings[{i}].verdict invalid: {f['verdict']!r}"
        if not isinstance(f["lines"], list) or not all(isinstance(n, int) for n in f["lines"]):
            return None, f"findings[{i}].lines must be a list of ints"
    return findings, None


def call_critic(file_text: str, findings_in: list, max_retries: int = 2):
    """评审循环。返回 (findings, total_in, total_out, error)。"""
    findings_block = json.dumps(findings_in, ensure_ascii=False, indent=2)
    messages = [{
        "role": "user",
        "content": (
            f"=== COMPLETE FILE ===\n{file_text}\n\n"
            f"=== AUDITOR FINDINGS ===\n{findings_block}"
        ),
    }]
    total_in = total_out = 0
    last_error = None

    for attempt in range(1, max_retries + 2):          # 首次 + 最多 2 次重试
        resp = client.messages.create(
            model="deepseek-chat",
            system=[{
                "type": "text",
                "text": CRITIC_PROMPT,
                "cache_control":{"type":"ephemeral"}, #标记：这截前缀进缓存
            }],
            max_tokens=2000,
            messages=messages,
            tools=TOOLS,
            tool_choice=TOOL_CHOICE,                   # 洞2 的强制在这里生效
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens
        print(f"----- 第 {attempt} 次尝试: stop={resp.stop_reason} -----")
        print(f"usage: in ={resp.usage.input_tokens},cache_write={resp.usage.cache_creation_input_tokens}, cache_read ={ resp.usage.cache_read_input_tokens} ")
        # ---- 洞3:从响应里取结构化 input ----
        tool_block = next((b for b in resp.content if b.type == "tool_use"), None)

        if tool_block is None:
            # 情况一:模型没用工具(自由文本)→ 直接文本警告喂回
            last_error = f"no tool_use block (stop={resp.stop_reason})"
            print(f"校验失败: {last_error},要求重交", file=sys.stderr)
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content":
                "Free text is not accepted. You MUST answer by calling the submit_verdict tool."})
            continue

        # 情况二:拿到 tool_use,校验 input
        findings, err = validate_verdict(tool_block.input)
        if err is None:
            return findings, total_in, total_out, None

        last_error = err
        print(f"校验失败: {err},错误作为 tool_result 喂回重交", file=sys.stderr)
        # 协议关键点:assistant 已发 tool_use,下一条 user 消息必须以 tool_result 开头,
        # 且 tool_use_id 必须配对 —— 0003 补考三次空白的配对点
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": tool_block.id,
            "content": f"VALIDATION REJECTED: {err}. Call submit_verdict again with a corrected payload.",
        }]})

    return None, total_in, total_out, last_error


CASES = {
    "fixtures/case_a.py": [
        {"id": "F1", "claim": "mutable default argument: cart=[] is shared across calls", "lines": [7]},
        {"id": "F2", "claim": "bare except swallows every exception including KeyboardInterrupt", "lines": [15]},
    ],
    "fixtures/case_b.py": [
        {"id": "F1", "claim": "transfer() does not validate that amount is positive", "lines": [20]},
    ],
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        print(f"用法: python 0009-structured-verdicts.py <{'|'.join(CASES)}>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    file_text = read_file(path)
    findings, tin, tout, err = call_critic(file_text, CASES[path])

    print(f"\n总用量: in={tin} out={tout}")
    if findings is None:
        print(f"流程失败: {err}", file=sys.stderr)
        sys.exit(2)

    # ---- 洞4:算术权归 Python ----
    survived = 0
    for f in findings:
        print(f"[{f['verdict']}] {f['id']} | lines {','.join(map(str, f['lines']))} | {f['evidence']}")
        if f["verdict"] == "VERIFIED":
            survived += 1
    print(f"\n程序自算 survived = {survived} / {len(findings)}")
    sys.exit(1 if survived > 0 else 0)


if __name__ == "__main__":
    main()
