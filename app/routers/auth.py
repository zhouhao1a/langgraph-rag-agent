from pydantic import BaseModel
from sqlalchemy import select

from app.core.security import hash_password, verify_password, create_token
from app.models.base import SessionLocal
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.common import fail, ok
from fastapi import APIRouter

router = APIRouter()


@router.post("/auth/register")
async def register(req: RegisterRequest):
  async with SessionLocal() as session:
      exists = (await session.execute(select(User).where(User.username ==
req.username))).scalar_one_or_none()
      if exists:
          return fail("用户名已存在")
      session.add(User(username=req.username,
password_hash=hash_password(req.password)))
      await session.commit()
  return ok({"username": req.username})

@router.post("/auth/login")
async def login(req: RegisterRequest):
  async with SessionLocal() as session:
      user = (await session.execute(select(User).where(User.username ==
req.username))).scalar_one_or_none()
      if not user or not verify_password(req.password, user.password_hash):
          return fail("用户名或密码错误")
  return ok({"token": create_token(user.id)})