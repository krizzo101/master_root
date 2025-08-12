"""
OAMAT Agents Module

Clean exports of current agent classes and components.
"""

# Import current classes with their proper names
from src.applications.oamat.agents.agent_factory import AgentOutput
from src.applications.oamat.agents.agent_factory.factory import AgentFactory
from src.applications.oamat.agents.agent_factory.tools import (
    CodeRequest,
    DocumentationRequest,
    ResearchRequest,
    ReviewRequest,
)
from src.applications.oamat.agents.agent_factory.tools_manager import (
    LangGraphAgentTools,
)
from src.applications.oamat.agents.llm_base_agent import LLMBaseAgent
from src.applications.oamat.agents.manager.workflow_manager import WorkflowManager
from src.applications.oamat.agents.models import (
    EnhancedRequestAnalysis,
    EnhancedWorkflowNode,
    EnhancedWorkflowPlan,
    TaskComplexity,
    WorkflowStrategy,
)
from src.applications.oamat.agents.registry import (
    AGENT_REGISTRY,
    MCP_TOOL_REGISTRY,
    OPERATIONAL_GUIDELINES,
    SYSTEM_IDENTITY,
    WORKFLOW_PATTERNS,
)

# Export current names only
__all__ = [
    # Core agent classes
    "WorkflowManager",
    "AgentFactory",
    "LangGraphAgentTools",
    "LLMBaseAgent",
    # Models and schemas
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
    # Constants and registries
    "AGENT_REGISTRY",
    "MCP_TOOL_REGISTRY",
    "WORKFLOW_PATTERNS",
    "OPERATIONAL_GUIDELINES",
    "SYSTEM_IDENTITY",
]
