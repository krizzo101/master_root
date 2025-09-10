#!/usr/bin/env python3
"""
Apply key database optimizations to the project-context system.
"""

import asyncio

import asyncpg


async def apply_key_optimizations():
    """Apply key database optimizations."""

    db_dsn = "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"

    # Key optimization statements
    optimizations = [
        {
            "name": "File path optimization index",
            "sql": """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_file_path_optimized
            ON code_elements (file_path, element_type, line_start)
            WHERE element_type IN ('function', 'class', 'method');
            """,
        },
        {
            "name": "Search optimization index",
            "sql": """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_search_optimized
            ON code_elements (element_name, element_type, last_modified DESC)
            WHERE element_name IS NOT NULL;
            """,
        },
        {
            "name": "Dependencies GIN index",
            "sql": """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_dependencies_gin
            ON code_elements USING GIN (dependencies)
            WHERE dependencies IS NOT NULL;
            """,
        },
        {
            "name": "Recent modifications index",
            "sql": """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_recent_modified
            ON code_elements (last_modified DESC)
            WHERE last_modified >= NOW() - INTERVAL '7 days';
            """,
        },
        {
            "name": "Session-time optimization",
            "sql": """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_session_time
            ON context_items (session_id, timestamp DESC)
            WHERE session_id IS NOT NULL;
            """,
        },
        {
            "name": "File-source optimization",
            "sql": """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_file_source
            ON context_items (file_path, source_type, timestamp DESC)
            WHERE file_path IS NOT NULL;
            """,
        },
        {
            "name": "Code context joins optimization",
            "sql": """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_context_element_session
            ON code_context (code_element_id, session_id, timestamp DESC);
            """,
        },
        {
            "name": "Project complexity stats view",
            "sql": """
            CREATE MATERIALIZED VIEW IF NOT EXISTS project_complexity_stats AS
            SELECT
                language,
                element_type,
                COUNT(*) as element_count,
                AVG(complexity_score) as avg_complexity,
                MAX(complexity_score) as max_complexity,
                STDDEV(complexity_score) as complexity_stddev,
                COUNT(*) FILTER (WHERE complexity_score > 15) as high_complexity_count
            FROM code_elements
            WHERE complexity_score IS NOT NULL
            GROUP BY language, element_type;
            """,
        },
        {
            "name": "Complexity stats unique index",
            "sql": """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_project_complexity_stats_unique
            ON project_complexity_stats (language, element_type);
            """,
        },
        {
            "name": "Autovacuum settings for code_elements",
            "sql": """
            ALTER TABLE code_elements SET (
                autovacuum_vacuum_scale_factor = 0.1,
                autovacuum_analyze_scale_factor = 0.05
            );
            """,
        },
        {
            "name": "Performance views refresh function",
            "sql": """
            CREATE OR REPLACE FUNCTION refresh_performance_views()
            RETURNS void AS $$
            BEGIN
                REFRESH MATERIALIZED VIEW CONCURRENTLY project_complexity_stats;
                REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_token_usage;
                REFRESH MATERIALIZED VIEW CONCURRENTLY daily_file_activity;
                RAISE NOTICE 'Performance materialized views refreshed successfully';
            END;
            $$ LANGUAGE plpgsql;
            """,
        },
    ]

    # Connect and apply optimizations
    conn = await asyncpg.connect(db_dsn)

    try:
        print("Applying key database optimizations...")

        successful = 0
        failed = 0

        # Apply each optimization
        for opt in optimizations:
            try:
                print(f"Applying: {opt['name']}")
                await conn.execute(opt["sql"])
                print(f"✓ {opt['name']} applied successfully")
                successful += 1

            except Exception as e:
                print(f"✗ Failed to apply {opt['name']}: {e}")
                failed += 1

        print(f"\nOptimizations complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        # Refresh materialized views
        print("\nRefreshing materialized views...")
        try:
            await conn.execute("SELECT refresh_performance_views()")
            print("✓ Materialized views refreshed successfully")
        except Exception as e:
            print(f"Note: Some materialized views may need manual refresh: {e}")

        # Get current database statistics
        print("\nCurrent database statistics:")

        # Table sizes
        table_stats = await conn.fetch(
            """
            SELECT
                tablename,
                pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size('public.'||tablename) DESC
            LIMIT 5;
        """
        )

        print("Largest tables:")
        for row in table_stats:
            print(f"  - {row['tablename']}: {row['size']}")

        # Index count
        index_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'
        """
        )
        print(f"Total indexes: {index_count}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(apply_key_optimizations())
