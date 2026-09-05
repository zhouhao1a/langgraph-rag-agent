from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from app.core.deps import get_current_user
from app.models.base import SessionLocal
from app.models.test_case import TestCase
from app.models.user import User
from app.models.execution import ExecutionRecord
from app.schemas.execution import ExecutionCreate
from app.schemas.common import ok, fail

router = APIRouter(prefix="/executions", tags=["executions"])


def to_dict(e: ExecutionRecord):
    return {"id": e.id, "case_id": e.case_id, "status": e.status,
            "remark": e.remark, "executed_by": e.executed_by,
            "created_at": str(e.created_at)}


# 记录一次执行（POST，只增不改）
@router.post("")
async def create_execution(req: ExecutionCreate, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        case = (await session.execute(
            select(TestCase).where(TestCase.id == req.case_id, TestCase.created_by == user.id)
        )).scalar_one_or_none()
        if not case:
            return fail("用例不存在")
        e = ExecutionRecord(case_id=req.case_id, status=req.status,
                            remark=req.remark, executed_by=user.id)
        session.add(e)
        await session.commit()
        await session.refresh(e)
    return ok(to_dict(e))


# 查执行历史（GET，按 case_id 过滤 + 分页）
@router.get("")
async def list_executions(case_id: int = None, page: int = 1, page_size: int = 10,
                          user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        q = select(ExecutionRecord).where(ExecutionRecord.executed_by == user.id)
        if case_id:
            q = q.where(ExecutionRecord.case_id == case_id)
        total = (await session.execute(
            select(func.count()).select_from(q.subquery())
        )).scalar()
        rows = (await session.execute(
            q.order_by(ExecutionRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
    return ok({"items": [to_dict(e) for e in rows], "total": total,
               "page": page, "page_size": page_size})