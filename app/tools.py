import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from simpleeval import simple_eval

hugging = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

@tool
def calculator(expression:str)->str:
    """
    对数学表达式进行计算，比如 500*3、1200/4
    """
    try:
        result = simple_eval(expression)
        return str(result)
    except Exception as e:
        return f"计算失败：{str(e)}"


@tool
def search_kb(query: str) -> str:
        """
         对于知识方面的问题，要先去rag库检索
         """
        # 【在线检索】
        # 第 1 小步：加载已有的向量库
        vectorstore = Chroma(
            persist_directory="./chroma_db",  # 从哪个文件夹加载
            embedding_function=hugging  # 告诉它查询时用哪个模型把用户的问题转向量
        )
        # 检索，将用户的问题和转化成向量，在与库的文件比对向量比
        result = vectorstore.similarity_search_with_score(
            query=query,  # 用户的问题
            k=4  # 返回向量比距离最近的最多k个代码块
        )
        # for doc, score in result:  # ← 从这行到下面两行是观测点
        #     print(f"[search_kb] L2={score:.3f} | {doc.page_content[:30]}")
        filtered = [doc for doc, score in result if score < 0.9]  # ③ 过滤
        if not filtered:
            return "知识库中没有找到相关内容"
        return "\n".join(doc.page_content for doc in filtered)

# 查天气真数据
@tool
def get_weather(city: str) -> str:
    """查询指定城市的实时天气信息，用户问天气、温度、下雨等问题时使用"""
    r = requests.get(
        f"https://wttr.in/{city}",
        params={"format": "j1"},   # 返回JSON而不是默认的ASCII天气图
        timeout=10,                # 最多等10秒，防止网络卡死拖住整个Agent
    )
    cur = r.json()["current_condition"][0]
    desc = cur["lang_zh"][0]["value"] if "lang_zh" in cur else cur["weatherDesc"][0]["value"]
    return f"{city}当前：{desc}，气温{cur['temp_C']}°C，体感{cur['FeelsLikeC']}°C，湿度{cur['humidity']}%"

# 爬取网页内容真数据
@tool
def scrape_web(url: str) -> str:
    """爬取指定网页的内容，用户需要获取某个网页信息时使用"""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()    #raise_for_status() 管“服务器拒绝”，except RequestException 管“根本连不上”，timeout 管“连上但不说话”——三兄弟各管一段。
        r.encoding = r.apparent_encoding   # 自动检测网页真实编码，防止中文乱码
        soup = BeautifulSoup(r.text, "html.parser")
    # 粗清洗：整棵砍掉与正文无关的标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:3000]  # 截断，防止超长网页撑爆LLM上下文
    except requests.RequestException as e:  # ← requests 所有网络异常的基类，一个 except 全兜住
        return f"网页抓取失败：{e}"            # ← 返回字符串而不是抛异常，LLM 能看到并告诉用户

