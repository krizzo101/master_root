"""
Configuration management for opsvi-llm.

Provides configuration loading, validation, and management for all opsvi-llm components.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from opsvi_foundation.config.settings import BaseSettings


class LlmConfig(BaseSettings):
    """Configuration for opsvi-llm components."""
    
    # Add library-specific configuration fields here
    enabled: bool = Field(default=True, description="Enable opsvi-llm functionality")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    class Config:
        env_prefix = "OPSVI-LLM_"


class LlmSettings(BaseSettings):
    """Global settings for opsvi-llm."""
    
    config: LlmConfig = Field(default_factory=LlmConfig)
    
    class Config:
        env_prefix = "OPSVI-LLM_"


# Global settings instance
settings = LlmSettings()
