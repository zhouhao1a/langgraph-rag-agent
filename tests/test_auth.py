import sys
from pathlib import Path

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.security import (
    hash_password, verify_password,
    create_token, verify_token,
    SECRET_KEY, ALGORITHM,
)


# ===== 密码：正例 + 反例 =====
def test_hash_then_verify_ok():
    hashed = hash_password("123456")
    assert verify_password("123456", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("123456")
    assert verify_password("wrong", hashed) is False


def test_hash_is_salted():
    # 同一密码两次哈希结果不同（bcrypt 随机盐），但都能验证通过
    h1 = hash_password("123456")
    h2 = hash_password("123456")
    assert h1 != h2
    assert verify_password("123456", h1) is True
    assert verify_password("123456", h2) is True


# ===== token：正例 + 反例 =====
def test_token_roundtrip():
    token = create_token(7)
    payload = verify_token(token)
    assert payload["sub"] == "7"


def test_token_tampered():
    token = create_token(1)
    tampered = token[:-1] + ("0" if token[-1] != "0" else "1")  # 改最后一位
    with pytest.raises(jwt.InvalidTokenError):
        verify_token(tampered)


def test_token_expired():
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY, algorithm=ALGORITHM,
    )
    with pytest.raises(jwt.InvalidTokenError):
        verify_token(expired)