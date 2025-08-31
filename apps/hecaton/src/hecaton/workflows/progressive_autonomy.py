"""
Progressive Autonomy Manager for adaptive agent behavior based on confidence and performance.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AutonomyLevel(IntEnum):
    """Levels of agent autonomy"""

    NONE = 0  # No autonomy - all actions require approval
    MINIMAL = 1  # Can perform basic read operations
    LOW = 2  # Can perform safe operations with notification
    MODERATE = 3  # Can perform most operations, critical ones need approval
    HIGH = 4  # Can perform all but the most critical operations
    FULL = 5  # Complete autonomy


class ActionCategory(Enum):
    """Categories of agent actions"""

    READ = "read"  # Reading data/files
    ANALYZE = "analyze"  # Analysis operations
    MODIFY = "modify"  # Modifying existing resources
    CREATE = "create"  # Creating new resources
    DELETE = "delete"  # Deleting resources
    EXECUTE = "execute"  # Executing commands
    DEPLOY = "deploy"  # Deployment operations
    CRITICAL = "critical"  # Critical system operations


@dataclass
class AutonomyPolicy:
    """Policy defining allowed actions at each autonomy level"""

    level: AutonomyLevel
    allowed_actions: List[ActionCategory]
    requires_approval: List[ActionCategory]
    notification_required: List[ActionCategory]
    max_resource_usage: Dict[str, Any] = field(default_factory=dict)
    time_restrictions: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """Agent performance metrics for autonomy adjustment"""

    success_rate: float = 0.0
    error_rate: float = 0.0
    avg_task_time: float = 0.0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    confidence_scores: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class ProgressiveAutonomyManager:
    """Manages progressive autonomy for agents based on performance and confidence"""

    def __init__(self):
        self.agent_autonomy: Dict[str, AutonomyLevel] = {}
        self.agent_metrics: Dict[str, PerformanceMetrics] = {}
        self.policies: Dict[AutonomyLevel, AutonomyPolicy] = self._initialize_policies()
        self.adjustment_history: List[Dict[str, Any]] = []
        self.confidence_threshold: float = 0.8
        self.performance_threshold: float = 0.85

    def _initialize_policies(self) -> Dict[AutonomyLevel, AutonomyPolicy]:
        """Initialize default autonomy policies"""
        return {
            AutonomyLevel.NONE: AutonomyPolicy(
                level=AutonomyLevel.NONE,
                allowed_actions=[],
                requires_approval=[cat for cat in ActionCategory],
                notification_required=[],
            ),
            AutonomyLevel.MINIMAL: AutonomyPolicy(
                level=AutonomyLevel.MINIMAL,
                allowed_actions=[ActionCategory.READ, ActionCategory.ANALYZE],
                requires_approval=[
                    ActionCategory.MODIFY,
                    ActionCategory.CREATE,
                    ActionCategory.DELETE,
                    ActionCategory.EXECUTE,
                    ActionCategory.DEPLOY,
                    ActionCategory.CRITICAL,
                ],
                notification_required=[ActionCategory.ANALYZE],
            ),
            AutonomyLevel.LOW: AutonomyPolicy(
                level=AutonomyLevel.LOW,
                allowed_actions=[
                    ActionCategory.READ,
                    ActionCategory.ANALYZE,
                    ActionCategory.CREATE,
                ],
                requires_approval=[
                    ActionCategory.DELETE,
                    ActionCategory.EXECUTE,
                    ActionCategory.DEPLOY,
                    ActionCategory.CRITICAL,
                ],
                notification_required=[ActionCategory.CREATE, ActionCategory.MODIFY],
            ),
            AutonomyLevel.MODERATE: AutonomyPolicy(
                level=AutonomyLevel.MODERATE,
                allowed_actions=[
                    ActionCategory.READ,
                    ActionCategory.ANALYZE,
                    ActionCategory.CREATE,
                    ActionCategory.MODIFY,
                    ActionCategory.EXECUTE,
                ],
                requires_approval=[
                    ActionCategory.DELETE,
                    ActionCategory.DEPLOY,
                    ActionCategory.CRITICAL,
                ],
                notification_required=[ActionCategory.EXECUTE],
            ),
            AutonomyLevel.HIGH: AutonomyPolicy(
                level=AutonomyLevel.HIGH,
                allowed_actions=[
                    ActionCategory.READ,
                    ActionCategory.ANALYZE,
                    ActionCategory.CREATE,
                    ActionCategory.MODIFY,
                    ActionCategory.EXECUTE,
                    ActionCategory.DELETE,
                ],
                requires_approval=[ActionCategory.DEPLOY, ActionCategory.CRITICAL],
                notification_required=[ActionCategory.DELETE, ActionCategory.DEPLOY],
            ),
            AutonomyLevel.FULL: AutonomyPolicy(
                level=AutonomyLevel.FULL,
                allowed_actions=[cat for cat in ActionCategory],
                requires_approval=[],
                notification_required=[ActionCategory.CRITICAL, ActionCategory.DEPLOY],
            ),
        }

    def register_agent(
        self, agent_id: str, initial_level: AutonomyLevel = AutonomyLevel.MINIMAL
    ):
        """Register an agent with initial autonomy level"""
        self.agent_autonomy[agent_id] = initial_level
        self.agent_metrics[agent_id] = PerformanceMetrics()
        logger.info(
            f"Registered agent {agent_id} with autonomy level {initial_level.name}"
        )

    async def check_permission(
        self, agent_id: str, action: ActionCategory, confidence: float = 0.5
    ) -> Tuple[bool, bool, str]:
        """
        Check if agent has permission for an action

        Returns:
            Tuple of (allowed, requires_approval, reason)
        """
        if agent_id not in self.agent_autonomy:
            return False, False, "Agent not registered"

        level = self.agent_autonomy[agent_id]
        policy = self.policies[level]

        # Check if action is allowed
        if action in policy.allowed_actions:
            # Check confidence threshold for critical actions
            if action in [
                ActionCategory.DELETE,
                ActionCategory.DEPLOY,
                ActionCategory.CRITICAL,
            ]:
                if confidence < self.confidence_threshold:
                    return (
                        False,
                        True,
                        f"Confidence {confidence:.2f} below threshold {self.confidence_threshold}",
                    )

            notification_required = action in policy.notification_required
            return True, notification_required, "Action allowed"

        # Check if action requires approval
        if action in policy.requires_approval:
            return False, True, "Action requires approval"

        return False, False, "Action not permitted at current autonomy level"

    async def update_metrics(
        self,
        agent_id: str,
        task_success: bool,
        task_duration: float,
        confidence_score: float,
    ):
        """Update agent performance metrics"""

        if agent_id not in self.agent_metrics:
            return

        metrics = self.agent_metrics[agent_id]

        # Update task counts
        metrics.total_tasks += 1
        if task_success:
            metrics.successful_tasks += 1
        else:
            metrics.failed_tasks += 1

        # Update rates
        metrics.success_rate = metrics.successful_tasks / metrics.total_tasks
        metrics.error_rate = metrics.failed_tasks / metrics.total_tasks

        # Update average task time (exponential moving average)
        alpha = 0.1
        if metrics.avg_task_time == 0:
            metrics.avg_task_time = task_duration
        else:
            metrics.avg_task_time = (
                1 - alpha
            ) * metrics.avg_task_time + alpha * task_duration

        # Store confidence score
        metrics.confidence_scores.append(confidence_score)
        if len(metrics.confidence_scores) > 100:  # Keep last 100 scores
            metrics.confidence_scores = metrics.confidence_scores[-100:]

        metrics.last_updated = datetime.utcnow()

        # Check for autonomy adjustment
        await self._check_autonomy_adjustment(agent_id)

    async def _check_autonomy_adjustment(self, agent_id: str):
        """Check if agent's autonomy level should be adjusted"""

        metrics = self.agent_metrics[agent_id]
        current_level = self.agent_autonomy[agent_id]

        # Need minimum tasks for evaluation
        if metrics.total_tasks < 10:
            return

        # Calculate average confidence
        avg_confidence = (
            sum(metrics.confidence_scores) / len(metrics.confidence_scores)
            if metrics.confidence_scores
            else 0
        )

        new_level = current_level
        reason = ""

        # Check for promotion
        if (
            metrics.success_rate >= self.performance_threshold
            and avg_confidence >= self.confidence_threshold
            and current_level < AutonomyLevel.FULL
        ):
            new_level = AutonomyLevel(current_level + 1)
            reason = f"Promoted due to high performance (success: {metrics.success_rate:.2%}, confidence: {avg_confidence:.2f})"

        # Check for demotion
        elif (
            metrics.error_rate > 0.3 or avg_confidence < 0.5
        ) and current_level > AutonomyLevel.MINIMAL:
            new_level = AutonomyLevel(current_level - 1)
            reason = f"Demoted due to low performance (error: {metrics.error_rate:.2%}, confidence: {avg_confidence:.2f})"

        # Apply adjustment if needed
        if new_level != current_level:
            await self.adjust_autonomy(agent_id, new_level, reason)

    async def adjust_autonomy(
        self, agent_id: str, new_level: AutonomyLevel, reason: str
    ):
        """Adjust agent's autonomy level"""

        if agent_id not in self.agent_autonomy:
            return

        old_level = self.agent_autonomy[agent_id]
        self.agent_autonomy[agent_id] = new_level

        # Record adjustment
        adjustment = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow(),
            "old_level": old_level.name,
            "new_level": new_level.name,
            "reason": reason,
            "metrics": {
                "success_rate": self.agent_metrics[agent_id].success_rate,
                "error_rate": self.agent_metrics[agent_id].error_rate,
                "total_tasks": self.agent_metrics[agent_id].total_tasks,
            },
        }

        self.adjustment_history.append(adjustment)

        logger.info(
            f"Adjusted {agent_id} autonomy: {old_level.name} -> {new_level.name}. Reason: {reason}"
        )

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get current autonomy status for an agent"""

        if agent_id not in self.agent_autonomy:
            return {"error": "Agent not found"}

        level = self.agent_autonomy[agent_id]
        metrics = self.agent_metrics[agent_id]
        policy = self.policies[level]

        avg_confidence = (
            sum(metrics.confidence_scores) / len(metrics.confidence_scores)
            if metrics.confidence_scores
            else 0
        )

        return {
            "agent_id": agent_id,
            "autonomy_level": level.name,
            "level_value": level.value,
            "allowed_actions": [a.value for a in policy.allowed_actions],
            "requires_approval": [a.value for a in policy.requires_approval],
            "metrics": {
                "success_rate": metrics.success_rate,
                "error_rate": metrics.error_rate,
                "avg_task_time": metrics.avg_task_time,
                "total_tasks": metrics.total_tasks,
                "avg_confidence": avg_confidence,
            },
            "last_updated": metrics.last_updated.isoformat(),
        }

    def get_adjustment_history(
        self, agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get autonomy adjustment history"""

        if agent_id:
            return [
                adj for adj in self.adjustment_history if adj["agent_id"] == agent_id
            ]
        return self.adjustment_history

    async def override_autonomy(
        self, agent_id: str, new_level: AutonomyLevel, duration_minutes: int = 60
    ):
        """Temporarily override agent autonomy level"""

        if agent_id not in self.agent_autonomy:
            return

        original_level = self.agent_autonomy[agent_id]
        self.agent_autonomy[agent_id] = new_level

        # Schedule reversion
        revert_time = datetime.utcnow() + timedelta(minutes=duration_minutes)

        logger.info(
            f"Temporarily overrode {agent_id} autonomy to {new_level.name} until {revert_time}"
        )

        # Store override info
        self.adjustment_history.append(
            {
                "agent_id": agent_id,
                "timestamp": datetime.utcnow(),
                "type": "override",
                "original_level": original_level.name,
                "override_level": new_level.name,
                "revert_time": revert_time.isoformat(),
                "duration_minutes": duration_minutes,
            }
        )

    def set_thresholds(self, confidence: float = 0.8, performance: float = 0.85):
        """Set thresholds for autonomy adjustments"""
        self.confidence_threshold = confidence
        self.performance_threshold = performance
        logger.info(
            f"Set thresholds - confidence: {confidence}, performance: {performance}"
        )
