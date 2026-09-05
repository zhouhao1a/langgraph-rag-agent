from typing import Optional
from pydantic import BaseModel


class ExecutionCreate(BaseModel):
      case_id: int
      status: str = "通过"
      remark: Optional[str] = None
