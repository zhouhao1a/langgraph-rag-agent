import asyncio
from fastapi import FastAPI
from ..core.config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE,HF_ENDPOINT
from rich import print as rprint
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from .tools import calculator, search_kb, scrape_web, get_weather
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage,ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver



# DeepSeek API 是 OpenAI 兼容的，用 ChatOpenAI 直接接，bind_tools 才能正常工作
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_API_BASE
)

llm_with_tools = llm.bind_tools([calculator, search_kb, scrape_web, get_weather])

tools = ToolNode([calculator, search_kb, get_weather, scrape_web])


def agent(state: MessagesState):
    messages=[SystemMessage(content="你是测试团队的AI助手，帮助测试工程师解答测试规范、缺陷管理、回归流程、""日志排查等问题。"
                                    "涉及测试规范和流程的问题，必须调用search_kb工具查询知识库后再回答，禁止凭记忆编造。")]+state["messages"]


    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent)
builder.add_node("tools", tools)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")


# 注意：AsyncSqliteSaver 需要先从连接字符串异步打开数据库，所以 graph 的编译放到 main() 里做（见文件底部）
# 流式输出
async def stream_answer(query: str, graph, config):
    async for chunk, metadata in graph.astream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="messages",
        config=config,               # 关键：带上 thread_id，记忆才能按线程存取
    ):
        # 只打印 AI 的文本 token； HumanMessage(输入) 和 ToolMessage(工具结果) 都不打
        if chunk.content and not isinstance(chunk, (HumanMessage, ToolMessage)):
            print(chunk.content, end="", flush=True)
    print()


async def run_agent(user_query: str, thread_id: str, graph=None):
    config = {"configurable": {"thread_id": thread_id}}  # 同一个 thread_id = 同一段记忆
    input_data = {"messages": [("user", user_query)]}
    if graph is None:
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
            graph = builder.compile(checkpointer=checkpointer)
            async for message_chunk, _ in graph.astream(input_data, config, stream_mode="messages"):
                if message_chunk.content and not isinstance(message_chunk, (HumanMessage, ToolMessage)):
                    yield message_chunk
    else:
        async for message_chunk, _ in graph.astream(input_data, config, stream_mode="messages"):
            if message_chunk.content and not isinstance(message_chunk, (HumanMessage, ToolMessage)):
                yield message_chunk






