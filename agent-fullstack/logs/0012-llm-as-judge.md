# 0012 · LLM-as-judge (0010): confirmation bias caught live, rubric iteration diminishing returns

**Date: 2026-11-15 · Session 12**

## What I did
1. Opening quiz (3 questions): Q2 half-correct (defense layers' executors confused: tool_choice is API/relay, retry+fail-loud is own code — none is "the model"); Q3 answered the id pairing but missed "protocol requires tool_result first after tool_use, else 400"; Q1 (fake tool) taught via follow-up — learner articulated the mechanism (tool_use carries name+input, program takes input) but initially missed WHY the model obeys the schema (answer: tool_choice gives only one answer card; enum probability suppression beats content judgment — the REFUTEDD run).
2. New unit: LLM-as-judge. One-liner: use a model to grade outputs, replacing manual eval at scale. Three known traps taught upfront: position bias / self-preference / score inflation. Countermeasures: swap order, different judge model, rubric anchors.
3. Built `0010-llm-judge.py`: grades three REAL evidence pieces from 0009's case_b runs (E1 thorough, E2 cites irrelevant lines 23/6, E3 minimal-but-correct) against the file, forced tool use (`submit_grades` schema, reusing 0009's full stack: schema + validate + retry + fail loud). Human baseline: E1=4, E2=2, E3=3. **Prompt deliberately did NOT mention verifying lines — testing spontaneous fact-checking.**
4. Learner predicted "judge will verify". **Falsified, and more interestingly than expected: SELECTIVE verification.** Run 1: E2 got 4/5 — reasoning cited only the accurate lines (21, 10), silently skipped irrelevant 23 and 6. Confirmation bias: conclusion first, then cherry-picked support. Classic LLM-as-judge trap, caught live.
5. Rubric iteration (two rounds by learner):
   - v2 "list what EACH cited line contains; above 3 requires accurate AND relevant" → E2 still 4. Behavior changed (it DID enumerate line 23 = `if amount > balance`) but the adjective "relevant" never executed — "accurate description" satisfied it.
   - v3 binary question "for each cited line yes/no: does it help refute the claim? above 3 requires all yes" → E2 dropped to 3. Direction correct, still 1 above human baseline (2); E2/E3 ranking still tied vs human (E3 > E2).

## Key knowledge
1. Adjectives in rubrics don't execute; binary decidable questions do. (Same lesson as 0007's rubric decidability — second sighting, different costume.)
2. Rubric iteration shows diminishing returns: 2 edits moved E2 by 1 point; chasing 3/3 agreement via prompt alone is a losing game.
3. Correct deployment: judge for ranking/coarse filtering; exact scores need human calibration or deterministic code checks (line-in-range, line-content markers are code-checkable).
4. The 0009 structured-output stack (schema + validate + retry + fail loud) transfers verbatim to any judge/agent output contract — it is the reusable layer of this whole track so far.

## Cost
Run ~1.0K in / 240-420 out per run.

## Open items
- Surgery experiment still queued (delete prompt clause #2 in 0009, re-run case_b — instruction vs data).
- Memory-systems unit untouched (next candidate).

## Re-quiz seeds
1. Confirmation bias in LLM-as-judge: what did E2's selective verification look like, concretely?
2. Why did "accurate AND relevant" fail but the yes/no question moved the score?
3. When is LLM-as-judge the right tool vs deterministic checks vs human eval?
