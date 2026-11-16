"""Component catalog model (populated in milestone M4)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from app.models.enums import ComponentAvailability, ComponentCategory


class Component(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "components"
    __table_args__ = (Index("ix_components_category_active", "category", "is_active"),)

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[ComponentCategory] = mapped_column(
        enum_type(ComponentCategory, "component_category"), nullable=False
    )
    manufacturer: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    model_number: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    specs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    price_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    supplier: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    supplier_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    datasheet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    availability: Mapped[ComponentAvailability] = mapped_column(
        enum_type(ComponentAvailability, "component_availability"),
        default=ComponentAvailability.UNKNOWN,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
