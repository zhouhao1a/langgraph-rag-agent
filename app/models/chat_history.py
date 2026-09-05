from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Column, ForeignKey

from app.models.base import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"
    user_id=Column(Integer,ForeignKey("user.id"),index=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(64), index=True)
    role = Column(String(16))  # user / assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)