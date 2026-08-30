from typing import Optional
from pydantic import BaseModel      # （输入校验用Pydantic）：


class CaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "进行中"


class CaseUpdate(BaseModel):
    name: Optional[str] = None       #这里为什么要加optional，为什么这三个变量都可以设置为空
    description: Optional[str] = None
    status: Optional[str] = None