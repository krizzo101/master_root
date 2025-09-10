#!/usr/bin/env python3
"""
Domain layer following Domain-Driven Design principles.

This module provides value objects, entities, and aggregates for
modeling the agent orchestration domain with rich behavior.
"""

from .aggregates import TaskAggregate
from .entities import AgentTask
from .value_objects import (
    ResultStatus,
    RetryPolicy,
    TaskMetrics,
    TaskPriority,
    TaskResult,
    TaskStatus,
    ValidationResult,
)

__all__ = [
    # Aggregates
    "TaskAggregate",
    # Entities
    "AgentTask",
    # Value Objects
    "TaskResult",
    "TaskStatus",
    "ResultStatus",
    "ValidationResult",
    "RetryPolicy",
    "TaskMetrics",
    "TaskPriority",
]
