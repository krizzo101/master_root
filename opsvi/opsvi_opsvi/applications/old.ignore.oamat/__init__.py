"""
OAMAT (Orchestration and Automation Management Application and Tools)

Top-level module providing access to all OAMAT components.
"""

# Import key components for easy access
from src.applications.multi_agent_orchestration.orchestrator.workflow_orchestrator import (
    WorkflowOrchestrator,
)
from src.applications.oamat.agents import (
    AGENT_REGISTRY,
    MCP_TOOL_REGISTRY,
    OPERATIONAL_GUIDELINES,
    SYSTEM_IDENTITY,
    WORKFLOW_PATTERNS,
    AgentFactory,
    AgentOutput,
    CodeRequest,
    DocumentationRequest,
    EnhancedRequestAnalysis,
    EnhancedWorkflowNode,
    EnhancedWorkflowPlan,
    LangGraphAgentTools,
    LLMBaseAgent,
    ResearchRequest,
    ReviewRequest,
    TaskComplexity,
    WorkflowManager,
    WorkflowStrategy,
)
from src.applications.oamat.workflows import (
    AgenticWorkflowState,
)

# Version information
__version__ = "1.0.0"
__author__ = "OAMAT Development Team"

# Export everything for easy top-level access
__all__ = [
    # Core classes
    "WorkflowOrchestrator",
    "WorkflowManager",
    "AgentFactory",
    "LangGraphAgentTools",
    # Supporting classes
    "LLMBaseAgent",
    "AgenticWorkflowState",
    # Data models
    "EnhancedRequestAnalysis",
    "EnhancedWorkflowPlan",
    "EnhancedWorkflowNode",
    "TaskComplexity",
    "WorkflowStrategy",
    "AgentOutput",
    "ResearchRequest",
    "CodeRequest",
    "ReviewRequest",
    "DocumentationRequest",
    # System constants
    "AGENT_REGISTRY",
    "MCP_TOOL_REGISTRY",
    "WORKFLOW_PATTERNS",
    "OPERATIONAL_GUIDELINES",
    "SYSTEM_IDENTITY",
    # Version info
    "__version__",
    "__author__",
]
