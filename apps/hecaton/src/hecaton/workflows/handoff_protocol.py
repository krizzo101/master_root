"""
Agent Handoff Protocol for seamless context transfer between agents.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HandoffReason(Enum):
    """Reasons for agent handoff"""

    PHASE_TRANSITION = "phase_transition"  # Moving to next SDLC phase
    SKILL_MISMATCH = "skill_mismatch"  # Current agent lacks required skills
    LOAD_BALANCING = "load_balancing"  # Redistribute workload
    ERROR_RECOVERY = "error_recovery"  # Recovering from agent failure
    COMPLETION = "completion"  # Task completed successfully
    ESCALATION = "escalation"  # Issue requires higher authority
    SPECIALIZATION = "specialization"  # Needs specialized agent


@dataclass
class HandoffPackage:
    """Structured handoff information between agents"""

    handoff_id: str
    from_agent: str
    to_agent: str
    timestamp: datetime
    reason: HandoffReason
    context: Dict[str, Any]
    completed_work: Dict[str, Any]
    remaining_work: List[str]
    recommendations: List[str]
    artifacts: Dict[str, Any]  # Files, data, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_passed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "handoff_id": self.handoff_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason.value,
            "context": self.context,
            "completed_work": self.completed_work,
            "remaining_work": self.remaining_work,
            "recommendations": self.recommendations,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
            "validation_passed": self.validation_passed,
        }

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate handoff package completeness"""
        issues = []

        if not self.completed_work:
            issues.append("No completed work documented")

        if not self.context:
            issues.append("Missing context information")

        if self.reason == HandoffReason.ERROR_RECOVERY and "error" not in self.metadata:
            issues.append("Error recovery handoff missing error details")

        if not self.to_agent:
            issues.append("Target agent not specified")

        self.validation_passed = len(issues) == 0
        return self.validation_passed, issues


class HandoffProtocol:
    """Manages structured handoffs between agents"""

    def __init__(self):
        self.handoff_history: List[HandoffPackage] = []
        self.pending_handoffs: Dict[str, HandoffPackage] = {}
        self.handoff_handlers: Dict[HandoffReason, Callable] = {}
        self.validation_rules: List[Callable] = []

    async def prepare_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        reason: HandoffReason,
        task_context: Dict[str, Any],
        completed_work: Dict[str, Any],
        remaining_work: List[str],
        recommendations: Optional[List[str]] = None,
        artifacts: Optional[Dict[str, Any]] = None,
    ) -> HandoffPackage:
        """Prepare handoff package from one agent to another"""

        # Generate unique handoff ID
        handoff_id = f"{from_agent_id}_to_{to_agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Create handoff package
        handoff = HandoffPackage(
            handoff_id=handoff_id,
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            timestamp=datetime.utcnow(),
            reason=reason,
            context=task_context,
            completed_work=completed_work,
            remaining_work=remaining_work,
            recommendations=recommendations or [],
            artifacts=artifacts or {},
            metadata={
                "handoff_reason": reason.value,
                "task_id": task_context.get("task_id"),
                "project": task_context.get("project"),
            },
        )

        # Validate the package
        is_valid, issues = handoff.validate()
        if not is_valid:
            logger.warning(f"Handoff package has issues: {issues}")

        # Apply custom validation rules
        for rule in self.validation_rules:
            if not rule(handoff):
                logger.warning(
                    f"Handoff failed custom validation rule: {rule.__name__}"
                )

        # Store in pending
        self.pending_handoffs[handoff_id] = handoff

        logger.info(
            f"Prepared handoff {handoff_id} from {from_agent_id} to {to_agent_id}"
        )

        return handoff

    async def execute_handoff(self, handoff_id: str) -> bool:
        """Execute a pending handoff"""

        if handoff_id not in self.pending_handoffs:
            logger.error(f"Handoff {handoff_id} not found in pending")
            return False

        handoff = self.pending_handoffs[handoff_id]

        # Execute reason-specific handler if registered
        if handoff.reason in self.handoff_handlers:
            handler = self.handoff_handlers[handoff.reason]
            try:
                await handler(handoff)
            except Exception as e:
                logger.error(f"Handoff handler failed: {e}")
                return False

        # Move to history
        self.handoff_history.append(handoff)
        del self.pending_handoffs[handoff_id]

        logger.info(f"Executed handoff {handoff_id}")
        return True

    def register_handler(self, reason: HandoffReason, handler: Callable):
        """Register a custom handler for specific handoff reasons"""
        self.handoff_handlers[reason] = handler
        logger.debug(f"Registered handler for {reason.value}")

    def add_validation_rule(self, rule: Callable[[HandoffPackage], bool]):
        """Add custom validation rule for handoff packages"""
        self.validation_rules.append(rule)

    async def get_handoff_chain(self, task_id: str) -> List[HandoffPackage]:
        """Get all handoffs for a specific task"""
        chain = []
        for handoff in self.handoff_history:
            if handoff.metadata.get("task_id") == task_id:
                chain.append(handoff)

        # Sort by timestamp
        chain.sort(key=lambda h: h.timestamp)
        return chain

    def get_pending_handoffs(
        self, agent_id: Optional[str] = None
    ) -> List[HandoffPackage]:
        """Get pending handoffs, optionally filtered by agent"""
        pending = list(self.pending_handoffs.values())

        if agent_id:
            pending = [h for h in pending if h.to_agent == agent_id]

        return pending

    async def abort_handoff(self, handoff_id: str, reason: str) -> bool:
        """Abort a pending handoff"""

        if handoff_id not in self.pending_handoffs:
            return False

        handoff = self.pending_handoffs[handoff_id]
        handoff.metadata["aborted"] = True
        handoff.metadata["abort_reason"] = reason

        # Move to history as aborted
        self.handoff_history.append(handoff)
        del self.pending_handoffs[handoff_id]

        logger.info(f"Aborted handoff {handoff_id}: {reason}")
        return True

    def get_handoff_statistics(self) -> Dict[str, Any]:
        """Get statistics about handoffs"""

        total = len(self.handoff_history)
        if total == 0:
            return {"total_handoffs": 0, "pending": len(self.pending_handoffs)}

        # Count by reason
        by_reason = {}
        for handoff in self.handoff_history:
            reason = handoff.reason.value
            by_reason[reason] = by_reason.get(reason, 0) + 1

        # Count aborted
        aborted = sum(
            1 for h in self.handoff_history if h.metadata.get("aborted", False)
        )

        # Calculate average artifacts size
        artifact_sizes = [len(h.artifacts) for h in self.handoff_history]
        avg_artifacts = (
            sum(artifact_sizes) / len(artifact_sizes) if artifact_sizes else 0
        )

        return {
            "total_handoffs": total,
            "pending": len(self.pending_handoffs),
            "by_reason": by_reason,
            "aborted": aborted,
            "success_rate": (total - aborted) / total if total > 0 else 0,
            "avg_artifacts": avg_artifacts,
            "avg_recommendations": sum(
                len(h.recommendations) for h in self.handoff_history
            )
            / total,
        }

    async def serialize_handoff(self, handoff: HandoffPackage) -> str:
        """Serialize handoff package to JSON"""
        return json.dumps(handoff.to_dict(), indent=2, default=str)

    async def deserialize_handoff(self, data: str) -> HandoffPackage:
        """Deserialize handoff package from JSON"""
        obj = json.loads(data)

        # Convert timestamp back to datetime
        obj["timestamp"] = datetime.fromisoformat(obj["timestamp"])

        # Convert reason back to enum
        obj["reason"] = HandoffReason(obj["reason"])

        # Remove handoff_id from dict as it's a positional argument
        handoff_id = obj.pop("handoff_id")

        return HandoffPackage(handoff_id=handoff_id, **obj)
