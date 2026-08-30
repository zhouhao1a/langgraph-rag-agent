from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Column, ForeignKey

from app.models.base import Base


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20),default="进行中")
    owner_id = Column(Integer,ForeignKey("user.id"),index=True)
    created_at = Column(DateTime, default=datetime.now)