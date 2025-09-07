"""Production configuration for Sleuth Intel application."""

import logging
import os
from typing import Any, Dict, Optional


class ProductionConfig:
    """Production environment configuration."""

    # Environment
    ENV = "production"
    DEBUG = False
    TESTING = False

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", None)
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")

    # API Configuration
    API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100/hour")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))
    API_RETRY_DELAY = int(os.getenv("API_RETRY_DELAY", "1"))

    # Enformion API Configuration
    ENFORMION_API_URL = os.getenv("ENFORMION_API_URL", "https://api.enformion.com/v2")
    ENFORMION_API_KEY = os.getenv("ENFORMION_API_KEY", None)
    ENFORMION_REQUEST_TIMEOUT = int(os.getenv("ENFORMION_REQUEST_TIMEOUT", "60"))
    ENFORMION_MAX_CONCURRENT_REQUESTS = int(
        os.getenv("ENFORMION_MAX_CONCURRENT_REQUESTS", "10")
    )

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", None)
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "40"))
    DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "100"))
    REDIS_SOCKET_KEEPALIVE = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS = {
        1: 3,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    }

    # Cache Configuration
    CACHE_TYPE = "redis"
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))
    CACHE_KEY_PREFIX = "sleuth_intel:"
    CACHE_REDIS_URL = REDIS_URL

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/sleuth-intel/app.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "10"))

    # Performance Configuration
    WORKER_PROCESSES = int(os.getenv("WORKER_PROCESSES", "4"))
    WORKER_THREADS = int(os.getenv("WORKER_THREADS", "2"))
    WORKER_MAX_REQUESTS = int(os.getenv("WORKER_MAX_REQUESTS", "1000"))
    WORKER_MAX_REQUESTS_JITTER = int(os.getenv("WORKER_MAX_REQUESTS_JITTER", "50"))

    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # CORS Configuration
    CORS_ORIGINS = (
        os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    )
    CORS_ALLOW_CREDENTIALS = False
    CORS_MAX_AGE = 3600

    # Monitoring Configuration
    METRICS_ENABLED = True
    METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
    HEALTH_CHECK_PATH = "/health"
    READY_CHECK_PATH = "/ready"

    # Error Tracking
    SENTRY_DSN = os.getenv("SENTRY_DSN", None)
    SENTRY_ENVIRONMENT = "production"
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # Feature Flags
    FEATURE_ASYNC_PROCESSING = (
        os.getenv("FEATURE_ASYNC_PROCESSING", "true").lower() == "true"
    )
    FEATURE_CACHING = os.getenv("FEATURE_CACHING", "true").lower() == "true"
    FEATURE_RATE_LIMITING = os.getenv("FEATURE_RATE_LIMITING", "true").lower() == "true"

    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": cls.LOG_FORMAT, "datefmt": "%Y-%m-%d %H:%M:%S"},
                "json": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": cls.LOG_LEVEL,
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": cls.LOG_LEVEL,
                    "formatter": "json",
                    "filename": cls.LOG_FILE,
                    "maxBytes": cls.LOG_MAX_BYTES,
                    "backupCount": cls.LOG_BACKUP_COUNT,
                },
            },
            "root": {"level": cls.LOG_LEVEL, "handlers": ["console", "file"]},
            "loggers": {
                "sleuth_intel": {
                    "level": cls.LOG_LEVEL,
                    "handlers": ["console", "file"],
                    "propagate": False,
                }
            },
        }

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        required = [
            ("SECRET_KEY", cls.SECRET_KEY),
            ("ENFORMION_API_KEY", cls.ENFORMION_API_KEY),
            ("DATABASE_URL", cls.DATABASE_URL),
        ]

        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
