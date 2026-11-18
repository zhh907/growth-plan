# 0015 — Handoff: mid-execution relay, medical record travels with the patient (0013-handoff-agent.py)

Date: 2026-11-18. Stack: 0009/0012's (relay, forced tool use, cache_control, load_dotenv).

## 1. Pattern: routing vs handoff vs orchestrator

- Routing (0012): fork at the ENTRY — classify once, dispatch to one specialist, done.
- Handoff (0013): relay DURING execution — agent A works, then transfers the conversation to B who continues. Transfer patient, and the medical record travels along.
- Orchestrator (0006): central dispatcher; control at every step.
- One-liner: routing = triage; handoff = hospital transfer with the chart.

## 2. Three design decisions (the lesson's core)

1. **What transfers** — three tiers: full history (lossless, linear token growth) / compressed summary (cheap, telephone-game distortion) / handoff note (structured: DONE / KEY FACTS / REMAINS). Two-birds answer (carried over from 0011's memory-injection principle): give B BOTH the note AND the original ticket, with trust levels labeled — the note opens with "hints, not authority; re-verify against the snapshot". The note is the guide for cheap reading; the ticket is the archive preventing distortion.
2. **Who decides to hand off** — the model can only EXPRESS intent through one of two forced tools; the code performs the switch. Control flow stays in code (0006 principle).
3. **How the relay lands in messages** — append-only, three steps: assistant content (tool_use, leaves the trail) + tool_result with matching tool_use_id (receipt) + the handoff note as a user message (B's opening view). History is never deleted.

New API point: `tool_choice={"type": "any"}` — must call at least ONE tool, model picks which. Learner asked "why pass it at all?" — because default `auto` allows plain-text replies (billing could write "should go to logistics" in prose, no tool_use block, code falls into exit 2). Three levels: auto (0003) / any (0013) / tool+name (0009/0012). `any` constrains "must submit" while freeing "which form".

## 3. Acceptance: both paths exercised first run

| Ticket | Path | Readings |
|---|---|---|
| ticket_refund (paid, stock=0) | billing → handoff → logistics → finish (2 hops) | note followed DONE/KEY FACTS/REMAINS format; logistics final answer cited `refund_issued=false` — a field ABSENT from billing's note → re-verification against the snapshot actually happened, the hints-not-authority clause worked |
| ticket_dupcharge (double charge) | billing → finish (1 hop, no handoff) | resolved in-domain, no unnecessary relay |

Cost readings: relay path in=1694 vs direct in=422 — **the relay tax is 4×**: each hop appends the note + ticket again. That is why the note is a guide, not full history. Cache hit ACROSS RUNS: dupcharge's cache_read=256 = the billing system prefix still inside the 5-min TTL from the previous ticket — the mirror image of 0012's "why cache_read=0 on first run".

Anti-pattern guarded in code: MAX_HOPS=4 breaks A→B→A ping-pong loops; invalid target (not in AGENTS, or self) → exit 2.

## 4. Topology map status

orchestrator-critic ✅ / fan-out ✅ / routing ✅ / handoff ✅ (supervisor-worker, debate left optional). The multi-agent pattern tour is complete; consolidation campaign (real codebase) and RAG remain.

## Re-quiz seeds

1. Routing vs handoff in one sentence each (entry fork vs mid-execution relay).
2. The two-birds handoff content: what does B receive, and what trust label leads the note?
3. Why must tool_choice be {"type":"any"} here — what breaks under default auto? (plain-text intent → no tool_use block → exit 2)
4. Why was the relay ticket 4× the input cost of the direct one? (append-only history: note + original ticket re-enter each hop)
5. Evidence that logistics re-verified rather than trusting the note? (cited refund_issued=false, absent from the note)
