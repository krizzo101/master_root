"""
Configuration for Context Bridge Server

Handles configuration from environment variables and config files.
"""

import os
from typing import Optional, Literal
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class ContextBridgeConfig(BaseSettings):
    """
    Configuration for Context Bridge Server

    Can be configured via:
    - Environment variables (CONTEXT_BRIDGE_*)
    - Config file
    - Constructor parameters
    """

    model_config = {
        "env_prefix": "CONTEXT_BRIDGE_",
        "env_file": ".env",
        "extra": "ignore",  # Ignore extra fields instead of raising errors
    }

    # Pub/Sub Backend Configuration
    pubsub_backend: Literal["redis", "memory", "auto"] = Field(
        default="auto",
        description="Pub/sub backend: 'redis', 'memory', or 'auto' (try Redis, fallback to memory)",
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )
    redis_connect_timeout: int = Field(
        default=5, description="Redis connection timeout in seconds"
    )
    redis_retry_on_timeout: bool = Field(
        default=True, description="Retry Redis operations on timeout"
    )
    redis_max_connections: int = Field(
        default=10, description="Maximum Redis connections in pool"
    )

    # Server Configuration
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=3000, description="Server port")

    # Context Management
    max_history_size: int = Field(
        default=100,
        description="Maximum number of context snapshots to keep in history",
    )
    context_ttl_seconds: int = Field(
        default=3600, description="TTL for cached context in seconds (Redis only)"
    )

    # Performance
    enable_metrics: bool = Field(
        default=True, description="Enable performance metrics collection"
    )
    metrics_interval_seconds: int = Field(
        default=60, description="Metrics reporting interval"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: Literal["json", "text"] = Field(
        default="text", description="Log format"
    )

    # In-Memory Pub/Sub Settings
    memory_pubsub_max_queue_size: int = Field(
        default=1000, description="Maximum queue size per channel for in-memory pub/sub"
    )
    memory_pubsub_cleanup_interval: int = Field(
        default=300, description="Cleanup interval for inactive subscriptions (seconds)"
    )

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    @validator("pubsub_backend")
    def validate_pubsub_backend(cls, v):
        """Validate pub/sub backend"""
        if v not in ["redis", "memory", "auto"]:
            raise ValueError(f"Invalid pubsub_backend: {v}")
        return v

    class Config:
        env_prefix = "CONTEXT_BRIDGE_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_effective_backend(self) -> str:
        """
        Get the effective backend based on configuration and availability

        Returns:
            'redis' or 'memory'
        """
        if self.pubsub_backend == "memory":
            return "memory"
        elif self.pubsub_backend == "redis":
            return "redis"
        else:  # auto
            # Will be determined at runtime based on Redis availability
            return "auto"

    def configure_logging(self):
        """Configure logging based on settings"""
        level = getattr(logging, self.log_level)

        if self.log_format == "json":
            try:
                from pythonjsonlogger import jsonlogger

                handler = logging.StreamHandler()
                formatter = jsonlogger.JsonFormatter()
                handler.setFormatter(formatter)
                logging.root.handlers = [handler]
            except ImportError:
                logger.warning("python-json-logger not installed, using text format")
                self.log_format = "text"

        if self.log_format == "text":
            logging.basicConfig(
                level=level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                force=True,
            )

    @classmethod
    def from_env(cls) -> "ContextBridgeConfig":
        """Create config from environment variables"""
        return cls()

    def to_dict(self) -> dict:
        """Export configuration as dictionary"""
        return self.dict(exclude_unset=False)


# Default configuration instance (created lazily)
_default_config = None


def get_default_config():
    """Get or create default configuration"""
    global _default_config
    if _default_config is None:
        _default_config = ContextBridgeConfig()
    return _default_config
