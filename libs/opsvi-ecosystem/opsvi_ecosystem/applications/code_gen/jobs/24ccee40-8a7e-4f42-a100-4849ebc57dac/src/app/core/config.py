"""
Application configuration management and settings using Pydantic BaseSettings.
"""
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Todo List Web Service"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./todolist.db"
    ALLOW_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
