#!/usr/bin/env python3
"""
Performance Optimization Engine for Unified Context System

Automated optimization recommendations and capacity planning for:
- PostgreSQL query optimization
- Neo4j relationship queries
- pgvector search performance
- System resource optimization
- Materialized view refresh strategies
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import psycopg2
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRecommendation:
    category: str  # 'query', 'index', 'system', 'configuration'
    priority: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    impact_estimate: str
    implementation_effort: str
    sql_commands: List[str]
    verification_query: str
    estimated_improvement_percent: float


@dataclass
class PerformanceMetric:
    component: str
    metric_name: str
    current_value: float
    target_value: float
    trend_direction: str  # 'improving', 'stable', 'degrading'
    measurement_unit: str
    timestamp: str


class PerformanceOptimizer:
    """Analyzes system performance and provides optimization recommendations."""

    def __init__(self, postgres_config: Dict, neo4j_config: Dict):
        self.postgres_config = postgres_config
        self.neo4j_config = neo4j_config
        self.postgres_conn = None
        self.neo4j_driver = None
        self.performance_history = []
        self.recommendations = []

    async def initialize(self):
        """Initialize database connections."""
        try:
            # PostgreSQL connection
            self.postgres_conn = psycopg2.connect(**self.postgres_config)
            self.postgres_conn.autocommit = True

            # Neo4j connection
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_config["uri"],
                auth=(self.neo4j_config["user"], self.neo4j_config["password"]),
            )

            logger.info("Performance optimizer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize performance optimizer: {e}")
            raise

    async def analyze_system_performance(self) -> Dict[str, Any]:
        """Comprehensive system performance analysis."""
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "postgres_analysis": await self._analyze_postgres_performance(),
            "neo4j_analysis": await self._analyze_neo4j_performance(),
            "vector_analysis": await self._analyze_vector_search_performance(),
            "system_analysis": await self._analyze_system_resources(),
            "materialized_views_analysis": await self._analyze_materialized_views(),
            "recommendations": await self._generate_recommendations(),
        }

        # Store in history
        self.performance_history.append(analysis_results)

        # Keep only last 100 analyses
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        return analysis_results

    async def _analyze_postgres_performance(self) -> Dict[str, Any]:
        """Analyze PostgreSQL performance metrics."""
        try:
            cursor = self.postgres_conn.cursor()

            # Query performance analysis
            cursor.execute(
                """
                SELECT
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    rows,
                    shared_blks_hit,
                    shared_blks_read,
                    temp_blks_written
                FROM pg_stat_statements
                WHERE calls > 10
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """
            )

            slow_queries = cursor.fetchall()

            # Table statistics
            cursor.execute(
                """
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins + n_tup_upd + n_tup_del as total_modifications,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    analyze_count,
                    vacuum_count
                FROM pg_stat_user_tables
                ORDER BY total_modifications DESC
            """
            )

            table_stats = cursor.fetchall()

            # Index usage analysis
            cursor.execute(
                """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_scan > 0
                ORDER BY idx_scan DESC
            """
            )

            index_stats = cursor.fetchall()

            # Database size and bloat estimation
            cursor.execute(
                """
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    count(*) as total_tables,
                    sum(n_live_tup) as total_live_tuples,
                    sum(n_dead_tup) as total_dead_tuples
                FROM pg_stat_user_tables
            """
            )

            db_stats = cursor.fetchone()

            # Connection and activity stats
            cursor.execute(
                """
                SELECT
                    count(*) as total_connections,
                    count(*) filter (where state = 'active') as active_connections,
                    count(*) filter (where state = 'idle') as idle_connections,
                    count(*) filter (where state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity
                WHERE pid <> pg_backend_pid()
            """
            )

            connection_stats = cursor.fetchone()

            return {
                "slow_queries": [
                    {
                        "query": query[0][:200] + "..."
                        if len(query[0]) > 200
                        else query[0],
                        "calls": query[1],
                        "total_time_ms": round(query[2], 2),
                        "mean_time_ms": round(query[3], 2),
                        "max_time_ms": round(query[4], 2),
                        "rows_per_call": round(
                            query[5] / query[1] if query[1] > 0 else 0, 2
                        ),
                        "cache_hit_ratio": round(
                            (query[6] / (query[6] + query[7]) * 100)
                            if (query[6] + query[7]) > 0
                            else 0,
                            2,
                        ),
                    }
                    for query in slow_queries
                ],
                "table_statistics": [
                    {
                        "schema": stat[0],
                        "table": stat[1],
                        "total_modifications": stat[2],
                        "seq_scans": stat[6],
                        "index_scans": stat[8],
                        "scan_efficiency": round(
                            (stat[8] / (stat[6] + stat[8]) * 100)
                            if (stat[6] + stat[8]) > 0
                            else 0,
                            2,
                        ),
                    }
                    for stat in table_stats[:10]
                ],
                "index_usage": [
                    {
                        "table": stat[1],
                        "index": stat[2],
                        "scans": stat[3],
                        "efficiency": round(
                            (stat[5] / stat[4] * 100) if stat[4] > 0 else 0, 2
                        ),
                    }
                    for stat in index_stats[:10]
                ],
                "database_overview": {
                    "size": db_stats[0],
                    "total_tables": db_stats[1],
                    "live_tuples": db_stats[2],
                    "dead_tuples": db_stats[3],
                    "bloat_ratio": round(
                        (db_stats[3] / (db_stats[2] + db_stats[3]) * 100)
                        if (db_stats[2] + db_stats[3]) > 0
                        else 0,
                        2,
                    ),
                },
                "connections": {
                    "total": connection_stats[0],
                    "active": connection_stats[1],
                    "idle": connection_stats[2],
                    "idle_in_transaction": connection_stats[3],
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing PostgreSQL performance: {e}")
            return {"error": str(e)}

    async def _analyze_neo4j_performance(self) -> Dict[str, Any]:
        """Analyze Neo4j performance metrics."""
        try:
            with self.neo4j_driver.session() as session:
                # Query performance analysis
                result = session.run(
                    """
                    CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Kernel')
                    YIELD attributes
                    RETURN attributes.NumberOfOpenTransactions.value as open_transactions,
                           attributes.NumberOfRolledBackTransactions.value as rolled_back_transactions
                """
                )

                transaction_stats = result.single()

                # Memory usage
                memory_result = session.run(
                    """
                    CALL dbms.queryJmx('java.lang:type=Memory')
                    YIELD attributes
                    RETURN attributes.HeapMemoryUsage.value as heap_memory
                """
                )

                memory_stats = memory_result.single()

                # Database size metrics
                size_result = session.run(
                    """
                    CALL apoc.monitor.store()
                    YIELD logSize, stringStoreSize, arrayStoreSize, relStoreSize, propStoreSize, totalStoreSize
                    RETURN logSize, stringStoreSize, arrayStoreSize, relStoreSize, propStoreSize, totalStoreSize
                """
                )

                size_stats = size_result.single()

                # Most connected nodes analysis
                connected_nodes_result = session.run(
                    """
                    MATCH (n)
                    WITH n, size((n)--()) as degree
                    WHERE degree > 0
                    RETURN labels(n)[0] as node_type,
                           count(n) as node_count,
                           avg(degree) as avg_degree,
                           max(degree) as max_degree
                    ORDER BY avg_degree DESC
                    LIMIT 10
                """
                )

                connectivity_stats = [dict(record) for record in connected_nodes_result]

                # Relationship density by type
                relationship_stats_result = session.run(
                    """
                    MATCH ()-[r]->()
                    WITH type(r) as rel_type, count(r) as rel_count
                    MATCH (n)
                    WITH rel_type, rel_count, count(n) as total_nodes
                    RETURN rel_type, rel_count,
                           toFloat(rel_count) / total_nodes as density_ratio
                    ORDER BY rel_count DESC
                    LIMIT 10
                """
                )

                relationship_stats = [
                    dict(record) for record in relationship_stats_result
                ]

                return {
                    "transaction_metrics": {
                        "open_transactions": transaction_stats["open_transactions"]
                        if transaction_stats
                        else 0,
                        "rolled_back_transactions": transaction_stats[
                            "rolled_back_transactions"
                        ]
                        if transaction_stats
                        else 0,
                    },
                    "memory_usage": {
                        "heap_used_mb": round(
                            memory_stats["heap_memory"]["used"] / 1024 / 1024, 2
                        )
                        if memory_stats and memory_stats["heap_memory"]
                        else 0,
                        "heap_max_mb": round(
                            memory_stats["heap_memory"]["max"] / 1024 / 1024, 2
                        )
                        if memory_stats and memory_stats["heap_memory"]
                        else 0,
                        "heap_usage_percent": round(
                            (
                                memory_stats["heap_memory"]["used"]
                                / memory_stats["heap_memory"]["max"]
                                * 100
                            )
                            if memory_stats and memory_stats["heap_memory"]
                            else 0,
                            2,
                        ),
                    },
                    "storage_metrics": {
                        "total_store_size_mb": round(
                            size_stats["totalStoreSize"] / 1024 / 1024, 2
                        )
                        if size_stats
                        else 0,
                        "relationship_store_mb": round(
                            size_stats["relStoreSize"] / 1024 / 1024, 2
                        )
                        if size_stats
                        else 0,
                        "property_store_mb": round(
                            size_stats["propStoreSize"] / 1024 / 1024, 2
                        )
                        if size_stats
                        else 0,
                    },
                    "connectivity_analysis": connectivity_stats,
                    "relationship_distribution": relationship_stats,
                }

        except Exception as e:
            logger.error(f"Error analyzing Neo4j performance: {e}")
            return {"error": str(e)}

    async def _analyze_vector_search_performance(self) -> Dict[str, Any]:
        """Analyze pgvector search performance."""
        try:
            cursor = self.postgres_conn.cursor()

            # Vector index statistics
            cursor.execute(
                """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE indexname LIKE '%embedding%'
                   OR indexname LIKE '%vector%'
            """
            )

            vector_indexes = cursor.fetchall()

            # Vector search performance test
            test_vector = [0.1] * 384
            search_times = []

            for i in range(5):  # Run 5 test searches
                start_time = time.time()

                cursor.execute(
                    """
                    SELECT file_path, embedding <-> %s::vector as distance
                    FROM context_items
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <-> %s::vector
                    LIMIT 10
                """,
                    (test_vector, test_vector),
                )

                results = cursor.fetchall()
                search_time = (time.time() - start_time) * 1000
                search_times.append(search_time)

            # Embedding statistics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_vectors,
                    COUNT(*) filter (where embedding IS NOT NULL) as non_null_vectors,
                    AVG(array_length(embedding, 1)) as avg_dimensions,
                    pg_size_pretty(sum(pg_column_size(embedding))) as total_vector_size
                FROM context_items
            """
            )

            vector_stats = cursor.fetchone()

            return {
                "vector_indexes": [
                    {
                        "schema": idx[0],
                        "table": idx[1],
                        "index_name": idx[2],
                        "size": idx[3],
                    }
                    for idx in vector_indexes
                ],
                "search_performance": {
                    "avg_search_time_ms": round(np.mean(search_times), 2),
                    "min_search_time_ms": round(min(search_times), 2),
                    "max_search_time_ms": round(max(search_times), 2),
                    "search_time_std_ms": round(np.std(search_times), 2),
                },
                "vector_statistics": {
                    "total_vectors": vector_stats[0],
                    "non_null_vectors": vector_stats[1],
                    "coverage_percent": round(
                        (vector_stats[1] / vector_stats[0] * 100)
                        if vector_stats[0] > 0
                        else 0,
                        2,
                    ),
                    "avg_dimensions": vector_stats[2],
                    "total_size": vector_stats[3],
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing vector search performance: {e}")
            return {"error": str(e)}

    async def _analyze_system_resources(self) -> Dict[str, Any]:
        """Analyze system resource utilization."""
        # CPU usage over time
        cpu_measurements = []
        for _ in range(5):
            cpu_measurements.append(psutil.cpu_percent(interval=1))

        # Memory analysis
        memory = psutil.virtual_memory()

        # Disk analysis
        disk = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()

        # Network analysis
        network_io = psutil.net_io_counters()

        # Process analysis
        processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"]
        ):
            try:
                info = proc.info
                if info["cpu_percent"] > 1.0 or info["memory_percent"] > 1.0:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x["cpu_percent"], reverse=True)

        return {
            "cpu_metrics": {
                "avg_usage_percent": round(np.mean(cpu_measurements), 2),
                "max_usage_percent": round(max(cpu_measurements), 2),
                "core_count": psutil.cpu_count(),
                "load_average": list(psutil.getloadavg())
                if hasattr(psutil, "getloadavg")
                else [0, 0, 0],
            },
            "memory_metrics": {
                "total_gb": round(memory.total / 1024**3, 2),
                "available_gb": round(memory.available / 1024**3, 2),
                "used_percent": memory.percent,
                "cached_gb": round(getattr(memory, "cached", 0) / 1024**3, 2),
            },
            "disk_metrics": {
                "total_gb": round(disk.total / 1024**3, 2),
                "free_gb": round(disk.free / 1024**3, 2),
                "used_percent": disk.percent,
                "io_read_mb": round(disk_io.read_bytes / 1024**2, 2)
                if disk_io
                else 0,
                "io_write_mb": round(disk_io.write_bytes / 1024**2, 2)
                if disk_io
                else 0,
            },
            "network_metrics": {
                "bytes_sent_mb": round(network_io.bytes_sent / 1024**2, 2)
                if network_io
                else 0,
                "bytes_recv_mb": round(network_io.bytes_recv / 1024**2, 2)
                if network_io
                else 0,
                "packets_sent": network_io.packets_sent if network_io else 0,
                "packets_recv": network_io.packets_recv if network_io else 0,
            },
            "top_processes": processes[:10],
        }

    async def _analyze_materialized_views(self) -> Dict[str, Any]:
        """Analyze materialized view performance and refresh patterns."""
        try:
            cursor = self.postgres_conn.cursor()

            # Get materialized view statistics
            cursor.execute(
                """
                SELECT
                    schemaname,
                    matviewname,
                    pg_size_pretty(pg_total_relation_size(oid)) as size,
                    n_tup_ins + n_tup_upd + n_tup_del as total_changes
                FROM pg_stat_user_tables
                JOIN pg_class ON pg_class.relname = tablename
                WHERE relkind = 'm'  -- materialized views
            """
            )

            mv_stats = cursor.fetchall()

            # Check refresh frequency and patterns
            cursor.execute(
                """
                SELECT
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time
                FROM pg_stat_statements
                WHERE query LIKE '%REFRESH MATERIALIZED VIEW%'
                ORDER BY calls DESC
            """
            )

            refresh_stats = cursor.fetchall()

            return {
                "materialized_views": [
                    {
                        "schema": mv[0],
                        "name": mv[1],
                        "size": mv[2],
                        "total_changes": mv[3],
                    }
                    for mv in mv_stats
                ],
                "refresh_patterns": [
                    {
                        "query": refresh[0],
                        "calls": refresh[1],
                        "total_time_ms": round(refresh[2], 2),
                        "avg_time_ms": round(refresh[3], 2),
                    }
                    for refresh in refresh_stats
                ],
            }

        except Exception as e:
            logger.error(f"Error analyzing materialized views: {e}")
            return {"error": str(e)}

    async def _generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []

        # Analyze recent performance data
        if len(self.performance_history) > 0:
            latest_analysis = self.performance_history[-1]

            # PostgreSQL recommendations
            pg_analysis = latest_analysis.get("postgres_analysis", {})

            # Slow query recommendations
            slow_queries = pg_analysis.get("slow_queries", [])
            if slow_queries:
                for query in slow_queries[:3]:  # Top 3 slowest
                    if query["mean_time_ms"] > 100:  # Queries over 100ms
                        recommendations.append(
                            OptimizationRecommendation(
                                category="query",
                                priority="high"
                                if query["mean_time_ms"] > 1000
                                else "medium",
                                title=f"Optimize slow query (avg: {query['mean_time_ms']:.0f}ms)",
                                description=f"Query with {query['calls']} calls averaging {query['mean_time_ms']:.1f}ms execution time",
                                impact_estimate=f"Could improve response time by 30-50%",
                                implementation_effort="Medium - requires query analysis and potential indexing",
                                sql_commands=[
                                    f"EXPLAIN (ANALYZE, BUFFERS) {query['query'][:100]}...",
                                    "-- Add appropriate indexes based on EXPLAIN output",
                                ],
                                verification_query=f"SELECT mean_exec_time FROM pg_stat_statements WHERE query LIKE '%{query['query'][:50]}%'",
                                estimated_improvement_percent=35.0,
                            )
                        )

            # Index recommendations
            table_stats = pg_analysis.get("table_statistics", [])
            for table in table_stats:
                if table["scan_efficiency"] < 50 and table["seq_scans"] > 100:
                    recommendations.append(
                        OptimizationRecommendation(
                            category="index",
                            priority="medium",
                            title=f"Add indexes to {table['table']} table",
                            description=f"Table has {table['scan_efficiency']:.1f}% index scan efficiency with {table['seq_scans']} sequential scans",
                            impact_estimate="Could reduce query time by 60-80%",
                            implementation_effort="Low - single CREATE INDEX command",
                            sql_commands=[
                                f"CREATE INDEX CONCURRENTLY idx_{table['table']}_common_queries ON {table['table']} (column_name);",
                                "-- Replace column_name with frequently queried columns",
                            ],
                            verification_query=f"SELECT idx_scan, seq_scan FROM pg_stat_user_tables WHERE tablename = '{table['table']}'",
                            estimated_improvement_percent=70.0,
                        )
                    )

            # Vacuum recommendations
            db_overview = pg_analysis.get("database_overview", {})
            if db_overview.get("bloat_ratio", 0) > 20:
                recommendations.append(
                    OptimizationRecommendation(
                        category="maintenance",
                        priority="medium",
                        title="Reduce table bloat with VACUUM",
                        description=f"Database has {db_overview['bloat_ratio']:.1f}% dead tuple bloat ratio",
                        impact_estimate="Could recover disk space and improve query performance by 15-25%",
                        implementation_effort="Low - automated maintenance command",
                        sql_commands=[
                            "VACUUM ANALYZE;",
                            "-- Consider VACUUM FULL for heavily bloated tables during maintenance window",
                        ],
                        verification_query="SELECT sum(n_dead_tup), sum(n_live_tup) FROM pg_stat_user_tables",
                        estimated_improvement_percent=20.0,
                    )
                )

            # Vector search recommendations
            vector_analysis = latest_analysis.get("vector_analysis", {})
            search_perf = vector_analysis.get("search_performance", {})

            if search_perf.get("avg_search_time_ms", 0) > 50:
                recommendations.append(
                    OptimizationRecommendation(
                        category="vector",
                        priority="high",
                        title="Optimize vector search performance",
                        description=f"Vector searches averaging {search_perf['avg_search_time_ms']:.1f}ms",
                        impact_estimate="Could improve vector search speed by 40-60%",
                        implementation_effort="Medium - requires index tuning",
                        sql_commands=[
                            "CREATE INDEX CONCURRENTLY idx_context_items_embedding_ivfflat ON context_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
                            "-- Adjust lists parameter based on data size",
                        ],
                        verification_query="SELECT avg(execution_time) FROM vector_search_performance_log",
                        estimated_improvement_percent=50.0,
                    )
                )

            # System resource recommendations
            system_analysis = latest_analysis.get("system_analysis", {})
            cpu_metrics = system_analysis.get("cpu_metrics", {})
            memory_metrics = system_analysis.get("memory_metrics", {})

            if cpu_metrics.get("avg_usage_percent", 0) > 80:
                recommendations.append(
                    OptimizationRecommendation(
                        category="system",
                        priority="critical",
                        title="High CPU utilization detected",
                        description=f"CPU averaging {cpu_metrics['avg_usage_percent']:.1f}% utilization",
                        impact_estimate="Could improve overall system responsiveness by 30-40%",
                        implementation_effort="High - may require hardware upgrade or workload redistribution",
                        sql_commands=[],
                        verification_query="SELECT pg_stat_get_db_xact_commit(oid) FROM pg_database WHERE datname = current_database()",
                        estimated_improvement_percent=35.0,
                    )
                )

            if memory_metrics.get("used_percent", 0) > 85:
                recommendations.append(
                    OptimizationRecommendation(
                        category="system",
                        priority="high",
                        title="High memory utilization detected",
                        description=f"Memory usage at {memory_metrics['used_percent']:.1f}%",
                        impact_estimate="Could prevent system slowdown and improve cache efficiency",
                        implementation_effort="Medium - configuration tuning or memory upgrade",
                        sql_commands=[
                            "-- Consider adjusting PostgreSQL shared_buffers and work_mem parameters",
                            "-- Or increase system RAM",
                        ],
                        verification_query="SHOW shared_buffers",
                        estimated_improvement_percent=25.0,
                    )
                )

        # Sort by priority and impact
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(
            key=lambda x: (priority_order[x.priority], -x.estimated_improvement_percent)
        )

        return recommendations

    async def generate_capacity_planning_report(self) -> Dict[str, Any]:
        """Generate capacity planning recommendations."""
        if len(self.performance_history) < 2:
            return {"error": "Insufficient historical data for capacity planning"}

        # Analyze trends over time
        recent_data = self.performance_history[-10:]  # Last 10 measurements

        # Data growth trends
        data_growth = []
        for i in range(1, len(recent_data)):
            prev = recent_data[i - 1]
            curr = recent_data[i]

            prev_postgres = prev.get("postgres_analysis", {}).get(
                "database_overview", {}
            )
            curr_postgres = curr.get("postgres_analysis", {}).get(
                "database_overview", {}
            )

            if prev_postgres.get("live_tuples") and curr_postgres.get("live_tuples"):
                growth_rate = (
                    curr_postgres["live_tuples"] - prev_postgres["live_tuples"]
                ) / prev_postgres["live_tuples"]
                data_growth.append(growth_rate)

        avg_data_growth_rate = np.mean(data_growth) if data_growth else 0

        # Resource utilization trends
        cpu_trends = []
        memory_trends = []

        for analysis in recent_data:
            system_analysis = analysis.get("system_analysis", {})
            cpu_metrics = system_analysis.get("cpu_metrics", {})
            memory_metrics = system_analysis.get("memory_metrics", {})

            if cpu_metrics.get("avg_usage_percent"):
                cpu_trends.append(cpu_metrics["avg_usage_percent"])
            if memory_metrics.get("used_percent"):
                memory_trends.append(memory_metrics["used_percent"])

        # Capacity projections (3, 6, 12 months)
        projections = {}

        for months in [3, 6, 12]:
            current_data_size = (
                recent_data[-1]
                .get("postgres_analysis", {})
                .get("database_overview", {})
                .get("live_tuples", 0)
            )
            projected_data_size = (
                current_data_size * (1 + avg_data_growth_rate) ** months
            )

            current_cpu = np.mean(cpu_trends) if cpu_trends else 50
            current_memory = np.mean(memory_trends) if memory_trends else 50

            # Assume linear relationship between data growth and resource usage
            projected_cpu = (
                current_cpu * (projected_data_size / current_data_size) ** 0.7
            )  # Sublinear scaling
            projected_memory = (
                current_memory * (projected_data_size / current_data_size) ** 0.8
            )

            projections[f"{months}_months"] = {
                "data_growth_factor": round(projected_data_size / current_data_size, 2),
                "projected_cpu_percent": round(min(projected_cpu, 100), 1),
                "projected_memory_percent": round(min(projected_memory, 100), 1),
                "capacity_warnings": [],
            }

            # Add capacity warnings
            if projected_cpu > 80:
                projections[f"{months}_months"]["capacity_warnings"].append(
                    f"CPU utilization projected to reach {projected_cpu:.1f}% - consider CPU upgrade"
                )

            if projected_memory > 85:
                projections[f"{months}_months"]["capacity_warnings"].append(
                    f"Memory utilization projected to reach {projected_memory:.1f}% - consider RAM upgrade"
                )

        return {
            "analysis_period": f"Based on last {len(recent_data)} measurements",
            "current_growth_rate": {
                "data_growth_rate_per_period": round(avg_data_growth_rate * 100, 2),
                "avg_cpu_utilization": round(np.mean(cpu_trends), 1)
                if cpu_trends
                else 0,
                "avg_memory_utilization": round(np.mean(memory_trends), 1)
                if memory_trends
                else 0,
            },
            "capacity_projections": projections,
            "recommendations": [
                {
                    "category": "capacity_planning",
                    "timeline": "immediate",
                    "action": "Implement monitoring alerts at 80% CPU and 85% memory utilization",
                    "rationale": "Early warning system for capacity issues",
                },
                {
                    "category": "capacity_planning",
                    "timeline": "3_months",
                    "action": "Review and optimize database indexes and queries",
                    "rationale": "Preventive maintenance to handle growing data efficiently",
                },
                {
                    "category": "capacity_planning",
                    "timeline": "6_months",
                    "action": "Plan hardware upgrade if projections show >80% resource utilization",
                    "rationale": "Maintain performance headroom for peak loads",
                },
            ],
            "timestamp": datetime.now().isoformat(),
        }

    def export_performance_report(self, file_path: str):
        """Export comprehensive performance report."""
        if not self.performance_history:
            logger.warning("No performance data available for export")
            return

        latest_analysis = self.performance_history[-1]
        recommendations = self.recommendations[-20:] if self.recommendations else []

        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "system_name": "Unified Context System",
                "analysis_version": "2.0.0",
                "data_points": len(self.performance_history),
            },
            "executive_summary": {
                "total_recommendations": len(recommendations),
                "critical_issues": len(
                    [r for r in recommendations if r.priority == "critical"]
                ),
                "high_priority_issues": len(
                    [r for r in recommendations if r.priority == "high"]
                ),
                "estimated_total_improvement": sum(
                    [r.estimated_improvement_percent for r in recommendations[:5]]
                )
                / 5,
            },
            "current_performance": latest_analysis,
            "optimization_recommendations": [asdict(r) for r in recommendations],
            "capacity_planning": self.generate_capacity_planning_report(),
            "historical_trends": {
                "data_points": len(self.performance_history),
                "first_measurement": self.performance_history[0]["timestamp"]
                if self.performance_history
                else None,
                "latest_measurement": latest_analysis["timestamp"],
            },
        }

        with open(file_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Performance report exported to {file_path}")


# Async function to run performance analysis
async def run_performance_analysis():
    """Run comprehensive performance analysis."""
    optimizer = PerformanceOptimizer(
        postgres_config={
            "host": "localhost",
            "port": 5432,
            "database": "unified_context",
            "user": "opsvi",
            "password": "opsvi_secure_password",
        },
        neo4j_config={
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password",
        },
    )

    try:
        await optimizer.initialize()
        analysis_results = await optimizer.analyze_system_performance()

        # Generate and export report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = (
            f"/home/opsvi/master_root/PERFORMANCE_OPTIMIZATION_REPORT_{timestamp}.json"
        )
        optimizer.export_performance_report(report_path)

        print(f"Performance analysis complete. Report saved to: {report_path}")

        # Print key recommendations
        recommendations = analysis_results.get("recommendations", [])
        if recommendations:
            print(f"\nTop {min(5, len(recommendations))} Optimization Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"{i}. [{rec.priority.upper()}] {rec.title}")
                print(f"   Impact: {rec.impact_estimate}")
                print(f"   Effort: {rec.implementation_effort}")
                print()

        return analysis_results

    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    asyncio.run(run_performance_analysis())
