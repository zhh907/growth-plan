# 0010 · Phase 1 L2 — Fan-out + whole-file critic (0008): acceptance passed, two hazards detonated live

**Date: 2026-11-13 (evening session) · Session 10**

## What I did
1. Opening quiz: tool-protocol direction correct (assistant=tool_use / user=tool_result / paired by tool_use_id); Q2 (critic boundary) and Q3 (SURVIVED hazard) from memory: "don't know" → corrected before content.
2. Transcribed `0008-fanout-critic.py` (full transcription, last one — learner feedback "抄代码像练打字" changed the default mode to surgery/cloze going forward).
3. Path bug: ran `../evals/...` from inside hello-agent → `projects/evals` doesn't exist; the error message itself printed the resolved absolute path (resolve_path dividend). Fix: `evals/...`.
4. Ran 3-paper acceptance B/C/A. Ritual payload achieved (C boundary FP refuted); two hazards detonated.
5. Deferred: surgery 1 (remove whole-file clause from critic prompt → does the instruction or the data do the work?) to next session's opener.

## Language-policy change (mid-session, learner-driven)
Learner: "纯英注释和输出 我也吃力". Amended `agent.md` rule 2: identifiers / LLM prompts / commits / docs stay English; **code comments and script output become Chinese** (key terms kept in English); prompts stay English (they feed the model) but get a line-by-line Chinese walkthrough. Also logged as memory rule #13.

## Acceptance results (real numbers)

**Paper B (78 lines) — expected short-circuit, got full critic cycle:**
- Segment FPs: same-bar boundary FP (guard at 21-24 invisible to segment 2), lotStep<=0 edge FP, lot-not-normalized FP (segment 3 seeing only the call site)
- Critic: SURVIVED:0 of 3 — all REFUTED with exact line evidence (21-24 guard; 40-42 normalization; 52 NormalizeLots chain)
- Design assumption falsified: a "clean" paper still produces segment-level FPs → **short-circuit almost never fires in practice; the critic is the load-bearing wall, not a safety net.** Recorded as architecture finding.

**Paper C (75 lines) — the ritual:**
- Segment 2: same-bar boundary FP (guard at 20-23 here, outside its slice)
- Segment 3: SL=0 true bug VERIFIED + same-bar boundary FP (again)
- Critic: both boundary FPs REFUTED citing lines 20-23; SL VERIFIED citing line 57 `OrderSend(..., 0, tp, ...)`; noted no OrderModify. **Ritual PASS: boundary FP refuted, true bug survives.**

**Paper A (59 lines) — expected all-VERIFIED:**
- 4 findings (same-bar ×2, lot unnormalized, SL=0), critic VERIFIED all 4 with whole-file evidence.

Cost ledger (in/out tokens): B 1595/1008 · C 3225/982 · A 2945/1055. Compared with 0006 whole-file (3150 in for A): fan-out + critic stays competitive at 3 segments on small files; win grows with file size.

## Hazard 1 detonated — output-format drift (string matching dead)
Summary line across the three runs:

```
SURVIVED:0 of 3   (no space after colon)
SURVIVED: 2       ("of N" dropped)
SURVIVED: 3       ("of N" dropped)
```

Same prompt, three shapes → regex parse failed on all three → exit=2 every run. The 0006 "SURVIVED string-match hazard" is now a **100% reproducible** failure, not a theoretical risk.

## Hazard 2 detonated — model self-counting is unreliable
- Paper C: summary claims `SURVIVED: 2`; per-finding verdicts are REFUTED/REFUTED/VERIFIED → true survived = 1.
- Paper A: summary claims `SURVIVED: 3`; per-finding verdicts are 4× VERIFIED → true survived = 4.
**Lesson: never let the model do arithmetic. Count `[VERIFIED]` markers in Python (deterministic), or emit structured JSON and validate.**

## Findings
1. Generation layer is non-deterministic (two B runs: 2 vs 3 segment FPs, different FP content); adjudication layer is stable (every FP refuted, every true bug verified, both runs). Confidence should live in the critic, not the scouts.
2. Self-reported summary lines contradict per-finding verdicts → the summary field is decoration; the per-finding verdicts are the data.
3. Short-circuit path is untested-by-fixtures and likely dead in practice (clean paper ≠ clean segment reports).

## Next step (queue)
1. **Structured output for critic verdicts** (JSON schema) — now with live evidence; kills hazard 1, enables deterministic counting to kill hazard 2.
2. Deferred opener: surgery 1 (comment out the "search the WHOLE FILE first" clause, re-run C — instruction vs data as the cure?) + surgery 2 (fan-in by as_completed to observe order dependency).
3. Then L3 dynamic routing/handoff; real-EA consolidation campaign after the pattern tour.

## Re-quiz seeds
Per-finding verdicts vs summary line (why one is data and one is decoration); short-circuit falsification; critic boundary (fact-check cannot catch rubric overreach — B/C both showed rubric-edge FPs that the critic DID catch when the file contained counter-evidence); why exit=2 on all three runs.
