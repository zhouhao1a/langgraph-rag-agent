import json, re
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.core.config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE
from app.schemas.case import GenerateResult

SYSTEM_PROMPT =  """你是资深测试工程师。根据用户需求设计测试用例，要求：
1. 覆盖正常流程、异常输入、边界值；
2. priority 只能取 P0/P1/P2/P3（P0 最高，与阻断性缺陷相关）；
3. steps 用换行分隔多个步骤；type 只能取 功能/接口/兼容/性能。
4. 每条用例的 title、module、priority、precondition、steps、expected、type 必须全部填写；
   module 不能为空；没有前置条件就写"无"。
5. 只输出结构化结果，不要解释。"""

def _llm():
    return ChatOpenAI(model="deepseek-chat",
                      api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE,
                      temperature=0.3)

def generate_cases(requirement: str, count: int = 5) -> list[dict]:
    llm = _llm().with_structured_output(GenerateResult)
    result = llm.invoke([
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(f"【需求】\n{requirement}\n\n请生成 {count} 条测试用例。"),
    ])
    return [c.model_dump() for c in result.cases]

def generate_cases_fallback(requirement: str, count: int = 5) -> list[dict]:
    """兜底：结构化输出失败时走纯文本 + 手工解析"""
    resp = _llm().invoke([
        SystemMessage(SYSTEM_PROMPT + "\n以 JSON 输出 {\"cases\":[...]}"),
        HumanMessage(f"【需求】\n{requirement}\n\n请生成 {count} 条测试用例。"),
    ])
    text = re.sub(r"```(?:json)?", "", resp.content)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("LLM 没输出合法 JSON")
    return json.loads(text[start:end+1])["cases"]