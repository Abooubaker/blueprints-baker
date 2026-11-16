"""FastAPI application factory, middleware, and error handling."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.endpoints import health
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.db import dispose_engine
from app.core.errors import AppError, error_payload
from app.core.logging import configure_logging

logger = logging.getLogger("robocraft.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    logger.info(
        "api.startup",
        extra={"environment": settings.environment, "version": settings.app_version},
    )
    yield
    await dispose_engine()
    logger.info("api.shutdown")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "") or str(uuid.uuid4())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "location": list(error.get("loc", [])),
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_payload(
                code="validation_error",
                message="The request payload is invalid.",
                details=details,
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=code,
                message=str(exc.detail),
                request_id=_request_id(request),
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("database.error", extra={"request_id": _request_id(request)})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_payload(
                code="database_unavailable",
                message="The database is unavailable. Try again shortly.",
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("api.unhandled", extra={"request_id": _request_id(request)})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload(
                code="internal_error",
                message="An unexpected error occurred.",
                request_id=_request_id(request),
            ),
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(
        settings.log_level,
        json_logs=settings.environment in {"staging", "production"},
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "RoboCraft is an AI-assisted robotics engineering platform. This API "
            "exposes project, component catalog, and agent orchestration contracts."
        ),
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next: Any) -> Any:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started) * 1000)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "http.request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs" if not settings.is_production else "",
            "health": "/health",
            "api": settings.api_v1_prefix,
        }

    return app


app = create_app()
