# 0008 · Phase 1 Unit 1 — Orchestrator-Critic: two agents in series · Acceptance on all three papers

**Date: 2026-11-12 · Session 8**

## What I did
1. Hand-transcribed `0006-orchestrator-critic.py` from mentor's reference (user writes all code; mentor reviews).
2. First run crashed with error 1213 — found and fixed a transcription bug (missing return branch).
3. Ran the full eval suite (A/B/C) with the OLD auditor prompt — observed the known FP survive the critic (deliberate "stress the system" route).
4. Applied the rubric fix (delete the subjective sizing clause from AUDITOR_PROMPT), re-ran C and B as regression.
5. All acceptance criteria met. L1 (multi-agent, hand-rolled) first artifact shipped.

## The artifact (what's actually new vs 0005)

Deliberately ~90% identical to 0005. The delta is the whole point of L1:

| New part | Why it matters |
|---|---|
| `run_agent(system_prompt, first_message, max_rounds)` | prompt is now a PARAMETER — one loop machine, many roles. In 0005 the prompt was welded inside the function |
| `CRITIC_PROMPT` | second role: fact-checker. For EVERY finding, re-read cited lines via `read_file_chunk`, then verdict `VERIFIED \| REFUTED` with one line of evidence |
| `main()` = orchestrator | deterministic PYTHON, not an LLM: stage 1 audit → check report string → maybe stage 2 verify → exit code. Control flow lives in code; probability only inside roles |
| Short-circuit | `"NO BUGS FOUND" in audit_report` → critic never runs, exit 0 |
| Rubric tightening in AUDITOR_PROMPT | deleted "or hardcoded fixed lots with no risk-based sizing" — the FP root cause found in session 0007 |

## Debug case: error 1213 after end_turn (the session's best catch)

**Symptom**: A-paper run printed `round 3 : stop=end_turn, tools=[]` — then a traceback from `client.messages.create`. Error `1213 未正常接收到prompt参数`.

**Root cause chain** (transcription bug, NOT an API problem):
1. In `run_agent`, the `if not tool_calls:` block only handled `stop_reason == "max_tokens"` — the `end_turn` success path had NO return.
2. Execution fell through: appended the assistant message, built `results = []` (empty), appended a user message with EMPTY content.
3. Loop continued to round 4, called create with a trailing empty user message → relay rejected: 1213.

**Analogy that stuck**: like an EA with a guard branch for `!OrderSelect()` but no return on the normal path — the normal case falls into error-handling code below.

**Fix**: in `if not tool_calls:` — extract text first, warn only if max_tokens, return UNCONDITIONALLY.

**Lesson**: error 1213 = malformed message list (we've now seen it twice: reversed tool direction in 0004-era, empty trailing user message today). Read what the last message in `messages` actually is before blaming the API.

## Acceptance run 1 — OLD prompt (stress test, deliberate)

| Paper | Result | Verdict |
|---|---|---|
| A (3 seeds) | auditor 3 findings, critic 3/3 VERIFIED, SURVIVED 3/3 | PASS — in=3150 (~1.4× the 2263 single-audit run) |
| B (clean) | NO BUGS FOUND → short-circuit, critic never ran | PASS — in=1179, cheapest full run yet |
| C (1 seed) | auditor reported SL (true) + LOT [MED] (the known FP); critic VERIFIED BOTH — **FP survived** | FAIL by design criteria — and that's the finding |

## Key insight 1: what the critic can and cannot catch

The critic VERIFIED the false positive — and every word of its evidence was TRUE (`BaseLots = 0.01` is real, no `AccountBalance()` anywhere, the NormalizeLots side-note was accurate). The finding's FACTS were all correct; its VERDICT was out of rubric (a design choice prosecuted as a checklist violation).

| Defense line | Catches | Cannot catch |
|---|---|---|
| Critic (fact-check) | fabricated line numbers, mismatched quotes, unsupported claims | true-fact findings that SHOULD NOT be filed (rubric overreach) |
| Rubric (prosecution standard) | — | overreach must be fixed at the source, in the prompt |

Hypothesis "adding a critic stops the C-paper FP" was REFUTED by experiment. Evals did their job: they turned a plausible architecture claim into a measured negative result.

## Key insight 2: `SURVIVED: 3 of 3` — string-matching LLM output is a loaded gun

On the fixed-prompt C run, the auditor filed 1 finding; the critic ALSO numbered and verified the two "checklist does not apply" statements → `SURVIVED: 3 of 3` (semantically wrong; true survivors = 1). Exit code was right by luck this time. Failure mode: if the single real finding gets REFUTED while clean-claims verify, output reads `SURVIVED: 2 of 3` → `"SURVIVED: 0" in report` = False → exit 1 = false alarm.

**Lesson**: exit-code logic keyed on `"SURVIVED: 0" in critic_report` bets correctness on the model's phrasing habits. Proper fix = structured output (JSON schema) — queued for L2. Recorded, not fixed (YAGNI at this scale).

## Acceptance run 2 — rubric fixed, regression on C + B

| Paper | Before fix | After fix |
|---|---|---|
| C | 2 findings (SL + FP) | **1 finding (SL only)**, lot item explicitly "no bug" with line evidence; critic VERIFIED the real finding |
| B | NO BUGS FOUND, short-circuit | NO BUGS FOUND, short-circuit, in=1179 — no collateral damage |

**Final scoreboard: 3/3 papers pass. 0006 accepted.**

## Cost observations
- A (auditor+critic): in=3150 vs 0005 single audit in=2263 → **~1.4×**, cheaper than the 1.8-2.2× estimate because the critic reads a small file once.
- B short-circuit: in=1179 — the cheap path is genuinely cheap.
- C regression after fix: in=6212 (both stages re-read the full file; critic counted clean-claims too).
- Critic bills are driven by its tool granularity, exactly like the auditor's.

## Transcription nits found during review (fixed or noted)
1. `read_file_chuck` typo in AUDITOR_PROMPT (tool names in prose vs schema fight by luck — model trusts the schema).
2. `run_agent` hard-coded the prefix `"Analyze this MQL4 file for bugs:"` inside the message builder AND main passed it again → critic's first message wrongly opened with the auditor's instruction. Noted; critic coped.
3. Various cosmetic typos (s senior, bugget) — harmless.

## Gotchas
1. `if not tool_calls:` must return on BOTH stop reasons — an agent loop needs exactly one exit per branch. Missing-return bugs surface one round LATER, at the API boundary, disguised as an API error.
2. Always `print(resp.stop_reason)` per round (we did) — it's the flight recorder that made this bug diagnosable in one look.
3. Regression scope rule applied: after tightening the rubric, re-ran only C (target) + B (control). A untouched — a narrower rubric can only remove findings, not add them.

## Artifacts
- `projects/hello-agent/0006-orchestrator-critic.py` — orchestrator-critic, accepted
- `evals/` — unchanged; same three papers as Phase 0 Step C
- Scoreboard: A 3/3 VERIFIED · B short-circuit · C 1 true finding, FP eliminated by rubric fix

## Next step
- Opening quiz next session (the protocol question, asked before reading ANY code): assistant `tool_use` → user `tool_result`, matched by `tool_use_id`. Plus new seeds: critic's defense boundary (fact-check vs rubric), SURVIVED string-matching hazard.
- Decide: run 0006 against the real 700-line EA (cost ~2× the 206K single audit) or move to next unit first.
- Queued: structured output for critic verdicts (JSON schema); B1 UTF-16 BOM sniffing; prompt caching.
- SECURITY: relay key rotation STILL pending since 2026-11-07.
