#!/usr/bin/env python3
"""
Real-Time Monitoring Example
============================

This example demonstrates real-time monitoring and alerting
capabilities for continuous surveillance and notification.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python real_time_monitoring.py
"""

import asyncio
import hashlib
import json
import logging
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    EmailVerificationRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MonitorType(Enum):
    """Types of monitoring."""

    PERSON = "person"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    BUSINESS = "business"


class Alert:
    """Alert data structure."""

    def __init__(
        self,
        monitor_id: str,
        level: AlertLevel,
        title: str,
        description: str,
        data: Dict[str, Any],
    ):
        self.id = hashlib.sha256(
            f"{monitor_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        self.monitor_id = monitor_id
        self.level = level
        self.title = title
        self.description = description
        self.data = data
        self.timestamp = datetime.now()
        self.acknowledged = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "monitor_id": self.monitor_id,
            "level": self.level.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }


class Monitor:
    """Individual monitoring task."""

    def __init__(
        self,
        monitor_id: str,
        monitor_type: MonitorType,
        target: Dict[str, Any],
        check_interval: int = 3600,  # seconds
        alert_conditions: Optional[List[Dict]] = None,
    ):
        self.monitor_id = monitor_id
        self.monitor_type = monitor_type
        self.target = target
        self.check_interval = check_interval
        self.alert_conditions = alert_conditions or []
        self.last_check = None
        self.last_data = None
        self.check_count = 0
        self.alerts = []
        self.active = True

    def should_check(self) -> bool:
        """Check if it's time for next check."""
        if not self.active:
            return False

        if self.last_check is None:
            return True

        elapsed = (datetime.now() - self.last_check).total_seconds()
        return elapsed >= self.check_interval

    def add_alert(self, alert: Alert):
        """Add alert to monitor."""
        self.alerts.append(alert)


class RealTimeMonitor:
    """Real-time monitoring system."""

    def __init__(self):
        self.client = SleuthIntel()
        self.monitors: Dict[str, Monitor] = {}
        self.alerts: deque = deque(maxlen=1000)
        self.alert_handlers: List[Callable] = []
        self.running = False
        self.stats = {
            "monitors_active": 0,
            "total_checks": 0,
            "total_alerts": 0,
            "alerts_by_level": {
                AlertLevel.INFO.value: 0,
                AlertLevel.WARNING.value: 0,
                AlertLevel.CRITICAL.value: 0,
            },
        }

    def add_monitor(
        self,
        monitor_type: MonitorType,
        target: Dict[str, Any],
        check_interval: int = 3600,
        alert_conditions: Optional[List[Dict]] = None,
    ) -> str:
        """
        Add a new monitoring task.

        Args:
            monitor_type: Type of monitoring
            target: Target information to monitor
            check_interval: Check interval in seconds
            alert_conditions: List of alert condition rules

        Returns:
            Monitor ID
        """
        monitor_id = hashlib.sha256(
            f"{monitor_type.value}{target}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        monitor = Monitor(
            monitor_id=monitor_id,
            monitor_type=monitor_type,
            target=target,
            check_interval=check_interval,
            alert_conditions=alert_conditions,
        )

        self.monitors[monitor_id] = monitor
        self.stats["monitors_active"] = len(self.monitors)

        logger.info(f"Added monitor {monitor_id} for {monitor_type.value}")

        return monitor_id

    def remove_monitor(self, monitor_id: str):
        """Remove a monitor."""
        if monitor_id in self.monitors:
            self.monitors[monitor_id].active = False
            del self.monitors[monitor_id]
            self.stats["monitors_active"] = len(self.monitors)
            logger.info(f"Removed monitor {monitor_id}")

    def add_alert_handler(self, handler: Callable):
        """Add custom alert handler."""
        self.alert_handlers.append(handler)

    async def start(self, duration: Optional[int] = None):
        """
        Start monitoring system.

        Args:
            duration: Optional duration in seconds to run
        """
        self.running = True
        start_time = datetime.now()

        print(f"\n🚨 Real-Time Monitoring Started")
        print(f"Active Monitors: {len(self.monitors)}")
        print("=" * 60)

        try:
            while self.running:
                # Check if duration exceeded
                if duration:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= duration:
                        print(f"\n⏱️ Duration limit reached ({duration}s)")
                        break

                # Check all monitors
                await self._check_monitors()

                # Display status
                self._display_status()

                # Wait before next cycle
                await asyncio.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            print("\n⚠️ Monitoring interrupted")

        finally:
            self.running = False
            await self._shutdown()

    async def _check_monitors(self):
        """Check all active monitors."""
        for monitor_id, monitor in self.monitors.items():
            if monitor.should_check():
                await self._check_monitor(monitor)

    async def _check_monitor(self, monitor: Monitor):
        """Check individual monitor."""
        try:
            monitor.last_check = datetime.now()
            monitor.check_count += 1
            self.stats["total_checks"] += 1

            # Perform check based on monitor type
            if monitor.monitor_type == MonitorType.PERSON:
                data = await self._check_person(monitor.target)
            elif monitor.monitor_type == MonitorType.PHONE:
                data = await self._check_phone(monitor.target)
            elif monitor.monitor_type == MonitorType.EMAIL:
                data = await self._check_email(monitor.target)
            elif monitor.monitor_type == MonitorType.ADDRESS:
                data = await self._check_address(monitor.target)
            else:
                logger.warning(f"Unknown monitor type: {monitor.monitor_type}")
                return

            # Compare with last data
            changes = self._detect_changes(monitor.last_data, data)

            # Evaluate alert conditions
            alerts = self._evaluate_conditions(monitor, data, changes)

            # Process alerts
            for alert in alerts:
                await self._process_alert(monitor, alert)

            # Update monitor data
            monitor.last_data = data

        except Exception as e:
            logger.error(f"Error checking monitor {monitor.monitor_id}: {e}")

            # Create error alert
            alert = Alert(
                monitor_id=monitor.monitor_id,
                level=AlertLevel.WARNING,
                title="Monitor Check Failed",
                description=f"Failed to check monitor: {str(e)}",
                data={"error": str(e)},
            )
            await self._process_alert(monitor, alert)

    async def _check_person(self, target: Dict) -> Dict[str, Any]:
        """Check person information."""
        request = PersonSearchRequest(
            first_name=target.get("first_name"),
            last_name=target.get("last_name"),
            date_of_birth=target.get("date_of_birth"),
            city=target.get("city"),
            state=target.get("state"),
        )

        response = await self.client.person_search(request)

        if response.success and response.results:
            person = response.results[0]
            return {
                "found": True,
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}",
                "age": person.get("age"),
                "addresses": person.get("addresses", []),
                "phones": person.get("phones", []),
                "emails": person.get("emails", []),
                "relatives": len(person.get("relatives", [])),
                "associates": len(person.get("associates", [])),
            }

        return {"found": False}

    async def _check_phone(self, target: Dict) -> Dict[str, Any]:
        """Check phone information."""
        request = PhoneLookupRequest(phone=target.get("phone"))
        response = await self.client.phone_lookup(request)

        if response.success:
            return {
                "valid": response.is_valid,
                "type": response.phone_type,
                "carrier": response.carrier,
                "owner": response.owner_info,
                "location": response.location_info,
            }

        return {"valid": False}

    async def _check_email(self, target: Dict) -> Dict[str, Any]:
        """Check email information."""
        request = EmailVerificationRequest(email=target.get("email"))
        response = await self.client.email_verification(request)

        if response.success:
            return {
                "valid": response.is_valid,
                "deliverable": response.is_deliverable,
                "disposable": response.is_disposable,
                "domain": response.domain,
                "social_profiles": response.social_profiles,
            }

        return {"valid": False}

    async def _check_address(self, target: Dict) -> Dict[str, Any]:
        """Check address information."""
        request = AddressSearchRequest(
            address=target.get("address"),
            city=target.get("city"),
            state=target.get("state"),
            zip_code=target.get("zip_code"),
        )

        response = await self.client.address_search(request)

        if response.success:
            return {
                "valid": True,
                "formatted_address": response.formatted_address,
                "residents": response.residents,
                "property_info": response.property_info,
            }

        return {"valid": False}

    def _detect_changes(
        self, old_data: Optional[Dict], new_data: Dict
    ) -> Dict[str, Any]:
        """Detect changes between data snapshots."""
        if not old_data:
            return {"first_check": True}

        changes = {}

        # Check for new or removed keys
        old_keys = set(old_data.keys())
        new_keys = set(new_data.keys())

        added_keys = new_keys - old_keys
        removed_keys = old_keys - new_keys

        if added_keys:
            changes["added_fields"] = list(added_keys)
        if removed_keys:
            changes["removed_fields"] = list(removed_keys)

        # Check for value changes
        for key in old_keys & new_keys:
            if old_data[key] != new_data[key]:
                changes[f"changed_{key}"] = {"old": old_data[key], "new": new_data[key]}

        return changes

    def _evaluate_conditions(
        self, monitor: Monitor, data: Dict, changes: Dict
    ) -> List[Alert]:
        """Evaluate alert conditions."""
        alerts = []

        # Default conditions
        if changes.get("first_check"):
            alerts.append(
                Alert(
                    monitor_id=monitor.monitor_id,
                    level=AlertLevel.INFO,
                    title="Initial Check Complete",
                    description="First monitoring check completed",
                    data=data,
                )
            )

        # Check for significant changes
        if "changed_addresses" in changes:
            alerts.append(
                Alert(
                    monitor_id=monitor.monitor_id,
                    level=AlertLevel.WARNING,
                    title="Address Change Detected",
                    description="Subject has new or changed addresses",
                    data=changes["changed_addresses"],
                )
            )

        if "changed_phones" in changes:
            alerts.append(
                Alert(
                    monitor_id=monitor.monitor_id,
                    level=AlertLevel.INFO,
                    title="Phone Change Detected",
                    description="Phone numbers have changed",
                    data=changes["changed_phones"],
                )
            )

        # Custom conditions
        for condition in monitor.alert_conditions:
            if self._evaluate_condition(condition, data, changes):
                alerts.append(
                    Alert(
                        monitor_id=monitor.monitor_id,
                        level=AlertLevel(condition.get("level", "info")),
                        title=condition.get("title", "Custom Alert"),
                        description=condition.get(
                            "description", "Custom condition triggered"
                        ),
                        data={"condition": condition, "data": data},
                    )
                )

        return alerts

    def _evaluate_condition(self, condition: Dict, data: Dict, changes: Dict) -> bool:
        """Evaluate a single condition."""
        # Simple field-based conditions
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if field and field in data:
            field_value = data[field]

            if operator == "equals":
                return field_value == value
            elif operator == "not_equals":
                return field_value != value
            elif operator == "contains":
                return value in str(field_value)
            elif operator == "greater_than":
                return field_value > value
            elif operator == "less_than":
                return field_value < value
            elif operator == "changed":
                return f"changed_{field}" in changes

        return False

    async def _process_alert(self, monitor: Monitor, alert: Alert):
        """Process and dispatch alert."""
        # Add to monitor
        monitor.add_alert(alert)

        # Add to global alerts
        self.alerts.append(alert)

        # Update statistics
        self.stats["total_alerts"] += 1
        self.stats["alerts_by_level"][alert.level.value] += 1

        # Log alert
        logger.info(f"Alert [{alert.level.value}]: {alert.title} - {alert.description}")

        # Display alert
        self._display_alert(alert)

        # Call custom handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

    def _display_alert(self, alert: Alert):
        """Display alert to console."""
        symbols = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
        }

        print(f"\n{symbols[alert.level]} ALERT [{alert.level.value.upper()}]")
        print(f"   Monitor: {alert.monitor_id}")
        print(f"   Title: {alert.title}")
        print(f"   Description: {alert.description}")
        print(f"   Time: {alert.timestamp:%Y-%m-%d %H:%M:%S}")

    def _display_status(self):
        """Display monitoring status."""
        # Only display periodically to avoid clutter
        if self.stats["total_checks"] % 10 == 0:
            print(
                f"\n📊 Status: Monitors={self.stats['monitors_active']} | "
                f"Checks={self.stats['total_checks']} | "
                f"Alerts={self.stats['total_alerts']}",
                end="\r",
            )

    async def _shutdown(self):
        """Shutdown monitoring system."""
        print("\n\n🛑 Shutting down monitoring system...")

        # Save alerts
        if self.alerts:
            alerts_file = f"monitoring_alerts_{datetime.now():%Y%m%d_%H%M%S}.json"
            with open(alerts_file, "w") as f:
                json.dump([a.to_dict() for a in self.alerts], f, indent=2)
            print(f"💾 Alerts saved to: {alerts_file}")

        # Display summary
        print("\n" + "=" * 60)
        print("MONITORING SUMMARY")
        print("=" * 60)
        print(f"Total Monitors: {len(self.monitors)}")
        print(f"Total Checks: {self.stats['total_checks']}")
        print(f"Total Alerts: {self.stats['total_alerts']}")
        print("\nAlerts by Level:")
        for level, count in self.stats["alerts_by_level"].items():
            print(f"  • {level.upper()}: {count}")

        await self.client.close()


class WebhookAlertHandler:
    """Send alerts to webhook endpoints."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def handle(self, alert: Alert):
        """Send alert to webhook."""
        # This would send HTTP POST to webhook
        logger.info(f"Would send alert {alert.id} to webhook: {self.webhook_url}")


class EmailAlertHandler:
    """Send alerts via email."""

    def __init__(self, email_addresses: List[str]):
        self.email_addresses = email_addresses

    async def handle(self, alert: Alert):
        """Send alert via email."""
        # This would send email notification
        logger.info(f"Would email alert {alert.id} to {self.email_addresses}")


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Real-Time Monitoring Example")
    print("=" * 60)

    monitor = RealTimeMonitor()

    # Example 1: Monitor person
    print("\n📌 Example 1: Person Monitoring")
    print("-" * 40)

    person_monitor_id = monitor.add_monitor(
        monitor_type=MonitorType.PERSON,
        target={
            "first_name": "John",
            "last_name": "Smith",
            "city": "Los Angeles",
            "state": "CA",
        },
        check_interval=30,  # Check every 30 seconds for demo
        alert_conditions=[
            {
                "field": "addresses",
                "operator": "changed",
                "level": "warning",
                "title": "Address Change",
                "description": "Person's address information has changed",
            }
        ],
    )

    print(f"✅ Added person monitor: {person_monitor_id}")

    # Example 2: Monitor phone
    print("\n📌 Example 2: Phone Monitoring")
    print("-" * 40)

    phone_monitor_id = monitor.add_monitor(
        monitor_type=MonitorType.PHONE,
        target={"phone": "5551234567"},
        check_interval=60,
        alert_conditions=[
            {
                "field": "valid",
                "operator": "equals",
                "value": False,
                "level": "critical",
                "title": "Phone Invalid",
                "description": "Phone number is no longer valid",
            }
        ],
    )

    print(f"✅ Added phone monitor: {phone_monitor_id}")

    # Example 3: Monitor email
    print("\n📌 Example 3: Email Monitoring")
    print("-" * 40)

    email_monitor_id = monitor.add_monitor(
        monitor_type=MonitorType.EMAIL,
        target={"email": "test@example.com"},
        check_interval=45,
        alert_conditions=[
            {
                "field": "deliverable",
                "operator": "equals",
                "value": False,
                "level": "warning",
                "title": "Email Undeliverable",
                "description": "Email is no longer deliverable",
            }
        ],
    )

    print(f"✅ Added email monitor: {email_monitor_id}")

    # Add custom alert handlers
    webhook_handler = WebhookAlertHandler("https://example.com/alerts")
    monitor.add_alert_handler(webhook_handler.handle)

    email_handler = EmailAlertHandler(["admin@example.com"])
    monitor.add_alert_handler(email_handler.handle)

    # Start monitoring (run for 2 minutes for demo)
    print("\n🚀 Starting real-time monitoring (2 minute demo)...")
    print("Press Ctrl+C to stop early")

    try:
        await monitor.start(duration=120)
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring stopped by user")

    print("\n✨ Monitoring example completed!")


if __name__ == "__main__":
    asyncio.run(main())
