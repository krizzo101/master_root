"""Configuration settings for opsvi-gateway.


"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, Field, validator
from pydantic_settings import SettingsConfigDict

class OpsviGatewaySettings(BaseSettings):
    """Settings for opsvi-gateway."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Core settings
    enabled: bool = Field(default=True, description="Enable opsvi-gateway")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Library-specific settings
    

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    

    class Config:
        env_prefix = "OPSVI_OPSVI_GATEWAY__"

# Convenience function
def get_settings() -> OpsviGatewaySettings:
    """Get opsvi-gateway settings."""
    return OpsviGatewaySettings()
