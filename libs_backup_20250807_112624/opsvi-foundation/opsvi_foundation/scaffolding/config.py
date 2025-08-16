"""
Centralized configuration framework for OPSVI libraries.

Provides generic configuration patterns to eliminate repetition across all libraries.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LibraryConfig(BaseSettings):
    """Base configuration for all OPSVI libraries."""

    enabled: bool = Field(default=True, description="Enable library functionality")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    class Config:
        env_prefix = "OPSVI_"


class LibrarySettings(BaseSettings):
    """Base settings for all OPSVI libraries."""

    config: LibraryConfig = Field(default_factory=LibraryConfig)

    class Config:
        env_prefix = "OPSVI_"


def create_library_config(
    library_name: str,
    additional_fields: Optional[Dict[str, Any]] = None,
    env_prefix: Optional[str] = None
) -> Type[LibraryConfig]:
    """Factory function to create library-specific configuration classes."""

    class_name = f"{library_name.title().replace('-', '')}Config"

    # Create fields dict with base fields
    fields = {
        "enabled": (bool, Field(default=True, description=f"Enable {library_name} functionality")),
        "debug": (bool, Field(default=False, description=f"Enable {library_name} debug mode")),
        "log_level": (str, Field(default="INFO", description=f"{library_name} logging level")),
    }

    # Add additional fields
    if additional_fields:
        fields.update(additional_fields)

    # Create the class
    config_class = type(class_name, (LibraryConfig,), fields)

    # Set the environment prefix
    if env_prefix:
        config_class.Config.env_prefix = env_prefix
    else:
        config_class.Config.env_prefix = library_name.upper().replace('-', '_') + "_"

    return config_class


def create_library_settings(
    library_name: str,
    config_class: Optional[Type[LibraryConfig]] = None,
    additional_fields: Optional[Dict[str, Any]] = None,
    env_prefix: Optional[str] = None
) -> Type[LibrarySettings]:
    """Factory function to create library-specific settings classes."""

    class_name = f"{library_name.title().replace('-', '')}Settings"

    # Use provided config class or create default one
    if config_class is None:
        config_class = create_library_config(library_name, env_prefix=env_prefix)

    # Create fields dict
    fields = {
        "config": (config_class, Field(default_factory=config_class)),
    }

    # Add additional fields
    if additional_fields:
        fields.update(additional_fields)

    # Create the class
    settings_class = type(class_name, (LibrarySettings,), fields)

    # Set the environment prefix
    if env_prefix:
        settings_class.Config.env_prefix = env_prefix
    else:
        settings_class.Config.env_prefix = library_name.upper().replace('-', '_') + "_"

    return settings_class


def create_settings_instance(library_name: str, **kwargs) -> LibrarySettings:
    """Create a settings instance for a library."""
    settings_class = create_library_settings(library_name)
    return settings_class(**kwargs)


# Global settings instance
global_settings = LibrarySettings()
