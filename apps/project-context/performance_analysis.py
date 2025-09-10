#!/usr/bin/env python3
"""
Performance Analysis Script for Project Context System
Benchmarks all 21 tools and analyzes database performance.
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import psutil

# Add the project context source to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from project_context.server.main import ProjectContextServer


@dataclass
class PerformanceMetric:
    """Performance metric for a tool."""

    tool_name: str
    execution_time_ms: float
    memory_delta_mb: float
    db_queries_count: int
    cache_hits: int
    cache_misses: int
    success: bool
    error: Optional[str] = None


@dataclass
class DatabasePerformanceMetric:
    """Database performance metric."""

    query: str
    execution_time_ms: float
    rows_returned: int
    table_name: str
    index_used: bool


class PerformanceAnalyzer:
    """Analyzes performance of the project-context system."""

    def __init__(self):
        self.server: Optional[ProjectContextServer] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.metrics: List[PerformanceMetric] = []
        self.db_metrics: List[DatabasePerformanceMetric] = []

        # Database connection string
        self.db_dsn = (
            "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
        )

        # Tools to benchmark - all 21 tools
        self.tools_to_test = [
            "get_project_summary",
            "get_file_info",
            "search_code",
            "get_dependencies",
            "get_imports",
            "get_call_graph",
            "get_data_models",
            "get_api_endpoints",
            "get_entry_points",
            "get_tests",
            "get_documentation",
            "get_config",
            "get_todos",
            "get_security_issues",
            "get_quality_metrics",
            "get_complexity",
            "get_recent_changes",
            "find_files",
            "find_symbols",
            "find_agents",
            "validate_intelligence",
        ]

    async def initialize(self):
        """Initialize the server and database connections."""
        print("Initializing performance analyzer...")

        # Initialize database pool
        self.db_pool = await asyncpg.create_pool(
            self.db_dsn, min_size=5, max_size=20, command_timeout=60
        )

        # Test database connection
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"Database connection test: {result}")

        # Initialize project context server
        self.server = ProjectContextServer()
        await self.server.initialize()
        print("Server initialized successfully")

    async def analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze current database schema and indexes."""
        print("Analyzing database schema...")

        schema_info = {
            "tables": {},
            "indexes": {},
            "table_sizes": {},
            "index_usage": {},
        }

        async with self.db_pool.acquire() as conn:
            # Get table information
            tables_query = """
            SELECT
                schemaname, tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """

            tables = await conn.fetch(tables_query)
            for table in tables:
                table_name = table["tablename"]
                schema_info["tables"][table_name] = {
                    "size": table["size"],
                    "size_bytes": table["size_bytes"],
                }

            # Get index information
            indexes_query = """
            SELECT
                schemaname, tablename, indexname,
                pg_size_pretty(pg_relation_size(indexname)) as size,
                pg_relation_size(indexname) as size_bytes
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY pg_relation_size(indexname) DESC;
            """

            indexes = await conn.fetch(indexes_query)
            for index in indexes:
                schema_info["indexes"][index["indexname"]] = {
                    "table": index["tablename"],
                    "size": index["size"],
                    "size_bytes": index["size_bytes"],
                }

            # Get index usage statistics
            index_usage_query = """
            SELECT
                schemaname, tablename, indexname,
                idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_tup_read DESC;
            """

            index_stats = await conn.fetch(index_usage_query)
            for stat in index_stats:
                schema_info["index_usage"][stat["indexname"]] = {
                    "table": stat["tablename"],
                    "reads": stat["idx_tup_read"],
                    "fetches": stat["idx_tup_fetch"],
                }

        return schema_info

    async def benchmark_tool(self, tool_name: str) -> PerformanceMetric:
        """Benchmark a specific tool."""
        print(f"Benchmarking tool: {tool_name}")

        # Get memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Prepare test parameters for each tool
        test_params = self._get_tool_test_params(tool_name)

        start_time = time.time()

        try:
            # Execute the tool
            if hasattr(self.server, tool_name):
                tool_method = getattr(self.server, tool_name)
                result = await tool_method(**test_params)

                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # Convert to ms

                # Get memory after
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = memory_after - memory_before

                return PerformanceMetric(
                    tool_name=tool_name,
                    execution_time_ms=execution_time,
                    memory_delta_mb=memory_delta,
                    db_queries_count=0,  # TODO: Implement query counting
                    cache_hits=0,  # TODO: Implement cache hit counting
                    cache_misses=0,  # TODO: Implement cache miss counting
                    success=True,
                )
            else:
                return PerformanceMetric(
                    tool_name=tool_name,
                    execution_time_ms=0,
                    memory_delta_mb=0,
                    db_queries_count=0,
                    cache_hits=0,
                    cache_misses=0,
                    success=False,
                    error=f"Tool {tool_name} not found",
                )

        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000

            return PerformanceMetric(
                tool_name=tool_name,
                execution_time_ms=execution_time,
                memory_delta_mb=0,
                db_queries_count=0,
                cache_hits=0,
                cache_misses=0,
                success=False,
                error=str(e),
            )

    def _get_tool_test_params(self, tool_name: str) -> Dict[str, Any]:
        """Get test parameters for each tool."""
        # Common parameters
        base_params = {}

        # Specific parameters for different tools
        if tool_name == "get_file_info":
            return {
                "file_path": "/home/opsvi/master_root/apps/project-context/src/project_context/server/main.py"
            }
        elif tool_name == "search_code":
            return {"query": "async def", "file_types": ["py"], "limit": 10}
        elif tool_name == "find_files":
            return {"pattern": "*.py", "limit": 10}
        elif tool_name == "find_symbols":
            return {"symbol": "ProjectContextServer", "limit": 10}
        elif tool_name == "find_agents":
            return {"agent_type": "mcp", "limit": 10}
        elif tool_name == "get_recent_changes":
            return {"time_range_hours": 24, "limit": 10}
        else:
            return base_params

    async def benchmark_database_queries(self) -> List[DatabasePerformanceMetric]:
        """Benchmark common database queries."""
        print("Benchmarking database queries...")

        db_metrics = []

        # Common queries to benchmark
        test_queries = [
            {
                "name": "get_recent_context_items",
                "query": """
                SELECT * FROM context_items
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC LIMIT 100;
                """,
                "table": "context_items",
            },
            {
                "name": "search_code_elements",
                "query": """
                SELECT * FROM code_elements
                WHERE element_name ILIKE %s
                ORDER BY last_modified DESC LIMIT 50;
                """,
                "table": "code_elements",
                "params": ["%main%"],
            },
            {
                "name": "get_file_activity",
                "query": """
                SELECT * FROM file_activity
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                ORDER BY timestamp DESC LIMIT 100;
                """,
                "table": "file_activity",
            },
            {
                "name": "get_session_context",
                "query": """
                SELECT c.*, ce.element_name, ce.file_path
                FROM code_context c
                LEFT JOIN code_elements ce ON c.code_element_id = ce.id
                WHERE c.session_id = %s
                ORDER BY c.timestamp DESC;
                """,
                "table": "code_context",
                "params": ["test_session"],
            },
            {
                "name": "aggregate_hourly_usage",
                "query": """
                SELECT
                    time_bucket('1 hour', timestamp) AS hour,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM context_items
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY hour
                ORDER BY hour;
                """,
                "table": "context_items",
            },
        ]

        async with self.db_pool.acquire() as conn:
            for query_info in test_queries:
                try:
                    start_time = time.time()

                    if "params" in query_info:
                        result = await conn.fetch(
                            query_info["query"], *query_info["params"]
                        )
                    else:
                        result = await conn.fetch(query_info["query"])

                    end_time = time.time()
                    execution_time = (end_time - start_time) * 1000  # Convert to ms

                    # Get query plan to check if index was used
                    explain_query = f"EXPLAIN (FORMAT JSON) {query_info['query']}"
                    if "params" in query_info:
                        plan = await conn.fetch(explain_query, *query_info["params"])
                    else:
                        plan = await conn.fetch(explain_query)

                    # Check if index was used (simplified check)
                    index_used = "Index" in str(plan)

                    db_metrics.append(
                        DatabasePerformanceMetric(
                            query=query_info["name"],
                            execution_time_ms=execution_time,
                            rows_returned=len(result),
                            table_name=query_info["table"],
                            index_used=index_used,
                        )
                    )

                except Exception as e:
                    print(f"Error benchmarking query {query_info['name']}: {e}")
                    db_metrics.append(
                        DatabasePerformanceMetric(
                            query=query_info["name"],
                            execution_time_ms=0,
                            rows_returned=0,
                            table_name=query_info["table"],
                            index_used=False,
                        )
                    )

        return db_metrics

    async def analyze_connection_pool(self) -> Dict[str, Any]:
        """Analyze connection pool performance."""
        print("Analyzing connection pool performance...")

        pool_stats = {
            "min_size": self.db_pool._minsize,
            "max_size": self.db_pool._maxsize,
            "current_size": self.db_pool.get_size(),
            "idle_count": self.db_pool.get_idle_size(),
            "connection_creation_time_ms": [],
        }

        # Test connection creation time
        for i in range(5):
            start_time = time.time()
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            end_time = time.time()
            creation_time = (end_time - start_time) * 1000
            pool_stats["connection_creation_time_ms"].append(creation_time)

        pool_stats["avg_connection_time_ms"] = sum(
            pool_stats["connection_creation_time_ms"]
        ) / len(pool_stats["connection_creation_time_ms"])

        return pool_stats

    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete performance analysis."""
        print("Starting full performance analysis...")

        analysis_results = {
            "timestamp": time.time(),
            "database_schema": await self.analyze_database_schema(),
            "connection_pool": await self.analyze_connection_pool(),
            "tool_benchmarks": [],
            "database_benchmarks": await self.benchmark_database_queries(),
            "summary": {},
        }

        # Benchmark all tools
        for tool_name in self.tools_to_test:
            metric = await self.benchmark_tool(tool_name)
            analysis_results["tool_benchmarks"].append(metric)
            self.metrics.append(metric)

        # Generate summary
        successful_tools = [m for m in self.metrics if m.success]
        failed_tools = [m for m in self.metrics if not m.success]

        if successful_tools:
            avg_execution_time = sum(
                m.execution_time_ms for m in successful_tools
            ) / len(successful_tools)
            max_execution_time = max(m.execution_time_ms for m in successful_tools)
            slow_tools = [m for m in successful_tools if m.execution_time_ms > 500]
        else:
            avg_execution_time = 0
            max_execution_time = 0
            slow_tools = []

        analysis_results["summary"] = {
            "total_tools_tested": len(self.tools_to_test),
            "successful_tools": len(successful_tools),
            "failed_tools": len(failed_tools),
            "avg_execution_time_ms": avg_execution_time,
            "max_execution_time_ms": max_execution_time,
            "slow_tools_count": len(slow_tools),
            "slow_tools": [
                {"name": t.tool_name, "time_ms": t.execution_time_ms}
                for t in slow_tools
            ],
        }

        return analysis_results

    async def cleanup(self):
        """Clean up resources."""
        if self.db_pool:
            await self.db_pool.close()
        if self.server:
            await self.server.cleanup()


async def main():
    """Main performance analysis function."""
    analyzer = PerformanceAnalyzer()

    try:
        await analyzer.initialize()
        results = await analyzer.run_full_analysis()

        # Save results to file
        output_file = (
            Path(__file__).parent / f"performance_report_{int(time.time())}.json"
        )

        # Convert dataclasses to dicts for JSON serialization
        json_results = {
            "timestamp": results["timestamp"],
            "database_schema": results["database_schema"],
            "connection_pool": results["connection_pool"],
            "tool_benchmarks": [
                {
                    "tool_name": m.tool_name,
                    "execution_time_ms": m.execution_time_ms,
                    "memory_delta_mb": m.memory_delta_mb,
                    "success": m.success,
                    "error": m.error,
                }
                for m in analyzer.metrics
            ],
            "database_benchmarks": [
                {
                    "query": m.query,
                    "execution_time_ms": m.execution_time_ms,
                    "rows_returned": m.rows_returned,
                    "table_name": m.table_name,
                    "index_used": m.index_used,
                }
                for m in results["database_benchmarks"]
            ],
            "summary": results["summary"],
        }

        with open(output_file, "w") as f:
            json.dump(json_results, f, indent=2)

        print(f"\nPerformance analysis complete!")
        print(f"Results saved to: {output_file}")
        print(f"\nSummary:")
        print(f"- Total tools tested: {results['summary']['total_tools_tested']}")
        print(f"- Successful tools: {results['summary']['successful_tools']}")
        print(f"- Failed tools: {results['summary']['failed_tools']}")
        print(
            f"- Average execution time: {results['summary']['avg_execution_time_ms']:.2f}ms"
        )
        print(
            f"- Maximum execution time: {results['summary']['max_execution_time_ms']:.2f}ms"
        )
        print(f"- Slow tools (>500ms): {results['summary']['slow_tools_count']}")

        if results["summary"]["slow_tools"]:
            print("\nSlow tools:")
            for tool in results["summary"]["slow_tools"]:
                print(f"  - {tool['name']}: {tool['time_ms']:.2f}ms")

        return results

    except Exception as e:
        print(f"Error during performance analysis: {e}")
        import traceback

        traceback.print_exc()
        return None
    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
