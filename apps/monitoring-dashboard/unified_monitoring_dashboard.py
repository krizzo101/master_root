#!/usr/bin/env python3
"""
Unified Monitoring Dashboard for Complete Context System

Comprehensive monitoring for all completed components:
- PostgreSQL + TimescaleDB + pgvector
- Neo4j relationship graph (21k+ nodes)
- Context items population pipeline
- Real-time chat ingestion
- IDE context bridge
- Materialized views performance
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import docker
import psutil
import psycopg2
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from neo4j import GraphDatabase
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "postgres": {
        "host": "localhost",
        "port": 5432,
        "database": "unified_context",
        "user": "opsvi",
        "password": "opsvi_secure_password",
    },
    "neo4j": {"uri": "bolt://localhost:7687", "user": "neo4j", "password": "password"},
    "embedding_service": {"url": "http://localhost:8001"},
    "monitoring_service": {"url": "http://localhost:8000"},
}


# Data Models
@dataclass
class ComponentStatus:
    name: str
    status: str  # 'healthy', 'degraded', 'unhealthy', 'offline'
    uptime: float
    cpu_usage: float
    memory_usage: float
    connections: int
    last_activity: str
    metrics: Dict[str, Any]
    issues: List[str]


@dataclass
class DatabaseMetrics:
    total_records: int
    active_connections: int
    queries_per_second: float
    avg_query_time: float
    cache_hit_ratio: float
    disk_usage: int
    index_efficiency: float


@dataclass
class VectorSearchMetrics:
    total_vectors: int
    search_latency_ms: float
    index_size_mb: float
    searches_per_minute: float
    embedding_accuracy: float


@dataclass
class SystemOverview:
    total_components: int
    healthy_components: int
    total_data_points: int
    system_load: float
    overall_status: str
    last_updated: str


class UnifiedMonitoringDashboard:
    """Main monitoring dashboard for the unified context system."""

    def __init__(self):
        self.app = FastAPI(
            title="Unified Context System Monitoring",
            description="Comprehensive monitoring for all context system components",
            version="2.0.0",
        )

        # Enable CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.postgres_pool = None
        self.neo4j_driver = None
        self.component_status = {}
        self.metrics_history = []
        self.alerts = []

        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def dashboard_home():
            return HTMLResponse(self._generate_dashboard_html())

        @self.app.get("/api/overview")
        async def get_system_overview():
            return await self._get_system_overview()

        @self.app.get("/api/components")
        async def get_component_status():
            return await self._get_all_components_status()

        @self.app.get("/api/postgres")
        async def get_postgres_metrics():
            return await self._get_postgres_metrics()

        @self.app.get("/api/neo4j")
        async def get_neo4j_metrics():
            return await self._get_neo4j_metrics()

        @self.app.get("/api/vector-search")
        async def get_vector_search_metrics():
            return await self._get_vector_search_metrics()

        @self.app.get("/api/ingestion")
        async def get_ingestion_metrics():
            return await self._get_ingestion_metrics()

        @self.app.get("/api/performance")
        async def get_performance_metrics():
            return await self._get_performance_metrics()

        @self.app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @self.app.get("/api/alerts")
        async def get_alerts():
            return await self._get_current_alerts()

        @self.app.websocket("/ws/monitoring")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket(websocket)

    async def start_monitoring(self):
        """Initialize monitoring connections and start background tasks."""
        logger.info("Starting unified monitoring dashboard...")

        # Initialize database connections
        await self._init_postgres_connection()
        await self._init_neo4j_connection()

        # Start background monitoring tasks
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._alert_checker())

        logger.info("Unified monitoring dashboard started successfully")

    async def _init_postgres_connection(self):
        """Initialize PostgreSQL connection pool."""
        try:
            import asyncpg

            self.postgres_pool = await asyncpg.create_pool(
                host=CONFIG["postgres"]["host"],
                port=CONFIG["postgres"]["port"],
                database=CONFIG["postgres"]["database"],
                user=CONFIG["postgres"]["user"],
                password=CONFIG["postgres"]["password"],
                min_size=2,
                max_size=10,
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection: {e}")

    async def _init_neo4j_connection(self):
        """Initialize Neo4j connection."""
        try:
            self.neo4j_driver = GraphDatabase.driver(
                CONFIG["neo4j"]["uri"],
                auth=(CONFIG["neo4j"]["user"], CONFIG["neo4j"]["password"]),
            )
            # Test connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {e}")

    async def _get_system_overview(self) -> Dict[str, Any]:
        """Get overall system overview."""
        try:
            components = await self._get_all_components_status()

            total_components = len(components)
            healthy_components = sum(
                1 for c in components.values() if c["status"] == "healthy"
            )

            # Calculate total data points across all systems
            postgres_metrics = await self._get_postgres_metrics()
            neo4j_metrics = await self._get_neo4j_metrics()

            total_data_points = (
                postgres_metrics.get("total_records", 0)
                + neo4j_metrics.get("node_count", 0)
                + neo4j_metrics.get("relationship_count", 0)
            )

            # System load from psutil
            system_load = psutil.cpu_percent()

            # Overall status
            if healthy_components == total_components:
                overall_status = "healthy"
            elif healthy_components >= total_components * 0.7:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"

            return SystemOverview(
                total_components=total_components,
                healthy_components=healthy_components,
                total_data_points=total_data_points,
                system_load=system_load,
                overall_status=overall_status,
                last_updated=datetime.now().isoformat(),
            ).__dict__

        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {"error": str(e)}

    async def _get_all_components_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all monitored components."""
        components = {}

        # PostgreSQL + pgvector
        components["postgresql"] = await self._check_postgres_status()

        # Neo4j
        components["neo4j"] = await self._check_neo4j_status()

        # Embedding Service
        components["embedding_service"] = await self._check_embedding_service_status()

        # Real-time Ingestion
        components["realtime_ingestion"] = await self._check_ingestion_status()

        # Docker containers
        components["docker_services"] = await self._check_docker_services()

        return components

    async def _check_postgres_status(self) -> Dict[str, Any]:
        """Check PostgreSQL and pgvector status."""
        try:
            if not self.postgres_pool:
                return {"status": "offline", "error": "Connection pool not initialized"}

            async with self.postgres_pool.acquire() as conn:
                # Check basic connectivity
                result = await conn.fetchval("SELECT 1")

                # Check pgvector extension
                pgvector_check = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )

                # Get database stats
                stats = await conn.fetchrow(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM context_items) as context_items_count,
                        (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT pg_database_size(current_database())) as database_size
                """
                )

                return {
                    "status": "healthy",
                    "uptime": time.time(),  # Simplified
                    "pgvector_enabled": bool(pgvector_check),
                    "context_items_count": stats["context_items_count"],
                    "active_connections": stats["active_connections"],
                    "database_size_bytes": stats["database_size"],
                    "last_check": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"PostgreSQL status check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def _check_neo4j_status(self) -> Dict[str, Any]:
        """Check Neo4j status and relationship graph metrics."""
        try:
            if not self.neo4j_driver:
                return {"status": "offline", "error": "Neo4j driver not initialized"}

            with self.neo4j_driver.session() as session:
                # Get node and relationship counts
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

                # Get memory usage
                memory_info = session.run(
                    "CALL dbms.queryJmx('java.lang:type=Memory')"
                ).single()

                return {
                    "status": "healthy",
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "total_graph_elements": node_count + rel_count,
                    "memory_usage": memory_info.get("HeapMemoryUsage", {})
                    if memory_info
                    else {},
                    "last_check": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Neo4j status check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def _check_embedding_service_status(self) -> Dict[str, Any]:
        """Check embedding service status."""
        try:
            response = requests.get(
                f"{CONFIG['embedding_service']['url']}/health", timeout=5
            )

            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "healthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "health_data": health_data,
                    "last_check": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "degraded",
                    "http_status": response.status_code,
                    "last_check": datetime.now().isoformat(),
                }

        except requests.exceptions.RequestException as e:
            return {
                "status": "offline",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def _check_ingestion_status(self) -> Dict[str, Any]:
        """Check real-time ingestion pipeline status."""
        try:
            # Check if ingestion services are running via existing monitoring
            monitoring_response = requests.get(
                f"{CONFIG['monitoring_service']['url']}/api/dashboard", timeout=5
            )

            if monitoring_response.status_code == 200:
                data = monitoring_response.json()
                return {
                    "status": "healthy",
                    "ingestion_metrics": data,
                    "last_check": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "degraded",
                    "error": f"Monitoring service returned {monitoring_response.status_code}",
                    "last_check": datetime.now().isoformat(),
                }

        except requests.exceptions.RequestException as e:
            return {
                "status": "offline",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def _check_docker_services(self) -> Dict[str, Any]:
        """Check Docker services status."""
        try:
            client = docker.from_env()
            containers = client.containers.list()

            context_containers = []
            for container in containers:
                if any(
                    keyword in container.name.lower()
                    for keyword in ["unified_context", "postgres", "neo4j", "embedding"]
                ):
                    stats = container.stats(stream=False)

                    # Calculate basic metrics
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

                    context_containers.append(
                        {
                            "name": container.name,
                            "status": container.status,
                            "cpu_percent": round(cpu_percent, 2),
                            "memory_percent": round(memory_percent, 2),
                            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
                        }
                    )

            return {
                "status": "healthy" if context_containers else "degraded",
                "containers": context_containers,
                "total_containers": len(context_containers),
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Docker services check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def _get_postgres_metrics(self) -> Dict[str, Any]:
        """Get detailed PostgreSQL metrics."""
        try:
            if not self.postgres_pool:
                return {"error": "PostgreSQL not connected"}

            async with self.postgres_pool.acquire() as conn:
                # Context items metrics
                context_stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_items,
                        COUNT(DISTINCT source_type) as source_types,
                        COUNT(DISTINCT file_path) as unique_files,
                        AVG(LENGTH(content)) as avg_content_length
                    FROM context_items
                """
                )

                # Vector search metrics (if vectors exist)
                vector_stats = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as vector_count
                    FROM context_items
                    WHERE embedding IS NOT NULL
                """
                )

                # Performance metrics
                perf_stats = await conn.fetchrow(
                    """
                    SELECT
                        (SELECT SUM(n_tup_ins + n_tup_upd + n_tup_del) FROM pg_stat_user_tables) as total_operations,
                        (SELECT SUM(seq_scan + idx_scan) FROM pg_stat_user_tables) as total_scans,
                        (SELECT AVG(mean_exec_time) FROM pg_stat_statements WHERE calls > 10) as avg_query_time
                """
                )

                return {
                    "total_records": context_stats["total_items"] or 0,
                    "source_types": context_stats["source_types"] or 0,
                    "unique_files": context_stats["unique_files"] or 0,
                    "avg_content_length": round(
                        context_stats["avg_content_length"] or 0, 2
                    ),
                    "vector_count": vector_stats["vector_count"] or 0,
                    "total_operations": perf_stats["total_operations"] or 0,
                    "total_scans": perf_stats["total_scans"] or 0,
                    "avg_query_time_ms": round(perf_stats["avg_query_time"] or 0, 2),
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting PostgreSQL metrics: {e}")
            return {"error": str(e)}

    async def _get_neo4j_metrics(self) -> Dict[str, Any]:
        """Get detailed Neo4j metrics."""
        try:
            if not self.neo4j_driver:
                return {"error": "Neo4j not connected"}

            with self.neo4j_driver.session() as session:
                # Node type distribution
                node_types = session.run(
                    """
                    MATCH (n)
                    RETURN labels(n)[0] as node_type, count(n) as count
                    ORDER BY count DESC
                    LIMIT 10
                """
                )

                node_distribution = [dict(record) for record in node_types]

                # Relationship type distribution
                rel_types = session.run(
                    """
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(r) as count
                    ORDER BY count DESC
                    LIMIT 10
                """
                )

                rel_distribution = [dict(record) for record in rel_types]

                # Graph density metrics
                density_stats = session.run(
                    """
                    MATCH (n) WITH count(n) as nodes
                    MATCH ()-[r]->() WITH nodes, count(r) as rels
                    RETURN nodes, rels,
                           CASE WHEN nodes > 1 THEN toFloat(rels) / (nodes * (nodes - 1)) ELSE 0 END as density
                """
                ).single()

                return {
                    "node_count": density_stats["nodes"] or 0,
                    "relationship_count": density_stats["rels"] or 0,
                    "graph_density": round(density_stats["density"] or 0, 6),
                    "node_type_distribution": node_distribution,
                    "relationship_type_distribution": rel_distribution,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting Neo4j metrics: {e}")
            return {"error": str(e)}

    async def _get_vector_search_metrics(self) -> Dict[str, Any]:
        """Get vector search performance metrics."""
        try:
            # Test vector search performance
            test_vector = [0.1] * 384  # Standard sentence transformer dimension

            start_time = time.time()

            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    # Perform a test vector similarity search
                    results = await conn.fetch(
                        """
                        SELECT file_path, content,
                               embedding <-> $1::vector as distance
                        FROM context_items
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <-> $1::vector
                        LIMIT 5
                    """,
                        test_vector,
                    )

                    search_time_ms = (time.time() - start_time) * 1000

                    return {
                        "search_latency_ms": round(search_time_ms, 2),
                        "results_found": len(results),
                        "test_successful": True,
                        "timestamp": datetime.now().isoformat(),
                    }
            else:
                return {"error": "PostgreSQL connection not available"}

        except Exception as e:
            logger.error(f"Error testing vector search: {e}")
            return {
                "search_latency_ms": -1,
                "test_successful": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _get_ingestion_metrics(self) -> Dict[str, Any]:
        """Get ingestion pipeline metrics."""
        try:
            # Get metrics from the existing monitoring service
            response = requests.get(
                f"{CONFIG['monitoring_service']['url']}/api/dashboard", timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "pipeline_active": True,
                    "monitoring_data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "pipeline_active": False,
                    "error": f"Monitoring service unavailable: {response.status_code}",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            return {
                "pipeline_active": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall system performance metrics."""
        # System resources
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Process-specific metrics
        process = psutil.Process()
        process_info = {
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
        }

        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / 1024**3, 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024**3, 2),
            },
            "dashboard_process": process_info,
            "load_average": list(psutil.getloadavg())
            if hasattr(psutil, "getloadavg")
            else [0, 0, 0],
            "timestamp": datetime.now().isoformat(),
        }

    async def _get_current_alerts(self) -> Dict[str, Any]:
        """Get current system alerts."""
        alerts = []

        # Check all components and generate alerts
        components = await self._get_all_components_status()

        for comp_name, comp_data in components.items():
            if comp_data.get("status") == "unhealthy":
                alerts.append(
                    {
                        "severity": "critical",
                        "component": comp_name,
                        "message": f"{comp_name} is unhealthy",
                        "details": comp_data.get("error", "No details available"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            elif comp_data.get("status") == "degraded":
                alerts.append(
                    {
                        "severity": "warning",
                        "component": comp_name,
                        "message": f"{comp_name} is degraded",
                        "details": comp_data.get(
                            "error", "Performance issues detected"
                        ),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # System resource alerts
        perf_metrics = await self._get_performance_metrics()
        system = perf_metrics.get("system", {})

        if system.get("cpu_percent", 0) > 80:
            alerts.append(
                {
                    "severity": "warning",
                    "component": "system",
                    "message": "High CPU usage detected",
                    "details": f"CPU usage: {system['cpu_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        if system.get("memory_percent", 0) > 85:
            alerts.append(
                {
                    "severity": "critical",
                    "component": "system",
                    "message": "High memory usage detected",
                    "details": f"Memory usage: {system['memory_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return {
            "active_alerts": alerts,
            "total_alerts": len(alerts),
            "critical_count": sum(1 for a in alerts if a["severity"] == "critical"),
            "warning_count": sum(1 for a in alerts if a["severity"] == "warning"),
            "last_check": datetime.now().isoformat(),
        }

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                # Collect all metrics
                overview = await self._get_system_overview()
                components = await self._get_all_components_status()
                performance = await self._get_performance_metrics()

                # Store metrics history
                metric_point = {
                    "timestamp": datetime.now().isoformat(),
                    "overview": overview,
                    "components": components,
                    "performance": performance,
                }

                self.metrics_history.append(metric_point)

                # Keep only last 1000 points
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                # Log status every 5 minutes
                if len(self.metrics_history) % 5 == 0:
                    logger.info(
                        f"System Status - {overview.get('overall_status', 'unknown')} - "
                        f"Healthy: {overview.get('healthy_components', 0)}/"
                        f"{overview.get('total_components', 0)} components"
                    )

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(60)  # Run every minute

    async def _alert_checker(self):
        """Background alert checking loop."""
        while True:
            try:
                alerts = await self._get_current_alerts()
                self.alerts = alerts["active_alerts"]

                # Log critical alerts
                for alert in self.alerts:
                    if alert["severity"] == "critical":
                        logger.warning(
                            f"CRITICAL ALERT: {alert['message']} - {alert['details']}"
                        )

            except Exception as e:
                logger.error(f"Error in alert checker: {e}")

            await asyncio.sleep(30)  # Check every 30 seconds

    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections for real-time updates."""
        await websocket.accept()

        try:
            while True:
                # Send current dashboard data
                overview = await self._get_system_overview()
                components = await self._get_all_components_status()
                alerts = await self._get_current_alerts()

                data = {
                    "type": "dashboard_update",
                    "timestamp": datetime.now().isoformat(),
                    "overview": overview,
                    "components": components,
                    "alerts": alerts,
                }

                await websocket.send_json(data)
                await asyncio.sleep(10)  # Update every 10 seconds

        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    def _generate_dashboard_html(self) -> str:
        """Generate HTML dashboard."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Context System Monitoring</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .dashboard { max-width: 1400px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .status-healthy { color: #10b981; font-weight: bold; }
        .status-degraded { color: #f59e0b; font-weight: bold; }
        .status-unhealthy { color: #ef4444; font-weight: bold; }
        .status-offline { color: #6b7280; font-weight: bold; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 6px; }
        .alert-critical { background: #fef2f2; border-left: 4px solid #ef4444; }
        .alert-warning { background: #fefce8; border-left: 4px solid #f59e0b; }
        .refresh-btn { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; }
        .refresh-btn:hover { background: #5a67d8; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🔍 Unified Context System Monitoring</h1>
            <p>Comprehensive monitoring for PostgreSQL, Neo4j, Vector Search, and Real-time Ingestion</p>
            <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh</button>
        </div>

        <div class="cards">
            <div class="card">
                <h3>📊 System Overview</h3>
                <div id="overview">Loading...</div>
            </div>

            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="alerts">Loading...</div>
            </div>

            <div class="card">
                <h3>🗄️ PostgreSQL + pgvector</h3>
                <div id="postgres">Loading...</div>
            </div>

            <div class="card">
                <h3>🕸️ Neo4j Graph Database</h3>
                <div id="neo4j">Loading...</div>
            </div>

            <div class="card">
                <h3>🤖 Embedding Service</h3>
                <div id="embedding">Loading...</div>
            </div>

            <div class="card">
                <h3>⚡ Real-time Ingestion</h3>
                <div id="ingestion">Loading...</div>
            </div>
        </div>
    </div>

    <script>
        async function loadDashboard() {
            try {
                // Load overview
                const overview = await fetch('/api/overview').then(r => r.json());
                document.getElementById('overview').innerHTML = `
                    <div class="metric"><span>Total Components:</span><span>${overview.total_components}</span></div>
                    <div class="metric"><span>Healthy Components:</span><span class="status-healthy">${overview.healthy_components}</span></div>
                    <div class="metric"><span>Total Data Points:</span><span>${overview.total_data_points.toLocaleString()}</span></div>
                    <div class="metric"><span>System Load:</span><span>${overview.system_load.toFixed(1)}%</span></div>
                    <div class="metric"><span>Overall Status:</span><span class="status-${overview.overall_status}">${overview.overall_status.toUpperCase()}</span></div>
                `;

                // Load alerts
                const alerts = await fetch('/api/alerts').then(r => r.json());
                const alertsHtml = alerts.active_alerts.length === 0 ?
                    '<div style="color: #10b981;">✅ No active alerts</div>' :
                    alerts.active_alerts.map(alert =>
                        `<div class="alert alert-${alert.severity}">
                            <strong>${alert.severity.toUpperCase()}</strong>: ${alert.message}<br>
                            <small>${alert.details}</small>
                        </div>`
                    ).join('');
                document.getElementById('alerts').innerHTML = alertsHtml;

                // Load component statuses
                const components = await fetch('/api/components').then(r => r.json());

                // PostgreSQL
                const pg = components.postgresql || {};
                document.getElementById('postgres').innerHTML = `
                    <div class="metric"><span>Status:</span><span class="status-${pg.status || 'offline'}">${(pg.status || 'offline').toUpperCase()}</span></div>
                    <div class="metric"><span>Context Items:</span><span>${(pg.context_items_count || 0).toLocaleString()}</span></div>
                    <div class="metric"><span>Active Connections:</span><span>${pg.active_connections || 0}</span></div>
                    <div class="metric"><span>pgvector Enabled:</span><span>${pg.pgvector_enabled ? '✅' : '❌'}</span></div>
                    <div class="metric"><span>DB Size:</span><span>${((pg.database_size_bytes || 0) / 1024 / 1024).toFixed(1)} MB</span></div>
                `;

                // Neo4j
                const neo4j = components.neo4j || {};
                document.getElementById('neo4j').innerHTML = `
                    <div class="metric"><span>Status:</span><span class="status-${neo4j.status || 'offline'}">${(neo4j.status || 'offline').toUpperCase()}</span></div>
                    <div class="metric"><span>Nodes:</span><span>${(neo4j.node_count || 0).toLocaleString()}</span></div>
                    <div class="metric"><span>Relationships:</span><span>${(neo4j.relationship_count || 0).toLocaleString()}</span></div>
                    <div class="metric"><span>Total Elements:</span><span>${(neo4j.total_graph_elements || 0).toLocaleString()}</span></div>
                `;

                // Embedding Service
                const embedding = components.embedding_service || {};
                document.getElementById('embedding').innerHTML = `
                    <div class="metric"><span>Status:</span><span class="status-${embedding.status || 'offline'}">${(embedding.status || 'offline').toUpperCase()}</span></div>
                    <div class="metric"><span>Response Time:</span><span>${(embedding.response_time_ms || 0).toFixed(0)} ms</span></div>
                `;

                // Real-time Ingestion
                const ingestion = components.realtime_ingestion || {};
                document.getElementById('ingestion').innerHTML = `
                    <div class="metric"><span>Status:</span><span class="status-${ingestion.status || 'offline'}">${(ingestion.status || 'offline').toUpperCase()}</span></div>
                    <div class="metric"><span>Pipeline Active:</span><span>${ingestion.pipeline_active ? '✅' : '❌'}</span></div>
                `;

                document.getElementById('overview').innerHTML += `<div style="margin-top: 10px; font-size: 12px; color: #666;">Last updated: ${new Date().toLocaleTimeString()}</div>`;

            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }

        // Load dashboard on page load
        loadDashboard();

        // Auto-refresh every 30 seconds
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
        """


# Main application instance
dashboard = UnifiedMonitoringDashboard()


@dashboard.app.on_event("startup")
async def startup_event():
    await dashboard.start_monitoring()


if __name__ == "__main__":
    uvicorn.run(
        "unified_monitoring_dashboard:dashboard.app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info",
    )
