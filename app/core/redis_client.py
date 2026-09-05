import redis.asyncio as aioredis
from app.core.config import REDIS_URL

# decode_responses=True：get 出来是 str 不是 bytes，缓存 JSON 字符串方便
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)