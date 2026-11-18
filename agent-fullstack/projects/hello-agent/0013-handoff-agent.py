#!/usr/bin/env python3
"""0013 — handoff(交接):执行中接力,病历跟着走。

模式:与路由(0012)的区别——路由在入口分诊一次;handoff 是 A 干到一半
     把对话转交 B 接着干。转交三件套:
  1. 转交什么:交接单(导读,hints not authority)+ 原始工单(档案,权威)
     ——两者都给 B,标注可信级别,防电话游戏也防全量重读
  2. 谁决定转:模型只能通过 forced tool 二选一表达意图(finish / handoff),
     真正换人由代码执行——控制流永远在代码里(0006 原则)
  3. 消息怎么落:assistant 的 tool_use 留痕 + tool_result(配对 id)+
     交接单作为 user 消息追加,历史只追加不删除

新 API 点:tool_choice={"type": "any"} —— 不指定具体工具,模型从
finish/handoff 两个工具里自选一个(0009/0012 用的是 type:tool 指定单个)。

用法: python 0013-handoff-agent.py <ticket.txt>
退出码: 0 = 处理完成 / 1 = 工单读不到 / 2 = 非法交接或跳数超限
"""
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

# ---------- 环境 ----------
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
client = Anthropic(
    base_url=os.environ["ANTHROPIC_BASE_URL"],
    auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"],
)
MODEL = os.environ.get("MODEL_NAME", "deepseek-chat")

# ---------- 角色表:handoff 的目标只允许这几个(DRY 单一事实来源) ----------
AGENTS = ("billing", "logistics")

FINISH_TOOL = {
    "name": "submit_finish",
    "description": "Submit the final resolution of the ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "description": "final answer in Chinese"},
        },
        "required": ["answer"],
    },
}

HANDOFF_TOOL = {
    "name": "submit_handoff",
    "description": "Hand the ticket over to another agent with a handoff note.",
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "enum": list(AGENTS),
                   "description": "the receiving agent"},
            "note": {"type": "string",
                     "description": "handoff note: what is DONE, KEY FACTS verified, "
                                    "and what REMAINS. One line each."},
        },
        "required": ["to", "note"],
    },
}

SYSTEMS = {
    "billing": """You are the billing specialist of a support desk.
Your job: verify payment facts against the ORDER SNAPSHOT in the ticket
(the snapshot is the AUTHORITY; never assume beyond it).
- If the problem is a billing problem you can fully resolve, call submit_finish.
- If money is fine and the problem clearly belongs to shipping/stock, call
  submit_handoff to logistics. Your note must list: DONE, KEY FACTS, REMAINS.
- Never answer questions about shipping arrangements yourself.""",
    "logistics": """You are the logistics specialist of a support desk.
You may receive a handoff note from billing. IMPORTANT: the note is a HINT,
not authority — re-verify its key facts against the ORDER SNAPSHOT yourself
(the snapshot is the AUTHORITY). Then give the final resolution
(what to do with the order, what to tell the customer) via submit_finish.""",
}

MAX_HOPS = 4  # 防 A→B→A 乒乓死循环:接力跳数上限


def run(ticket: str) -> None:
    agent = "billing"  # 起始医生固定;入口分诊是 0012 路由的事
    messages = [{"role": "user", "content": ticket}]
    total_in = total_out = 0

    for hop in range(1, MAX_HOPS + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEMS[agent],
                     "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            tools=[FINISH_TOOL, HANDOFF_TOOL],
            tool_choice={"type": "any"},  # 二选一:模型自选,但只能在这两个里选
        )
        usage = resp.usage
        total_in += usage.input_tokens
        total_out += usage.output_tokens

        block = next((b for b in resp.content if b.type == "tool_use"), None)
        if block is None:
            print(f"[hop {hop}] {agent} 未交工具调用,退出", file=sys.stderr)
            sys.exit(2)

        if block.name == "submit_finish":
            print(f"[hop {hop}] {agent} → finish")
            print(f"\n{block.input['answer']}")
            print(f"\n[tokens] in={total_in} out={total_out}"
                  + (f" cache_read={usage.cache_read_input_tokens}"
                     if getattr(usage, "cache_read_input_tokens", None) else ""))
            return  # 处理完成

        # ---- handoff 分支:真正换人的是下面这段代码,不是模型 ----
        to = block.input.get("to")
        note = block.input.get("note", "")
        if to not in AGENTS or to == agent:
            print(f"[hop {hop}] 非法交接目标 {to!r},退出", file=sys.stderr)
            sys.exit(2)
        print(f"[hop {hop}] {agent} → handoff → {to}\n  note: {note}")

        # 病历追加三步,只追加不删除:
        messages.append({"role": "assistant", "content": resp.content})  # ① 留痕
        messages.append({"role": "user", "content": [                    # ② 回执 + ③ 转诊单
            {"type": "tool_result", "tool_use_id": block.id,
             "content": "handoff accepted"},
            {"type": "text", "text":
                f"[HANDOFF NOTE from {agent} — hints, not authority; "
                f"re-verify against the snapshot]\n{note}\n\n"
                f"[ORIGINAL TICKET]\n{ticket}"},
        ]})
        agent = to  # 换医生

    print(f"跳数超过 {MAX_HOPS},疑似乒乓死循环", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    if len(sys.argv) != 2:
        print("用法: python 0013-handoff-agent.py <ticket.txt>", file=sys.stderr)
        sys.exit(1)
    try:
        ticket = open(sys.argv[1], encoding="utf-8").read()
    except OSError as e:
        print(f"读不到工单: {e}", file=sys.stderr)
        sys.exit(1)
    run(ticket)


if __name__ == "__main__":
    main()
