"""
OAMAT Agent Factory Package

Modularized agent factory for creating LangGraph agents with standardized tools.
Refactored from the original agent_factory.py for better organization and maintainability.
"""

# Import main classes
from datetime import datetime
from typing import Any, Dict, List

# Import shared models from original file
from pydantic import BaseModel, Field

from src.applications.oamat.agents.agent_factory.factory import AgentFactory

# Import request models
from src.applications.oamat.agents.agent_factory.tools import (
    CodeRequest,
    DocumentationRequest,
    ResearchRequest,
    ReviewRequest,
)
from src.applications.oamat.agents.agent_factory.tools_manager import (
    LangGraphAgentTools,
)


class AgentOutput(BaseModel):
    """Standardized output format for LangGraph agents"""

    agent_name: str = Field(..., description="Name of the agent")
    agent_role: str = Field(..., description="Role/type of the agent")
    success: bool = Field(..., description="Whether the task succeeded")
    result: Any = Field(None, description="Main result from agent execution")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    confidence_score: float = Field(
        0.7, ge=0.0, le=1.0, description="Confidence in results"
    )
    errors: list[str] = Field(
        default_factory=list, description="Any errors encountered"
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Export all public classes and models
__all__ = [
    # Main classes
    "AgentFactory",
    "LangGraphAgentTools",
    # Request models
    "ResearchRequest",
    "CodeRequest",
    "ReviewRequest",
    "DocumentationRequest",
    # Output model
    "AgentOutput",
]
