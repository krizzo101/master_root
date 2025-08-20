from __future__ import annotations

from typing import Any, Dict

from .schemas.coder import CodeOutput
from .schemas.critic import CriticOutput
from .schemas.planner import PlanOutput
from .schemas.specifier import SpecificationOutput

# Schema registry for agent outputs
_registry: Dict[str, Any] = {}


def register_schema(key: str, schema: Any) -> None:
    """Register a schema for an agent output."""
    _registry[key] = schema


def get_schema(key: str) -> Any:
    """Get a schema by key."""
    return _registry.get(key)


def get_agent_schema(agent_type: str) -> Any:
    """Get schema for a specific agent type."""
    agent_schemas = {
        "planner": PlanOutput,
        "specifier": SpecificationOutput,
        "coder": CodeOutput,
        "critic": CriticOutput,
    }
    return agent_schemas.get(agent_type)


# Initialize with basic schemas for common agent outputs
def _initialize_basic_schemas():
    """Initialize basic schemas for common agent outputs."""

    # Planner output schema
    planner_schema = {
        "type": "object",
        "properties": {
            "plan": {"type": "string", "description": "High-level plan"},
            "tasks": {"type": "array", "items": {"type": "string"}},
            "timeline": {"type": "string"},
            "risks": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["plan", "tasks"],
    }

    # Specifier output schema
    specifier_schema = {
        "type": "object",
        "properties": {
            "requirements": {"type": "array", "items": {"type": "string"}},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["requirements"],
    }

    # Coder output schema
    coder_schema = {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "tests": {"type": "string"},
            "documentation": {"type": "string"},
            "dependencies": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["code"],
    }

    # Tester output schema
    tester_schema = {
        "type": "object",
        "properties": {
            "test_cases": {"type": "array", "items": {"type": "string"}},
            "coverage": {"type": "number"},
            "results": {"type": "string"},
        },
        "required": ["test_cases"],
    }

    # Critic output schema
    critic_schema = {
        "type": "object",
        "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "issues": {"type": "array", "items": {"type": "string"}},
            "recommendations": {"type": "array", "items": {"type": "string"}},
            "passed": {"type": "boolean"},
        },
        "required": ["score", "passed"],
    }

    # Register schemas
    register_schema("planner_output", planner_schema)
    register_schema("specifier_output", specifier_schema)
    register_schema("coder_output", coder_schema)
    register_schema("tester_output", tester_schema)
    register_schema("critic_output", critic_schema)


# Initialize schemas on module import
_initialize_basic_schemas()
