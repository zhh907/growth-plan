# Current Task — Agent Full-Stack [ACTIVE TRACK]

> Promoted to primary track on 2026-11-07 (priority: agent → ops → languages).
> ops-engineer track paused at Phase 0 step 1 (`orbctl start k8s` still pending — can resume anytime).

## Task: Pick stack & ship first agent CLI [Phase 0]

**Status: IN PROGRESS (start here)**
**Started: 2026-11-07**

### Step 1 — Language: **Python (decided 2026-11-07)**

> Rationale: it's your main-job language — zero ramp-up, agent ecosystem (LangGraph, Claude Agent SDK, OpenAI SDK) is Python-first. Frontend (main-job skill) covers the UI side in Phase 2; Java background helps when reading orchestration patterns.

### Step 2 — First API call

- [x] Relay probing done (0000-probe.py): glm-5.3 & deepseek-chat OK via Anthropic protocol (2026-11-07)
- [x] LLM API call with streaming output (0001-streaming.py, 2026-11-07)
- [x] Structured output (0002-structured-output.py PASSED 2026-11-08: clean JSON on first try, 78 in / 188 out tokens)
- [ ] Tool use loop (0003-tool-use.py) ← **断点**

### Step 3 — Tool use loop

- [ ] Define 1-2 tools (function calling)
- [ ] Agent loop: model calls tool → execute → feed result back

### Step 4 — Ship first CLI agent

- [ ] Candidate: MQL4 code analyzer (reads EA source, flags common bugs) — leverages your domain edge
- [ ] Candidate B: generic single-agent CLI (simpler, less domain-coupled)

### Notes

- 报错直接贴给 Claude,附完整输出。
- 完成每小步更新 01-learning-log.md(英文)。
