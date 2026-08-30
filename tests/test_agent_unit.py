import sys
from pathlib import Path

# 往上回退两层，回到项目根目录
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
# 单元测试，白盒测试
import pytest
from app.agent.agent import run_agent



@pytest.mark.asyncio
async def test_agent_normal_chat():
    """普通闲聊，不需要调用工具"""
    answer=""
    async for chunk in run_agent("你好","unit_001"):
        answer+=chunk.content
        assert len(answer)> 0



@pytest.mark.asyncio
async def test_agent_weather_tool():
    """测试Agent能否正确调用天气工具"""
    answer =""
    async for chunk in run_agent("查一下深圳现在天气", "unit_002"):
        answer+=chunk.content
    keywords = ["深圳", "°C", "温度", "天气"]
    hit = any(word in answer for word in keywords)
    assert hit, f"天气查询失败，返回内容：{answer}"


@pytest.mark.asyncio
async def test_agent_memory():
    """测试会话记忆持久化"""
    tid = "mem_003"
    answer = ""
    async for chunk in run_agent("我的名字叫小郭", tid):
        answer+=chunk.content
    async for chunk in run_agent("我叫什么名字", tid):
        answer += chunk.content
    assert "小郭" in answer, "记忆失效，Agent忘记名字"


@pytest.mark.asyncio
async def test_agent_calulator():
    """测试agent是否能使用计算器"""
    answer=""
    async for chunk in run_agent("2的10次方","unit004"):
        answer+=chunk.content
    assert "1024" in answer,"计算错误垃圾"
