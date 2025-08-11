"""
config.py: Configuration management for the backend (env, secrets, etc.)
"""
from functools import lru_cache
from pydantic import BaseSettings, Field
from typing import List


class Settings(BaseSettings):
    debug: bool = Field(False, env="DEBUG")
    port: int = Field(8080, env="PORT")
    session_secret: str = Field(..., env="SESSION_SECRET")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algo: str = Field("HS256", env="JWT_ALGO")
    allowed_hosts: List[str] = Field(["*"], env="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    postgres_url: str = Field(..., env="POSTGRES_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_models: List[str] = Field(["o3", "o4-mini"])
    s3_endpoint: str = Field(..., env="S3_ENDPOINT")
    s3_access_key: str = Field(..., env="S3_ACCESS_KEY")
    s3_secret_key: str = Field(..., env="S3_SECRET_KEY")
    s3_bucket: str = Field(..., env="S3_BUCKET")
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_refresh_token: str = Field(..., env="GOOGLE_REFRESH_TOKEN")
    frontend_url: str = Field("http://localhost:3000", env="FRONTEND_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
