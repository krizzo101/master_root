"""
Governance module for Autonomous Claude Agent.

Provides resource monitoring, safety rules, approval systems, and audit logging
to ensure safe, controlled, and accountable autonomous operations.
"""

from .resource_monitor import ResourceMonitor, ResourceLimits, ResourceMetrics
from .safety_rules import SafetyRules, SafetyViolation, SafetyLevel
from .approval_system import ApprovalSystem, ApprovalRequest, ApprovalStatus
from .audit_logger import AuditLogger, AuditEvent, AuditSeverity

__version__ = "1.0.0"

__all__ = [
    # Resource monitoring
    "ResourceMonitor",
    "ResourceLimits",
    "ResourceMetrics",
    # Safety rules
    "SafetyRules",
    "SafetyViolation",
    "SafetyLevel",
    # Approval system
    "ApprovalSystem",
    "ApprovalRequest",
    "ApprovalStatus",
    # Audit logging
    "AuditLogger",
    "AuditEvent",
    "AuditSeverity",
]
