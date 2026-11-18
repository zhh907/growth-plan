#!/usr/bin/env python3
"""0014 — RAG L2:真实 embedding + 余弦相似度检索。

L1 纸面玩具 [提到钱吗, 提到货吗] 只有 2 根轴;这里换真模型:
BAAI/bge-small-zh-v1.5(中文优化,512 维,CPU 可跑,离线)。

流程 = RAG 的"R"半边:
  文档库 encode 成向量 → 问题 encode 成向量 → 余弦相似度排序 → top-k

用法: python 0014-embedding-retrieval.py
首次运行会下载模型(约 100MB);HF 慢可先 export HF_ENDPOINT=https://hf-mirror.com
"""
import torch
from sentence_transformers import SentenceTransformer

MODEL = "BAAI/bge-small-zh-v1.5"

# 知识库:4 张工单(扩充版 —— 每张 20~30 字,接近真实工单长度)
# D 是干扰项:和 A 都围绕"扣款",但意思相反
#   A = 钱扣多了,要退回
#   D = 没扣成功,钱没出去
DOCS = [
    "我买一件东西却被扣了两次钱,重复扣款了,要求把多扣的一笔退回来",          # A
    "订单显示已付款,可是三天过去了,物流信息一直没有更新,到现在还没收到货",    # B
    "快递送到的时候盒子已经压破了,打开发现里面的东西摔坏了,没法用了",        # C
    "我下单之后账户余额没有变化,支付页面显示扣款失败,订单也一直没有生效",    # D
]

# 3 个问题(Q1 加长:补出"付款/账上少了两次"这些上下文,给模型更多信息)
#   Q1 应匹配 A;注意和 A 表达完全不同("划走两笔" = "扣了两次")
#   Q2 应匹配 C;但"收到/东西"这些字也出现在 B 里
#   Q3 是 B 的大意复述,不是原话 —— 比照抄更接近真实使用
QUERIES = [
    "我付款的时候同一秒被划走了两笔钱,账上少了两次",        # Q1 → 应捞 A
    "收到的东西摔碎了",                                # Q2 → 应捞 C
    "钱付了好几天,东西一直没送过来",                      # Q3 → 应捞 B
]


def main() -> None:
    # 加载模型;首次运行会先下载到本地缓存
    print("加载模型(首次运行需下载)...", flush=True)
    model = SentenceTransformer(MODEL)
    dim = model.get_sentence_embedding_dimension()
    print(f"向量维度 = {dim}(L1 玩具只有 2 维)\n")

    # encode():输入字符串列表,输出向量列表
    #   doc_vecs 是 4 个向量,每个 512 个数
    #   query_vecs 是 3 个向量,每个 512 个数
    # normalize_embeddings=True:把向量长度统一成 1
    #   这样两个向量直接点乘,结果就等于余弦相似度
    doc_vecs = model.encode(DOCS, normalize_embeddings=True)
    query_vecs = model.encode(QUERIES, normalize_embeddings=True)

    # @ 是矩阵乘法,一次算出所有"问题-文档"两两组合的相似度
    # 结果 sim 是 3 行 4 列:
    #   sim[i][j] = 第 i 个问题和第 j 份文档的余弦相似度
    #   范围 -1 到 1,越大越相似
    sim = torch.from_numpy(query_vecs) @ torch.from_numpy(doc_vecs).T

    for qi, q in enumerate(QUERIES):
        scores = sim[qi]  # 第 qi 行 = 这个问题分别对 4 份文档的相似度
        # argsort():排序后返回下标,不返回分数
        # 例如分数 [0.7, 0.3, 0.9, 0.1] → order [2, 0, 1, 3]
        # 表示最相似的是 2 号文档,其次是 0 号,依此类推
        order = scores.argsort(descending=True)
        print(f"问: {q}")
        for rank, di in enumerate(order.tolist(), 1):
            mark = " ← top-1" if rank == 1 else ""
            print(f"  {rank}. [{scores[di]:+.3f}] {DOCS[di]}{mark}")

        # 对比:传统关键词法 = 哪份文档和问题相同的字最多,就选哪份
        # set(q) & set(d) 取两个字符串的公共字符
        overlap = [(len(set(q) & set(d)), d) for d in DOCS]
        overlap.sort(reverse=True)
        print(f"  (关键词法会选: {overlap[0][1]},共同字符 {overlap[0][0]} 个)")
        print()

    # 附加:4 份文档两两之间的相似度,4 行 4 列
    dd = torch.from_numpy(doc_vecs) @ torch.from_numpy(doc_vecs).T
    # 对角线是文档和自己的相似度,恒等于 1,必须先排除
    # 方法:把对角线改成 -2(一个不可能的极小值),让它们永远排不上最大
    dd.fill_diagonal_(-2)
    # 在全表找最大值的位置,换算回第 i 行第 j 列
    i, j = divmod(dd.argmax().item(), len(DOCS))
    print(f"语义最远的两份文档: 「{DOCS[i]}」 vs 「{DOCS[j]}」 余弦 = {dd[i, j]:+.3f}")


if __name__ == "__main__":
    main()
