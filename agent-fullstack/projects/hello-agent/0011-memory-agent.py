"""
    0011 memory agent : 给审计流程加跨会话长期记忆(存/取/注入闭环)

    存:每次裁决后追加 memory.jsonl(一行一条,JSON Lines 格式)
    取:审计前按文件名检索历史裁决
    注入:作为 PRIOR VERDICTS 块拼进 prompt —— 标注为 hint 而非权威,防记忆代代传错
    退出码:0=干净,1=有真 bug,2=流程失败
"""

import json
import os
import sys
from datetime import date

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(
    base_url=os.environ["ANTHROPIC_BASE_URL"],
    auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"],
)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
MEMORY_FILE = os.path.join(SCRIPT_DIR, "memory.jsonl")

CRITIC_PROMPT = """
    You are a senior Python code reviewer adjudicating findings from junior auditors.
    You receive the COMPLETE file plus all auditor findings.
    You MAY also receive PRIOR VERDICTS from earlier sessions.
    Treat prior verdicts as hints, not authority - always re-verify against the actual code.

    For EACH finding:
    1. Check the cited lines against the actual code.
    2. If the finding claims protective logic is MISSING, search the WHOLE FILE first.
    3. Verdict: VERIFIED (real bug) or REFUTED (cite the exact lines that refute it).

    Submit ONLY via the submit_verdict tool. Free text is not accepted.
"""

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
                    "verdict": {"type": "string", "enum": list(ALLOWED_VERDICTS)},
                    "lines": {"type": "array", "items": {"type": "integer"}},
                    "evidence": {"type": "string"},
                },
                "required": ["id", "verdict", "lines", "evidence"],
            },
        },
    },
    "required": ["findings"],
}

TOOLS = [{
    "name": "submit_verdict",
    "description": "Submit the final adjudication for each auditor finding.",
    "input_schema": VERDICT_SCHEMA,
}]
TOOL_CHOICE = {"type": "tool", "name": "submit_verdict"}


def validate_verdict(payload) -> tuple[list | None, str | None]:
    if not isinstance(payload, dict):
        return None, "payload is not an object"
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


# ---- 记忆层:取(按文件名检索) / 存(追加一行) ----

def load_memory(path_key: str) -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    hits = []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue                      # 坏行跳过,不让一条脏数据炸掉整个流程
            if rec.get("file") == path_key:
                hits.append(rec)
    return hits


def save_memory(path_key: str, findings: list) -> None:
    """upsert:同 file+id 更新而非追加 —— 防止记忆无限膨胀(每次运行同文件只留最新裁决)"""
    old = []
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        old.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    new_keys = {(path_key, fd["id"]) for fd in findings}
    kept = [r for r in old if (r.get("file"), r.get("id")) not in new_keys]   # 旧记录里删掉将被覆盖的
    fresh = [{
        "file": path_key,
        "id": fd["id"],
        "verdict": fd["verdict"],
        "lines": fd["lines"],
        "date": date.today().isoformat(),
    } for fd in findings]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        for r in kept + fresh:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def call_critic(file_text: str, findings_in: list, prior_block: str):
    """评审循环。返回 (findings, total_in, total_out, error)。"""
    messages = [{
        "role": "user",
        "content": (
            f"=== COMPLETE FILE ===\n{file_text}\n\n"
            f"{prior_block}"
            f"=== AUDITOR FINDINGS ===\n{json.dumps(findings_in, ensure_ascii=False, indent=2)}"
        ),
    }]
    total_in = total_out = 0
    last_error = None

    for attempt in range(1, 3):               # 首次 + 1 次重试
        resp = client.messages.create(
            model="deepseek-chat",
            system=[{"type": "text", "text": CRITIC_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            max_tokens=2000,
            messages=messages,
            tools=TOOLS,
            tool_choice=TOOL_CHOICE,
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens
        print(f"----- 第 {attempt} 次尝试: stop={resp.stop_reason} -----")

        tool_block = next((b for b in resp.content if b.type == "tool_use"), None)
        if tool_block is None:
            last_error = f"no tool_use block (stop={resp.stop_reason})"
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": "Call submit_verdict."})
            continue

        findings, err = validate_verdict(tool_block.input)
        if err is None:
            return findings, total_in, total_out, None

        last_error = err
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": tool_block.id,
            "content": f"REJECTED: {err}. Call submit_verdict again with a corrected payload.",
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
        print(f"用法: python 0011-memory-agent.py <{'|'.join(CASES)}>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    file_text = open(os.path.join(SCRIPT_DIR, path), encoding="utf-8").read()

    # 取记忆 → 注入
    prior = load_memory(path)
    print(f"记忆命中: {len(prior)} 条")
    if prior:
        prior_block = ("=== PRIOR VERDICTS (hints, re-verify) ===\n"
                       + json.dumps(prior, ensure_ascii=False, indent=2) + "\n\n")
    else:
        prior_block = ""

    findings, tin, tout, err = call_critic(file_text, CASES[path], prior_block)

    print(f"\n总用量: in={tin} out={tout}")
    if findings is None:
        print(f"流程失败: {err}", file=sys.stderr)
        sys.exit(2)

    survived = 0
    for f in findings:
        print(f"[{f['verdict']}] {f['id']} | lines {','.join(map(str, f['lines']))} | {f['evidence'][:70]}")
        survived += f["verdict"] == "VERIFIED"

    save_memory(path, findings)               # 存记忆
    print(f"记忆已写入 memory.jsonl(+{len(findings)} 条)")
    print(f"程序自算 survived = {survived} / {len(findings)}")
    sys.exit(1 if survived > 0 else 0)


if __name__ == "__main__":
    main()
