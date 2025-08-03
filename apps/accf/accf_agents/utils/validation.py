"""
Validation utilities for the ACCF Research Agent.

This module provides validation functions for tasks, results, and other data structures.
"""

from typing import Dict, Any, List
from ..agents import Task, Result


def validate_task(task: Task) -> List[str]:
    """Validate a task and return list of validation errors."""
    errors = []

    if not task.id:
        errors.append("Task ID is required")

    if not task.type:
        errors.append("Task type is required")

    if task.parameters is None:
        errors.append("Task parameters are required")

    if task.priority < 1 or task.priority > 10:
        errors.append("Task priority must be between 1 and 10")

    if task.timeout is not None and task.timeout <= 0:
        errors.append("Task timeout must be positive")

    return errors


def validate_result(result: Result) -> List[str]:
    """Validate a result and return list of validation errors."""
    errors = []

    if not result.task_id:
        errors.append("Result task ID is required")

    if result.status not in ["success", "error", "timeout"]:
        errors.append("Result status must be one of: success, error, timeout")

    if result.data is None:
        errors.append("Result data is required")

    if result.execution_time is not None and result.execution_time < 0:
        errors.append("Execution time must be non-negative")

    return errors


def validate_parameters(
    parameters: Dict[str, Any], required_keys: List[str]
) -> List[str]:
    """Validate parameters against required keys."""
    errors = []

    for key in required_keys:
        if key not in parameters:
            errors.append(f"Required parameter '{key}' is missing")
        elif parameters[key] is None:
            errors.append(f"Required parameter '{key}' cannot be None")

    return errors


def sanitize_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize parameters to remove sensitive information."""
    sanitized = parameters.copy()

    # Remove sensitive keys
    sensitive_keys = ["password", "api_key", "secret", "token"]
    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = "***"

    return sanitized
