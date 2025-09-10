#!/usr/bin/env python3
"""
Database Performance Analysis for Project Context System
Direct database benchmarking without server initialization.
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import psutil


@dataclass
class QueryPerformanceMetric:
    """Performance metric for a database query."""

    query_name: str
    execution_time_ms: float
    rows_returned: int
    table_name: str
    index_used: bool
    query_plan: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class IndexAnalysis:
    """Analysis of database indexes."""

    index_name: str
    table_name: str
    size_bytes: int
    usage_count: int
    efficiency_score: float  # usage per size
    recommendations: List[str]


class DatabasePerformanceAnalyzer:
    """Analyzes database performance for project-context system."""

    def __init__(self):
        self.db_dsn = (
            "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
        )
        self.db_pool: Optional[asyncpg.Pool] = None
        self.query_metrics: List[QueryPerformanceMetric] = []
        self.index_analyses: List[IndexAnalysis] = []

    async def initialize(self):
        """Initialize database connection pool."""
        print("Initializing database connection pool...")
        self.db_pool = await asyncpg.create_pool(
            self.db_dsn, min_size=5, max_size=20, command_timeout=60
        )

        # Test connection
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"Database connection test: {result}")

    async def analyze_table_sizes(self) -> Dict[str, Any]:
        """Analyze table sizes and row counts."""
        print("Analyzing table sizes...")

        query = """
        SELECT
            schemaname, tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
            (SELECT COUNT(*) FROM information_schema.columns
             WHERE table_schema = schemaname AND table_name = tablename) as column_count
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """

        async with self.db_pool.acquire() as conn:
            tables = await conn.fetch(query)

            # Get row counts for each table
            table_info = {}
            for table in tables:
                table_name = table["tablename"]
                try:
                    row_count = await conn.fetchval(
                        f"SELECT COUNT(*) FROM {table_name}"
                    )
                except Exception as e:
                    row_count = 0  # Handle tables without read access

                table_info[table_name] = {
                    "size": table["table_size"],
                    "size_bytes": table["size_bytes"],
                    "row_count": row_count,
                    "column_count": table["column_count"],
                }

        return table_info

    async def analyze_indexes(self) -> Dict[str, Any]:
        """Analyze index usage and performance."""
        print("Analyzing indexes...")

        # Get basic index information first
        index_query = """
        SELECT
            schemaname, tablename, indexname,
            pg_size_pretty(pg_relation_size((schemaname||'.'||indexname)::regclass)) as size,
            pg_relation_size((schemaname||'.'||indexname)::regclass) as size_bytes
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY pg_relation_size((schemaname||'.'||indexname)::regclass) DESC;
        """

        async with self.db_pool.acquire() as conn:
            indexes = await conn.fetch(index_query)

            # Get usage statistics separately
            usage_query = """
            SELECT indexrelname as indexname, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            """
            usage_stats = await conn.fetch(usage_query)
            usage_dict = {stat["indexname"]: stat for stat in usage_stats}

            index_info = {}
            for idx in indexes:
                index_name = idx["indexname"]
                usage = usage_dict.get(
                    index_name, {"idx_tup_read": 0, "idx_tup_fetch": 0}
                )

                # Calculate efficiency score
                usage_count = usage["idx_tup_read"] or 0
                size_bytes = idx["size_bytes"] or 1
                efficiency_score = usage_count / max(
                    size_bytes / 1024, 1
                )  # usage per KB

                # Generate recommendations
                recommendations = []
                if usage_count == 0:
                    recommendations.append("Consider dropping - unused index")
                elif efficiency_score < 0.01:
                    recommendations.append("Low efficiency - review if needed")
                else:
                    recommendations.append("Index appears to be used effectively")

                analysis = IndexAnalysis(
                    index_name=index_name,
                    table_name=idx["tablename"],
                    size_bytes=size_bytes,
                    usage_count=usage_count,
                    efficiency_score=efficiency_score,
                    recommendations=recommendations,
                )

                self.index_analyses.append(analysis)
                index_info[index_name] = asdict(analysis)

        return index_info

    async def benchmark_query(
        self, query_name: str, query: str, table_name: str, params: List[Any] = None
    ) -> QueryPerformanceMetric:
        """Benchmark a specific query."""

        async with self.db_pool.acquire() as conn:
            try:
                # Execute query and measure time
                start_time = time.time()
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)
                end_time = time.time()

                execution_time = (end_time - start_time) * 1000  # Convert to ms

                # Get query plan
                explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"
                try:
                    if params:
                        plan_result = await conn.fetch(explain_query, *params)
                    else:
                        plan_result = await conn.fetch(explain_query)

                    plan_json = plan_result[0][0]  # Extract JSON from record
                    plan_str = json.dumps(plan_json, indent=2)

                    # Check if index was used
                    index_used = "Index" in plan_str

                except Exception as e:
                    plan_str = f"Error getting plan: {e}"
                    index_used = False

                return QueryPerformanceMetric(
                    query_name=query_name,
                    execution_time_ms=execution_time,
                    rows_returned=len(result),
                    table_name=table_name,
                    index_used=index_used,
                    query_plan=plan_str,
                    success=True,
                )

            except Exception as e:
                return QueryPerformanceMetric(
                    query_name=query_name,
                    execution_time_ms=0,
                    rows_returned=0,
                    table_name=table_name,
                    index_used=False,
                    success=False,
                    error=str(e),
                )

    async def benchmark_common_queries(self) -> List[QueryPerformanceMetric]:
        """Benchmark queries that simulate tool operations."""
        print("Benchmarking common queries...")

        # Simulate queries for each tool type
        test_queries = [
            # Project summary queries
            {
                "name": "project_summary_files",
                "query": "SELECT COUNT(*) as file_count FROM code_elements WHERE element_type = $1",
                "table": "code_elements",
                "params": ["file"],
            },
            {
                "name": "project_summary_functions",
                "query": "SELECT COUNT(*) as function_count FROM code_elements WHERE element_type = $1",
                "table": "code_elements",
                "params": ["function"],
            },
            # File info queries
            {
                "name": "get_file_info",
                "query": "SELECT * FROM code_elements WHERE file_path = $1 ORDER BY line_start",
                "table": "code_elements",
                "params": [
                    "/home/opsvi/master_root/apps/project-context/src/project_context/server/main.py"
                ],
            },
            # Search code queries
            {
                "name": "search_code_content",
                "query": """
                SELECT file_path, element_name, signature, line_start, line_end
                FROM code_elements
                WHERE element_name ILIKE $1
                ORDER BY last_modified DESC NULLS LAST
                LIMIT 50
                """,
                "table": "code_elements",
                "params": ["%async%"],
            },
            # Dependencies analysis
            {
                "name": "get_dependencies",
                "query": "SELECT DISTINCT dependencies FROM code_elements WHERE dependencies IS NOT NULL",
                "table": "code_elements",
            },
            # Recent changes
            {
                "name": "recent_file_activity",
                "query": """
                SELECT * FROM file_activity
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                ORDER BY timestamp DESC
                LIMIT 100
                """,
                "table": "file_activity",
            },
            # Context items (chat history)
            {
                "name": "recent_context_items",
                "query": """
                SELECT * FROM context_items
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC
                LIMIT 100
                """,
                "table": "context_items",
            },
            # Code context correlation
            {
                "name": "code_context_join",
                "query": """
                SELECT cc.*, ce.element_name, ce.signature
                FROM code_context cc
                LEFT JOIN code_elements ce ON cc.code_element_id = ce.id
                WHERE cc.session_id = $1
                ORDER BY cc.timestamp DESC
                LIMIT 50
                """,
                "table": "code_context",
                "params": ["test_session_123"],
            },
            # Aggregation queries (like hourly stats)
            {
                "name": "hourly_activity_stats",
                "query": """
                SELECT
                    date_trunc('hour', timestamp) AS hour,
                    COUNT(*) as activity_count,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM context_items
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY hour
                ORDER BY hour DESC
                """,
                "table": "context_items",
            },
            # Complex join query (worst case)
            {
                "name": "complex_correlation_query",
                "query": """
                SELECT
                    ci.title, ci.file_path, ci.timestamp,
                    ce.element_name, ce.element_type,
                    cc.symbols, cc.relevance_score
                FROM context_items ci
                LEFT JOIN code_context cc ON ci.session_id = cc.session_id
                LEFT JOIN code_elements ce ON cc.code_element_id = ce.id
                WHERE ci.timestamp >= NOW() - INTERVAL '1 hour'
                    AND ci.source_type = 'chat'
                ORDER BY ci.timestamp DESC
                LIMIT 20
                """,
                "table": "context_items",
            },
            # Full-text search simulation
            {
                "name": "full_text_search",
                "query": """
                SELECT file_path, element_name, signature, docstring
                FROM code_elements
                WHERE search_vector @@ plainto_tsquery('english', $1)
                ORDER BY ts_rank(search_vector, plainto_tsquery('english', $1)) DESC
                LIMIT 25
                """,
                "table": "code_elements",
                "params": ["async function"],
            },
        ]

        metrics = []
        for query_info in test_queries:
            print(f"  Benchmarking: {query_info['name']}")
            metric = await self.benchmark_query(
                query_info["name"],
                query_info["query"],
                query_info["table"],
                query_info.get("params"),
            )
            metrics.append(metric)
            self.query_metrics.append(metric)

        return metrics

    async def analyze_connection_pool_performance(self) -> Dict[str, Any]:
        """Analyze connection pool performance."""
        print("Analyzing connection pool performance...")

        connection_times = []
        for i in range(10):
            start_time = time.time()
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            end_time = time.time()
            connection_times.append((end_time - start_time) * 1000)

        return {
            "pool_min_size": self.db_pool._minsize,
            "pool_max_size": self.db_pool._maxsize,
            "current_size": self.db_pool.get_size(),
            "idle_connections": self.db_pool.get_idle_size(),
            "connection_times_ms": connection_times,
            "avg_connection_time_ms": sum(connection_times) / len(connection_times),
            "max_connection_time_ms": max(connection_times),
            "min_connection_time_ms": min(connection_times),
        }

    async def generate_optimization_recommendations(self) -> Dict[str, List[str]]:
        """Generate optimization recommendations based on analysis."""
        print("Generating optimization recommendations...")

        recommendations = {
            "database_indexes": [],
            "query_optimization": [],
            "connection_pool": [],
            "caching_strategy": [],
        }

        # Analyze query performance
        slow_queries = [
            m for m in self.query_metrics if m.success and m.execution_time_ms > 500
        ]
        queries_without_indexes = [
            m for m in self.query_metrics if m.success and not m.index_used
        ]

        if slow_queries:
            recommendations["query_optimization"].append(
                f"Found {len(slow_queries)} slow queries (>500ms). Consider optimization."
            )
            for query in slow_queries:
                recommendations["query_optimization"].append(
                    f"- {query.query_name}: {query.execution_time_ms:.2f}ms"
                )

        if queries_without_indexes:
            recommendations["database_indexes"].append(
                f"Found {len(queries_without_indexes)} queries not using indexes"
            )

        # Analyze index efficiency
        unused_indexes = [idx for idx in self.index_analyses if idx.usage_count == 0]
        if unused_indexes:
            recommendations["database_indexes"].append(
                f"Consider dropping {len(unused_indexes)} unused indexes to save space"
            )

        # Connection pool recommendations
        recommendations["connection_pool"].append(
            "Current pool size (5-20) seems appropriate for moderate load"
        )

        # Caching recommendations
        recommendations["caching_strategy"].append(
            "Implement Redis caching for frequently accessed queries"
        )
        recommendations["caching_strategy"].append(
            "Consider query result memoization for expensive operations"
        )
        recommendations["caching_strategy"].append(
            "Current TTL settings (60s file data, 300s stats) are reasonable"
        )

        return recommendations

    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete database performance analysis."""
        print("Starting comprehensive database performance analysis...")

        start_time = time.time()

        # Run all analysis components
        table_sizes = await self.analyze_table_sizes()
        index_analysis = await self.analyze_indexes()
        query_metrics = await self.benchmark_common_queries()
        connection_pool_stats = await self.analyze_connection_pool_performance()
        recommendations = await self.generate_optimization_recommendations()

        end_time = time.time()
        total_analysis_time = (end_time - start_time) * 1000

        # Generate summary statistics
        successful_queries = [m for m in query_metrics if m.success]
        failed_queries = [m for m in query_metrics if not m.success]

        if successful_queries:
            avg_query_time = sum(m.execution_time_ms for m in successful_queries) / len(
                successful_queries
            )
            max_query_time = max(m.execution_time_ms for m in successful_queries)
            slow_queries = [m for m in successful_queries if m.execution_time_ms > 500]
        else:
            avg_query_time = 0
            max_query_time = 0
            slow_queries = []

        results = {
            "analysis_metadata": {
                "timestamp": time.time(),
                "analysis_duration_ms": total_analysis_time,
                "database_dsn": self.db_dsn.split("@")[1],  # Hide credentials
            },
            "table_analysis": table_sizes,
            "index_analysis": index_analysis,
            "query_performance": {
                "total_queries_tested": len(query_metrics),
                "successful_queries": len(successful_queries),
                "failed_queries": len(failed_queries),
                "average_execution_time_ms": avg_query_time,
                "max_execution_time_ms": max_query_time,
                "slow_queries_count": len(slow_queries),
                "queries_using_indexes": len(
                    [m for m in successful_queries if m.index_used]
                ),
                "metrics": [asdict(m) for m in query_metrics],
            },
            "connection_pool_performance": connection_pool_stats,
            "optimization_recommendations": recommendations,
            "summary": {
                "performance_grade": "A"
                if avg_query_time < 100
                else "B"
                if avg_query_time < 300
                else "C",
                "critical_issues": len(slow_queries) + len(failed_queries),
                "optimization_priority": "HIGH"
                if slow_queries or failed_queries
                else "MEDIUM",
            },
        }

        return results

    async def cleanup(self):
        """Clean up database connections."""
        if self.db_pool:
            await self.db_pool.close()


async def main():
    """Main analysis function."""
    analyzer = DatabasePerformanceAnalyzer()

    try:
        await analyzer.initialize()
        results = await analyzer.run_full_analysis()

        # Save results
        output_file = (
            Path(__file__).parent / f"db_performance_report_{int(time.time())}.json"
        )
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Print summary
        print(f"\n{'='*60}")
        print("DATABASE PERFORMANCE ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Report saved to: {output_file}")
        print(
            f"Analysis duration: {results['analysis_metadata']['analysis_duration_ms']:.2f}ms"
        )
        print(f"Performance grade: {results['summary']['performance_grade']}")
        print(f"Critical issues: {results['summary']['critical_issues']}")

        qp = results["query_performance"]
        print(f"\nQuery Performance:")
        print(f"- Total queries tested: {qp['total_queries_tested']}")
        print(f"- Successful: {qp['successful_queries']}")
        print(f"- Failed: {qp['failed_queries']}")
        print(f"- Average execution time: {qp['average_execution_time_ms']:.2f}ms")
        print(f"- Maximum execution time: {qp['max_execution_time_ms']:.2f}ms")
        print(f"- Slow queries (>500ms): {qp['slow_queries_count']}")
        print(f"- Queries using indexes: {qp['queries_using_indexes']}")

        print(f"\nConnection Pool:")
        cp = results["connection_pool_performance"]
        print(
            f"- Pool size: {cp['current_size']} ({cp['pool_min_size']}-{cp['pool_max_size']})"
        )
        print(f"- Average connection time: {cp['avg_connection_time_ms']:.2f}ms")

        print(f"\nTop optimization priorities:")
        for category, recs in results["optimization_recommendations"].items():
            if recs:
                print(
                    f"- {category.replace('_', ' ').title()}: {len(recs)} recommendations"
                )

        return results

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback

        traceback.print_exc()
        return None
    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
