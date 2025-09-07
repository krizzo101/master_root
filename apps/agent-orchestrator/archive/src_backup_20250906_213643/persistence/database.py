"""
Database Connection and Configuration Management
PostgreSQL with connection pooling and Redis caching
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional
from urllib.parse import urlparse

import asyncpg
import redis.asyncio as aioredis
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration with environment variable support"""

    def __init__(
        self,
        postgres_url: str = "postgresql://localhost:5432/collaboration",
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 20,
        min_connections: int = 5,
        connection_timeout: int = 30,
        query_timeout: int = 60,
        enable_ssl: bool = False,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connection_timeout = connection_timeout
        self.query_timeout = query_timeout
        self.enable_ssl = enable_ssl
        self.pool_recycle = pool_recycle
        self.echo = echo

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables"""
        import os

        return cls(
            postgres_url=os.getenv(
                "COLLABORATION_DATABASE_URL",
                "postgresql://localhost:5432/collaboration",
            ),
            redis_url=os.getenv("COLLABORATION_REDIS_URL", "redis://localhost:6379/0"),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "5")),
            connection_timeout=int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
            query_timeout=int(os.getenv("DB_QUERY_TIMEOUT", "60")),
            enable_ssl=os.getenv("DB_ENABLE_SSL", "false").lower() == "true",
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )


class DatabaseManager:
    """Centralized database connection and pool management"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._redis_pool: Optional[aioredis.ConnectionPool] = None
        self._async_engine = None
        self._async_session_factory = None
        self._sync_engine = None
        self._sync_session_factory = None
        self._initialized = False

    async def initialize(self):
        """Initialize database connections and pools"""
        if self._initialized:
            return

        try:
            # Initialize PostgreSQL connection pool
            await self._init_postgres()

            # Initialize Redis connection pool
            await self._init_redis()

            # Initialize SQLAlchemy engines
            self._init_sqlalchemy()

            self._initialized = True
            logger.info("Database manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            await self.cleanup()
            raise

    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        parsed_url = urlparse(self.config.postgres_url)

        # Extract connection parameters
        host = parsed_url.hostname or "localhost"
        port = parsed_url.port or 5432
        database = parsed_url.path.lstrip("/") or "collaboration"
        user = parsed_url.username or "postgres"
        password = parsed_url.password or ""

        self._pg_pool = await asyncpg.create_pool(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
            timeout=self.config.connection_timeout,
            command_timeout=self.config.query_timeout,
            ssl="require" if self.config.enable_ssl else "disable",
        )

        logger.info(f"PostgreSQL pool created: {host}:{port}/{database}")

    async def _init_redis(self):
        """Initialize Redis connection pool"""
        self._redis_pool = aioredis.ConnectionPool.from_url(
            self.config.redis_url,
            max_connections=self.config.max_connections,
            socket_timeout=self.config.connection_timeout,
        )

        # Test Redis connection
        redis_client = aioredis.Redis(connection_pool=self._redis_pool)
        await redis_client.ping()

        logger.info(f"Redis pool created: {self.config.redis_url}")

    def _init_sqlalchemy(self):
        """Initialize SQLAlchemy async and sync engines"""
        # Convert postgres:// to postgresql+asyncpg://
        async_url = self.config.postgres_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

        # Async engine for modern async operations
        self._async_engine = create_async_engine(
            async_url,
            poolclass=QueuePool,
            pool_size=self.config.max_connections,
            max_overflow=10,
            pool_recycle=self.config.pool_recycle,
            echo=self.config.echo,
        )

        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Sync engine for migrations and simple operations
        sync_url = self.config.postgres_url.replace(
            "postgresql://", "postgresql+psycopg2://"
        )

        self._sync_engine = create_engine(
            sync_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=5,
            pool_recycle=self.config.pool_recycle,
            echo=self.config.echo,
        )

        self._sync_session_factory = sessionmaker(bind=self._sync_engine)

        logger.info("SQLAlchemy engines initialized")

    async def cleanup(self):
        """Cleanup database connections"""
        try:
            if self._pg_pool:
                await self._pg_pool.close()
                self._pg_pool = None

            if self._redis_pool:
                await self._redis_pool.disconnect()
                self._redis_pool = None

            if self._async_engine:
                await self._async_engine.dispose()
                self._async_engine = None

            if self._sync_engine:
                self._sync_engine.dispose()
                self._sync_engine = None

            self._initialized = False
            logger.info("Database connections cleaned up")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    @asynccontextmanager
    async def get_pg_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get PostgreSQL connection from pool"""
        if not self._pg_pool:
            raise RuntimeError("PostgreSQL pool not initialized")

        async with self._pg_pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def get_redis_client(self) -> AsyncGenerator[aioredis.Redis, None]:
        """Get Redis client from pool"""
        if not self._redis_pool:
            raise RuntimeError("Redis pool not initialized")

        client = aioredis.Redis(connection_pool=self._redis_pool)
        try:
            yield client
        finally:
            await client.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get SQLAlchemy async session"""
        if not self._async_session_factory:
            raise RuntimeError("Async session factory not initialized")

        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_sync_session(self):
        """Get SQLAlchemy sync session (for migrations)"""
        if not self._sync_session_factory:
            raise RuntimeError("Sync session factory not initialized")

        return self._sync_session_factory()

    async def create_tables(self):
        """Create all database tables"""
        if not self._async_engine:
            raise RuntimeError("Database not initialized")

        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created")

    async def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        if not self._async_engine:
            raise RuntimeError("Database not initialized")

        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("Database tables dropped")

    async def health_check(self) -> Dict[str, Any]:
        """Check database health status"""
        health = {
            "postgres": {"status": "unknown", "latency_ms": None},
            "redis": {"status": "unknown", "latency_ms": None},
        }

        # PostgreSQL health check
        try:
            start_time = asyncio.get_event_loop().time()
            async with self.get_pg_connection() as conn:
                await conn.fetchval("SELECT 1")
            latency = (asyncio.get_event_loop().time() - start_time) * 1000

            health["postgres"] = {"status": "healthy", "latency_ms": round(latency, 2)}
        except Exception as e:
            health["postgres"] = {"status": "unhealthy", "error": str(e)}

        # Redis health check
        try:
            start_time = asyncio.get_event_loop().time()
            async with self.get_redis_client() as redis:
                await redis.ping()
            latency = (asyncio.get_event_loop().time() - start_time) * 1000

            health["redis"] = {"status": "healthy", "latency_ms": round(latency, 2)}
        except Exception as e:
            health["redis"] = {"status": "unhealthy", "error": str(e)}

        return health


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager

    if _db_manager is None:
        config = DatabaseConfig.from_env()
        _db_manager = DatabaseManager(config)
        await _db_manager.initialize()

    return _db_manager


async def initialize_database(
    config: Optional[DatabaseConfig] = None,
) -> DatabaseManager:
    """Initialize database with custom configuration"""
    global _db_manager

    if config is None:
        config = DatabaseConfig.from_env()

    _db_manager = DatabaseManager(config)
    await _db_manager.initialize()

    return _db_manager


async def cleanup_database():
    """Cleanup global database manager"""
    global _db_manager

    if _db_manager:
        await _db_manager.cleanup()
        _db_manager = None
