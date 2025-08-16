from typing import List

from pydantic import BaseModel, Field


class AgentSpecificationOutput(BaseModel):
    """Structured output schema for O3 agent specification generation

    IMPORTANT: This schema expects a JSON object with an 'agent_specifications' key containing an array.
    DO NOT return just the array directly - wrap it in this object structure.
    """

    agent_specifications: List["AgentSpecification"] = Field(
        description="Array of agent specifications for the subdivided workflow. This must be wrapped in a JSON object with key 'agent_specifications'",
        min_items=1,
        max_items=10,
    )


class AgentSpecification(BaseModel):
    """Individual agent specification with all required fields"""

    agent_id: str = Field(
        description="Unique identifier for the agent (snake_case format)",
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    role_name: str = Field(
        description="Human-readable role name for the agent",
        min_length=3,
        max_length=100,
    )

    domain_specialization: str = Field(
        description="Specific technical domain this agent specializes in",
        min_length=10,
        max_length=200,
    )

    system_prompt: str = Field(
        description="Detailed prompt defining agent behavior and expertise",
        min_length=200,
        max_length=2000,
    )

    tools: List[str] = Field(
        description="List of tool names this agent needs", default_factory=list
    )

    deliverables: List[str] = Field(
        description="Specific outputs this agent will produce", default_factory=list
    )

    handoff_targets: List[str] = Field(
        description="Other agents this agent can hand off to", default_factory=list
    )

    integration_requirements: List[str] = Field(
        description="How this agent's output integrates with others",
        default_factory=list,
    )


# Update forward references
AgentSpecificationOutput.model_rebuild()
