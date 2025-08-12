"""
Application configuration management and settings using Pydantic BaseSettings.
"""
from pydantic import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Todo List Web Service"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./todolist.db"
    ALLOW_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
