#!/usr/bin/env python3
"""
Comprehensive Data Collection Service

Aggregates data from multiple sources:
- SQLite database queries (tokens, sessions, tool calls)
- System resources (CPU, memory, disk, network)
- Docker containers (Claude-related processes)
- Process monitoring (Claude processes)
- Log files (error patterns, performance metrics)

Features:
- Caching for performance optimization
- Cost calculations by model type
- Resource usage tracking by project
- Error rate analysis and pattern detection
- Configurable collection intervals
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, RLock
from typing import Any, Dict, List, Optional, Tuple, Union

import docker
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DB_PATH = "/home/opsvi/master_root/chat_logs.db"
CACHE_TTL = 60  # seconds
MAX_CACHE_SIZE = 1000
LOG_PATTERNS = {
    "error": r"(error|exception|failed|failure)",
    "warning": r"(warning|warn)",
    "token": r"(token[s]?|usage|cost)",
    "claude": r"(claude|anthropic)",
    "performance": r"(slow|timeout|latency|response_time)",
}

# Model pricing (per 1K tokens)
MODEL_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-2": {"input": 0.008, "output": 0.024},
    "default": {"input": 0.01, "output": 0.03},
}


@dataclass
class SystemMetrics:
    """System resource metrics."""

    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    network_io: Dict[str, int]
    load_average: List[float]
    timestamp: datetime


@dataclass
class TokenMetrics:
    """Token usage and cost metrics."""

    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    sessions_count: int
    avg_tokens_per_session: float
    cost_by_model: Dict[str, float]
    tokens_by_model: Dict[str, Dict[str, int]]
    timestamp: datetime


@dataclass
class ProcessMetrics:
    """Process monitoring metrics."""

    claude_processes: List[Dict[str, Any]]
    total_processes: int
    cpu_usage_by_process: Dict[str, float]
    memory_usage_by_process: Dict[str, int]
    timestamp: datetime


@dataclass
class DockerMetrics:
    """Docker container metrics."""

    containers: List[Dict[str, Any]]
    total_containers: int
    running_containers: int
    claude_containers: int
    total_cpu_percent: float
    total_memory_bytes: int
    network_io: Dict[str, int]
    timestamp: datetime


@dataclass
class LogMetrics:
    """Log analysis metrics."""

    error_count: int
    warning_count: int
    error_rate: float
    common_errors: Dict[str, int]
    performance_issues: List[Dict[str, Any]]
    log_files_processed: int
    timestamp: datetime


@dataclass
class ProjectMetrics:
    """Project-specific resource usage."""

    project_name: str
    resource_usage: Dict[str, Any]
    token_usage: TokenMetrics
    active_sessions: int
    error_rate: float
    timestamp: datetime


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        self.max_size = max_size
        self.cache = {}
        self.access_order = deque()
        self.lock = RLock()

    def get(self, key: str, ttl: int = CACHE_TTL) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None

            value, timestamp = self.cache[key]
            if time.time() - timestamp > ttl:
                del self.cache[key]
                self.access_order.remove(key)
                return None

            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return value

    def set(self, key: str, value: Any):
        with self.lock:
            if key in self.cache:
                self.access_order.remove(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used
                lru_key = self.access_order.popleft()
                del self.cache[lru_key]

            self.cache[key] = (value, time.time())
            self.access_order.append(key)

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.access_order.clear()


class DatabaseCollector:
    """Collects data from SQLite database."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.cache = LRUCache()

    def _get_connection(self) -> sqlite3.Connection:
        """Create database connection with error handling."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_token_metrics(self, hours_back: int = 24) -> TokenMetrics:
        """Get comprehensive token usage metrics."""
        cache_key = f"token_metrics_{hours_back}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get total token usage
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as sessions_count,
                        COALESCE(SUM(
                            CASE
                                WHEN json_extract(raw_json, '$.input_tokens') IS NOT NULL
                                THEN CAST(json_extract(raw_json, '$.input_tokens') AS INTEGER)
                                ELSE 0
                            END
                        ), 0) as total_input_tokens,
                        COALESCE(SUM(
                            CASE
                                WHEN json_extract(raw_json, '$.output_tokens') IS NOT NULL
                                THEN CAST(json_extract(raw_json, '$.output_tokens') AS INTEGER)
                                ELSE 0
                            END
                        ), 0) as total_output_tokens
                    FROM nodes
                    WHERE raw_json IS NOT NULL
                        AND datetime(timestamp) >= datetime('now', '-{} hours')
                """.format(
                        hours_back
                    )
                )

                result = cursor.fetchone()

                # Get model-specific usage
                cursor.execute(
                    """
                    SELECT
                        COALESCE(json_extract(raw_json, '$.model'), 'unknown') as model,
                        COUNT(*) as usage_count,
                        COALESCE(SUM(
                            CASE
                                WHEN json_extract(raw_json, '$.input_tokens') IS NOT NULL
                                THEN CAST(json_extract(raw_json, '$.input_tokens') AS INTEGER)
                                ELSE 0
                            END
                        ), 0) as input_tokens,
                        COALESCE(SUM(
                            CASE
                                WHEN json_extract(raw_json, '$.output_tokens') IS NOT NULL
                                THEN CAST(json_extract(raw_json, '$.output_tokens') AS INTEGER)
                                ELSE 0
                            END
                        ), 0) as output_tokens
                    FROM nodes
                    WHERE raw_json IS NOT NULL
                        AND datetime(timestamp) >= datetime('now', '-{} hours')
                    GROUP BY json_extract(raw_json, '$.model')
                """.format(
                        hours_back
                    )
                )

                model_results = cursor.fetchall()

                if result and result["sessions_count"] > 0:
                    total_input = result["total_input_tokens"] or 0
                    total_output = result["total_output_tokens"] or 0
                    total_tokens = total_input + total_output
                    sessions = result["sessions_count"]

                    # Calculate costs by model
                    cost_by_model = {}
                    tokens_by_model = {}
                    total_cost = 0.0

                    for model_result in model_results:
                        model = model_result["model"]
                        input_tokens = model_result["input_tokens"]
                        output_tokens = model_result["output_tokens"]

                        tokens_by_model[model] = {
                            "input": input_tokens,
                            "output": output_tokens,
                            "total": input_tokens + output_tokens,
                        }

                        # Get pricing for model
                        pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
                        model_cost = (input_tokens * pricing["input"] / 1000) + (
                            output_tokens * pricing["output"] / 1000
                        )
                        cost_by_model[model] = round(model_cost, 4)
                        total_cost += model_cost

                    avg_tokens = total_tokens / sessions if sessions > 0 else 0

                    metrics = TokenMetrics(
                        total_input_tokens=total_input,
                        total_output_tokens=total_output,
                        total_tokens=total_tokens,
                        total_cost=round(total_cost, 4),
                        sessions_count=sessions,
                        avg_tokens_per_session=round(avg_tokens, 2),
                        cost_by_model=cost_by_model,
                        tokens_by_model=tokens_by_model,
                        timestamp=datetime.now(),
                    )

                    self.cache.set(cache_key, metrics)
                    return metrics

        except Exception as e:
            logger.error(f"Error getting token metrics: {e}")

        # Return default metrics on error
        return TokenMetrics(
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            total_cost=0.0,
            sessions_count=0,
            avg_tokens_per_session=0.0,
            cost_by_model={},
            tokens_by_model={},
            timestamp=datetime.now(),
        )

    def get_session_metrics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get session activity metrics."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Active sessions
                cursor.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM sessions
                    WHERE datetime(created_at) >= datetime('now', '-1 hour')
                """
                )
                active_sessions = cursor.fetchone()["count"]

                # Total sessions in timeframe
                cursor.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM sessions
                    WHERE datetime(created_at) >= datetime('now', '-{} hours')
                """.format(
                        hours_back
                    )
                )
                total_sessions = cursor.fetchone()["count"]

                # Tool calls
                cursor.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM tool_calls
                    WHERE datetime(timestamp) >= datetime('now', '-{} hours')
                """.format(
                        hours_back
                    )
                )
                tool_calls = cursor.fetchone()["count"]

                return {
                    "active_sessions": active_sessions,
                    "total_sessions": total_sessions,
                    "recent_tool_calls": tool_calls,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting session metrics: {e}")
            return {
                "active_sessions": 0,
                "total_sessions": 0,
                "recent_tool_calls": 0,
                "timestamp": datetime.now().isoformat(),
            }


class SystemCollector:
    """Collects system resource metrics."""

    def __init__(self):
        self.cache = LRUCache()
        self._prev_network_io = None

    def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system metrics."""
        cache_key = "system_metrics"
        cached = self.cache.get(cache_key, ttl=5)  # Short TTL for system metrics
        if cached:
            return cached

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            # Network I/O
            network_io = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
                "errin": network_io.errin,
                "errout": network_io.errout,
                "dropin": network_io.dropin,
                "dropout": network_io.dropout,
            }

            # Load average
            load_avg = (
                list(psutil.getloadavg())
                if hasattr(psutil, "getloadavg")
                else [0.0, 0.0, 0.0]
            )

            metrics = SystemMetrics(
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory.percent, 2),
                memory_used=memory.used,
                memory_total=memory.total,
                disk_percent=round(disk.percent, 2),
                disk_used=disk.used,
                disk_total=disk.total,
                network_io=network_stats,
                load_average=load_avg,
                timestamp=datetime.now(),
            )

            self.cache.set(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            raise


class ProcessCollector:
    """Collects process monitoring data."""

    def __init__(self):
        self.cache = LRUCache()

    def get_claude_processes(self) -> ProcessMetrics:
        """Get Claude-related processes."""
        cache_key = "claude_processes"
        cached = self.cache.get(cache_key, ttl=10)
        if cached:
            return cached

        try:
            claude_processes = []
            cpu_usage_by_process = {}
            memory_usage_by_process = {}

            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_info", "create_time"]
            ):
                try:
                    info = proc.info
                    cmdline = " ".join(info["cmdline"] or [])

                    # Check if process is Claude-related
                    if any(
                        keyword in cmdline.lower() or keyword in info["name"].lower()
                        for keyword in ["claude", "anthropic", "llm", "ai-chat"]
                    ):
                        process_info = {
                            "pid": info["pid"],
                            "name": info["name"],
                            "cmdline": cmdline,
                            "cpu_percent": proc.cpu_percent(),
                            "memory_rss": info["memory_info"].rss,
                            "memory_vms": info["memory_info"].vms,
                            "create_time": datetime.fromtimestamp(
                                info["create_time"]
                            ).isoformat(),
                            "status": proc.status(),
                            "username": proc.username()
                            if hasattr(proc, "username")
                            else "unknown",
                        }

                        claude_processes.append(process_info)
                        cpu_usage_by_process[str(info["pid"])] = process_info[
                            "cpu_percent"
                        ]
                        memory_usage_by_process[str(info["pid"])] = process_info[
                            "memory_rss"
                        ]

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            metrics = ProcessMetrics(
                claude_processes=claude_processes,
                total_processes=len(claude_processes),
                cpu_usage_by_process=cpu_usage_by_process,
                memory_usage_by_process=memory_usage_by_process,
                timestamp=datetime.now(),
            )

            self.cache.set(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error getting Claude processes: {e}")
            return ProcessMetrics(
                claude_processes=[],
                total_processes=0,
                cpu_usage_by_process={},
                memory_usage_by_process={},
                timestamp=datetime.now(),
            )


class DockerCollector:
    """Collects Docker container metrics."""

    def __init__(self):
        self.cache = LRUCache()
        self.client = None
        self._connect_docker()

    def _connect_docker(self):
        """Connect to Docker daemon."""
        try:
            self.client = docker.from_env()
            self.client.ping()
        except Exception as e:
            logger.warning(f"Could not connect to Docker: {e}")
            self.client = None

    def get_docker_metrics(self) -> DockerMetrics:
        """Get Docker container metrics."""
        cache_key = "docker_metrics"
        cached = self.cache.get(cache_key, ttl=15)
        if cached:
            return cached

        if not self.client:
            return DockerMetrics(
                containers=[],
                total_containers=0,
                running_containers=0,
                claude_containers=0,
                total_cpu_percent=0.0,
                total_memory_bytes=0,
                network_io={"rx_bytes": 0, "tx_bytes": 0},
                timestamp=datetime.now(),
            )

        try:
            containers = []
            running_containers = 0
            claude_containers = 0
            total_cpu_percent = 0.0
            total_memory_bytes = 0
            total_rx_bytes = 0
            total_tx_bytes = 0

            for container in self.client.containers.list(all=True):
                try:
                    container_info = {
                        "id": container.id[:12],
                        "name": container.name,
                        "status": container.status,
                        "image": str(container.image.tags[0])
                        if container.image.tags
                        else container.image.id[:12],
                        "created": container.attrs["Created"],
                    }

                    # Check if Claude-related
                    is_claude_related = any(
                        keyword in container.name.lower()
                        or keyword in str(container.image).lower()
                        for keyword in ["claude", "ai", "llm", "anthropic"]
                    )

                    if is_claude_related:
                        claude_containers += 1

                    if container.status == "running":
                        running_containers += 1

                        # Get stats for running containers
                        try:
                            stats = container.stats(stream=False)

                            # CPU usage
                            cpu_delta = (
                                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                            )
                            system_delta = (
                                stats["cpu_stats"]["system_cpu_usage"]
                                - stats["precpu_stats"]["system_cpu_usage"]
                            )
                            cpu_percent = 0.0
                            if system_delta > 0:
                                cpu_percent = (
                                    (cpu_delta / system_delta)
                                    * len(
                                        stats["cpu_stats"]["cpu_usage"]["percpu_usage"]
                                    )
                                    * 100.0
                                )

                            # Memory usage
                            memory_usage = stats["memory_stats"]["usage"]
                            memory_limit = stats["memory_stats"]["limit"]

                            # Network I/O
                            rx_bytes = 0
                            tx_bytes = 0
                            if "networks" in stats:
                                for interface in stats["networks"].values():
                                    rx_bytes += interface.get("rx_bytes", 0)
                                    tx_bytes += interface.get("tx_bytes", 0)

                            container_info.update(
                                {
                                    "cpu_percent": round(cpu_percent, 2),
                                    "memory_usage": memory_usage,
                                    "memory_limit": memory_limit,
                                    "memory_percent": round(
                                        (memory_usage / memory_limit * 100)
                                        if memory_limit > 0
                                        else 0,
                                        2,
                                    ),
                                    "network_rx_bytes": rx_bytes,
                                    "network_tx_bytes": tx_bytes,
                                    "is_claude_related": is_claude_related,
                                }
                            )

                            total_cpu_percent += cpu_percent
                            total_memory_bytes += memory_usage
                            total_rx_bytes += rx_bytes
                            total_tx_bytes += tx_bytes

                        except Exception as e:
                            logger.warning(
                                f"Could not get stats for container {container.name}: {e}"
                            )

                    containers.append(container_info)

                except Exception as e:
                    logger.warning(f"Error processing container: {e}")
                    continue

            metrics = DockerMetrics(
                containers=containers,
                total_containers=len(containers),
                running_containers=running_containers,
                claude_containers=claude_containers,
                total_cpu_percent=round(total_cpu_percent, 2),
                total_memory_bytes=total_memory_bytes,
                network_io={"rx_bytes": total_rx_bytes, "tx_bytes": total_tx_bytes},
                timestamp=datetime.now(),
            )

            self.cache.set(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error getting Docker metrics: {e}")
            return DockerMetrics(
                containers=[],
                total_containers=0,
                running_containers=0,
                claude_containers=0,
                total_cpu_percent=0.0,
                total_memory_bytes=0,
                network_io={"rx_bytes": 0, "tx_bytes": 0},
                timestamp=datetime.now(),
            )


class LogCollector:
    """Collects and analyzes log files."""

    def __init__(self, log_directories: List[str] = None):
        self.log_directories = log_directories or [
            "/var/log",
            "/home/opsvi/master_root/.audit_logs",
            "/tmp",
            os.path.expanduser("~/.cache/claude"),
            os.path.expanduser("~/.local/share/claude"),
        ]
        self.cache = LRUCache()

    def get_log_metrics(self, hours_back: int = 24) -> LogMetrics:
        """Analyze log files for errors and patterns."""
        cache_key = f"log_metrics_{hours_back}"
        cached = self.cache.get(cache_key, ttl=300)  # 5 minute cache
        if cached:
            return cached

        try:
            error_count = 0
            warning_count = 0
            common_errors = defaultdict(int)
            performance_issues = []
            log_files_processed = 0

            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            for log_dir in self.log_directories:
                if not os.path.exists(log_dir):
                    continue

                try:
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            if not file.endswith((".log", ".jsonl", ".txt")):
                                continue

                            file_path = os.path.join(root, file)

                            try:
                                # Check file modification time
                                if (
                                    datetime.fromtimestamp(os.path.getmtime(file_path))
                                    < cutoff_time
                                ):
                                    continue

                                # Analyze file
                                (
                                    file_errors,
                                    file_warnings,
                                    file_performance,
                                ) = self._analyze_log_file(file_path)
                                error_count += file_errors
                                warning_count += file_warnings
                                performance_issues.extend(file_performance)
                                log_files_processed += 1

                                # Extract common error patterns
                                self._extract_error_patterns(file_path, common_errors)

                            except (PermissionError, OSError) as e:
                                logger.debug(
                                    f"Could not read log file {file_path}: {e}"
                                )
                                continue

                except (PermissionError, OSError):
                    continue

            # Calculate error rate
            total_log_entries = error_count + warning_count + 1000  # Rough estimate
            error_rate = (
                (error_count / total_log_entries) * 100 if total_log_entries > 0 else 0
            )

            # Convert common_errors to regular dict and get top 10
            common_errors_dict = dict(
                sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:10]
            )

            metrics = LogMetrics(
                error_count=error_count,
                warning_count=warning_count,
                error_rate=round(error_rate, 2),
                common_errors=common_errors_dict,
                performance_issues=performance_issues[-20:],  # Keep last 20
                log_files_processed=log_files_processed,
                timestamp=datetime.now(),
            )

            self.cache.set(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return LogMetrics(
                error_count=0,
                warning_count=0,
                error_rate=0.0,
                common_errors={},
                performance_issues=[],
                log_files_processed=0,
                timestamp=datetime.now(),
            )

    def _analyze_log_file(self, file_path: str) -> Tuple[int, int, List[Dict]]:
        """Analyze a single log file."""
        error_count = 0
        warning_count = 0
        performance_issues = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip().lower()

                    # Count errors and warnings
                    if re.search(LOG_PATTERNS["error"], line, re.IGNORECASE):
                        error_count += 1
                    elif re.search(LOG_PATTERNS["warning"], line, re.IGNORECASE):
                        warning_count += 1

                    # Look for performance issues
                    if re.search(LOG_PATTERNS["performance"], line, re.IGNORECASE):
                        performance_issues.append(
                            {
                                "file": file_path,
                                "line_number": line_num,
                                "content": line[:200],  # Truncate long lines
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

        except Exception as e:
            logger.debug(f"Error reading {file_path}: {e}")

        return error_count, warning_count, performance_issues

    def _extract_error_patterns(self, file_path: str, common_errors: defaultdict):
        """Extract common error patterns from log file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if re.search(LOG_PATTERNS["error"], line, re.IGNORECASE):
                        # Extract error pattern (simplified)
                        error_match = re.search(
                            r"(error|exception|failed):\s*([^.\n]{0,50})",
                            line,
                            re.IGNORECASE,
                        )
                        if error_match:
                            error_pattern = error_match.group(2).strip()
                            if error_pattern:
                                common_errors[error_pattern] += 1
        except Exception:
            pass


class DataCollector:
    """Main data collection orchestrator."""

    def __init__(
        self, db_path: str = DEFAULT_DB_PATH, log_directories: List[str] = None
    ):
        self.db_collector = DatabaseCollector(db_path)
        self.system_collector = SystemCollector()
        self.process_collector = ProcessCollector()
        self.docker_collector = DockerCollector()
        self.log_collector = LogCollector(log_directories)

        self.cache = LRUCache()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = Lock()

    async def collect_all_metrics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Collect metrics from all sources asynchronously."""
        cache_key = f"all_metrics_{hours_back}"
        cached = self.cache.get(cache_key, ttl=30)
        if cached:
            return cached

        try:
            # Collect all metrics concurrently
            loop = asyncio.get_event_loop()

            tasks = [
                loop.run_in_executor(
                    self.executor, self.db_collector.get_token_metrics, hours_back
                ),
                loop.run_in_executor(
                    self.executor, self.db_collector.get_session_metrics, hours_back
                ),
                loop.run_in_executor(
                    self.executor, self.system_collector.get_system_metrics
                ),
                loop.run_in_executor(
                    self.executor, self.process_collector.get_claude_processes
                ),
                loop.run_in_executor(
                    self.executor, self.docker_collector.get_docker_metrics
                ),
                loop.run_in_executor(
                    self.executor, self.log_collector.get_log_metrics, hours_back
                ),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            (
                token_metrics,
                session_metrics,
                system_metrics,
                process_metrics,
                docker_metrics,
                log_metrics,
            ) = results

            # Handle any exceptions
            if isinstance(token_metrics, Exception):
                logger.error(f"Token metrics error: {token_metrics}")
                token_metrics = TokenMetrics(
                    0, 0, 0, 0.0, 0, 0.0, {}, {}, datetime.now()
                )

            if isinstance(session_metrics, Exception):
                logger.error(f"Session metrics error: {session_metrics}")
                session_metrics = {
                    "active_sessions": 0,
                    "total_sessions": 0,
                    "recent_tool_calls": 0,
                }

            if isinstance(system_metrics, Exception):
                logger.error(f"System metrics error: {system_metrics}")
                system_metrics = SystemMetrics(
                    0, 0, 0, 0, 0, 0, 0, {}, [0, 0, 0], datetime.now()
                )

            if isinstance(process_metrics, Exception):
                logger.error(f"Process metrics error: {process_metrics}")
                process_metrics = ProcessMetrics([], 0, {}, {}, datetime.now())

            if isinstance(docker_metrics, Exception):
                logger.error(f"Docker metrics error: {docker_metrics}")
                docker_metrics = DockerMetrics(
                    [], 0, 0, 0, 0.0, 0, {"rx_bytes": 0, "tx_bytes": 0}, datetime.now()
                )

            if isinstance(log_metrics, Exception):
                logger.error(f"Log metrics error: {log_metrics}")
                log_metrics = LogMetrics(0, 0, 0.0, {}, [], 0, datetime.now())

            # Aggregate all data
            aggregated_data = {
                "summary": {
                    "total_cost": token_metrics.total_cost,
                    "total_tokens": token_metrics.total_tokens,
                    "active_sessions": session_metrics["active_sessions"],
                    "error_rate": log_metrics.error_rate,
                    "system_cpu_percent": system_metrics.cpu_percent,
                    "system_memory_percent": system_metrics.memory_percent,
                    "claude_processes": process_metrics.total_processes,
                    "claude_containers": docker_metrics.claude_containers,
                    "timestamp": datetime.now().isoformat(),
                },
                "token_usage": asdict(token_metrics),
                "system_resources": asdict(system_metrics),
                "process_monitoring": asdict(process_metrics),
                "docker_containers": asdict(docker_metrics),
                "log_analysis": asdict(log_metrics),
                "session_activity": session_metrics,
                "collection_info": {
                    "hours_back": hours_back,
                    "cache_hit": False,
                    "collection_time": datetime.now().isoformat(),
                },
            }

            self.cache.set(cache_key, aggregated_data)
            return aggregated_data

        except Exception as e:
            logger.error(f"Error collecting all metrics: {e}")
            raise

    def get_project_metrics(self, project_name: str = "default") -> ProjectMetrics:
        """Get project-specific resource usage metrics."""
        try:
            # This would ideally be enhanced to track per-project usage
            # For now, we'll provide aggregated metrics with project context
            token_metrics = self.db_collector.get_token_metrics()
            session_metrics = self.db_collector.get_session_metrics()
            log_metrics = self.log_collector.get_log_metrics()

            # Calculate project-specific resource usage
            resource_usage = {
                "cpu_usage": 0.0,  # Would track per-project CPU
                "memory_usage": 0,  # Would track per-project memory
                "disk_usage": 0,  # Would track per-project disk
                "network_usage": 0,  # Would track per-project network
            }

            return ProjectMetrics(
                project_name=project_name,
                resource_usage=resource_usage,
                token_usage=token_metrics,
                active_sessions=session_metrics["active_sessions"],
                error_rate=log_metrics.error_rate,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error getting project metrics: {e}")
            return ProjectMetrics(
                project_name=project_name,
                resource_usage={},
                token_usage=TokenMetrics(0, 0, 0, 0.0, 0, 0.0, {}, {}, datetime.now()),
                active_sessions=0,
                error_rate=0.0,
                timestamp=datetime.now(),
            )

    def clear_cache(self):
        """Clear all caches."""
        self.cache.clear()
        self.db_collector.cache.clear()
        self.system_collector.cache.clear()
        self.process_collector.cache.clear()
        self.docker_collector.cache.clear()
        self.log_collector.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "main_cache_size": len(self.cache.cache),
            "db_cache_size": len(self.db_collector.cache.cache),
            "system_cache_size": len(self.system_collector.cache.cache),
            "process_cache_size": len(self.process_collector.cache.cache),
            "docker_cache_size": len(self.docker_collector.cache.cache),
            "log_cache_size": len(self.log_collector.cache.cache),
        }


# Convenience function for external use
async def collect_comprehensive_data(
    db_path: str = DEFAULT_DB_PATH,
    log_directories: List[str] = None,
    hours_back: int = 24,
) -> Dict[str, Any]:
    """Collect comprehensive data from all sources."""
    collector = DataCollector(db_path, log_directories)
    return await collector.collect_all_metrics(hours_back)


# Example usage
async def main():
    """Example usage of the data collector."""
    collector = DataCollector()

    try:
        print("Collecting comprehensive metrics...")
        data = await collector.collect_all_metrics(hours_back=24)

        print("\n=== SUMMARY ===")
        summary = data["summary"]
        print(f"Total Cost: ${summary['total_cost']}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Active Sessions: {summary['active_sessions']}")
        print(f"Error Rate: {summary['error_rate']:.2f}%")
        print(f"CPU Usage: {summary['system_cpu_percent']:.1f}%")
        print(f"Memory Usage: {summary['system_memory_percent']:.1f}%")
        print(f"Claude Processes: {summary['claude_processes']}")
        print(f"Claude Containers: {summary['claude_containers']}")

        print("\n=== TOKEN USAGE BY MODEL ===")
        for model, metrics in data["token_usage"]["cost_by_model"].items():
            tokens = data["token_usage"]["tokens_by_model"].get(model, {})
            print(f"{model}: ${metrics:.4f} ({tokens.get('total', 0):,} tokens)")

        print("\n=== LOG ANALYSIS ===")
        log_data = data["log_analysis"]
        print(f"Errors: {log_data['error_count']}")
        print(f"Warnings: {log_data['warning_count']}")
        print(f"Files Processed: {log_data['log_files_processed']}")

        print("\n=== CACHE STATS ===")
        cache_stats = collector.get_cache_stats()
        for cache_name, size in cache_stats.items():
            print(f"{cache_name}: {size} items")

        # Example project metrics
        project_metrics = collector.get_project_metrics("claude-monitor")
        print(f"\n=== PROJECT METRICS (claude-monitor) ===")
        print(f"Active Sessions: {project_metrics.active_sessions}")
        print(f"Error Rate: {project_metrics.error_rate:.2f}%")
        print(f"Total Cost: ${project_metrics.token_usage.total_cost:.4f}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        collector.executor.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
