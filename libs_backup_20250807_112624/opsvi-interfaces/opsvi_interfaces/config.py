"""Package configuration (Pydantic V2 stub)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime settings."""

    debug: bool = Field(default=False, description="Enable debug logging")

    @property
    def log_level(self) -> str:
        return "DEBUG" if self.debug else "INFO"
