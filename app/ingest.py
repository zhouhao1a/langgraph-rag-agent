import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = TextLoader("../data/knowledge.txt", encoding="utf-8")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20,
    separators=["\n\n", "\n", "。", "；", "，", " ", ""]
)
chunks = splitter.split_documents(documents)
# 调试用的
# print(f"切出来 {len(chunks)} 块")
# for i, chunk in enumerate(chunks):
#     print(f"--- 第{i+1}块 (长度{len(chunk.page_content)}) ---")
#     print(chunk.page_content)

hugging=HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
# 【离线入库】
# 拿到你传的文档块（文本）
# 用你传的 embedding 模型，把每个块文本转成向量
# 把"文本 + 向量"一起存到你指定的文件夹里
Chroma.from_documents(
    documents=chunks,
    embedding=hugging,
    persist_directory="./chroma_db")

