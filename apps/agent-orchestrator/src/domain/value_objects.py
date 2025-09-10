#!/usr/bin/env python3
"""
Domain Value Objects following DDD principles

Value objects are immutable objects that represent domain concepts
without identity. They are compared by their values, not references.
"""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Task execution status enumeration"""

    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResultStatus(str, Enum):
    """Result status enumeration"""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskResult:
    """
    Immutable value object representing task execution result.

    This value object encapsulates the outcome of a task execution,
    including status, data, errors, and execution metadata.
    """

    status: ResultStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize frozen fields with defaults"""
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    @classmethod
    def success(
        cls,
        data: Any = None,
        execution_time: float = None,
        metadata: Dict[str, Any] = None,
    ) -> "TaskResult":
        """Factory method for successful result"""
        return cls(
            status=ResultStatus.SUCCESS,
            data=data,
            execution_time=execution_time,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        error: str,
        error_type: str = None,
        execution_time: float = None,
        retry_count: int = 0,
        metadata: Dict[str, Any] = None,
    ) -> "TaskResult":
        """Factory method for failed result"""
        return cls(
            status=ResultStatus.FAILURE,
            error=error,
            error_type=error_type or "UnknownError",
            execution_time=execution_time,
            retry_count=retry_count,
            metadata=metadata or {},
        )

    @classmethod
    def partial_success(
        cls,
        data: Any = None,
        error: str = None,
        execution_time: float = None,
        metadata: Dict[str, Any] = None,
    ) -> "TaskResult":
        """Factory method for partial success result"""
        return cls(
            status=ResultStatus.PARTIAL_SUCCESS,
            data=data,
            error=error,
            execution_time=execution_time,
            metadata=metadata or {},
        )

    @classmethod
    def timeout(
        cls,
        error: str = "Task execution timed out",
        execution_time: float = None,
        retry_count: int = 0,
        metadata: Dict[str, Any] = None,
    ) -> "TaskResult":
        """Factory method for timeout result"""
        return cls(
            status=ResultStatus.TIMEOUT,
            error=error,
            error_type="TimeoutError",
            execution_time=execution_time,
            retry_count=retry_count,
            metadata=metadata or {},
        )

    @classmethod
    def cancelled(
        cls, reason: str = "Task was cancelled", metadata: Dict[str, Any] = None
    ) -> "TaskResult":
        """Factory method for cancelled result"""
        return cls(
            status=ResultStatus.CANCELLED,
            error=reason,
            error_type="CancellationError",
            metadata=metadata or {},
        )

    def is_success(self) -> bool:
        """Check if result represents success"""
        return self.status in [ResultStatus.SUCCESS, ResultStatus.PARTIAL_SUCCESS]

    def is_failure(self) -> bool:
        """Check if result represents failure"""
        return self.status in [ResultStatus.FAILURE, ResultStatus.TIMEOUT]

    def is_retryable(self) -> bool:
        """Check if task can be retried based on result"""
        return self.status in [
            ResultStatus.FAILURE,
            ResultStatus.TIMEOUT,
        ] and self.error_type not in [
            "ValidationError",
            "AuthenticationError",
            "PermissionError",
        ]

    def with_retry(self, retry_count: int) -> "TaskResult":
        """Create new result with updated retry count"""
        return replace(self, retry_count=retry_count)

    def with_metadata(self, key: str, value: Any) -> "TaskResult":
        """Create new result with additional metadata"""
        new_metadata = {**self.metadata, key: value}
        return replace(self, metadata=new_metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "error_type": self.error_type,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable value object for validation results.

    Represents the outcome of validating a task or entity.
    """

    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize frozen fields with defaults"""
        if self.errors is None:
            object.__setattr__(self, "errors", [])
        if self.warnings is None:
            object.__setattr__(self, "warnings", [])
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    @classmethod
    def valid(
        cls, warnings: List[str] = None, metadata: Dict[str, Any] = None
    ) -> "ValidationResult":
        """Factory method for valid result"""
        return cls(is_valid=True, warnings=warnings or [], metadata=metadata or {})

    @classmethod
    def invalid(
        cls,
        errors: List[str],
        warnings: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> "ValidationResult":
        """Factory method for invalid result"""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            metadata=metadata or {},
        )

    def add_error(self, error: str) -> "ValidationResult":
        """Create new result with additional error"""
        new_errors = self.errors + [error]
        return replace(self, is_valid=False, errors=new_errors)

    def add_warning(self, warning: str) -> "ValidationResult":
        """Create new result with additional warning"""
        new_warnings = self.warnings + [warning]
        return replace(self, warnings=new_warnings)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge with another validation result"""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            metadata={**self.metadata, **other.metadata},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class RetryPolicy:
    """
    Immutable value object for retry configuration.

    Defines how and when tasks should be retried.
    """

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: List[str] = None
    non_retryable_errors: List[str] = None

    def __post_init__(self):
        """Initialize frozen fields with defaults"""
        if self.retryable_errors is None:
            object.__setattr__(
                self,
                "retryable_errors",
                ["TimeoutError", "ConnectionError", "NetworkError", "RateLimitError"],
            )
        if self.non_retryable_errors is None:
            object.__setattr__(
                self,
                "non_retryable_errors",
                [
                    "ValidationError",
                    "AuthenticationError",
                    "PermissionError",
                    "NotFoundError",
                ],
            )

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given retry attempt"""
        if attempt <= 0:
            return 0

        delay = min(
            self.initial_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay,
        )

        if self.jitter:
            import random

            delay *= 0.5 + random.random()

        return delay

    def should_retry(self, error_type: str, attempt: int) -> bool:
        """Determine if retry should be attempted"""
        if attempt >= self.max_attempts:
            return False

        if error_type in self.non_retryable_errors:
            return False

        if self.retryable_errors and error_type not in self.retryable_errors:
            return False

        return True

    def with_max_attempts(self, max_attempts: int) -> "RetryPolicy":
        """Create new policy with different max attempts"""
        return replace(self, max_attempts=max_attempts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "max_attempts": self.max_attempts,
            "initial_delay": self.initial_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter,
            "retryable_errors": self.retryable_errors,
            "non_retryable_errors": self.non_retryable_errors,
        }


@dataclass(frozen=True)
class TaskMetrics:
    """
    Immutable value object for task execution metrics.

    Captures performance and quality metrics for task execution.
    """

    execution_time: float
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    token_count: Optional[int] = None
    quality_score: Optional[float] = None
    retry_count: int = 0
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize frozen fields with defaults"""
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())

    def with_quality_score(self, score: float) -> "TaskMetrics":
        """Create new metrics with quality score"""
        return replace(self, quality_score=score)

    def with_resource_usage(self, cpu: float, memory: float) -> "TaskMetrics":
        """Create new metrics with resource usage"""
        return replace(self, cpu_usage=cpu, memory_usage=memory)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "execution_time": self.execution_time,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "token_count": self.token_count,
            "quality_score": self.quality_score,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass(frozen=True)
class TaskPriority:
    """
    Immutable value object for task priority.

    Represents task execution priority with deadline support.
    """

    level: int  # 0-100, higher is more important
    deadline: Optional[datetime] = None
    preemptible: bool = True

    @classmethod
    def high(cls, deadline: datetime = None) -> "TaskPriority":
        """Factory method for high priority"""
        return cls(level=80, deadline=deadline, preemptible=False)

    @classmethod
    def normal(cls, deadline: datetime = None) -> "TaskPriority":
        """Factory method for normal priority"""
        return cls(level=50, deadline=deadline, preemptible=True)

    @classmethod
    def low(cls) -> "TaskPriority":
        """Factory method for low priority"""
        return cls(level=20, deadline=None, preemptible=True)

    def is_urgent(self) -> bool:
        """Check if task is urgent based on deadline"""
        if not self.deadline:
            return False

        time_until_deadline = self.deadline - datetime.utcnow()
        return time_until_deadline < timedelta(hours=1)

    def effective_priority(self) -> int:
        """Calculate effective priority considering deadline"""
        priority = self.level

        if self.deadline:
            time_until_deadline = (self.deadline - datetime.utcnow()).total_seconds()
            if time_until_deadline < 3600:  # Less than 1 hour
                priority = min(100, priority + 30)
            elif time_until_deadline < 86400:  # Less than 1 day
                priority = min(100, priority + 10)

        return priority

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "level": self.level,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "preemptible": self.preemptible,
            "effective_priority": self.effective_priority(),
        }
