# 0005 · Script → CLI tool (0004, Phase 0 near-final)

**Date: 2026-11-08 · Session 5**

## What I did
1. Transformed the 0003 agent loop script into a real CLI: `0004-cli-agent.py`.
2. Mentor provided full reference code (user transcribed by hand per tutoring rules); user ran all 4 acceptance checks — ALL PASSED.
3. Post-pass quiz on three design decisions (return vs break / stderr / nargs) — answers reviewed and completed by mentor.

## Concepts learned

**1. Script vs tool: deterministic shell wrapping a probabilistic core.**
0003 was a screenplay (question hardcoded). 0004 takes the question from argv. Layering rule: `run_agent()` knows nothing about CLI — it takes a question string and RETURNS `(answer, in_tokens, out_tokens)`. Shell (argparse, validation, exit codes, printing) owns all I/O. Tomorrow a FastAPI service can call `run_agent()` unchanged: print is for humans, return is for programs.

**2. argparse = the first guardrail.**
- positional `question` with `nargs="+"` + optional `--max-rounds` (default 5).
- Missing args → argparse prints usage and exits with code 2 (free validation, no custom code).
- Why `nargs="+"`: shell word-splitting. Quoted question = single argv element (works either way). Unquoted = N elements; without nargs, argparse takes only the first word and fails LOUDLY on the rest (unrecognized arguments, exit 2). With nargs="+" + `" ".join()`, unquoted input degrades gracefully. Guardrail (loud failure) + degradation (join) = two layers.

**3. Exit codes are the product's handshake with the world.**
- 0 = success, 1 = runtime failure (round cap hit → `sys.exit(1)`), 2 = usage error (argparse).
- cron / CI / shell pipelines chain on `$?`. "Prints an error but exits 0" = silent success in a pipeline — classic incident source.

**4. stderr vs stdout.**
Pipes only carry stdout. `print(..., file=sys.stderr)` keeps the error channel out of the data channel: `agent.py "..." | jq .` still works when the agent fails — jq sees empty/clean data, the human sees the real error on the terminal. Bonus: `2>/dev/null` silences diagnostics; log collectors separate the streams.

**5. `main()` + `if __name__ == "__main__"`.**
`__name__` is `"__main__"` only when run directly; on import it's the module name. Future tests can `import` the module and call functions WITHOUT triggering an API call (cost discipline). Standard structure for every serious Python CLI.

**6. Function exits beat loop breaks.**
`return text, ...` on final answer; `return None, ...` after the loop (round cap). Caller distinguishes success from truncation by checking None — never silently truncate.

## Acceptance evidence (all from user's real runs, 2026-11-08)
1. Normal: parallel tool calls in round 1 (2× get_file_info), verdict correct (51 vs 35 lines), exit=0, usage in=564/out=181.
2. `--help`: usage + help rendered.
3. No args: argparse usage error, exit=2.
4. Run from `~`: tool returned ABSOLUTE path → SCRIPT_DIR anchoring verified (also closes the 0003 open item "rerun from a different directory").
   - Cost observation: single-file question (479/74) ~30% cheaper than two-file comparison (564/181) — more entities in a question = more tool calls + more context. Design questions cost-consciously.

## Gotchas
1. When wrapping a loop into a function, the whole body re-indents one level — most error-prone step (watch for IndentationError).
2. Junk auto-import from 0003 (`from anthropic.resources.messages import messages`) must NOT be carried over — it shadowed the local `messages` before.
3. `SCRIPT_DIR` computed once at module level, not inside the tool function (it never changes).

## Artifacts
- `0004-cli-agent.py` PASSED all 4 acceptance checks (exit codes 0/2/0, anchoring verified)

## Next step
- Phase 0 Step 4: pick the CLI agent topic — candidate A: MQL4 code analyzer (domain edge) vs candidate B: generic single-agent CLI. Then Phase 0 finale → roadmap Phase 1.
