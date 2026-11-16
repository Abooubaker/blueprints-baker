"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    app_name: str = "RoboCraft API"
    app_version: str = "0.1.0"
    environment: Environment = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    database_url: str = "postgresql+asyncpg://robocraft:robocraft@localhost:5432/robocraft"
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
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

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
        return {}


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance (safe to use as a FastAPI dependency)."""
    return Settings()
