from functools import lru_cache
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Pressivox"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./web_search.db"

    tavily_api_key: str = "replace_me"
    tavily_base_url: str = "https://api.tavily.com"
    default_search_provider: str = "tavily"
    default_max_results: int = 10
    http_timeout_seconds: int = 20
    cors_allow_origins: str = "*"

    auth_secret_key: str = "change-this-secret-key"
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 60
    auth_refresh_token_expire_days: int = 7

    @property
    def cors_origins_list(self) -> list[str]:
        values = [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
        return values or ["*"]

    def validate_security(self) -> None:
        """Raise if insecure defaults are used in a non-development environment."""
        insecure_keys = {"change-this-secret-key", "", "secret", "dev"}
        if os.getenv("VERCEL") and self.database_url.startswith("sqlite"):
            raise RuntimeError(
                "DATABASE_URL must use a persistent database on Vercel (for example Postgres). "
                "SQLite on serverless instances causes user accounts and login state to disappear across devices."
            )
        if self.app_env != "development" and self.auth_secret_key in insecure_keys:
            raise RuntimeError(
                "AUTH_SECRET_KEY must be set to a secure random value in non-development environments. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if self.app_env == "production" and self.app_debug:
            raise RuntimeError("APP_DEBUG must be false in production.")
        if self.app_env == "production" and "*" in self.cors_origins_list:
            raise RuntimeError("CORS_ALLOW_ORIGINS must be explicit in production and cannot include '*'.")


@lru_cache
def get_settings() -> Settings:
    return Settings()