import asyncio
import os
from dotenv import load_dotenv
from lark_channel import FeishuChannel
from app.agent.agent import run_agent, builder
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

load_dotenv()
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

# 初始化长连接通道
channel = FeishuChannel(
    app_id=APP_ID,
    app_secret=APP_SECRET
)

# 全局图：启动时编译一次，复用（和后端 main.py 的 lifespan 一样）
graph = None


async def on_message(msg):
    """收到消息后的完整处理流程"""
    print("=" * 50)
    print("✅收到飞书消息")

    # lark_channel 已经帮你解析好了，直接取属性
    user_text = msg.content_text
    sender_open_id = msg.sender_id
    chat_type = msg.chat_type
    chat_id = msg.chat_id

    print(f"用户ID: {sender_open_id}")
    print(f"聊天类型: {chat_type}")
    print(f"用户提问: {user_text}")

    # 群聊没有@机器人就跳过
    if chat_type == "group" and not msg.is_mentioned:
        print("群消息没有@机器人，跳过")
        return

    # ========== 调用 LangGraph-RAG Agent ==========
    print("\n🤖 正在调用LangGraph-RAG智能体...")
    full_answer = ""
    try:
        async for chunk in run_agent(
                user_query=user_text,
                thread_id=sender_open_id,  # 每个用户一条记忆线
                user_id=sender_open_id,  # open_id 当 user_id 做多用户隔离
                graph=graph,  # 复用预编译图，别用 None
        ):
            if chunk.content:
                full_answer += chunk.content
    except Exception as e:
        full_answer = f"⚠️ Agent处理出错: {str(e)}"
        print(f"❌ Agent报错: {e}")

    print(f"\n📝 完整回复: {full_answer}")

    # ========== 发送回复给飞书用户 ==========
    try:
        await channel.send(
            chat_id,
            {"text": full_answer}
        )
        print("✅回复消息发送成功")
    except Exception as e:
        print(f"❌发送回复失败: {e}")

    print("=" * 50)


# 注册消息事件
channel.on("message", on_message)


async def main():
    global graph
    # 启动时编译一次图，并让 checkpointer 保持打开直到 bot 退出
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        print("✅ 图编译完成，飞书机器人长连接启动，等待消息...")
        await channel.connect()  # 阻塞运行，期间 checkpointer 保持打开


if __name__ == "__main__":
    asyncio.run(main())