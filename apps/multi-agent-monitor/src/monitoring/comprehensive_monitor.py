#!/usr/bin/env python3
"""
Comprehensive Agent Monitor - Production Ready
Monitors all aspects of multi-agent execution including tokens, sessions, logs, errors, and config
"""

import asyncio
import json
import os
import re
import subprocess
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import psutil
import yaml


class MonitoringLevel(Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    DEBUG = "debug"


@dataclass
class TokenUsage:
    """Track token usage metrics"""

    token_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    last_used: Optional[datetime] = None
    current_session: Optional[str] = None
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class SessionMetrics:
    """Track session metrics"""

    session_id: str
    agent_name: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    token_used: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    log_file: Optional[str] = None
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0


@dataclass
class SystemMetrics:
    """Track system resource metrics"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_agents: int
    queued_tasks: int
    network_bytes_sent: int
    network_bytes_recv: int
    open_file_descriptors: int


@dataclass
class ErrorMetrics:
    """Track error patterns and frequencies"""

    error_type: str
    count: int = 0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    affected_sessions: Set[str] = field(default_factory=set)
    sample_messages: List[str] = field(default_factory=list)
    resolution_attempts: int = 0
    resolved: bool = False


class ComprehensiveAgentMonitor:
    """Production-ready monitoring system for multi-agent orchestration"""

    def __init__(
        self,
        output_dir: Path = Path("/tmp/agent_monitor"),
        monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED,
        max_history: int = 1000,
        enable_alerts: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.monitoring_level = monitoring_level
        self.max_history = max_history
        self.enable_alerts = enable_alerts

        # Monitoring data structures
        self.token_usage: Dict[str, TokenUsage] = {}
        self.active_sessions: Dict[str, SessionMetrics] = {}
        self.completed_sessions: deque = deque(maxlen=max_history)
        self.error_metrics: Dict[str, ErrorMetrics] = {}
        self.system_metrics: deque = deque(maxlen=1000)

        # Configuration tracking
        self.config: Dict[str, Any] = {}
        self.config_changes: List[Dict] = []

        # Real-time metrics
        self.metrics_lock = threading.Lock()
        self.current_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "avg_session_duration": 0.0,
            "error_rate": 0.0,
        }

        # Alert thresholds
        self.alert_thresholds = {
            "error_rate": 0.2,  # 20% error rate
            "token_failure_rate": 0.1,  # 10% token failure
            "memory_usage": 80,  # 80% memory
            "disk_usage": 90,  # 90% disk
            "session_timeout": 600,  # 10 minutes
            "cost_per_hour": 10.0,  # $10/hour
        }

        # Initialize monitoring files
        self._init_monitoring_files()

        # Start background monitoring
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._background_monitor, daemon=True
        )
        self.monitor_thread.start()

    def _init_monitoring_files(self):
        """Initialize monitoring output files"""
        # Create monitoring subdirectories
        dirs = ["sessions", "tokens", "errors", "system", "config", "reports"]
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(exist_ok=True)

        # Create main dashboard file
        self.dashboard_file = self.output_dir / "dashboard.json"
        self.update_dashboard()

    def register_token(self, token_id: str, token_value: str = None):
        """Register a token for monitoring"""
        if token_id not in self.token_usage:
            self.token_usage[token_id] = TokenUsage(token_id=token_id)
            self._log_event("token_registered", {"token_id": token_id})

    def start_session(
        self, session_id: str, agent_name: str, task_type: str, token_id: str = None
    ) -> SessionMetrics:
        """Start monitoring a new session"""
        with self.metrics_lock:
            session = SessionMetrics(
                session_id=session_id,
                agent_name=agent_name,
                task_type=task_type,
                start_time=datetime.now(),
                token_used=token_id,
            )

            self.active_sessions[session_id] = session
            self.current_stats["active_sessions"] += 1
            self.current_stats["total_sessions"] += 1

            if token_id:
                if token_id in self.token_usage:
                    self.token_usage[token_id].current_session = session_id
                    self.token_usage[token_id].total_requests += 1

            self._log_event(
                "session_started",
                {
                    "session_id": session_id,
                    "agent_name": agent_name,
                    "task_type": task_type,
                    "token_id": token_id,
                },
            )

            return session

    def update_session(self, session_id: str, **kwargs):
        """Update session metrics"""
        with self.metrics_lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]

                # Update metrics
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        if key in [
                            "errors",
                            "warnings",
                            "files_created",
                            "files_modified",
                            "deliverables",
                        ]:
                            getattr(session, key).extend(
                                value if isinstance(value, list) else [value]
                            )
                        else:
                            setattr(session, key, value)

                # Update token usage if tokens are reported
                if "input_tokens" in kwargs or "output_tokens" in kwargs:
                    if session.token_used and session.token_used in self.token_usage:
                        token = self.token_usage[session.token_used]
                        token.total_input_tokens += kwargs.get("input_tokens", 0)
                        token.total_output_tokens += kwargs.get("output_tokens", 0)
                        token.last_used = datetime.now()

                # Update cost if provided
                if "cost_usd" in kwargs:
                    self.current_stats["total_cost_usd"] += kwargs["cost_usd"]
                    if session.token_used and session.token_used in self.token_usage:
                        self.token_usage[session.token_used].total_cost_usd += kwargs[
                            "cost_usd"
                        ]

    def end_session(
        self, session_id: str, status: str = "completed", exit_code: int = 0
    ):
        """End a monitoring session"""
        with self.metrics_lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.end_time = datetime.now()
                session.status = status
                session.exit_code = exit_code
                session.duration_seconds = (
                    session.end_time - session.start_time
                ).total_seconds()

                # Update token usage
                if session.token_used and session.token_used in self.token_usage:
                    token = self.token_usage[session.token_used]
                    if status == "completed":
                        token.successful_requests += 1
                    else:
                        token.failed_requests += 1
                        token.error_count += 1
                    token.current_session = None

                # Update stats
                self.current_stats["active_sessions"] -= 1
                if status == "completed":
                    self.current_stats["successful_sessions"] += 1
                else:
                    self.current_stats["failed_sessions"] += 1

                # Calculate averages
                self._update_averages()

                # Move to completed
                self.completed_sessions.append(session)
                del self.active_sessions[session_id]

                # Save session report
                self._save_session_report(session)

                self._log_event(
                    "session_ended",
                    {
                        "session_id": session_id,
                        "status": status,
                        "duration": session.duration_seconds,
                        "exit_code": exit_code,
                    },
                )

    def record_error(self, error_type: str, message: str, session_id: str = None):
        """Record an error occurrence"""
        with self.metrics_lock:
            if error_type not in self.error_metrics:
                self.error_metrics[error_type] = ErrorMetrics(error_type=error_type)

            error = self.error_metrics[error_type]
            error.count += 1
            error.last_seen = datetime.now()
            if session_id:
                error.affected_sessions.add(session_id)

            # Keep sample messages
            if len(error.sample_messages) < 10:
                error.sample_messages.append(message)

            # Update session if applicable
            if session_id and session_id in self.active_sessions:
                self.active_sessions[session_id].errors.append(
                    f"{error_type}: {message}"
                )

            # Check for alerts
            if self.enable_alerts:
                self._check_error_alerts()

    def update_config(self, config_key: str, config_value: Any):
        """Update configuration tracking"""
        old_value = self.config.get(config_key)
        self.config[config_key] = config_value

        change = {
            "timestamp": datetime.now().isoformat(),
            "key": config_key,
            "old_value": old_value,
            "new_value": config_value,
        }
        self.config_changes.append(change)

        # Save config history
        self._save_config_change(change)

    def monitor_log_file(self, log_path: Path, session_id: str = None):
        """Monitor a log file for patterns"""
        if not log_path.exists():
            return

        patterns = {
            "error": re.compile(r"(?i)(error|exception|failed|failure)"),
            "warning": re.compile(r"(?i)(warning|warn|caution)"),
            "success": re.compile(r"(?i)(success|completed|finished|done)"),
            "file_created": re.compile(
                r"(?i)(created?|wrote|generated)\s+(?:file\s+)?([^\s]+)"
            ),
            "token_used": re.compile(r"(?i)token[:\s]+(\w+)"),
            "cost": re.compile(r"\$?([\d.]+)\s*(?:USD|usd|\$)"),
        }

        try:
            with open(log_path, "r") as f:
                for line in f:
                    for pattern_name, pattern in patterns.items():
                        if match := pattern.search(line):
                            if pattern_name == "error":
                                self.record_error("log_error", line.strip(), session_id)
                            elif pattern_name == "file_created" and session_id:
                                self.update_session(
                                    session_id, files_created=[match.group(1)]
                                )
                            elif pattern_name == "cost" and session_id:
                                try:
                                    cost = float(match.group(1))
                                    self.update_session(session_id, cost_usd=cost)
                                except ValueError:
                                    pass
        except Exception as e:
            self._log_event(
                "log_monitor_error", {"error": str(e), "log_path": str(log_path)}
            )

    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        with self.metrics_lock:
            # Calculate current rates
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            recent_sessions = [
                s
                for s in self.completed_sessions
                if s.end_time and s.end_time > hour_ago
            ]

            hourly_cost = sum(s.cost_usd for s in recent_sessions)
            hourly_tokens = sum(
                s.input_tokens + s.output_tokens for s in recent_sessions
            )

            # Token health
            token_health = {}
            for token_id, usage in self.token_usage.items():
                total = usage.successful_requests + usage.failed_requests
                success_rate = usage.successful_requests / total if total > 0 else 1.0
                token_health[token_id] = {
                    "status": "healthy"
                    if success_rate > 0.9
                    else "degraded"
                    if success_rate > 0.7
                    else "unhealthy",
                    "success_rate": success_rate,
                    "total_requests": total,
                    "last_used": usage.last_used.isoformat()
                    if usage.last_used
                    else None,
                    "current_session": usage.current_session,
                }

            # System health
            latest_system = self.system_metrics[-1] if self.system_metrics else None
            system_health = {
                "cpu_percent": latest_system.cpu_percent if latest_system else 0,
                "memory_percent": latest_system.memory_percent if latest_system else 0,
                "disk_usage": latest_system.disk_usage_percent if latest_system else 0,
                "status": self._get_system_status(latest_system)
                if latest_system
                else "unknown",
            }

            # Error summary
            error_summary = {}
            for error_type, metrics in self.error_metrics.items():
                if metrics.last_seen > hour_ago:
                    error_summary[error_type] = {
                        "count": metrics.count,
                        "recent_count": len(
                            [
                                s
                                for s in metrics.affected_sessions
                                if s in [sess.session_id for sess in recent_sessions]
                            ]
                        ),
                        "last_seen": metrics.last_seen.isoformat(),
                    }

            return {
                "timestamp": now.isoformat(),
                "summary": {
                    "active_agents": len(self.active_sessions),
                    "total_sessions": self.current_stats["total_sessions"],
                    "success_rate": self._calculate_success_rate(),
                    "error_rate": self.current_stats["error_rate"],
                    "hourly_cost": hourly_cost,
                    "hourly_tokens": hourly_tokens,
                    "avg_duration": self.current_stats["avg_session_duration"],
                },
                "active_sessions": {
                    sid: {
                        "agent": s.agent_name,
                        "task": s.task_type,
                        "duration": (now - s.start_time).total_seconds(),
                        "status": s.status,
                        "token": s.token_used,
                    }
                    for sid, s in self.active_sessions.items()
                },
                "token_health": token_health,
                "system_health": system_health,
                "recent_errors": error_summary,
                "alerts": self._get_active_alerts(),
            }

    def generate_report(
        self, report_type: str = "summary", period_hours: int = 24
    ) -> str:
        """Generate a detailed report"""
        now = datetime.now()
        period_start = now - timedelta(hours=period_hours)

        # Filter sessions for period
        period_sessions = [
            s
            for s in self.completed_sessions
            if s.end_time and s.end_time > period_start
        ]

        report = []
        report.append(f"# Agent Monitor Report - {report_type.upper()}")
        report.append(f"Period: {period_start.isoformat()} to {now.isoformat()}")
        report.append("")

        # Executive Summary
        report.append("## Executive Summary")
        report.append(f"- Total Sessions: {len(period_sessions)}")
        report.append(f"- Active Sessions: {len(self.active_sessions)}")
        report.append(f"- Success Rate: {self._calculate_success_rate():.1%}")
        report.append(f"- Total Cost: ${sum(s.cost_usd for s in period_sessions):.2f}")
        report.append(
            f"- Total Tokens: {sum(s.input_tokens + s.output_tokens for s in period_sessions):,}"
        )
        report.append("")

        # Token Usage
        report.append("## Token Usage")
        for token_id, usage in sorted(
            self.token_usage.items(), key=lambda x: x[1].total_requests, reverse=True
        ):
            report.append(f"### {token_id}")
            report.append(
                f"- Requests: {usage.total_requests} (Success: {usage.successful_requests}, Failed: {usage.failed_requests})"
            )
            report.append(
                f"- Tokens: {usage.total_input_tokens:,} in, {usage.total_output_tokens:,} out"
            )
            report.append(f"- Cost: ${usage.total_cost_usd:.2f}")
            report.append(
                f"- Last Used: {usage.last_used.isoformat() if usage.last_used else 'Never'}"
            )
            report.append("")

        # Error Analysis
        if self.error_metrics:
            report.append("## Error Analysis")
            for error_type, metrics in sorted(
                self.error_metrics.items(), key=lambda x: x[1].count, reverse=True
            ):
                report.append(f"### {error_type}")
                report.append(f"- Total Count: {metrics.count}")
                report.append(f"- Affected Sessions: {len(metrics.affected_sessions)}")
                report.append(f"- First Seen: {metrics.first_seen.isoformat()}")
                report.append(f"- Last Seen: {metrics.last_seen.isoformat()}")
                if metrics.sample_messages:
                    report.append("- Sample: " + metrics.sample_messages[0][:100])
                report.append("")

        # Performance Metrics
        report.append("## Performance Metrics")
        if period_sessions:
            durations = [
                s.duration_seconds for s in period_sessions if s.duration_seconds > 0
            ]
            if durations:
                report.append(f"- Avg Duration: {sum(durations)/len(durations):.1f}s")
                report.append(f"- Min Duration: {min(durations):.1f}s")
                report.append(f"- Max Duration: {max(durations):.1f}s")

        # System Resources
        if self.system_metrics:
            recent_system = list(self.system_metrics)[-100:]  # Last 100 measurements
            report.append("")
            report.append("## System Resources")
            report.append(
                f"- Avg CPU: {sum(s.cpu_percent for s in recent_system)/len(recent_system):.1f}%"
            )
            report.append(
                f"- Avg Memory: {sum(s.memory_percent for s in recent_system)/len(recent_system):.1f}%"
            )
            report.append(
                f"- Current Disk: {recent_system[-1].disk_usage_percent:.1f}%"
            )

        # Configuration Changes
        if self.config_changes:
            report.append("")
            report.append("## Configuration Changes")
            for change in self.config_changes[-10:]:  # Last 10 changes
                report.append(
                    f"- {change['timestamp']}: {change['key']} changed from {change['old_value']} to {change['new_value']}"
                )

        report_text = "\n".join(report)

        # Save report
        report_file = (
            self.output_dir / "reports" / f"report_{now.strftime('%Y%m%d_%H%M%S')}.md"
        )
        report_file.write_text(report_text)

        return report_text

    def update_dashboard(self):
        """Update the main dashboard file"""
        dashboard_data = self.get_dashboard_data()
        self.dashboard_file.write_text(
            json.dumps(dashboard_data, indent=2, default=str)
        )

    def _background_monitor(self):
        """Background monitoring thread"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Check for stale sessions
                self._check_stale_sessions()

                # Update dashboard
                self.update_dashboard()

                # Check alerts
                if self.enable_alerts:
                    self._check_all_alerts()

                # Sleep
                time.sleep(5)  # Update every 5 seconds

            except Exception as e:
                self._log_event("monitor_error", {"error": str(e)})

    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            net_io = psutil.net_io_counters()
            disk_usage = psutil.disk_usage("/")

            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage_percent=disk_usage.percent,
                active_agents=len(self.active_sessions),
                queued_tasks=0,  # Would need task queue integration
                network_bytes_sent=net_io.bytes_sent,
                network_bytes_recv=net_io.bytes_recv,
                open_file_descriptors=len(psutil.Process().open_files()),
            )

            self.system_metrics.append(metrics)

        except Exception as e:
            self._log_event("system_metrics_error", {"error": str(e)})

    def _check_stale_sessions(self):
        """Check for stale/hung sessions"""
        now = datetime.now()
        for session_id, session in list(self.active_sessions.items()):
            duration = (now - session.start_time).total_seconds()
            if duration > self.alert_thresholds["session_timeout"]:
                self._log_event(
                    "stale_session_detected",
                    {"session_id": session_id, "duration": duration},
                )
                # Could auto-terminate or alert

    def _update_averages(self):
        """Update running averages"""
        if self.completed_sessions:
            durations = [
                s.duration_seconds
                for s in self.completed_sessions
                if s.duration_seconds > 0
            ]
            if durations:
                self.current_stats["avg_session_duration"] = sum(durations) / len(
                    durations
                )

            total = len(self.completed_sessions)
            failed = len(
                [s for s in self.completed_sessions if s.status != "completed"]
            )
            self.current_stats["error_rate"] = failed / total if total > 0 else 0

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total = (
            self.current_stats["successful_sessions"]
            + self.current_stats["failed_sessions"]
        )
        if total == 0:
            return 1.0
        return self.current_stats["successful_sessions"] / total

    def _get_system_status(self, metrics: SystemMetrics) -> str:
        """Determine system health status"""
        if metrics.cpu_percent > 90 or metrics.memory_percent > 90:
            return "critical"
        elif metrics.cpu_percent > 70 or metrics.memory_percent > 70:
            return "warning"
        return "healthy"

    def _check_all_alerts(self):
        """Check all alert conditions"""
        self._check_error_alerts()
        self._check_resource_alerts()
        self._check_cost_alerts()

    def _check_error_alerts(self):
        """Check for error rate alerts"""
        if self.current_stats["error_rate"] > self.alert_thresholds["error_rate"]:
            self._trigger_alert(
                "high_error_rate",
                {
                    "rate": self.current_stats["error_rate"],
                    "threshold": self.alert_thresholds["error_rate"],
                },
            )

    def _check_resource_alerts(self):
        """Check for resource alerts"""
        if self.system_metrics:
            latest = self.system_metrics[-1]
            if latest.memory_percent > self.alert_thresholds["memory_usage"]:
                self._trigger_alert(
                    "high_memory_usage",
                    {
                        "usage": latest.memory_percent,
                        "threshold": self.alert_thresholds["memory_usage"],
                    },
                )
            if latest.disk_usage_percent > self.alert_thresholds["disk_usage"]:
                self._trigger_alert(
                    "high_disk_usage",
                    {
                        "usage": latest.disk_usage_percent,
                        "threshold": self.alert_thresholds["disk_usage"],
                    },
                )

    def _check_cost_alerts(self):
        """Check for cost alerts"""
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_sessions = [
            s for s in self.completed_sessions if s.end_time and s.end_time > hour_ago
        ]
        hourly_cost = sum(s.cost_usd for s in recent_sessions)

        if hourly_cost > self.alert_thresholds["cost_per_hour"]:
            self._trigger_alert(
                "high_cost",
                {
                    "hourly_cost": hourly_cost,
                    "threshold": self.alert_thresholds["cost_per_hour"],
                },
            )

    def _get_active_alerts(self) -> List[Dict]:
        """Get list of active alerts"""
        alerts = []

        # Check each alert condition
        if self.current_stats["error_rate"] > self.alert_thresholds["error_rate"]:
            alerts.append(
                {
                    "type": "error_rate",
                    "severity": "high",
                    "message": f"Error rate {self.current_stats['error_rate']:.1%} exceeds threshold",
                }
            )

        if self.system_metrics:
            latest = self.system_metrics[-1]
            if latest.memory_percent > self.alert_thresholds["memory_usage"]:
                alerts.append(
                    {
                        "type": "memory",
                        "severity": "medium",
                        "message": f"Memory usage {latest.memory_percent:.1f}% exceeds threshold",
                    }
                )

        return alerts

    def _trigger_alert(self, alert_type: str, details: Dict):
        """Trigger an alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "details": details,
        }

        # Log alert
        self._log_event("alert_triggered", alert)

        # Could integrate with notification systems here
        # e.g., send email, Slack message, etc.

    def _save_session_report(self, session: SessionMetrics):
        """Save detailed session report"""
        report_file = self.output_dir / "sessions" / f"{session.session_id}.json"
        report_file.write_text(json.dumps(asdict(session), indent=2, default=str))

    def _save_config_change(self, change: Dict):
        """Save configuration change"""
        config_file = self.output_dir / "config" / "changes.jsonl"
        with open(config_file, "a") as f:
            f.write(json.dumps(change, default=str) + "\n")

    def _log_event(self, event_type: str, details: Dict):
        """Log monitoring event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details,
        }

        if self.monitoring_level == MonitoringLevel.DEBUG:
            print(f"[MONITOR] {event_type}: {details}")

        # Append to event log
        event_file = self.output_dir / "events.jsonl"
        with open(event_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def shutdown(self):
        """Shutdown monitoring gracefully"""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        # Final dashboard update
        self.update_dashboard()

        # Generate final report
        self.generate_report("final")


# Integration with existing orchestrator
class MonitoredOrchestrator:
    """Wrapper to add monitoring to any orchestrator"""

    def __init__(self, orchestrator, monitor: ComprehensiveAgentMonitor):
        self.orchestrator = orchestrator
        self.monitor = monitor

        # Register all tokens
        if hasattr(orchestrator, "token_pool"):
            for i, token in enumerate(orchestrator.token_pool.tokens):
                self.monitor.register_token(f"token_{i+1}", token)

    async def execute_task(self, task, **kwargs):
        """Execute task with monitoring"""
        # Start session monitoring
        session_id = kwargs.get("session_id", str(uuid.uuid4()))
        session = self.monitor.start_session(
            session_id=session_id,
            agent_name=task.get("agent_name", "unknown"),
            task_type=task.get("task_type", "unknown"),
            token_id=kwargs.get("token_id"),
        )

        try:
            # Execute actual task
            result = await self.orchestrator.execute_task(task, **kwargs)

            # Update session with results
            if isinstance(result, dict):
                self.monitor.update_session(session_id, **result)

            # End session successfully
            self.monitor.end_session(session_id, status="completed")

            return result

        except Exception as e:
            # Record error
            self.monitor.record_error(type(e).__name__, str(e), session_id)

            # End session with error
            self.monitor.end_session(session_id, status="failed", exit_code=1)

            raise


if __name__ == "__main__":
    # Example usage
    monitor = ComprehensiveAgentMonitor(
        monitoring_level=MonitoringLevel.DEBUG, enable_alerts=True
    )

    # Simulate some sessions
    import uuid

    # Register tokens
    for i in range(1, 16):
        monitor.register_token(f"token_{i}")

    # Start a session
    session_id = str(uuid.uuid4())
    monitor.start_session(session_id, "test_agent", "documentation", "token_1")

    # Update with progress
    monitor.update_session(
        session_id,
        input_tokens=1000,
        output_tokens=500,
        cost_usd=0.05,
        files_created=["test.md"],
    )

    # Record an error
    monitor.record_error("api_error", "Rate limit exceeded", session_id)

    # End session
    monitor.end_session(session_id, status="completed")

    # Get dashboard
    dashboard = monitor.get_dashboard_data()
    print(json.dumps(dashboard, indent=2, default=str))

    # Generate report
    report = monitor.generate_report()
    print("\n" + report)

    # Shutdown
    monitor.shutdown()
