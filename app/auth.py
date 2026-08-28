import os
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from sqlalchemy import select

from app.db import SessionLocal, User

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")   # 生产必须换强密钥
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str) -> str:
  # bcrypt 每次 gensalt() 不同 → 同密码哈希结果也不同，但都能验证
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()    #encode-->decode 二进制转成字符串

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def create_token(user_id: int) -> str:
    payload = {
      "sub": str(user_id),   # sub = subject，放用户标识
      "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])   # 过期/伪造会抛异常

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

from fastapi import Depends, HTTPException

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