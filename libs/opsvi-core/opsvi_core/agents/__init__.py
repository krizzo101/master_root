"""
Agents module for opsvi-core.

Provides agent management, lifecycle, and communication.
"""

from .base_agent import (
    AgentCapability,
    AgentMessage,
    AgentMetadata,
    AgentState,
    BaseAgent,
)

__all__ = [
    "BaseAgent",
    "AgentState",
    "AgentCapability",
    "AgentMetadata",
    "AgentMessage",
]
