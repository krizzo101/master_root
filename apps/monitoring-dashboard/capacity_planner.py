#!/usr/bin/env python3
"""
Advanced Capacity Planning System for Unified Context System

Comprehensive capacity planning and forecasting for:
- Database growth trends (PostgreSQL + Neo4j)
- Vector storage requirements and scaling
- System resource utilization forecasting
- Cost analysis and optimization
- Infrastructure scaling recommendations
- Performance capacity modeling
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import psycopg2
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class GrowthMetric:
    metric_name: str
    current_value: float
    unit: str
    growth_rate_per_week: float
    confidence_score: float  # 0-1 confidence in prediction
    data_points: int
    trend_direction: str  # 'increasing', 'decreasing', 'stable'


@dataclass
class CapacityForecast:
    component: str
    metric: str
    current_value: float
    forecasts: Dict[str, float]  # timeframe -> predicted value
    capacity_limits: Dict[str, float]
    warning_thresholds: Dict[str, float]
    recommendations: List[str]
    confidence: float


@dataclass
class ResourceRequirement:
    resource_type: str  # 'cpu', 'memory', 'disk', 'network'
    current_usage: float
    projected_usage: Dict[str, float]  # timeframe -> usage
    capacity_limit: float
    scaling_options: List[Dict[str, Any]]
    cost_implications: Dict[str, float]


@dataclass
class ScalingRecommendation:
    priority: str  # 'immediate', 'short_term', 'medium_term', 'long_term'
    component: str
    action_type: str  # 'scale_up', 'scale_out', 'optimize', 'migrate'
    description: str
    estimated_cost: float
    risk_level: str
    implementation_timeline: str
    expected_benefits: List[str]


@dataclass
class CapacityPlanningReport:
    report_id: str
    generated_at: str
    analysis_period: str
    growth_analysis: List[GrowthMetric]
    capacity_forecasts: List[CapacityForecast]
    resource_requirements: List[ResourceRequirement]
    scaling_recommendations: List[ScalingRecommendation]
    cost_projections: Dict[str, float]
    risk_assessment: Dict[str, Any]
    executive_summary: str


class CapacityPlanner:
    """Advanced capacity planning with ML-based forecasting."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.historical_data = deque(maxlen=10000)  # Keep last 10k measurements
        self.growth_models = {}
        self.capacity_limits = self._initialize_capacity_limits()
        self.cost_models = self._initialize_cost_models()

        # Database connections
        self.postgres_conn = None
        self.neo4j_driver = None

        # Data collection
        self.data_points = defaultdict(deque)
        self.collection_interval = 300  # 5 minutes

    def _initialize_capacity_limits(self) -> Dict[str, Dict[str, float]]:
        """Initialize known capacity limits for different components."""
        return {
            "postgresql": {
                "max_connections": 200,
                "shared_buffers_gb": 8,
                "max_db_size_gb": 500,
                "max_table_size_gb": 100,
                "max_concurrent_queries": 50,
            },
            "neo4j": {
                "heap_memory_gb": 16,
                "page_cache_gb": 32,
                "max_nodes": 10000000,
                "max_relationships": 100000000,
                "max_concurrent_transactions": 100,
            },
            "system": {
                "max_cpu_percent": 85,
                "max_memory_percent": 90,
                "max_disk_percent": 85,
                "max_load_average": 8,
                "max_open_files": 65536,
            },
            "vector_storage": {
                "max_vectors": 1000000,
                "max_index_size_gb": 50,
                "search_latency_ms": 100,
                "max_dimension": 1024,
            },
            "docker": {
                "max_containers": 50,
                "max_memory_per_container_gb": 4,
                "max_cpu_per_container_percent": 50,
            },
        }

    def _initialize_cost_models(self) -> Dict[str, Any]:
        """Initialize cost models for different resources."""
        return {
            "compute": {
                "cpu_core_monthly": 25.0,  # USD per core per month
                "memory_gb_monthly": 3.5,  # USD per GB per month
                "storage_gb_monthly": 0.10,  # USD per GB per month
            },
            "database": {
                "postgres_instance_monthly": 150.0,
                "neo4j_instance_monthly": 200.0,
                "backup_storage_gb_monthly": 0.05,
            },
            "network": {"bandwidth_gb_monthly": 0.09, "load_balancer_monthly": 25.0},
            "maintenance": {
                "admin_hours_monthly": 2000.0,  # USD per month for admin time
                "monitoring_tools_monthly": 100.0,
            },
        }

    async def initialize(self):
        """Initialize connections to data sources."""
        try:
            # PostgreSQL connection
            postgres_config = self.config.get("postgres", {})
            if postgres_config:
                self.postgres_conn = psycopg2.connect(**postgres_config)
                self.postgres_conn.autocommit = True

            # Neo4j connection
            neo4j_config = self.config.get("neo4j", {})
            if neo4j_config:
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_config["uri"],
                    auth=(neo4j_config["user"], neo4j_config["password"]),
                )

            logger.info("Capacity planner initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize capacity planner: {e}")
            raise

    async def collect_metrics(self):
        """Collect metrics for capacity planning analysis."""
        timestamp = datetime.now()
        metrics = {
            "timestamp": timestamp.isoformat(),
            "postgres": await self._collect_postgres_metrics(),
            "neo4j": await self._collect_neo4j_metrics(),
            "system": await self._collect_system_metrics(),
            "vector_storage": await self._collect_vector_metrics(),
            "docker": await self._collect_docker_metrics(),
        }

        # Store historical data
        self.historical_data.append(metrics)

        # Update growth models
        await self._update_growth_models(metrics)

        return metrics

    async def _collect_postgres_metrics(self) -> Dict[str, Any]:
        """Collect PostgreSQL capacity-related metrics."""
        metrics = {}

        try:
            if not self.postgres_conn:
                return metrics

            cursor = self.postgres_conn.cursor()

            # Database size metrics
            cursor.execute(
                """
                SELECT
                    pg_database_size(current_database()) as db_size,
                    (SELECT count(*) FROM context_items) as total_records,
                    (SELECT count(*) FROM context_items WHERE embedding IS NOT NULL) as vector_records,
                    (SELECT count(*) FROM pg_stat_activity) as total_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
            """
            )

            result = cursor.fetchone()
            if result:
                metrics.update(
                    {
                        "database_size_bytes": result[0],
                        "total_records": result[1],
                        "vector_records": result[2],
                        "total_connections": result[3],
                        "active_connections": result[4],
                    }
                )

            # Table size metrics
            cursor.execute(
                """
                SELECT
                    relname,
                    pg_total_relation_size(oid) as size_bytes,
                    n_tup_ins + n_tup_upd + n_tup_del as modifications
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(oid) DESC
                LIMIT 10
            """
            )

            table_sizes = []
            for row in cursor.fetchall():
                table_sizes.append(
                    {
                        "table_name": row[0],
                        "size_bytes": row[1],
                        "modifications": row[2],
                    }
                )

            metrics["table_sizes"] = table_sizes

            # Query performance metrics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_queries,
                    AVG(mean_exec_time) as avg_query_time,
                    MAX(max_exec_time) as max_query_time
                FROM pg_stat_statements
                WHERE calls > 1
            """
            )

            perf_result = cursor.fetchone()
            if perf_result:
                metrics.update(
                    {
                        "total_queries": perf_result[0] or 0,
                        "avg_query_time_ms": perf_result[1] or 0,
                        "max_query_time_ms": perf_result[2] or 0,
                    }
                )

        except Exception as e:
            logger.error(f"Error collecting PostgreSQL metrics: {e}")

        return metrics

    async def _collect_neo4j_metrics(self) -> Dict[str, Any]:
        """Collect Neo4j capacity-related metrics."""
        metrics = {}

        try:
            if not self.neo4j_driver:
                return metrics

            with self.neo4j_driver.session() as session:
                # Graph size metrics
                result = session.run(
                    """
                    MATCH (n) WITH count(n) as node_count
                    MATCH ()-[r]->() WITH node_count, count(r) as rel_count
                    RETURN node_count, rel_count
                """
                )

                graph_stats = result.single()
                if graph_stats:
                    metrics.update(
                        {
                            "node_count": graph_stats["node_count"],
                            "relationship_count": graph_stats["rel_count"],
                            "total_graph_elements": graph_stats["node_count"]
                            + graph_stats["rel_count"],
                        }
                    )

                # Memory usage metrics
                try:
                    memory_result = session.run(
                        "CALL dbms.queryJmx('java.lang:type=Memory')"
                    ).single()
                    if memory_result and "attributes" in memory_result:
                        heap_memory = memory_result["attributes"]["HeapMemoryUsage"][
                            "value"
                        ]
                        metrics.update(
                            {
                                "heap_used_bytes": heap_memory["used"],
                                "heap_max_bytes": heap_memory["max"],
                                "heap_usage_percent": (
                                    heap_memory["used"] / heap_memory["max"]
                                )
                                * 100,
                            }
                        )
                except Exception:
                    pass

                # Storage metrics
                try:
                    store_result = session.run("CALL apoc.monitor.store()").single()
                    if store_result:
                        metrics.update(
                            {
                                "store_size_bytes": store_result["totalStoreSize"],
                                "node_store_bytes": store_result.get(
                                    "nodeStoreSize", 0
                                ),
                                "relationship_store_bytes": store_result.get(
                                    "relStoreSize", 0
                                ),
                            }
                        )
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error collecting Neo4j metrics: {e}")

        return metrics

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system resource metrics."""
        metrics = {}

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = (
                list(psutil.getloadavg())
                if hasattr(psutil, "getloadavg")
                else [0, 0, 0]
            )

            metrics.update(
                {
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "load_average_1m": load_avg[0],
                    "load_average_5m": load_avg[1],
                    "load_average_15m": load_avg[2],
                }
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.update(
                {
                    "memory_total_bytes": memory.total,
                    "memory_used_bytes": memory.used,
                    "memory_available_bytes": memory.available,
                    "memory_percent": memory.percent,
                    "memory_cached_bytes": getattr(memory, "cached", 0),
                }
            )

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_io = psutil.disk_io_counters()

            metrics.update(
                {
                    "disk_total_bytes": disk.total,
                    "disk_used_bytes": disk.used,
                    "disk_free_bytes": disk.free,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "disk_read_bytes": disk_io.read_bytes if disk_io else 0,
                    "disk_write_bytes": disk_io.write_bytes if disk_io else 0,
                }
            )

            # Network metrics
            network_io = psutil.net_io_counters()
            if network_io:
                metrics.update(
                    {
                        "network_bytes_sent": network_io.bytes_sent,
                        "network_bytes_recv": network_io.bytes_recv,
                        "network_packets_sent": network_io.packets_sent,
                        "network_packets_recv": network_io.packets_recv,
                    }
                )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

        return metrics

    async def _collect_vector_metrics(self) -> Dict[str, Any]:
        """Collect vector storage metrics."""
        metrics = {}

        try:
            if not self.postgres_conn:
                return metrics

            cursor = self.postgres_conn.cursor()

            # Vector statistics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_items,
                    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as items_with_vectors,
                    AVG(array_length(embedding, 1)) as avg_dimensions,
                    pg_size_pretty(SUM(pg_column_size(embedding))) as total_vector_size_pretty,
                    SUM(pg_column_size(embedding)) as total_vector_size_bytes
                FROM context_items
            """
            )

            result = cursor.fetchone()
            if result:
                total_items = result[0] or 0
                items_with_vectors = result[1] or 0

                metrics.update(
                    {
                        "total_items": total_items,
                        "items_with_vectors": items_with_vectors,
                        "vector_coverage_percent": (
                            items_with_vectors / max(total_items, 1)
                        )
                        * 100,
                        "avg_vector_dimensions": result[2] or 0,
                        "total_vector_size_bytes": result[4] or 0,
                    }
                )

            # Vector index statistics
            cursor.execute(
                """
                SELECT
                    indexname,
                    pg_relation_size(indexrelid) as index_size_bytes
                FROM pg_stat_user_indexes
                WHERE indexname LIKE '%embedding%' OR indexname LIKE '%vector%'
            """
            )

            vector_indexes = []
            total_index_size = 0
            for row in cursor.fetchall():
                index_size = row[1] or 0
                vector_indexes.append({"index_name": row[0], "size_bytes": index_size})
                total_index_size += index_size

            metrics.update(
                {
                    "vector_indexes": vector_indexes,
                    "total_index_size_bytes": total_index_size,
                }
            )

        except Exception as e:
            logger.error(f"Error collecting vector metrics: {e}")

        return metrics

    async def _collect_docker_metrics(self) -> Dict[str, Any]:
        """Collect Docker container metrics."""
        metrics = {}

        try:
            import docker

            client = docker.from_env()

            containers = client.containers.list(all=True)
            context_containers = [
                c
                for c in containers
                if any(
                    keyword in c.name.lower()
                    for keyword in ["unified_context", "postgres", "neo4j", "embedding"]
                )
            ]

            total_memory_usage = 0
            total_cpu_usage = 0
            running_containers = 0

            container_details = []
            for container in context_containers:
                try:
                    if container.status == "running":
                        stats = container.stats(stream=False)

                        memory_usage = stats["memory_stats"].get("usage", 0)
                        memory_limit = stats["memory_stats"].get("limit", 1)

                        # Calculate CPU percentage
                        cpu_delta = (
                            stats["cpu_stats"]["cpu_usage"]["total_usage"]
                            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                        )
                        system_delta = (
                            stats["cpu_stats"]["system_cpu_usage"]
                            - stats["precpu_stats"]["system_cpu_usage"]
                        )
                        cpu_percent = 0
                        if system_delta > 0:
                            cpu_percent = (cpu_delta / system_delta) * 100

                        total_memory_usage += memory_usage
                        total_cpu_usage += cpu_percent
                        running_containers += 1

                        container_details.append(
                            {
                                "name": container.name,
                                "memory_usage_bytes": memory_usage,
                                "memory_limit_bytes": memory_limit,
                                "cpu_percent": cpu_percent,
                                "status": container.status,
                            }
                        )

                except Exception as e:
                    logger.debug(
                        f"Error getting stats for container {container.name}: {e}"
                    )

            metrics.update(
                {
                    "total_containers": len(context_containers),
                    "running_containers": running_containers,
                    "total_memory_usage_bytes": total_memory_usage,
                    "avg_cpu_percent": total_cpu_usage / max(running_containers, 1),
                    "container_details": container_details,
                }
            )

        except Exception as e:
            logger.error(f"Error collecting Docker metrics: {e}")

        return metrics

    async def _update_growth_models(self, current_metrics: Dict[str, Any]):
        """Update growth models with new metrics."""
        try:
            # Extract key metrics for growth analysis
            growth_metrics = self._extract_growth_metrics(current_metrics)

            for metric_name, value in growth_metrics.items():
                if metric_name not in self.data_points:
                    self.data_points[metric_name] = deque(maxlen=1000)

                self.data_points[metric_name].append(
                    {"timestamp": current_metrics["timestamp"], "value": value}
                )

                # Update growth model if we have enough data points
                if len(self.data_points[metric_name]) >= 10:
                    self.growth_models[metric_name] = self._calculate_growth_model(
                        list(self.data_points[metric_name])
                    )

        except Exception as e:
            logger.error(f"Error updating growth models: {e}")

    def _extract_growth_metrics(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Extract key metrics for growth analysis."""
        growth_metrics = {}

        # PostgreSQL metrics
        postgres = metrics.get("postgres", {})
        if postgres:
            growth_metrics.update(
                {
                    "postgres_db_size": postgres.get("database_size_bytes", 0),
                    "postgres_total_records": postgres.get("total_records", 0),
                    "postgres_vector_records": postgres.get("vector_records", 0),
                    "postgres_connections": postgres.get("active_connections", 0),
                }
            )

        # Neo4j metrics
        neo4j = metrics.get("neo4j", {})
        if neo4j:
            growth_metrics.update(
                {
                    "neo4j_nodes": neo4j.get("node_count", 0),
                    "neo4j_relationships": neo4j.get("relationship_count", 0),
                    "neo4j_heap_usage": neo4j.get("heap_used_bytes", 0),
                }
            )

        # System metrics
        system = metrics.get("system", {})
        if system:
            growth_metrics.update(
                {
                    "system_cpu_percent": system.get("cpu_percent", 0),
                    "system_memory_percent": system.get("memory_percent", 0),
                    "system_disk_used": system.get("disk_used_bytes", 0),
                    "system_load_average": system.get("load_average_1m", 0),
                }
            )

        # Vector storage metrics
        vector = metrics.get("vector_storage", {})
        if vector:
            growth_metrics.update(
                {
                    "vector_total_size": vector.get("total_vector_size_bytes", 0),
                    "vector_index_size": vector.get("total_index_size_bytes", 0),
                    "vector_count": vector.get("items_with_vectors", 0),
                }
            )

        return growth_metrics

    def _calculate_growth_model(
        self, data_points: List[Dict[str, Any]]
    ) -> GrowthMetric:
        """Calculate growth model for a metric."""
        if len(data_points) < 2:
            return None

        # Extract values and timestamps
        values = [point["value"] for point in data_points]
        timestamps = [
            datetime.fromisoformat(point["timestamp"]) for point in data_points
        ]

        # Convert to numeric sequence
        time_deltas = [
            (ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps
        ]  # Hours

        try:
            # Calculate linear growth rate
            growth_rate = self._calculate_linear_regression_slope(time_deltas, values)

            # Convert to weekly growth rate
            weekly_growth_rate = growth_rate * 24 * 7  # per week

            # Calculate confidence based on R-squared
            confidence = self._calculate_r_squared(time_deltas, values, growth_rate)

            # Determine trend direction
            if (
                abs(weekly_growth_rate) < values[-1] * 0.01
            ):  # Less than 1% change per week
                trend_direction = "stable"
            elif weekly_growth_rate > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"

            return GrowthMetric(
                metric_name=data_points[0].get("metric_name", "unknown"),
                current_value=values[-1],
                unit="",  # Will be set by caller
                growth_rate_per_week=weekly_growth_rate,
                confidence_score=max(0, min(1, confidence)),
                data_points=len(data_points),
                trend_direction=trend_direction,
            )

        except Exception as e:
            logger.error(f"Error calculating growth model: {e}")
            return None

    def _calculate_linear_regression_slope(
        self, x_values: List[float], y_values: List[float]
    ) -> float:
        """Calculate linear regression slope."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0

        n = len(x_values)
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0

        return numerator / denominator

    def _calculate_r_squared(
        self, x_values: List[float], y_values: List[float], slope: float
    ) -> float:
        """Calculate R-squared correlation coefficient."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0

        y_mean = statistics.mean(y_values)
        x_mean = statistics.mean(x_values)

        # Calculate predicted values
        y_pred = [slope * (x - x_mean) + y_mean for x in x_values]

        # Calculate R-squared
        ss_res = sum((y - y_p) ** 2 for y, y_p in zip(y_values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)

        if ss_tot == 0:
            return 0

        return 1 - (ss_res / ss_tot)

    async def generate_capacity_forecast(
        self, timeframes: List[str] = None
    ) -> List[CapacityForecast]:
        """Generate capacity forecasts for different timeframes."""
        if timeframes is None:
            timeframes = ["1_month", "3_months", "6_months", "1_year"]

        forecasts = []

        for metric_name, growth_model in self.growth_models.items():
            if growth_model is None:
                continue

            component = metric_name.split("_")[0]  # Extract component from metric name

            # Generate forecasts for each timeframe
            forecast_values = {}
            for timeframe in timeframes:
                weeks = self._timeframe_to_weeks(timeframe)
                projected_value = growth_model.current_value + (
                    growth_model.growth_rate_per_week * weeks
                )
                forecast_values[timeframe] = max(
                    0, projected_value
                )  # Ensure non-negative

            # Get capacity limits for this component and metric
            capacity_limits = self._get_capacity_limits(component, metric_name)
            warning_thresholds = self._get_warning_thresholds(component, metric_name)

            # Generate recommendations
            recommendations = self._generate_forecast_recommendations(
                metric_name, growth_model, forecast_values, capacity_limits
            )

            forecast = CapacityForecast(
                component=component,
                metric=metric_name,
                current_value=growth_model.current_value,
                forecasts=forecast_values,
                capacity_limits=capacity_limits,
                warning_thresholds=warning_thresholds,
                recommendations=recommendations,
                confidence=growth_model.confidence_score,
            )

            forecasts.append(forecast)

        return forecasts

    def _timeframe_to_weeks(self, timeframe: str) -> float:
        """Convert timeframe string to weeks."""
        timeframe_map = {
            "1_month": 4.33,
            "3_months": 13.0,
            "6_months": 26.0,
            "1_year": 52.0,
            "2_years": 104.0,
        }
        return timeframe_map.get(timeframe, 4.33)

    def _get_capacity_limits(
        self, component: str, metric_name: str
    ) -> Dict[str, float]:
        """Get capacity limits for a specific metric."""
        limits = self.capacity_limits.get(component, {})

        # Map metric names to limit keys
        metric_mapping = {
            "postgres_db_size": "max_db_size_gb",
            "postgres_total_records": "max_table_size_gb",  # Approximate
            "postgres_connections": "max_connections",
            "neo4j_nodes": "max_nodes",
            "neo4j_relationships": "max_relationships",
            "neo4j_heap_usage": "heap_memory_gb",
            "system_cpu_percent": "max_cpu_percent",
            "system_memory_percent": "max_memory_percent",
            "system_disk_used": "max_disk_percent",
            "vector_count": "max_vectors",
        }

        limit_key = None
        for metric_pattern, limit_key_mapped in metric_mapping.items():
            if metric_pattern in metric_name:
                limit_key = limit_key_mapped
                break

        if limit_key and limit_key in limits:
            return {"hard_limit": limits[limit_key]}

        return {}

    def _get_warning_thresholds(
        self, component: str, metric_name: str
    ) -> Dict[str, float]:
        """Get warning thresholds for a specific metric."""
        limits = self._get_capacity_limits(component, metric_name)

        if "hard_limit" in limits:
            hard_limit = limits["hard_limit"]
            return {"warning": hard_limit * 0.7, "critical": hard_limit * 0.85}

        return {}

    def _generate_forecast_recommendations(
        self,
        metric_name: str,
        growth_model: GrowthMetric,
        forecasts: Dict[str, float],
        capacity_limits: Dict[str, float],
    ) -> List[str]:
        """Generate recommendations based on forecast."""
        recommendations = []

        if "hard_limit" in capacity_limits:
            hard_limit = capacity_limits["hard_limit"]

            # Check if any forecast exceeds limits
            for timeframe, forecast_value in forecasts.items():
                if forecast_value > hard_limit:
                    recommendations.append(
                        f"Capacity limit will be exceeded in {timeframe} - consider scaling up"
                    )
                elif forecast_value > hard_limit * 0.85:
                    recommendations.append(
                        f"Approaching capacity limit in {timeframe} - plan for scaling"
                    )

        # Growth rate based recommendations
        if (
            growth_model.growth_rate_per_week > growth_model.current_value * 0.1
        ):  # >10% per week
            recommendations.append(
                "High growth rate detected - monitor closely and plan for scaling"
            )
        elif growth_model.growth_rate_per_week < 0:
            recommendations.append(
                "Negative growth trend - consider optimization or right-sizing"
            )

        # Confidence-based recommendations
        if growth_model.confidence_score < 0.5:
            recommendations.append(
                "Low confidence in forecast - collect more data for accurate predictions"
            )

        return recommendations

    async def generate_scaling_recommendations(
        self, forecasts: List[CapacityForecast]
    ) -> List[ScalingRecommendation]:
        """Generate scaling recommendations based on forecasts."""
        recommendations = []

        for forecast in forecasts:
            # Analyze forecast to determine scaling needs
            scaling_needs = self._analyze_scaling_needs(forecast)

            for need in scaling_needs:
                recommendation = self._create_scaling_recommendation(forecast, need)
                if recommendation:
                    recommendations.append(recommendation)

        # Sort by priority
        priority_order = {
            "immediate": 0,
            "short_term": 1,
            "medium_term": 2,
            "long_term": 3,
        }
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))

        return recommendations

    def _analyze_scaling_needs(
        self, forecast: CapacityForecast
    ) -> List[Dict[str, Any]]:
        """Analyze forecast to determine scaling needs."""
        scaling_needs = []

        # Check capacity limits
        if "hard_limit" in forecast.capacity_limits:
            hard_limit = forecast.capacity_limits["hard_limit"]

            for timeframe, predicted_value in forecast.forecasts.items():
                if predicted_value > hard_limit:
                    priority = self._determine_priority(timeframe)
                    scaling_needs.append(
                        {
                            "timeframe": timeframe,
                            "priority": priority,
                            "action_needed": "scale_up",
                            "predicted_value": predicted_value,
                            "limit_value": hard_limit,
                            "severity": "critical",
                        }
                    )
                elif predicted_value > hard_limit * 0.85:
                    priority = self._determine_priority(timeframe)
                    scaling_needs.append(
                        {
                            "timeframe": timeframe,
                            "priority": priority,
                            "action_needed": "scale_up",
                            "predicted_value": predicted_value,
                            "limit_value": hard_limit,
                            "severity": "warning",
                        }
                    )

        return scaling_needs

    def _determine_priority(self, timeframe: str) -> str:
        """Determine priority based on timeframe."""
        if timeframe == "1_month":
            return "immediate"
        elif timeframe == "3_months":
            return "short_term"
        elif timeframe == "6_months":
            return "medium_term"
        else:
            return "long_term"

    def _create_scaling_recommendation(
        self, forecast: CapacityForecast, scaling_need: Dict[str, Any]
    ) -> Optional[ScalingRecommendation]:
        """Create a scaling recommendation."""
        try:
            component = forecast.component
            metric = forecast.metric
            timeframe = scaling_need["timeframe"]
            priority = scaling_need["priority"]

            # Generate action description
            if "postgres" in component:
                action_type = "scale_up"
                description = f"Increase PostgreSQL capacity for {metric}"
                estimated_cost = self._estimate_postgres_scaling_cost(scaling_need)
                benefits = [
                    "Improved query performance",
                    "Increased data capacity",
                    "Better concurrency",
                ]

            elif "neo4j" in component:
                action_type = "scale_up"
                description = f"Increase Neo4j capacity for {metric}"
                estimated_cost = self._estimate_neo4j_scaling_cost(scaling_need)
                benefits = [
                    "Improved graph query performance",
                    "Increased graph size capacity",
                ]

            elif "system" in component:
                action_type = "scale_up"
                description = f"Increase system resources for {metric}"
                estimated_cost = self._estimate_system_scaling_cost(scaling_need)
                benefits = ["Better system performance", "Increased capacity"]

            elif "vector" in component:
                action_type = "optimize"
                description = f"Optimize vector storage for {metric}"
                estimated_cost = self._estimate_vector_scaling_cost(scaling_need)
                benefits = [
                    "Improved vector search performance",
                    "Better storage efficiency",
                ]

            else:
                return None

            # Determine risk level
            risk_level = "medium"
            if scaling_need["severity"] == "critical":
                risk_level = "high"
            elif priority == "long_term":
                risk_level = "low"

            # Implementation timeline
            timeline_map = {
                "immediate": "1-2 weeks",
                "short_term": "1-2 months",
                "medium_term": "3-6 months",
                "long_term": "6-12 months",
            }

            return ScalingRecommendation(
                priority=priority,
                component=component,
                action_type=action_type,
                description=description,
                estimated_cost=estimated_cost,
                risk_level=risk_level,
                implementation_timeline=timeline_map.get(priority, "3-6 months"),
                expected_benefits=benefits,
            )

        except Exception as e:
            logger.error(f"Error creating scaling recommendation: {e}")
            return None

    def _estimate_postgres_scaling_cost(self, scaling_need: Dict[str, Any]) -> float:
        """Estimate cost for PostgreSQL scaling."""
        # Base cost for larger PostgreSQL instance
        base_monthly_cost = 300.0  # USD

        # Additional storage cost
        additional_storage_gb = max(
            100, scaling_need.get("predicted_value", 0) / 1024**3
        )
        storage_cost = (
            additional_storage_gb * self.cost_models["compute"]["storage_gb_monthly"]
        )

        return base_monthly_cost + storage_cost

    def _estimate_neo4j_scaling_cost(self, scaling_need: Dict[str, Any]) -> float:
        """Estimate cost for Neo4j scaling."""
        # Base cost for larger Neo4j instance
        base_monthly_cost = 400.0  # USD

        # Additional memory cost
        additional_memory_gb = 8  # Assume 8GB additional memory needed
        memory_cost = (
            additional_memory_gb * self.cost_models["compute"]["memory_gb_monthly"]
        )

        return base_monthly_cost + memory_cost

    def _estimate_system_scaling_cost(self, scaling_need: Dict[str, Any]) -> float:
        """Estimate cost for system scaling."""
        # Base cost for larger instance
        cpu_cores = 4  # Additional cores
        memory_gb = 16  # Additional memory

        cpu_cost = cpu_cores * self.cost_models["compute"]["cpu_core_monthly"]
        memory_cost = memory_gb * self.cost_models["compute"]["memory_gb_monthly"]

        return cpu_cost + memory_cost

    def _estimate_vector_scaling_cost(self, scaling_need: Dict[str, Any]) -> float:
        """Estimate cost for vector storage scaling."""
        # Mostly storage and compute optimization costs
        additional_storage_gb = 50  # Estimated additional storage
        storage_cost = (
            additional_storage_gb * self.cost_models["compute"]["storage_gb_monthly"]
        )

        # Optimization service cost
        optimization_cost = 200.0  # USD monthly

        return storage_cost + optimization_cost

    async def generate_comprehensive_report(self) -> CapacityPlanningReport:
        """Generate comprehensive capacity planning report."""
        report_id = f"capacity_report_{int(time.time())}"

        # Collect current metrics
        current_metrics = await self.collect_metrics()

        # Generate growth analysis
        growth_analysis = []
        for metric_name, growth_model in self.growth_models.items():
            if growth_model:
                growth_analysis.append(growth_model)

        # Generate capacity forecasts
        capacity_forecasts = await self.generate_capacity_forecast()

        # Generate scaling recommendations
        scaling_recommendations = await self.generate_scaling_recommendations(
            capacity_forecasts
        )

        # Generate resource requirements
        resource_requirements = await self._generate_resource_requirements(
            capacity_forecasts
        )

        # Calculate cost projections
        cost_projections = self._calculate_cost_projections(scaling_recommendations)

        # Risk assessment
        risk_assessment = self._perform_risk_assessment(
            capacity_forecasts, scaling_recommendations
        )

        # Executive summary
        executive_summary = self._generate_executive_summary(
            growth_analysis,
            capacity_forecasts,
            scaling_recommendations,
            cost_projections,
        )

        return CapacityPlanningReport(
            report_id=report_id,
            generated_at=datetime.now().isoformat(),
            analysis_period=f"Last {len(self.historical_data)} data points",
            growth_analysis=growth_analysis,
            capacity_forecasts=capacity_forecasts,
            resource_requirements=resource_requirements,
            scaling_recommendations=scaling_recommendations,
            cost_projections=cost_projections,
            risk_assessment=risk_assessment,
            executive_summary=executive_summary,
        )

    async def _generate_resource_requirements(
        self, forecasts: List[CapacityForecast]
    ) -> List[ResourceRequirement]:
        """Generate resource requirements based on forecasts."""
        requirements = []

        # Aggregate requirements by resource type
        resource_usage = defaultdict(dict)

        for forecast in forecasts:
            if "system_cpu" in forecast.metric:
                resource_usage["cpu"]["current"] = forecast.current_value
                resource_usage["cpu"]["forecasts"] = forecast.forecasts
            elif "system_memory" in forecast.metric:
                resource_usage["memory"]["current"] = forecast.current_value
                resource_usage["memory"]["forecasts"] = forecast.forecasts
            elif "disk" in forecast.metric or "size" in forecast.metric:
                if "disk" not in resource_usage:
                    resource_usage["disk"]["current"] = 0
                    resource_usage["disk"]["forecasts"] = {}

                resource_usage["disk"]["current"] += forecast.current_value
                for timeframe, value in forecast.forecasts.items():
                    resource_usage["disk"]["forecasts"][timeframe] = (
                        resource_usage["disk"]["forecasts"].get(timeframe, 0) + value
                    )

        # Create resource requirements
        for resource_type, usage_data in resource_usage.items():
            current_usage = usage_data.get("current", 0)
            projected_usage = usage_data.get("forecasts", {})

            # Define capacity limits and scaling options
            if resource_type == "cpu":
                capacity_limit = 100.0  # 100% CPU
                scaling_options = [
                    {
                        "type": "vertical",
                        "description": "Add more CPU cores",
                        "cost_monthly": 100,
                    },
                    {
                        "type": "horizontal",
                        "description": "Add more instances",
                        "cost_monthly": 200,
                    },
                ]
            elif resource_type == "memory":
                capacity_limit = 100.0  # 100% memory
                scaling_options = [
                    {
                        "type": "vertical",
                        "description": "Add more RAM",
                        "cost_monthly": 150,
                    },
                    {
                        "type": "horizontal",
                        "description": "Add more instances",
                        "cost_monthly": 200,
                    },
                ]
            elif resource_type == "disk":
                capacity_limit = 1000 * 1024**3  # 1TB
                scaling_options = [
                    {
                        "type": "storage",
                        "description": "Add more storage",
                        "cost_monthly": 50,
                    },
                    {
                        "type": "archive",
                        "description": "Archive old data",
                        "cost_monthly": 20,
                    },
                ]
            else:
                continue

            # Calculate cost implications
            cost_implications = {}
            for timeframe, usage in projected_usage.items():
                if usage > capacity_limit:
                    # Need scaling
                    cost_implications[timeframe] = min(
                        scaling_options, key=lambda x: x["cost_monthly"]
                    )["cost_monthly"]
                else:
                    cost_implications[timeframe] = 0

            requirement = ResourceRequirement(
                resource_type=resource_type,
                current_usage=current_usage,
                projected_usage=projected_usage,
                capacity_limit=capacity_limit,
                scaling_options=scaling_options,
                cost_implications=cost_implications,
            )

            requirements.append(requirement)

        return requirements

    def _calculate_cost_projections(
        self, scaling_recommendations: List[ScalingRecommendation]
    ) -> Dict[str, float]:
        """Calculate cost projections for scaling recommendations."""
        cost_projections = {"1_month": 0, "3_months": 0, "6_months": 0, "1_year": 0}

        for recommendation in scaling_recommendations:
            monthly_cost = recommendation.estimated_cost

            if recommendation.priority == "immediate":
                cost_projections["1_month"] += monthly_cost
                cost_projections["3_months"] += monthly_cost * 3
                cost_projections["6_months"] += monthly_cost * 6
                cost_projections["1_year"] += monthly_cost * 12
            elif recommendation.priority == "short_term":
                cost_projections["3_months"] += monthly_cost * 2  # Start in month 2
                cost_projections["6_months"] += monthly_cost * 5  # 5 months of cost
                cost_projections["1_year"] += monthly_cost * 11  # 11 months of cost
            elif recommendation.priority == "medium_term":
                cost_projections["6_months"] += monthly_cost * 2  # Start in month 5
                cost_projections["1_year"] += monthly_cost * 8  # 8 months of cost
            elif recommendation.priority == "long_term":
                cost_projections["1_year"] += monthly_cost * 6  # Start in month 7

        return cost_projections

    def _perform_risk_assessment(
        self,
        forecasts: List[CapacityForecast],
        recommendations: List[ScalingRecommendation],
    ) -> Dict[str, Any]:
        """Perform risk assessment."""
        risks = []
        risk_score = 0

        # Analyze forecasts for risks
        for forecast in forecasts:
            if forecast.confidence < 0.5:
                risks.append(
                    {
                        "type": "forecast_uncertainty",
                        "component": forecast.component,
                        "description": f"Low confidence in {forecast.metric} forecast ({forecast.confidence:.2f})",
                        "severity": "medium",
                    }
                )
                risk_score += 10

            # Check for capacity exceeded
            for timeframe, value in forecast.forecasts.items():
                if "hard_limit" in forecast.capacity_limits:
                    if value > forecast.capacity_limits["hard_limit"]:
                        risks.append(
                            {
                                "type": "capacity_exceeded",
                                "component": forecast.component,
                                "description": f"{forecast.metric} will exceed capacity in {timeframe}",
                                "severity": "high",
                            }
                        )
                        risk_score += 25

        # Analyze scaling recommendations for risks
        immediate_actions = [r for r in recommendations if r.priority == "immediate"]
        if len(immediate_actions) > 3:
            risks.append(
                {
                    "type": "scaling_pressure",
                    "component": "system",
                    "description": f"{len(immediate_actions)} immediate scaling actions required",
                    "severity": "high",
                }
            )
            risk_score += 20

        # High cost risks
        total_yearly_cost = sum(r.estimated_cost * 12 for r in recommendations)
        if total_yearly_cost > 50000:  # $50k per year
            risks.append(
                {
                    "type": "high_cost",
                    "component": "budget",
                    "description": f"High scaling costs projected: ${total_yearly_cost:,.0f}/year",
                    "severity": "medium",
                }
            )
            risk_score += 15

        # Determine overall risk level
        if risk_score >= 50:
            overall_risk = "high"
        elif risk_score >= 25:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        return {
            "overall_risk_level": overall_risk,
            "risk_score": risk_score,
            "identified_risks": risks,
            "total_risks": len(risks),
            "mitigation_recommendations": self._generate_risk_mitigation(risks),
        }

    def _generate_risk_mitigation(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation recommendations."""
        mitigations = []

        for risk in risks:
            if risk["type"] == "forecast_uncertainty":
                mitigations.append(
                    "Increase monitoring frequency to improve forecast accuracy"
                )
            elif risk["type"] == "capacity_exceeded":
                mitigations.append(
                    f"Implement proactive scaling for {risk['component']}"
                )
            elif risk["type"] == "scaling_pressure":
                mitigations.append("Prioritize and phase scaling implementations")
            elif risk["type"] == "high_cost":
                mitigations.append(
                    "Review cost-optimization opportunities and phased scaling approach"
                )

        # Remove duplicates
        return list(set(mitigations))

    def _generate_executive_summary(
        self,
        growth_analysis: List[GrowthMetric],
        capacity_forecasts: List[CapacityForecast],
        scaling_recommendations: List[ScalingRecommendation],
        cost_projections: Dict[str, float],
    ) -> str:
        """Generate executive summary."""
        summary_parts = []

        # Growth trends
        high_growth_metrics = [
            g
            for g in growth_analysis
            if g.trend_direction == "increasing"
            and g.growth_rate_per_week > g.current_value * 0.05
        ]
        if high_growth_metrics:
            summary_parts.append(
                f"High growth detected in {len(high_growth_metrics)} key metrics"
            )

        # Capacity concerns
        immediate_concerns = [
            f
            for f in capacity_forecasts
            if any(
                v > f.capacity_limits.get("hard_limit", float("inf"))
                for v in f.forecasts.values()
            )
        ]
        if immediate_concerns:
            summary_parts.append(
                f"{len(immediate_concerns)} components will exceed capacity within forecast period"
            )

        # Scaling requirements
        immediate_scaling = [
            r for r in scaling_recommendations if r.priority == "immediate"
        ]
        if immediate_scaling:
            summary_parts.append(
                f"{len(immediate_scaling)} immediate scaling actions required"
            )

        # Cost impact
        yearly_cost = cost_projections.get("1_year", 0)
        if yearly_cost > 0:
            summary_parts.append(f"Projected scaling costs: ${yearly_cost:,.0f}/year")

        # Generate summary
        if not summary_parts:
            return "System capacity is currently adequate with no immediate scaling concerns identified."

        summary = "Key findings: " + "; ".join(summary_parts) + "."

        if immediate_scaling:
            summary += f" Immediate attention required for {', '.join([r.component for r in immediate_scaling])}."

        return summary

    def export_capacity_report(self, report: CapacityPlanningReport, file_path: str):
        """Export capacity planning report to JSON file."""
        with open(file_path, "w") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(f"Capacity planning report exported to {file_path}")


# Example usage
async def run_capacity_planning_demo():
    """Demo the capacity planner."""
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
    }

    planner = CapacityPlanner(config)

    try:
        await planner.initialize()

        # Collect metrics for a few iterations to build growth models
        for i in range(3):
            await planner.collect_metrics()
            await asyncio.sleep(2)  # Wait 2 seconds between collections

        # Generate comprehensive report
        report = await planner.generate_comprehensive_report()

        print("Capacity Planning Report Generated:")
        print(f"Report ID: {report.report_id}")
        print(f"Growth Metrics Analyzed: {len(report.growth_analysis)}")
        print(f"Capacity Forecasts: {len(report.capacity_forecasts)}")
        print(f"Scaling Recommendations: {len(report.scaling_recommendations)}")
        print(f"Executive Summary: {report.executive_summary}")

        # Export report
        report_path = (
            f"/home/opsvi/master_root/CAPACITY_PLANNING_REPORT_{int(time.time())}.json"
        )
        planner.export_capacity_report(report, report_path)
        print(f"\nCapacity planning report exported to: {report_path}")

        return report

    except Exception as e:
        logger.error(f"Capacity planning demo failed: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_capacity_planning_demo())
