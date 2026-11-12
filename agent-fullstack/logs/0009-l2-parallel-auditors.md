# 0009 · Phase 1 L2 — Parallel auditors: fan-out/fan-in · Context economics + boundary blindness

**Date: 2026-11-12 (evening session) · Session 9**

## What I did
1. Global-map lesson first (user's stated learning preference: whole map before details, no interleaved consolidation): Phase 1 = 5 units (multi-agent / RAG / memory / evals / frameworks), multi-agent unit internal map L1 serial → L2 parallel → L3 dynamic, structured output as cross-cutting block.
2. Hand-transcribed `0007-parallel-auditors.py`; two transcription bugs fixed along the way.
3. Ran paper A: 2/3 hits, cost halved — plus rubric ambiguity #2 discovered.
4. Fixed rubric item 2 (decidable-question rewrite).
5. Ran paper C (before the A/B regression): hit 1/1 plus a NEW false positive — the boundary-blindness case, the signature failure of parallel slicing.
6. 0008 (fan-out + whole-file critic, MapReduce shape) designed and briefed — transcription queued for tonight.

## The artifact (0007 — what changed vs 0006)

| Decision | Implementation |
|---|---|
| Python splits the file, not the model | orchestrator calls `get_file_info` + `read_file_chunk` itself (recon in deterministic code) |
| Segment auditors are TOOLLESS | segment text arrives in the FIRST user message; `run_agent` returns on round 1 (`end_turn`). Proves the loop machine is role-agnostic |
| Fan-in by submission order | `[f.result() for f in futures]` — ThreadPoolExecutor futures preserve submission order regardless of completion order |
| Threads | API calls are I/O-bound → `ThreadPoolExecutor`, wall-clock ≈ slowest segment |

`run_agent` nit from 0006 finally fixed: hardcoded `"Analyze this MQL4 file for bugs:"` prefix removed; `first_message` used verbatim.

## Debug cases (transcription)

1. `IndentationError: unindent does not match any outer indentation level` at `def split_segments` — invisible whitespace mix before the def. Diagnosis: `sed -n '120,135p' f | cat -A` (^I = tab, $ = EOL). Same law as YAML sibling alignment: same level must align exactly.
2. `SyntaxError: did you forget parentheses around the comprehension target?` — user wrote `pool.submit(audit_segment),i,...` (paren closed after the function name); args must live INSIDE the call parens. Structure explained: submit = "drop the task ticket, don't wait"; futures = claim checks in submission order; `f.result()` = redeem (blocks there).

## Run results

**Paper A (first run, old rubric item 2):**

| Segment | Result |
|---|---|
| 1 (1-19) | NO BUGS + honest NOT JUDGEABLE ×3 (zero fabrication — small view, tight mouth) |
| 2 (20-38) | lot finding [HIGH] ✓ — same-bar NOT filed (saw the MaxTrades cap, read checklist literally) |
| 3 (39-59) | SL=0 finding [HIGH] ✓ |

Score 2/3 (vs whole-file 0006: 3/3). Cost: **in=1472 total vs 0006's 3150 → 53% cheaper**. Wall-clock 61.9s ≈ slowest segment.

**Rubric ambiguity #2 (the same-bar miss):** checklist said "no new-bar guard AND no check for already-open orders". Segment auditor read "check" literally (a MaxTrades cap exists → AND fails → no bug). Whole-file auditors read it semantically (cap of 5 does not REFUSE re-entry → bug). Two agents, same code, opposite verdicts — same disease as ambiguity #1, new transmission route: **independent contexts share no precedent**. Fix: rewrite as a decidable question — "the bug exists if an entry signal can fire again while a same-type position is already open; a MaxTrades cap > 1 does NOT count as refusal."

**Paper C (after rubric fix, before A/B regression):**

| Segment | Result |
|---|---|
| 1 (1-25) | NO BUGS — quoted the real new-bar guard at lines 20-23 ✓ |
| 2 (26-50) | **SAME-BAR filed [HIGH] — FALSE POSITIVE** ("no new-bar guard exists anywhere in the visible entry path" — the guard lives in segment 1's slice) |
| 3 (51-75) | SL=0 ✓ (the only true seed) |

Score: 1/1 hits + 1 FP — a brand-new disease.

## Key insight: boundary blindness (the L2 signature failure)

A segment auditor cannot see outside its slice, and when a judgment needs facts from another slice, it treats what it cannot see as non-existent. Fan-in then receives **contradictory testimony** (segment 1: "guard exists"; segment 2: "no guard, file a bug") and our string-counting merge cannot cross-examine. The rubric fix was correct; the failure is architectural.

The complete L2 cost catalog (all three now observed live):

| L2 cost | Observed as |
|---|---|
| Cross-segment bugs invisible | NOT JUDGEABLE ×N (honest, harmless) |
| Calibration/verdict consistency drops | A-paper same-bar miss (rubric ambiguity #2) |
| Cross-segment fact loss → FP | C-paper same-bar FP (boundary blindness) |

## The fix designed: 0008 — fan-out + whole-file critic (MapReduce shape)

- Stage 1: 0007 unchanged (parallel scouts, cheap, honest, boundary-blind)
- Short-circuit: all segments clean → critic never runs, exit 0
- Stage 2: ONE critic gets the WHOLE file + all segment reports in its first message (toolless; whole-file reading is exactly the cure for slice-blindness). Prompt clause: "if a finding claims protective logic is missing, CHECK THE WHOLE FILE FIRST — the guard may exist in lines that auditor never saw"
- Acceptance: A = findings VERIFIED; B = short-circuit; **C = SL VERIFIED + boundary FP REFUTED, SURVIVED: 1 of 2** (the ritual)
- A/B regression with new rubric folded into 0008 acceptance

Vocabulary moment (user asked "what does rubric mean"): rubric = grading criteria / scoring standard (Latin ruber = red; medieval red-ink chapter instructions). Project usage: the checklist's per-item violation definitions. Two production incidents so far both traced to ambiguous rubric wording.

## Gotchas
1. f-string prefix lost in transcribed print → `{elapsed:.1f}` printed raw full-precision float. Tiny, but unformatted floats in output are how you spot a missing `f`.
2. Toolless agents: when the model reaches for a tool that isn't there, feed back a plain string ("no tools in this role") — it self-corrects in the same turn.
3. Wall-clock gain claim needs the serial baseline to be rigorous — noted, not measured (three sequential 0006-style runs would be the control).

## Artifacts
- `projects/hello-agent/0007-parallel-auditors.py` — L2 fan-out/fan-in, accepted with known limitation
- `evals/` unchanged
- 0008 reference design delivered, transcription queued same evening

## Next step
- Tonight: transcribe 0008, run 3-paper acceptance (C = the ritual: boundary FP must get REFUTED)
- Then: structured output for critic verdicts (kills the SURVIVED string-match hazard) — next sub-lesson
- L3 (dynamic routing/handoff) after that; real-EA campaign as consolidation after the pattern tour (user preference: whole map first, consolidate later)
- SECURITY: relay key rotation STILL pending since 2026-11-07
