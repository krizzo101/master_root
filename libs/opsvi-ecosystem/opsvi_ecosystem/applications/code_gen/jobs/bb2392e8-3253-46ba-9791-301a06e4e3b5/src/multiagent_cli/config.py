"""
Configuration & Secrets management for Multi-Agent CLI Tool
"""
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseSettings, Field, ValidationError


class AppConfig(BaseSettings):
    """
    Runtime configuration and secrets loaded from environment or .env files.
    """

    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_API_MODEL: str = Field(default="gpt-3.5-turbo-1106", env="OPENAI_API_MODEL")
    MAX_AGENT_CONCURRENCY: int = Field(
        default=4, env="MAX_AGENT_CONCURRENCY", gt=0, le=32
    )
    AGENT_RESULT_TIMEOUT: int = Field(
        default=600, env="AGENT_RESULT_TIMEOUT", gt=10, le=3600
    )
    LANGGRAPH_CONFIG: str | None = Field(
        default=None, env="LANGGRAPH_CONFIG"
    )  # For advanced users

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


CONFIG_CACHE = None


def load_dotenv_config(config_file: Path | None = None):
    """Loads .env files and updates os.environ accordingly."""
    # Most important: load this FIRST
    if config_file is not None and config_file.exists():
        logger.info(f"Loading environment variables from {config_file}")
        load_dotenv(dotenv_path=config_file)
    else:
        # Fallback: try local .env
        if Path(".env").exists():
            load_dotenv(dotenv_path=Path(".env"))


def get_config() -> AppConfig:
    """Singleton accessor for AppConfig"""
    global CONFIG_CACHE
    if CONFIG_CACHE:
        return CONFIG_CACHE
    try:
        cfg = AppConfig()
        CONFIG_CACHE = cfg
        return cfg
    except ValidationError as e:
        logger.error(f"Configuration Loading Error: {e.errors()}")
        raise RuntimeError(f"AppConfig validation failed: {e.errors()}")
