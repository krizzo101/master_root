"""Configuration settings for opsvi-rag."""

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpsviRagSettings(BaseSettings):
    """Settings for opsvi-rag."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Core settings
    enabled: bool = Field(default=True, description="Enable opsvi-rag")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Library-specific settings
    default_vector_size: int = Field(
        default=1536, description="Default embedding dimension"
    )
    default_distance: str = Field(
        default="Cosine", description="Default distance metric"
    )

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    class Config:
        env_prefix = "OPSVI_RAG_"


# Convenience function
def get_settings() -> OpsviRagSettings:
    """Get opsvi-rag settings."""
    return OpsviRagSettings()
