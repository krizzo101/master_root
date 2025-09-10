#!/usr/bin/env python3
"""
Enhanced Claude Monitor with PostgreSQL/TimescaleDB Integration
Implements the Unified Context System design for monitoring metrics
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import docker
import psutil
import psycopg2
import redis
from psycopg2.extras import Json, RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MonitoringMetric:
    """Monitoring metric for TimescaleDB storage"""

    metric_type: str  # 'token_usage', 'system_resource', 'agent_status', 'docker_container'
    metric_name: str
    metric_value: float
    timestamp: datetime
    source: str  # 'claude_cli', 'docker', 'orchestrator', 'system'

    # Context
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    container_id: Optional[str] = None
    project_path: Optional[str] = None

    # Additional data
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None


class UnifiedMonitoringService:
    """
    Claude Monitor integrated with Unified Context System
    - Collects metrics from all sources
    - Stores in PostgreSQL/TimescaleDB
    - Publishes to Redis for real-time
    - Extracts relationships for Neo4j
    """

    def __init__(
        self,
        postgres_config: Dict,
        redis_config: Dict = None,
        enable_neo4j: bool = True,
    ):
        self.pg_config = postgres_config
        self.redis_client = None
        if redis_config:
            self.redis_client = redis.Redis(**redis_config)

        self.enable_neo4j = enable_neo4j
        self.docker_client = docker.from_env()

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize PostgreSQL schema for monitoring"""
        conn = psycopg2.connect(**self.pg_config)
        cur = conn.cursor()

        # Create monitoring metrics table (TimescaleDB hypertable)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS monitoring_metrics (
                id SERIAL,
                metric_type VARCHAR(50) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value NUMERIC NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                source VARCHAR(50) NOT NULL,

                -- Context fields
                session_id VARCHAR(255),
                agent_id VARCHAR(100),
                container_id VARCHAR(100),
                project_path TEXT,

                -- Additional data
                tags JSONB,
                metadata JSONB,

                -- For joining with context_items
                context_item_id UUID,

                PRIMARY KEY (id, timestamp)
            );
        """
        )

        # Create hypertable if TimescaleDB is available
        try:
            cur.execute(
                """
                SELECT create_hypertable('monitoring_metrics', 'timestamp',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 hour');
            """
            )
            logger.info("Created TimescaleDB hypertable for monitoring_metrics")
        except Exception as e:
            logger.warning(
                f"Could not create hypertable (TimescaleDB may not be installed): {e}"
            )

        # Create indexes for common queries
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_monitoring_metrics_session
            ON monitoring_metrics(session_id, timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_monitoring_metrics_type
            ON monitoring_metrics(metric_type, timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_monitoring_metrics_source
            ON monitoring_metrics(source, timestamp DESC);
        """
        )

        # Create aggregated views
        cur.execute(
            """
            CREATE OR REPLACE VIEW token_usage_hourly AS
            SELECT
                date_trunc('hour', timestamp) as hour,
                source,
                SUM(metric_value) as total_tokens,
                COUNT(*) as request_count,
                AVG(metric_value) as avg_tokens
            FROM monitoring_metrics
            WHERE metric_type = 'token_usage'
            GROUP BY date_trunc('hour', timestamp), source;

            CREATE OR REPLACE VIEW system_resources_current AS
            SELECT DISTINCT ON (metric_name)
                metric_name,
                metric_value,
                timestamp,
                metadata
            FROM monitoring_metrics
            WHERE metric_type = 'system_resource'
                AND timestamp > NOW() - INTERVAL '5 minutes'
            ORDER BY metric_name, timestamp DESC;
        """
        )

        conn.commit()
        conn.close()
        logger.info("PostgreSQL monitoring schema initialized")

    async def collect_token_usage(self):
        """Collect token usage from SQLite and store in PostgreSQL"""
        import sqlite3

        # Query existing SQLite database
        sqlite_conn = sqlite3.connect("/home/opsvi/master_root/chat_logs.db")
        sqlite_conn.row_factory = sqlite3.Row
        cur = sqlite_conn.cursor()

        # Get recent token usage
        cur.execute(
            """
            SELECT
                json_extract(raw_json, '$.sessionId') as session_id,
                json_extract(raw_json, '$.message.model') as model,
                json_extract(raw_json, '$.message.usage.input_tokens') as input_tokens,
                json_extract(raw_json, '$.message.usage.cache_read_input_tokens') as cache_tokens,
                json_extract(raw_json, '$.message.usage.output_tokens') as output_tokens,
                json_extract(raw_json, '$.timestamp') as timestamp,
                json_extract(raw_json, '$.cwd') as cwd
            FROM nodes
            WHERE node_type = 'assistant'
                AND json_extract(raw_json, '$.message.usage') IS NOT NULL
                AND json_extract(raw_json, '$.timestamp') > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
        """
        )

        rows = cur.fetchall()
        sqlite_conn.close()

        # Store in PostgreSQL
        pg_conn = await asyncpg.connect(**self.pg_config)

        for row in rows:
            # Calculate total tokens
            total_tokens = (
                (row["input_tokens"] or 0)
                + (row["cache_tokens"] or 0)
                + (row["output_tokens"] or 0)
            )

            metric = MonitoringMetric(
                metric_type="token_usage",
                metric_name="claude_tokens",
                metric_value=total_tokens,
                timestamp=datetime.fromisoformat(
                    row["timestamp"].replace("Z", "+00:00")
                ),
                source="claude_cli",
                session_id=row["session_id"],
                project_path=row["cwd"],
                metadata={
                    "model": row["model"],
                    "input_tokens": row["input_tokens"],
                    "cache_tokens": row["cache_tokens"],
                    "output_tokens": row["output_tokens"],
                },
            )

            await self.store_metric(pg_conn, metric)

        await pg_conn.close()
        logger.info(f"Collected {len(rows)} token usage records")

    async def collect_system_resources(self):
        """Collect system resource metrics"""
        metrics = []

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(
            MonitoringMetric(
                metric_type="system_resource",
                metric_name="cpu_percent",
                metric_value=cpu_percent,
                timestamp=datetime.now(),
                source="system",
                metadata={"cores": psutil.cpu_count()},
            )
        )

        # Memory usage
        mem = psutil.virtual_memory()
        metrics.append(
            MonitoringMetric(
                metric_type="system_resource",
                metric_name="memory_percent",
                metric_value=mem.percent,
                timestamp=datetime.now(),
                source="system",
                metadata={
                    "total_gb": mem.total / (1024**3),
                    "used_gb": mem.used / (1024**3),
                    "available_gb": mem.available / (1024**3),
                },
            )
        )

        # Disk usage
        disk = psutil.disk_usage("/")
        metrics.append(
            MonitoringMetric(
                metric_type="system_resource",
                metric_name="disk_percent",
                metric_value=disk.percent,
                timestamp=datetime.now(),
                source="system",
                metadata={
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                },
            )
        )

        # Store metrics
        pg_conn = await asyncpg.connect(**self.pg_config)
        for metric in metrics:
            await self.store_metric(pg_conn, metric)
        await pg_conn.close()

        # Publish to Redis for real-time
        if self.redis_client:
            for metric in metrics:
                self.redis_client.publish(
                    "monitoring:system_resources",
                    json.dumps(asdict(metric), default=str),
                )

    async def collect_docker_metrics(self):
        """Collect metrics from Docker containers running Claude"""
        containers_with_claude = []

        for container in self.docker_client.containers.list():
            # Check if container has Claude activity
            env_vars = container.attrs["Config"]["Env"]
            has_claude = any("CLAUDE" in var for var in env_vars)

            if has_claude:
                # Get container stats
                stats = container.stats(stream=False)

                # Calculate CPU percentage
                cpu_delta = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_delta = (
                    stats["cpu_stats"]["system_cpu_usage"]
                    - stats["precpu_stats"]["system_cpu_usage"]
                )
                cpu_percent = (
                    (cpu_delta / system_delta) * 100 if system_delta > 0 else 0
                )

                # Memory usage
                mem_usage = stats["memory_stats"].get("usage", 0)
                mem_limit = stats["memory_stats"].get("limit", 1)
                mem_percent = (mem_usage / mem_limit) * 100

                metric = MonitoringMetric(
                    metric_type="docker_container",
                    metric_name=f"container_{container.name}",
                    metric_value=cpu_percent,
                    timestamp=datetime.now(),
                    source="docker",
                    container_id=container.id[:12],
                    metadata={
                        "name": container.name,
                        "image": container.image.tags[0]
                        if container.image.tags
                        else "unknown",
                        "status": container.status,
                        "cpu_percent": cpu_percent,
                        "memory_percent": mem_percent,
                        "memory_mb": mem_usage / (1024 * 1024),
                    },
                )

                containers_with_claude.append(metric)

        # Store metrics
        if containers_with_claude:
            pg_conn = await asyncpg.connect(**self.pg_config)
            for metric in containers_with_claude:
                await self.store_metric(pg_conn, metric)
            await pg_conn.close()

            logger.info(
                f"Collected metrics for {len(containers_with_claude)} Docker containers"
            )

    async def collect_agent_orchestrator_metrics(self):
        """Collect metrics from agent orchestrator if running"""
        # Check for orchestrator output
        orchestrator_dirs = [
            Path("/tmp/agent_teams"),
            Path("/tmp/claude_monitor_build"),
            Path("/home/opsvi/master_root/apps/agent-orchestrator/output"),
        ]

        metrics = []
        for dir_path in orchestrator_dirs:
            if not dir_path.exists():
                continue

            # Look for task files
            for task_file in dir_path.glob("tasks/*.json"):
                try:
                    task_data = json.loads(task_file.read_text())

                    if task_data.get("status") == "running":
                        metric = MonitoringMetric(
                            metric_type="agent_status",
                            metric_name="active_agent",
                            metric_value=1,
                            timestamp=datetime.now(),
                            source="orchestrator",
                            agent_id=task_data.get("task_id"),
                            metadata=task_data,
                        )
                        metrics.append(metric)
                except Exception as e:
                    logger.error(f"Error reading task file {task_file}: {e}")

        if metrics:
            pg_conn = await asyncpg.connect(**self.pg_config)
            for metric in metrics:
                await self.store_metric(pg_conn, metric)
            await pg_conn.close()

            logger.info(f"Collected {len(metrics)} agent orchestrator metrics")

    async def store_metric(self, conn, metric: MonitoringMetric):
        """Store a metric in PostgreSQL"""
        await conn.execute(
            """
            INSERT INTO monitoring_metrics
            (metric_type, metric_name, metric_value, timestamp, source,
             session_id, agent_id, container_id, project_path, tags, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
            metric.metric_type,
            metric.metric_name,
            metric.metric_value,
            metric.timestamp,
            metric.source,
            metric.session_id,
            metric.agent_id,
            metric.container_id,
            metric.project_path,
            json.dumps(metric.tags) if metric.tags else None,
            json.dumps(metric.metadata, default=str) if metric.metadata else None,
        )

    async def run_collection_loop(self, interval: int = 10):
        """Run continuous collection loop"""
        logger.info(f"Starting monitoring collection loop (interval: {interval}s)")

        while True:
            try:
                # Run all collectors
                await asyncio.gather(
                    self.collect_token_usage(),
                    self.collect_system_resources(),
                    self.collect_docker_metrics(),
                    self.collect_agent_orchestrator_metrics(),
                    return_exceptions=True,
                )

                # Create important events for Neo4j
                await self.detect_important_events()

            except Exception as e:
                logger.error(f"Error in collection loop: {e}")

            await asyncio.sleep(interval)

    async def detect_important_events(self):
        """Detect important events that should create Neo4j relationships"""
        pg_conn = await asyncpg.connect(**self.pg_config)

        # Check for high resource usage
        high_cpu = await pg_conn.fetchval(
            """
            SELECT metric_value FROM monitoring_metrics
            WHERE metric_type = 'system_resource'
                AND metric_name = 'cpu_percent'
                AND timestamp > NOW() - INTERVAL '1 minute'
            ORDER BY timestamp DESC
            LIMIT 1
        """
        )

        if high_cpu and high_cpu > 80:
            # This would trigger Neo4j relationship creation
            logger.warning(f"High CPU detected: {high_cpu}%")
            # TODO: Send to Neo4j

        # Check for excessive token usage
        recent_tokens = await pg_conn.fetchval(
            """
            SELECT SUM(metric_value) FROM monitoring_metrics
            WHERE metric_type = 'token_usage'
                AND timestamp > NOW() - INTERVAL '1 hour'
        """
        )

        if recent_tokens and recent_tokens > 100000:
            logger.warning(f"High token usage in last hour: {recent_tokens}")
            # TODO: Send to Neo4j

        await pg_conn.close()

    def get_dashboard_metrics(self) -> Dict:
        """Get current metrics for dashboard display"""
        conn = psycopg2.connect(**self.pg_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "system_resources": {},
            "token_usage": {},
            "docker_containers": [],
            "active_agents": [],
        }

        # Get current system resources
        cur.execute(
            """
            SELECT * FROM system_resources_current
        """
        )
        for row in cur.fetchall():
            dashboard["system_resources"][row["metric_name"]] = {
                "value": float(row["metric_value"]),
                "metadata": row["metadata"],
            }

        # Get hourly token usage
        cur.execute(
            """
            SELECT * FROM token_usage_hourly
            WHERE hour > NOW() - INTERVAL '24 hours'
            ORDER BY hour DESC
        """
        )
        dashboard["token_usage"]["hourly"] = cur.fetchall()

        conn.close()
        return dashboard


async def main():
    """Main entry point for enhanced monitoring"""

    # PostgreSQL configuration
    pg_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", 5432),
        "database": os.getenv("POSTGRES_DB", "unified_context"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }

    # Redis configuration (optional)
    redis_config = {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": os.getenv("REDIS_PORT", 6379),
        "db": 0,
    }

    # Create and run monitoring service
    monitor = UnifiedMonitoringService(pg_config, redis_config)

    # Start collection loop
    await monitor.run_collection_loop(interval=10)


if __name__ == "__main__":
    asyncio.run(main())
