# 0014 — Dynamic routing: triage desk + specialists (0012-routing-agent.py)

Date: 2026-11-17. Stack: 0009's (relay via .env, forced tool use, cache_control).

## 1. Pattern: static division vs dynamic division

Already-known topologies divide labor STATICALLY: orchestrator-critic (fixed pipeline, every paper flows the same path), fan-out (everyone does the same job on slices). Routing divides DYNAMICALLY: the task TYPE decides which specialist runs.

Model: hospital triage. The router (nurse) never treats — it only picks the department; each specialist (doctor) is a different system prompt (+ per-specialist budget/tools in production).

Two design decisions (the lesson's core, more than the code):
1. Router = one CHEAP structured-output call: forced tool use returns a route enum label. Router classifies, doesn't analyze.
2. Misroute defense: the classic routing accident is "wrong-department doctor treats anyway" — a specialist confidently answers outside its specialty. Two barriers: router may return `unsure` → generalist fallback; specialist schema has `out_of_scope: bool` and is instructed to report it instead of guessing.

## 2. Key readings (from live run)

- **Routing in code = classification + dict lookup, no if/else chain**: `route = call_router(text)` then `SPECIALISTS[route]` pulls the prompt. A specialist IS just its prompt; production adds per-specialist tools, model tier, max_tokens — still one config table.
- **Structure only what code consumes**: code branches on the route label → label is schema-validated via forced tool use. The specialist's long answer is for humans → it rides in one string field, no findings-array schema (deliberate contrast with 0009).
- **Forced tool use (professional term)**: `tool_choice={"type":"tool","name":...}` — API-level switch forcing the model to answer ONLY through that tool's parameter slots; the "tool" has no def and never executes; its schema is the answer sheet. 0003's tools = model USES our functions; 0009/0012's forced tool = model FILLS OUR FORM. cures free-text format drift.

## 3. Incidents during acceptance (both instructive)

1. **Hand-rolled .env parser broke on quoted values**: base_url kept its quotes → "URL missing protocol". Fixed by switching to standard `load_dotenv(path)` — the std answer exists precisely because someone already hit these traps. Path is passed explicitly (not default) because default resolves against CWD, not script dir, and fails SILENTLY — same CWD-anchoring lesson as 0003.
2. **explain specialist truncated at max_tokens=1024** (out exactly 1024, answer field never written): live detonation of the Phase-1 remediation item "max_tokens is a thinking+text SHARED pool" — explaining-style tasks think long and burn the answer budget. Fixes: per-specialist budgets in the config table (explain=4096), and fail-loud `stop_reason == "max_tokens"` warning to stderr instead of silently passing a truncated answer.

## 4. Acceptance results

| Fixture | Expected route | Actual | Specialist behavior |
|---|---|---|---|
| case_a.py (2 seeded bugs) | bug_hunt | bug_hunt ✅ | both bugs hit, no style-nagging |
| style_bad.py (works, ugly) | style_review | style_review ✅ | pure PEP8 fixes, no bug-hunting |
| explain_me.py (memoize+fib) | explain | explain ✅ | full explanation after budget fix |

Cost readings: specialist in ≈ 195–490; cache_read=256 appeared on the SECOND explain call (first call was a miss — cache only pays when the SAME prefix repeats; three different specialists = three different prefixes = no cross-hits). Router reason line leaked full bug analysis (triage nurse started prescribing) — acceptable, could be constrained in prompt.

## 5. Prompt line-by-line reading (meaning + English grammar)

> New log convention from 0014 on (user request): every lesson's prompts get a line-by-line reading with grammar notes. The prompt-writing arsenal these five prompts demonstrate: imperative for commands, only/NOT for boundaries, passive voice for assumptions, pro-forms to avoid repetition.

### ROUTER_PROMPT (8 lines)

| Line | Reading | Grammar point |
|---|---|---|
| You are the router..., like a triage nurse. | role anchor + simile | `like + noun` simile; **triage** = ER sorting, the pattern's namesake; `the router of a code-review service` of-genitive |
| Classify EACH file into exactly one route: | the task | imperative; `classify A into B` collocation; EACH caps = per-item; `exactly one` blocks multi-label |
| bug_hunt: the file likely contains logic bugs, worth a bug audit. | route def | `likely` here is an ADVERB (= probably; can also be adj in "is likely to"); `worth + noun/gerund` (active form, passive sense) |
| style_review: the file works but is badly styled. | route def | ellipsis: second clause shares subject, keeps only `is`; `badly styled` past participle as adjective; **style as VERB**; `works` = runs correctly |
| explain: the file is clean and correct; what it needs is an explanation of how it works. | route def | **pseudo-cleft** `what X needs is Y` = emphasis; `how it works` noun clause as object of of |
| unsure: none of the above fits confidently. | escape hatch | `none of + noun` takes SINGULAR verb (AmE); `confidently` softens: not "nothing matches" but "nothing matches WITH CONFIDENCE" — invites admitting uncertainty |
| Decide from what the code actually is, not from its comments alone. | evidence rule | parallel contrast `from X, not from Y`; `what the code actually is` noun clause; `alone` POSTPOSED adjective = "comments alone / 仅凭注释" (blocks comment spoilers in fixtures) |
| Answer with the submit_route tool only. | output format | `with X only` restriction — pairs with tool_choice as double lock |

### Specialist skeleton + one grammar gem each

Shared skeleton: identity (You are...) → boundary (only / Do NOT) → honesty clause.

| Prompt | Gem |
|---|---|
| bug_hunt `Do NOT report style issues` | full form `Do NOT` (not Don't) — prompt convention, caps NOT for visual reinforcement |
| bug_hunt `If the file is actually clean, say so honestly` | **say so**: so = pro-form replacing the whole clause ("say THAT it is clean") |
| style_review `The code is assumed functional` | passive + ellipsis: assumed (to be) functional — preset assumption that blocks scope creep into bug-hunting |
| style_review `Do NOT hunt for logic bugs` | **hunt for** collocation; hunt echoes bug_hunt imagery |
| explain `Assume the reader knows Python basics` | assume + that-clause (that deleted): audience setting |
| explain `(e.g. decorators, recursion, caching)` | **e.g.** = exempli gratia = for example (NOT i.e.); mixing nouns and gerunds in enumeration is fine |
| unsure `The router could not classify this file` | **could not** past form = router already tried and failed; auto-becomes reported admission |
| unsure `which specialty would be most useful next` | **would** subjunctive softener: suggest, don't prescribe — the generalist's exit is re-triage |

## Re-quiz seeds

1. Routing in code: where does the "choice" actually happen? (router fills a label; `SPECIALISTS[route]` dict lookup IS the dispatch)
2. What is a specialist, concretely? (an entry in a config table: prompt + budget (+tools/model in production))
3. Why did cache_read=0 on the first 3-file run but 256 on the re-run? (cache needs the same byte-identical prefix a second time)
4. explain got out=1024 and empty answer — cause and two fixes? (thinking+text shared pool; per-specialist budget + stop_reason max_tokens fail-loud)
5. Professional term for `tool_choice={"type":"tool"}`? (forced tool use; the broader technique = structured output via tool calling)
