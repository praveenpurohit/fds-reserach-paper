from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.paper import Paper
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(req: ProjectCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = Project(user_id=user.id, title=req.title, research_question=req.research_question, description=req.description)
    db.add(project)
    await db.flush()
    return ProjectResponse(id=project.id, title=project.title, research_question=project.research_question,
                          description=project.description, status=project.status, created_at=project.created_at)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    responses = []
    for p in projects:
        count_result = await db.execute(select(func.count(Paper.id)).where(Paper.project_id == p.id))
        paper_count = count_result.scalar() or 0
        responses.append(ProjectResponse(id=p.id, title=p.title, research_question=p.research_question,
                                        description=p.description, status=p.status, created_at=p.created_at,
                                        paper_count=paper_count))
    return responses


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    count_result = await db.execute(select(func.count(Paper.id)).where(Paper.project_id == project.id))
    paper_count = count_result.scalar() or 0
    return ProjectResponse(id=project.id, title=project.title, research_question=project.research_question,
                          description=project.description, status=project.status, created_at=project.created_at,
                          paper_count=paper_count)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, req: ProjectUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if req.title is not None:
        project.title = req.title
    if req.research_question is not None:
        project.research_question = req.research_question
    if req.description is not None:
        project.description = req.description
    await db.flush()
    return ProjectResponse(id=project.id, title=project.title, research_question=project.research_question,
                          description=project.description, status=project.status, created_at=project.created_at)


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    return {"detail": "deleted"}
