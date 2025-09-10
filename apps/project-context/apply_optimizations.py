#!/usr/bin/env python3
"""
Apply database optimizations to the project-context system.
"""

import asyncio
from pathlib import Path

import asyncpg


async def apply_optimizations():
    """Apply database optimizations."""

    db_dsn = "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"

    # Read the optimization SQL
    sql_file = Path(__file__).parent / "database_optimizations.sql"
    with open(sql_file, "r") as f:
        sql_content = f.read()

    # Split into individual statements (rough approach)
    statements = []
    current_statement = []

    for line in sql_content.split("\n"):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("--"):
            continue

        current_statement.append(line)

        # End of statement
        if line.endswith(";"):
            statement = " ".join(current_statement).strip()
            if statement and not statement.startswith("DO $$"):
                statements.append(statement)
            elif statement.startswith("DO $$"):
                # Handle DO blocks specially
                do_block = []
                in_do_block = True
                for l in sql_content.split("\n")[
                    sql_content.split("\n").index(line.replace(";", ""))
                    - len(current_statement)
                    + 1 :
                ]:
                    do_block.append(l)
                    if l.strip() == "END $$;":
                        break
                statements.append("\n".join(do_block))

            current_statement = []

    # Connect and apply optimizations
    conn = await asyncpg.connect(db_dsn)

    try:
        print("Applying database optimizations...")

        successful = 0
        failed = 0

        # Apply each statement
        for i, statement in enumerate(statements, 1):
            try:
                if not statement.strip():
                    continue

                print(f"Executing statement {i}/{len(statements)}")
                print(f"Statement preview: {statement[:100]}...")

                await conn.execute(statement)
                successful += 1

            except Exception as e:
                print(f"Failed to execute statement {i}: {e}")
                print(f"Statement was: {statement[:200]}...")
                failed += 1

        print(f"\nOptimizations complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        # Test a few key indexes were created
        print("\nVerifying key optimizations...")

        # Check if new indexes exist
        check_indexes = [
            "idx_code_elements_file_path_optimized",
            "idx_code_elements_search_optimized",
            "idx_context_items_session_time",
        ]

        for index_name in check_indexes:
            result = await conn.fetchval(
                """
                SELECT COUNT(*) FROM pg_indexes
                WHERE indexname = $1 AND schemaname = 'public'
            """,
                index_name,
            )

            if result > 0:
                print(f"✓ Index {index_name} created successfully")
            else:
                print(f"✗ Index {index_name} not found")

        # Check materialized views
        check_views = ["project_complexity_stats", "dependency_analysis"]
        for view_name in check_views:
            result = await conn.fetchval(
                """
                SELECT COUNT(*) FROM pg_matviews
                WHERE matviewname = $1 AND schemaname = 'public'
            """,
                view_name,
            )

            if result > 0:
                print(f"✓ Materialized view {view_name} created successfully")
            else:
                print(f"✗ Materialized view {view_name} not found")

        # Refresh the materialized views
        print("\nRefreshing materialized views...")
        try:
            await conn.execute("SELECT refresh_performance_views()")
            print("✓ Materialized views refreshed successfully")
        except Exception as e:
            print(f"✗ Failed to refresh materialized views: {e}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(apply_optimizations())
