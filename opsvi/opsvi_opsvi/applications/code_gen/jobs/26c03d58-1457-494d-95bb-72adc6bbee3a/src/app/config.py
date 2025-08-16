"""
Simple project configuration management for FastAPI application.
"""
from typing import List
from functools import lru_cache
from pydantic import BaseSettings


class ApiSettings(BaseSettings):
    cors_allow_origins: List[str] = ["*"]

    class Config:
        env_prefix = "API_"
        case_sensitive = False


@lru_cache()
def get_api_settings() -> ApiSettings:
    return ApiSettings()
