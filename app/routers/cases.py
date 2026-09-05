from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit_generate
from app.models.base import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.case import CaseCreate, CaseUpdate, GenerateRequest
from app.schemas.common import ok, fail
from app.services.case_generator import generate_cases as gen_cases, \
    generate_cases_fallback as gen_cases_fb

router = APIRouter(prefix="/cases", tags=["cases"])


def to_dict(c: TestCase):
    return {"id": c.id, "project_id": c.project_id, "title": c.title,
            "module": c.module, "priority": c.priority, "precondition": c.precondition,
            "steps": c.steps, "expected": c.expected, "type": c.type,
            "source": c.source, "created_by": c.created_by, "created_at": str(c.created_at)}


"""
scalar_one_or_none()
数据库查询结果拿到之后，处理返回值，3 种结局：

1. **查到 1 条匹配的数据** → 返回 `Project` ORM 对象（项目实体）
2. **一条都没查到** → 返回 `None`
3. **查到≥2 条** → 直接抛出异常报错，防止重复脏数据
"""
@router.post("")
async def create_case(req: CaseCreate, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        proj = (await session.execute(select(Project).where(
            Project.id == req.project_id, Project.owner_id == user.id))).scalar_one_or_none()
        if not proj:
            return fail("项目不存在")
        c = TestCase(project_id=req.project_id, title=req.title, module=req.module,
                     priority=req.priority, precondition=req.precondition,
                     steps=req.steps, expected=req.expected, type=req.type,
                     source="手工", created_by=user.id)
        session.add(c)
        await session.commit()
        await session.refresh(c)    #刷新对象，从数据库拉取最新数据
    return ok(to_dict(c))



@router.get("")
async def list_cases(page: int = 1, page_size: int = 10, project_id: int = None,
                     user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        q = select(TestCase).where(TestCase.created_by == user.id)
        if project_id:
            q = q.where(TestCase.project_id == project_id)
        total = (await session.execute(
            select(func.count()).select_from(q.subquery())
        )).scalar()
        rows = (await session.execute(
            q.order_by(TestCase.id.desc()).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
    return ok({"items": [to_dict(c) for c in rows], "total": total,
               "page": page, "page_size": page_size})


@router.get("/{case_id}")
async def get_case(case_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        c = (await session.execute(select(TestCase).where(TestCase.id == case_id, TestCase.created_by == user.id))).scalar_one_or_none()
    if not c:
        return fail("用例不存在")
    return ok(to_dict(c))


@router.put("/{case_id}")
async def update_case(case_id: int, req: CaseUpdate, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        c = (await session.execute(select(TestCase).where(TestCase.id == case_id, TestCase.created_by == user.id))).scalar_one_or_none()
        if not c:
            return fail("用例不存在")
        if req.title is not None: c.title = req.title
        if req.module is not None: c.module = req.module
        if req.priority is not None: c.priority = req.priority
        if req.precondition is not None: c.precondition = req.precondition
        if req.steps is not None: c.steps = req.steps
        if req.expected is not None: c.expected = req.expected
        if req.type is not None: c.type = req.type
        await session.commit()
        await session.refresh(c)
    return ok(to_dict(c))


@router.delete("/{case_id}")
async def delete_case(case_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        c = (await session.execute(select(TestCase).where(TestCase.id == case_id, TestCase.created_by == user.id))).scalar_one_or_none()
        if not c:
            return fail("用例不存在")
        await session.delete(c)
        await session.commit()
    return ok()


@router.post("/generate")
async def generate_cases(req: GenerateRequest, user: User = Depends(rate_limit_generate)):
    async with SessionLocal() as session:
        proj = (await session.execute(select(Project).where(
            Project.id == req.project_id, Project.owner_id == user.id))).scalar_one_or_none()
        if not proj:
            return fail("项目不存在")
        try:
            cases = gen_cases(req.requirement, req.count)
        except Exception:
            cases = gen_cases_fb(req.requirement, req.count)
        for c in cases:
            session.add(TestCase(
                project_id=req.project_id, title=c["title"],
                module=c.get("module"), priority=c.get("priority", "P1"),
                precondition=c.get("precondition", ""), steps=c.get("steps", ""),
                expected=c.get("expected", ""), type=c.get("type", "功能"),
                source="AI生成", created_by=user.id))
        await session.commit()
    return ok({"count": len(cases)})