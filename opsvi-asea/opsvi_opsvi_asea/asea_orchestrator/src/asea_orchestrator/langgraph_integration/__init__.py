"""
ASEA-LangGraph Integration Module

This module provides integration between the ASEA orchestrator and LangGraph,
allowing existing ASEA plugins to work within LangGraph workflows while
preserving all existing functionality.

Phase 1: Basic Integration
- ASEAState schema and plugin adapters
- Workflow conversion and checkpointing
- Template engine for backward compatibility

Phase 2: Enhanced Capabilities  
- Conditional routing and dynamic workflows
- Streaming and real-time feedback
- Human-in-the-loop approvals and interventions
- Advanced state management and error recovery
"""

# Phase 1 - Basic Integration
from .state import ASEAState
from .plugin_adapter import ASEAPluginNode
from .workflow_converter import WorkflowConverter
from .checkpointer import ASEAArangoCheckpointer

# Phase 2 - Enhanced Capabilities
from .enhanced_workflows import (
    EnhancedWorkflowBuilder,
    ConditionalRouter,
    StreamingManager,
    HumanInTheLoopManager,
)
from .error_recovery import (
    ErrorRecoveryManager,
    RetryStrategy,
    ErrorSeverity,
    create_default_error_patterns,
)

__all__ = [
    # Phase 1
    "ASEAState",
    "ASEAPluginNode",
    "WorkflowConverter",
    "ASEAArangoCheckpointer",
    # Phase 2
    "EnhancedWorkflowBuilder",
    "ConditionalRouter",
    "StreamingManager",
    "HumanInTheLoopManager",
    "ErrorRecoveryManager",
    "RetryStrategy",
    "ErrorSeverity",
    "create_default_error_patterns",
]
