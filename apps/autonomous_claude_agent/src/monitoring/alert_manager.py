"""
Alert management system for monitoring and notifications.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import hashlib
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from ..utils.logger import get_logger

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def priority(self) -> int:
        """Get numeric priority (higher = more severe)."""
        priorities = {self.INFO: 1, self.WARNING: 2, self.ERROR: 3, self.CRITICAL: 4}
        return priorities[self]


@dataclass
class Alert:
    """Alert definition."""

    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        if self.acknowledged_at:
            data["acknowledged_at"] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            data["resolved_at"] = self.resolved_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        """Create from dictionary."""
        data = data.copy()
        data["severity"] = AlertSeverity(data["severity"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("acknowledged_at"):
            data["acknowledged_at"] = datetime.fromisoformat(data["acknowledged_at"])
        if data.get("resolved_at"):
            data["resolved_at"] = datetime.fromisoformat(data["resolved_at"])
        return cls(**data)


@dataclass
class AlertRule:
    """Alert rule definition."""

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    title_template: str
    message_template: str
    cooldown: timedelta = timedelta(minutes=5)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.name)


class NotificationChannel:
    """Base class for notification channels."""

    async def send(self, alert: Alert) -> bool:
        """Send alert notification."""
        raise NotImplementedError


class WebhookChannel(NotificationChannel):
    """Webhook notification channel."""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}

    async def send(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"alert": alert.to_dict(), "timestamp": datetime.utcnow().isoformat()}

                async with session.post(self.url, json=payload, headers=self.headers) as response:
                    success = response.status == 200
                    if not success:
                        logger.error(f"Webhook failed: {response.status}")
                    return success

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False


class EmailChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addrs: List[str],
        use_tls: bool = True,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.use_tls = use_tls

    async def send(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            # Create HTML content
            html_content = f"""
            <html>
                <body>
                    <h2 style="color: {'red' if alert.severity == AlertSeverity.CRITICAL else 'orange'};">
                        {alert.title}
                    </h2>
                    <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                    <p><strong>Time:</strong> {alert.timestamp.isoformat()}</p>
                    <p><strong>Source:</strong> {alert.source}</p>
                    <hr>
                    <p>{alert.message}</p>
                    {self._format_metadata(alert.metadata)}
                </body>
            </html>
            """

            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as HTML."""
        if not metadata:
            return ""

        html = "<h3>Additional Information:</h3><ul>"
        for key, value in metadata.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html


class SlackChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        try:
            # Map severity to color
            colors = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900",
                AlertSeverity.ERROR: "#ff0000",
                AlertSeverity.CRITICAL: "#800000",
            }

            # Create Slack message
            payload = {
                "attachments": [
                    {
                        "color": colors.get(alert.severity, "#808080"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {"title": "Source", "value": alert.source, "short": True},
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": False,
                            },
                        ],
                        "footer": "Autonomous Agent Alert System",
                        "ts": int(alert.timestamp.timestamp()),
                    }
                ]
            }

            # Add metadata fields
            if alert.metadata:
                for key, value in alert.metadata.items():
                    payload["attachments"][0]["fields"].append(
                        {"title": key, "value": str(value), "short": len(str(value)) < 20}
                    )

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.rules: Set[AlertRule] = set()
        self.channels: List[NotificationChannel] = []
        self.rule_cooldowns: Dict[str, datetime] = {}
        self.lock = asyncio.Lock()

        # Alert history
        self.history: List[Alert] = []
        self.max_history = 1000

        # Deduplication
        self.dedup_cache: Dict[str, datetime] = {}
        self.dedup_window = timedelta(minutes=5)

    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.add(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def add_channel(self, channel: NotificationChannel):
        """Add a notification channel."""
        self.channels.append(channel)
        logger.info(f"Added notification channel: {channel.__class__.__name__}")

    async def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str = "manual",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Create and register a new alert."""
        # Generate alert ID
        alert_id = self._generate_alert_id(title, message)

        # Check for deduplication
        if await self._is_duplicate(alert_id):
            logger.debug(f"Suppressing duplicate alert: {title}")
            return None

        # Create alert
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            message=message,
            source=source,
            metadata=metadata or {},
        )

        async with self.lock:
            # Store alert
            self.alerts[alert_id] = alert
            self.history.append(alert)

            # Trim history
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history :]

            # Update dedup cache
            self.dedup_cache[alert_id] = datetime.utcnow()

        # Send notifications
        await self._send_notifications(alert)

        logger.info(f"Created alert: {alert.title} (severity: {alert.severity.value})")
        return alert

    async def evaluate_rules(self, metrics: Dict[str, Any]):
        """Evaluate alert rules against metrics."""
        for rule in self.rules:
            try:
                # Check cooldown
                if rule.name in self.rule_cooldowns:
                    if datetime.utcnow() - self.rule_cooldowns[rule.name] < rule.cooldown:
                        continue

                # Evaluate condition
                if rule.condition(metrics):
                    # Format title and message
                    title = rule.title_template.format(**metrics)
                    message = rule.message_template.format(**metrics)

                    # Create alert
                    alert = await self.create_alert(
                        severity=rule.severity,
                        title=title,
                        message=message,
                        source=f"rule:{rule.name}",
                        metadata={**rule.metadata, **metrics},
                    )

                    if alert:
                        # Update cooldown
                        self.rule_cooldowns[rule.name] = datetime.utcnow()

            except Exception as e:
                logger.error(f"Failed to evaluate rule {rule.name}: {e}")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert."""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by

        logger.info(f"Alert acknowledged: {alert.title}")
        return True

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()

        # Remove from active alerts
        del self.alerts[alert_id]

        logger.info(f"Alert resolved: {alert.title}")
        return True

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None, source: Optional[str] = None
    ) -> List[Alert]:
        """Get active alerts with optional filtering."""
        alerts = list(self.alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if source:
            alerts = [a for a in alerts if a.source == source]

        # Sort by severity and timestamp
        alerts.sort(key=lambda a: (-a.severity.priority, a.timestamp))

        return alerts

    def get_alert_history(
        self, duration: Optional[timedelta] = None, limit: int = 100
    ) -> List[Alert]:
        """Get alert history."""
        history = self.history.copy()

        if duration:
            cutoff = datetime.utcnow() - duration
            history = [a for a in history if a.timestamp >= cutoff]

        return history[-limit:]

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications to all channels."""
        if not self.channels:
            logger.warning("No notification channels configured")
            return

        # Send to all channels concurrently
        tasks = [channel.send(alert) for channel in self.channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results
        for channel, result in zip(self.channels, results):
            if isinstance(result, Exception):
                logger.error(f"Notification failed for {channel.__class__.__name__}: {result}")
            elif not result:
                logger.warning(f"Notification failed for {channel.__class__.__name__}")

    def _generate_alert_id(self, title: str, message: str) -> str:
        """Generate unique alert ID."""
        content = f"{title}:{message}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _is_duplicate(self, alert_id: str) -> bool:
        """Check if alert is a duplicate within dedup window."""
        async with self.lock:
            if alert_id not in self.dedup_cache:
                return False

            last_seen = self.dedup_cache[alert_id]
            if datetime.utcnow() - last_seen < self.dedup_window:
                return True

            # Clean old entries
            cutoff = datetime.utcnow() - self.dedup_window
            self.dedup_cache = {k: v for k, v in self.dedup_cache.items() if v > cutoff}

            return False

    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()
        logger.info("Cleared all alerts")

    def export_alerts(self, format: str = "json") -> str:
        """Export alerts in specified format."""
        alerts_data = [alert.to_dict() for alert in self.get_active_alerts()]

        if format == "json":
            return json.dumps(alerts_data, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")


# Example usage
if __name__ == "__main__":

    async def example():
        # Create alert manager
        manager = AlertManager()

        # Add webhook channel
        webhook = WebhookChannel("https://example.com/webhook")
        manager.add_channel(webhook)

        # Add alert rules
        high_cpu_rule = AlertRule(
            name="high_cpu",
            condition=lambda m: m.get("cpu_usage", 0) > 80,
            severity=AlertSeverity.WARNING,
            title_template="High CPU Usage: {cpu_usage:.1f}%",
            message_template="CPU usage has exceeded 80% threshold",
            cooldown=timedelta(minutes=10),
        )
        manager.add_rule(high_cpu_rule)

        # Create manual alert
        alert = await manager.create_alert(
            severity=AlertSeverity.ERROR,
            title="Test Alert",
            message="This is a test alert",
            metadata={"component": "test", "value": 42},
        )

        # Evaluate rules with metrics
        await manager.evaluate_rules({"cpu_usage": 85.5})

        # Get active alerts
        print("Active alerts:")
        for alert in manager.get_active_alerts():
            print(f"  - [{alert.severity.value}] {alert.title}")

        # Acknowledge alert
        if alert:
            manager.acknowledge_alert(alert.id)

        # Export alerts
        print("\nExported alerts:")
        print(manager.export_alerts())

    asyncio.run(example())
