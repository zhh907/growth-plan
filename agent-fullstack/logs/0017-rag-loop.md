# 0017 — RAG L3: chunking + full RAG loop (0015-rag-loop.py)

Date: 2026-11-18. Stack: L2's local embedding (bge-small-zh) + 0009's relay LLM stack. First unit where R and G halves meet.

## 1. What was built

- KB fixture: `fixtures/kb_after_sales.txt` — 8-section after-sales policy, 771 chars (refund/exchange/freight/timing/double-charge/payment-anomaly/complaints).
- Pipeline: read doc → sliding-window chunk (CHUNK_SIZE=150, OVERLAP=40 → 7 chunks) → encode each chunk → cosine → top-k=3 → chunks into prompt → LLM answers with citation tags ([片段n]).
- Anti-hallucination clause: "only answer from the excerpts; if the info isn't there, say you don't know; don't fabricate" + mandatory citation tags.

## 2. Acceptance: 4/4 (3 positive + 1 negative)

| Q | Retrieval top-1 | Answer | Note |
|---|---|---|---|
| 无理由退货运费谁出 | ✅ chunk 0 (0.748) | 买家承担 [片段1] | |
| 质量问题运费谁承担 | ❌ chunk 0 (无理由!) 0.673 > correct chunk 1 at 0.637 | 卖家全额承担 [片段2] | **retrieval wrong, answer right** |
| 退款多久到账 | ✅ chunk 2 (0.651) | 1-3 / 3-7 工作日 [片段1] | |
| 支持货到付款吗 (negative) | max 0.478 | "不知道,片段里没有" | anti-hallucination held |

## 3. Key findings

1. **Retrieval top-1 miss ≠ wrong answer.** Q2's query (退货+运费) surfaced the 无理由 chunk first, but top-k=3 carried the correct chunk along; the LLM read all 3, answered from the right one, and the citation tag made the rescue AUDITABLE. Live proof of why production uses top-k (k=5~10), never top-1. With TOP_K=1 this would have answered wrong (买家承担 for a quality issue).
2. **Overlap is boundary insurance.** Chunk 1 starts mid-section ("退换货 商品存在质量问题..." — its heading "二、质量问题" landed at the end of chunk 0). The heading/body split didn't detonate because the 40-char overlap kept the body text matchable. The hazard is real; overlap is the mitigation.
3. **Cost honesty: RAG is NOT cheaper on a small KB.** in≈230 per call vs ~500 to paste the whole 771-char doc. RAG pays off when the KB is orders of magnitude larger than a retrieval window.
4. **Dead-zone signal in absolute scores.** Off-KB question topped out at 0.478 while all on-KB questions hit 0.6~0.75. Earlier L2 rule ("absolute cosine values are meaningless, only ranking matters") gets a refinement: within-domain rankings matter most, but a **sudden drop of the max score** is itself a usable "no good match" signal (dead-zone / low-confidence detection).
5. **Citation rule incomplete**: the model answered "不知道" yet still tagged [片段1][片段2][片段3]. The prompt never defined what to cite when it doesn't know. Fix: "if you answer 不知道, no citation tags needed." Small, logged.

## 4. Chunking mechanics recap (taught with the 20-char worked example)

- step = size - overlap; window slides by step; chunks = text[start:start+size]; trailing scraps <20 chars dropped.
- Why chunk at all: whole-doc embedding averages 8 topics into one vector (specific questions match nothing); plus injection cost.
- Tradeoff table: chunk too small → L2's flat cosine band; too big → multi-topic dilution again.

## Re-quiz seeds

1. Q2's retrieval top-1 was wrong but the answer was right — what two mechanisms saved it? (top-k carried the right chunk; LLM picked among k, citation tag made it auditable)
2. Why does chunking need overlap? What failure does it prevent? (facts straddling a cut point become half-sentences in both chunks; overlap gives border content one complete copy)
3. Why not embed the whole document as one vector? (topic-averaged vector matches nothing specific; injection cost)
4. Off-KB question's max score was 0.478 vs 0.6-0.75 on-KB — what is this signal called and what's it for? (dead-zone/low-confidence detection)
5. When is RAG cheaper than pasting the whole doc, concretely? (KB ≫ retrieval window; here it was NOT: in≈230 vs ~500 whole-doc)
