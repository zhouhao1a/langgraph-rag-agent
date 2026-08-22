import os
import asyncio

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from dotenv import load_dotenv
load_dotenv(override=True)

from rich import print as rprint
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from tools import calculator, search_kb, scrape_web, get_weather
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage,ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver



# DeepSeek API 是 OpenAI 兼容的，用 ChatOpenAI 直接接，bind_tools 才能正常工作
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE")
)

llm_with_tools = llm.bind_tools([calculator, search_kb, scrape_web, get_weather])

tools = ToolNode([calculator, search_kb, get_weather, scrape_web])


def agent(state: MessagesState):
    messages=[SystemMessage(content="你是测试团队的AI助手，帮助测试工程师解答测试规范、缺陷管理、回归流程、""日志排查等问题。"
                                    "涉及测试规范和流程的问题，必须调用search_kb工具查询知识库后再回答，禁止凭记忆编造。")]+state["messages"]

    # messages = [SystemMessage(content="你是公司知识库助手。用户问到公司制度、报销标准、差旅等问题时，必须调用search_kb工具查询，"
    #                                   "不要自己编造。其他问题可以用计算器、查天气、爬网页等工具。")] + state["messages"]


    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent)
builder.add_node("tools", tools)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")


# 注意：AsyncSqliteSaver 需要先从连接字符串异步打开数据库，所以 graph 的编译
# 放到 main() 里做（见文件底部），这里不再在模块级编译 graph
# graph = builder.compile()   # 旧写法：MemorySaver 在内存，关程序记忆即丢


# #程序停下来后，langgraph自动将messages消息存到memorySaver记忆里，不然消息会消失，通过thread_id来存和找message，所以暂停和继续的时候都要加入config参数
# config={"configurable": {"thread_id": "demo_001"}}

#
# result=graph.invoke({"messages": [HumanMessage(content="公司的差旅报销标准是什么")]},
#                        # config=config
#                     )

#   HITL === 这里就是"人工介入点" ===
# print("=== 暂停：LLM 想调用以下工具 ===")
# last_msg = result["messages"][-1]
# for call in last_msg.tool_calls:
#     print(f"  工具名: {call['name']}, 参数: {call['args']}")
# input("按回车继续执行（这就是人工确认）\n")  # 真正阻塞等待


# 观察整个AImessage的运行过程
# result = graph.invoke(None, config=config)
#  打印完整消息流，看 ReAct 循环过程
# for i, msg in enumerate(result["messages"]):
#     print(f"[{i}] {type(msg).__name__}: {msg.content[:80]}")
#     if hasattr(msg, "tool_calls") and msg.tool_calls:
#         print(f"    -> 调了工具: {msg.tool_calls}")



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


async def main():
    # AsyncSqliteSaver 是异步版持久化 checkpointer，自动把每个 thread 的对话落盘到 checkpoints.db
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "user_001"}}  # 同一个 thread_id = 同一段记忆
        #
        # # 第一轮：正常提问
        # print("=== 第一轮 ===")
        # await stream_answer("查一下深圳现在的天气", graph, config)

        # 第二轮：问"刚才聊了什么"，验证记忆真的持久化了（同一 thread_id 才能读到历史）
        print("\n\n=== 第二轮（验证记忆持久化）===")
        await stream_answer("我刚才让你查了什么？", graph, config)


if __name__ == "__main__":
    asyncio.run(main())


# async def stream_answer(query: str):
#     async for chunk, metadata in graph.astream(
#         {"messages": [HumanMessage(content=query)]},
#         stream_mode="messages",
#     ):
#         if chunk.content:
#             for char in chunk.content:        # 把每个 chunk 再拆成单字
#                 print(char, end="", flush=True)
#                 await asyncio.sleep(0.03)      # 每字停 30ms，打字机感
#     print()
#
# if __name__ == "__main__":
#     asyncio.run(stream_answer("公司的差旅报销标准是什么"))

