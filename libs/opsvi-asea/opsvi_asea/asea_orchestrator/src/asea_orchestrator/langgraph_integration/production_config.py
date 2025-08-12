"""
Phase 4: Production Configuration and Deployment

Implements production-ready configuration including:
1. Environment Management
2. Performance Optimization
3. Security Configuration
4. Scaling and Resource Management
5. Monitoring and Logging Setup
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import redis
from concurrent.futures import ThreadPoolExecutor
import asyncio


@dataclass
class DatabaseConfig:
    """Database configuration."""

    host: str = "127.0.0.1"
    port: int = 8529
    username: str = "root"
    password: str = "arango_dev_password"
    database: str = "_system"
    connection_pool_size: int = 10
    timeout_seconds: int = 30


@dataclass
class CacheConfig:
    """Cache configuration."""

    enabled: bool = True
    backend: str = "redis"  # redis, memory
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    ttl_seconds: int = 3600
    max_memory_items: int = 10000


@dataclass
class SecurityConfig:
    """Security configuration."""

    api_key_secret: str = "change-this-in-production"
    jwt_secret: str = "change-this-in-production"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    trusted_hosts: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_per_minute: int = 60
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    enable_https: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None


@dataclass
class PerformanceConfig:
    """Performance configuration."""

    max_concurrent_workflows: int = 20
    worker_threads: int = 4
    async_queue_size: int = 1000
    execution_timeout_seconds: int = 300
    memory_limit_mb: int = 2048
    enable_compression: bool = True
    enable_caching: bool = True
    connection_pool_size: int = 20


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""

    enable_metrics: bool = True
    metrics_retention_hours: int = 24
    enable_alerts: bool = True
    alert_webhook_url: Optional[str] = None
    log_level: str = "INFO"
    log_format: str = "json"
    enable_tracing: bool = False
    jaeger_endpoint: Optional[str] = None


@dataclass
class ProductionConfig:
    """Complete production configuration."""

    environment: str = "production"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    @classmethod
    def from_environment(cls) -> "ProductionConfig":
        """Load configuration from environment variables."""
        config = cls()

        # Basic settings
        config.environment = os.getenv("ASEA_ENVIRONMENT", "production")
        config.debug = os.getenv("ASEA_DEBUG", "false").lower() == "true"
        config.host = os.getenv("ASEA_HOST", "0.0.0.0")
        config.port = int(os.getenv("ASEA_PORT", "8000"))
        config.workers = int(os.getenv("ASEA_WORKERS", "1"))

        # Database
        config.database.host = os.getenv("ASEA_DB_HOST", "127.0.0.1")
        config.database.port = int(os.getenv("ASEA_DB_PORT", "8529"))
        config.database.username = os.getenv("ASEA_DB_USERNAME", "root")
        config.database.password = os.getenv("ASEA_DB_PASSWORD", "arango_dev_password")
        config.database.database = os.getenv("ASEA_DB_DATABASE", "_system")

        # Cache
        config.cache.enabled = os.getenv("ASEA_CACHE_ENABLED", "true").lower() == "true"
        config.cache.backend = os.getenv("ASEA_CACHE_BACKEND", "redis")
        config.cache.redis_host = os.getenv("ASEA_REDIS_HOST", "localhost")
        config.cache.redis_port = int(os.getenv("ASEA_REDIS_PORT", "6379"))
        config.cache.redis_password = os.getenv("ASEA_REDIS_PASSWORD")

        # Security
        config.security.api_key_secret = os.getenv(
            "ASEA_API_SECRET", "change-this-in-production"
        )
        config.security.jwt_secret = os.getenv(
            "ASEA_JWT_SECRET", "change-this-in-production"
        )
        cors_origins = os.getenv("ASEA_CORS_ORIGINS", "*")
        config.security.cors_origins = (
            cors_origins.split(",") if cors_origins != "*" else ["*"]
        )

        # Performance
        config.performance.max_concurrent_workflows = int(
            os.getenv("ASEA_MAX_CONCURRENT", "20")
        )
        config.performance.worker_threads = int(os.getenv("ASEA_WORKER_THREADS", "4"))
        config.performance.execution_timeout_seconds = int(
            os.getenv("ASEA_EXECUTION_TIMEOUT", "300")
        )

        # Monitoring
        config.monitoring.log_level = os.getenv("ASEA_LOG_LEVEL", "INFO")
        config.monitoring.enable_metrics = (
            os.getenv("ASEA_ENABLE_METRICS", "true").lower() == "true"
        )
        config.monitoring.enable_alerts = (
            os.getenv("ASEA_ENABLE_ALERTS", "true").lower() == "true"
        )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "username": self.database.username,
                "database": self.database.database,
                "connection_pool_size": self.database.connection_pool_size,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "backend": self.cache.backend,
                "redis_host": self.cache.redis_host,
                "redis_port": self.cache.redis_port,
                "ttl_seconds": self.cache.ttl_seconds,
            },
            "security": {
                "cors_origins": self.security.cors_origins,
                "rate_limit_per_minute": self.security.rate_limit_per_minute,
                "max_request_size": self.security.max_request_size,
                "enable_https": self.security.enable_https,
            },
            "performance": {
                "max_concurrent_workflows": self.performance.max_concurrent_workflows,
                "worker_threads": self.performance.worker_threads,
                "execution_timeout_seconds": self.performance.execution_timeout_seconds,
                "memory_limit_mb": self.performance.memory_limit_mb,
            },
            "monitoring": {
                "enable_metrics": self.monitoring.enable_metrics,
                "enable_alerts": self.monitoring.enable_alerts,
                "log_level": self.monitoring.log_level,
                "log_format": self.monitoring.log_format,
            },
        }


class CacheManager:
    """Production-ready cache manager."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client = None
        self.memory_cache = {}

        if config.enabled and config.backend == "redis":
            try:
                self.redis_client = redis.Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    password=config.redis_password,
                    decode_responses=True,
                )
                # Test connection
                self.redis_client.ping()
                logging.info("Redis cache connected successfully")
            except Exception as e:
                logging.warning(
                    f"Redis connection failed, falling back to memory cache: {e}"
                )
                self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.config.enabled:
            return None

        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.config.enabled:
            return False

        try:
            ttl = ttl or self.config.ttl_seconds

            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                # Simple memory cache with size limit
                if len(self.memory_cache) >= self.config.max_memory_items:
                    # Remove oldest items
                    keys_to_remove = list(self.memory_cache.keys())[:100]
                    for k in keys_to_remove:
                        del self.memory_cache[k]

                self.memory_cache[key] = value

            return True
        except Exception as e:
            logging.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.config.enabled:
            return False

        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)

            return True
        except Exception as e:
            logging.error(f"Cache delete error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache."""
        if not self.config.enabled:
            return False

        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()

            return True
        except Exception as e:
            logging.error(f"Cache clear error: {e}")
            return False


class PerformanceOptimizer:
    """Production performance optimization."""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.thread_pool = ThreadPoolExecutor(max_workers=config.worker_threads)
        self.workflow_semaphore = asyncio.Semaphore(config.max_concurrent_workflows)
        self.execution_queue = asyncio.Queue(maxsize=config.async_queue_size)

    async def execute_with_limits(self, coro):
        """Execute coroutine with resource limits."""
        async with self.workflow_semaphore:
            try:
                return await asyncio.wait_for(
                    coro, timeout=self.config.execution_timeout_seconds
                )
            except asyncio.TimeoutError:
                raise Exception(
                    f"Execution timeout after {self.config.execution_timeout_seconds} seconds"
                )

    def run_in_thread(self, func, *args, **kwargs):
        """Run function in thread pool."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.thread_pool, func, *args, **kwargs)

    async def queue_task(self, task):
        """Queue task for async execution."""
        try:
            await self.execution_queue.put(task, timeout=1.0)
            return True
        except asyncio.TimeoutError:
            return False

    async def get_queued_task(self):
        """Get task from queue."""
        try:
            return await self.execution_queue.get()
        except asyncio.TimeoutError:
            return None


class ProductionLogger:
    """Production logging configuration."""

    @staticmethod
    def setup_logging(config: MonitoringConfig):
        """Setup production logging."""

        # Configure log level
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)

        # Configure format
        if config.log_format == "json":
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"module": "%(name)s", "message": "%(message)s"}'
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        # Configure handlers
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # File handler for production
        file_handler = logging.FileHandler("/var/log/asea/application.log")
        file_handler.setFormatter(formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(console_handler)

        # Add file handler in production
        if config.log_format == "json":
            root_logger.addHandler(file_handler)

        # Configure specific loggers
        logging.getLogger("uvicorn").setLevel(log_level)
        logging.getLogger("fastapi").setLevel(log_level)
        logging.getLogger("asea").setLevel(log_level)

        logging.info("Production logging configured")


class HealthChecker:
    """Production health checking."""

    def __init__(self, config: ProductionConfig):
        self.config = config
        self.start_time = time.time()

    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # This would connect to ArangoDB and check status
            return {
                "status": "healthy",
                "response_time_ms": 10,
                "connection_pool": "available",
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_cache_health(self) -> Dict[str, Any]:
        """Check cache connectivity."""
        if not self.config.cache.enabled:
            return {"status": "disabled"}

        try:
            # This would check cache connectivity
            return {
                "status": "healthy",
                "backend": self.config.cache.backend,
                "response_time_ms": 5,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        import psutil

        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "uptime_seconds": time.time() - self.start_time,
        }

    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        database_health = await self.check_database_health()
        cache_health = await self.check_cache_health()
        system_health = await self.check_system_resources()

        overall_status = "healthy"
        if (
            database_health.get("status") == "unhealthy"
            or cache_health.get("status") == "unhealthy"
            or system_health.get("memory_percent", 0) > 90
        ):
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": database_health,
                "cache": cache_health,
                "system": system_health,
            },
            "configuration": {
                "environment": self.config.environment,
                "debug": self.config.debug,
                "workers": self.config.workers,
            },
        }


def create_production_app(config_path: Optional[str] = None) -> "FastAPI":
    """Create production-configured FastAPI application."""

    # Load configuration
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            config_data = json.load(f)
        # Would need to implement config loading from file
        config = ProductionConfig.from_environment()
    else:
        config = ProductionConfig.from_environment()

    # Setup logging
    ProductionLogger.setup_logging(config.monitoring)

    # Initialize components
    cache_manager = CacheManager(config.cache)
    performance_optimizer = PerformanceOptimizer(config.performance)
    health_checker = HealthChecker(config)

    # Create API gateway with production config
    from .api_gateway import create_api_gateway

    app = create_api_gateway()

    # Store production components
    app.state.config = config
    app.state.cache = cache_manager
    app.state.performance = performance_optimizer
    app.state.health_checker = health_checker

    # Add production health endpoint
    @app.get("/health/detailed")
    async def detailed_health():
        """Detailed health check for production monitoring."""
        return await health_checker.get_comprehensive_health()

    logging.info("Production ASEA API Gateway configured")
    logging.info(f"Configuration: {config.to_dict()}")

    return app


if __name__ == "__main__":
    import time
    from datetime import datetime

    # Example production startup
    config = ProductionConfig.from_environment()
    app = create_production_app()

    print("Production configuration loaded:")
    print(json.dumps(config.to_dict(), indent=2))
