from pydantic import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite+aiosqlite:///./tasks.db"
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
