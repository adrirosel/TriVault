"""Application settings loaded from environment variables."""

from functools import lru_cache
import json
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration validated with Pydantic v2."""

    PROJECT_NAME: str = "TriVault API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    DB_USE_NULL_POOL: bool = False
    DB_POOL_RECYCLE: int = 300

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> list[str]:
        """Accept either a JSON list or a comma-separated string of origins."""
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("ALLOWED_ORIGINS must be a list or comma-separated string.")

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def disallow_wildcard_in_production(cls, origins: list[str], info) -> list[str]:
        """Prevent wildcard CORS origins in production environments."""
        environment = info.data.get("ENVIRONMENT")
        if environment == "production" and "*" in origins:
            raise ValueError("Wildcard '*' is not allowed in ALLOWED_ORIGINS in production.")
        return origins

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_length(cls, value: str) -> str:
        """Require a minimum secret length so JWT signatures remain strong."""
        if len(value.strip()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
