#!/usr/bin/env python3
"""
Comprehensive Health Check System for Unified Context System

Advanced diagnostic tools and health validation for:
- PostgreSQL + TimescaleDB + pgvector connectivity and performance
- Neo4j graph database integrity and query performance
- Vector search functionality and accuracy
- Real-time ingestion pipeline health
- System resource monitoring with predictive alerts
- Inter-component communication validation
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import docker
import numpy as np
import psutil
import psycopg2
import requests
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    component: str
    status: str  # 'healthy', 'warning', 'critical', 'offline'
    score: float  # 0-100 health score
    response_time_ms: float
    checks_performed: List[str]
    issues_found: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]
    timestamp: str


@dataclass
class DiagnosticReport:
    overall_health_score: float
    system_status: str
    component_results: List[HealthCheckResult]
    critical_issues: List[str]
    performance_summary: Dict[str, Any]
    capacity_warnings: List[str]
    next_recommended_check: str
    report_id: str
    timestamp: str


class ComprehensiveHealthChecker:
    """Advanced health checking with deep diagnostics."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.postgres_conn = None
        self.neo4j_driver = None
        self.health_history = []
        self.check_results = {}
        self.alert_thresholds = {
            "cpu_warning": 75.0,
            "cpu_critical": 85.0,
            "memory_warning": 80.0,
            "memory_critical": 90.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "query_time_warning": 100.0,  # ms
            "query_time_critical": 1000.0,  # ms
            "vector_search_warning": 50.0,  # ms
            "vector_search_critical": 200.0,  # ms
        }

    async def initialize(self):
        """Initialize connections for health checking."""
        try:
            # PostgreSQL connection
            if "postgres" in self.config:
                self.postgres_conn = psycopg2.connect(**self.config["postgres"])
                self.postgres_conn.autocommit = True

            # Neo4j connection
            if "neo4j" in self.config:
                self.neo4j_driver = GraphDatabase.driver(
                    self.config["neo4j"]["uri"],
                    auth=(
                        self.config["neo4j"]["user"],
                        self.config["neo4j"]["password"],
                    ),
                )
                # Test connection
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")

            logger.info("Health checker initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize health checker: {e}")
            raise

    async def run_comprehensive_health_check(self) -> DiagnosticReport:
        """Run complete system health check with deep diagnostics."""
        report_id = f"health_{int(time.time())}"
        start_time = time.time()

        logger.info(f"Starting comprehensive health check - Report ID: {report_id}")

        component_results = []
        critical_issues = []
        capacity_warnings = []

        # 1. PostgreSQL Health Check
        postgres_result = await self._check_postgres_health()
        component_results.append(postgres_result)
        if postgres_result.status == "critical":
            critical_issues.extend(postgres_result.issues_found)

        # 2. Neo4j Health Check
        neo4j_result = await self._check_neo4j_health()
        component_results.append(neo4j_result)
        if neo4j_result.status == "critical":
            critical_issues.extend(neo4j_result.issues_found)

        # 3. Vector Search Health Check
        vector_result = await self._check_vector_search_health()
        component_results.append(vector_result)
        if vector_result.status == "critical":
            critical_issues.extend(vector_result.issues_found)

        # 4. System Resources Health Check
        system_result = await self._check_system_resources()
        component_results.append(system_result)
        if system_result.status == "critical":
            critical_issues.extend(system_result.issues_found)

        # 5. Docker Services Health Check
        docker_result = await self._check_docker_services()
        component_results.append(docker_result)
        if docker_result.status == "critical":
            critical_issues.extend(docker_result.issues_found)

        # 6. Real-time Ingestion Health Check
        ingestion_result = await self._check_ingestion_pipeline()
        component_results.append(ingestion_result)
        if ingestion_result.status == "critical":
            critical_issues.extend(ingestion_result.issues_found)

        # 7. Inter-component Communication Check
        communication_result = await self._check_component_communication()
        component_results.append(communication_result)
        if communication_result.status == "critical":
            critical_issues.extend(communication_result.issues_found)

        # Calculate overall health score
        total_score = sum([result.score for result in component_results])
        overall_health_score = (
            total_score / len(component_results) if component_results else 0
        )

        # Determine overall system status
        if overall_health_score >= 90:
            system_status = "healthy"
        elif overall_health_score >= 70:
            system_status = "warning"
        else:
            system_status = "critical"

        # Performance summary
        performance_summary = {
            "total_check_time_ms": round((time.time() - start_time) * 1000, 2),
            "components_checked": len(component_results),
            "avg_response_time_ms": round(
                np.mean([r.response_time_ms for r in component_results]), 2
            ),
            "max_response_time_ms": max(
                [r.response_time_ms for r in component_results]
            ),
            "checks_passed": sum(
                [1 for r in component_results if r.status in ["healthy", "warning"]]
            ),
            "checks_failed": sum(
                [1 for r in component_results if r.status == "critical"]
            ),
        }

        # Generate capacity warnings
        for result in component_results:
            if result.component == "system_resources":
                metrics = result.metrics
                if metrics.get("cpu_percent", 0) > 75:
                    capacity_warnings.append(
                        f"CPU utilization high: {metrics['cpu_percent']:.1f}%"
                    )
                if metrics.get("memory_percent", 0) > 80:
                    capacity_warnings.append(
                        f"Memory utilization high: {metrics['memory_percent']:.1f}%"
                    )
                if metrics.get("disk_percent", 0) > 85:
                    capacity_warnings.append(
                        f"Disk utilization high: {metrics['disk_percent']:.1f}%"
                    )

        # Next recommended check
        next_check = self._calculate_next_check_time(overall_health_score)

        # Create diagnostic report
        report = DiagnosticReport(
            overall_health_score=round(overall_health_score, 1),
            system_status=system_status,
            component_results=component_results,
            critical_issues=critical_issues,
            performance_summary=performance_summary,
            capacity_warnings=capacity_warnings,
            next_recommended_check=next_check,
            report_id=report_id,
            timestamp=datetime.now().isoformat(),
        )

        # Store in history
        self.health_history.append(report)

        # Keep only last 100 reports
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

        logger.info(
            f"Health check complete - Overall score: {overall_health_score:.1f}% ({system_status})"
        )

        return report

    async def _check_postgres_health(self) -> HealthCheckResult:
        """Comprehensive PostgreSQL health check."""
        start_time = time.time()
        checks_performed = []
        issues_found = []
        recommendations = []
        metrics = {}

        try:
            if not self.postgres_conn:
                return HealthCheckResult(
                    component="postgresql",
                    status="offline",
                    score=0.0,
                    response_time_ms=0.0,
                    checks_performed=["connection_test"],
                    issues_found=["PostgreSQL connection not available"],
                    recommendations=[
                        "Check PostgreSQL service status and configuration"
                    ],
                    metrics={},
                    timestamp=datetime.now().isoformat(),
                )

            cursor = self.postgres_conn.cursor()

            # 1. Basic connectivity test
            cursor.execute("SELECT 1")
            checks_performed.append("basic_connectivity")

            # 2. Database size and performance
            cursor.execute(
                """
                SELECT
                    pg_database_size(current_database()) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') as idle_in_transaction,
                    (SELECT count(*) FROM context_items) as context_items_count
            """
            )

            db_stats = cursor.fetchone()
            checks_performed.append("database_statistics")

            metrics.update(
                {
                    "database_size_mb": round(db_stats[0] / 1024 / 1024, 2),
                    "active_connections": db_stats[1],
                    "idle_in_transaction": db_stats[2],
                    "context_items_count": db_stats[3],
                }
            )

            # 3. pgvector extension check
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            pgvector_installed = cursor.fetchone()[0]
            checks_performed.append("pgvector_extension")

            metrics["pgvector_enabled"] = pgvector_installed

            if not pgvector_installed:
                issues_found.append("pgvector extension not installed")
                recommendations.append(
                    "Install pgvector extension for vector search functionality"
                )

            # 4. Query performance test
            test_start = time.time()
            cursor.execute(
                """
                SELECT COUNT(*) FROM context_items
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """
            )
            query_time = (time.time() - test_start) * 1000
            checks_performed.append("query_performance")

            metrics["test_query_time_ms"] = round(query_time, 2)

            if query_time > self.alert_thresholds["query_time_critical"]:
                issues_found.append(f"Query performance critical: {query_time:.1f}ms")
                recommendations.append(
                    "Investigate slow queries and consider database optimization"
                )
            elif query_time > self.alert_thresholds["query_time_warning"]:
                issues_found.append(f"Query performance warning: {query_time:.1f}ms")
                recommendations.append(
                    "Monitor query performance and consider index optimization"
                )

            # 5. Index efficiency check
            cursor.execute(
                """
                SELECT
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch
                FROM pg_stat_user_tables
                WHERE seq_scan + idx_scan > 0
                ORDER BY seq_scan DESC
                LIMIT 5
            """
            )

            table_stats = cursor.fetchall()
            checks_performed.append("index_efficiency")

            for table_stat in table_stats:
                seq_scans = table_stat[2]
                idx_scans = table_stat[4]
                total_scans = seq_scans + idx_scans

                if total_scans > 100:  # Only check tables with significant activity
                    index_ratio = idx_scans / total_scans if total_scans > 0 else 0
                    if index_ratio < 0.5:  # Less than 50% index usage
                        issues_found.append(
                            f"Low index usage on table {table_stat[1]}: {index_ratio:.1%}"
                        )
                        recommendations.append(
                            f"Consider adding indexes to table {table_stat[1]}"
                        )

            # 6. Connection limits check
            cursor.execute("SHOW max_connections")
            max_connections = int(cursor.fetchone()[0])
            connection_usage = metrics["active_connections"] / max_connections

            metrics["connection_usage_percent"] = round(connection_usage * 100, 1)

            if connection_usage > 0.9:
                issues_found.append(
                    f"Connection usage critical: {connection_usage:.1%}"
                )
                recommendations.append(
                    "Increase max_connections or optimize connection pooling"
                )
            elif connection_usage > 0.75:
                issues_found.append(f"Connection usage high: {connection_usage:.1%}")
                recommendations.append(
                    "Monitor connection usage and consider connection pooling"
                )

            # 7. Vacuum and maintenance check
            cursor.execute(
                """
                SELECT
                    sum(n_dead_tup) as total_dead_tuples,
                    sum(n_live_tup) as total_live_tuples
                FROM pg_stat_user_tables
            """
            )

            tuple_stats = cursor.fetchone()
            if tuple_stats and tuple_stats[0] and tuple_stats[1]:
                dead_tuple_ratio = tuple_stats[0] / (tuple_stats[0] + tuple_stats[1])
                metrics["dead_tuple_ratio"] = round(dead_tuple_ratio, 3)

                if dead_tuple_ratio > 0.2:
                    issues_found.append(
                        f"High dead tuple ratio: {dead_tuple_ratio:.1%}"
                    )
                    recommendations.append("Run VACUUM ANALYZE to clean up dead tuples")

            checks_performed.append("maintenance_status")

        except Exception as e:
            issues_found.append(f"Health check error: {str(e)}")
            logger.error(f"PostgreSQL health check error: {e}")

        # Calculate health score
        score = 100.0
        score -= len(issues_found) * 15  # Deduct points for issues
        score = max(0, score)

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        return HealthCheckResult(
            component="postgresql",
            status=status,
            score=score,
            response_time_ms=response_time_ms,
            checks_performed=checks_performed,
            issues_found=issues_found,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
        )

    async def _check_neo4j_health(self) -> HealthCheckResult:
        """Comprehensive Neo4j health check."""
        start_time = time.time()
        checks_performed = []
        issues_found = []
        recommendations = []
        metrics = {}

        try:
            if not self.neo4j_driver:
                return HealthCheckResult(
                    component="neo4j",
                    status="offline",
                    score=0.0,
                    response_time_ms=0.0,
                    checks_performed=["connection_test"],
                    issues_found=["Neo4j connection not available"],
                    recommendations=["Check Neo4j service status and configuration"],
                    metrics={},
                    timestamp=datetime.now().isoformat(),
                )

            with self.neo4j_driver.session() as session:
                # 1. Basic connectivity test
                session.run("RETURN 1")
                checks_performed.append("basic_connectivity")

                # 2. Graph statistics
                result = session.run(
                    """
                    MATCH (n)
                    WITH count(n) as node_count
                    MATCH ()-[r]->()
                    WITH node_count, count(r) as rel_count
                    RETURN node_count, rel_count
                """
                )

                record = result.single()
                node_count = record["node_count"] if record else 0
                rel_count = record["rel_count"] if record else 0

                metrics.update(
                    {
                        "node_count": node_count,
                        "relationship_count": rel_count,
                        "total_graph_elements": node_count + rel_count,
                    }
                )

                checks_performed.append("graph_statistics")

                # 3. Query performance test
                test_start = time.time()
                session.run("MATCH (n) RETURN count(n) LIMIT 1")
                query_time = (time.time() - test_start) * 1000

                metrics["test_query_time_ms"] = round(query_time, 2)
                checks_performed.append("query_performance")

                if query_time > 500:  # Neo4j queries typically slower than SQL
                    issues_found.append(
                        f"Neo4j query performance slow: {query_time:.1f}ms"
                    )
                    recommendations.append(
                        "Consider optimizing Neo4j queries and indexes"
                    )

                # 4. Memory usage check
                try:
                    memory_result = session.run(
                        "CALL dbms.queryJmx('java.lang:type=Memory')"
                    ).single()
                    if memory_result:
                        heap_memory = memory_result["attributes"]["HeapMemoryUsage"][
                            "value"
                        ]
                        heap_used_mb = heap_memory["used"] / 1024 / 1024
                        heap_max_mb = heap_memory["max"] / 1024 / 1024
                        heap_usage_percent = (
                            heap_memory["used"] / heap_memory["max"]
                        ) * 100

                        metrics.update(
                            {
                                "heap_used_mb": round(heap_used_mb, 2),
                                "heap_max_mb": round(heap_max_mb, 2),
                                "heap_usage_percent": round(heap_usage_percent, 1),
                            }
                        )

                        if heap_usage_percent > 85:
                            issues_found.append(
                                f"Neo4j heap usage critical: {heap_usage_percent:.1f}%"
                            )
                            recommendations.append(
                                "Increase Neo4j heap memory allocation"
                            )
                        elif heap_usage_percent > 75:
                            issues_found.append(
                                f"Neo4j heap usage high: {heap_usage_percent:.1f}%"
                            )
                            recommendations.append("Monitor Neo4j memory usage")

                    checks_performed.append("memory_usage")
                except Exception:
                    # Memory check might fail on some Neo4j versions
                    pass

                # 5. Database consistency check
                try:
                    consistency_result = session.run(
                        """
                        MATCH (n)
                        WHERE size(labels(n)) = 0
                        RETURN count(n) as unlabeled_nodes
                    """
                    ).single()

                    unlabeled_nodes = (
                        consistency_result["unlabeled_nodes"]
                        if consistency_result
                        else 0
                    )
                    metrics["unlabeled_nodes"] = unlabeled_nodes

                    if unlabeled_nodes > 0:
                        issues_found.append(
                            f"{unlabeled_nodes} nodes without labels found"
                        )
                        recommendations.append(
                            "Review and label unlabeled nodes for better performance"
                        )

                    checks_performed.append("consistency_check")
                except Exception:
                    pass

                # 6. Index utilization check
                try:
                    index_result = session.run("SHOW INDEXES").data()
                    metrics["index_count"] = len(index_result)
                    checks_performed.append("index_status")

                    if len(index_result) == 0 and node_count > 1000:
                        issues_found.append("No indexes found for large graph")
                        recommendations.append(
                            "Consider creating indexes on frequently queried properties"
                        )
                except Exception:
                    pass

        except Exception as e:
            issues_found.append(f"Health check error: {str(e)}")
            logger.error(f"Neo4j health check error: {e}")

        # Calculate health score
        score = 100.0
        score -= len(issues_found) * 20  # Neo4j issues are more critical
        score = max(0, score)

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        return HealthCheckResult(
            component="neo4j",
            status=status,
            score=score,
            response_time_ms=response_time_ms,
            checks_performed=checks_performed,
            issues_found=issues_found,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
        )

    async def _check_vector_search_health(self) -> HealthCheckResult:
        """Vector search functionality health check."""
        start_time = time.time()
        checks_performed = []
        issues_found = []
        recommendations = []
        metrics = {}

        try:
            if not self.postgres_conn:
                return HealthCheckResult(
                    component="vector_search",
                    status="offline",
                    score=0.0,
                    response_time_ms=0.0,
                    checks_performed=["connection_test"],
                    issues_found=["PostgreSQL connection required for vector search"],
                    recommendations=["Establish PostgreSQL connection"],
                    metrics={},
                    timestamp=datetime.now().isoformat(),
                )

            cursor = self.postgres_conn.cursor()

            # 1. Vector count and coverage
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_items,
                    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as items_with_vectors,
                    AVG(array_length(embedding, 1)) as avg_vector_dimension
                FROM context_items
            """
            )

            vector_stats = cursor.fetchone()
            total_items = vector_stats[0] or 0
            items_with_vectors = vector_stats[1] or 0
            avg_dimension = vector_stats[2] or 0

            coverage_percent = (
                (items_with_vectors / total_items * 100) if total_items > 0 else 0
            )

            metrics.update(
                {
                    "total_items": total_items,
                    "items_with_vectors": items_with_vectors,
                    "coverage_percent": round(coverage_percent, 1),
                    "avg_vector_dimension": avg_dimension,
                }
            )

            checks_performed.append("vector_coverage")

            if coverage_percent < 80:
                issues_found.append(f"Low vector coverage: {coverage_percent:.1f}%")
                recommendations.append(
                    "Increase vector embedding coverage for better search results"
                )

            # 2. Vector search performance test
            if items_with_vectors > 0:
                test_vector = (
                    [0.1] * int(avg_dimension) if avg_dimension else [0.1] * 384
                )

                search_times = []
                for _ in range(3):  # Run 3 test searches
                    search_start = time.time()

                    cursor.execute(
                        """
                        SELECT file_path, embedding <-> %s::vector as distance
                        FROM context_items
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <-> %s::vector
                        LIMIT 5
                    """,
                        (test_vector, test_vector),
                    )

                    results = cursor.fetchall()
                    search_time = (time.time() - search_start) * 1000
                    search_times.append(search_time)

                avg_search_time = np.mean(search_times)
                metrics["avg_search_time_ms"] = round(avg_search_time, 2)
                metrics["search_results_count"] = len(results)

                checks_performed.append("search_performance")

                if avg_search_time > self.alert_thresholds["vector_search_critical"]:
                    issues_found.append(
                        f"Vector search critical: {avg_search_time:.1f}ms"
                    )
                    recommendations.append(
                        "Optimize vector indexes and consider database tuning"
                    )
                elif avg_search_time > self.alert_thresholds["vector_search_warning"]:
                    issues_found.append(f"Vector search slow: {avg_search_time:.1f}ms")
                    recommendations.append("Monitor vector search performance")
            else:
                issues_found.append("No vectors available for search testing")
                recommendations.append(
                    "Ensure embedding generation is working properly"
                )

            # 3. Vector index status
            cursor.execute(
                """
                SELECT
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE indexname LIKE '%embedding%' OR indexname LIKE '%vector%'
            """
            )

            vector_indexes = cursor.fetchall()
            metrics["vector_index_count"] = len(vector_indexes)

            if vector_indexes:
                metrics["vector_indexes"] = [
                    {"name": idx[0], "size": idx[1]} for idx in vector_indexes
                ]
            else:
                issues_found.append("No vector indexes found")
                recommendations.append(
                    "Create appropriate vector indexes for optimal search performance"
                )

            checks_performed.append("index_status")

            # 4. Vector dimension consistency
            if items_with_vectors > 0:
                cursor.execute(
                    """
                    SELECT
                        array_length(embedding, 1) as dimension,
                        count(*) as count
                    FROM context_items
                    WHERE embedding IS NOT NULL
                    GROUP BY array_length(embedding, 1)
                    ORDER BY count DESC
                """
                )

                dimension_stats = cursor.fetchall()
                if len(dimension_stats) > 1:
                    issues_found.append("Inconsistent vector dimensions found")
                    recommendations.append(
                        "Ensure all vectors have consistent dimensions"
                    )

                metrics["dimension_distribution"] = [
                    {"dimension": dim[0], "count": dim[1]} for dim in dimension_stats
                ]

                checks_performed.append("dimension_consistency")

        except Exception as e:
            issues_found.append(f"Vector search health check error: {str(e)}")
            logger.error(f"Vector search health check error: {e}")

        # Calculate health score
        score = 100.0
        score -= len(issues_found) * 15

        # Bonus points for good coverage
        if metrics.get("coverage_percent", 0) > 90:
            score += 5

        score = max(0, min(100, score))

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        return HealthCheckResult(
            component="vector_search",
            status=status,
            score=score,
            response_time_ms=response_time_ms,
            checks_performed=checks_performed,
            issues_found=issues_found,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
        )

    async def _check_system_resources(self) -> HealthCheckResult:
        """System resource health check."""
        start_time = time.time()
        checks_performed = []
        issues_found = []
        recommendations = []
        metrics = {}

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics["cpu_percent"] = round(cpu_percent, 1)
            checks_performed.append("cpu_usage")

            if cpu_percent > self.alert_thresholds["cpu_critical"]:
                issues_found.append(f"CPU usage critical: {cpu_percent:.1f}%")
                recommendations.append(
                    "Investigate high CPU usage processes and consider scaling"
                )
            elif cpu_percent > self.alert_thresholds["cpu_warning"]:
                issues_found.append(f"CPU usage high: {cpu_percent:.1f}%")
                recommendations.append("Monitor CPU usage trends")

            # Memory usage
            memory = psutil.virtual_memory()
            metrics.update(
                {
                    "memory_percent": round(memory.percent, 1),
                    "memory_available_gb": round(memory.available / 1024**3, 2),
                    "memory_total_gb": round(memory.total / 1024**3, 2),
                }
            )
            checks_performed.append("memory_usage")

            if memory.percent > self.alert_thresholds["memory_critical"]:
                issues_found.append(f"Memory usage critical: {memory.percent:.1f}%")
                recommendations.append("Free up memory or add more RAM")
            elif memory.percent > self.alert_thresholds["memory_warning"]:
                issues_found.append(f"Memory usage high: {memory.percent:.1f}%")
                recommendations.append("Monitor memory usage and consider optimization")

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            metrics.update(
                {
                    "disk_percent": round(disk_percent, 1),
                    "disk_free_gb": round(disk.free / 1024**3, 2),
                    "disk_total_gb": round(disk.total / 1024**3, 2),
                }
            )
            checks_performed.append("disk_usage")

            if disk_percent > self.alert_thresholds["disk_critical"]:
                issues_found.append(f"Disk usage critical: {disk_percent:.1f}%")
                recommendations.append("Free up disk space immediately")
            elif disk_percent > self.alert_thresholds["disk_warning"]:
                issues_found.append(f"Disk usage high: {disk_percent:.1f}%")
                recommendations.append("Clean up old files and monitor disk usage")

            # Load average
            if hasattr(psutil, "getloadavg"):
                load_avg = psutil.getloadavg()
                metrics["load_average"] = list(load_avg)

                cpu_count = psutil.cpu_count()
                if load_avg[0] > cpu_count * 2:  # Load > 2x CPU count
                    issues_found.append(f"System load very high: {load_avg[0]:.2f}")
                    recommendations.append(
                        "Investigate system load and process scheduling"
                    )
                elif load_avg[0] > cpu_count:
                    issues_found.append(f"System load high: {load_avg[0]:.2f}")
                    recommendations.append("Monitor system load")

                checks_performed.append("load_average")

            # Network I/O
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    metrics.update(
                        {
                            "network_bytes_sent": net_io.bytes_sent,
                            "network_bytes_recv": net_io.bytes_recv,
                            "network_packets_sent": net_io.packets_sent,
                            "network_packets_recv": net_io.packets_recv,
                        }
                    )
                checks_performed.append("network_io")
            except Exception:
                pass  # Network stats might not be available

            # Open file descriptors (Unix-like systems)
            try:
                process = psutil.Process()
                open_files = len(process.open_files())
                metrics["open_files"] = open_files

                # Warn if too many open files
                if open_files > 1000:
                    issues_found.append(f"Many open files: {open_files}")
                    recommendations.append("Check for file descriptor leaks")

                checks_performed.append("file_descriptors")
            except Exception:
                pass

        except Exception as e:
            issues_found.append(f"System resource check error: {str(e)}")
            logger.error(f"System resource check error: {e}")

        # Calculate health score
        score = 100.0
        score -= len(issues_found) * 10
        score = max(0, score)

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        return HealthCheckResult(
            component="system_resources",
            status=status,
            score=score,
            response_time_ms=response_time_ms,
            checks_performed=checks_performed,
            issues_found=issues_found,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
        )

    async def _check_docker_services(self) -> HealthCheckResult:
        """Docker services health check."""
        start_time = time.time()
        checks_performed = []
        issues_found = []
        recommendations = []
        metrics = {}

        try:
            client = docker.from_env()

            # Get all containers
            all_containers = client.containers.list(all=True)
            running_containers = [c for c in all_containers if c.status == "running"]

            # Focus on context system containers
            context_containers = []
            for container in all_containers:
                if any(
                    keyword in container.name.lower()
                    for keyword in [
                        "unified_context",
                        "postgres",
                        "neo4j",
                        "embedding",
                        "claude",
                    ]
                ):
                    context_containers.append(container)

            metrics.update(
                {
                    "total_containers": len(all_containers),
                    "running_containers": len(running_containers),
                    "context_containers": len(context_containers),
                }
            )

            checks_performed.append("container_count")

            # Check each context container
            container_details = []
            for container in context_containers:
                try:
                    container_info = {
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0]
                        if container.image.tags
                        else container.image.id[:12],
                    }

                    if container.status == "running":
                        # Get resource usage
                        stats = container.stats(stream=False)

                        # Calculate CPU percentage
                        cpu_percent = 0.0
                        if "cpu_stats" in stats and "precpu_stats" in stats:
                            cpu_delta = (
                                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                            )
                            system_delta = (
                                stats["cpu_stats"]["system_cpu_usage"]
                                - stats["precpu_stats"]["system_cpu_usage"]
                            )
                            if system_delta > 0:
                                cpu_percent = (cpu_delta / system_delta) * 100.0

                        memory_usage = stats["memory_stats"].get("usage", 0)
                        memory_limit = stats["memory_stats"].get("limit", 1)
                        memory_percent = (memory_usage / memory_limit) * 100.0

                        container_info.update(
                            {
                                "cpu_percent": round(cpu_percent, 2),
                                "memory_percent": round(memory_percent, 2),
                                "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
                            }
                        )
                    else:
                        issues_found.append(
                            f"Container {container.name} is not running: {container.status}"
                        )
                        recommendations.append(f"Start container {container.name}")

                    container_details.append(container_info)

                except Exception as e:
                    issues_found.append(
                        f"Error checking container {container.name}: {str(e)}"
                    )

            metrics["container_details"] = container_details
            checks_performed.append("container_status")

            # Check for required containers
            required_containers = ["postgres", "neo4j", "embedding"]
            running_names = [
                c["name"].lower() for c in container_details if c["status"] == "running"
            ]

            for required in required_containers:
                if not any(required in name for name in running_names):
                    issues_found.append(
                        f'Required container with "{required}" not running'
                    )
                    recommendations.append(f"Start {required} container")

            checks_performed.append("required_containers")

            # Check Docker daemon health
            try:
                docker_info = client.info()
                metrics["docker_info"] = {
                    "containers": docker_info.get("Containers", 0),
                    "containers_running": docker_info.get("ContainersRunning", 0),
                    "images": docker_info.get("Images", 0),
                    "server_version": docker_info.get("ServerVersion", "unknown"),
                }
                checks_performed.append("docker_daemon")
            except Exception as e:
                issues_found.append(f"Docker daemon check failed: {str(e)}")

        except docker.errors.DockerException as e:
            issues_found.append(f"Docker connection error: {str(e)}")
            recommendations.append("Check Docker daemon status")
        except Exception as e:
            issues_found.append(f"Docker health check error: {str(e)}")
            logger.error(f"Docker health check error: {e}")

        # Calculate health score
        score = 100.0
        score -= len(issues_found) * 12
        score = max(0, score)

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        return HealthCheckResult(
            component="docker_services",
            status=status,
            score=score,
            response_time_ms=response_time_ms,
            checks_performed=checks_performed,
            issues_found=issues_found,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
        )

    async def _check_ingestion_pipeline(self) -> HealthCheckResult:
        """Real-time ingestion pipeline health check."""
        start_time = time.time()
        checks_performed = []
        issues_found = []
        recommendations = []
        metrics = {}

        try:
            # Check monitoring service endpoint
            monitoring_url = self.config.get("monitoring_service", {}).get(
                "url", "http://localhost:8000"
            )

            try:
                response = requests.get(f"{monitoring_url}/api/dashboard", timeout=10)
                if response.status_code == 200:
                    monitoring_data = response.json()

                    # Extract ingestion metrics
                    token_usage = monitoring_data.get("token_usage", {})
                    tool_usage = monitoring_data.get("tool_usage", {})

                    metrics.update(
                        {
                            "monitoring_service_available": True,
                            "recent_sessions": monitoring_data.get(
                                "active_sessions", 0
                            ),
                            "recent_tool_calls": monitoring_data.get(
                                "recent_tool_calls", 0
                            ),
                            "total_sessions": token_usage.get("sessions_count", 0),
                        }
                    )

                    checks_performed.append("monitoring_service")

                    # Check if there's recent activity
                    if monitoring_data.get("recent_tool_calls", 0) == 0:
                        issues_found.append("No recent tool call activity detected")
                        recommendations.append(
                            "Check if ingestion pipeline is processing data"
                        )
                else:
                    issues_found.append(
                        f"Monitoring service returned status {response.status_code}"
                    )
                    metrics["monitoring_service_available"] = False

            except requests.exceptions.RequestException as e:
                issues_found.append(f"Monitoring service unavailable: {str(e)}")
                recommendations.append("Check monitoring service status")
                metrics["monitoring_service_available"] = False

            checks_performed.append("monitoring_endpoint")

            # Check real-time ingestion components via file system
            ingestion_path = Path(
                "/home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/realtime_ingestion"
            )

            if ingestion_path.exists():
                ingestion_files = list(ingestion_path.glob("*.py"))
                metrics["ingestion_files_count"] = len(ingestion_files)

                required_files = [
                    "realtime_service.py",
                    "ingestion_pipeline.py",
                    "chat_log_watcher.py",
                ]
                missing_files = []

                for required_file in required_files:
                    if not (ingestion_path / required_file).exists():
                        missing_files.append(required_file)

                if missing_files:
                    issues_found.append(
                        f'Missing ingestion files: {", ".join(missing_files)}'
                    )
                    recommendations.append("Verify ingestion pipeline installation")

                checks_performed.append("ingestion_files")
            else:
                issues_found.append("Ingestion pipeline directory not found")
                recommendations.append("Install real-time ingestion pipeline")

            # Check if ingestion service is running as a process
            ingestion_processes = []
            for process in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = (
                        " ".join(process.info["cmdline"])
                        if process.info["cmdline"]
                        else ""
                    )
                    if "ingestion" in cmdline.lower() or "realtime" in cmdline.lower():
                        ingestion_processes.append(
                            {
                                "pid": process.info["pid"],
                                "name": process.info["name"],
                                "cmdline": cmdline[:100] + "..."
                                if len(cmdline) > 100
                                else cmdline,
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            metrics["ingestion_processes"] = len(ingestion_processes)
            metrics["ingestion_process_details"] = ingestion_processes

            if len(ingestion_processes) == 0:
                issues_found.append("No ingestion processes found running")
                recommendations.append("Start real-time ingestion service")

            checks_performed.append("ingestion_processes")

        except Exception as e:
            issues_found.append(f"Ingestion pipeline check error: {str(e)}")
            logger.error(f"Ingestion pipeline check error: {e}")

        # Calculate health score
        score = 100.0
        score -= len(issues_found) * 15
        score = max(0, score)

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        return HealthCheckResult(
            component="ingestion_pipeline",
            status=status,
            score=score,
            response_time_ms=response_time_ms,
            checks_performed=checks_performed,
            issues_found=issues_found,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
        )

    async def _check_component_communication(self) -> HealthCheckResult:
        """Inter-component communication health check."""
        start_time = time.time()
        checks_performed = []
        issues_found = []
        recommendations = []
        metrics = {}

        try:
            communication_tests = []

            # 1. PostgreSQL to Neo4j data consistency check
            if self.postgres_conn and self.neo4j_driver:
                try:
                    # Get count from PostgreSQL
                    cursor = self.postgres_conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM context_items")
                    postgres_count = cursor.fetchone()[0]

                    # Get count from Neo4j
                    with self.neo4j_driver.session() as session:
                        result = session.run("MATCH (n) RETURN count(n) as count")
                        neo4j_count = result.single()["count"]

                    metrics.update(
                        {"postgres_items": postgres_count, "neo4j_nodes": neo4j_count}
                    )

                    # Check for reasonable data correlation
                    if postgres_count > 0 and neo4j_count == 0:
                        issues_found.append("PostgreSQL has data but Neo4j is empty")
                        recommendations.append(
                            "Check data synchronization between databases"
                        )
                    elif abs(postgres_count - neo4j_count) > postgres_count * 0.5:
                        issues_found.append(
                            "Large data discrepancy between PostgreSQL and Neo4j"
                        )
                        recommendations.append(
                            "Review data ingestion and synchronization processes"
                        )

                    communication_tests.append("postgres_neo4j_consistency")
                    checks_performed.append("database_consistency")
                except Exception as e:
                    issues_found.append(f"Database consistency check failed: {str(e)}")

            # 2. Embedding service connectivity
            embedding_url = self.config.get("embedding_service", {}).get(
                "url", "http://localhost:8001"
            )

            try:
                response = requests.get(f"{embedding_url}/health", timeout=5)
                if response.status_code == 200:
                    embedding_health = response.json()
                    metrics["embedding_service_response"] = embedding_health
                    communication_tests.append("embedding_service_connectivity")
                else:
                    issues_found.append(
                        f"Embedding service returned status {response.status_code}"
                    )
                    recommendations.append("Check embedding service configuration")

                checks_performed.append("embedding_service")
            except requests.exceptions.RequestException as e:
                issues_found.append(f"Embedding service unreachable: {str(e)}")
                recommendations.append(
                    "Verify embedding service is running and accessible"
                )

            # 3. Vector search integration test
            if self.postgres_conn:
                try:
                    cursor = self.postgres_conn.cursor()

                    # Test vector search with actual data
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM context_items
                        WHERE embedding IS NOT NULL
                    """
                    )

                    vector_count = cursor.fetchone()[0]

                    if vector_count > 0:
                        # Perform a search test
                        test_vector = [0.1] * 384
                        cursor.execute(
                            """
                            SELECT file_path, content, embedding <-> %s::vector as distance
                            FROM context_items
                            WHERE embedding IS NOT NULL
                            ORDER BY embedding <-> %s::vector
                            LIMIT 3
                        """,
                            (test_vector, test_vector),
                        )

                        search_results = cursor.fetchall()
                        metrics["vector_search_test_results"] = len(search_results)
                        communication_tests.append("vector_search_integration")
                    else:
                        issues_found.append(
                            "No vectors available for integration testing"
                        )
                        recommendations.append("Generate embeddings for context items")

                    checks_performed.append("vector_search_integration")
                except Exception as e:
                    issues_found.append(
                        f"Vector search integration test failed: {str(e)}"
                    )

            # 4. End-to-end data flow test
            try:
                # This would test the complete pipeline from ingestion to search
                # For now, we check if the pipeline components can communicate

                pipeline_health_score = 100

                # Check if we have recent data
                if self.postgres_conn:
                    cursor = self.postgres_conn.cursor()
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM context_items
                        WHERE created_at >= NOW() - INTERVAL '1 day'
                    """
                    )
                    recent_items = cursor.fetchone()[0]
                    metrics["recent_context_items"] = recent_items

                    if recent_items == 0:
                        issues_found.append("No recent data ingestion detected")
                        recommendations.append("Check data ingestion pipeline")
                        pipeline_health_score -= 30

                metrics["pipeline_health_score"] = pipeline_health_score
                communication_tests.append("end_to_end_flow")
                checks_performed.append("end_to_end_test")

            except Exception as e:
                issues_found.append(f"End-to-end test failed: {str(e)}")

            metrics["communication_tests_passed"] = len(communication_tests)
            metrics["communication_tests"] = communication_tests

        except Exception as e:
            issues_found.append(f"Communication check error: {str(e)}")
            logger.error(f"Communication check error: {e}")

        # Calculate health score
        score = 100.0
        score -= len(issues_found) * 20  # Communication issues are serious
        score = max(0, score)

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        return HealthCheckResult(
            component="component_communication",
            status=status,
            score=score,
            response_time_ms=response_time_ms,
            checks_performed=checks_performed,
            issues_found=issues_found,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
        )

    def _calculate_next_check_time(self, health_score: float) -> str:
        """Calculate when the next health check should be performed."""
        if health_score >= 90:
            # System is healthy - check every hour
            next_check = datetime.now() + timedelta(hours=1)
        elif health_score >= 70:
            # System has warnings - check every 30 minutes
            next_check = datetime.now() + timedelta(minutes=30)
        else:
            # System is critical - check every 10 minutes
            next_check = datetime.now() + timedelta(minutes=10)

        return next_check.isoformat()

    def export_health_report(self, report: DiagnosticReport, file_path: str):
        """Export health report to JSON file."""
        report_dict = asdict(report)

        with open(file_path, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"Health report exported to {file_path}")

    async def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze health trends over time."""
        if len(self.health_history) < 2:
            return {"error": "Insufficient health history for trend analysis"}

        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_reports = [
            report
            for report in self.health_history
            if datetime.fromisoformat(report.timestamp) > cutoff_time
        ]

        if not recent_reports:
            return {"error": "No health data available for specified period"}

        # Calculate trends
        health_scores = [report.overall_health_score for report in recent_reports]
        response_times = []

        for report in recent_reports:
            avg_response_time = np.mean(
                [result.response_time_ms for result in report.component_results]
            )
            response_times.append(avg_response_time)

        # Component-specific trends
        component_trends = {}
        for report in recent_reports:
            for result in report.component_results:
                if result.component not in component_trends:
                    component_trends[result.component] = []
                component_trends[result.component].append(result.score)

        return {
            "analysis_period_hours": hours,
            "total_reports": len(recent_reports),
            "overall_health_trend": {
                "current_score": health_scores[-1] if health_scores else 0,
                "average_score": round(np.mean(health_scores), 1),
                "score_change": health_scores[-1] - health_scores[0]
                if len(health_scores) > 1
                else 0,
                "trend_direction": "improving"
                if len(health_scores) > 1 and health_scores[-1] > health_scores[0]
                else "stable",
            },
            "performance_trend": {
                "current_response_time_ms": response_times[-1] if response_times else 0,
                "average_response_time_ms": round(np.mean(response_times), 1),
                "response_time_change_ms": response_times[-1] - response_times[0]
                if len(response_times) > 1
                else 0,
            },
            "component_trends": {
                component: {
                    "current_score": scores[-1],
                    "average_score": round(np.mean(scores), 1),
                    "score_change": scores[-1] - scores[0] if len(scores) > 1 else 0,
                    "measurements": len(scores),
                }
                for component, scores in component_trends.items()
            },
            "timestamp": datetime.now().isoformat(),
        }


# Async function to run health check
async def run_health_check():
    """Run comprehensive health check."""
    config = {
        "postgres": {
            "host": "localhost",
            "port": 5432,
            "database": "unified_context",
            "user": "opsvi",
            "password": "opsvi_secure_password",
        },
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password",
        },
        "embedding_service": {"url": "http://localhost:8001"},
        "monitoring_service": {"url": "http://localhost:8000"},
    }

    health_checker = ComprehensiveHealthChecker(config)

    try:
        await health_checker.initialize()
        diagnostic_report = await health_checker.run_comprehensive_health_check()

        # Export report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/home/opsvi/master_root/HEALTH_CHECK_REPORT_{timestamp}.json"
        health_checker.export_health_report(diagnostic_report, report_path)

        print(f"Health check complete. Report saved to: {report_path}")
        print(
            f"Overall Health Score: {diagnostic_report.overall_health_score:.1f}% ({diagnostic_report.system_status.upper()})"
        )

        if diagnostic_report.critical_issues:
            print(
                f"\nCritical Issues Found ({len(diagnostic_report.critical_issues)}):"
            )
            for issue in diagnostic_report.critical_issues:
                print(f"  ⚠️  {issue}")

        print(f"\nComponent Status Summary:")
        for result in diagnostic_report.component_results:
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "critical": "❌",
                "offline": "🔴",
            }.get(result.status, "❓")

            print(
                f"  {status_emoji} {result.component}: {result.score:.1f}% ({result.status})"
            )

        return diagnostic_report

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    asyncio.run(run_health_check())
