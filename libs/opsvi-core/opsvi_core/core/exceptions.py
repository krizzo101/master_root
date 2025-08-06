"""
Core-specific exceptions.

Extends foundation exceptions with core domain errors.
"""

from opsvi_foundation import ComponentError


class CoreError(ComponentError):
    """Base exception for opsvi-core."""
    pass


class AgentError(CoreError):
    """Agent-related errors."""
    pass


class WorkflowError(CoreError):
    """Workflow execution errors."""
    pass
