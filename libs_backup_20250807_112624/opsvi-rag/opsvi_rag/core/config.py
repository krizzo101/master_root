"""
Configuration management for opsvi-rag.

Provides configuration loading, validation, and management for all opsvi-rag components.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from opsvi_foundation.config.settings import BaseSettings


class RagConfig(BaseSettings):
    """Configuration for opsvi-rag components."""
    
    # Add library-specific configuration fields here
    enabled: bool = Field(default=True, description="Enable opsvi-rag functionality")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    class Config:
        env_prefix = "OPSVI-RAG_"


class RagSettings(BaseSettings):
    """Global settings for opsvi-rag."""
    
    config: RagConfig = Field(default_factory=RagConfig)
    
    class Config:
        env_prefix = "OPSVI-RAG_"


# Global settings instance
settings = RagSettings()
