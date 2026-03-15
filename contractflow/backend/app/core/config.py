"""Application configuration using Pydantic v2 settings."""
from __future__ import annotations

import json
import os
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration hub.

    In development, values can be loaded from .env.
    In production, values must come from environment variables or Key Vault references.
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://contractflow:contractflow@localhost:5432/contractflow"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Azure Storage
    AZURE_STORAGE_ACCOUNT_URL: str = "http://127.0.0.1:10000/devstoreaccount1"
    AZURE_STORAGE_CONTAINER: str = "contracts"

    # Azure Key Vault
    KEY_VAULT_URI: str = ""

    # Entra ID (required in production)
    ENTRA_TENANT_ID: str = ""
    ENTRA_CLIENT_ID: str = ""
    ENTRA_AUDIENCE: str = ""

    # Auth/session
    LOCAL_AUTH_ENABLED: bool = True
    SESSION_COOKIE_NAME: str = "cf_session"
    CSRF_COOKIE_NAME: str = "cf_csrf"
    SESSION_TTL_MINUTES: int = 60
    SESSION_SECURE_COOKIE: bool = False

    # CSRF
    CSRF_SECRET: str = "dev-csrf-secret-change-me"

    # Upload controls
    MAX_UPLOAD_SIZE_MB: int = 50
    SAS_URL_TTL_MINUTES: int = 15

    @field_validator("ENVIRONMENT")
    @classmethod
    def _validate_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"development", "test", "staging", "production"}
        if normalized not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def database_url_async(self) -> str:
        """Ensure the DATABASE_URL uses the asyncpg driver."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def database_url_sync(self) -> str:
        """Return a sync-compatible DATABASE_URL (for Alembic migrations)."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def allowed_origins_list(self) -> list[str]:
        raw = self.ALLOWED_ORIGINS.strip()
        if not raw:
            return []
        if raw.startswith("["):
            parsed = json.loads(raw)
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [o.strip() for o in raw.split(",") if o.strip()]

    def validate_production(self) -> None:
        """Fail fast if production config is incomplete or insecure."""
        if not self.is_production:
            return

        missing: list[str] = []
        if not self.ENTRA_TENANT_ID:
            missing.append("ENTRA_TENANT_ID")
        if not self.ENTRA_CLIENT_ID:
            missing.append("ENTRA_CLIENT_ID")
        if not self.ENTRA_AUDIENCE:
            missing.append("ENTRA_AUDIENCE")
        if not self.KEY_VAULT_URI:
            missing.append("KEY_VAULT_URI")
        if self.CSRF_SECRET == "dev-csrf-secret-change-me":
            missing.append("CSRF_SECRET (must not use default)")
        if self.LOCAL_AUTH_ENABLED:
            missing.append("LOCAL_AUTH_ENABLED (must be false in production)")

        if missing:
            raise RuntimeError(
                f"Production startup blocked. Missing required config: {', '.join(missing)}"
            )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton.

    Only load `.env` in non-production contexts.
    """
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    env_file = ".env" if environment != "production" else None
    return Settings(_env_file=env_file)
