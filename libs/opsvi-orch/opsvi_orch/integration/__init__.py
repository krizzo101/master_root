"""
Integration Module
------------------
Integration layers for connecting orchestration with existing systems.
"""

from .claude_integration import (
    ClaudeOrchestrationConfig,
    ClaudeOrchestrationIntegration,
    enhance_claude_code_server,
)

__all__ = [
    "ClaudeOrchestrationConfig",
    "ClaudeOrchestrationIntegration",
    "enhance_claude_code_server",
]
