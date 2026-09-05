from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Column, ForeignKey

from app.models.base import Base


class ExecutionRecord(Base):
    __tablename__ = "execution_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("test_case.id"), index=True)
    status = Column(String(20), default="通过")  # 通过/失败/执行中
    remark = Column(Text)  # 执行备注
    executed_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime, default=datetime.now)