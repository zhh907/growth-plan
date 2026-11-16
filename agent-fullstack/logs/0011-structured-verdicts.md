# 0011 · Phase 1 — Structured verdicts via forced tool use (0009): both hazards killed on first run

**Date: 2026-11-15 · Session 11**

## What I did
1. Opening quiz (3 questions from log 0010): ALL THREE missed or reversed.
   - Q1 (summary line vs per-finding verdicts): answered "trust the summary" — reversed. Correction: BOTH are LLM output; the difference is the program can cross-check per-finding verdicts against the file and count them itself. "Never trust second-hand conclusions; trust what you can compute from raw material."
   - Q2 (why short-circuit never fired): "don't know". Answer: clean file ≠ clean segment reports; boundary blindness makes FPs inevitable → 0 firings.
   - Q3 (why exit=2 three times): "don't know". Answer: triple regex mismatch — `SURVIED` typo (missing V), literal space before colon in regex, and `of N` dropped from model output (prompt's `<n> or <N>` ambiguity).
2. Concept block (before any code): two INDEPENDENT death causes of string parsing — (A) structure guessed via regex → format drift; (B) content self-reported → model arithmetic wrong (0008: said 2 truth 1, said 3 truth 4). Different cures: schema kills A, count-in-Python kills B. Retry ladder: retry (1–2 max) → deterministic repair → fail loud (exit 2), with the three judgments (error type transient vs design flaw / idempotency / budget cap).
3. **Learning-mode change (learner-driven, mid-session)**: transcription/cloze retired. Learner: "不想照着敲了 感觉很浪费时间 我感觉初步学习 需要的是理解知识 理解伪代码". New mode: mentor delivers concepts (Chinese) + pseudocode + the runnable file; learner studies, runs acceptance, answers prediction questions. Synced to `agent.md` (Who the learner is) and memory rule #16.
4. Learner self-doubt episode ("Python 基础不牢固, 本命是 Java"): honest split — the actual gaps were nested-dict literal muscle memory (Java `Map.of` equivalent) and first-time JSON Schema authoring (Swagger/OpenAPI counterpart), NOT programming ability. Evidence: line-level code questions (os.environ, os.path) are reviewer behavior, not beginner behavior.
5. Shipped `0009-structured-verdicts.py` + `fixtures/case_a.py` (2 seeded bugs: mutable default arg L7, bare except L15) + `fixtures/case_b.py` (clean; mocked FP replicating 0008 boundary blindness — guard `validate_amount` at L10-18/21 invisible to a slice around L20).
6. Acceptance run by learner, BOTH CASES PASSED FIRST TRY: case_a `stop=tool_use`, 2×VERIFIED, survived=2/2 (in=718 out=219); case_b 1×REFUTED citing **lines 10,18,21** (in=486 out=147) — the "search the WHOLE FILE first" clause did the work; refutation cites counter-evidence lines, not the accusation line. Cost ~5-7× cheaper than 0008's full pipeline (3225/982 for paper C).
7. Side Q&A: `os.environ["K"]` vs `os.getenv("K")` = same source, two failure philosophies (fail-fast KeyError at startup vs None-propagation exploding far from root cause; required config → `[]`, optional → `.get(default)`); `os.path` trio (`realpath`/`dirname`/`isabs`+`join`) = CWD anchoring, the 0003 lesson made structural.
8. Understanding-climb friction points (valuable): "submit_verdict 这个方法没看到" — the fake-tool insight. It has NO function body; appears only in TOOLS declaration, tool_choice, and prompt. 0003 borrowed the tool's EXECUTION (real read_file), 0009 borrows the tool's PARAMETER SLOT as the answer sheet. "Nobody executes a DTO."
9. **Destructive test RUN (next-session opener, after initial skip)**: learner changed schema enum to `["VERIFIED","REFUTEDD"]`, re-ran case_b. Observed: attempt 1 model submitted `REFUTEDD` (**schema's format constraint overrode the model's own content judgment** — format-first behavior, direct evidence of forced-tool-use strength); validate_verdict rejected it; error fed back as tool_result with tool_use_id; attempt 2 model submitted `REFUTED` (inferred correct value from the error message) → accepted, survived=0, exit=0. **The tool_result feedback path is now EXECUTED and verified (relay accepted the shape, no 400).** Bonus bug found: the enum existed in TWO places (schema enum + hardcoded whitelist in validate_verdict) → drift → fixed with single source of truth `ALLOWED_VERDICTS` constant referenced by both. DRY violation was mentor's own. Still unverified: the retry-exhausted → exit=2 path (would require both copies to reject REFUTED).

## Key knowledge (the load-bearing five)
1. Two independent death causes of string parsing need two different cures: schema (shape) + count in Python (arithmetic).
2. Defense in depth: layer 0 tool_choice (enforced by API/relay — "probably works", unauditable), layer 1 validate_verdict (your own deterministic code — the ONLY guarantee you fully control), layer 2 retry cap, layer 3 fail loud.
3. Forced tool use = borrow the tool's parameter slot as the output format. The API gives the model only one answer card, so it cannot free-style.
4. Two retry feedback paths differ by protocol: free text → plain user message; invalid tool_use → tool_result WITH matching tool_use_id, else HTTP 400. This is the pairing point blanked 3× in quizzes — now hand-walked in code (still unexecuted).
5. schema guarantees shape, never semantics. That's why survived_count is deliberately absent from the schema.

## Prompt caching addendum (same session)
Learner added `cache_control: ephemeral` to the system block (hit a 422 first: forgot the `[...]` list wrapper around the text block). Observed across runs: `cache_read=512` stable hit (system + tools prefix), `cache_write=0` (write was paid in an earlier un-instrumented run), uncached `in=230` (file + findings, changes every call). in dropped 486→230 after the marker. Unexplained honestly: 230+512=742 ≠ 486 — relay billing or block-formatting overhead, insufficient data, no conclusion. Lesson: prefix must be byte-identical; write 1.25× once, read 0.1× per hit, 5-min rolling TTL.

## Open items
- Retry-exhausted → exit=2 path still not observed (destructive test triggered the recovery path instead — both enum copies must reject REFUTED to force exhaustion).
- Surgery experiments still queued (whole-file clause ablation; as_completed fan-in ordering).
- Note: log 0010's "next artifact" language policy confirmed in practice — Python fixtures worked cleanly, no encoding sagas.

## Re-quiz seeds (next session opens with these)
1. Why does submit_verdict have no `def`? What does 0009 borrow from the tool mechanism that 0003 also borrowed but differently?
2. The three defense layers: who executes each, and why is validate_verdict the only one you can fully trust?
3. Two retry feedback paths: when must the feedback be a tool_result with tool_use_id?
4. (carried, missed this session) summary line vs per-finding verdicts — which is data, which is decoration, and why?
