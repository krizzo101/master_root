"""
Event Processors

Automated event handling and response system that implements
business logic for coordination, load balancing, and failure recovery.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .event_bus import EventBus, get_global_event_bus
from .event_types import (
    BaseEvent,
    CoordinationEvent,
    ErrorEvent,
    EventType,
    Priority,
    ProgressEvent,
    create_help_request_event,
    create_progress_event,
    create_task_handoff_event,
)

logger = logging.getLogger(__name__)


class ProcessorStatus(Enum):
    """Event processor status"""

    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ProcessingRule:
    """Rule for event processing"""

    rule_id: str
    event_types: List[EventType]
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    priority: int = 1
    enabled: bool = True
    max_retries: int = 3
    cooldown_seconds: int = 30


class EventProcessor(ABC):
    """Base class for event processors"""

    def __init__(
        self,
        processor_id: str,
        event_bus: Optional[EventBus] = None,
        enabled: bool = True,
    ):
        self.processor_id = processor_id
        self.event_bus = event_bus or get_global_event_bus()
        self.enabled = enabled
        self.status = ProcessorStatus.IDLE
        self.processed_count = 0
        self.error_count = 0
        self.last_processed = 0.0
        self.processing_times: List[float] = []

        # Subscribe to relevant events
        self.subscription_id = self.event_bus.subscribe(
            self._process_event, event_types=self.get_handled_event_types()
        )

        logger.info(f"EventProcessor {processor_id} initialized")

    @abstractmethod
    def get_handled_event_types(self) -> List[EventType]:
        """Return list of event types this processor handles"""
        pass

    @abstractmethod
    async def process_event(self, event: BaseEvent) -> None:
        """Process a single event"""
        pass

    def should_process_event(self, event: BaseEvent) -> bool:
        """Check if this processor should handle the event"""
        return self.enabled and event.event_type in self.get_handled_event_types()

    async def _process_event(self, event: BaseEvent) -> None:
        """Internal event processing with error handling and metrics"""
        if not self.should_process_event(event):
            return

        start_time = time.time()
        self.status = ProcessorStatus.PROCESSING

        try:
            await self.process_event(event)

            # Update metrics
            self.processed_count += 1
            self.last_processed = time.time()
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)

            # Keep only recent processing times
            if len(self.processing_times) > 100:
                self.processing_times = self.processing_times[-100:]

            logger.debug(
                f"Processor {self.processor_id} processed event {event.event_id} "
                f"in {processing_time:.3f}s"
            )

        except Exception as e:
            self.error_count += 1
            self.status = ProcessorStatus.ERROR
            logger.error(
                f"Processor {self.processor_id} failed to process event "
                f"{event.event_id}: {e}"
            )
        finally:
            self.status = ProcessorStatus.IDLE

    def get_metrics(self) -> Dict[str, Any]:
        """Get processor performance metrics"""
        return {
            "processor_id": self.processor_id,
            "status": self.status.value,
            "enabled": self.enabled,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "last_processed": self.last_processed,
            "avg_processing_time": (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times
                else 0.0
            ),
            "error_rate": (
                self.error_count / max(1, self.processed_count + self.error_count)
            ),
        }

    def enable(self) -> None:
        """Enable the processor"""
        self.enabled = True
        logger.info(f"Processor {self.processor_id} enabled")

    def disable(self) -> None:
        """Disable the processor"""
        self.enabled = False
        logger.info(f"Processor {self.processor_id} disabled")

    def shutdown(self) -> None:
        """Shutdown the processor"""
        self.enabled = False
        self.status = ProcessorStatus.STOPPED
        if self.subscription_id:
            self.event_bus.unsubscribe(self.subscription_id)
        logger.info(f"Processor {self.processor_id} shutdown")


class TaskHandoffProcessor(EventProcessor):
    """Processes task handoff events for intelligent routing"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("task_handoff_processor", event_bus)
        self.agent_workloads: Dict[str, int] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.handoff_history: List[Dict[str, Any]] = []

    def get_handled_event_types(self) -> List[EventType]:
        return [EventType.TASK_HANDOFF, EventType.AGENT_AVAILABLE]

    async def process_event(self, event: BaseEvent) -> None:
        if event.event_type == EventType.TASK_HANDOFF:
            await self._process_task_handoff(event)
        elif event.event_type == EventType.AGENT_AVAILABLE:
            await self._update_agent_availability(event)

    async def _process_task_handoff(self, event: BaseEvent) -> None:
        """Process task handoff and optimize routing"""
        if not isinstance(event, CoordinationEvent):
            return

        logger.info(
            f"Processing task handoff from {event.source_agent_id} "
            f"to {event.target_agent_ids}"
        )

        # Update workload tracking
        if event.source_agent_id in self.agent_workloads:
            self.agent_workloads[event.source_agent_id] -= 1

        for target_id in event.target_agent_ids:
            self.agent_workloads[target_id] = self.agent_workloads.get(target_id, 0) + 1

        # Record handoff
        self.handoff_history.append(
            {
                "timestamp": time.time(),
                "source": event.source_agent_id,
                "targets": event.target_agent_ids,
                "task_id": event.task_id,
            }
        )

        # Keep history size manageable
        if len(self.handoff_history) > 1000:
            self.handoff_history = self.handoff_history[-1000:]

        # Check for potential load balancing issues
        await self._check_load_balance()

    async def _update_agent_availability(self, event: BaseEvent) -> None:
        """Update agent availability information"""
        agent_id = event.source_agent_id
        self.agent_workloads[agent_id] = 0  # Agent is available
        logger.debug(f"Agent {agent_id} marked as available")

    async def _check_load_balance(self) -> None:
        """Check for load imbalances and suggest corrections"""
        if len(self.agent_workloads) < 2:
            return

        workloads = list(self.agent_workloads.values())
        if not workloads:
            return

        max_workload = max(workloads)
        min_workload = min(workloads)

        # If imbalance is significant, publish a recommendation event
        if max_workload - min_workload > 3:
            overloaded_agents = [
                agent_id
                for agent_id, workload in self.agent_workloads.items()
                if workload == max_workload
            ]
            underloaded_agents = [
                agent_id
                for agent_id, workload in self.agent_workloads.items()
                if workload == min_workload
            ]

            # Create load balancing suggestion event
            suggestion_event = BaseEvent(
                event_type=EventType.SYSTEM_ALERT,
                source_agent_id="task_handoff_processor",
                priority=Priority.NORMAL,
                metadata={
                    "alert_type": "load_imbalance",
                    "overloaded_agents": overloaded_agents,
                    "underloaded_agents": underloaded_agents,
                    "max_workload": max_workload,
                    "min_workload": min_workload,
                },
            )

            await self.event_bus.publish(suggestion_event)


class FailureRecoveryProcessor(EventProcessor):
    """Processes error events and implements recovery strategies"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("failure_recovery_processor", event_bus)
        self.failed_agents: Set[str] = set()
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = 3

    def get_handled_event_types(self) -> List[EventType]:
        return [EventType.AGENT_ERROR, EventType.TASK_FAILED, EventType.SYSTEM_ALERT]

    async def process_event(self, event: BaseEvent) -> None:
        if event.event_type == EventType.AGENT_ERROR:
            await self._handle_agent_error(event)
        elif event.event_type == EventType.TASK_FAILED:
            await self._handle_task_failure(event)
        elif event.event_type == EventType.SYSTEM_ALERT:
            await self._handle_system_alert(event)

    async def _handle_agent_error(self, event: BaseEvent) -> None:
        """Handle agent error and attempt recovery"""
        agent_id = event.source_agent_id

        # Track failed agent
        self.failed_agents.add(agent_id)

        # Increment recovery attempts
        self.recovery_attempts[agent_id] = self.recovery_attempts.get(agent_id, 0) + 1

        logger.warning(
            f"Agent {agent_id} error detected (attempt {self.recovery_attempts[agent_id]})"
        )

        # If too many attempts, mark as permanently failed
        if self.recovery_attempts[agent_id] >= self.max_recovery_attempts:
            await self._escalate_agent_failure(agent_id)
        else:
            # Attempt recovery by requesting help
            help_event = create_help_request_event(
                source_agent_id="failure_recovery_processor",
                problem_description=f"Agent {agent_id} experienced an error and needs assistance",
                urgency=Priority.HIGH,
            )
            await self.event_bus.publish(help_event)

    async def _handle_task_failure(self, event: BaseEvent) -> None:
        """Handle task failure and reassignment"""
        if not isinstance(event, ProgressEvent):
            return

        task_id = event.task_id
        failed_agent = event.source_agent_id

        logger.warning(f"Task {task_id} failed on agent {failed_agent}")

        # Create task reassignment event
        reassignment_event = BaseEvent(
            event_type=EventType.RESOURCE_REQUEST,
            source_agent_id="failure_recovery_processor",
            priority=Priority.HIGH,
            metadata={
                "request_type": "task_reassignment",
                "failed_task_id": task_id,
                "failed_agent": failed_agent,
                "reason": "task_failure",
            },
        )

        await self.event_bus.publish(reassignment_event)

    async def _handle_system_alert(self, event: BaseEvent) -> None:
        """Handle system-level alerts"""
        alert_type = event.metadata.get("alert_type", "unknown")

        if alert_type == "load_imbalance":
            await self._handle_load_imbalance_alert(event)

        logger.info(f"Processing system alert: {alert_type}")

    async def _handle_load_imbalance_alert(self, event: BaseEvent) -> None:
        """Handle load imbalance alert"""
        overloaded_agents = event.metadata.get("overloaded_agents", [])
        underloaded_agents = event.metadata.get("underloaded_agents", [])

        # Create work redistribution recommendations
        for overloaded in overloaded_agents:
            if underloaded_agents:
                target = underloaded_agents[0]  # Simple strategy

                redistribution_event = BaseEvent(
                    event_type=EventType.WORK_REQUEST,
                    source_agent_id="failure_recovery_processor",
                    priority=Priority.NORMAL,
                    metadata={
                        "request_type": "work_redistribution",
                        "source_agent": overloaded,
                        "target_agent": target,
                        "reason": "load_balancing",
                    },
                )

                await self.event_bus.publish(redistribution_event)

    async def _escalate_agent_failure(self, agent_id: str) -> None:
        """Escalate persistent agent failure"""
        escalation_event = BaseEvent(
            event_type=EventType.SYSTEM_ALERT,
            source_agent_id="failure_recovery_processor",
            priority=Priority.CRITICAL,
            metadata={
                "alert_type": "agent_failure_escalation",
                "failed_agent": agent_id,
                "recovery_attempts": self.recovery_attempts[agent_id],
                "action_required": "manual_intervention",
            },
        )

        await self.event_bus.publish(escalation_event)

        logger.critical(
            f"Agent {agent_id} failure escalated after "
            f"{self.recovery_attempts[agent_id]} recovery attempts"
        )


class ProgressTrackingProcessor(EventProcessor):
    """Tracks progress and generates status updates"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        super().__init__("progress_tracking_processor", event_bus)
        self.task_progress: Dict[str, Dict[str, Any]] = {}
        self.agent_status: Dict[str, Dict[str, Any]] = {}

    def get_handled_event_types(self) -> List[EventType]:
        return [
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.PROGRESS_UPDATE,
            EventType.MILESTONE_REACHED,
        ]

    async def process_event(self, event: BaseEvent) -> None:
        if event.event_type == EventType.TASK_STARTED:
            await self._track_task_start(event)
        elif event.event_type == EventType.TASK_COMPLETED:
            await self._track_task_completion(event)
        elif event.event_type == EventType.PROGRESS_UPDATE:
            await self._track_progress_update(event)
        elif event.event_type == EventType.MILESTONE_REACHED:
            await self._track_milestone(event)

    async def _track_task_start(self, event: BaseEvent) -> None:
        """Track task start"""
        if not isinstance(event, ProgressEvent):
            return

        task_id = event.task_id
        agent_id = event.source_agent_id

        self.task_progress[task_id] = {
            "agent_id": agent_id,
            "start_time": event.timestamp,
            "progress": 0.0,
            "status": "started",
            "milestones": [],
        }

        # Update agent status
        if agent_id not in self.agent_status:
            self.agent_status[agent_id] = {"active_tasks": [], "completed_tasks": 0}

        self.agent_status[agent_id]["active_tasks"].append(task_id)

        logger.info(f"Tracking started for task {task_id} on agent {agent_id}")

    async def _track_task_completion(self, event: BaseEvent) -> None:
        """Track task completion"""
        if not isinstance(event, ProgressEvent):
            return

        task_id = event.task_id
        agent_id = event.source_agent_id

        if task_id in self.task_progress:
            task_info = self.task_progress[task_id]
            task_info["status"] = "completed"
            task_info["end_time"] = event.timestamp
            task_info["duration"] = event.timestamp - task_info["start_time"]
            task_info["progress"] = 100.0

        # Update agent status
        if agent_id in self.agent_status:
            if task_id in self.agent_status[agent_id]["active_tasks"]:
                self.agent_status[agent_id]["active_tasks"].remove(task_id)
            self.agent_status[agent_id]["completed_tasks"] += 1

        logger.info(f"Task {task_id} completed by agent {agent_id}")

        # Generate performance summary
        await self._generate_performance_summary(task_id)

    async def _track_progress_update(self, event: BaseEvent) -> None:
        """Track progress update"""
        if not isinstance(event, ProgressEvent):
            return

        task_id = event.task_id

        if task_id in self.task_progress:
            self.task_progress[task_id]["progress"] = event.progress_percentage
            self.task_progress[task_id]["last_update"] = event.timestamp

            # Check for stalled progress
            await self._check_progress_health(task_id)

    async def _track_milestone(self, event: BaseEvent) -> None:
        """Track milestone reached"""
        if not isinstance(event, ProgressEvent):
            return

        task_id = event.task_id

        if task_id in self.task_progress:
            self.task_progress[task_id]["milestones"].append(
                {
                    "timestamp": event.timestamp,
                    "description": event.status_message,
                    "progress": event.progress_percentage,
                }
            )

    async def _check_progress_health(self, task_id: str) -> None:
        """Check if task progress is healthy"""
        if task_id not in self.task_progress:
            return

        task_info = self.task_progress[task_id]
        current_time = time.time()

        # Check for stalled progress (no update in 5 minutes)
        if "last_update" in task_info:
            time_since_update = current_time - task_info["last_update"]
            if time_since_update > 300:  # 5 minutes
                stall_alert = BaseEvent(
                    event_type=EventType.SYSTEM_ALERT,
                    source_agent_id="progress_tracking_processor",
                    priority=Priority.NORMAL,
                    metadata={
                        "alert_type": "progress_stalled",
                        "task_id": task_id,
                        "agent_id": task_info["agent_id"],
                        "time_since_update": time_since_update,
                    },
                )

                await self.event_bus.publish(stall_alert)

    async def _generate_performance_summary(self, task_id: str) -> None:
        """Generate performance summary for completed task"""
        if task_id not in self.task_progress:
            return

        task_info = self.task_progress[task_id]

        summary_event = BaseEvent(
            event_type=EventType.MILESTONE_REACHED,
            source_agent_id="progress_tracking_processor",
            priority=Priority.LOW,
            metadata={
                "summary_type": "task_completion",
                "task_id": task_id,
                "agent_id": task_info["agent_id"],
                "duration": task_info.get("duration", 0),
                "milestones_count": len(task_info.get("milestones", [])),
                "performance_metrics": {
                    "completion_time": task_info.get("duration", 0),
                    "milestone_frequency": (
                        len(task_info.get("milestones", []))
                        / max(1, task_info.get("duration", 1))
                    ),
                },
            },
        )

        await self.event_bus.publish(summary_event)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        return self.task_progress.get(task_id)

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an agent"""
        return self.agent_status.get(agent_id)


class EventProcessorManager:
    """Manages multiple event processors"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_global_event_bus()
        self.processors: Dict[str, EventProcessor] = {}
        self.running = False

        logger.info("EventProcessorManager initialized")

    def register_processor(self, processor: EventProcessor) -> None:
        """Register an event processor"""
        self.processors[processor.processor_id] = processor
        logger.info(f"Registered processor: {processor.processor_id}")

    def unregister_processor(self, processor_id: str) -> bool:
        """Unregister an event processor"""
        if processor_id in self.processors:
            processor = self.processors.pop(processor_id)
            processor.shutdown()
            logger.info(f"Unregistered processor: {processor_id}")
            return True
        return False

    async def start_all_processors(self) -> None:
        """Start all registered processors"""
        self.running = True
        for processor in self.processors.values():
            processor.enable()

        logger.info(f"Started {len(self.processors)} event processors")

    async def stop_all_processors(self) -> None:
        """Stop all registered processors"""
        self.running = False
        for processor in self.processors.values():
            processor.shutdown()

        logger.info("Stopped all event processors")

    def get_processor_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all processors"""
        return {
            processor_id: processor.get_metrics()
            for processor_id, processor in self.processors.items()
        }

    def get_processor(self, processor_id: str) -> Optional[EventProcessor]:
        """Get a specific processor"""
        return self.processors.get(processor_id)


def create_default_processors(
    event_bus: Optional[EventBus] = None,
) -> EventProcessorManager:
    """Create manager with default set of processors"""
    manager = EventProcessorManager(event_bus)

    # Register default processors
    manager.register_processor(TaskHandoffProcessor(event_bus))
    manager.register_processor(FailureRecoveryProcessor(event_bus))
    manager.register_processor(ProgressTrackingProcessor(event_bus))

    return manager
