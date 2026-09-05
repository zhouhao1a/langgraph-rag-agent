from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from app.core.deps import get_current_user
from app.models.base import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.common import ok, fail

router = APIRouter(prefix="/projects", tags=["projects"])


def to_dict(p: Project):
    return {"id": p.id, "name": p.name, "description": p.description,
            "status": p.status, "owner_id": p.owner_id, "created_at": str(p.created_at)}


@router.post("")
async def create_project(req: ProjectCreate, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        p = Project(name=req.name, description=req.description,
                    status=req.status, owner_id=user.id)
        session.add(p)
        await session.commit()
        await session.refresh(p)  # 拿自增 id
    return ok(to_dict(p))


@router.get("")
async def list_projects(page: int = 1, page_size: int = 10,
                        user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        total = (await session.execute(
            select(func.count()).select_from(Project).where(Project.owner_id == user.id)
        )).scalar()
        rows = (await session.execute(
            select(Project).where(Project.owner_id == user.id)
            .order_by(Project.id.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
    return ok({"items": [to_dict(p) for p in rows], "total": total, "page": page, "page_size": page_size})


@router.get("/{project_id}")
async def get_project(project_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        p = (await session.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))).scalar_one_or_none()
    if not p:
        return fail("项目不存在")
    return ok(to_dict(p))


@router.put("/{project_id}")
async def update_project(project_id: int, req: ProjectUpdate,
                         user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        p = (await session.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))).scalar_one_or_none()
        if not p:
            return fail("项目不存在")
        if req.name is not None: p.name = req.name
        if req.description is not None: p.description = req.description
        if req.status is not None: p.status = req.status
        await session.commit()
        await session.refresh(p)
    return ok(to_dict(p))


@router.delete("/{project_id}")
async def delete_project(project_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        p = (await session.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))).scalar_one_or_none()
        if not p:
            return fail("项目不存在")
        await session.delete(p)
        await session.commit()
    return ok()