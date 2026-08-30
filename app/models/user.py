from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.models.base import Base


class User(Base):
    __tablename__ = "user"
    id = Column(Integer,primary_key=True,autoincrement=True)
    username = Column(String(50),unique=True,index=True) #unique唯一约束不能重复
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.now)
