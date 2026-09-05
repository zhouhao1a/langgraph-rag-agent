from typing import Optional, Literal
from pydantic import BaseModel, Field  # （输入校验用Pydantic）：


class CaseCreate(BaseModel):
    project_id: int
    title: str
    module: Optional[str] = None
    priority: str = "P1"
    precondition: Optional[str] = None
    steps: Optional[str] = None
    expected: Optional[str] = None
    type: str = "功能"

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    module: Optional[str] = None
    priority: Optional[str] = None
    precondition: Optional[str] = None
    steps: Optional[str] = None
    expected: Optional[str] = None
    type: Optional[str] = None

class GenerateRequest(BaseModel):
    project_id: int
    requirement: str
    count: int = 5


class GeneratedCase(BaseModel):
    title: str = Field(description="用例标题")
    module: str = Field(description="所属模块")
    priority: Literal["P0", "P1", "P2", "P3"]
    precondition: str = Field(description="前置条件，没有就写'无'")
    steps: str = Field(description="多步用换行分隔")
    expected: str
    type: Literal["功能", "接口", "兼容", "性能"]

class GenerateResult(BaseModel):
    cases: list[GeneratedCase]