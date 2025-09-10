"""
Human-in-the-loop approval system for high-risk autonomous operations.

Provides mechanisms for requesting, tracking, and enforcing human approvals
for operations that exceed safety thresholds or require explicit authorization.
"""

import asyncio
import uuid
import json
from typing import Dict, Optional, List, Any, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import threading
from queue import Queue, Empty
import hashlib


class ApprovalStatus(Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    CANCELLED = "cancelled"


class ApprovalPriority(Enum):
    """Priority levels for approval requests."""

    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"  # Important, should be reviewed soon
    MEDIUM = "medium"  # Standard priority
    LOW = "low"  # Can wait
    BACKGROUND = "background"  # Non-urgent


class ApprovalMode(Enum):
    """Approval processing modes."""

    MANUAL = "manual"  # Always require human approval
    AUTO = "auto"  # Auto-approve based on rules
    HYBRID = "hybrid"  # Mix of manual and auto based on context
    BATCH = "batch"  # Group approvals for efficiency


@dataclass
class ApprovalPolicy:
    """Policy for automatic approval decisions."""

    policy_id: str
    name: str
    description: str
    conditions: Dict[str, Any]  # Conditions for auto-approval
    action: str  # "approve" or "reject"
    enabled: bool = True
    max_auto_approvals: int = 100  # Max auto-approvals per day
    valid_until: Optional[datetime] = None

    def matches(self, request_details: Dict[str, Any]) -> bool:
        """Check if policy conditions match the request."""
        for key, expected_value in self.conditions.items():
            if key not in request_details:
                return False

            actual_value = request_details[key]

            # Handle different comparison types
            if isinstance(expected_value, dict):
                if "$lt" in expected_value and actual_value >= expected_value["$lt"]:
                    return False
                if "$gt" in expected_value and actual_value <= expected_value["$gt"]:
                    return False
                if "$in" in expected_value and actual_value not in expected_value["$in"]:
                    return False
                if "$regex" in expected_value:
                    import re

                    if not re.match(expected_value["$regex"], str(actual_value)):
                        return False
            elif actual_value != expected_value:
                return False

        return True


@dataclass
class ApprovalRequest:
    """Represents a request for approval."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""
    operation_details: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    requester: str = "autonomous_agent"
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[str] = None
    approval_time: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return {
            "request_id": self.request_id,
            "operation_type": self.operation_type,
            "operation_details": self.operation_details,
            "risk_level": self.risk_level,
            "priority": self.priority.value,
            "requester": self.requester,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "approver": self.approver,
            "approval_time": self.approval_time.isoformat() if self.approval_time else None,
            "rejection_reason": self.rejection_reason,
            "metadata": self.metadata,
        }

    def is_expired(self) -> bool:
        """Check if request has expired."""
        if self.expires_at and datetime.now() > self.expires_at:
            return True
        return False


class ApprovalSystem:
    """
    Comprehensive approval system for human-in-the-loop control
    of autonomous operations.
    """

    def __init__(
        self,
        mode: ApprovalMode = ApprovalMode.HYBRID,
        default_timeout_minutes: int = 30,
        audit_logger: Optional[Any] = None,
    ):
        """
        Initialize approval system.

        Args:
            mode: Approval processing mode
            default_timeout_minutes: Default timeout for approval requests
            audit_logger: Optional audit logger
        """
        self.mode = mode
        self.default_timeout_minutes = default_timeout_minutes
        self.audit_logger = audit_logger

        # Request tracking
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: List[ApprovalRequest] = []
        self.max_completed_history = 10000

        # Policies for auto-approval
        self.policies: Dict[str, ApprovalPolicy] = {}
        self.policy_usage_count: Dict[str, int] = {}
        self.policy_usage_date: Dict[str, datetime] = {}

        # Callbacks and notifications
        self.approval_callbacks: Dict[str, Callable] = {}
        self.notification_handlers: List[Callable] = []

        # Approval queue for batch processing
        self.approval_queue = Queue()
        self.batch_processor_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "expired": 0,
            "auto_approved": 0,
            "auto_rejected": 0,
            "average_response_time": 0.0,
        }

        # Initialize default policies
        self._init_default_policies()

    def _init_default_policies(self) -> None:
        """Initialize default approval policies."""

        # Policy: Auto-approve low-risk read operations
        self.add_policy(
            ApprovalPolicy(
                policy_id="POL001",
                name="Low Risk Read Operations",
                description="Auto-approve low-risk read-only operations",
                conditions={
                    "risk_level": "low",
                    "operation_type": {"$in": ["file_read", "list_files", "get_status"]},
                },
                action="approve",
            )
        )

        # Policy: Auto-reject critical system operations
        self.add_policy(
            ApprovalPolicy(
                policy_id="POL002",
                name="Critical System Operations",
                description="Auto-reject critical system modifications",
                conditions={
                    "risk_level": "critical",
                    "operation_type": {"$in": ["system_delete", "permission_change"]},
                },
                action="reject",
            )
        )

        # Policy: Auto-approve small file writes
        self.add_policy(
            ApprovalPolicy(
                policy_id="POL003",
                name="Small File Writes",
                description="Auto-approve writing small files",
                conditions={
                    "operation_type": "file_write",
                    "file_size": {"$lt": 1048576},  # Less than 1MB
                },
                action="approve",
            )
        )

    def add_policy(self, policy: ApprovalPolicy) -> None:
        """Add an approval policy."""
        self.policies[policy.policy_id] = policy
        self.policy_usage_count[policy.policy_id] = 0
        self.policy_usage_date[policy.policy_id] = datetime.now()

        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="APPROVAL_POLICY_ADDED",
                details={"policy_id": policy.policy_id, "name": policy.name},
            )

    def remove_policy(self, policy_id: str) -> None:
        """Remove an approval policy."""
        if policy_id in self.policies:
            del self.policies[policy_id]

            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type="APPROVAL_POLICY_REMOVED", details={"policy_id": policy_id}
                )

    async def request_approval(
        self,
        operation_type: str,
        operation_details: Dict[str, Any],
        risk_level: str = "medium",
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        timeout_minutes: Optional[int] = None,
        callback: Optional[Callable] = None,
    ) -> ApprovalRequest:
        """
        Request approval for an operation.

        Args:
            operation_type: Type of operation requiring approval
            operation_details: Details about the operation
            risk_level: Risk level of the operation
            priority: Priority of the approval request
            timeout_minutes: Custom timeout for this request
            callback: Optional callback when approval decision is made

        Returns:
            ApprovalRequest object
        """
        # Create request
        timeout = timeout_minutes or self.default_timeout_minutes
        request = ApprovalRequest(
            operation_type=operation_type,
            operation_details=operation_details,
            risk_level=risk_level,
            priority=priority,
            expires_at=datetime.now() + timedelta(minutes=timeout),
        )

        # Update statistics
        self.stats["total_requests"] += 1

        # Log the request
        if self.audit_logger:
            self.audit_logger.log_event(event_type="APPROVAL_REQUESTED", details=request.to_dict())

        # Check for auto-approval/rejection
        if self.mode in [ApprovalMode.AUTO, ApprovalMode.HYBRID]:
            auto_decision = self._check_auto_approval(request)
            if auto_decision:
                request.status = auto_decision
                request.approval_time = datetime.now()

                if auto_decision == ApprovalStatus.AUTO_APPROVED:
                    request.approver = "auto_policy"
                    self.stats["auto_approved"] += 1
                else:
                    request.rejection_reason = "Auto-rejected by policy"
                    self.stats["auto_rejected"] += 1

                self._complete_request(request)

                if callback:
                    callback(request)

                return request

        # Add to pending if not auto-decided
        self.pending_requests[request.request_id] = request

        # Register callback if provided
        if callback:
            self.approval_callbacks[request.request_id] = callback

        # Send notifications
        self._send_notifications(request)

        # Add to batch queue if in batch mode
        if self.mode == ApprovalMode.BATCH:
            self.approval_queue.put(request)

        return request

    def _check_auto_approval(self, request: ApprovalRequest) -> Optional[ApprovalStatus]:
        """Check if request can be auto-approved or rejected."""
        request_dict = {
            "operation_type": request.operation_type,
            "risk_level": request.risk_level,
            **request.operation_details,
        }

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            # Check if policy is still valid
            if policy.valid_until and datetime.now() > policy.valid_until:
                continue

            # Check daily usage limit
            if self._check_policy_usage_limit(policy):
                continue

            if policy.matches(request_dict):
                # Update usage count
                self._update_policy_usage(policy.policy_id)

                if self.audit_logger:
                    self.audit_logger.log_event(
                        event_type="AUTO_APPROVAL_POLICY_MATCHED",
                        details={
                            "request_id": request.request_id,
                            "policy_id": policy.policy_id,
                            "action": policy.action,
                        },
                    )

                if policy.action == "approve":
                    return ApprovalStatus.AUTO_APPROVED
                elif policy.action == "reject":
                    return ApprovalStatus.AUTO_REJECTED

        return None

    def _check_policy_usage_limit(self, policy: ApprovalPolicy) -> bool:
        """Check if policy has exceeded daily usage limit."""
        policy_id = policy.policy_id

        # Reset counter if new day
        if policy_id in self.policy_usage_date:
            last_use = self.policy_usage_date[policy_id]
            if last_use.date() != datetime.now().date():
                self.policy_usage_count[policy_id] = 0
                self.policy_usage_date[policy_id] = datetime.now()

        # Check limit
        current_usage = self.policy_usage_count.get(policy_id, 0)
        return current_usage >= policy.max_auto_approvals

    def _update_policy_usage(self, policy_id: str) -> None:
        """Update policy usage statistics."""
        self.policy_usage_count[policy_id] = self.policy_usage_count.get(policy_id, 0) + 1
        self.policy_usage_date[policy_id] = datetime.now()

    def approve(
        self, request_id: str, approver: str = "human", comments: Optional[str] = None
    ) -> bool:
        """
        Approve a pending request.

        Args:
            request_id: ID of the request to approve
            approver: Identifier of the approver
            comments: Optional approval comments

        Returns:
            True if approved successfully, False otherwise
        """
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests[request_id]

        # Check if expired
        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            self._complete_request(request)
            return False

        # Approve the request
        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.approval_time = datetime.now()

        if comments:
            request.metadata["approval_comments"] = comments

        # Update statistics
        self.stats["approved"] += 1
        self._update_response_time(request)

        # Log approval
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="APPROVAL_GRANTED",
                details={"request_id": request_id, "approver": approver, "comments": comments},
            )

        # Complete the request
        self._complete_request(request)

        # Trigger callback if registered
        if request_id in self.approval_callbacks:
            callback = self.approval_callbacks[request_id]
            callback(request)
            del self.approval_callbacks[request_id]

        return True

    def reject(self, request_id: str, reason: str, rejector: str = "human") -> bool:
        """
        Reject a pending request.

        Args:
            request_id: ID of the request to reject
            reason: Reason for rejection
            rejector: Identifier of the rejector

        Returns:
            True if rejected successfully, False otherwise
        """
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests[request_id]

        # Reject the request
        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason
        request.approver = rejector
        request.approval_time = datetime.now()

        # Update statistics
        self.stats["rejected"] += 1
        self._update_response_time(request)

        # Log rejection
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="APPROVAL_REJECTED",
                details={"request_id": request_id, "rejector": rejector, "reason": reason},
            )

        # Complete the request
        self._complete_request(request)

        # Trigger callback if registered
        if request_id in self.approval_callbacks:
            callback = self.approval_callbacks[request_id]
            callback(request)
            del self.approval_callbacks[request_id]

        return True

    def _complete_request(self, request: ApprovalRequest) -> None:
        """Move request from pending to completed."""
        if request.request_id in self.pending_requests:
            del self.pending_requests[request.request_id]

        self.completed_requests.append(request)

        # Trim history if too large
        if len(self.completed_requests) > self.max_completed_history:
            self.completed_requests = self.completed_requests[-self.max_completed_history :]

    def _update_response_time(self, request: ApprovalRequest) -> None:
        """Update average response time statistic."""
        if request.approval_time:
            response_time = (request.approval_time - request.timestamp).total_seconds()

            # Update moving average
            current_avg = self.stats["average_response_time"]
            total_completed = self.stats["approved"] + self.stats["rejected"]

            if total_completed > 0:
                self.stats["average_response_time"] = (
                    current_avg * (total_completed - 1) + response_time
                ) / total_completed

    def _send_notifications(self, request: ApprovalRequest) -> None:
        """Send notifications for new approval request."""
        for handler in self.notification_handlers:
            try:
                handler(request)
            except Exception as e:
                if self.audit_logger:
                    self.audit_logger.log_error("Notification handler failed", {"error": str(e)})

    def register_notification_handler(self, handler: Callable) -> None:
        """Register a notification handler for approval requests."""
        self.notification_handlers.append(handler)

    def check_expired_requests(self) -> List[ApprovalRequest]:
        """Check and expire timed-out requests."""
        expired = []

        for request_id, request in list(self.pending_requests.items()):
            if request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                expired.append(request)

                # Update statistics
                self.stats["expired"] += 1

                # Log expiration
                if self.audit_logger:
                    self.audit_logger.log_event(
                        event_type="APPROVAL_EXPIRED", details={"request_id": request_id}
                    )

                # Complete the request
                self._complete_request(request)

                # Trigger callback if registered
                if request_id in self.approval_callbacks:
                    callback = self.approval_callbacks[request_id]
                    callback(request)
                    del self.approval_callbacks[request_id]

        return expired

    def get_pending_requests(
        self, priority: Optional[ApprovalPriority] = None
    ) -> List[ApprovalRequest]:
        """
        Get list of pending approval requests.

        Args:
            priority: Optional filter by priority

        Returns:
            List of pending requests
        """
        requests = list(self.pending_requests.values())

        if priority:
            requests = [r for r in requests if r.priority == priority]

        # Sort by priority and timestamp
        priority_order = {
            ApprovalPriority.CRITICAL: 0,
            ApprovalPriority.HIGH: 1,
            ApprovalPriority.MEDIUM: 2,
            ApprovalPriority.LOW: 3,
            ApprovalPriority.BACKGROUND: 4,
        }

        requests.sort(key=lambda r: (priority_order[r.priority], r.timestamp))

        return requests

    def batch_approve(self, request_ids: List[str], approver: str = "human") -> Dict[str, bool]:
        """
        Approve multiple requests at once.

        Args:
            request_ids: List of request IDs to approve
            approver: Identifier of the approver

        Returns:
            Dictionary mapping request IDs to success status
        """
        results = {}

        for request_id in request_ids:
            results[request_id] = self.approve(request_id, approver)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get approval system statistics."""
        return {
            **self.stats,
            "pending_count": len(self.pending_requests),
            "completed_count": len(self.completed_requests),
            "active_policies": len([p for p in self.policies.values() if p.enabled]),
            "policy_usage": {pid: count for pid, count in self.policy_usage_count.items()},
        }

    def export_approval_history(self, filepath: str) -> None:
        """Export approval history to JSON file."""
        history = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "pending_requests": [r.to_dict() for r in self.pending_requests.values()],
            "recent_completed": [r.to_dict() for r in self.completed_requests[-100:]],
            "policies": [
                {
                    "policy_id": p.policy_id,
                    "name": p.name,
                    "enabled": p.enabled,
                    "usage_count": self.policy_usage_count.get(p.policy_id, 0),
                }
                for p in self.policies.values()
            ],
        }

        with open(filepath, "w") as f:
            json.dump(history, f, indent=2)

    async def wait_for_approval(self, request_id: str, check_interval: int = 5) -> ApprovalRequest:
        """
        Wait for approval decision on a request.

        Args:
            request_id: ID of the request to wait for
            check_interval: Seconds between status checks

        Returns:
            Updated ApprovalRequest when decision is made
        """
        while request_id in self.pending_requests:
            await asyncio.sleep(check_interval)

            # Check if expired
            self.check_expired_requests()

        # Find in completed requests
        for request in reversed(self.completed_requests):
            if request.request_id == request_id:
                return request

        # Not found, create expired request
        expired_request = ApprovalRequest(request_id=request_id, status=ApprovalStatus.EXPIRED)
        return expired_request
