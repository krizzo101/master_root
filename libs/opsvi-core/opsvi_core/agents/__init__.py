"""
Agents module for opsvi-core.

Provides agent management, lifecycle, and communication.
"""

from .base_agent import (
    BaseAgent,
    AgentState,
    AgentCapability,
    AgentMetadata,
    AgentMessage
)

__all__ = [
    "BaseAgent",
    "AgentState",
    "AgentCapability",
    "AgentMetadata",
    "AgentMessage",
]
