"""Database connections for Project Context MCP Server."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

import asyncpg
import redis.asyncio as redis
import structlog
from neo4j import AsyncGraphDatabase

from ..ingestion.database import DatabaseConnectionPool, IngestionDatabase

logger = structlog.get_logger(__name__)


class UnifiedContextConnections:
    """Manages connections to unified context backend with enhanced performance."""

    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver = None
        self.redis_client: Optional[redis.Redis] = None
        self.ingestion_pool: Optional[DatabaseConnectionPool] = None
        self.ingestion_db: Optional[IngestionDatabase] = None

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
        """Connect to all databases with enhanced performance."""
        await self.connect_postgres()
        await self.connect_ingestion_pool()
        await self.connect_neo4j()
        await self.connect_redis()

    async def connect_postgres(self):
        """Connect to PostgreSQL with optimized connection pooling."""
        try:
            self.pg_pool = await asyncpg.create_pool(
                self.pg_dsn,
                min_size=5,
                max_size=20,
                command_timeout=120,
                server_settings={
                    "application_name": "unified_context_dashboard",
                },
            )
            # Test connection
            async with self.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            logger.info("Connected to PostgreSQL", dsn=self.pg_dsn.split("@")[1])
        except Exception as e:
            logger.error("Failed to connect to PostgreSQL", error=str(e))
            raise

    async def connect_ingestion_pool(self):
        """Initialize the ingestion database pool for high-performance operations."""
        try:
            self.ingestion_pool = DatabaseConnectionPool(
                database_url=self.pg_dsn,
                min_connections=5,
                max_connections=30,
                command_timeout=120,
            )
            await self.ingestion_pool.initialize()
            self.ingestion_db = IngestionDatabase(self.ingestion_pool)
            logger.info("Ingestion database pool initialized")
        except Exception as e:
            logger.error("Failed to initialize ingestion pool", error=str(e))
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
        if self.ingestion_pool:
            await self.ingestion_pool.close()
        if self.pg_pool:
            await self.pg_pool.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        if self.redis_client:
            await self.redis_client.close()

    # Enhanced PostgreSQL query helpers
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row from PostgreSQL using optimized pool."""
        if self.ingestion_pool:
            row = await self.ingestion_pool.execute_query(query, *args, fetch="one")
            return dict(row) if row else None
        else:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None

    async def fetch_many(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows from PostgreSQL using optimized pool."""
        if self.ingestion_pool:
            rows = await self.ingestion_pool.execute_query(query, *args, fetch="all")
            return [dict(row) for row in rows]
        else:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]

    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results using optimized pool."""
        if self.ingestion_pool:
            return await self.ingestion_pool.execute_query(query, *args, fetch="none")
        else:
            async with self.pg_pool.acquire() as conn:
                return await conn.execute(query, *args)

    # Unified Context Query Methods
    async def search_context_items(
        self,
        source_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        file_path: Optional[str] = None,
        content_search: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search context items with enhanced filtering."""
        conditions = ["1=1"]
        params = []
        param_idx = 1

        if source_types:
            conditions.append(f"source_type = ANY(${param_idx})")
            params.append(source_types)
            param_idx += 1

        if entity_types:
            conditions.append(f"entity_type = ANY(${param_idx})")
            params.append(entity_types)
            param_idx += 1

        if project_id:
            conditions.append(f"project_id = ${param_idx}")
            params.append(project_id)
            param_idx += 1

        if file_path:
            conditions.append(f"file_path ILIKE ${param_idx}")
            params.append(f"%{file_path}%")
            param_idx += 1

        if content_search:
            conditions.append(f"(content ILIKE ${param_idx} OR title ILIKE ${param_idx + 1})")
            params.extend([f"%{content_search}%", f"%{content_search}%"])
            param_idx += 2

        query = f"""
            SELECT * FROM context_items
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        return await self.fetch_many(query, *params)

    async def get_file_context(self, file_path: str) -> Dict[str, Any]:
        """Get all context items for a specific file."""
        items = await self.search_context_items(file_path=file_path)

        # Group by entity type for better organization
        by_type = {}
        for item in items:
            entity_type = item.get("entity_type", "unknown")
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(item)

        return {
            "file_path": file_path,
            "total_items": len(items),
            "items": items,
            "by_type": by_type,
        }

    async def get_project_stats(self) -> Dict[str, Any]:
        """Get comprehensive project statistics from unified context."""
        stats_query = """
            SELECT
                source_type,
                entity_type,
                COUNT(*) as count,
                COUNT(DISTINCT project_id) as unique_projects,
                COUNT(DISTINCT file_path) as unique_files,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM context_items
            GROUP BY source_type, entity_type
            ORDER BY source_type, entity_type
        """

        rows = await self.fetch_many(stats_query)

        # Aggregate stats
        total_items = sum(row["count"] for row in rows)
        unique_projects = len(set(row["project_id"] for row in rows if row.get("project_id")))

        return {
            "total_items": total_items,
            "unique_projects": unique_projects,
            "breakdown": rows,
            "generated_at": "NOW()",
        }

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
db_connections = UnifiedContextConnections()

# Legacy class for backward compatibility
DatabaseConnections = UnifiedContextConnections


async def initialize_connections():
    """Initialize all database connections with enhanced performance."""
    await db_connections.connect_all()
    logger.info("All database connections initialized")
    return db_connections


async def get_db():
    """Get the global unified context database connections instance."""
    if not db_connections.pg_pool:
        await initialize_connections()
    return db_connections


async def get_unified_context():
    """Get the ingestion database instance for advanced operations."""
    db = await get_db()
    if not db.ingestion_db:
        raise RuntimeError("Ingestion database not initialized")
    return db.ingestion_db
