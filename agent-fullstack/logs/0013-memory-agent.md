# 0013 · Memory systems (0011): store/retrieve/inject loop, upsert, poison self-heal

**Date: 2026-11-17 · Session 13**

## What I did
1. New unit: memory systems. Core concepts: short-term = the context window itself (free, gone at close, cost grows with size); long-term = external storage + retrieve + inject ("stuff relevant old facts back into the next prompt"). Three questions decide the design: what to store / how to retrieve / when to inject — **injecting the wrong thing is worse than injecting nothing**.
2. Live example on hand: the mentor's own memory system (index file always loaded + per-topic files opened on demand + typed records) — the retrieve-inject pattern in production.
3. Built `0011-memory-agent.py` on top of the 0009 stack (schema + validate + forced tool use, reused verbatim — third reuse, the stack is now a proven layer):
   - STORE: append verdicts to `memory.jsonl` (JSON Lines, one record per line)
   - RETRIEVE: filter by filename before adjudication
   - INJECT: `PRIOR VERDICTS` block, prompt marks it "hints, not authority - always re-verify"
4. **Learner spotted the flaw unprompted: "记忆会无限增加"** — every run appends, same file accumulates duplicates. Correct observation; fixed with **upsert** (same file+id → replace, rewrite file). Standard toolkit taught: upsert / eviction / top-k retrieval. Bonus: upsert gives **self-heal** — a poisoned record survives only until the next run overwrites it.
5. Poison experiment (prediction first): learner predicted C (unstable/hesitant). **Actual: B — model re-verified the code and kept VERIFIED despite memory claiming REFUTED.** Three-run data: cold start in=227 / memory hit in=240 (+13 tokens for 2 records) / poisoned in=241, verdict unchanged. After the run, `cat memory.jsonl` confirms F1 flipped back to VERIFIED (self-heal worked).
6. Honesty note recorded: case_a's bug is textbook-grade (mutable default arg) — code evidence crushes memory, little room for bias. **Borderline cases (ambiguous evidence) are the real testbed for memory-induced drift; one strong-evidence run does not generalize.**

## Key knowledge
1. Memory = store + retrieve + inject; the inject step costs tokens every call (+13 for 2 records here; scales linearly → top-k needed at scale).
2. Naive append grows unbounded → upsert (dedup by key) / eviction / top-k are the three standard controls.
3. Injected memory must be labeled as hint, not authority — and even then, verify with borderline cases before trusting it.
4. Upsert self-heals poisoned memory in one run — destructive writes beat append-only when records are keyed.

## Cost
~230-240 in / ~190-205 out per run.

## Open items
- Borderline-case poison experiment (real testbed for memory drift) — queued, optional.
- Retrieval is exact-key (filename) only; semantic retrieval (embedding + top-k) = the bridge into the RAG unit.
- Surgery experiment still queued from 0009.

## Re-quiz seeds
1. Three questions of memory design, and why "inject wrong > inject nothing"?
2. What did the learner-spot infinite-growth flaw teach, and what are the three standard controls?
3. Why is the poison result (model kept VERIFIED) NOT generalizable evidence that memory can't bias?
