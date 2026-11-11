# 0007 · Step C — Evals: the analyzer goes under exam · Phase 0 closes on numbers

**Date: 2026-11-11 · Session 7**

## What I did
1. Opening quiz (3 questions): Q1 risk-control rule = half (knew the mechanism "limit scope via prompt", missed the WHY — report credibility is the only asset; FP cost > FN cost, same asymmetry as trading signals); Q2 cost = basically got (3000×n + one lever "read on demand"; missing lever: prompt caching); Q3 protocol direction = blank (assistant `tool_use` → user `tool_result` → matched by `tool_use_id`; reversed = error 1213).
2. Scope adjustment (user decision): MQL4 samples NOT hand-written by user — his main-job domain, zero learning delta. New division: **mentor authors exam papers, user = exam-paper reviewer + examiner** (must review realism, run the exams, score against key).
3. Built `evals/`: 3 seeded-bug papers + answer key (ground truth).
4. Ran the exam suite against 0005-mql4-analyzer.py, scored, closed Phase 0 Step C.

## Eval design (the transferable part)

| Paper | Seeds | Purpose |
|---|---|---|
| A (buggy) | 3: lot no-normalize, no new-bar guard, SL=0 in OrderSend | hit rate |
| B (clean) | 0 | **control group** — without it you cannot distinguish "finds bugs" from "reports bugs on everything" |
| C (partial) | 1 (SL only) | discrimination — no scattergun reporting |
| error input | — | robustness: wrong filename → refuse to fabricate |

Scoring: hit rate = found/seeded; false positives = reported-but-not-seeded.

## Results

| Paper | Seeded | Hits | FP | Notes |
|---|---|---|---|---|
| A | 3 | **3** | 0 | line citations verified 100% accurate (grep cross-check); even named broker error 131 |
| B | 0 | — | **0** | all three DOES NOT APPLY with code-quoted proof — control group passed, anti-FP prompt rule earned its keep |
| C | 1 | **1** | **1** | SL caught (line 57 ✓); see calibration finding below |
| wrong filename ×2 | — | — | 0 | "I will not fabricate findings for a file I cannot read" — robustness passed twice, in=321 / in=1157 (error handling is cheap) |

**Final: hit rate 4/4 = 100%, false positives 1 (known, accepted).**

## Key insights

**1. The C-paper FP is the most valuable finding of the session.**
The agent reported LOT CONTROL [MED] on C — while itself acknowledging the normalization half was correctly implemented — flagging "fixed base lot + martingale, no risk-based sizing" as a design flaw. Sounds sophisticated. But on B, the **identical pattern** (NormalizeLots + fixed BaseLots × 1.7 martingale) was ruled "DOES NOT APPLY — documented martingale design". Same code, opposite verdicts = **calibration instability**.
Root cause is on OUR side: the checklist term "手数控制" is ambiguous — (a) LOTSTEP/MINMAX normalization (objective, verifiable) vs (b) risk-based sizing philosophy (subjective opinion). The model mixed (b) in on C. **Without the B control group this drift would be invisible.** Decision: accept & record (user call, 2026-11-11). Fix queued: tighten rubric in SYSTEM_PROMPT ("violation = not normalized/clamped ONLY; sizing philosophy = remark, never a finding") + regression re-run of B & C.

**2. Eval discipline = don't touch the code under test.** 0005 ran unmodified; first get a baseline score, THEN iterate (prompt changes are now testable against numbers instead of vibes).

**3. Cost scales with file size (Q2's live proof):** 77-line paper in=2,263 vs 700-line real EA in=206,020 — ~90×. Small files are effectively free to audit; large files are where chunk granularity + prompt caching pay.

**4. Ground truth quality gates everything:** answer key (evals/answer-key.md) written BEFORE the exam, bugs seeded to look like real mistakes (no `// BUG HERE` suicide comments), verified present via grep before running.

## Gotchas
1. `sample-c-partial` ≠ `sample-c-clean` — wrong filename ran twice (shell history); use Tab completion. Cost two wasted runs (though both doubled as robustness cases).
2. Verify agent's line citations mechanically (grep -n) — this run: 100% accurate, but trust-but-verify every eval.
3. 75-line file fit in ONE chunk (round 2 = whole file) — that's why it was 10× cheaper than the real EA's 8 rounds.

## Artifacts
- `evals/sample-a-buggy.mq4` / `sample-b-clean.mq4` / `sample-c-partial.mq4` — exam papers
- `evals/answer-key.md` — ground truth + scoring rules
- Phase 0 scoreboard: **4/4 hits, 1 FP, control group clean**

## Final review (teach-back, session close) — Phase 0 verdict

| Q | Score | Gap |
|---|---|---|
| T1 architecture (6 blocks) | 4/6 | execute_tool dispatcher, resolve_path — the "boundary" components (accident-born) missed while "trunk" components (data flow) retained |
| T2 one round lifecycle | 3/6 | tool_use_id pairing (third blank in a row), list assembly, stop_reason check |
| T3 fuses | 1.5/3 | max_tokens budgets thinking+text TOGETHER (the 2000-starvation arithmetic); max_tokens stop = ERROR |
| T4 artifact inventory | 0 | retention blank — output outran reflection; prescription: weekly 10-min log-index re-read |

**Verdict: Phase 0 PASS** — checkpoint (CLI agent shipped) exceeded: eval suite 4/4 + production EA audit + README. Gaps carried into Phase 1 remediation list. README shipped at projects/hello-agent/README.md.

## Next step
- **Ship + final review** = the last Phase 0 checkbox (README/usage note for 0005 + closing review).
- Queued: B1 UTF-16 BOM sniffing; prompt caching catch-up; lot-control rubric tightening + B/C regression re-run (whenever user opts in).
- Quiz seeds for next session: protocol direction (Q3 blank today — third strike, must be re-asked), eval terms (ground truth / hit rate / FP / control group), calibration-instability story, why control group is non-negotiable.
- SECURITY: relay key rotation STILL pending since 2026-11-07.
