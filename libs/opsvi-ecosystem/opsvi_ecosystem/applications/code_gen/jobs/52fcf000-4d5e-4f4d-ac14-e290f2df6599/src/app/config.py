"""
App configuration and settings management.
Uses pydantic settings for environment variable based config.
"""
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # General
    PROJECT_NAME: str = "AutoPyReview"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: list[str] = ["*"]
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Database
    DB_URL: str = Field(..., env="DATABASE_URL")
    DB_ECHO: bool = False

    # File Storage
    UPLOAD_DIR: str = str(Path("uploads").resolve())
    RETAIN_HOURS: int = 24
    MAX_UPLOAD_SIZE: int = 1024 * 1024  # 1MB

    # Celery / Task Queue
    CELERY_BROKER_URL: str = Field(..., env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(..., env="CELERY_RESULT_BACKEND")
    CELERY_TASK_TIMEOUT: int = 120

    # GitHub
    GITHUB_CLIENT_ID: str = Field(..., env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = Field(..., env="GITHUB_CLIENT_SECRET")

    # S3
    USE_S3: bool = False
    S3_BUCKET: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
