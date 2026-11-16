"""Async database engine and request-scoped session management."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine(settings: Settings) -> AsyncEngine:
    """Create an async engine from settings.

    SQLite is supported for tests only; PostgreSQL is the production database.
    """
    kwargs: dict[str, object] = {
        "echo": settings.database_echo,
        "pool_pre_ping": True,
        "connect_args": settings.sqlalchemy_connect_args,
    }
    if not settings.database_url.startswith("sqlite"):
        kwargs["pool_size"] = settings.database_pool_size
        kwargs["max_overflow"] = settings.database_max_overflow
    return create_async_engine(settings.database_url, **kwargs)


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings())
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(), expire_on_commit=False, autoflush=False
        )
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session that is always closed."""
    async with get_session_factory()() as session:
        yield session


async def dispose_engine() -> None:
    """Close pooled connections during application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
