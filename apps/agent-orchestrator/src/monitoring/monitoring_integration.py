"""
Integration layer between ResourceMonitor and MonitoringModule
Provides seamless resource tracking and limit enforcement for orchestrator tasks
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..modules.monitoring_module import MonitoringModule
from .resource_monitor import (
    ResourceLimitAction,
    ResourceLimits,
    ResourceMonitor,
    TaskResourceUsage,
    get_global_resource_monitor,
)

logger = logging.getLogger(__name__)


class MonitoringIntegration:
    """
    Integration class that bridges ResourceMonitor with MonitoringModule
    Provides unified resource tracking and enforcement
    """

    def __init__(
        self,
        monitoring_module: MonitoringModule,
        resource_monitor: Optional[ResourceMonitor] = None,
        enable_auto_enforcement: bool = True,
    ):
        """
        Initialize monitoring integration

        Args:
            monitoring_module: The orchestrator's monitoring module
            resource_monitor: Resource monitor instance (uses global if None)
            enable_auto_enforcement: Automatically enforce resource limits
        """
        self.monitoring_module = monitoring_module
        self.resource_monitor = resource_monitor or get_global_resource_monitor()
        self.enable_auto_enforcement = enable_auto_enforcement

        # Track task mappings
        self._task_mappings: Dict[
            str, str
        ] = {}  # orchestrator_task_id -> resource_task_id

        # Setup callbacks
        self._setup_callbacks()

        logger.info(
            "MonitoringIntegration initialized with auto-enforcement: %s",
            enable_auto_enforcement,
        )

    def _setup_callbacks(self):
        """Setup callbacks between monitors"""
        # Register violation callback
        self.resource_monitor.set_violation_callback(self._handle_resource_violation)

        # Register suspension callback
        self.resource_monitor.set_suspension_callback(self._handle_task_suspension)

    async def register_task(
        self, task: "AgentTask", resource_limits: Optional[ResourceLimits] = None
    ) -> TaskResourceUsage:
        """
        Register a task for integrated monitoring

        Args:
            task: The agent task to monitor
            resource_limits: Optional specific limits for this task

        Returns:
            TaskResourceUsage object for tracking
        """
        # Generate unique resource task ID
        resource_task_id = f"{task.task_id}_{datetime.now().timestamp()}"
        self._task_mappings[task.task_id] = resource_task_id

        # Get default limits from task configuration if not provided
        if resource_limits is None:
            resource_limits = self._get_task_limits(task)

        # Register with resource monitor
        usage = self.resource_monitor.register_task(
            task_id=resource_task_id,
            process_id=None,  # Will use current process
            limits=resource_limits,
        )

        # Start monitoring in monitoring module
        self.monitoring_module.start_task_monitoring(task)

        # Update task metadata
        self.monitoring_module.update_task_metrics(
            task.task_id,
            resource_monitor_id=resource_task_id,
            resource_limits=resource_limits.to_dict() if resource_limits else None,
        )

        logger.info("Registered task %s for integrated monitoring", task.task_id)
        return usage

    async def unregister_task(self, task: "AgentTask"):
        """Unregister a task from integrated monitoring"""
        task_id = task.task_id
        resource_task_id = self._task_mappings.get(task_id)

        if resource_task_id:
            # Get final usage stats
            usage = self.resource_monitor.get_task_usage(resource_task_id)

            if usage:
                # Update monitoring module with final stats
                self.monitoring_module.update_task_metrics(
                    task_id,
                    peak_memory_mb=usage.peak_memory_mb,
                    peak_cpu_percent=usage.peak_cpu_percent,
                    avg_memory_mb=usage.avg_memory_mb,
                    avg_cpu_percent=usage.avg_cpu_percent,
                    resource_violations={
                        "memory": usage.memory_violations,
                        "cpu": usage.cpu_violations,
                        "duration": usage.duration_violations,
                    },
                )

            # Unregister from resource monitor
            self.resource_monitor.unregister_task(resource_task_id)
            del self._task_mappings[task_id]

            logger.info("Unregistered task %s from integrated monitoring", task_id)

    def _get_task_limits(self, task: "AgentTask") -> ResourceLimits:
        """
        Get resource limits for a task based on its configuration

        Args:
            task: The agent task

        Returns:
            ResourceLimits object
        """
        limits = ResourceLimits()

        # Check task configuration for limits
        if hasattr(task, "config") and task.config:
            config = task.config

            # Memory limits
            if "max_memory_mb" in config:
                limits.max_memory_mb = config["max_memory_mb"]
            elif "max_memory_gb" in config:
                limits.max_memory_mb = config["max_memory_gb"] * 1024

            # CPU limits
            if "max_cpu_percent" in config:
                limits.max_cpu_percent = config["max_cpu_percent"]

            # Duration limits
            if "max_duration_seconds" in config:
                limits.max_duration_seconds = config["max_duration_seconds"]
            elif "timeout" in config:
                limits.max_duration_seconds = config["timeout"]

            # Limit actions
            if "memory_limit_action" in config:
                limits.memory_limit_action = ResourceLimitAction(
                    config["memory_limit_action"]
                )
            if "cpu_limit_action" in config:
                limits.cpu_limit_action = ResourceLimitAction(
                    config["cpu_limit_action"]
                )

        # Apply task-type specific defaults
        task_type = getattr(task, "task_type", "unknown")
        limits = self._apply_task_type_defaults(task_type, limits)

        return limits

    def _apply_task_type_defaults(
        self, task_type: str, limits: ResourceLimits
    ) -> ResourceLimits:
        """
        Apply task-type specific default limits

        Args:
            task_type: Type of task
            limits: Current limits

        Returns:
            Updated limits
        """
        # Define task-type specific defaults
        task_defaults = {
            "development": {
                "max_memory_mb": 4096,  # 4GB for development tasks
                "max_cpu_percent": 400,  # 4 cores
                "max_duration_seconds": 7200,  # 2 hours
            },
            "analysis": {
                "max_memory_mb": 2048,  # 2GB for analysis
                "max_cpu_percent": 200,  # 2 cores
                "max_duration_seconds": 3600,  # 1 hour
            },
            "testing": {
                "max_memory_mb": 3072,  # 3GB for testing
                "max_cpu_percent": 300,  # 3 cores
                "max_duration_seconds": 1800,  # 30 minutes
            },
            "documentation": {
                "max_memory_mb": 1024,  # 1GB for docs
                "max_cpu_percent": 100,  # 1 core
                "max_duration_seconds": 1800,  # 30 minutes
            },
        }

        # Apply defaults if not already set
        if task_type in task_defaults:
            defaults = task_defaults[task_type]

            if limits.max_memory_mb is None:
                limits.max_memory_mb = defaults["max_memory_mb"]
            if limits.max_cpu_percent is None:
                limits.max_cpu_percent = defaults["max_cpu_percent"]
            if limits.max_duration_seconds is None:
                limits.max_duration_seconds = defaults["max_duration_seconds"]

        return limits

    def _handle_resource_violation(
        self,
        resource_task_id: str,
        violation_type: str,
        current_value: float,
        limit_value: float,
    ):
        """Handle resource violation callback from ResourceMonitor"""
        # Find orchestrator task ID
        orchestrator_task_id = None
        for orch_id, res_id in self._task_mappings.items():
            if res_id == resource_task_id:
                orchestrator_task_id = orch_id
                break

        if not orchestrator_task_id:
            return

        # Create alert in monitoring module
        asyncio.create_task(
            self.monitoring_module._create_alert(
                orchestrator_task_id,
                "critical" if violation_type == "memory" else "warning",
                f"Resource violation: {violation_type} ({current_value:.1f} > {limit_value:.1f})",
            )
        )

        # Update task metrics
        self.monitoring_module.update_task_metrics(
            orchestrator_task_id,
            last_violation_type=violation_type,
            last_violation_time=datetime.now().isoformat(),
        )

    def _handle_task_suspension(self, resource_task_id: str, usage: TaskResourceUsage):
        """Handle task suspension callback from ResourceMonitor"""
        # Find orchestrator task ID
        orchestrator_task_id = None
        for orch_id, res_id in self._task_mappings.items():
            if res_id == resource_task_id:
                orchestrator_task_id = orch_id
                break

        if not orchestrator_task_id:
            return

        # Update task status in monitoring module
        self.monitoring_module.update_task_metrics(
            orchestrator_task_id,
            status="suspended",
            suspended_at=datetime.now().isoformat(),
            suspension_reason=f"Resource limit exceeded (Memory: {usage.peak_memory_mb:.1f}MB, CPU: {usage.peak_cpu_percent:.1f}%)",
        )

        # Create critical alert
        asyncio.create_task(
            self.monitoring_module._create_alert(
                orchestrator_task_id,
                "critical",
                f"Task suspended due to resource limits",
            )
        )

    async def update_task_resources(self, task_id: str):
        """
        Update resource metrics for a task in the monitoring module

        Args:
            task_id: Orchestrator task ID
        """
        resource_task_id = self._task_mappings.get(task_id)
        if not resource_task_id:
            return

        usage = self.resource_monitor.get_task_usage(resource_task_id)
        if not usage:
            return

        # Update monitoring module metrics
        metrics = self.monitoring_module.task_metrics.get(task_id)
        if metrics:
            metrics.cpu_usage.append(usage.current_cpu_percent)
            metrics.memory_usage.append(usage.current_memory_mb)

    async def periodic_update(self):
        """Periodic update of all task resources"""
        while True:
            try:
                # Update all active tasks
                for task_id in list(self._task_mappings.keys()):
                    await self.update_task_resources(task_id)

                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic resource update: %s", e)
                await asyncio.sleep(5)

    def get_task_resource_summary(self, task_id: str) -> Dict[str, Any]:
        """
        Get comprehensive resource summary for a task

        Args:
            task_id: Orchestrator task ID

        Returns:
            Resource summary dictionary
        """
        resource_task_id = self._task_mappings.get(task_id)
        if not resource_task_id:
            return {"error": "Task not found"}

        usage = self.resource_monitor.get_task_usage(resource_task_id)
        if not usage:
            return {"error": "No resource data available"}

        # Get monitoring module data
        health = self.monitoring_module.get_task_health(task_id)

        # Combine data
        return {
            "task_id": task_id,
            "resource_task_id": resource_task_id,
            "state": usage.state.value,
            "duration": usage.duration,
            "resources": {
                "current": {
                    "memory_mb": usage.current_memory_mb,
                    "cpu_percent": usage.current_cpu_percent,
                    "threads": usage.current_threads,
                    "file_handles": usage.current_file_handles,
                },
                "peak": {
                    "memory_mb": usage.peak_memory_mb,
                    "cpu_percent": usage.peak_cpu_percent,
                    "threads": usage.peak_threads,
                },
                "average": {
                    "memory_mb": usage.avg_memory_mb,
                    "cpu_percent": usage.avg_cpu_percent,
                },
            },
            "violations": {
                "memory": usage.memory_violations,
                "cpu": usage.cpu_violations,
                "duration": usage.duration_violations,
            },
            "health": health,
            "suspended": usage.suspended_at.isoformat() if usage.suspended_at else None,
            "throttled": usage.throttled_at.isoformat() if usage.throttled_at else None,
        }

    def get_all_tasks_summary(self) -> Dict[str, Any]:
        """Get summary of all monitored tasks"""
        summaries = {}
        for task_id in self._task_mappings:
            summaries[task_id] = self.get_task_resource_summary(task_id)

        # Add global statistics
        stats = self.resource_monitor.get_statistics()

        return {
            "tasks": summaries,
            "statistics": stats,
            "monitoring_metrics": self.monitoring_module.get_metrics(),
        }


async def setup_monitoring_integration(
    orchestrator: "UnifiedOrchestrator",
    resource_limits: Optional[Dict[str, Any]] = None,
) -> MonitoringIntegration:
    """
    Setup monitoring integration for an orchestrator

    Args:
        orchestrator: The orchestrator instance
        resource_limits: Default resource limits configuration

    Returns:
        MonitoringIntegration instance
    """
    # Get or create monitoring module
    monitoring_module = orchestrator.get_module("monitoring")
    if not monitoring_module:
        raise ValueError("Monitoring module not found in orchestrator")

    # Create resource monitor with defaults
    default_limits = None
    if resource_limits:
        default_limits = ResourceLimits(
            max_memory_mb=resource_limits.get("max_memory_mb"),
            max_cpu_percent=resource_limits.get("max_cpu_percent"),
            max_duration_seconds=resource_limits.get("max_duration_seconds"),
            max_threads=resource_limits.get("max_threads"),
        )

    resource_monitor = ResourceMonitor(default_limits=default_limits)
    resource_monitor.start_monitoring()

    # Create integration
    integration = MonitoringIntegration(
        monitoring_module=monitoring_module,
        resource_monitor=resource_monitor,
        enable_auto_enforcement=resource_limits.get("enable_enforcement", True)
        if resource_limits
        else True,
    )

    # Start periodic updates
    asyncio.create_task(integration.periodic_update())

    logger.info("Monitoring integration setup complete")
    return integration
