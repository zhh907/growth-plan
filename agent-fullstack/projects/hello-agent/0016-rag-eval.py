#!/usr/bin/env python3
"""0016 — RAG L4:检索质量评估(recall@k + 参数扫描)。

L3 的 4/4 是人眼看的;这次换成数字:
  黄金集(问题 + 人工标注的证据串)→ 对每组切块参数算 recall@k → 参数扫描对比

两个关键设计:
  1. 命中判定 = 证据串出现在 top-k 任何一块里(纯字符串检查)
     → 不用 LLM、零成本、结果确定,可以反复跑(可回归)
  2. 不调 LLM,只跑 embedding → 几秒扫完三组配置

用法: python 0016-rag-eval.py
"""
import os

import torch
from sentence_transformers import SentenceTransformer

KB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "kb_after_sales.txt")
MODEL = "BAAI/bge-small-zh-v1.5"

# ---- 黄金集:10 道题,每题人工标注一个"答案独有的证据串" ----------------
# 证据串的选取原则:只出现在答案所在的那一段,不出现在其他段(否则判定失真)
# (evidence 已逐条核对过唯一性)
GOLDEN = [
    ("不想要了,七天无理由退货,运费谁出?",     "买家自己承担"),    # 一
    ("哪些商品不能无理由退货?",                "贴身衣物"),        # 一
    ("东西有质量问题要退货,运费谁承担?",       "卖家全额承担"),    # 二
    ("退款一般多久能到账?",                    "1-3 个工作日"),    # 三
    ("同一订单被扣了两次钱怎么办?",            "多扣的款项"),      # 四
    ("快递运坏了什么时候申请赔付?",            "24 小时内"),       # 五
    ("买完降价了能补差价吗?",                  "差价补偿"),        # 六
    ("显示扣款失败但钱没退回来怎么回事?",       "支付渠道延迟"),    # 七
    ("对客服处理结果不满意怎么办?",            "48 小时内"),       # 八
    ("质量问题坚持退货卖家能拒绝吗?",          "不得拒绝"),        # 二
    # ---- 干扰轮新增:3 段"运费/付款"话题的近似段(九/十/十一)----
    ("会员退货有什么运费优惠?",                "运费抵扣券"),      # 九
    ("海外购退货运费怎么算?",                  "国际段运费"),      # 十
    ("可以货到付款吗?",                        "货到付款"),        # 十一
]

# ---- 参数扫描:三组切块配置 × 四档 k ------------------------------------
CONFIGS = [
    {"size": 80,  "overlap": 20},   # 块太短:预期余弦挤扁,排序乱
    {"size": 150, "overlap": 40},   # L3 的配置,基线
    {"size": 300, "overlap": 60},   # 块太长:一块混几个话题,向量稀释
]
K_LIST = [1, 2, 3, 5]


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """滑动窗口切块,和 0015 相同的函数。"""
    chunks = []
    step = size - overlap
    for start in range(0, len(text), step):
        piece = text[start:start + size]
        if len(piece) < 20:
            break
        chunks.append(piece)
    return chunks


def main() -> None:
    with open(KB_PATH, encoding="utf-8") as f:
        doc = f.read()

    embedder = SentenceTransformer(MODEL)

    # 问题向量只算一次(和切块参数无关,省时间)
    questions = [q for q, _ in GOLDEN]
    evidences = [e for _, e in GOLDEN]
    q_vecs = embedder.encode(questions, normalize_embeddings=True)  # 10 行 512 列

    # 表头
    print(f"{'配置':<14}", end="")
    for k in K_LIST:
        print(f"  recall@{k}", end="")
    print("   (k=3 时没命中的题号)")
    print("-" * 72)

    for cfg in CONFIGS:
        size, overlap = cfg["size"], cfg["overlap"]
        chunks = chunk_text(doc, size, overlap)
        chunk_vecs = embedder.encode(chunks, normalize_embeddings=True)

        # 相似度矩阵:10 行(题)× N 列(块)
        sims = torch.from_numpy(q_vecs) @ torch.from_numpy(chunk_vecs).T
        # 按分数从大到小排好每题的块编号
        orders = sims.argsort(dim=1, descending=True)

        recalls = {}
        missed_at_3 = []
        for k in K_LIST:
            hits = 0
            for qi in range(len(GOLDEN)):
                # 取该题的 top-k 块,检查证据串是否出现在任何一块的原文里
                topk_chunks = [chunks[ci] for ci in orders[qi][:k].tolist()]
                if any(GOLDEN[qi][1] in c for c in topk_chunks):
                    hits += 1
                elif k == 3:
                    missed_at_3.append(qi + 1)
            recalls[k] = hits / len(GOLDEN)

        label = f"{size}字/叠{overlap} ({len(chunks)}块)"
        print(f"{label:<14}", end="")
        for k in K_LIST:
            print(f"  {recalls[k]:>8.0%}", end="")
        print(f"   {missed_at_3 if missed_at_3 else '无'}")

    print()
    print("读表方法:recall@k = 10 题里答案块进入 top-k 的比例;1 = 全命中")


if __name__ == "__main__":
    main()
