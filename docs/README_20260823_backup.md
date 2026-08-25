# LangGraph Agentic RAG 测试助手

基于 **LangGraph + DeepSeek** 构建的测试团队 AI 助手。支持 RAG 知识库检索、工具调用（ReAct 循环）、多轮对话记忆持久化与流式输出，并通过 LangSmith 做调用链路观测。

## 核心特性

- **Agentic RAG 管道**：用户提问 → LLM 决策 → 工具调用 → 结果回传 → 生成答案，完整 ReAct 循环
- **四类真实工具**：`calculator`（计算）、`search_kb`（知识库检索）、`get_weather`（实时天气）、`scrape_web`（网页爬取），均带异常处理与优雅降级
- **向量知识库**：HuggingFace 本地 Embedding + Chroma 向量库，L2 距离阈值过滤（0.9）做召回精筛
- **记忆持久化**：`AsyncSqliteSaver` 将对话落盘到 SQLite，进程重启后多轮记忆不丢失（`thread_id` 隔离会话）
- **流式输出**：`astream(stream_mode="messages")` 逐 token 输出，区分 AIMessage / ToolMessage
- **可观测性**：接入 LangSmith，完整 trace 每次工具调用的输入输出与耗时

## 系统架构

```mermaid
graph LR
    U[用户问题] --> A[Agent 节点<br/>LLM + bind_tools]
    A -->|tool_calls| T[Tools 节点]
    T -->|ToolMessage| A
    A -->|最终回答| U
    KB[(Chroma 向量库)] -.->|search_kb| T
    DB[(SQLite 记忆<br/>checkpoints.db)] -.->|thread_id| A
