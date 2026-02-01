import os
from enum import Enum
from functools import lru_cache
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings:
    """
    APP_ENV: Current environment (development, staging, production)
    SECRET_KEY: Secret key for JWT signing
    ALGORITHM: JWT algorithm (default: HS256)
    ACCESS_TOKEN_EXPIRE_MINUTES: Access token expiration in minutes
    REFRESH_TOKEN_EXPIRE_DAYS: Refresh token expiration in days
    DATABASE_URL: PostgreSQL connection string
    DEBUG: Enable debug mode
    CORS_ORIGINS: Allowed CORS origins
    """
    def __init__(self):
        env_value = os.getenv("APP_ENV", "development").lower()

        try:
            self.APP_ENV = Environment(env_value)
        except ValueError:
            self.APP_ENV = Environment.DEVELOPMENT

        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")
        self.ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        self.DATABASE_URL: str | None = os.getenv("DATABASE_URL")
        debug_env = os.getenv("DEBUG")

        if debug_env is not None:
            self.DEBUG = debug_env.lower() in ("true", "1", "yes")
        else:
            self.DEBUG = self.is_development

        cors_origins = os.getenv("CORS_ORIGINS", "")
        self.CORS_ORIGINS: List[str] = (
            [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
            if cors_origins
            else ["http://localhost:3000", "http://localhost:3001"]
        )

        self._validate()

    def _validate(self):
        import warnings

        if not self.SECRET_KEY:
            if self.is_production:
                raise ValueError("SECRET_KEY is required in production")
            warnings.warn(
                "SECRET_KEY is not set. Using insecure default for development only.",
                UserWarning,
                stacklevel=2,
            )
            self.SECRET_KEY = "insecure-development-key-change-in-production"

        if len(self.SECRET_KEY) < 32:
            if self.is_production:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters in production. "
                    'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )

            warnings.warn(
                f"SECRET_KEY should be at least 32 characters for security. "
                f"Current length: {len(self.SECRET_KEY)}. "
                f'Generate a secure key with: python -c "import secrets; print(secrets.token_urlsafe(32))"',
                UserWarning,
                stacklevel=2,
            )

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        return self.APP_ENV == Environment.STAGING

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == Environment.PRODUCTION

    def __repr__(self) -> str:
        return (
            f"Settings(APP_ENV={self.APP_ENV.value}, "
            f"DEBUG={self.DEBUG}, "
            f"ACCESS_TOKEN_EXPIRE_MINUTES={self.ACCESS_TOKEN_EXPIRE_MINUTES}, "
            f"REFRESH_TOKEN_EXPIRE_DAYS={self.REFRESH_TOKEN_EXPIRE_DAYS})"
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

# Auth endpoint paths to be used by rate limiter middleware
AUTH_ENDPOINTS = frozenset({
    "/api/authenticate",
    "/api/refresh",
})
