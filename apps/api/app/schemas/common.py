"""Common response envelopes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageMeta(APIModel):
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class Page[T](APIModel):
    items: list[T]
    meta: PageMeta


class ErrorDetail(APIModel):
    code: str
    message: str
    details: object | None = None
    request_id: str | None = None


class ErrorResponse(APIModel):
    error: ErrorDetail
