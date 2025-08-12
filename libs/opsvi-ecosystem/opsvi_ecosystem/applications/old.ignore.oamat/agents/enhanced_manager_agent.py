"""
BACKWARD COMPATIBILITY MODULE

This module provides backward compatibility for the renamed enhanced_manager_agent.py.
All imports from this module will work exactly as before.

The actual implementation has moved to manager.py for cleaner naming.
"""

# Re-export everything from the new manager module
from .manager import *

# Ensure the main class alias is available
from .manager import WorkflowManager as EnhancedManagerAgent

# Make sure all the original exports are available
__all__ = [
    "EnhancedManagerAgent",
    "EnhancedRequestAnalysis",
    "EnhancedWorkflowPlan",
    "EnhancedWorkflowNode",
    "TaskComplexity",
    "WorkflowStrategy",
    "AGENT_REGISTRY",
    "MCP_TOOL_REGISTRY",
    "WORKFLOW_PATTERNS",
    "OPERATIONAL_GUIDELINES",
    "SYSTEM_IDENTITY",
]
