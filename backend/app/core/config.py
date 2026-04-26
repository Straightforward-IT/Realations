"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Realations backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REALATIONS_",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Realations"
    environment: Literal["dev", "test", "staging", "prod"] = "dev"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # --- Database ---
    # Driver-prefixed SQLAlchemy URL. Default uses sqlite for ease of local/test bootstrapping;
    # production deployments MUST point this at PostgreSQL to enable RLS-based tenant isolation.
    database_url: str = "sqlite+pysqlite:///./realations.db"

    # --- Security ---
    jwt_secret: str = Field(
        default="change-me-in-production-this-is-not-a-real-secret",
        description="HMAC secret for signing access tokens. Override in every environment.",
    )
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60 * 12  # 12 hours

    # --- Integrations ---
    # Outbound webhook delivery is performed via httpx with this timeout.
    webhook_timeout_seconds: float = 10.0

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith(("postgresql", "postgres"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
