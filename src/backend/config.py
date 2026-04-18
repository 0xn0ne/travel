"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./data/travel.db"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    amap_api_key: str = ""
    openai_api_key: str = ""  # for Group C ChatGPT competitor
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret_key: str = ""
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
