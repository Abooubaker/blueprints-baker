"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import parse_qsl, urlencode

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    """Runtime settings.

    Values are read from environment variables and an optional local ``.env``
    file. Secrets never have usable defaults in non-test environments.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Albayraq API"
    app_version: str = "0.1.0"
    environment: Environment = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # NoDecode keeps pydantic-settings from JSON-decoding the raw env value, so
    # the comma-separated form documented for hosted providers keeps working.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    database_url: str = "postgresql+asyncpg://albayraq:albayraq@localhost:5432/albayraq"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    ai_provider: str = "mock"
    ai_model: str = "placeholder"
    ai_api_key: str | None = None
    ai_request_timeout_seconds: float = 60.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                try:
                    decoded = json.loads(text)
                except json.JSONDecodeError:
                    pass
                else:
                    if isinstance(decoded, list):
                        return [str(origin).strip() for origin in decoded if str(origin).strip()]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        """Accept the URLs hosted providers emit and use the async driver.

        Neon and Render hand out libpq-style URLs (``sslmode``, ``channel_binding``)
        that asyncpg does not understand, so those parameters are translated or
        dropped. The async driver is selected automatically.
        """

        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            value = "postgresql+asyncpg://" + value.removeprefix("postgres://")
        elif value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        elif not value.startswith("postgresql+asyncpg://"):
            return value

        scheme, separator, rest = value.partition("://")
        authority, question, query = rest.partition("?")
        if not question:
            return value

        allowed: list[tuple[str, str]] = []
        for key, raw in parse_qsl(query, keep_blank_values=True):
            if key == "sslmode":
                allowed.append(("ssl", "require" if raw == "require" else raw))
            elif key in {"channel_binding", "options"}:
                continue
            else:
                allowed.append((key, raw))
        normalized = urlencode(allowed)
        return f"{scheme}{separator}{authority}" + (f"?{normalized}" if normalized else "")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        level = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if level not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return level

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sqlalchemy_connect_args(self) -> dict[str, object]:
        """Driver-specific connection arguments."""
        if self.database_url.startswith("sqlite"):
            return {"check_same_thread": False}
        # Neon's pooled endpoint (PgBouncer) cannot use asyncpg's prepared-statement
        # cache. Detect it from the conventional ``-pooler`` host label.
        if "-pooler." in self.database_url:
            return {"statement_cache_size": 0}
        return {}


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance (safe to use as a FastAPI dependency)."""
    return Settings()
