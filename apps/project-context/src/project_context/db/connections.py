"""Database connections for Project Context MCP Server."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

import asyncpg
import redis.asyncio as redis
from neo4j import AsyncGraphDatabase


class DatabaseConnections:
    """Manages connections to PostgreSQL, Neo4j, and Redis."""

    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver = None
        self.redis_client: Optional[redis.Redis] = None

        # Connection settings from environment or defaults
        self.pg_dsn = os.getenv(
            "POSTGRES_URL",
            "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        )
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", None)  # No auth for dev
        self.neo4j_pass = os.getenv("NEO4J_PASSWORD", None)
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))

    async def connect_all(self):
        """Connect to all databases."""
        await self.connect_postgres()
        await self.connect_neo4j()
        await self.connect_redis()

    async def connect_postgres(self):
        """Connect to PostgreSQL with connection pooling."""
        try:
            self.pg_pool = await asyncpg.create_pool(
                self.pg_dsn, min_size=5, max_size=20, command_timeout=60
            )
            # Test connection
            async with self.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            print(f"Connected to PostgreSQL: {self.pg_dsn.split('@')[1]}")
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def connect_neo4j(self):
        """Connect to Neo4j graph database."""
        try:
            auth = None
            if self.neo4j_user and self.neo4j_pass:
                auth = (self.neo4j_user, self.neo4j_pass)

            self.neo4j_driver = AsyncGraphDatabase.driver(self.neo4j_uri, auth=auth)
            # Test connection
            async with self.neo4j_driver.session() as session:
                await session.run("RETURN 1")
            print(f"Connected to Neo4j: {self.neo4j_uri}")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            # Neo4j is optional, so we don't raise
            self.neo4j_driver = None

    async def connect_redis(self):
        """Connect to Redis for Context Bridge integration."""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
            )
            # Test connection
            await self.redis_client.ping()
            print(f"Connected to Redis: {self.redis_host}:{self.redis_port}")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            # Redis is optional for Context Bridge
            self.redis_client = None

    async def close_all(self):
        """Close all database connections."""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        if self.redis_client:
            await self.redis_client.close()

    # PostgreSQL query helpers
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row from PostgreSQL."""
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_many(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows from PostgreSQL."""
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results."""
        async with self.pg_pool.acquire() as conn:
            return await conn.execute(query, *args)

    # Neo4j query helpers
    async def run_cypher(self, query: str, **params) -> List[Dict[str, Any]]:
        """Run a Cypher query on Neo4j."""
        if not self.neo4j_driver:
            return []

        async with self.neo4j_driver.session() as session:
            result = await session.run(query, **params)
            return [record.data() async for record in result]

    # Redis helpers for Context Bridge
    async def get_ide_context(self, key: str) -> Optional[Dict[str, Any]]:
        """Get current IDE context from Redis cache."""
        if not self.redis_client:
            return None

        value = await self.redis_client.get(f"context:{key}")
        return json.loads(value) if value else None

    async def subscribe_to_context(self, channel: str):
        """Subscribe to Context Bridge updates."""
        if not self.redis_client:
            return None

        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# Global connection instance
db_connections = DatabaseConnections()


async def initialize_connections():
    """Initialize all database connections."""
    await db_connections.connect_all()
    return db_connections


async def get_db():
    """Get the global database connections instance."""
    if not db_connections.pg_pool:
        await initialize_connections()
    return db_connections
