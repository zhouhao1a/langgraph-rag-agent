from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select


from app.agent import run_agent, builder
from fastapi import Request
from fastapi.responses import JSONResponse

from app.db import init_db
from app.db import SessionLocal, ChatHistory


# 定义fastapi生命周期，防止一直反复编译浪费资源
@asynccontextmanager
async def lifespan(app:FastAPI):
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        app.state.graph = builder.compile(checkpointer=checkpointer)
        print("已编译图")
        await init_db()
        yield



app = FastAPI(title="Agent后端请求",lifespan=lifespan)
#定义前端传过来的参数是什么类型，前端穿两个值，一个提问，一个记忆id
class ChatRequest(BaseModel):
    query: str
    thread_id: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=fail(f"服务器内部错误：{exc}")
    )


def ok(data=None,message="success",code=0):
    return {"code":code,"message":message,"data":data}

def fail(message="message",code=1):
    return {"code":code,"message":message,"data":None}

@app.post("/chat/stream")
async def chat(req: ChatRequest):
    """
        接收前端POST ，前端会传一个json格式的post
        json:
        {
          "query":"帮我查测试规范",
          "thread_id":"session_001"
        }
        返回SSE流式数据，对应agent.astream分片
        """

# 定义一个函数（生成器），循环拿agent吐出的一小块一小块chunk数据
    async def stream_generator():
       async for chunk in run_agent(req.query,req.thread_id,graph=app.state.graph):
# 把拿到的小块数据包装成SSE规定格式往前端发
            yield f"data: {chunk.content}\n\n"
# SSE流式响应，实现打字输出效果
    return StreamingResponse(stream_generator(), media_type="text/event-stream")


# ===== 新增：非流式合并输出接口 =====



@app.post("/chat/once")
async def chat_once(req: ChatRequest):
        full_answer = ""
        async for chunk in run_agent(req.query, req.thread_id,graph=app.state.graph):
                full_answer += chunk.content
        async with SessionLocal() as session:
            session.add(ChatHistory(thread_id=req.thread_id,role="user",content=req.query))
            session.add(ChatHistory(thread_id=req.thread_id, role="assistant", content=full_answer))
            await session.commit()         #给表加参数要按顺序不能并行
        # raise Exception("测试异常")
        return ok({"answer": full_answer})

@app.get("/chat/history")
async def chat_history(thread_id: str):
      async with SessionLocal() as session:
          result = await session.execute(
                select(ChatHistory).where(ChatHistory.thread_id ==
  thread_id).order_by(ChatHistory.id)
          )
          rows = result.scalars().all()
      return ok({"messages": [{"role": r.role, "content": r.content} for r in rows]})


# 防止被浏览器“跨域”拦掉
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.responses import FileResponse
import os

# 负责前端启动不是在直接打开html，可以直接访问127.0.0.1:8000
@app.get("/")
async def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static/index.html"))


# 4. 运行服务的入口（unicorn.run，启动服务）
if __name__ == "__main__":
    import uvicorn
    # **uvicorn 是 ASGI 服务器**，FastAPI 本身只是 web 框架，不能直接接收网络请求；必须靠 uvicorn 来跑，处理 TCP 连接、http 请求、异步事件循环。

    uvicorn.run(app, host="0.0.0.0", port=8000)



