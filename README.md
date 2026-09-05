# LangGraph Agentic RAG 测试助手

基于 **LangGraph + DeepSeek** 构建的测试团队 AI 助手。支持 RAG 知识库检索、工具调用（ReAct 循环）、多轮对话记忆持久化、JWT 鉴权、对话落 MySQL 与流式输出，并封装了一层 **FastAPI 服务 + 前端演示页**，可直接在浏览器里对话。

> 📊 可观测性已接入：项目通过根目录 `.env` 中的 `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` 开启 LangSmith 链路追踪，框架自动读取并上报 trace，无需改代码。密钥仅存于本地 `.env`（已 gitignore），切勿提交或写进文档。

## 核心特性

- **Agentic RAG 管道（ReAct 循环）**：用户提问 → LLM 决策 → 工具调用 → 结果回传 → 生成答案，由 `tools_condition` 自动路由。
- **四类真实工具**：`calculator`（计算）、`search_kb`（知识库检索）、`get_weather`（实时天气）、`scrape_web`（网页爬取），均带异常处理与优雅降级。
- **向量知识库**：HuggingFace 本地 Embedding + Chroma 向量库，L2 距离阈值过滤做召回精筛；内置 14 段测试知识库（手机兼容性、缺陷管理、用例设计、接口测试、单元测试等），由 `app/ingest.py` 建库。
- **记忆持久化**：`AsyncSqliteSaver` 将对话落盘到 `checkpoints.db`，进程重启后多轮记忆不丢失，`thread_id` 隔离不同会话。
- **JWT 鉴权**：`/auth/register` 注册、`/auth/login` 登录签发 token（bcrypt 哈希密码 + PyJWT），受保护接口需携带 `Authorization: Bearer <token>`。
- **对话落 MySQL**：`/chat/once` 将 user / assistant 两条对话写入 MySQL（异步 SQLAlchemy + asyncmy），`/chat/history` 按 `thread_id` 查询历史。
- **统一响应格式**：所有接口返回 `{code, message, data}`，并配置全局异常处理器兜底。
- **分层架构**：`routers/`（路由）、`models/`（表）、`schemas/`（Pydantic）、`services/`（业务）、`core/`（配置/安全/依赖）。
- **测试管理平台（V1.8）**：项目/用例 CRUD、AI 生成用例（结构化输出）、执行记录、统计看板，所有数据按 `user.id` 多租户隔离。
- **质量保障**：pytest 单元测试（auth 密码/token、calculator 工具）+ RAG 评测集（24 条，阈值 0.9 下检索命中率 87.5%）。

## 系统架构

```mermaid
graph LR
    U[浏览器用户] --> F[index.html 演示前端]
    F -->|POST /chat/stream 或 /chat/once| API[FastAPI 控制层 main.py]
    API --> AUTH[JWT 鉴权 register/login]
    AUTH -->|校验 token| R[run_agent / builder LangGraph 图]
    R --> A[Agent 节点 LLM + bind_tools]
    A -->|tool_calls| T[Tools 节点]
    T -->|ToolMessage| A
    A -->|最终回答| R
    KB[(Chroma 向量库 chroma_db)] -.->|search_kb| T
    DB[(SQLite 记忆 checkpoints.db)] -.->|thread_id| R
    MY[(MySQL 对话记录)] -.->|/chat/once /chat/history| API
```

## 项目结构

```
langgraph_rag_agent/
├── main.py                 # FastAPI 入口：创建 app + lifespan + 中间件 + 挂载 routers + 异常处理
├── app/
│   ├── agent/              # Agent 相关
│   │   ├── agent.py        #   LangGraph 图定义 + run_agent + builder
│   │   ├── tools.py        #   四个 @tool：calculator / search_kb / get_weather / scrape_web
│   │   └── state.py        #   状态定义参考
│   ├── core/               # 配置、安全、依赖
│   │   ├── config.py       #   集中读 .env（DEEPSEEK/JWT/DB/RAG 阈值/HF 镜像）
│   │   ├── security.py     #   bcrypt + PyJWT（hash/verify/token）
│   │   └── deps.py         #   get_current_user 依赖
│   ├── models/             # SQLAlchemy 表（每个实体一个文件）
│   │   ├── base.py         #   Base + engine + SessionLocal + init_db
│   │   ├── user.py         #   用户表
│   │   ├── chat_history.py #   对话记录表
│   │   ├── project.py      #   项目表（V1.8）
│   │   ├── test_case.py    #   测试用例表（V1.8）
│   │   └── execution.py    #   执行记录表（V1.8）
│   ├── schemas/            # Pydantic 请求/响应模型
│   │   └── common.py       #   ok()/fail() 统一响应
│   ├── routers/            # API 路由（APIRouter）
│   │   ├── auth.py         #   /auth/register /auth/login
│   │   ├── chat.py         #   /chat/stream /chat/once /chat/history
│   │   ├── projects.py     #   /projects/*（V1.8）
│   │   ├── cases.py        #   /cases/*（V1.8）
│   │   ├── executions.py   #   /executions/*（V1.8）
│   │   └── dashboard.py    #   /dashboard/*（V1.8）
│   ├── services/           # 业务逻辑
│   │   └── case_generator.py  # AI 生成用例（V1.8）
│   └── ingest.py           # 建库脚本：data/knowledge.txt → 分块 → Embedding → Chroma
├── static/index.html       # 演示前端（登录/注册 + 聊天）
├── data/                   # knowledge.txt（知识库）+ eval_set.json（评测集）
├── tests/                  # pytest 测试：auth/tools/agent 单测 + 接口黑盒
├── eval_rag.py             # RAG 评测脚本：扫描阈值 → 命中率
├── requirements.txt        # 依赖清单
└── .env.example            # 环境变量模板
```

## 环境准备

1. 安装依赖（建议用 conda 环境 `langgraph`）：

   ```bash
   pip install -r requirements.txt
   ```

2. 在项目根目录创建 `.env`（参考 `.env.example`），关键变量：

   ```ini
   DEEPSEEK_API_KEY=你的_key
   DEEPSEEK_API_BASE=https://api.deepseek.com
   DB_URL=mysql+asyncmy://root:root@localhost:3306/langgraph_agent?charset=utf8mb4
   JWT_SECRET=你的随机密钥（建议 openssl rand -hex 32 生成）
   SEARCH_KB_THRESHOLD=0.9
   # 可选：LangSmith 链路追踪
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=你的_langsmith_key
   LANGSMITH_PROJECT=my_langgraph_agent
   ```

   > 首次启动会自动 `init_db()` 建 MySQL 表（User / ChatHistory / Project / TestCase / Execution）。

3. 构建知识库（首次运行或更新语料后执行）：

   ```bash
   python app/ingest.py
   ```

   > Embedding 走 HuggingFace 本地模型（`BAAI/bge-small-zh-v1.5`），镜像 `https://hf-mirror.com` 已集中在 `app/core/config.py`。

## 运行

```bash
uvicorn main:app --reload --port 8000
# 或
python main.py
```

启动后浏览器打开 **http://127.0.0.1:8000**，先注册/登录，再进入聊天。

## API 接口

统一响应格式：`{"code": 0, "message": "success", "data": {...}}`（`code=0` 成功，非 0 失败）。

| 方法 | 路径 | 鉴权 | 说明 | 请求体 |
| ---- | ---- | ---- | ---- | ---- |
| POST | `/auth/register` | 否 | 注册用户 | `{"username": "...", "password": "..."}` |
| POST | `/auth/login` | 否 | 登录，返回 `data.token` | 同上 |
| POST | `/chat/stream` | **是** | SSE 流式输出，逐 token | `{"query": "...", "thread_id": "..."}` |
| POST | `/chat/once` | **是** | 非流式一次性返回 + 落 MySQL | 同上 |
| GET | `/chat/history` | **是** | 按 thread_id 查历史对话 | query 参数 `?thread_id=...` |
| POST | `/projects` | **是** | 新建项目 | `{"name", "description"?, "status"?}` |
| GET | `/projects` | **是** | 项目列表（分页） | `?page=&page_size=` |
| GET | `/projects/{id}` | **是** | 项目详情 | — |
| PUT | `/projects/{id}` | **是** | 更新项目 | `{"name"?,"description"?,"status"?}` |
| DELETE | `/projects/{id}` | **是** | 删除项目 | — |
| POST | `/cases` | **是** | 新建用例 | `{"project_id","title","module"?,"priority"?,"type"?,...}` |
| GET | `/cases` | **是** | 用例列表（分页 + 按项目过滤） | `?page=&page_size=&project_id=` |
| GET | `/cases/{id}` | **是** | 用例详情 | — |
| PUT | `/cases/{id}` | **是** | 更新用例 | 字段可选 |
| DELETE | `/cases/{id}` | **是** | 删除用例 | — |
| POST | `/cases/generate` | **是** | AI 生成用例并入库 | `{"project_id","requirement","count"?}` |
| POST | `/executions` | **是** | 记录一次执行 | `{"case_id","status"?,"remark"?}` |
| GET | `/executions` | **是** | 执行历史（分页 + 按用例过滤） | `?case_id=&page=&page_size=` |
| GET | `/dashboard/overview` | **是** | 统计看板（项目/用例/优先级/来源/执行通过率） | — |
| GET | `/` | 否 | 同源托管前端页面 | — |

鉴权示例（先登录拿 token，再访问受保护接口）：

```bash
# 登录
curl.exe -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"zhouhao","password":"123456"}'

# 带 token 调用 /chat/once
curl.exe -X POST http://127.0.0.1:8000/chat/once \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query":"帮我查测试规范","thread_id":"session_001"}'
```

## 测试与评测

```bash
# 单元测试
pytest tests/test_auth.py tests/test_tools.py -v

# RAG 评测（扫描不同阈值，输出命中率对比）
python eval_rag.py
```

评测结果（24 条评测集）：阈值 0.5→12.5%、0.7→54.2%、**0.9→87.5%**、1.0→91.7%，选定 0.9 作为召回与精度的平衡点。

## 关键设计点

- **ReAct 循环**：`builder` 用 `StateGraph(MessagesState)` 搭图，`agent` 节点调用 `llm_with_tools`，`tools_condition` 决定继续调工具还是结束。
- **流式实现引擎是 `yield`**：`run_agent` 是异步生成器，过滤掉 HumanMessage / ToolMessage，只把 AI 文本 chunk 透传给 SSE。
- **记忆按线程隔离**：同一个 `thread_id` 在 `AsyncSqliteSaver` 中对应同一段历史，多轮上下文不丢失。
- **lifespan 复用图**：服务启动时编译一次图存 `app.state.graph`，接口复用，不再每请求重编译。
- **路由分层**：`main.py` 只做 app 创建 + `include_router` 挂载，各模块路由独立在 `routers/`，用 `APIRouter` 避免循环导入。
- **防幻觉两层过滤**：向量分数粗筛（L2 阈值）+ 系统提示强制"先 `search_kb` 再回答，禁止凭记忆编造"。

## 可观测性（已接入 LangSmith）

通过环境变量接入，无需代码改动——只要 `.env` 里存在以下变量，框架自动上报 trace：

```ini
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=你的_langsmith_key
LANGSMITH_PROJECT=my_langgraph_agent
```

配置正确后，每次对话都在 LangSmith 看板生成完整调用链路，含每轮工具调用的入参、出参与耗时。

## 待做

- 401 返回的是 FastAPI 默认 `{"detail": ...}`，未统一进 `{code, message, data}`。
- 聊天历史未按用户隔离：`ChatHistory` 无 `user_id` 字段，`/chat/history` 只按 thread_id 查（计划 V2.0 加 user 维度）。
