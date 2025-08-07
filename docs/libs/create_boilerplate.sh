#!/bin/bash

# Create all __init__.py and core boilerplate files efficiently

echo "📝 Creating __init__.py files for all modules..."

# Function to create __init__.py
create_init() {
    local file="$1"
    local module="$2"
    local description="$3"

    cat > "$file" << EOF
"""
$description

Part of the OPSVI ecosystem.
"""

__version__ = "1.0.0"
EOF
}

# Create __init__.py for all directories
for lib in opsvi-core opsvi-llm opsvi-rag opsvi-agents; do
    lib_name=$(echo $lib | tr '-' '_')

    # Find all directories and create __init__.py
    find "$lib/$lib_name" -type d | while read dir; do
        module_path=$(echo "$dir" | sed "s|$lib/$lib_name/||" | sed 's|/|.|g')
        if [ "$module_path" = "" ]; then
            module_path="main"
        fi

        description="$(basename "$dir" | sed 's/.*/\u&/') module for $lib"
        create_init "$dir/__init__.py" "$module_path" "$description"
    done
done

echo "🔧 Creating core exception files..."

# Create exceptions for all libraries
for lib in opsvi-core opsvi-llm opsvi-rag opsvi-agents; do
    lib_name=$(echo $lib | tr '-' '_')
    lib_class=$(echo $lib | sed 's/opsvi-//' | sed 's/.*/\u&/')

    cat > "$lib/$lib_name/core/exceptions.py" << EOF
"""
Exception hierarchy for $lib.

Provides structured error handling across all $lib components.
"""

from typing import Any, Optional


class ${lib_class}Error(Exception):
    """Base exception for all $lib errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(${lib_class}Error):
    """Raised when configuration is invalid or missing."""
    pass


class InitializationError(${lib_class}Error):
    """Raised when component initialization fails."""
    pass


class ValidationError(${lib_class}Error):
    """Raised when data validation fails."""
    pass


class ExternalServiceError(${lib_class}Error):
    """Raised when external service calls fail."""
    pass


class AuthenticationError(${lib_class}Error):
    """Raised when authentication fails."""
    pass


class AuthorizationError(${lib_class}Error):
    """Raised when authorization fails."""
    pass


class RateLimitError(${lib_class}Error):
    """Raised when rate limits are exceeded."""
    pass


class TimeoutError(${lib_class}Error):
    """Raised when operations timeout."""
    pass


class NetworkError(${lib_class}Error):
    """Raised when network operations fail."""
    pass


class SerializationError(${lib_class}Error):
    """Raised when serialization/deserialization fails."""
    pass
EOF
done

echo "⚙️ Creating configuration files..."

# Create config files for all libraries
for lib in opsvi-core opsvi-llm opsvi-rag opsvi-agents; do
    lib_name=$(echo $lib | tr '-' '_')
    lib_class=$(echo $lib | sed 's/opsvi-//' | sed 's/.*/\u&/')

    cat > "$lib/$lib_name/core/config.py" << EOF
"""
Configuration management for $lib.

Handles environment-based configuration with validation and defaults.
"""

import os
from typing import Any, Optional
from pydantic import BaseModel, Field

from .exceptions import ConfigurationError


class ${lib_class}Config(BaseModel):
    """Configuration settings for $lib."""

    # Environment settings
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security settings
    encryption_key: Optional[str] = Field(default=None, description="Encryption key for sensitive data")
    api_timeout: int = Field(default=30, description="Default API timeout in seconds")
    max_retries: int = Field(default=3, description="Default maximum retry attempts")

    @classmethod
    def from_env(cls) -> "${lib_class}Config":
        """Create configuration from environment variables."""
        try:
            return cls(
                environment=os.getenv("OPSVI_ENVIRONMENT", "development"),
                debug=os.getenv("OPSVI_DEBUG", "false").lower() == "true",
                log_level=os.getenv("OPSVI_LOG_LEVEL", "INFO").upper(),
                encryption_key=os.getenv("OPSVI_ENCRYPTION_KEY"),
                api_timeout=int(os.getenv("OPSVI_API_TIMEOUT", "30")),
                max_retries=int(os.getenv("OPSVI_MAX_RETRIES", "3"))
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.environment not in ["development", "staging", "production"]:
            raise ConfigurationError(f"Invalid environment: {self.environment}")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigurationError(f"Invalid log level: {self.log_level}")


# Global configuration instance
config = ${lib_class}Config.from_env()
EOF
done

echo "📊 Creating logging files..."

# Create logging files for all libraries
for lib in opsvi-core opsvi-llm opsvi-rag opsvi-agents; do
    lib_name=$(echo $lib | tr '-' '_')

    cat > "$lib/$lib_name/core/logging.py" << EOF
"""
Structured logging setup for $lib.

Provides consistent logging configuration across all components.
"""

import logging
import sys
from typing import Any
import structlog
import orjson

from .config import config


def setup_logging() -> None:
    """Configure structured logging for the application."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(serializer=orjson.dumps),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_context(**kwargs: Any) -> structlog.stdlib.BoundLogger:
    """Create a logger with additional context."""
    return structlog.get_logger().bind(**kwargs)


# Set up logging on import
setup_logging()
logger = get_logger(__name__)
logger.info("Logging configured", library="$lib", version="1.0.0")
EOF
done

echo "✅ Boilerplate creation completed!"
