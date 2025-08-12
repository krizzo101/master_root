import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecret")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/metricsdb"
    )
    METRICS_COLLECTION_INTERVAL_SEC: int = int(
        os.getenv("METRICS_COLLECTION_INTERVAL_SEC", "1")
    )
    CORS_ALLOW_ORIGINS: list[str] = [os.getenv("FRONTEND_URL", "http://localhost:3000")]


settings = Settings()
