"""
Configuration management for opsvi-core.

Provides configuration loading, validation, and management for all opsvi-core components.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from opsvi_foundation.config.settings import BaseSettings


class CoreConfig(BaseSettings):
    """Configuration for opsvi-core components."""
    
    # Add library-specific configuration fields here
    enabled: bool = Field(default=True, description="Enable opsvi-core functionality")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    class Config:
        env_prefix = "OPSVI-CORE_"


class CoreSettings(BaseSettings):
    """Global settings for opsvi-core."""
    
    config: CoreConfig = Field(default_factory=CoreConfig)
    
    class Config:
        env_prefix = "OPSVI-CORE_"


# Global settings instance
settings = CoreSettings()
