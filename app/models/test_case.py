from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Column, ForeignKey

from app.models.base import Base


class TestCase(Base):
    __tablename__ = "test_case"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"),index=True)
    title = Column(String(200), nullable=False)
    module = Column(String(100))
    priority = Column(String(10), default="P1")
    precondition = Column(Text)
    steps = Column(Text)
    expected = Column(Text)
    type = Column(String(20),default="功能")
    source = Column(String(20),default="手工")
    created_by = Column(Integer,ForeignKey("user.id"))
    created_at = Column(DateTime, default=datetime.now)