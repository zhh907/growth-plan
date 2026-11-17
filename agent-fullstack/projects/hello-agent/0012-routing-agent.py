#!/usr/bin/env python3
"""0012 — 动态路由 (dynamic routing):分诊台 + 各科专家。

模式:router 做一次便宜的结构化分类调用,决定任务送哪个 specialist;
     specialist 各带自己的提示词,答错科室必须报 out_of_scope,不许硬答。

复用 0009 的两件武器:
  - forced tool use (tool_choice):借工具参数槽当交卷格式
  - cache_control:router/specialist 的固定 system 前缀都打缓存标记
新增一条原则:结构化只用在代码要消费的字段上 —— 代码只分支 route 标签,
  specialist 的长答案只是给人看的,不需要 schema。

用法: python 0012-routing-agent.py <file1.py> [file2.py ...]
退出码: 0 = 全部完成 / 1 = 文件读不到 / 2 = router 输出不合法且重试用尽
"""
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

# ---------- 环境加载:标准做法 load_dotenv(手搓解析已被引号坑过一次) ----------
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

client = Anthropic(
    base_url=os.environ["ANTHROPIC_BASE_URL"],
    auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"],
)
MODEL = os.environ.get("MODEL_NAME", "deepseek-chat")

# ---------- 路由表:单一事实来源(DRY,0009 的教训) ----------
ROUTES = ("bug_hunt", "style_review", "explain")
ALL_ROUTES = ROUTES + ("unsure",)  # unsure = 兜底,router 拿不准时用

ROUTE_TOOL = {
    "name": "submit_route",
    "description": "Submit the routing decision for one code file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "route": {
                "type": "string",
                "enum": list(ALL_ROUTES),
                "description": "bug_hunt | style_review | explain | unsure",
            },
            "reason": {"type": "string", "description": "one-sentence reason"},
        },
        "required": ["route", "reason"],
    },
}

ANSWER_TOOL = {
    "name": "submit_answer",
    "description": "Submit the specialist's answer.",
    "input_schema": {
        "type": "object",
        "properties": {
            "out_of_scope": {
                "type": "boolean",
                "description": "true if this task does NOT belong to your specialty",
            },
            "answer": {"type": "string", "description": "your answer in Chinese"},
        },
        "required": ["out_of_scope", "answer"],
    },
}

# 分诊台提示词:角色定位 + 四选一的分类定义 + 两条行为规则
ROUTER_PROMPT = """You are the router of a code-review service, like a triage nurse.
Classify EACH file into exactly one route:

- bug_hunt: the file likely contains logic bugs (wrong behavior), worth a bug audit.
- style_review: the file works but is badly styled (naming, spacing, structure).
- explain: the file is clean and correct; what it needs is an explanation of how it works.
- unsure: none of the above fits confidently.

Decide from what the code actually is, not from its comments alone.
Answer with the submit_route tool only."""

# 配置表:specialist = 提示词 + 预算(路由的本质就是查这张表)
# 各科提示词的共同骨架:身份(You are...)→ 职责边界(only / Do NOT)→ 兜底条款(诚实报告)
SPECIALISTS = {
    "bug_hunt": {
        "prompt": """You are a bug hunter. Find LOGIC bugs only (wrong behavior,
wrong result, crash paths). Do NOT report style issues. Cite line numbers.
If the file is actually clean, say so honestly.""",
        "max_tokens": 2048,
    },
    "style_review": {
        "prompt": """You are a style reviewer. The code is assumed functional.
Report style problems only: naming, spacing, line length, structure.
Give concrete fixes. Do NOT hunt for logic bugs.""",
        "max_tokens": 2048,
    },
    # 教训 2026-11-17:explain 用 1024 被截断(out 顶满,answer 字段没写出来)
    # ——max_tokens 是 thinking+text 共享池,讲解类思考长,预算要给足
    "explain": {
        "prompt": """You are a code explainer. Assume the reader knows Python basics.
Explain what this code does, how it works step by step, and any notable
technique it uses (e.g. decorators, recursion, caching).""",
        "max_tokens": 4096,
    },
    "unsure": {
        "prompt": """You are the generalist. The router could not classify this file.
Give a brief overall review: what it does, any obvious problems, and which
specialty (bugs / style / explanation) would be most useful next.""",
        "max_tokens": 2048,
    },
}

# ---------- ① router:一次便宜的结构化分类 ----------
def call_router(text: str) -> str:
    messages = [{"role": "user", "content": "Classify this file:\n\n" + text}]
    for attempt in range(2):  # 重试上限 1 次,0009 同款
        resp = client.messages.create(
            model=MODEL,
            max_tokens=512,  # router 只出标签+理由,预算小(thinking+text 共享池)
            system=[{"type": "text", "text": ROUTER_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            tools=[ROUTE_TOOL],
            tool_choice={"type": "tool", "name": "submit_route"},  # 强制交卷
        )
        block = next((b for b in resp.content if b.type == "tool_use"), None)
        route = block.input.get("route") if block else None
        if route in ALL_ROUTES:
            print(f"  [router] {route} — {block.input.get('reason', '')}")
            return route
        # 不合法 → 用 tool_result 反馈(配对 tool_use_id),给一次重试
        print(f"  [router] 非法输出 {route!r},重试 ({attempt + 1}/2)", file=sys.stderr)
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": block.id if block else "unknown",
            "content": f"Invalid route {route!r}. Allowed: {ALL_ROUTES}",
        }]})
    sys.exit(2)  # fail loud:重试用尽,宁死不出错账

# ---------- ② specialist:各科医生,可报 out_of_scope ----------
def call_specialist(route: str, text: str) -> None:
    spec = SPECIALISTS[route]  # 查配置表:这段提示词、这份预算
    messages = [{"role": "user", "content": "Handle this file:\n\n" + text}]
    resp = client.messages.create(
        model=MODEL,
        max_tokens=spec["max_tokens"],
        system=[{"type": "text", "text": spec["prompt"],
                 "cache_control": {"type": "ephemeral"}}],
        messages=messages,
        tools=[ANSWER_TOOL],
        tool_choice={"type": "tool", "name": "submit_answer"},
    )
    block = next((b for b in resp.content if b.type == "tool_use"), None)
    if resp.stop_reason == "max_tokens":
        # fail loud:截断的答案不可信,宁可报警不许静默通过
        print("  [specialist] ⚠ 答案被 max_tokens 截断,结果不完整", file=sys.stderr)
    if not block:
        sys.exit(2)
    if block.input.get("out_of_scope"):
        print("  [specialist] ⚠ out_of_scope:送错科了,router 判断需复查")
    print(block.input.get("answer", ""))
    usage = resp.usage
    print(f"  [tokens] in={usage.input_tokens} out={usage.output_tokens}"
          + (f" cache_read={usage.cache_read_input_tokens}"
             if getattr(usage, "cache_read_input_tokens", None) else ""))

# ---------- main ----------
def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python 0012-routing-agent.py <file1.py> ...", file=sys.stderr)
        sys.exit(1)
    for path in sys.argv[1:]:
        print(f"\n=== {path} ===")
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"读不到文件: {e}", file=sys.stderr)
            sys.exit(1)
        route = call_router(text)   # 先分诊
        call_specialist(route, text)  # 再派单(unsure → 通科兜底)

if __name__ == "__main__":
    main()
