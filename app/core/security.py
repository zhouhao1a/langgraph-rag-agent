from datetime import datetime, timedelta, timezone
import jwt
import bcrypt

from app.core.config import TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET


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
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])   # 过期/伪造会抛异常
