#!/usr/bin/env python3
"""0015 — RAG L3:切块 (chunking) + 完整 RAG 闭环。

L2 只做了"R"(检索);这次把"G"(生成)接上:
  长文档 → 切块 → 每块 encode → 问题 encode → top-k 捞块 → 块拼进 prompt → LLM 回答

知识库 = fixtures/kb_after_sales.txt(8 段售后政策,约 700 字)

用法: python 0015-rag-loop.py
"""
import os

import torch
from anthropic import Anthropic
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# ==================== 配置区 ====================

# 知识库文件路径:以本脚本位置为基准拼接,和运行时所在目录无关
KB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "kb_after_sales.txt")

MODEL = "BAAI/bge-small-zh-v1.5"   # 沿用 L2 的 embedding 模型(512 维)

# 切块的三个参数,本课的主角:
CHUNK_SIZE = 150   # 每块 150 个字
OVERLAP = 40       # 相邻两块之间重叠 40 个字
TOP_K = 3          # 每次检索只取相似度最高的 3 块,喂给 LLM

# 3 个问题,分别指向知识库里不同的段落。
# Q1 和 Q2 是一对:问法几乎一样,答案相反 ——
#   都在问"运费谁出",但无理由退货是买家出,质量问题是卖家出。
#   检索如果捞错段落,LLM 就会答反。这两题是本课的验收点。
QUESTIONS = [
    "不想要了,七天无理由退货,运费谁出?",        # Q1 → 应捞「一、七天无理由退货」
    "东西有质量问题要退货,运费谁承担?",          # Q2 → 应捞「二、质量问题退换货」
    "退款一般多久能到账?",                       # Q3 → 应捞「三、退款时效」
    "你们支持货到付款吗?",
]


# ==================== 切块函数 ====================

def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """把长文本切成若干块,返回字符串列表。

    方法:滑动窗口 —— 一个固定长度 (size) 的窗口,从文本开头一路滑到结尾。

    举例:size=10, overlap=3, 文本一共 20 个字(编号 0~19):
      第 1 块 = 第 0~9 字      (窗口起点 0)
      第 2 块 = 第 7~16 字     (窗口起点 7 = 0 + 步长)
      第 3 块 = 第 14~19 字    (窗口起点 14,右边不够就少截几个)
      步长 = size - overlap = 10 - 3 = 7
      第 7、8、9 字在第 1 块和第 2 块里都出现 —— 这就是"重叠"。

    为什么要重叠:切块只看字数,不看语义。
      如果"运费由买家承担"这句话正好横跨切割点,不重叠的话它会被切成两半,
      两块里各剩半句,哪块都检索不到。
      有了重叠,切割点附近的内容会在下一块里完整出现一次。
    """
    chunks = []
    step = size - overlap  # 窗口每次前进的字数
    for start in range(0, len(text), step):
        # 从 start 开始,往后截 size 个字,不够就截到结尾
        piece = text[start:start + size]
        if len(piece) < 20:
            break  # 最后剩下的零头太短,直接丢弃,不产生信息量
        chunks.append(piece)
    return chunks


# ==================== 主流程 ====================

def main() -> None:
    # ---- 第 1 步:读入文档并切块 ----
    with open(KB_PATH, encoding="utf-8") as f:
        doc = f.read()
    chunks = chunk_text(doc, CHUNK_SIZE, OVERLAP)
    # chunks 是一个字符串列表,比如 [第0块的前150字, 第1块的150字, ...]
    print(f"文档总长 {len(doc)} 字 → 切成 {len(chunks)} 块(每块 {CHUNK_SIZE} 字,重叠 {OVERLAP} 字)\n")

    # ---- 第 2 步:把每一块变成向量 ----
    # 和 L2 完全一样的方法:encode + 归一化。
    # chunk_vecs 是 N 行 512 列(N = 块数),每一行是一块的向量。
    # 注意:切完块之后,检索的"单位"就不再是整篇文档,而是每一小块。
    embedder = SentenceTransformer(MODEL)
    chunk_vecs = embedder.encode(chunks, normalize_embeddings=True)

    # ---- 第 3 步:准备 LLM(生成半边,沿用 0009 的环境变量)----
    # .env 里有 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / MODEL_NAME
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)
    client = Anthropic(
        base_url=os.environ["ANTHROPIC_BASE_URL"],
        auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"],
    )
    llm_model = os.environ.get("MODEL_NAME", "deepseek-chat")

    # ---- 第 4 步:对每个问题走一遍完整闭环 ----
    for q in QUESTIONS:

        # (a) 检索:问题和所有块算余弦,取前 TOP_K 块
        q_vec = embedder.encode([q], normalize_embeddings=True)      # 1 行 512 列
        sims = torch.from_numpy(q_vec) @ torch.from_numpy(chunk_vecs).T  # 1 行 N 列
        # sims[0][i] = 问题和第 i 块的余弦相似度
        # argsort 排序后取前 TOP_K 个下标,就是最像的 3 块
        topk = sims[0].argsort(descending=True)[:TOP_K]

        print(f"问: {q}")
        kb_parts = []  # 存捞到的块的完整文本,等下拼进 prompt
        for rank, ci in enumerate(topk.tolist(), 1):
            preview = chunks[ci][:30].replace("\n", " ")  # 打印前 30 字让人能认出是哪段
            print(f"  捞到块 {ci} [{sims[0, ci]:+.3f}] 「{preview}...」")
            kb_parts.append(f"[片段{rank}]\n{chunks[ci]}")

        # (b) 拼 prompt:捞到的块 + 顾客问题,组成给 LLM 的一段话
        # 两句关键指令:
        #   "只根据片段回答" + "没有的信息直说不知道" = 防幻觉(不让它靠自己的
        #   通用知识编答案,比如编一个和本政策矛盾的运费规则)
        #   "标注引用了哪几个片段" = 让答案可验证,回头能核对检索质量
        prompt = (
            "你是电商售后客服。只根据下面给出的政策片段回答问题,"
            "并在答案末尾标注你引用了哪几个片段(如 [片段1])。"
            "片段里没有的信息就直说不知道,不要编造。\n\n"
            + "\n\n".join(kb_parts)
            + f"\n\n顾客问题: {q}"
        )

        # (c) 生成:一次普通调用(这课不需要 forced tool use,答案给人看)
        resp = client.messages.create(
            model=llm_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        # resp.content 是块列表(text 块、thinking 块等),把 text 块拼起来
        answer = "".join(b.text for b in resp.content if b.type == "text")
        usage = resp.usage  # token 计量,老规矩,每次都打印
        print(f"答: {answer}")
        print(f"(in={usage.input_tokens} out={usage.output_tokens})")
        print()


if __name__ == "__main__":
    main()
