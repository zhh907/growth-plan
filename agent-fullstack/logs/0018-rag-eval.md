# 0018 — RAG L4: retrieval eval, recall@k + parameter sweep (0016-rag-eval.py)

Date: 2026-11-19. Zero-cost unit: no LLM calls — golden set + substring hit check only. Deterministic, repeatable, regression-able.

## 1. What was built

- Golden set: 10→13 questions, each human-labeled with an evidence substring unique to the answer section (uniqueness verified string-by-string before use).
- Hit rule: evidence substring appears in ANY of the top-k chunks. recall@k = hits / N.
- Sweep: chunk configs {80/20, 150/40, 300/60} × k ∈ {1,2,3,5}.
- Round 2 (harder test): +3 confusable sections in the KB (会员运费权益 / 海外购退货 / 货到付款 — all freight/payment topic, e.g. 海外购 splits freight international-buyer/domestic-seller vs 无理由 buyer-pays vs quality-issue seller-pays) + 3 golden questions targeting them. Also a deliberate landmine: 货到付款 section says NOT eligible for 7-day no-reason return, superficially conflicting with section 一.

## 2. Results

Round 1 (13→wait, 10 questions, 8-section KB):

| config | R@1 | R@2 | R@3 |
|---|---|---|---|
| 80/20 (13 blocks) | 60% | 90% | 100% |
| 150/40 (7) | 70% | 100% | 100% |
| 300/60 (4) | 100% | 100% | 100% |

Round 2 (13 questions, 11-section KB with distractors):

| config | R@1 | R@2 | R@3 |
|---|---|---|---|
| 80/20 (17 blocks) | 69% | 92% | 100% |
| 150/40 (10) | 69% | 85% | **92% — Q3 (quality-issue freight) missed at k=3** |
| 300/60 (5) | 92% | 92% | 100% |

## 3. Findings

1. **The columns are NOT comparable across rounds** — the golden set changed (10→13, new questions easier: 货到付款's evidence appears 4× in its section). 80-char's apparent 60%→69% "improvement" is a question-mix artifact. **Eval numbers are only comparable on the SAME golden set + SAME KB.** This methodology rule is the unit's top takeaway.
2. **Same-topic distractor sections are the real retrieval killer.** All damage concentrated in the freight question cluster (Q3 missed at k=3 on the baseline config): 海外购/会员/货到付款 chunks outranked the true 质量问题 chunk. Synonym-level mismatches (L2) were solved by longer text; lookalike-section confusion is a different failure mode that length does NOT solve.
3. **300-char lost its perfect score** (100%→92% at R@1): dilution smoke — one chunk averages ~3 topics, freight questions started landing on the wrong block. With only 5 blocks the ceiling effect still cushions it; in a real 10k-block KB this config degrades hard.
4. **No config passed clean in round 2.** Parameter choice has no free lunch; it must be re-evaluated whenever the KB changes (= regression testing for retrieval).
5. **Mentor prediction falsified** (predicted 80/300 drop, 150 stable; actual 150 hit hardest): 150-char chunks put the freight evidence at the same granularity as the distractor sections, maximizing lookalike-ness. Numbers over intuition — that's the point of evals.
6. **recall alone is gameable**: 300/60 wins R@1 in round 1 only because 4-block retrieval is nearly trivial and it silently injects 2-3 unrelated topics per hit. A second axis (precision@k / injected-chars) is still missing — queued, not built.

## 4. recall@k notation (taught on request)

@ = "at", recall@k = recall computed looking only at the top k results. Family: precision@k, MRR (1/rank of first correct), NDCG@k. Same role as Sharpe/MDD/PnL shorthand in trading — dense, standard, unfamiliar once.

## Re-quiz seeds

1. Why were round-1 and round-2 columns incomparable? (golden set + KB both changed; only same-set comparisons are valid)
2. What failure mode did the distractor sections expose that text length does NOT fix? (same-topic lookalike chunks outranking the true answer)
3. Why is 300/60's round-1 perfect score misleading? (5-block ceiling effect + recall blind to noise injection/dilution)
4. What must happen to eval numbers when the KB grows? (re-run on the fixed golden set = retrieval regression test)
5. recall@3 = 100% and = 60% both possible for the same system — what knob produces the difference? (k itself; also chunk config — the whole point of the sweep)
