#!/usr/bin/env python3
"""
Configuration for opsvi-fs, read from environment.
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class LibrarySettings(BaseSettings):
    """Settings controlling default filesystem provider behavior."""

    fs_provider: str = Field(
        default="local",
        description="Default provider: local|s3|gcs|azure|minio|fsspec",
    )
    fs_root: str = Field(default=".", description="Default root path or bucket/container")
    request_timeout_secs: int = Field(default=30, ge=1)
    max_retries: int = Field(default=3, ge=0)
    backoff_secs: float = Field(default=0.5, ge=0)

    # Provider-specific (optional)
    s3_endpoint_url: str | None = None
    s3_region: str | None = None

    class Config:
        env_prefix = "OPSVI_FS_"
        case_sensitive = False


class LibraryConfig:
    """Simple facade to access settings (for future expansion)."""

    def __init__(self, settings: LibrarySettings | None = None) -> None:
        self.settings = settings or LibrarySettings()

    @property
    def provider(self) -> str:
        return self.settings.fs_provider
