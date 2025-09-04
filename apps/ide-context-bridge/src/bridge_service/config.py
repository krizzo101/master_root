#!/usr/bin/env python3
"""
Configuration management for IDE Context Bridge.

Handles loading configuration from files, environment variables, and defaults.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 8080
    websocket_path: str = "/ide-bridge"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    max_connections: int = 1000
    connection_timeout: int = 300  # seconds


@dataclass
class DatabaseConfig:
    """Database configuration."""

    postgres_url: str = "postgresql://opsvi:password@localhost:5432/unified_context"
    redis_url: Optional[str] = "redis://localhost:6379/0"
    connection_pool_size: int = 20
    connection_timeout: int = 60
    query_timeout: int = 30


@dataclass
class EmbeddingConfig:
    """Embedding service configuration."""

    service_url: str = "http://localhost:8001"
    model: str = "sentence-transformers"
    batch_size: int = 100
    timeout: int = 30
    max_retries: int = 3


@dataclass
class SearchConfig:
    """Search configuration."""

    default_similarity_threshold: float = 0.7
    max_results: int = 10
    cache_ttl: int = 300  # seconds
    enable_hybrid_search: bool = True
    vector_search_limit: int = 50


@dataclass
class SecurityConfig:
    """Security configuration."""

    require_auth: bool = False
    api_key_header: str = "X-API-Key"
    allowed_api_keys: List[str] = field(default_factory=list)
    rate_limit: str = "100/minute"
    enable_cors: bool = True
    jwt_secret: Optional[str] = None
    jwt_expire_hours: int = 24


@dataclass
class CacheConfig:
    """Caching configuration."""

    enable_suggestion_cache: bool = True
    enable_search_cache: bool = True
    suggestion_cache_ttl: int = 300
    search_cache_ttl: int = 600
    max_cache_size: int = 1000


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""

    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    performance_tracking: bool = True
    detailed_metrics: bool = False


@dataclass
class BridgeConfig:
    """Main configuration class for IDE Context Bridge."""

    # Sub-configurations
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Legacy properties for backward compatibility
    @property
    def host(self) -> str:
        return self.server.host

    @property
    def port(self) -> int:
        return self.server.port

    @property
    def cors_origins(self) -> List[str]:
        return self.server.cors_origins

    @property
    def postgres_url(self) -> str:
        return self.database.postgres_url

    @property
    def redis_url(self) -> Optional[str]:
        return self.database.redis_url

    @property
    def embedding_service_url(self) -> str:
        return self.embedding.service_url

    @property
    def log_level(self) -> str:
        return self.logging.level

    @property
    def max_suggestions(self) -> int:
        return self.search.max_results


def load_config(config_path: Optional[str] = None) -> BridgeConfig:
    """
    Load configuration from file and environment variables.

    Args:
        config_path: Path to configuration file (YAML)

    Returns:
        BridgeConfig instance
    """
    config = BridgeConfig()

    # Load from file if provided
    if config_path:
        config = _load_from_file(config_path, config)

    # Override with environment variables
    config = _load_from_env(config)

    # Validate configuration
    _validate_config(config)

    logger.info("Configuration loaded successfully")
    return config


def _load_from_file(file_path: str, config: BridgeConfig) -> BridgeConfig:
    """Load configuration from YAML file."""
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return config

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"Empty config file: {file_path}")
            return config

        # Update configuration sections
        if "server" in data:
            config.server = _update_dataclass(config.server, data["server"])

        if "database" in data:
            config.database = _update_dataclass(config.database, data["database"])

        if "embedding" in data:
            config.embedding = _update_dataclass(config.embedding, data["embedding"])

        if "search" in data:
            config.search = _update_dataclass(config.search, data["search"])

        if "security" in data:
            config.security = _update_dataclass(config.security, data["security"])

        if "cache" in data:
            config.cache = _update_dataclass(config.cache, data["cache"])

        if "logging" in data:
            config.logging = _update_dataclass(config.logging, data["logging"])

        if "monitoring" in data:
            config.monitoring = _update_dataclass(config.monitoring, data["monitoring"])

        logger.info(f"Loaded configuration from: {file_path}")
        return config

    except Exception as e:
        logger.error(f"Failed to load config file {file_path}: {e}")
        return config


def _update_dataclass(instance: Any, data: Dict[str, Any]) -> Any:
    """Update dataclass instance with dictionary data."""
    for key, value in data.items():
        if hasattr(instance, key):
            setattr(instance, key, value)
    return instance


def _load_from_env(config: BridgeConfig) -> BridgeConfig:
    """Load configuration from environment variables."""

    # Server configuration
    config.server.host = os.getenv("BRIDGE_HOST", config.server.host)
    config.server.port = int(os.getenv("BRIDGE_PORT", config.server.port))
    config.server.websocket_path = os.getenv(
        "BRIDGE_WS_PATH", config.server.websocket_path
    )

    # CORS origins from environment
    cors_origins_env = os.getenv("BRIDGE_CORS_ORIGINS")
    if cors_origins_env:
        config.server.cors_origins = [
            origin.strip() for origin in cors_origins_env.split(",")
        ]

    # Database configuration
    config.database.postgres_url = os.getenv(
        "POSTGRES_URL", config.database.postgres_url
    )
    config.database.redis_url = os.getenv("REDIS_URL", config.database.redis_url)

    # Embedding service
    config.embedding.service_url = os.getenv(
        "EMBEDDING_SERVICE_URL", config.embedding.service_url
    )
    config.embedding.model = os.getenv("EMBEDDING_MODEL", config.embedding.model)

    # Security
    config.security.require_auth = (
        os.getenv("BRIDGE_REQUIRE_AUTH", "false").lower() == "true"
    )
    config.security.api_key_header = os.getenv(
        "BRIDGE_API_KEY_HEADER", config.security.api_key_header
    )

    # API keys from environment
    api_keys_env = os.getenv("BRIDGE_API_KEYS")
    if api_keys_env:
        config.security.allowed_api_keys = [
            key.strip() for key in api_keys_env.split(",")
        ]

    # Rate limiting
    config.security.rate_limit = os.getenv(
        "BRIDGE_RATE_LIMIT", config.security.rate_limit
    )

    # JWT configuration
    config.security.jwt_secret = os.getenv(
        "BRIDGE_JWT_SECRET", config.security.jwt_secret
    )

    # Logging
    config.logging.level = os.getenv("LOG_LEVEL", config.logging.level).upper()
    config.logging.file_path = os.getenv("LOG_FILE_PATH", config.logging.file_path)

    # Search configuration
    threshold_env = os.getenv("BRIDGE_SIMILARITY_THRESHOLD")
    if threshold_env:
        config.search.default_similarity_threshold = float(threshold_env)

    max_results_env = os.getenv("BRIDGE_MAX_RESULTS")
    if max_results_env:
        config.search.max_results = int(max_results_env)

    # Cache configuration
    config.cache.enable_suggestion_cache = (
        os.getenv("BRIDGE_ENABLE_SUGGESTION_CACHE", "true").lower() == "true"
    )
    config.cache.enable_search_cache = (
        os.getenv("BRIDGE_ENABLE_SEARCH_CACHE", "true").lower() == "true"
    )

    # Monitoring
    config.monitoring.enable_metrics = (
        os.getenv("BRIDGE_ENABLE_METRICS", "true").lower() == "true"
    )

    metrics_port_env = os.getenv("BRIDGE_METRICS_PORT")
    if metrics_port_env:
        config.monitoring.metrics_port = int(metrics_port_env)

    return config


def _validate_config(config: BridgeConfig):
    """Validate configuration values."""
    errors = []

    # Server validation
    if not (1 <= config.server.port <= 65535):
        errors.append(f"Invalid server port: {config.server.port}")

    if not (1 <= config.monitoring.metrics_port <= 65535):
        errors.append(f"Invalid metrics port: {config.monitoring.metrics_port}")

    # Database validation
    if not config.database.postgres_url:
        errors.append("PostgreSQL URL is required")

    if not config.database.postgres_url.startswith(("postgresql://", "postgres://")):
        errors.append("Invalid PostgreSQL URL format")

    # Embedding service validation
    if not config.embedding.service_url:
        errors.append("Embedding service URL is required")

    if not config.embedding.service_url.startswith(("http://", "https://")):
        errors.append("Invalid embedding service URL format")

    # Search validation
    if not (0.0 <= config.search.default_similarity_threshold <= 1.0):
        errors.append(
            f"Similarity threshold must be between 0.0 and 1.0: {config.search.default_similarity_threshold}"
        )

    if config.search.max_results <= 0:
        errors.append(f"Max results must be positive: {config.search.max_results}")

    # Security validation
    if config.security.require_auth and not config.security.allowed_api_keys:
        logger.warning("Authentication is required but no API keys are configured")

    # Logging validation
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.logging.level not in valid_log_levels:
        errors.append(
            f"Invalid log level: {config.logging.level}. Must be one of: {valid_log_levels}"
        )

    if errors:
        error_msg = "Configuration validation errors:\n" + "\n".join(
            f"- {error}" for error in errors
        )
        raise ValueError(error_msg)


def get_default_config_path() -> Optional[str]:
    """Get default configuration file path."""
    # Check common configuration locations
    possible_paths = [
        os.getenv("BRIDGE_CONFIG_PATH"),
        "./bridge-config.yaml",
        "./config.yaml",
        "/etc/ide-bridge/config.yaml",
        "~/.config/ide-bridge/config.yaml",
    ]

    for path in possible_paths:
        if path and Path(path).expanduser().exists():
            return str(Path(path).expanduser())

    return None


def create_sample_config(output_path: str = "./bridge-config.yaml"):
    """Create a sample configuration file."""
    sample_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "websocket_path": "/ide-bridge",
            "cors_origins": ["*"],
            "max_connections": 1000,
        },
        "database": {
            "postgres_url": "postgresql://opsvi:password@localhost:5432/unified_context",
            "redis_url": "redis://localhost:6379/0",
            "connection_pool_size": 20,
        },
        "embedding": {
            "service_url": "http://localhost:8001",
            "model": "sentence-transformers",
            "batch_size": 100,
            "timeout": 30,
        },
        "search": {
            "default_similarity_threshold": 0.7,
            "max_results": 10,
            "cache_ttl": 300,
            "enable_hybrid_search": True,
        },
        "security": {
            "require_auth": False,
            "api_key_header": "X-API-Key",
            "rate_limit": "100/minute",
            "enable_cors": True,
        },
        "cache": {
            "enable_suggestion_cache": True,
            "enable_search_cache": True,
            "suggestion_cache_ttl": 300,
            "search_cache_ttl": 600,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_path": None,
        },
        "monitoring": {
            "enable_metrics": True,
            "metrics_port": 9090,
            "health_check_interval": 30,
            "performance_tracking": True,
        },
    }

    try:
        with open(output_path, "w") as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
        logger.info(f"Sample configuration created at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to create sample config: {e}")
        raise


def print_config_summary(config: BridgeConfig):
    """Print a summary of the current configuration."""
    print(
        f"""
IDE Context Bridge Configuration Summary:
==========================================

Server:
  Host: {config.server.host}
  Port: {config.server.port}
  WebSocket Path: {config.server.websocket_path}
  Max Connections: {config.server.max_connections}

Database:
  PostgreSQL: {config.database.postgres_url}
  Redis: {config.database.redis_url or 'Not configured'}

Embedding Service:
  URL: {config.embedding.service_url}
  Model: {config.embedding.model}

Search:
  Similarity Threshold: {config.search.default_similarity_threshold}
  Max Results: {config.search.max_results}
  Hybrid Search: {config.search.enable_hybrid_search}

Security:
  Authentication Required: {config.security.require_auth}
  Rate Limiting: {config.security.rate_limit}
  CORS Enabled: {config.security.enable_cors}

Caching:
  Suggestion Cache: {config.cache.enable_suggestion_cache}
  Search Cache: {config.cache.enable_search_cache}

Logging:
  Level: {config.logging.level}
  File: {config.logging.file_path or 'Console only'}

Monitoring:
  Metrics Enabled: {config.monitoring.enable_metrics}
  Metrics Port: {config.monitoring.metrics_port}
  Performance Tracking: {config.monitoring.performance_tracking}
"""
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="IDE Context Bridge Configuration")
    parser.add_argument(
        "--create-sample", help="Create sample configuration file", metavar="PATH"
    )
    parser.add_argument(
        "--validate", help="Validate configuration file", metavar="PATH"
    )
    parser.add_argument(
        "--print-config", help="Print configuration summary", metavar="PATH"
    )

    args = parser.parse_args()

    if args.create_sample:
        create_sample_config(args.create_sample)
    elif args.validate:
        try:
            config = load_config(args.validate)
            print(f"✓ Configuration file {args.validate} is valid")
        except Exception as e:
            print(f"✗ Configuration validation failed: {e}")
    elif args.print_config:
        try:
            config = load_config(args.print_config)
            print_config_summary(config)
        except Exception as e:
            print(f"✗ Failed to load configuration: {e}")
    else:
        # Print default configuration
        config = load_config()
        print_config_summary(config)
