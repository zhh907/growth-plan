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
- [x] Tool use loop (0003-tool-use.py PASSED 2026-11-08: schema typo saga → parallel calls + CWD anchoring verified)

### Step 3 — Tool use loop

- [x] Define 1-2 tools (function calling) — get_file_info (line count + bytes)
- [x] Agent loop: model calls tool → execute → feed result back (0003, wrapped as `run_agent()` in 0004)

### Step 3.5 — CLI wrap (added 2026-11-08)

- [x] 0004-cli-agent.py: argparse + run_agent + exit codes 0/1/2 + stderr (PASSED all 4 acceptance checks 2026-11-08)

### Step 4 — Ship first CLI agent

**DECIDED 2026-11-08: Candidate A — MQL4 code analyzer** (rationale: 0004 already IS candidate B; A = domain edge × new learning; natural eval set with seeded-bug samples).

- [x] 0005-mql4-analyzer.py: new tool `read_file_chunk` (context budget + tool granularity lesson)
- [x] Wire both tools + analyzer prompt; findings output (2026-11-10 PASSED: audited real EA 悦鹤_均线逆势马丁_双边对冲_v2.mq4 — VERDICT 2/3 hits + 0 false positives, in=206020 out=7828; 7-bug debug saga + thinking/max_tokens/UTF-16 lessons in log 0006)
- [ ] Evals: 2-3 seeded-bug .mq4 samples in `evals/`, measure hit rate / false positives ← **断点**
- [ ] Ship + final review
- [ ] (queued) B1 tool hardening: UTF-16 BOM sniffing; prompt caching catch-up

### Notes

- 报错直接贴给 Claude,附完整输出。
- 完成每小步更新 01-learning-log.md(英文)。
