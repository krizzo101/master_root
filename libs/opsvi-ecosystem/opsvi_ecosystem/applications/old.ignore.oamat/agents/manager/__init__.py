"""
OAMAT Manager Package

Modularized workflow manager components for better maintainability.
"""

# Import the main WorkflowManager from the workflow_manager module
# Import modular components
from src.applications.oamat.agents.manager.request_analyzer import RequestAnalyzer
from src.applications.oamat.agents.manager.utilities import (
    clean_json_response,
    extract_json_from_response,
    extract_structured_info,
    format_dict_for_display,
    format_list_for_display,
    merge_dictionaries,
    safe_get_nested_value,
    serialize_analysis,
    truncate_text,
    validate_json_structure,
)
from src.applications.oamat.agents.manager.workflow_manager import WorkflowManager

# Import all models that were previously available from manager
from src.applications.oamat.agents.models import (
    ClarificationQuestion,
    DynamicQuestionUpdate,
    EnhancedRequestAnalysis,
    EnhancedWorkflowNode,
    EnhancedWorkflowPlan,
    ExpandedPrompt,
    NodeMetadata,
    NodeResourceRequirements,
    PlanMetadata,
    PlanResourceRequirements,
    ProcessingRequest,
    ProcessingResponse,
    QuestionAnswer,
    RefinedSpecification,
    RefinedSpecUpdate,
    TaskComplexity,
    UserClarificationResponse,
    WorkflowStrategy,
)

# Import all registry constants that were previously available from manager
from src.applications.oamat.agents.registry import (
    AGENT_REGISTRY,
    MCP_TOOL_REGISTRY,
    OPERATIONAL_GUIDELINES,
    SYSTEM_IDENTITY,
    WORKFLOW_PATTERNS,
)

__all__ = [
    # Main WorkflowManager class
    "WorkflowManager",
    # Model classes
    "TaskComplexity",
    "WorkflowStrategy",
    "EnhancedRequestAnalysis",
    "EnhancedWorkflowNode",
    "EnhancedWorkflowPlan",
    "ProcessingRequest",
    "ProcessingResponse",
    "NodeResourceRequirements",
    "NodeMetadata",
    "PlanResourceRequirements",
    "PlanMetadata",
    "ClarificationQuestion",
    "ExpandedPrompt",
    "QuestionAnswer",
    "UserClarificationResponse",
    "RefinedSpecification",
    "RefinedSpecUpdate",
    "DynamicQuestionUpdate",
    # Registry constants
    "AGENT_REGISTRY",
    "MCP_TOOL_REGISTRY",
    "WORKFLOW_PATTERNS",
    "OPERATIONAL_GUIDELINES",
    "SYSTEM_IDENTITY",
    # Modular components
    "RequestAnalyzer",
    "extract_structured_info",
    "clean_json_response",
    "extract_json_from_response",
    "serialize_analysis",
    "format_list_for_display",
    "format_dict_for_display",
    "truncate_text",
    "validate_json_structure",
    "safe_get_nested_value",
    "merge_dictionaries",
]
