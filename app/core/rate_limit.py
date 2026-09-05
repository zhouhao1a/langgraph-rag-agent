from fastapi import Depends, HTTPException
from app.core.redis_client import redis_client
from app.core.deps import get_current_user
from app.models.user import User


def make_rate_limit(scope: str, limit: int, window: int = 60):
    """返回一个针对不同接口、不同频次的限流依赖"""

    async def _rate_limit(user: User = Depends(get_current_user)):
        key = f"rate:{scope}:{user.id}"
        current = await redis_client.incr(key)  # 原子自增，第一次自动建 key=1
        if current == 1:
            await redis_client.expire(key, window)  # 只在第一次设过期，防窗口被重置
        if current > limit:
            raise HTTPException(status_code=429, detail="请求太频繁，请稍后再试")
        return user

    return _rate_limit


rate_limit_chat = make_rate_limit("chat", limit=5)  # 聊天 10次/分钟
rate_limit_generate = make_rate_limit("generate", limit=5)  # AI生成用例 5次/分钟