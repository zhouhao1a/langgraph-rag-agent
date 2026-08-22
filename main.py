import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph_rag_agent.state import InputState, AgentState, OutputState
from langgraph_rag_agent.testllm import llm
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
hugging = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")


def node_a(state:InputState):
    return {}

def node_b(state:AgentState)->AgentState:
    # 【在线检索】
    # 第 1 小步：加载已有的向量库
    vectorstore = Chroma(
        persist_directory="./chroma_db",  # 从哪个文件夹加载
        embedding_function=hugging  # 告诉它查询时用哪个模型把用户的问题转向量
    )
    # 检索，将用户的问题和转化成向量，在与库的文件比对向量比
    result=vectorstore.similarity_search_with_score(
        query=state["user_query"],    #用户的问题
        k=2                     #返回向量比距离最近的k个代码块
    )
    docs=[]
    for doc,score in result:
        # 提前过滤，就不用在grade那里在过滤了
        if score<1.0:
            doc.metadata["score"] = score
            docs.append(doc)
        print(f"分数:{score},内容:{doc.page_content[:30]}")

    return {"retrieved_docs":docs}


def grade_documents(state: AgentState) -> str:
    return "relevant" if state["retrieved_docs"] else "irrelevant"


def fallback(state:OutputState)->AgentState:
    return {"final_answer":"抱歉，知识库中没有找到与您问题相关的内容。"}



def node_c(state:AgentState)->AgentState:
    # 1. 把检索到的文档块拼成一段"参考资料"文本
    docs_text = ""
    for doc in state["retrieved_docs"]:
        docs_text += doc.page_content + "\n"

    # 2. 组装 prompt：参考资料 + 用户问题，一起放进 HumanMessage
    messages = [
        SystemMessage(content="你是一个知识库助手，只能根据提供的参考资料回答用户问题，资料中没有的不要编造"),
        HumanMessage(content=f"参考资料：\n{docs_text}\n问题：{state['user_query']}"),
    ]
    res = llm.invoke(messages)
    return {"final_answer": res.content}


builder=StateGraph(AgentState,input_schema=InputState,output_schema=OutputState)
builder.add_node("node_a",node_a)
builder.add_node("node_b",node_b)
builder.add_node("node_c",node_c)
builder.add_node("fallback",fallback)
builder.add_edge(START,"node_a")
builder.add_edge("node_a","node_b")
builder.add_conditional_edges("node_b",grade_documents,{
    "relevant": "node_c",
    "irrelevant": "fallback",
})
builder.add_edge("node_c",END)
builder.add_edge("fallback",END)
graph=builder.compile()
# 测试三个不同的问题，观察分数变化
test_queries = [
    "出差住宿费标准是多少",   # 相关，但换了说法
    "公司电话号码是多少",     # 完全无关
    "报销要带什么材料",       # 半相关
]

for query in test_queries:
    result = graph.invoke({"user_query": query})
    print("=" * 50)
    print(f"用户问题：{query}")
    print("-" * 50)
    print("AI 回答：")
    print(result["final_answer"])
    print()