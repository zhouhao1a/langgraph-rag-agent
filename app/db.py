from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import os
DB_URL = os.getenv("DB_URL")


class Base(DeclarativeBase):
    pass
class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(64), index=True)
    role = Column(String(16))  # user / assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# 创建异步引擎：相当于打开一条通往MySQL的通道
engine = create_async_engine(DB_URL, echo=True)

# 创建会话工厂：以后每次读写数据库，就从这里拿一个会话
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
"""
##Base内部是同步函数，要把同步函数放到异步链接桥接方法里执行
sqlalchemy内部方法会自动查询数据库有没有表，没有就创建
这样以后创表就可以继承base表，然后执行initdb自动建表了
"""
