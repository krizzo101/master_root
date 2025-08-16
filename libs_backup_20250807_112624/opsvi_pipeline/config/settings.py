"Runtime configuration powered by Pydantic v2."

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application/runtime settings."""

    model_config = SettingsConfigDict(env_prefix="OPSVI_PIPELINE_", extra="ignore")

    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Add additional settings here ----------------------------------

    @classmethod
    @lru_cache()
    def instance(cls) -> "Settings":
        """Return a cached Settings instance."""
        return cls()


# Public singleton-style accessor --------------------------------------
settings = Settings.instance()

