from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from app.core.deps import get_current_user
from app.models.base import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.execution import ExecutionRecord
from app.schemas.common import ok

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview(user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        # 项目总数（只看自己的）
        project_total = (await session.execute(
            select(func.count()).select_from(Project).where(Project.owner_id == user.id)
        )).scalar()

        # 用例总数
        case_total = (await session.execute(
            select(func.count()).select_from(TestCase).where(TestCase.created_by == user.id)
        )).scalar()

        # 按优先级分组（GROUP BY 三件套 + 元组转 dict）
        by_priority = {p: c for p, c in (await session.execute(
            select(TestCase.priority, func.count())
            .where(TestCase.created_by == user.id).group_by(TestCase.priority)
        )).all()}

        # 按类型分组
        by_type = {t: c for t, c in (await session.execute(
            select(TestCase.type, func.count())
            .where(TestCase.created_by == user.id).group_by(TestCase.type)
        )).all()}

        # 按来源分组
        by_source = {s: c for s, c in (await session.execute(
            select(TestCase.source, func.count())
            .where(TestCase.created_by == user.id).group_by(TestCase.source)
        )).all()}

        # 最近 5 条用例
        recent_rows = (await session.execute(
            select(TestCase).where(TestCase.created_by == user.id)
            .order_by(TestCase.id.desc()).limit(5)
        )).scalars().all()
        recent_cases = [{"id": c.id, "title": c.title, "project_id": c.project_id}
                        for c in recent_rows]

        # 执行统计（可选，注意防除零）
        exec_total = (await session.execute(
            select(func.count()).select_from(ExecutionRecord)
            .where(ExecutionRecord.executed_by == user.id)
        )).scalar()
        exec_passed = (await session.execute(
            select(func.count()).select_from(ExecutionRecord)
            .where(ExecutionRecord.executed_by == user.id,
                   ExecutionRecord.status == "通过")
        )).scalar()
        exec_pass_rate = round(exec_passed / exec_total * 100, 1) if exec_total else 0

    return ok({
        "project_total": project_total, "case_total": case_total,
        "by_priority": by_priority, "by_type": by_type, "by_source": by_source,
        "recent_cases": recent_cases,
        "exec_total": exec_total, "exec_passed": exec_passed,
        "exec_pass_rate": exec_pass_rate,
    })