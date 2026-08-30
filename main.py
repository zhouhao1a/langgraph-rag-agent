from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.agent.agent import builder
from fastapi import Request
from fastapi.responses import JSONResponse
from app.models.base import init_db
from app.schemas.common import fail
from app.routers import chat, auth, projects, cases


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

app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(cases.router)




@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=fail(f"服务器内部错误：{exc}")
    )




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



