# 0016 — RAG L2: real embeddings + cosine retrieval (0014-embedding-retrieval.py)

Date: 2026-11-18. First fully local ML unit — relay has no embeddings API (`/embeddings` → "not supported for this platform"), so sentence-transformers + BAAI/bge-small-zh-v1.5 (512-dim, CPU, offline) inside projects/hello-agent/.venv.

## 1. Setup

- RAG's "R" half: encode docs → encode query → cosine sort → top-k.
- Fixture: 4 e-commerce tickets. A double-charge refund / B paid-not-shipped / C damaged goods / D payment-failed distractor (D shares "扣款" with A but means the opposite: charged-twice vs charge-failed).
- 3 queries: Q1 synonym-level ("同一秒被划走了两笔", zero keyword overlap with A), Q2 collides with B's words ("收到/东西"), Q3 exact copy of B (control).
- Mechanics worth remembering: `normalize_embeddings=True` → unit vectors → dot product IS cosine; `(3,512) @ (512,4)` = full score matrix in one matmul; `argsort` returns indices not scores; `fill_diagonal_(-2)` to exclude self-similarity from farthest-pair search.

## 2. The three-round experiment (the real lesson)

| Round | Change | Q1 outcome | Top-1↔top-4 spread |
|---|---|---|---|
| 1 | 8-char short docs | FAIL: top-1=C, A rank 2 | 0.054 (flat) |
| 2 | official bge query prefix | WORSE: A rank 3 | 0.036 (flatter) |
| 3 | expand docs+query to 25–30 chars | PASS: A rank 1 (0.764) | 0.238 (4.4× wider) |

- **Root cause confirmed: text length.** Short same-domain sentences → all cosines squeeze into a narrow band → ranking is noise. Longer text = more signal = separation. Real RAG uses paragraph-level chunks, so this failure mode is mostly a fixture artifact — but it explains WHY chunking strategy matters (too-small chunks recreate it).
- **Official prefix trick falsified for this scenario**: designed for short-query→long-article asymmetry. Our query and docs were both 8 chars; the 19-char instruction prefix dragged the query vector toward "instruction-land", away from ticket-land. Experiments beat documentation.
- **Q3 paraphrase test**: "钱付了好几天,东西一直没送过来" vs doc "订单显示已付款…还没收到货" — zero sentence overlap, still 0.801 top-1. This is the realistic case (users never quote the doc).
- Honesty note: lengthening Q1 added shared characters (付款/钱), so keyword method ALSO picked A in round 3 (11 shared chars). Round 3's win is proven by margin spread, not by beating keywords. The zero-overlap synonym win is on record from round 1 (A at rank 2 while keyword picked C).

## 3. Findings that carry forward

1. **Cosine absolute values are meaningless in-domain; only ranking matters.** Farthest doc pair in the library still scored +0.667~+0.705. Never threshold-cut; use top-k.
2. **Keyword comparison line**: embedding's advantage is specific — synonym queries (round 1) and distractor semantics. When the query literally repeats doc vocabulary, both methods agree.
3. **A vs D insight (stable across all rounds)**: "重复扣款" vs "扣款失败" share the word 扣款 yet rank as the farthest pair (round 1-2) — the model reads semantics, not character counts. The embedding is not counting words.
4. **512 dims vs L1's 2 dims**: what the extra 510 buy = axes nobody can name by hand. L1's toy died on feature-list blindness ("钱付了货没到" vs "货到了钱没划走" both [1,1]); 512 learned features resolve both.

## 4. Ops notes

- FutureWarning: `get_sentence_embedding_dimension` renamed to `get_embedding_dimension` (library API churn, cosmetic).
- First run downloads ~100MB to ~/.cache; HF hub flaky mid-run (SSL EOF) but cached weights carried it — cache resilience noted.
- torch CPU on macOS prints a harmless "Redirects not supported" warning.

## Re-quiz seeds

1. Why did 8-char docs make ranking unreliable, and what single change fixed it? (narrow cosine band → spread 0.054→0.238; longer text)
2. Cosine range is -1..+1; what was the farthest in-library pair and what does that teach? (+0.667; absolute values useless in-domain, top-k not thresholds)
3. The bge query prefix made things worse — for what scenario was it designed, why did it fail here? (short query → long articles; both sides 8 chars, prefix dragged query off-domain)
4. What evidence shows the model reads semantics not words? (A 重复扣款 vs D 扣款失败 share 扣款 yet are the farthest pair)
5. normalize_embeddings=True buys what? (unit vectors → dot product == cosine → one matmul for all pairs)
