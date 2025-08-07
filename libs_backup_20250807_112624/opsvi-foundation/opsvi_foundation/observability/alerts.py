"""
Alert management system for monitoring and notifications.

Provides alert rules, notification channels, escalation policies,
and comprehensive alert management capabilities.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from opsvi_foundation.patterns import ComponentError


class AlertError(ComponentError):
    """Raised when alert operation fails."""


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status values."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    description: str = ""
    condition: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    cooldown: float = 300.0  # 5 minutes
    escalation_delay: float = 1800.0  # 30 minutes
    notification_channels: list[str] = field(default_factory=list)


@dataclass
class Alert:
    """Alert instance."""

    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    acknowledged_at: float | None = None
    resolved_at: float | None = None
    acknowledged_by: str | None = None
    resolved_by: str | None = None


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    def __init__(self, name: str, config: dict[str, Any]):
        """
        Initialize notification channel.

        Args:
            name: Channel name
            config: Channel configuration
        """
        self.name = name
        self.config = config

    @abstractmethod
    async def send_notification(self, alert: Alert, message: str) -> bool:
        """
        Send notification.

        Args:
            alert: Alert to notify about
            message: Notification message

        Returns:
            True if notification sent successfully
        """


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""

    async def send_notification(self, alert: Alert, message: str) -> bool:
        """Send email notification."""
        try:
            # In a real implementation, this would send an email
            # using smtplib or an email service
            print(
                f"Email notification to {self.config.get('recipients', [])}: {message}",
            )
            return True
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""

    async def send_notification(self, alert: Alert, message: str) -> bool:
        """Send Slack notification."""
        try:
            # In a real implementation, this would send a Slack message
            # using the Slack API
            print(
                f"Slack notification to {self.config.get('channel', '#alerts')}: {message}",
            )
            return True
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel."""

    async def send_notification(self, alert: Alert, message: str) -> bool:
        """Send webhook notification."""
        try:
            import httpx

            webhook_url = self.config.get("url")
            if not webhook_url:
                return False

            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "message": message,
                "details": alert.details,
                "timestamp": alert.created_at,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload)
                return response.status_code == 200
        except Exception as e:
            print(f"Failed to send webhook notification: {e}")
            return False


class AlertManager:
    """Main alert management system."""

    def __init__(self):
        """Initialize alert manager."""
        self.rules: dict[str, AlertRule] = {}
        self.alerts: dict[str, Alert] = {}
        self.notification_channels: dict[str, NotificationChannel] = {}
        self.alert_counters: dict[str, int] = {}
        self.last_alert_times: dict[str, float] = {}
        self.escalation_tasks: dict[str, asyncio.Task] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """
        Add alert rule.

        Args:
            rule: Alert rule to add
        """
        self.rules[rule.name] = rule

    def remove_rule(self, name: str) -> None:
        """
        Remove alert rule.

        Args:
            name: Rule name
        """
        self.rules.pop(name, None)

    def add_notification_channel(self, channel: NotificationChannel) -> None:
        """
        Add notification channel.

        Args:
            channel: Notification channel to add
        """
        self.notification_channels[channel.name] = channel

    def remove_notification_channel(self, name: str) -> None:
        """
        Remove notification channel.

        Args:
            name: Channel name
        """
        self.notification_channels.pop(name, None)

    async def create_alert(
        self,
        rule_name: str,
        message: str,
        severity: AlertSeverity | None = None,
        details: dict[str, Any] | None = None,
    ) -> Alert | None:
        """
        Create a new alert.

        Args:
            rule_name: Name of the alert rule
            message: Alert message
            severity: Alert severity (uses rule severity if None)
            details: Additional alert details

        Returns:
            Created alert or None if suppressed
        """
        if rule_name not in self.rules:
            raise AlertError(f"Alert rule '{rule_name}' not found")

        rule = self.rules[rule_name]
        if not rule.enabled:
            return None

        # Check cooldown
        current_time = time.time()
        last_alert_time = self.last_alert_times.get(rule_name, 0)
        if current_time - last_alert_time < rule.cooldown:
            return None

        # Create alert
        import uuid

        alert_id = str(uuid.uuid4())

        alert = Alert(
            id=alert_id,
            rule_name=rule_name,
            severity=severity or rule.severity,
            message=message,
            details=details or {},
            created_at=current_time,
        )

        self.alerts[alert_id] = alert
        self.alert_counters[rule_name] = self.alert_counters.get(rule_name, 0) + 1
        self.last_alert_times[rule_name] = current_time

        # Send notifications
        await self._send_notifications(alert)

        # Schedule escalation
        if rule.escalation_delay > 0:
            self._schedule_escalation(alert, rule)

        return alert

    async def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID
            user: User acknowledging the alert

        Returns:
            True if alert acknowledged successfully
        """
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        if alert.status != AlertStatus.ACTIVE:
            return False

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = time.time()
        alert.acknowledged_by = user

        # Cancel escalation if scheduled
        if alert_id in self.escalation_tasks:
            self.escalation_tasks[alert_id].cancel()
            del self.escalation_tasks[alert_id]

        return True

    async def resolve_alert(self, alert_id: str, user: str) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: Alert ID
            user: User resolving the alert

        Returns:
            True if alert resolved successfully
        """
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        if alert.status == AlertStatus.RESOLVED:
            return False

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = time.time()
        alert.resolved_by = user

        # Cancel escalation if scheduled
        if alert_id in self.escalation_tasks:
            self.escalation_tasks[alert_id].cancel()
            del self.escalation_tasks[alert_id]

        return True

    async def suppress_alert(self, alert_id: str, user: str) -> bool:
        """
        Suppress an alert.

        Args:
            alert_id: Alert ID
            user: User suppressing the alert

        Returns:
            True if alert suppressed successfully
        """
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        if alert.status == AlertStatus.SUPPRESSED:
            return False

        alert.status = AlertStatus.SUPPRESSED

        # Cancel escalation if scheduled
        if alert_id in self.escalation_tasks:
            self.escalation_tasks[alert_id].cancel()
            del self.escalation_tasks[alert_id]

        return True

    async def _send_notifications(self, alert: Alert) -> None:
        """Send notifications for an alert."""
        rule = self.rules[alert.rule_name]

        for channel_name in rule.notification_channels:
            if channel_name in self.notification_channels:
                channel = self.notification_channels[channel_name]

                # Create notification message
                message = self._format_notification_message(alert)

                try:
                    await channel.send_notification(alert, message)
                except Exception as e:
                    print(f"Failed to send notification via {channel_name}: {e}")

    def _format_notification_message(self, alert: Alert) -> str:
        """Format notification message."""
        rule = self.rules[alert.rule_name]

        message = f"[{alert.severity.value.upper()}] {rule.name}\n"
        message += f"Message: {alert.message}\n"
        message += f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.created_at))}\n"

        if alert.details:
            message += f"Details: {alert.details}\n"

        return message

    def _schedule_escalation(self, alert: Alert, rule: AlertRule) -> None:
        """Schedule alert escalation."""

        async def escalate():
            await asyncio.sleep(rule.escalation_delay)

            # Check if alert is still active
            if (
                alert.id in self.alerts
                and self.alerts[alert.id].status == AlertStatus.ACTIVE
            ):
                # Escalate by sending notifications again
                await self._send_notifications(alert)

        self.escalation_tasks[alert.id] = asyncio.create_task(escalate())

    def get_active_alerts(self) -> list[Alert]:
        """Get all active alerts."""
        return [
            alert
            for alert in self.alerts.values()
            if alert.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]
        ]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> list[Alert]:
        """Get alerts by severity."""
        return [alert for alert in self.alerts.values() if alert.severity == severity]

    def get_alerts_by_rule(self, rule_name: str) -> list[Alert]:
        """Get alerts by rule name."""
        return [alert for alert in self.alerts.values() if alert.rule_name == rule_name]

    def get_alert_summary(self) -> dict[str, Any]:
        """Get alert summary."""
        active_alerts = self.get_active_alerts()

        summary = {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "alerts_by_severity": {},
            "alerts_by_rule": {},
            "alert_counters": self.alert_counters.copy(),
        }

        # Count by severity
        for severity in AlertSeverity:
            summary["alerts_by_severity"][severity.value] = len(
                self.get_alerts_by_severity(severity),
            )

        # Count by rule
        for rule_name in self.rules:
            summary["alerts_by_rule"][rule_name] = len(
                self.get_alerts_by_rule(rule_name),
            )

        return summary


class AlertEvaluator:
    """Evaluates conditions and triggers alerts."""

    def __init__(self, alert_manager: AlertManager):
        """
        Initialize alert evaluator.

        Args:
            alert_manager: Alert manager instance
        """
        self.alert_manager = alert_manager
        self.evaluation_functions: dict[str, Callable] = {}

    def register_evaluation_function(self, name: str, func: Callable) -> None:
        """
        Register an evaluation function.

        Args:
            name: Function name
            func: Evaluation function
        """
        self.evaluation_functions[name] = func

    async def evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """
        Evaluate a condition string.

        Args:
            condition: Condition string to evaluate
            context: Context data for evaluation

        Returns:
            True if condition is met
        """
        try:
            # Simple condition evaluation
            # In a real implementation, this would use a proper expression evaluator
            if condition.startswith("threshold:"):
                # Threshold-based condition
                parts = condition.split(":")
                if len(parts) >= 3:
                    metric = parts[1]
                    operator = parts[2]
                    value = float(parts[3]) if len(parts) > 3 else 0

                    current_value = context.get(metric, 0)

                    if operator == "gt":
                        return current_value > value
                    if operator == "lt":
                        return current_value < value
                    if operator == "eq":
                        return current_value == value
                    if operator == "gte":
                        return current_value >= value
                    if operator == "lte":
                        return current_value <= value

            elif condition.startswith("custom:"):
                # Custom function condition
                func_name = condition.split(":")[1]
                if func_name in self.evaluation_functions:
                    func = self.evaluation_functions[func_name]
                    if asyncio.iscoroutinefunction(func):
                        return await func(context)
                    return func(context)

            return False
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False

    async def evaluate_all_rules(self, context: dict[str, Any]) -> None:
        """
        Evaluate all alert rules.

        Args:
            context: Context data for evaluation
        """
        for rule_name, rule in self.alert_manager.rules.items():
            if not rule.enabled:
                continue

            try:
                condition_met = await self.evaluate_condition(rule.condition, context)

                if condition_met:
                    await self.alert_manager.create_alert(
                        rule_name=rule_name,
                        message=f"Condition '{rule.condition}' met",
                        details=context,
                    )
            except Exception as e:
                print(f"Error evaluating rule '{rule_name}': {e}")


# Global alert manager
alert_manager = AlertManager()


def alert_rule(
    name: str,
    condition: str,
    severity: AlertSeverity = AlertSeverity.WARNING,
    description: str = "",
    cooldown: float = 300.0,
    escalation_delay: float = 1800.0,
    notification_channels: list[str] | None = None,
):
    """
    Decorator for creating alert rules from functions.

    Args:
        name: Alert rule name
        condition: Alert condition
        severity: Alert severity
        description: Alert description
        cooldown: Alert cooldown in seconds
        escalation_delay: Escalation delay in seconds
        notification_channels: List of notification channel names
    """

    def decorator(func):
        rule = AlertRule(
            name=name,
            description=description,
            condition=condition,
            severity=severity,
            cooldown=cooldown,
            escalation_delay=escalation_delay,
            notification_channels=notification_channels or [],
        )
        alert_manager.add_rule(rule)
        return func

    return decorator
