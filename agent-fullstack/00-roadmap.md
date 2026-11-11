# Agent Full-Stack Engineer · Two-Year Plan

> Goal: 2026-11 → 2028-11, become an agent full-stack engineer with English fluency.
> **PRIMARY TRACK since 2026-11-07 (priority: agent → ops → languages).**
> Existing base: main job = full-stack dev (Python + Java + frontend); MQL4/EA side work; Claude Code daily user. Stack decided: **Python** for agent core, main-job frontend skills for the UI layer.
> Created: 2026-11-07

## Core Thesis

AI agents are the new application layer. The winning stack in 2028:
**LLM API + Agent orchestration + RAG + tool use + full-stack delivery**.
The moat is not calling APIs — it's designing reliable agent systems (context engineering, evals, guardrails) and shipping them as products.

## Phases

### Phase 0: Agent fundamentals (2026-11 ~ 2027-01) — **DONE 2026-11-11, ~7 weeks early**
- [x] LLM API basics: chat completions, streaming, structured output (prompt caching OBSERVED live in=28; systematic catch-up queued to Phase 1)
- [x] Tool use / function calling from first principles (0003 saga + 0005 wired loop)
- [x] Build a single-agent CLI tool: MQL4 analyzer (0005) — audited a production EA + eval suite 4/4 hits (evals/, session 0007)
- [x] Understand context window economics: 206K-token audit post-mortem, thinking+text budget pool, cost ∝ file size × rounds
- Final review 2026-11-11: deliverables PASS (checkpoint exceeded); cognitive gaps logged for Phase 1 remediation: execute_tool/resolve_path boundary layers, tool_use_id pairing (3× blank), max_tokens budget pool, artifact retention (weekly 10-min log re-read prescribed).

### Phase 1: Agent engineering (2027 Q1 ~ Q2)
- [ ] Multi-agent patterns: orchestrator, handoff, critic loops
- [ ] RAG: embeddings, vector DB (pgvector/Qdrant), chunking strategies, eval
- [ ] Memory systems: short-term vs long-term, file-based memory design
- [ ] Frameworks: one of LangGraph / Claude Agent SDK — deep, not shallow on three
- [ ] Evals: golden datasets, regression testing for agents (most people skip this = your edge)

### Phase 2: Full-stack delivery (2027 Q3 ~ Q4)
- [ ] Backend: Python (FastAPI) or TypeScript (Hono/Next.js API) — pick one, go deep
- [ ] Frontend: Next.js/React, streaming UI (SSE/WebSocket), chat UX patterns
- [ ] Auth, billing, rate limiting — the boring parts that make products real
- [ ] Deploy your own agent SaaS (ties into ops-engineer track: run it on k8s)

### Phase 3: Production & monetization (2028)
- [ ] Observability for agents: tracing, cost tracking, failure analysis
- [ ] Guardrails & safety: injection defense, output validation
- [ ] Ship a paid product (leverage 悦鹤 brand + MT5 tooling market for distribution)
- [ ] English: publish writeups / open source READMEs in English

## English Track (integrated, same rules as ops-engineer)

- All docs, code comments, commit messages in English
- Read official docs only in English (Anthropic/OpenAI docs, framework docs)
- Weekly English technical video/paper (e.g. agent design posts)
- Checkpoint 2028: English technical writing that strangers find useful

## Files

- `00-roadmap.md` — this file
- `01-learning-log.md` — learning log, newest on top
- `02-current-task.md` — current checklist

## Milestones (checkpoints — slippage must trigger a review)

| Date | Must achieve | If missed |
|---|---|---|
| 2026-12-31 | Phase 0 done: first CLI agent shipped (0000~0004 scripts + tool-use loop) | pace -20%, review time allocation immediately |
| 2027-06-30 | Phase 1 done: multi-agent + RAG + evals; a real agent project on GitHub | core milestone — cut scope, don't cut date |
| 2027-12-31 | Phase 2 done: full-stack agent service DEPLOYED on own k8s (convergence with ops track) | most critical checkpoint of the whole plan |
| 2028-06-30 | Phase 3: observability + guardrails in production; English writeups published | resume-completeness review |
| 2028-11 | Monetization validated: job offer / paid gigs / shipped product (悦鹤 channel) | final deadline |

> First formal retrospective with REAL data (sessions/hours/artifacts): **2026-11-21**
