"""Settings normalization for hosted database URLs and CORS."""

from __future__ import annotations

import pytest

from app.core.config import Settings


def test_neon_libpq_url_is_normalized() -> None:
    settings = Settings(
        environment="test",
        database_url=(
            "postgresql://user:secret@db-pooler.example.com/neondb?sslmode=require&channel_binding=require"
        ),
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in settings.database_url
    assert "channel_binding" not in settings.database_url
    assert "ssl=require" in settings.database_url
    assert settings.sqlalchemy_connect_args == {"statement_cache_size": 0}


def test_render_postgres_url_is_normalized() -> None:
    settings = Settings(
        environment="test",
        database_url="postgres://albayraq:secret@db.example.com/albayraq",
    )

    assert settings.database_url == ("postgresql+asyncpg://albayraq:secret@db.example.com/albayraq")
    assert settings.sqlalchemy_connect_args == {}


def test_direct_neon_url_keeps_default_connect_args() -> None:
    settings = Settings(
        environment="test",
        database_url=("postgresql://user:secret@db.example.com/neondb?sslmode=require"),
    )

    assert "ssl=require" in settings.database_url
    assert settings.sqlalchemy_connect_args == {}


def test_cors_origins_accept_comma_separated_string() -> None:
    settings = Settings(
        environment="test",
        cors_origins="https://example.com, https://www.example.com",
    )

    assert settings.cors_origins == ["https://example.com", "https://www.example.com"]


def test_cors_origins_accept_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://albayraq-web.onrender.com,http://localhost:3000")

    settings = Settings(environment="test")

    assert settings.cors_origins == [
        "https://albayraq-web.onrender.com",
        "http://localhost:3000",
    ]


def test_cors_origins_accept_json_array_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS", '["https://albayraq-web.onrender.com","http://localhost:3000"]'
    )

    settings = Settings(environment="test")

    assert settings.cors_origins == [
        "https://albayraq-web.onrender.com",
        "http://localhost:3000",
    ]
