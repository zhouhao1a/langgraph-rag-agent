from fastapi import Depends, APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select
from starlette.responses import StreamingResponse
from app.agent.agent import run_agent
from app.core.deps import get_current_user
from app.models.base import SessionLocal
from app.models.chat_history import ChatHistory
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.schemas.common import ok

router = APIRouter()


@router.post("/chat/stream")
async def chat(req: ChatRequest, request: Request, user:User=Depends(get_current_user)):
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
       async for chunk in run_agent(req.query,req.thread_id,graph=request.app.state.graph):
# 把拿到的小块数据包装成SSE规定格式往前端发
            yield f"data: {chunk.content}\n\n"
# SSE流式响应，实现打字输出效果
    return StreamingResponse(stream_generator(), media_type="text/event-stream")


# ===== 新增：非流式合并输出接口 =====



@router.post("/chat/once")
async def chat_once(req: ChatRequest, request: Request, user:User=Depends(get_current_user)):
        full_answer = ""
        async for chunk in run_agent(req.query, req.thread_id,graph=request.app.state.graph):
                full_answer += chunk.content
        async with SessionLocal() as session:
            session.add(ChatHistory(thread_id=req.thread_id,role="user",content=req.query))
            session.add(ChatHistory(thread_id=req.thread_id, role="assistant", content=full_answer))
            await session.commit()         #给表加参数要按顺序不能并行
        # raise Exception("测试异常")
        return ok({"answer": full_answer})

@router.get("/chat/history")
async def chat_history(thread_id: str,user:User=Depends(get_current_user)):
      async with SessionLocal() as session:
          result = await session.execute(
                select(ChatHistory).where(ChatHistory.thread_id ==
  thread_id).order_by(ChatHistory.id)
          )
          rows = result.scalars().all()
      return ok({"messages": [{"role": r.role, "content": r.content} for r in rows]})

