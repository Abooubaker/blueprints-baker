"""Project use-cases: persistence and transaction boundaries."""

from __future__ import annotations

import re
import unicodedata
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.enums import ProjectStatus, RobotType
from app.models.project import RobotProject, RobotSpecification
from app.schemas.project import ProjectCreate, ProjectUpdate, SpecificationUpdate


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:100] or "robot-project"


async def _unique_slug(session: AsyncSession, name: str) -> str:
    base = _slugify(name)
    slug = base
    suffix = 2
    while await session.scalar(select(RobotProject.id).where(RobotProject.slug == slug)):
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


async def create_project(session: AsyncSession, payload: ProjectCreate) -> RobotProject:
    project = RobotProject(
        name=payload.name,
        slug=await _unique_slug(session, payload.name),
        description=payload.description,
        robot_type=payload.robot_type,
        difficulty=payload.difficulty,
        budget_min_usd=payload.budget_min_usd,
        budget_max_usd=payload.budget_max_usd,
        status=ProjectStatus.DRAFT,
    )
    project.specification = RobotSpecification(
        summary=payload.description,
        use_case=payload.description,
        target_platform=payload.target_platform,
        requirements=payload.requirements,
        constraints=payload.constraints,
    )
    session.add(project)
    await session.commit()
    return await get_project(session, project.id)


async def list_projects(
    session: AsyncSession,
    *,
    limit: int = 20,
    offset: int = 0,
    status: ProjectStatus | None = None,
    robot_type: RobotType | None = None,
    search: str | None = None,
) -> tuple[list[RobotProject], int]:
    filters = []
    if status is not None:
        filters.append(RobotProject.status == status)
    if robot_type is not None:
        filters.append(RobotProject.robot_type == robot_type)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(RobotProject.name.ilike(pattern), RobotProject.description.ilike(pattern))
        )

    total = await session.scalar(select(func.count()).select_from(RobotProject).where(*filters))
    rows = await session.scalars(
        select(RobotProject)
        .where(*filters)
        .order_by(RobotProject.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(rows), int(total or 0)


async def get_project(session: AsyncSession, project_id: uuid.UUID) -> RobotProject:
    project = await session.get(RobotProject, project_id)
    if project is None:
        raise NotFoundError(f"Robot project {project_id} was not found.")
    return project


async def update_project(
    session: AsyncSession, project_id: uuid.UUID, payload: ProjectUpdate
) -> RobotProject:
    project = await get_project(session, project_id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(project, field, value)
    await session.commit()
    return await get_project(session, project_id)


async def delete_project(session: AsyncSession, project_id: uuid.UUID) -> None:
    project = await get_project(session, project_id)
    await session.delete(project)
    await session.commit()


async def get_specification(session: AsyncSession, project_id: uuid.UUID) -> RobotSpecification:
    project = await get_project(session, project_id)
    if project.specification is None:
        raise NotFoundError(f"Robot project {project_id} has no specification.")
    return project.specification


async def update_specification(
    session: AsyncSession, project_id: uuid.UUID, payload: SpecificationUpdate
) -> RobotSpecification:
    specification = await get_specification(session, project_id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(specification, field, value)
    specification.version += 1
    await session.commit()
    await session.refresh(specification)
    return specification
