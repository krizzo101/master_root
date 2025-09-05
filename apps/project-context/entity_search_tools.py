#!/usr/bin/env python3
"""
Entity Search Tools for MCP Integration
Provides advanced search capabilities based on extracted entities
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import asyncpg


class EntitySearchService:
    """Advanced entity search service for chat context analysis"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def search_by_entity_type(
        self, entity_type: str, limit: int = 50, min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search messages by entity type"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    ci.id,
                    ci.title,
                    ci.content,
                    ci.timestamp,
                    ci.session_id,
                    ee.entity_value,
                    ee.confidence,
                    ee.metadata
                FROM context_items ci
                JOIN extracted_entities ee ON ci.id = ee.context_item_id
                WHERE ee.entity_type = $1
                AND ee.confidence >= $2
                ORDER BY ci.timestamp DESC
                LIMIT $3
            """,
                entity_type,
                min_confidence,
                limit,
            )

            return [dict(row) for row in rows]

    async def search_by_entity_value(
        self,
        entity_value: str,
        entity_type: Optional[str] = None,
        exact_match: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search messages by specific entity value"""
        async with self.db_pool.acquire() as conn:
            if exact_match:
                if entity_type:
                    query = """
                        SELECT
                            ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                            ee.entity_type, ee.entity_value, ee.confidence, ee.metadata
                        FROM context_items ci
                        JOIN extracted_entities ee ON ci.id = ee.context_item_id
                        WHERE ee.entity_value = $1 AND ee.entity_type = $2
                        ORDER BY ci.timestamp DESC
                        LIMIT $3
                    """
                    rows = await conn.fetch(query, entity_value, entity_type, limit)
                else:
                    query = """
                        SELECT
                            ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                            ee.entity_type, ee.entity_value, ee.confidence, ee.metadata
                        FROM context_items ci
                        JOIN extracted_entities ee ON ci.id = ee.context_item_id
                        WHERE ee.entity_value = $1
                        ORDER BY ci.timestamp DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query, entity_value, limit)
            else:
                # Fuzzy search
                if entity_type:
                    query = """
                        SELECT
                            ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                            ee.entity_type, ee.entity_value, ee.confidence, ee.metadata
                        FROM context_items ci
                        JOIN extracted_entities ee ON ci.id = ee.context_item_id
                        WHERE ee.entity_value ILIKE $1 AND ee.entity_type = $2
                        ORDER BY ci.timestamp DESC
                        LIMIT $3
                    """
                    rows = await conn.fetch(
                        query, f"%{entity_value}%", entity_type, limit
                    )
                else:
                    query = """
                        SELECT
                            ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                            ee.entity_type, ee.entity_value, ee.confidence, ee.metadata
                        FROM context_items ci
                        JOIN extracted_entities ee ON ci.id = ee.context_item_id
                        WHERE ee.entity_value ILIKE $1
                        ORDER BY ci.timestamp DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query, f"%{entity_value}%", limit)

            return [dict(row) for row in rows]

    async def search_tech_keywords(
        self, keywords: List[str], category: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search messages containing specific tech keywords"""
        async with self.db_pool.acquire() as conn:
            if category:
                query = """
                    SELECT
                        ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                        ee.entity_value, ee.confidence, ee.metadata,
                        COUNT(*) as keyword_count
                    FROM context_items ci
                    JOIN extracted_entities ee ON ci.id = ee.context_item_id
                    WHERE ee.entity_type = 'tech_keyword'
                    AND ee.entity_value = ANY($1)
                    AND ee.metadata->>'category' = $2
                    GROUP BY ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                             ee.entity_value, ee.confidence, ee.metadata
                    ORDER BY keyword_count DESC, ci.timestamp DESC
                    LIMIT $3
                """
                rows = await conn.fetch(query, keywords, category, limit)
            else:
                query = """
                    SELECT
                        ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                        ee.entity_value, ee.confidence, ee.metadata,
                        COUNT(*) as keyword_count
                    FROM context_items ci
                    JOIN extracted_entities ee ON ci.id = ee.context_item_id
                    WHERE ee.entity_type = 'tech_keyword'
                    AND ee.entity_value = ANY($1)
                    GROUP BY ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                             ee.entity_value, ee.confidence, ee.metadata
                    ORDER BY keyword_count DESC, ci.timestamp DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, keywords, limit)

            return [dict(row) for row in rows]

    async def search_files_and_commands(
        self,
        file_pattern: Optional[str] = None,
        command_pattern: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search messages containing file paths or commands"""
        conditions = []
        params = []

        if file_pattern:
            conditions.append(
                "(ee.entity_type = 'file_path' AND ee.entity_value ILIKE $1)"
            )
            params.append(f"%{file_pattern}%")

        if command_pattern:
            param_num = len(params) + 1
            conditions.append(
                f"(ee.entity_type = 'command' AND ee.entity_value ILIKE ${param_num})"
            )
            params.append(f"%{command_pattern}%")

        if not conditions:
            return []

        async with self.db_pool.acquire() as conn:
            query = f"""
                SELECT DISTINCT
                    ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                    ee.entity_type, ee.entity_value, ee.confidence, ee.metadata
                FROM context_items ci
                JOIN extracted_entities ee ON ci.id = ee.context_item_id
                WHERE ({' OR '.join(conditions)})
                ORDER BY ci.timestamp DESC
                LIMIT ${len(params) + 1}
            """
            params.append(limit)
            rows = await conn.fetch(query, *params)

            return [dict(row) for row in rows]

    async def get_entity_statistics(self) -> Dict[str, Any]:
        """Get statistics about extracted entities"""
        async with self.db_pool.acquire() as conn:
            # Entity type distribution
            type_stats = await conn.fetch(
                """
                SELECT entity_type, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM extracted_entities
                GROUP BY entity_type
                ORDER BY count DESC
            """
            )

            # Recent entity extraction activity
            recent_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_entities,
                    COUNT(DISTINCT context_item_id) as messages_with_entities,
                    COUNT(DISTINCT entity_type) as unique_entity_types
                FROM extracted_entities
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
            )

            # Top entities by type
            top_entities = {}
            for entity_type in ["tech_keyword", "file_path", "command", "url"]:
                top = await conn.fetch(
                    """
                    SELECT entity_value, COUNT(*) as frequency
                    FROM extracted_entities
                    WHERE entity_type = $1
                    GROUP BY entity_value
                    ORDER BY frequency DESC
                    LIMIT 10
                """,
                    entity_type,
                )
                top_entities[entity_type] = [dict(row) for row in top]

            return {
                "entity_type_distribution": [dict(row) for row in type_stats],
                "recent_activity": dict(recent_stats),
                "top_entities": top_entities,
            }

    async def find_related_messages(
        self,
        context_item_id: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Find messages related by shared entities"""
        async with self.db_pool.acquire() as conn:
            if entity_types:
                query = """
                    WITH source_entities AS (
                        SELECT entity_type, entity_value
                        FROM extracted_entities
                        WHERE context_item_id = $1::uuid
                        AND entity_type = ANY($2)
                    )
                    SELECT DISTINCT
                        ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                        ee.entity_type, ee.entity_value,
                        COUNT(*) OVER (PARTITION BY ci.id) as shared_entity_count
                    FROM context_items ci
                    JOIN extracted_entities ee ON ci.id = ee.context_item_id
                    WHERE ee.context_item_id != $1::uuid
                    AND EXISTS (
                        SELECT 1 FROM source_entities se
                        WHERE se.entity_type = ee.entity_type
                        AND se.entity_value = ee.entity_value
                    )
                    ORDER BY shared_entity_count DESC, ci.timestamp DESC
                    LIMIT $3
                """
                rows = await conn.fetch(query, context_item_id, entity_types, limit)
            else:
                query = """
                    WITH source_entities AS (
                        SELECT entity_type, entity_value
                        FROM extracted_entities
                        WHERE context_item_id = $1::uuid
                    )
                    SELECT DISTINCT
                        ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                        ee.entity_type, ee.entity_value,
                        COUNT(*) OVER (PARTITION BY ci.id) as shared_entity_count
                    FROM context_items ci
                    JOIN extracted_entities ee ON ci.id = ee.context_item_id
                    WHERE ee.context_item_id != $1::uuid
                    AND EXISTS (
                        SELECT 1 FROM source_entities se
                        WHERE se.entity_type = ee.entity_type
                        AND se.entity_value = ee.entity_value
                    )
                    ORDER BY shared_entity_count DESC, ci.timestamp DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, context_item_id, limit)

            return [dict(row) for row in rows]

    async def search_by_time_and_entities(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        entity_filters: Optional[Dict[str, List[str]]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search messages by time range with entity filtering"""
        if end_time is None:
            end_time = datetime.now()

        base_query = """
            SELECT DISTINCT
                ci.id, ci.title, ci.content, ci.timestamp, ci.session_id,
                array_agg(DISTINCT ee.entity_type) as entity_types,
                array_agg(DISTINCT ee.entity_value) as entity_values
            FROM context_items ci
            LEFT JOIN extracted_entities ee ON ci.id = ee.context_item_id
            WHERE ci.timestamp BETWEEN $1 AND $2
        """

        params = [start_time, end_time]

        if entity_filters:
            conditions = []
            for entity_type, values in entity_filters.items():
                param_num = len(params) + 1
                conditions.append(
                    f"""
                    EXISTS (
                        SELECT 1 FROM extracted_entities ee2
                        WHERE ee2.context_item_id = ci.id
                        AND ee2.entity_type = ${param_num}
                        AND ee2.entity_value = ANY(${param_num + 1})
                    )
                """
                )
                params.extend([entity_type, values])

            if conditions:
                base_query += " AND (" + " OR ".join(conditions) + ")"

        base_query += f"""
            GROUP BY ci.id, ci.title, ci.content, ci.timestamp, ci.session_id
            ORDER BY ci.timestamp DESC
            LIMIT ${len(params) + 1}
        """
        params.append(limit)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            return [dict(row) for row in rows]


# Example usage and testing
async def main():
    """Test entity search functionality"""
    db_pool = await asyncpg.create_pool(
        "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        min_size=2,
        max_size=5,
    )

    try:
        search_service = EntitySearchService(db_pool)

        # Test statistics
        print("📊 Entity Statistics:")
        stats = await search_service.get_entity_statistics()
        print(json.dumps(stats, indent=2, default=str))

        # Test tech keyword search
        print("\n🔍 Python-related messages:")
        python_messages = await search_service.search_tech_keywords(["python"], limit=5)
        for msg in python_messages:
            print(f"  - {msg['timestamp']}: {msg['title']}")

        # Test file path search
        print("\n📁 File path mentions:")
        file_messages = await search_service.search_files_and_commands(
            file_pattern=".py", limit=5
        )
        for msg in file_messages:
            print(f"  - {msg['entity_value']}")

    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
