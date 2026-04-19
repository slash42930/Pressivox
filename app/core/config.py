from functools import lru_cache

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

    @property
    def cors_origins_list(self) -> list[str]:
        values = [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
        return values or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()