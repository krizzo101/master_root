"""Exception classes for the orchestrator module."""

from typing import Optional


class OrchestrationError(Exception):
    """Error raised during orchestration."""

    def __init__(self, error_type: str, message: str, task_name: Optional[str] = None):
        self.error_type = error_type
        self.message = message
        self.task_name = task_name
        super().__init__(f"{error_type}: {message}")


class PipelineError(Exception):
    """Error raised during pipeline execution."""

    def __init__(self, message: str, pipeline_name: Optional[str] = None):
        self.message = message
        self.pipeline_name = pipeline_name
        super().__init__(f"Pipeline error: {message}")


class TaskExecutionError(Exception):
    """Error raised during task execution."""

    def __init__(self, message: str, task_name: Optional[str] = None):
        self.message = message
        self.task_name = task_name
        super().__init__(f"Task execution error: {message}")


class ValidationError(Exception):
    """Error raised during validation."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(f"Validation error: {message}")


class ResourceError(Exception):
    """Error raised when resources are insufficient."""

    def __init__(self, message: str, resource_type: Optional[str] = None):
        self.message = message
        self.resource_type = resource_type
        super().__init__(f"Resource error: {message}")


class TimeoutError(Exception):
    """Error raised when operations timeout."""

    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        self.message = message
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Timeout error: {message}")
