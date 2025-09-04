#!/usr/bin/env python3
"""
Advanced Log Aggregation System for Unified Context System

Centralized log collection and analysis for:
- PostgreSQL query logs and error logs
- Neo4j query logs and system logs
- Docker container logs
- Application logs from all services
- System logs and kernel messages
- Real-time log streaming and analysis
- Log-based alerting and pattern detection
"""

import asyncio
import json
import logging
import re
import sqlite3
import subprocess
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import aiofiles
import docker
import psycopg2
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    timestamp: str
    source: str  # postgres, neo4j, docker, application, system
    level: str  # debug, info, warning, error, critical
    component: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    parsed_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogPattern:
    name: str
    source: str
    regex: str
    severity: str
    description: str
    alert_threshold: int = 1  # Alert after N occurrences
    time_window_minutes: int = 5
    enabled: bool = True


@dataclass
class LogAnalysis:
    period_start: str
    period_end: str
    total_entries: int
    entries_by_level: Dict[str, int]
    entries_by_source: Dict[str, int]
    error_patterns: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]


class LogAggregator:
    """Advanced log aggregation with pattern detection and analysis."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_storage = deque(maxlen=50000)  # Keep last 50k log entries in memory
        self.log_patterns = self._initialize_log_patterns()
        self.pattern_matches = defaultdict(deque)  # Pattern -> timestamps
        self.log_sources = {}
        self.running = False
        self.tasks = []

        # Database for persistent log storage
        self.db_path = config.get(
            "database_path", "/home/opsvi/master_root/logs/log_aggregator.db"
        )
        self._init_database()

        # Log parsing statistics
        self.parse_stats = defaultdict(int)

    def _init_database(self):
        """Initialize SQLite database for log storage."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create logs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                tags TEXT,
                parsed_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON logs(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON logs(level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_component ON logs(component)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON logs(created_at)")

        # Create pattern matches table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pattern_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                log_id INTEGER,
                matched_text TEXT,
                severity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(log_id) REFERENCES logs(id)
            )
        """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pattern_timestamp ON pattern_matches(pattern_name, timestamp)"
        )

        conn.commit()
        conn.close()

        logger.info(f"Log aggregator database initialized at {self.db_path}")

    def _initialize_log_patterns(self) -> Dict[str, LogPattern]:
        """Initialize log patterns for detection and alerting."""
        patterns = {}

        # PostgreSQL patterns
        patterns["postgres_connection_error"] = LogPattern(
            name="postgres_connection_error",
            source="postgres",
            regex=r"FATAL:.*could not connect|connection refused|authentication failed",
            severity="critical",
            description="PostgreSQL connection failures",
            alert_threshold=1,
            time_window_minutes=1,
        )

        patterns["postgres_slow_query"] = LogPattern(
            name="postgres_slow_query",
            source="postgres",
            regex=r"LOG:.*duration: (\d+\.\d+) ms.*statement:",
            severity="warning",
            description="Slow PostgreSQL queries",
            alert_threshold=5,
            time_window_minutes=5,
        )

        patterns["postgres_deadlock"] = LogPattern(
            name="postgres_deadlock",
            source="postgres",
            regex=r"ERROR:.*deadlock detected",
            severity="critical",
            description="PostgreSQL deadlock detected",
            alert_threshold=1,
            time_window_minutes=5,
        )

        # Neo4j patterns
        patterns["neo4j_memory_error"] = LogPattern(
            name="neo4j_memory_error",
            source="neo4j",
            regex=r"OutOfMemoryError|GC overhead limit exceeded",
            severity="critical",
            description="Neo4j memory issues",
            alert_threshold=1,
            time_window_minutes=1,
        )

        patterns["neo4j_slow_query"] = LogPattern(
            name="neo4j_slow_query",
            source="neo4j",
            regex=r"Query took longer than \d+ seconds",
            severity="warning",
            description="Slow Neo4j queries",
            alert_threshold=3,
            time_window_minutes=5,
        )

        # System patterns
        patterns["disk_space_low"] = LogPattern(
            name="disk_space_low",
            source="system",
            regex=r"disk space low|No space left on device|filesystem.*full",
            severity="critical",
            description="Low disk space warnings",
            alert_threshold=1,
            time_window_minutes=5,
        )

        patterns["oom_killer"] = LogPattern(
            name="oom_killer",
            source="system",
            regex=r"Out of memory: Kill process|oom-kill|Killed process",
            severity="critical",
            description="Out of memory killer activated",
            alert_threshold=1,
            time_window_minutes=1,
        )

        # Docker patterns
        patterns["container_restart"] = LogPattern(
            name="container_restart",
            source="docker",
            regex=r"container.*restarted|container.*died",
            severity="warning",
            description="Docker container restarts",
            alert_threshold=2,
            time_window_minutes=10,
        )

        patterns["docker_error"] = LogPattern(
            name="docker_error",
            source="docker",
            regex=r"Error response from daemon|docker.*error",
            severity="error",
            description="Docker daemon errors",
            alert_threshold=3,
            time_window_minutes=5,
        )

        # Application patterns
        patterns["application_exception"] = LogPattern(
            name="application_exception",
            source="application",
            regex=r"Exception|Traceback|Error:|CRITICAL:|FATAL:",
            severity="error",
            description="Application exceptions and errors",
            alert_threshold=5,
            time_window_minutes=5,
        )

        return patterns

    async def start(self):
        """Start log aggregation services."""
        self.running = True

        # Initialize log sources
        await self._initialize_log_sources()

        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._postgres_log_collector()),
            asyncio.create_task(self._neo4j_log_collector()),
            asyncio.create_task(self._docker_log_collector()),
            asyncio.create_task(self._system_log_collector()),
            asyncio.create_task(self._application_log_collector()),
            asyncio.create_task(self._log_processor()),
            asyncio.create_task(self._pattern_detector()),
            asyncio.create_task(self._log_archiver()),
        ]

        logger.info("Log aggregator started")

    async def stop(self):
        """Stop log aggregation services."""
        self.running = False

        # Cancel all background tasks
        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Log aggregator stopped")

    async def _initialize_log_sources(self):
        """Initialize connections to various log sources."""
        # PostgreSQL connection for accessing logs
        try:
            postgres_config = self.config.get("postgres", {})
            if postgres_config:
                self.log_sources["postgres"] = psycopg2.connect(**postgres_config)
                self.log_sources["postgres"].autocommit = True
        except Exception as e:
            logger.warning(f"Failed to connect to PostgreSQL for log access: {e}")

        # Neo4j connection
        try:
            neo4j_config = self.config.get("neo4j", {})
            if neo4j_config:
                self.log_sources["neo4j"] = GraphDatabase.driver(
                    neo4j_config["uri"],
                    auth=(neo4j_config["user"], neo4j_config["password"]),
                )
        except Exception as e:
            logger.warning(f"Failed to connect to Neo4j for log access: {e}")

        # Docker client
        try:
            self.log_sources["docker"] = docker.from_env()
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {e}")

    async def _postgres_log_collector(self):
        """Collect PostgreSQL logs."""
        while self.running:
            try:
                if "postgres" not in self.log_sources:
                    await asyncio.sleep(60)
                    continue

                conn = self.log_sources["postgres"]
                cursor = conn.cursor()

                # Check PostgreSQL log settings
                try:
                    cursor.execute("SHOW log_destination")
                    log_destination = cursor.fetchone()[0]

                    cursor.execute("SHOW log_directory")
                    log_directory = cursor.fetchone()[0]

                    # If logging to file, try to read recent entries
                    if "stderr" in log_destination or "csvlog" in log_destination:
                        await self._collect_postgres_file_logs(log_directory)

                except Exception as e:
                    logger.debug(f"Could not access PostgreSQL log files: {e}")

                # Query pg_stat_statements for slow queries
                try:
                    cursor.execute(
                        """
                        SELECT query, calls, total_exec_time, mean_exec_time, max_exec_time
                        FROM pg_stat_statements
                        WHERE mean_exec_time > 100  -- Queries slower than 100ms
                        ORDER BY mean_exec_time DESC
                        LIMIT 10
                    """
                    )

                    slow_queries = cursor.fetchall()
                    for query_data in slow_queries:
                        log_entry = LogEntry(
                            timestamp=datetime.now().isoformat(),
                            source="postgres",
                            level="warning",
                            component="query_performance",
                            message=f"Slow query detected: {query_data[3]:.2f}ms average",
                            metadata={
                                "query": query_data[0][:200] + "..."
                                if len(query_data[0]) > 200
                                else query_data[0],
                                "calls": query_data[1],
                                "total_time": query_data[2],
                                "mean_time": query_data[3],
                                "max_time": query_data[4],
                            },
                            tags=["performance", "slow_query"],
                        )
                        await self._add_log_entry(log_entry)

                except Exception as e:
                    logger.debug(f"Could not query pg_stat_statements: {e}")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in PostgreSQL log collector: {e}")
                await asyncio.sleep(300)

    async def _collect_postgres_file_logs(self, log_directory: str):
        """Collect PostgreSQL logs from file system."""
        try:
            # Look for PostgreSQL log files
            log_paths = [
                "/var/log/postgresql/",
                f"/var/lib/postgresql/data/{log_directory}",
                "/home/opsvi/master_root/logs/postgres/",
            ]

            for log_path in log_paths:
                log_dir = Path(log_path)
                if log_dir.exists():
                    # Find recent log files
                    log_files = sorted(
                        log_dir.glob("postgresql-*.log"),
                        key=lambda f: f.stat().st_mtime,
                        reverse=True,
                    )

                    if log_files:
                        await self._tail_log_file(log_files[0], "postgres")
                    break

        except Exception as e:
            logger.debug(f"Error collecting PostgreSQL file logs: {e}")

    async def _neo4j_log_collector(self):
        """Collect Neo4j logs."""
        while self.running:
            try:
                # Collect Neo4j logs from file system
                neo4j_log_paths = [
                    "/var/log/neo4j/",
                    "/home/opsvi/master_root/logs/neo4j/",
                    "/opt/neo4j/logs/",
                ]

                for log_path in neo4j_log_paths:
                    log_dir = Path(log_path)
                    if log_dir.exists():
                        # Look for various Neo4j log files
                        for log_file in ["neo4j.log", "debug.log", "query.log"]:
                            log_file_path = log_dir / log_file
                            if log_file_path.exists():
                                await self._tail_log_file(log_file_path, "neo4j")
                        break

                # Query Neo4j for slow queries if available
                if "neo4j" in self.log_sources:
                    try:
                        with self.log_sources["neo4j"].session() as session:
                            # Check for slow queries in logs (if query logging is enabled)
                            result = session.run(
                                """
                                CALL dbms.listQueries()
                                YIELD query, elapsedTimeMillis, status
                                WHERE elapsedTimeMillis > 1000
                                RETURN query, elapsedTimeMillis, status
                                LIMIT 10
                            """
                            )

                            for record in result:
                                log_entry = LogEntry(
                                    timestamp=datetime.now().isoformat(),
                                    source="neo4j",
                                    level="warning",
                                    component="query_performance",
                                    message=f"Slow Neo4j query: {record['elapsedTimeMillis']}ms",
                                    metadata={
                                        "query": record["query"][:200] + "..."
                                        if len(record["query"]) > 200
                                        else record["query"],
                                        "elapsed_time": record["elapsedTimeMillis"],
                                        "status": record["status"],
                                    },
                                    tags=["performance", "slow_query"],
                                )
                                await self._add_log_entry(log_entry)

                    except Exception as e:
                        logger.debug(f"Could not query Neo4j for slow queries: {e}")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in Neo4j log collector: {e}")
                await asyncio.sleep(300)

    async def _docker_log_collector(self):
        """Collect Docker container logs."""
        while self.running:
            try:
                if "docker" not in self.log_sources:
                    await asyncio.sleep(60)
                    continue

                client = self.log_sources["docker"]

                # Get containers related to the context system
                containers = client.containers.list(all=True)
                context_containers = [
                    c
                    for c in containers
                    if any(
                        keyword in c.name.lower()
                        for keyword in [
                            "unified_context",
                            "postgres",
                            "neo4j",
                            "embedding",
                            "claude",
                        ]
                    )
                ]

                for container in context_containers:
                    try:
                        # Get recent logs (last 100 lines)
                        logs = container.logs(tail=100, timestamps=True).decode("utf-8")

                        for line in logs.split("\n"):
                            if line.strip():
                                await self._parse_docker_log_line(line, container.name)

                        # Check container health
                        if container.status != "running":
                            log_entry = LogEntry(
                                timestamp=datetime.now().isoformat(),
                                source="docker",
                                level="warning"
                                if container.status == "exited"
                                else "error",
                                component="container_status",
                                message=f"Container {container.name} status: {container.status}",
                                metadata={
                                    "container_id": container.id[:12],
                                    "container_name": container.name,
                                    "status": container.status,
                                    "image": str(container.image.tags[0])
                                    if container.image.tags
                                    else container.image.id[:12],
                                },
                                tags=["container", "status"],
                            )
                            await self._add_log_entry(log_entry)

                    except Exception as e:
                        logger.debug(
                            f"Error collecting logs from container {container.name}: {e}"
                        )

                await asyncio.sleep(180)  # Check every 3 minutes

            except Exception as e:
                logger.error(f"Error in Docker log collector: {e}")
                await asyncio.sleep(180)

    async def _parse_docker_log_line(self, line: str, container_name: str):
        """Parse a Docker log line."""
        try:
            # Docker log format: TIMESTAMP STREAM MESSAGE
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                timestamp = parts[0]
                stream = parts[1]  # stdout/stderr
                message = parts[2]

                # Determine log level from message content
                level = "info"
                if any(
                    keyword in message.lower()
                    for keyword in ["error", "exception", "failed"]
                ):
                    level = "error"
                elif any(keyword in message.lower() for keyword in ["warn", "warning"]):
                    level = "warning"
                elif any(keyword in message.lower() for keyword in ["debug", "trace"]):
                    level = "debug"

                log_entry = LogEntry(
                    timestamp=timestamp,
                    source="docker",
                    level=level,
                    component=container_name,
                    message=message,
                    metadata={"container": container_name, "stream": stream},
                    tags=["docker", "container"],
                )

                await self._add_log_entry(log_entry)

        except Exception as e:
            logger.debug(f"Error parsing Docker log line: {e}")

    async def _system_log_collector(self):
        """Collect system logs."""
        while self.running:
            try:
                # Collect from various system log sources
                system_log_files = [
                    "/var/log/syslog",
                    "/var/log/messages",
                    "/var/log/kern.log",
                    "/var/log/dmesg",
                ]

                for log_file_path in system_log_files:
                    log_file = Path(log_file_path)
                    if log_file.exists():
                        await self._tail_log_file(log_file, "system")

                # Use journalctl for systemd systems
                try:
                    result = subprocess.run(
                        [
                            "journalctl",
                            "--since",
                            "5 minutes ago",
                            "--no-pager",
                            "-o",
                            "json",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode == 0:
                        for line in result.stdout.split("\n"):
                            if line.strip():
                                try:
                                    journal_entry = json.loads(line)
                                    await self._parse_systemd_journal_entry(
                                        journal_entry
                                    )
                                except json.JSONDecodeError:
                                    continue

                except subprocess.TimeoutExpired:
                    logger.warning("journalctl command timed out")
                except FileNotFoundError:
                    logger.debug("journalctl not available")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in system log collector: {e}")
                await asyncio.sleep(300)

    async def _parse_systemd_journal_entry(self, entry: Dict[str, Any]):
        """Parse systemd journal entry."""
        try:
            timestamp = entry.get(
                "__REALTIME_TIMESTAMP", str(int(time.time() * 1000000))
            )
            # Convert microseconds to ISO format
            timestamp_dt = datetime.fromtimestamp(int(timestamp) / 1000000)

            message = entry.get("MESSAGE", "")
            priority = entry.get("PRIORITY", "6")  # Default to info
            unit = entry.get("_SYSTEMD_UNIT", entry.get("SYSLOG_IDENTIFIER", "system"))

            # Map systemd priority to log level
            level_map = {
                "0": "critical",  # Emergency
                "1": "critical",  # Alert
                "2": "critical",  # Critical
                "3": "error",  # Error
                "4": "warning",  # Warning
                "5": "info",  # Notice
                "6": "info",  # Info
                "7": "debug",  # Debug
            }

            level = level_map.get(str(priority), "info")

            log_entry = LogEntry(
                timestamp=timestamp_dt.isoformat(),
                source="system",
                level=level,
                component=unit,
                message=message,
                metadata={
                    "priority": priority,
                    "pid": entry.get("_PID"),
                    "uid": entry.get("_UID"),
                    "gid": entry.get("_GID"),
                    "comm": entry.get("_COMM"),
                },
                tags=["system", "systemd"],
            )

            await self._add_log_entry(log_entry)

        except Exception as e:
            logger.debug(f"Error parsing systemd journal entry: {e}")

    async def _application_log_collector(self):
        """Collect application-specific logs."""
        while self.running:
            try:
                # Collect logs from application directories
                app_log_paths = [
                    "/home/opsvi/master_root/logs/",
                    "/home/opsvi/master_root/apps/*/logs/",
                    "/var/log/apps/",
                ]

                for log_path_pattern in app_log_paths:
                    log_paths = Path("/").glob(log_path_pattern.lstrip("/"))

                    for log_path in log_paths:
                        if log_path.is_dir():
                            # Look for log files
                            for log_file in log_path.glob("*.log"):
                                await self._tail_log_file(log_file, "application")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in application log collector: {e}")
                await asyncio.sleep(300)

    async def _tail_log_file(self, file_path: Path, source: str):
        """Tail a log file and extract recent entries."""
        try:
            if not file_path.exists():
                return

            # Get file modification time
            mtime = file_path.stat().st_mtime
            current_time = time.time()

            # Only process files modified in the last 10 minutes
            if current_time - mtime > 600:
                return

            # Read last 100 lines
            result = subprocess.run(
                ["tail", "-n", "100", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        await self._parse_log_line(line, source, file_path.name)

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout reading log file: {file_path}")
        except Exception as e:
            logger.debug(f"Error tailing log file {file_path}: {e}")

    async def _parse_log_line(self, line: str, source: str, filename: str):
        """Parse a generic log line."""
        try:
            # Extract timestamp if present
            timestamp_match = re.search(
                r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})", line
            )
            timestamp = (
                timestamp_match.group(1)
                if timestamp_match
                else datetime.now().isoformat()
            )

            # Determine log level
            level = "info"
            level_match = re.search(
                r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b",
                line,
                re.IGNORECASE,
            )
            if level_match:
                level_str = level_match.group(1).lower()
                level_map = {
                    "debug": "debug",
                    "info": "info",
                    "warn": "warning",
                    "warning": "warning",
                    "error": "error",
                    "critical": "critical",
                    "fatal": "critical",
                }
                level = level_map.get(level_str, "info")

            # Extract component (often between brackets or after specific patterns)
            component_match = re.search(r"\[([^\]]+)\]|(\w+):", line)
            component = (
                component_match.group(1) or component_match.group(2)
                if component_match
                else filename
            )

            log_entry = LogEntry(
                timestamp=timestamp,
                source=source,
                level=level,
                component=component,
                message=line,
                metadata={"filename": filename, "raw_line": line},
                tags=[source, "file"],
            )

            await self._add_log_entry(log_entry)

        except Exception as e:
            logger.debug(f"Error parsing log line: {e}")

    async def _add_log_entry(self, log_entry: LogEntry):
        """Add a log entry to storage and trigger processing."""
        try:
            # Add to in-memory storage
            self.log_storage.append(log_entry)

            # Store in database (async)
            asyncio.create_task(self._store_log_entry_db(log_entry))

            # Update parse statistics
            self.parse_stats[f"{log_entry.source}_{log_entry.level}"] += 1

        except Exception as e:
            logger.error(f"Error adding log entry: {e}")

    async def _store_log_entry_db(self, log_entry: LogEntry):
        """Store log entry in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO logs (timestamp, source, level, component, message, metadata, tags, parsed_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    log_entry.timestamp,
                    log_entry.source,
                    log_entry.level,
                    log_entry.component,
                    log_entry.message,
                    json.dumps(log_entry.metadata),
                    json.dumps(log_entry.tags),
                    json.dumps(log_entry.parsed_data),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing log entry in database: {e}")

    async def _log_processor(self):
        """Process logs for enrichment and analysis."""
        while self.running:
            try:
                # Process recent log entries for enrichment
                recent_entries = list(self.log_storage)[-100:]  # Last 100 entries

                for log_entry in recent_entries:
                    if not log_entry.parsed_data:  # Not yet processed
                        await self._enrich_log_entry(log_entry)

                await asyncio.sleep(30)  # Process every 30 seconds

            except Exception as e:
                logger.error(f"Error in log processor: {e}")
                await asyncio.sleep(30)

    async def _enrich_log_entry(self, log_entry: LogEntry):
        """Enrich log entry with additional context."""
        try:
            # Extract structured data from message
            if log_entry.source == "postgres":
                await self._enrich_postgres_log(log_entry)
            elif log_entry.source == "neo4j":
                await self._enrich_neo4j_log(log_entry)
            elif log_entry.source == "docker":
                await self._enrich_docker_log(log_entry)

            # Add performance context
            await self._add_performance_context(log_entry)

            # Mark as processed
            log_entry.parsed_data["processed"] = True
            log_entry.parsed_data["processed_at"] = datetime.now().isoformat()

        except Exception as e:
            logger.debug(f"Error enriching log entry: {e}")

    async def _enrich_postgres_log(self, log_entry: LogEntry):
        """Enrich PostgreSQL log entries."""
        message = log_entry.message

        # Extract query duration
        duration_match = re.search(r"duration: ([\d.]+) ms", message)
        if duration_match:
            log_entry.parsed_data["duration_ms"] = float(duration_match.group(1))
            log_entry.tags.append("timed_query")

        # Extract query type
        query_match = re.search(
            r"statement: (SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)",
            message,
            re.IGNORECASE,
        )
        if query_match:
            log_entry.parsed_data["query_type"] = query_match.group(1).upper()
            log_entry.tags.append(f"query_{query_match.group(1).lower()}")

        # Extract error codes
        error_match = re.search(r"ERROR:\s+([^:]+):", message)
        if error_match:
            log_entry.parsed_data["error_type"] = error_match.group(1).strip()
            log_entry.tags.append("error")

    async def _enrich_neo4j_log(self, log_entry: LogEntry):
        """Enrich Neo4j log entries."""
        message = log_entry.message

        # Extract query execution time
        time_match = re.search(r"(\d+) ms", message)
        if time_match:
            log_entry.parsed_data["execution_time_ms"] = int(time_match.group(1))
            log_entry.tags.append("timed_operation")

        # Extract Cypher queries
        cypher_match = re.search(
            r"(MATCH|CREATE|MERGE|DELETE|RETURN)", message, re.IGNORECASE
        )
        if cypher_match:
            log_entry.parsed_data["cypher_operation"] = cypher_match.group(1).upper()
            log_entry.tags.append("cypher_query")

    async def _enrich_docker_log(self, log_entry: LogEntry):
        """Enrich Docker log entries."""
        message = log_entry.message

        # Extract container events
        if "start" in message.lower():
            log_entry.parsed_data["event_type"] = "container_start"
            log_entry.tags.append("container_event")
        elif "stop" in message.lower():
            log_entry.parsed_data["event_type"] = "container_stop"
            log_entry.tags.append("container_event")
        elif "restart" in message.lower():
            log_entry.parsed_data["event_type"] = "container_restart"
            log_entry.tags.append("container_event")

    async def _add_performance_context(self, log_entry: LogEntry):
        """Add performance context to log entries."""
        # Add system load context for performance-related logs
        if "performance" in log_entry.tags or log_entry.parsed_data.get("duration_ms"):
            try:
                import psutil

                log_entry.parsed_data["system_context"] = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "load_avg": list(psutil.getloadavg())
                    if hasattr(psutil, "getloadavg")
                    else [0, 0, 0],
                }
            except Exception:
                pass

    async def _pattern_detector(self):
        """Detect patterns in log entries and trigger alerts."""
        while self.running:
            try:
                current_time = datetime.now()

                # Check each pattern
                for pattern_name, pattern in self.log_patterns.items():
                    if not pattern.enabled:
                        continue

                    await self._check_pattern_matches(pattern, current_time)

                await asyncio.sleep(60)  # Check patterns every minute

            except Exception as e:
                logger.error(f"Error in pattern detector: {e}")
                await asyncio.sleep(60)

    async def _check_pattern_matches(self, pattern: LogPattern, current_time: datetime):
        """Check for pattern matches in recent logs."""
        try:
            cutoff_time = current_time - timedelta(minutes=pattern.time_window_minutes)

            # Get recent log entries for this source
            recent_entries = [
                entry
                for entry in self.log_storage
                if (
                    entry.source == pattern.source
                    and datetime.fromisoformat(entry.timestamp) > cutoff_time
                )
            ]

            matches = []
            for entry in recent_entries:
                if re.search(pattern.regex, entry.message, re.IGNORECASE):
                    matches.append(entry)

            # Check if we've exceeded the alert threshold
            if len(matches) >= pattern.alert_threshold:
                await self._trigger_pattern_alert(pattern, matches, current_time)

                # Store pattern matches in database
                await self._store_pattern_matches(pattern, matches)

        except Exception as e:
            logger.error(f"Error checking pattern {pattern.name}: {e}")

    async def _trigger_pattern_alert(
        self, pattern: LogPattern, matches: List[LogEntry], timestamp: datetime
    ):
        """Trigger an alert for pattern detection."""
        try:
            alert_message = f"Pattern '{pattern.name}' detected {len(matches)} times in {pattern.time_window_minutes} minutes"

            # Create structured alert data
            alert_data = {
                "pattern_name": pattern.name,
                "description": pattern.description,
                "severity": pattern.severity,
                "match_count": len(matches),
                "time_window_minutes": pattern.time_window_minutes,
                "threshold": pattern.alert_threshold,
                "matches": [
                    {
                        "timestamp": match.timestamp,
                        "component": match.component,
                        "message": match.message[:200] + "..."
                        if len(match.message) > 200
                        else match.message,
                    }
                    for match in matches[-10:]  # Last 10 matches
                ],
                "alert_timestamp": timestamp.isoformat(),
            }

            # Log the alert
            logger.warning(f"LOG PATTERN ALERT: {alert_message}")

            # You can integrate this with the alert manager
            # await self.alert_manager.create_log_based_alert(alert_data)

        except Exception as e:
            logger.error(f"Error triggering pattern alert: {e}")

    async def _store_pattern_matches(
        self, pattern: LogPattern, matches: List[LogEntry]
    ):
        """Store pattern matches in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for match in matches:
                cursor.execute(
                    """
                    INSERT INTO pattern_matches (pattern_name, timestamp, matched_text, severity)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        pattern.name,
                        match.timestamp,
                        match.message[:1000],  # Truncate long messages
                        pattern.severity,
                    ),
                )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing pattern matches: {e}")

    async def _log_archiver(self):
        """Archive old logs to prevent database growth."""
        while self.running:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Archive logs older than 30 days
                cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()

                # Count logs to be archived
                cursor.execute(
                    "SELECT COUNT(*) FROM logs WHERE created_at < ?", (cutoff_date,)
                )
                count = cursor.fetchone()[0]

                if count > 0:
                    # Export to archive file before deletion
                    archive_filename = (
                        f"archived_logs_{datetime.now().strftime('%Y%m%d')}.json"
                    )
                    archive_path = (
                        Path(self.db_path).parent / "archives" / archive_filename
                    )
                    archive_path.parent.mkdir(exist_ok=True)

                    cursor.execute(
                        """
                        SELECT timestamp, source, level, component, message, metadata, tags
                        FROM logs WHERE created_at < ?
                        ORDER BY created_at
                    """,
                        (cutoff_date,),
                    )

                    archived_logs = []
                    for row in cursor.fetchall():
                        archived_logs.append(
                            {
                                "timestamp": row[0],
                                "source": row[1],
                                "level": row[2],
                                "component": row[3],
                                "message": row[4],
                                "metadata": json.loads(row[5]) if row[5] else {},
                                "tags": json.loads(row[6]) if row[6] else [],
                            }
                        )

                    # Write archive file
                    async with aiofiles.open(archive_path, "w") as f:
                        await f.write(json.dumps(archived_logs, indent=2))

                    # Delete archived logs
                    cursor.execute(
                        "DELETE FROM logs WHERE created_at < ?", (cutoff_date,)
                    )
                    cursor.execute(
                        "DELETE FROM pattern_matches WHERE created_at < ?",
                        (cutoff_date,),
                    )

                    conn.commit()
                    logger.info(f"Archived {count} log entries to {archive_path}")

                conn.close()

                # Run archiving once per day
                await asyncio.sleep(86400)

            except Exception as e:
                logger.error(f"Error in log archiver: {e}")
                await asyncio.sleep(86400)

    async def analyze_logs(self, hours: int = 24) -> LogAnalysis:
        """Analyze logs for the specified time period."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get log statistics
            cursor.execute(
                """
                SELECT COUNT(*) as total,
                       level,
                       COUNT(*) as count
                FROM logs
                WHERE datetime(timestamp) > datetime(?)
                GROUP BY level
            """,
                (cutoff_time.isoformat(),),
            )

            level_stats = {row[1]: row[2] for row in cursor.fetchall()}
            total_entries = sum(level_stats.values())

            # Get source statistics
            cursor.execute(
                """
                SELECT source, COUNT(*) as count
                FROM logs
                WHERE datetime(timestamp) > datetime(?)
                GROUP BY source
            """,
                (cutoff_time.isoformat(),),
            )

            source_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # Get error patterns
            cursor.execute(
                """
                SELECT pattern_name, COUNT(*) as count, severity
                FROM pattern_matches
                WHERE datetime(timestamp) > datetime(?)
                GROUP BY pattern_name, severity
                ORDER BY count DESC
                LIMIT 10
            """,
                (cutoff_time.isoformat(),),
            )

            error_patterns = [
                {"pattern_name": row[0], "count": row[1], "severity": row[2]}
                for row in cursor.fetchall()
            ]

            # Calculate performance metrics
            cursor.execute(
                """
                SELECT AVG(CAST(json_extract(parsed_data, '$.duration_ms') AS REAL)) as avg_duration
                FROM logs
                WHERE datetime(timestamp) > datetime(?)
                  AND json_extract(parsed_data, '$.duration_ms') IS NOT NULL
            """,
                (cutoff_time.isoformat(),),
            )

            avg_query_time = cursor.fetchone()[0] or 0

            performance_metrics = {
                "avg_query_time_ms": round(avg_query_time, 2),
                "slow_query_count": level_stats.get("warning", 0)
                + level_stats.get("error", 0),
                "error_rate": round(
                    (level_stats.get("error", 0) / max(total_entries, 1)) * 100, 2
                ),
            }

            # Detect anomalies (simple spike detection)
            anomalies = []
            if level_stats.get("error", 0) > 10:  # More than 10 errors
                anomalies.append(
                    {
                        "type": "error_spike",
                        "description": f"High error count: {level_stats['error']} errors in {hours} hours",
                        "severity": "high",
                    }
                )

            # Generate recommendations
            recommendations = []
            if avg_query_time > 100:
                recommendations.append("Consider optimizing slow database queries")

            if level_stats.get("error", 0) > level_stats.get("info", 0):
                recommendations.append(
                    "High error rate detected - investigate error patterns"
                )

            if source_stats.get("system", 0) > 100:
                recommendations.append("High system log activity - check system health")

            conn.close()

            return LogAnalysis(
                period_start=(datetime.now() - timedelta(hours=hours)).isoformat(),
                period_end=datetime.now().isoformat(),
                total_entries=total_entries,
                entries_by_level=level_stats,
                entries_by_source=source_stats,
                error_patterns=error_patterns,
                performance_metrics=performance_metrics,
                anomalies=anomalies,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return LogAnalysis(
                period_start="",
                period_end="",
                total_entries=0,
                entries_by_level={},
                entries_by_source={},
                error_patterns=[],
                performance_metrics={},
                anomalies=[],
                recommendations=[f"Error analyzing logs: {str(e)}"],
            )

    def get_log_statistics(self) -> Dict[str, Any]:
        """Get current log aggregation statistics."""
        return {
            "in_memory_entries": len(self.log_storage),
            "parse_statistics": dict(self.parse_stats),
            "active_patterns": len(
                [p for p in self.log_patterns.values() if p.enabled]
            ),
            "log_sources_connected": len(self.log_sources),
            "database_path": self.db_path,
            "running": self.running,
            "timestamp": datetime.now().isoformat(),
        }

    async def export_log_report(self, file_path: str, hours: int = 24):
        """Export comprehensive log analysis report."""
        analysis = await self.analyze_logs(hours)
        statistics = self.get_log_statistics()

        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_period_hours": hours,
                "report_type": "comprehensive_log_analysis",
            },
            "log_analysis": asdict(analysis),
            "aggregator_statistics": statistics,
            "pattern_configuration": {
                pattern_name: {
                    "source": pattern.source,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "enabled": pattern.enabled,
                }
                for pattern_name, pattern in self.log_patterns.items()
            },
        }

        async with aiofiles.open(file_path, "w") as f:
            await f.write(json.dumps(report, indent=2, default=str))

        logger.info(f"Log analysis report exported to {file_path}")


# Example usage
async def run_log_aggregator_demo():
    """Demo the log aggregator."""
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
        "database_path": "/home/opsvi/master_root/logs/log_aggregator.db",
    }

    log_aggregator = LogAggregator(config)

    try:
        await log_aggregator.start()

        # Let it run for a bit to collect logs
        await asyncio.sleep(10)

        # Analyze logs
        analysis = await log_aggregator.analyze_logs(hours=1)
        print("Log Analysis:")
        print(json.dumps(asdict(analysis), indent=2, default=str))

        # Get statistics
        stats = log_aggregator.get_log_statistics()
        print("\nLog Aggregator Statistics:")
        print(json.dumps(stats, indent=2))

        # Export report
        report_path = (
            f"/home/opsvi/master_root/LOG_ANALYSIS_REPORT_{int(time.time())}.json"
        )
        await log_aggregator.export_log_report(report_path)
        print(f"\nLog analysis report exported to: {report_path}")

    finally:
        await log_aggregator.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_log_aggregator_demo())
