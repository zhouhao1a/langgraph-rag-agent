
from fastapi.security import OAuth2PasswordBearer

from app.core.security import verify_token
from app.models.base import SessionLocal
from sqlalchemy import select

from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

from fastapi import Depends, HTTPException


"""
他的作用是鉴权防护，还会返回user对象给你使用
"""
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)  # 过期/伪造会抛异常
    except Exception:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    user_id = int(payload["sub"])
    # 查库确认用户还在（被删号的 token 也失效）
    async with SessionLocal() as session:
        user = (
            await session.execute(
            select(User).where(User.id == user_id)
        )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user