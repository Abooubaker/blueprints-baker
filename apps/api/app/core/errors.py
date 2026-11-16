"""Domain exceptions and RFC 7807-inspired error responses."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for expected, client-facing application errors."""

    status_code: int = 400
    code: str = "bad_request"
    message: str = "The request could not be processed."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "The requested resource does not exist."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "The resource conflicts with an existing resource."


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"
    message = "The request payload is invalid."


class NotImplementedFeatureError(AppError):
    status_code = 501
    code = "not_implemented"
    message = "This capability is not implemented yet."


def error_payload(
    *, code: str, message: str, details: Any = None, request_id: str | None = None
) -> dict[str, Any]:
    """Build the canonical error envelope used by every endpoint."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    if request_id:
        error["request_id"] = request_id
    return {"error": error}
