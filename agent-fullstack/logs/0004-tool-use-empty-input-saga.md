# 0004 · Tool use — the empty-input saga (0003, near-complete)

**Date: 2026-11-08 · Session 4**

## What I did
1. Ran 0003: agent looped 4 rounds calling tools with EMPTY input `{}` — hit the hard cap.
2. Added observability (RAW tool_use dump + per-call print) — data over guesses.
3. Attempted curl bisection against both protocol endpoints (hit a shell-variable red herring).
4. Code review of MY OWN transcription found the real root cause.

## What I learned — key insights

**1. THE root cause: schema key typo — "input" vs "input_schema".**
API silently ignores unknown keys → model received a tool with NO parameter definition → sent `input: {}` → tool raised "missing path" → model retried forever (it couldn't know how to fix what it couldn't see). The relay was innocent. Lesson: when model behavior is bizarre, dump the RAW request you're sending before blaming infrastructure.

**2. Contract-key interfaces fail SILENTLY.**
A typo'd schema key doesn't error — it produces "haunted" behavior. Same class as YAML key typos in k8s. Countermeasure: dump raw payloads in smoke tests.

**3. Agent loop control-flow completeness.**
Missing `break` after FINAL ANSWER: unreachable while every round had tool calls, but GUARANTEED to fire once the schema was fixed — and it did (empty results appended → 400 "upstream_error"). Unexercised branch ≠ correct branch.

**4. Parallel tool calls exist.**
Fixed schema → model issued TWO tool_use blocks in one round (both paths, correct args) — models plan batch operations when the schema lets them.

**5. CWD vs script directory.**
Relative paths resolve against the process CWD, never the script location (same reason cron jobs "work manually but fail in cron"). Fix: anchor relative paths to `os.path.dirname(os.path.abspath(__file__))` inside the tool — deterministic layer absorbs the probabilistic layer's quirks.

**6. Tool-use smoke test doctrine.**
Chat ability ≠ tool ability. Before committing to a model for agents, run a standard tool-call smoke test (0003 serves as this from now on).

## Gotchas
1. `get_file_info() missing 1 required positional argument: 'path'` ×7 — caused by insight 1.
2. `Expecting value: line 1 column 1` — piping empty curl output into json.tool; never pipe blindly.
3. `HTTP 000, 0.000s, 0 bytes` — curl failed instantly: $BASE_URL was EMPTY (name mismatch ANTHROPIC_BASE_URL vs BASE_URL in different shells). 0.000s = no connection attempted; 60s = timeout. Read the timing!
4. `400 [1213] 未正常接收到prompt参数 upstream_error` — empty results array appended as user message (missing break).
5. IDE auto-import `from anthropic.resources.messages import messages` shadowed by my own `messages` list — delete junk imports.

## Artifacts
- `0002-structured-output.py` PASSED · `0003-tool-use.py` PASSED logic, pending final rerun with break + CWD anchoring

## Next step
- Rerun 0003 from a DIFFERENT directory to verify CWD anchoring; then 0004: wrap the loop as a real CLI tool (Phase 0 finale).
