"""Component catalog schemas (read-only foundation)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import ComponentAvailability, ComponentCategory
from app.schemas.common import APIModel


class ComponentRead(APIModel):
    id: UUID
    name: str
    category: ComponentCategory
    manufacturer: str
    model_number: str
    description: str
    specs: dict[str, Any]
    price_usd: float | None
    supplier: str
    supplier_url: str | None
    datasheet_url: str | None
    availability: ComponentAvailability
    is_active: bool
    created_at: datetime
    updated_at: datetime
