#!/usr/bin/env python3
"""
Advanced Alert Management System for Unified Context System

Intelligent alerting with:
- Multi-channel notifications (email, webhook, file)
- Alert correlation and suppression
- Escalation policies
- Historical alert analysis
- Predictive alerting based on trends
- Integration with health checker and performance optimizer
"""

import asyncio
import json
import logging
import smtplib
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    id: str
    component: str
    severity: str  # 'info', 'warning', 'critical'
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold_value: float
    tags: List[str]
    timestamp: str
    resolved: bool = False
    resolved_timestamp: Optional[str] = None
    escalation_level: int = 0
    notification_count: int = 0
    suppressed: bool = False
    correlation_group: Optional[str] = None


@dataclass
class AlertRule:
    name: str
    component: str
    metric_path: str  # JSONPath to metric in health check data
    operator: str  # 'gt', 'lt', 'eq', 'ne', 'contains'
    threshold: float
    severity: str
    duration_minutes: int = 0  # Alert only if condition persists
    description_template: str = ""
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    cooldown_minutes: int = 15  # Minimum time between same alerts


@dataclass
class NotificationChannel:
    name: str
    type: str  # 'email', 'webhook', 'file', 'slack'
    config: Dict[str, Any]
    severity_filter: List[str] = field(default_factory=lambda: ["critical"])
    enabled: bool = True


@dataclass
class EscalationPolicy:
    name: str
    levels: List[Dict[str, Any]]  # [{delay_minutes: 30, channels: ['email']}, ...]
    max_escalations: int = 3


class AlertManager:
    """Advanced alert management with intelligent features."""

    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.active_alerts = {}  # alert_id -> Alert
        self.alert_history = deque(maxlen=10000)  # Last 10k alerts
        self.alert_rules = self._initialize_default_rules()
        self.notification_channels = self._initialize_notification_channels()
        self.escalation_policies = self._initialize_escalation_policies()

        # Alert correlation and suppression
        self.correlation_windows = {}  # group -> time window
        self.suppression_rules = []

        # Metrics for alert analysis
        self.metric_history = deque(maxlen=1000)
        self.alert_stats = defaultdict(int)

        # Background tasks
        self.running = False
        self.tasks = []

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load alert manager configuration."""
        default_config = {
            "email": {
                "smtp_server": "localhost",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "alerts@opsvi.local",
                "use_tls": True,
            },
            "webhook": {"default_url": "", "timeout": 10, "retry_count": 3},
            "file": {
                "alert_log_path": "/home/opsvi/master_root/logs/alerts.log",
                "max_file_size_mb": 100,
            },
            "correlation": {"window_minutes": 5, "max_correlated_alerts": 10},
            "escalation": {"default_policy": "standard", "max_escalation_level": 3},
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")

        return default_config

    def _initialize_default_rules(self) -> Dict[str, AlertRule]:
        """Initialize default alert rules."""
        rules = {}

        # System resource rules
        rules["high_cpu"] = AlertRule(
            name="high_cpu",
            component="system",
            metric_path="$.cpu_percent",
            operator="gt",
            threshold=80.0,
            severity="warning",
            duration_minutes=2,
            description_template="CPU usage is {current_value:.1f}% (threshold: {threshold_value:.1f}%)",
            tags=["system", "performance"],
        )

        rules["critical_cpu"] = AlertRule(
            name="critical_cpu",
            component="system",
            metric_path="$.cpu_percent",
            operator="gt",
            threshold=90.0,
            severity="critical",
            duration_minutes=1,
            description_template="Critical CPU usage: {current_value:.1f}% (threshold: {threshold_value:.1f}%)",
            tags=["system", "performance", "critical"],
        )

        rules["high_memory"] = AlertRule(
            name="high_memory",
            component="system",
            metric_path="$.memory_percent",
            operator="gt",
            threshold=85.0,
            severity="warning",
            duration_minutes=3,
            description_template="Memory usage is {current_value:.1f}% (threshold: {threshold_value:.1f}%)",
            tags=["system", "memory"],
        )

        rules["critical_memory"] = AlertRule(
            name="critical_memory",
            component="system",
            metric_path="$.memory_percent",
            operator="gt",
            threshold=95.0,
            severity="critical",
            duration_minutes=1,
            description_template="Critical memory usage: {current_value:.1f}% (threshold: {threshold_value:.1f}%)",
            tags=["system", "memory", "critical"],
        )

        # Database rules
        rules["postgres_offline"] = AlertRule(
            name="postgres_offline",
            component="postgresql",
            metric_path="$.status",
            operator="eq",
            threshold="offline",
            severity="critical",
            duration_minutes=0,
            description_template="PostgreSQL database is offline",
            tags=["database", "postgresql", "critical"],
        )

        rules["slow_queries"] = AlertRule(
            name="slow_queries",
            component="postgresql",
            metric_path="$.test_query_time_ms",
            operator="gt",
            threshold=500.0,
            severity="warning",
            duration_minutes=2,
            description_template="Slow database queries detected: {current_value:.1f}ms (threshold: {threshold_value:.1f}ms)",
            tags=["database", "performance"],
        )

        rules["neo4j_offline"] = AlertRule(
            name="neo4j_offline",
            component="neo4j",
            metric_path="$.status",
            operator="eq",
            threshold="offline",
            severity="critical",
            duration_minutes=0,
            description_template="Neo4j graph database is offline",
            tags=["database", "neo4j", "critical"],
        )

        # Vector search rules
        rules["vector_search_slow"] = AlertRule(
            name="vector_search_slow",
            component="vector_search",
            metric_path="$.avg_search_time_ms",
            operator="gt",
            threshold=100.0,
            severity="warning",
            duration_minutes=3,
            description_template="Vector search performance degraded: {current_value:.1f}ms (threshold: {threshold_value:.1f}ms)",
            tags=["vector_search", "performance"],
        )

        rules["low_vector_coverage"] = AlertRule(
            name="low_vector_coverage",
            component="vector_search",
            metric_path="$.coverage_percent",
            operator="lt",
            threshold=70.0,
            severity="warning",
            duration_minutes=10,
            description_template="Low vector embedding coverage: {current_value:.1f}% (threshold: {threshold_value:.1f}%)",
            tags=["vector_search", "data_quality"],
        )

        # Docker rules
        rules["container_down"] = AlertRule(
            name="container_down",
            component="docker_services",
            metric_path="$.status",
            operator="eq",
            threshold="critical",
            severity="critical",
            duration_minutes=0,
            description_template="Critical Docker container issues detected",
            tags=["docker", "infrastructure", "critical"],
        )

        return rules

    def _initialize_notification_channels(self) -> Dict[str, NotificationChannel]:
        """Initialize notification channels."""
        channels = {}

        # File logging (always enabled)
        channels["file"] = NotificationChannel(
            name="file",
            type="file",
            config={"file_path": self.config["file"]["alert_log_path"]},
            severity_filter=["info", "warning", "critical"],
            enabled=True,
        )

        # Email notifications
        if self.config["email"]["from_address"]:
            channels["email"] = NotificationChannel(
                name="email",
                type="email",
                config=self.config["email"],
                severity_filter=["warning", "critical"],
                enabled=True,
            )

        # Webhook notifications
        if self.config["webhook"]["default_url"]:
            channels["webhook"] = NotificationChannel(
                name="webhook",
                type="webhook",
                config=self.config["webhook"],
                severity_filter=["critical"],
                enabled=True,
            )

        return channels

    def _initialize_escalation_policies(self) -> Dict[str, EscalationPolicy]:
        """Initialize escalation policies."""
        policies = {}

        policies["standard"] = EscalationPolicy(
            name="standard",
            levels=[
                {"delay_minutes": 0, "channels": ["file"]},
                {"delay_minutes": 5, "channels": ["file", "email"]},
                {"delay_minutes": 15, "channels": ["file", "email", "webhook"]},
            ],
            max_escalations=3,
        )

        policies["critical"] = EscalationPolicy(
            name="critical",
            levels=[
                {"delay_minutes": 0, "channels": ["file", "email", "webhook"]},
                {"delay_minutes": 2, "channels": ["file", "email", "webhook"]},
                {"delay_minutes": 5, "channels": ["file", "email", "webhook"]},
            ],
            max_escalations=3,
        )

        return policies

    async def start(self):
        """Start the alert manager background tasks."""
        self.running = True

        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._escalation_processor()),
            asyncio.create_task(self._alert_correlation_processor()),
            asyncio.create_task(self._metrics_trend_analyzer()),
            asyncio.create_task(self._alert_cleanup_task()),
        ]

        logger.info("Alert manager started")

    async def stop(self):
        """Stop the alert manager."""
        self.running = False

        # Cancel background tasks
        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Alert manager stopped")

    async def process_health_check_data(self, health_data: Dict[str, Any]):
        """Process health check data and trigger alerts."""
        try:
            # Store metrics for trend analysis
            self.metric_history.append(
                {"timestamp": datetime.now().isoformat(), "data": health_data}
            )

            # Process each component's data
            component_results = health_data.get("component_results", [])

            for component_result in component_results:
                component_name = component_result.get("component", "unknown")
                metrics = component_result.get("metrics", {})
                status = component_result.get("status", "unknown")

                # Add status to metrics for rule evaluation
                metrics["status"] = status

                await self._evaluate_rules_for_component(component_name, metrics)

            # Check for system-wide patterns
            await self._evaluate_system_patterns(health_data)

        except Exception as e:
            logger.error(f"Error processing health check data: {e}")

    async def _evaluate_rules_for_component(
        self, component: str, metrics: Dict[str, Any]
    ):
        """Evaluate alert rules for a specific component."""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled or rule.component != component:
                continue

            try:
                # Extract metric value using JSONPath-like syntax
                metric_value = self._extract_metric_value(metrics, rule.metric_path)
                if metric_value is None:
                    continue

                # Evaluate condition
                condition_met = self._evaluate_condition(
                    metric_value, rule.operator, rule.threshold
                )

                if condition_met:
                    await self._handle_rule_trigger(rule, metric_value, metrics)
                else:
                    await self._handle_rule_recovery(rule)

            except Exception as e:
                logger.error(f"Error evaluating rule {rule_name}: {e}")

    def _extract_metric_value(self, metrics: Dict[str, Any], metric_path: str) -> Any:
        """Extract metric value using simple JSONPath-like syntax."""
        # Remove JSONPath prefix if present
        if metric_path.startswith("$."):
            metric_path = metric_path[2:]

        try:
            # Handle nested paths
            parts = metric_path.split(".")
            value = metrics

            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None

            return value
        except Exception:
            return None

    def _evaluate_condition(self, value: Any, operator: str, threshold: Any) -> bool:
        """Evaluate alert condition."""
        try:
            if operator == "gt":
                return float(value) > float(threshold)
            elif operator == "lt":
                return float(value) < float(threshold)
            elif operator == "eq":
                return value == threshold
            elif operator == "ne":
                return value != threshold
            elif operator == "contains":
                return str(threshold).lower() in str(value).lower()
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except (ValueError, TypeError):
            return False

    async def _handle_rule_trigger(
        self, rule: AlertRule, current_value: Any, metrics: Dict[str, Any]
    ):
        """Handle when a rule condition is triggered."""
        alert_id = f"{rule.component}_{rule.name}_{int(time.time())}"

        # Check cooldown period
        if self._is_in_cooldown(rule):
            return

        # Check if duration requirement is met
        if rule.duration_minutes > 0:
            if not self._check_duration_requirement(rule, current_value):
                return

        # Create alert
        alert = Alert(
            id=alert_id,
            component=rule.component,
            severity=rule.severity,
            title=f"{rule.component.title()} Alert: {rule.name}",
            description=rule.description_template.format(
                current_value=current_value, threshold_value=rule.threshold
            )
            if rule.description_template
            else f"Alert triggered for {rule.name}",
            metric_name=rule.metric_path,
            current_value=float(current_value)
            if isinstance(current_value, (int, float))
            else 0,
            threshold_value=float(rule.threshold)
            if isinstance(rule.threshold, (int, float))
            else 0,
            tags=rule.tags.copy(),
            timestamp=datetime.now().isoformat(),
        )

        # Add to active alerts
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Update statistics
        self.alert_stats[f"{rule.component}_{rule.severity}"] += 1

        # Determine correlation group
        alert.correlation_group = self._determine_correlation_group(alert, metrics)

        # Schedule notifications
        await self._schedule_notifications(alert)

        logger.info(f"Alert triggered: {alert.title} (ID: {alert_id})")

    async def _handle_rule_recovery(self, rule: AlertRule):
        """Handle when a rule condition is no longer met (recovery)."""
        # Find active alerts for this rule
        rule_alerts = [
            alert
            for alert in self.active_alerts.values()
            if alert.component == rule.component
            and rule.name in alert.id
            and not alert.resolved
        ]

        for alert in rule_alerts:
            alert.resolved = True
            alert.resolved_timestamp = datetime.now().isoformat()

            # Send recovery notification
            await self._send_recovery_notification(alert)

            # Remove from active alerts after a delay
            asyncio.create_task(
                self._cleanup_resolved_alert(alert.id, delay_minutes=10)
            )

            logger.info(f"Alert resolved: {alert.title} (ID: {alert.id})")

    def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """Check if rule is in cooldown period."""
        cutoff_time = datetime.now() - timedelta(minutes=rule.cooldown_minutes)

        for alert in self.alert_history:
            if (
                rule.component in alert.component
                and rule.name in alert.id
                and datetime.fromisoformat(alert.timestamp) > cutoff_time
            ):
                return True

        return False

    def _check_duration_requirement(self, rule: AlertRule, current_value: Any) -> bool:
        """Check if condition has persisted for required duration."""
        # This is a simplified implementation
        # In a production system, you'd maintain a more sophisticated state

        cutoff_time = datetime.now() - timedelta(minutes=rule.duration_minutes)

        # Check recent metrics for persistent condition
        persistent_count = 0
        total_count = 0

        for metric_point in reversed(list(self.metric_history)):
            timestamp = datetime.fromisoformat(metric_point["timestamp"])
            if timestamp < cutoff_time:
                break

            total_count += 1

            # Extract the metric value from historical data
            component_data = None
            for comp_result in metric_point["data"].get("component_results", []):
                if comp_result.get("component") == rule.component:
                    component_data = comp_result.get("metrics", {})
                    break

            if component_data:
                historical_value = self._extract_metric_value(
                    component_data, rule.metric_path
                )
                if historical_value is not None and self._evaluate_condition(
                    historical_value, rule.operator, rule.threshold
                ):
                    persistent_count += 1

        # Require at least 70% of checks to meet condition
        if total_count > 0:
            persistence_ratio = persistent_count / total_count
            return persistence_ratio >= 0.7

        return False

    def _determine_correlation_group(
        self, alert: Alert, metrics: Dict[str, Any]
    ) -> str:
        """Determine correlation group for alert suppression."""
        # Group related alerts together
        if "system" in alert.tags:
            return "system_resources"
        elif "database" in alert.tags:
            return f"database_{alert.component}"
        elif "performance" in alert.tags:
            return "performance_issues"
        else:
            return alert.component

    async def _schedule_notifications(self, alert: Alert):
        """Schedule notifications based on escalation policy."""
        policy_name = "critical" if alert.severity == "critical" else "standard"
        policy = self.escalation_policies.get(policy_name)

        if not policy:
            # Fallback to immediate file notification
            await self._send_notification(alert, "file")
            return

        # Schedule escalation levels
        for level_index, level in enumerate(policy.levels):
            delay_minutes = level["delay_minutes"]
            channels = level["channels"]

            # Schedule the notification
            asyncio.create_task(
                self._delayed_notification(alert, channels, delay_minutes, level_index)
            )

    async def _delayed_notification(
        self, alert: Alert, channels: List[str], delay_minutes: int, level: int
    ):
        """Send notification after delay if alert is still active."""
        if delay_minutes > 0:
            await asyncio.sleep(delay_minutes * 60)

        # Check if alert is still active and not resolved
        if alert.id in self.active_alerts and not alert.resolved:
            alert.escalation_level = level

            for channel_name in channels:
                await self._send_notification(alert, channel_name)

    async def _send_notification(self, alert: Alert, channel_name: str):
        """Send notification through specified channel."""
        channel = self.notification_channels.get(channel_name)
        if not channel or not channel.enabled:
            return

        # Check severity filter
        if alert.severity not in channel.severity_filter:
            return

        try:
            if channel.type == "file":
                await self._send_file_notification(alert, channel)
            elif channel.type == "email":
                await self._send_email_notification(alert, channel)
            elif channel.type == "webhook":
                await self._send_webhook_notification(alert, channel)

            alert.notification_count += 1
            logger.debug(f"Notification sent via {channel_name} for alert {alert.id}")

        except Exception as e:
            logger.error(f"Failed to send notification via {channel_name}: {e}")

    async def _send_file_notification(self, alert: Alert, channel: NotificationChannel):
        """Send file-based notification."""
        file_path = channel.config.get("file_path", "/tmp/alerts.log")

        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        alert_message = {
            "timestamp": alert.timestamp,
            "alert_id": alert.id,
            "component": alert.component,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "current_value": alert.current_value,
            "threshold_value": alert.threshold_value,
            "tags": alert.tags,
            "escalation_level": alert.escalation_level,
        }

        with open(file_path, "a") as f:
            f.write(json.dumps(alert_message) + "\n")

    async def _send_email_notification(
        self, alert: Alert, channel: NotificationChannel
    ):
        """Send email notification."""
        config = channel.config

        msg = MimeMultipart()
        msg["From"] = config["from_address"]
        msg["To"] = config.get("to_address", config["from_address"])
        msg["Subject"] = f"[{alert.severity.upper()}] {alert.title}"

        body = f"""
Alert Details:
- Component: {alert.component}
- Severity: {alert.severity.upper()}
- Description: {alert.description}
- Current Value: {alert.current_value}
- Threshold: {alert.threshold_value}
- Timestamp: {alert.timestamp}
- Alert ID: {alert.id}
- Tags: {', '.join(alert.tags)}

This is escalation level {alert.escalation_level + 1}.
"""

        msg.attach(MimeText(body, "plain"))

        # Send email
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        if config.get("use_tls", True):
            server.starttls()

        if config.get("username") and config.get("password"):
            server.login(config["username"], config["password"])

        server.send_message(msg)
        server.quit()

    async def _send_webhook_notification(
        self, alert: Alert, channel: NotificationChannel
    ):
        """Send webhook notification."""
        config = channel.config
        url = config.get("webhook_url", config.get("default_url"))

        if not url:
            return

        payload = {
            "alert_id": alert.id,
            "component": alert.component,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "current_value": alert.current_value,
            "threshold_value": alert.threshold_value,
            "timestamp": alert.timestamp,
            "tags": alert.tags,
            "escalation_level": alert.escalation_level,
            "resolved": alert.resolved,
        }

        timeout = config.get("timeout", 10)
        retry_count = config.get("retry_count", 3)

        for attempt in range(retry_count):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=timeout,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                break

            except requests.exceptions.RequestException as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                if attempt == retry_count - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

    async def _send_recovery_notification(self, alert: Alert):
        """Send recovery notification."""
        recovery_alert = Alert(
            id=f"{alert.id}_recovery",
            component=alert.component,
            severity="info",
            title=f"RECOVERED: {alert.title}",
            description=f"Alert has been resolved: {alert.description}",
            metric_name=alert.metric_name,
            current_value=alert.current_value,
            threshold_value=alert.threshold_value,
            tags=alert.tags + ["recovery"],
            timestamp=datetime.now().isoformat(),
            resolved=True,
        )

        # Send through file channel
        await self._send_notification(recovery_alert, "file")

    async def _cleanup_resolved_alert(self, alert_id: str, delay_minutes: int = 10):
        """Remove resolved alert from active alerts after delay."""
        await asyncio.sleep(delay_minutes * 60)

        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]

    async def _escalation_processor(self):
        """Background task to handle alert escalation."""
        while self.running:
            try:
                current_time = datetime.now()

                for alert in list(self.active_alerts.values()):
                    if alert.resolved:
                        continue

                    alert_age_minutes = (
                        current_time - datetime.fromisoformat(alert.timestamp)
                    ).total_seconds() / 60

                    # Check if we need to escalate
                    policy_name = (
                        "critical" if alert.severity == "critical" else "standard"
                    )
                    policy = self.escalation_policies.get(policy_name)

                    if policy and alert.escalation_level < len(policy.levels) - 1:
                        next_level = policy.levels[alert.escalation_level + 1]

                        if alert_age_minutes >= next_level["delay_minutes"]:
                            # Escalate
                            alert.escalation_level += 1

                            for channel_name in next_level["channels"]:
                                await self._send_notification(alert, channel_name)

                            logger.info(
                                f"Alert {alert.id} escalated to level {alert.escalation_level}"
                            )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in escalation processor: {e}")
                await asyncio.sleep(60)

    async def _alert_correlation_processor(self):
        """Background task to handle alert correlation and suppression."""
        while self.running:
            try:
                # Group alerts by correlation group
                correlation_groups = defaultdict(list)

                for alert in self.active_alerts.values():
                    if not alert.resolved and alert.correlation_group:
                        correlation_groups[alert.correlation_group].append(alert)

                # Apply suppression logic
                for group, alerts in correlation_groups.items():
                    if len(alerts) > 1:
                        # Sort by severity and timestamp
                        alerts.sort(
                            key=lambda a: (
                                {"critical": 0, "warning": 1, "info": 2}[a.severity],
                                a.timestamp,
                            )
                        )

                        # Suppress all but the most severe/earliest
                        primary_alert = alerts[0]

                        for alert in alerts[1:]:
                            if not alert.suppressed:
                                alert.suppressed = True
                                logger.info(
                                    f"Alert {alert.id} suppressed in favor of {primary_alert.id}"
                                )

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in correlation processor: {e}")
                await asyncio.sleep(300)

    async def _metrics_trend_analyzer(self):
        """Background task to analyze metrics trends and create predictive alerts."""
        while self.running:
            try:
                if len(self.metric_history) < 10:
                    await asyncio.sleep(600)  # Wait for more data
                    continue

                # Analyze trends for key metrics
                await self._analyze_cpu_trend()
                await self._analyze_memory_trend()
                await self._analyze_disk_trend()
                await self._analyze_query_performance_trend()

                await asyncio.sleep(600)  # Analyze every 10 minutes

            except Exception as e:
                logger.error(f"Error in trend analyzer: {e}")
                await asyncio.sleep(600)

    async def _analyze_cpu_trend(self):
        """Analyze CPU usage trends for predictive alerting."""
        try:
            recent_metrics = list(self.metric_history)[-20:]  # Last 20 data points
            cpu_values = []

            for metric_point in recent_metrics:
                for comp_result in metric_point["data"].get("component_results", []):
                    if comp_result.get("component") == "system_resources":
                        cpu_percent = comp_result.get("metrics", {}).get("cpu_percent")
                        if cpu_percent is not None:
                            cpu_values.append(cpu_percent)

            if len(cpu_values) >= 10:
                # Calculate trend
                trend = self._calculate_trend(cpu_values)
                current_cpu = cpu_values[-1]

                # Predict CPU in next 30 minutes
                predicted_cpu = current_cpu + (trend * 6)  # 6 periods of 5 minutes

                if predicted_cpu > 85 and current_cpu < 75:
                    await self._create_predictive_alert(
                        "cpu_trend_warning",
                        "system",
                        f"CPU usage trending upward. Current: {current_cpu:.1f}%, Predicted: {predicted_cpu:.1f}%",
                        "warning",
                    )

        except Exception as e:
            logger.error(f"Error analyzing CPU trend: {e}")

    async def _analyze_memory_trend(self):
        """Analyze memory usage trends for predictive alerting."""
        try:
            recent_metrics = list(self.metric_history)[-20:]
            memory_values = []

            for metric_point in recent_metrics:
                for comp_result in metric_point["data"].get("component_results", []):
                    if comp_result.get("component") == "system_resources":
                        memory_percent = comp_result.get("metrics", {}).get(
                            "memory_percent"
                        )
                        if memory_percent is not None:
                            memory_values.append(memory_percent)

            if len(memory_values) >= 10:
                trend = self._calculate_trend(memory_values)
                current_memory = memory_values[-1]
                predicted_memory = current_memory + (trend * 6)

                if predicted_memory > 90 and current_memory < 80:
                    await self._create_predictive_alert(
                        "memory_trend_warning",
                        "system",
                        f"Memory usage trending upward. Current: {current_memory:.1f}%, Predicted: {predicted_memory:.1f}%",
                        "warning",
                    )

        except Exception as e:
            logger.error(f"Error analyzing memory trend: {e}")

    async def _analyze_disk_trend(self):
        """Analyze disk usage trends for predictive alerting."""
        # Similar to CPU/memory but for disk space
        pass

    async def _analyze_query_performance_trend(self):
        """Analyze database query performance trends."""
        # Analyze query response times and predict degradation
        pass

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend from values."""
        if len(values) < 2:
            return 0.0

        # Simple linear regression
        n = len(values)
        x_values = list(range(n))

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        return slope

    async def _create_predictive_alert(
        self, alert_id: str, component: str, description: str, severity: str
    ):
        """Create a predictive alert."""
        # Check if we've already sent this type of alert recently
        cutoff_time = datetime.now() - timedelta(hours=1)

        for alert in self.alert_history:
            if (
                alert_id in alert.id
                and datetime.fromisoformat(alert.timestamp) > cutoff_time
            ):
                return  # Don't spam predictive alerts

        alert = Alert(
            id=f"predictive_{alert_id}_{int(time.time())}",
            component=component,
            severity=severity,
            title=f"Predictive Alert: {alert_id}",
            description=description,
            metric_name="trend_analysis",
            current_value=0,
            threshold_value=0,
            tags=["predictive", "trend"],
            timestamp=datetime.now().isoformat(),
        )

        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)

        await self._send_notification(alert, "file")

        logger.info(f"Predictive alert created: {alert.title}")

    async def _alert_cleanup_task(self):
        """Background task to clean up old alerts."""
        while self.running:
            try:
                current_time = datetime.now()

                # Remove very old resolved alerts
                alerts_to_remove = []
                for alert_id, alert in self.active_alerts.items():
                    if alert.resolved and alert.resolved_timestamp:
                        resolved_time = datetime.fromisoformat(alert.resolved_timestamp)
                        if (
                            current_time - resolved_time
                        ).total_seconds() > 3600:  # 1 hour
                            alerts_to_remove.append(alert_id)

                for alert_id in alerts_to_remove:
                    del self.active_alerts[alert_id]

                await asyncio.sleep(3600)  # Clean up every hour

            except Exception as e:
                logger.error(f"Error in alert cleanup: {e}")
                await asyncio.sleep(3600)

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics and summary."""
        current_time = datetime.now()

        # Recent alerts (last 24 hours)
        cutoff_24h = current_time - timedelta(hours=24)
        recent_alerts = [
            alert
            for alert in self.alert_history
            if datetime.fromisoformat(alert.timestamp) > cutoff_24h
        ]

        # Group by severity
        severity_counts = defaultdict(int)
        component_counts = defaultdict(int)

        for alert in recent_alerts:
            severity_counts[alert.severity] += 1
            component_counts[alert.component] += 1

        # Active alerts
        active_by_severity = defaultdict(int)
        for alert in self.active_alerts.values():
            if not alert.resolved:
                active_by_severity[alert.severity] += 1

        return {
            "active_alerts": {
                "total": len(
                    [a for a in self.active_alerts.values() if not a.resolved]
                ),
                "by_severity": dict(active_by_severity),
                "suppressed": len(
                    [a for a in self.active_alerts.values() if a.suppressed]
                ),
            },
            "recent_24h": {
                "total": len(recent_alerts),
                "by_severity": dict(severity_counts),
                "by_component": dict(component_counts),
            },
            "all_time_stats": dict(self.alert_stats),
            "notification_channels": {
                name: {"enabled": channel.enabled, "type": channel.type}
                for name, channel in self.notification_channels.items()
            },
            "timestamp": current_time.isoformat(),
        }

    def export_alert_report(self, file_path: str, hours: int = 24):
        """Export alert report to JSON file."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_alerts = [
            asdict(alert)
            for alert in self.alert_history
            if datetime.fromisoformat(alert.timestamp) > cutoff_time
        ]

        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_hours": hours,
                "total_alerts": len(recent_alerts),
            },
            "active_alerts": [asdict(alert) for alert in self.active_alerts.values()],
            "recent_alerts": recent_alerts,
            "statistics": self.get_alert_statistics(),
            "configuration": {
                "alert_rules": len(self.alert_rules),
                "notification_channels": list(self.notification_channels.keys()),
                "escalation_policies": list(self.escalation_policies.keys()),
            },
        }

        with open(file_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Alert report exported to {file_path}")


# Example usage
async def run_alert_manager_demo():
    """Demo the alert manager with sample data."""
    alert_manager = AlertManager()

    try:
        await alert_manager.start()

        # Simulate health check data that would trigger alerts
        sample_health_data = {
            "component_results": [
                {
                    "component": "system_resources",
                    "status": "warning",
                    "metrics": {
                        "cpu_percent": 85.5,
                        "memory_percent": 78.2,
                        "disk_percent": 65.0,
                    },
                },
                {
                    "component": "postgresql",
                    "status": "warning",
                    "metrics": {"test_query_time_ms": 750.0, "active_connections": 50},
                },
            ]
        }

        # Process the health data
        await alert_manager.process_health_check_data(sample_health_data)

        # Wait a bit for processing
        await asyncio.sleep(5)

        # Get statistics
        stats = alert_manager.get_alert_statistics()
        print("Alert Statistics:")
        print(json.dumps(stats, indent=2))

        # Export report
        report_path = f"/home/opsvi/master_root/ALERT_REPORT_{int(time.time())}.json"
        alert_manager.export_alert_report(report_path)
        print(f"Alert report exported to: {report_path}")

    finally:
        await alert_manager.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_alert_manager_demo())
