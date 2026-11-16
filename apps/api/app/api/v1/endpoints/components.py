"""Read-only component catalog endpoints (writes arrive with M4)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.api.deps import PaginationDep
from app.core.db import get_db
from app.models.component import Component
from app.models.enums import ComponentCategory
from app.schemas.common import Page, PageMeta
from app.schemas.component import ComponentRead

router = APIRouter(prefix="/components", tags=["components"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=Page[ComponentRead], summary="List catalog components")
async def list_components(
    session: SessionDep,
    pagination: PaginationDep,
    category: Annotated[ComponentCategory | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
) -> Page[ComponentRead]:
    filters: list[ColumnElement[bool]] = [Component.is_active.is_(True)]
    if category is not None:
        filters.append(Component.category == category)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Component.name.ilike(pattern),
                Component.manufacturer.ilike(pattern),
                Component.model_number.ilike(pattern),
            )
        )

    total = await session.scalar(select(func.count()).select_from(Component).where(*filters))
    components = await session.scalars(
        select(Component)
        .where(*filters)
        .order_by(Component.name)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    return Page[ComponentRead](
        items=[ComponentRead.model_validate(component) for component in components],
        meta=PageMeta(total=int(total or 0), limit=pagination.limit, offset=pagination.offset),
    )
