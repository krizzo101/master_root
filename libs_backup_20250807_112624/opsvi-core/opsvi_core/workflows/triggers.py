"""
Workflow triggers for OPSVI Core.

Provides trigger management for workflow execution.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from opsvi_foundation import ComponentError, get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class TriggerError(ComponentError):
    """Raised when trigger operations fail."""

    pass


class TriggerType(str, Enum):
    """Types of workflow triggers."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    WEBHOOK = "webhook"
    CONDITION = "condition"


class TriggerStatus(str, Enum):
    """Status of workflow triggers."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


class TriggerDefinition(BaseModel):
    """Definition of a workflow trigger."""

    id: str
    name: str
    type: TriggerType
    workflow_id: str
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TriggerEvent(BaseModel):
    """Event that triggers workflow execution."""

    trigger_id: str
    workflow_id: str
    event_type: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str | None = None


class WorkflowTrigger(ABC):
    """Abstract base class for workflow triggers."""

    def __init__(self, definition: TriggerDefinition):
        """Initialize the trigger."""
        self.definition = definition
        self.status = TriggerStatus.INACTIVE

    @abstractmethod
    async def start(self) -> None:
        """Start the trigger."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the trigger."""
        pass

    @abstractmethod
    async def is_active(self) -> bool:
        """Check if trigger is active."""
        pass

    async def handle_event(self, event: TriggerEvent) -> None:
        """Handle trigger event."""
        logger.info(f"Trigger {self.definition.id} handling event: {event.event_type}")


class ManualTrigger(WorkflowTrigger):
    """Manual trigger for workflow execution."""

    async def start(self) -> None:
        """Start the manual trigger."""
        self.status = TriggerStatus.ACTIVE
        logger.info(f"Manual trigger {self.definition.id} started")

    async def stop(self) -> None:
        """Stop the manual trigger."""
        self.status = TriggerStatus.INACTIVE
        logger.info(f"Manual trigger {self.definition.id} stopped")

    async def is_active(self) -> bool:
        """Check if manual trigger is active."""
        return self.status == TriggerStatus.ACTIVE

    async def trigger_workflow(
        self, variables: dict[str, Any] | None = None
    ) -> TriggerEvent:
        """Manually trigger workflow execution."""
        if not await self.is_active():
            raise TriggerError(f"Manual trigger {self.definition.id} is not active")

        event = TriggerEvent(
            trigger_id=self.definition.id,
            workflow_id=self.definition.workflow_id,
            event_type="manual_trigger",
            data={"variables": variables or {}},
            source="manual",
        )

        await self.handle_event(event)
        return event


class ScheduleTrigger(WorkflowTrigger):
    """Scheduled trigger for workflow execution."""

    def __init__(self, definition: TriggerDefinition):
        """Initialize the schedule trigger."""
        super().__init__(definition)
        self.schedule_config = definition.config
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the schedule trigger."""
        if self._task and not self._task.done():
            return

        self.status = TriggerStatus.ACTIVE
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info(f"Schedule trigger {self.definition.id} started")

    async def stop(self) -> None:
        """Stop the schedule trigger."""
        self.status = TriggerStatus.INACTIVE
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Schedule trigger {self.definition.id} stopped")

    async def is_active(self) -> bool:
        """Check if schedule trigger is active."""
        return (
            self.status == TriggerStatus.ACTIVE and self._task and not self._task.done()
        )

    async def _schedule_loop(self) -> None:
        """Main schedule loop."""
        try:
            interval = self.schedule_config.get("interval", 60)  # Default 60 seconds

            while self.status == TriggerStatus.ACTIVE:
                # Check if it's time to trigger
                if await self._should_trigger():
                    event = TriggerEvent(
                        trigger_id=self.definition.id,
                        workflow_id=self.definition.workflow_id,
                        event_type="scheduled_trigger",
                        data={"schedule_config": self.schedule_config},
                        source="schedule",
                    )
                    await self.handle_event(event)

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info(f"Schedule trigger {self.definition.id} cancelled")
        except Exception as e:
            logger.error(f"Schedule trigger {self.definition.id} error: {e}")
            self.status = TriggerStatus.ERROR

    async def _should_trigger(self) -> bool:
        """Check if trigger should fire based on schedule."""
        # Simple interval-based scheduling
        # In a real implementation, this would support cron expressions, etc.
        return True


class EventTrigger(WorkflowTrigger):
    """Event-based trigger for workflow execution."""

    def __init__(self, definition: TriggerDefinition):
        """Initialize the event trigger."""
        super().__init__(definition)
        self.event_patterns = definition.config.get("patterns", [])
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the event trigger."""
        if self._task and not self._task.done():
            return

        self.status = TriggerStatus.ACTIVE
        self._task = asyncio.create_task(self._event_loop())
        logger.info(f"Event trigger {self.definition.id} started")

    async def stop(self) -> None:
        """Stop the event trigger."""
        self.status = TriggerStatus.INACTIVE
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Event trigger {self.definition.id} stopped")

    async def is_active(self) -> bool:
        """Check if event trigger is active."""
        return (
            self.status == TriggerStatus.ACTIVE and self._task and not self._task.done()
        )

    async def receive_event(self, event: TriggerEvent) -> None:
        """Receive an event for processing."""
        if await self.is_active():
            await self._event_queue.put(event)

    async def _event_loop(self) -> None:
        """Main event processing loop."""
        try:
            while self.status == TriggerStatus.ACTIVE:
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                    # Check if event matches patterns
                    if await self._matches_patterns(event):
                        await self.handle_event(event)

                except TimeoutError:
                    continue

        except asyncio.CancelledError:
            logger.info(f"Event trigger {self.definition.id} cancelled")
        except Exception as e:
            logger.error(f"Event trigger {self.definition.id} error: {e}")
            self.status = TriggerStatus.ERROR

    async def _matches_patterns(self, event: TriggerEvent) -> bool:
        """Check if event matches trigger patterns."""
        if not self.event_patterns:
            return True

        for pattern in self.event_patterns:
            if self._event_matches_pattern(event, pattern):
                return True

        return False

    def _event_matches_pattern(
        self, event: TriggerEvent, pattern: dict[str, Any]
    ) -> bool:
        """Check if event matches a specific pattern."""
        # Simple pattern matching
        # In a real implementation, this would support complex pattern matching
        if "event_type" in pattern and event.event_type != pattern["event_type"]:
            return False

        if "source" in pattern and event.source != pattern["source"]:
            return False

        return True


class WebhookTrigger(WorkflowTrigger):
    """Webhook trigger for workflow execution."""

    def __init__(self, definition: TriggerDefinition):
        """Initialize the webhook trigger."""
        super().__init__(definition)
        self.webhook_config = definition.config
        self._endpoint = self.webhook_config.get("endpoint", "/webhook")
        self._method = self.webhook_config.get("method", "POST")

    async def start(self) -> None:
        """Start the webhook trigger."""
        self.status = TriggerStatus.ACTIVE
        logger.info(f"Webhook trigger {self.definition.id} started at {self._endpoint}")

    async def stop(self) -> None:
        """Stop the webhook trigger."""
        self.status = TriggerStatus.INACTIVE
        logger.info(f"Webhook trigger {self.definition.id} stopped")

    async def is_active(self) -> bool:
        """Check if webhook trigger is active."""
        return self.status == TriggerStatus.ACTIVE

    async def handle_webhook_request(
        self, method: str, path: str, data: dict[str, Any]
    ) -> TriggerEvent:
        """Handle incoming webhook request."""
        if not await self.is_active():
            raise TriggerError(f"Webhook trigger {self.definition.id} is not active")

        if method != self._method or path != self._endpoint:
            raise TriggerError(f"Invalid webhook request: {method} {path}")

        event = TriggerEvent(
            trigger_id=self.definition.id,
            workflow_id=self.definition.workflow_id,
            event_type="webhook_trigger",
            data=data,
            source="webhook",
        )

        await self.handle_event(event)
        return event


class TriggerManager:
    """Manager for workflow triggers."""

    def __init__(self):
        """Initialize the trigger manager."""
        self._triggers: dict[str, WorkflowTrigger] = {}
        self._trigger_registry: dict[TriggerType, type] = {
            TriggerType.MANUAL: ManualTrigger,
            TriggerType.SCHEDULE: ScheduleTrigger,
            TriggerType.EVENT: EventTrigger,
            TriggerType.WEBHOOK: WebhookTrigger,
        }

    def register_trigger(self, definition: TriggerDefinition) -> WorkflowTrigger:
        """
        Register a workflow trigger.

        Args:
            definition: Trigger definition

        Returns:
            Created trigger instance

        Raises:
            TriggerError: If trigger type is not supported
        """
        trigger_class = self._trigger_registry.get(definition.type)
        if not trigger_class:
            raise TriggerError(f"Unsupported trigger type: {definition.type}")

        trigger = trigger_class(definition)
        self._triggers[definition.id] = trigger

        logger.info(f"Registered trigger: {definition.id} ({definition.type})")
        return trigger

    def get_trigger(self, trigger_id: str) -> WorkflowTrigger | None:
        """
        Get a trigger by ID.

        Args:
            trigger_id: ID of the trigger to get

        Returns:
            Trigger instance if found, None otherwise
        """
        return self._triggers.get(trigger_id)

    def list_triggers(self, workflow_id: str | None = None) -> list[WorkflowTrigger]:
        """
        List all triggers.

        Args:
            workflow_id: Filter by workflow ID

        Returns:
            List of trigger instances
        """
        triggers = list(self._triggers.values())
        if workflow_id:
            triggers = [t for t in triggers if t.definition.workflow_id == workflow_id]
        return triggers

    async def start_trigger(self, trigger_id: str) -> None:
        """
        Start a trigger.

        Args:
            trigger_id: ID of the trigger to start

        Raises:
            TriggerError: If trigger not found
        """
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            raise TriggerError(f"Trigger not found: {trigger_id}")

        await trigger.start()

    async def stop_trigger(self, trigger_id: str) -> None:
        """
        Stop a trigger.

        Args:
            trigger_id: ID of the trigger to stop

        Raises:
            TriggerError: If trigger not found
        """
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            raise TriggerError(f"Trigger not found: {trigger_id}")

        await trigger.stop()

    async def start_all_triggers(self) -> None:
        """Start all registered triggers."""
        for trigger in self._triggers.values():
            try:
                await trigger.start()
            except Exception as e:
                logger.error(f"Failed to start trigger {trigger.definition.id}: {e}")

    async def stop_all_triggers(self) -> None:
        """Stop all registered triggers."""
        for trigger in self._triggers.values():
            try:
                await trigger.stop()
            except Exception as e:
                logger.error(f"Failed to stop trigger {trigger.definition.id}: {e}")

    def unregister_trigger(self, trigger_id: str) -> bool:
        """
        Unregister a trigger.

        Args:
            trigger_id: ID of the trigger to unregister

        Returns:
            True if unregistered, False if not found
        """
        if trigger_id in self._triggers:
            trigger = self._triggers[trigger_id]
            asyncio.create_task(trigger.stop())  # Stop trigger asynchronously
            del self._triggers[trigger_id]
            logger.info(f"Unregistered trigger: {trigger_id}")
            return True
        return False

    async def receive_event(self, event: TriggerEvent) -> None:
        """
        Receive an event for processing by event triggers.

        Args:
            event: Event to process
        """
        for trigger in self._triggers.values():
            if isinstance(trigger, EventTrigger):
                await trigger.receive_event(event)

    async def health_check(self) -> bool:
        """Perform health check on all triggers."""
        try:
            active_count = 0
            error_count = 0

            for trigger in self._triggers.values():
                if await trigger.is_active():
                    active_count += 1
                elif trigger.status == TriggerStatus.ERROR:
                    error_count += 1

            logger.debug(
                f"Trigger health check: {active_count} active, {error_count} errors"
            )
            return error_count == 0

        except Exception as e:
            logger.error(f"Trigger health check failed: {e}")
            return False
