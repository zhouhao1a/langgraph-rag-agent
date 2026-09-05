import os
from dotenv import load_dotenv

load_dotenv()

# ===== DeepSeek（大模型）=====
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE")

# ===== JWT 鉴权 =====
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")  # 上线前换 openssl rand -hex 32
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

# ===== 数据库 =====
DB_URL = os.getenv("DB_URL")

# ===== RAG 检索阈值（L2 距离，越小越严格）=====
SEARCH_KB_THRESHOLD = float(os.getenv("SEARCH_KB_THRESHOLD", "0.9"))

# ===== HuggingFace 镜像（国内直连）=====
HF_ENDPOINT = "https://hf-mirror.com"
os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)  # huggingface_hub 读的是环境变量，顺手设进去

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")