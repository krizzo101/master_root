#!/usr/bin/env python3
"""Database integration for dashboard backend."""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append("/home/opsvi/master_root/apps/project-context/src")

from project_context.db.connections import get_db, initialize_connections


class DashboardDatabase:
    """Database integration for dashboard monitoring."""

    def __init__(self):
        self.db = None
        self._initialized = False

    async def initialize(self):
        """Initialize database connections."""
        try:
            self.db = await get_db()
            self._initialized = True
            print(f"✅ Dashboard database connected")
            return True
        except Exception as e:
            print(f"❌ Dashboard database failed: {e}")
            self._initialized = False
            return False

    async def get_status(self):
        """Get database connection status."""
        if not self._initialized:
            return {"connected": False, "error": "Database not initialized"}

        try:
            # Test PostgreSQL
            pg_status = bool(self.db.pg_pool)
            if pg_status:
                # Quick connectivity test
                result = await self.db.fetch_one("SELECT 1 as test")
                pg_status = result is not None

            # Test other connections
            redis_status = bool(self.db.redis_client)
            neo4j_status = bool(self.db.neo4j_driver)

            return {
                "connected": True,
                "postgres": pg_status,
                "redis": redis_status,
                "neo4j": neo4j_status,
                "ingestion_pool": bool(self.db.ingestion_db),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def get_project_stats(self):
        """Get project statistics from database."""
        if not self._initialized:
            return {"error": "Database not initialized"}

        try:
            stats = await self.db.get_project_stats()
            return stats
        except Exception as e:
            return {"error": f"Failed to get stats: {e}"}

    async def search_context(self, query: str, limit: int = 10):
        """Search context items in database."""
        if not self._initialized:
            return {"error": "Database not initialized"}

        try:
            items = await self.db.search_context_items(content_search=query, limit=limit)
            return {"query": query, "count": len(items), "items": items}
        except Exception as e:
            return {"error": f"Search failed: {e}"}


# Global database instance for dashboard
dashboard_db = DashboardDatabase()
