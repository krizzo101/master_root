"""
Agents-specific exceptions.

Extends foundation exceptions with Agents domain errors.
"""

from opsvi_foundation import ComponentError


class AgentsError(ComponentError):
    """Base exception for opsvi-agents."""
    pass


class AgentsValidationError(AgentsError):
    """Validation error specific to opsvi-agents."""
    pass


class AgentsConfigurationError(AgentsError):
    """Configuration error specific to opsvi-agents."""
    pass
