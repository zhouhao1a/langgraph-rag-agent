import sys
from pathlib import Path

# 往上回退两层，回到项目根目录
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))
import requests

BASE_URL = "http://127.0.0.1:8000"
# 接口测试，黑盒测试
def test_normal_chat():
    """测试正常对话，验证接口通、结果不为空"""
    url = f"{BASE_URL}/chat/stream"
    payload = {
        "query": "你好",
        "thread_id": "test_001"
    }
    # stream=True 开启流式
    resp = requests.post(url, json=payload, stream=True)

    # ----------断言1：状态码必须200----------
    assert resp.status_code == 200, f"接口异常！状态码:{resp.status_code}"

    # 收集分片
    full_text = ""
    for line in resp.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data:"):
                chunk = decoded.removeprefix("data: ")
                full_text += chunk

    # ----------断言2：最终回答不能为空----------
    assert len(full_text) > 0, "返回内容是空的！"

    print("✅测试通过，完整回答：", full_text)


def test_weather_query():
    """测试查天气，断言结果里面包含关键词"""
    url = f"{BASE_URL}/chat/stream"
    payload = {
        "query": "查询深圳天气",
        "thread_id": "test_002"
    }
    resp = requests.post(url, json=payload, stream=True)
    assert resp.status_code == 200

    full_text = ""
    for line in resp.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data:"):
                chunk = decoded.removeprefix("data: ")
                full_text += chunk

    # ----------断言3：回答里面要有气温/天气关键词----------
    keyword_list = ["温度","°C","天气"]
    hit = any(key in full_text for key in keyword_list)
    assert hit, f"回答没有天气相关内容！返回:{full_text}"


def test_missing_threadid():
    """异常用例：不传thread_id，应该返回422参数错误"""
    url = f"{BASE_URL}/chat/stream"
    payload = {
        "query": "你好"
        # 故意少写thread_id
    }
    resp = requests.post(url, json=payload)
    # FastAPI缺少必填字段返回422
    assert resp.status_code == 422

