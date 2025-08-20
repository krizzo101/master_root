"""Data models for Dynamic Prompt Generation (DPG) subsystem."""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class ContextBundle(BaseModel):
    """Compressed context bundle for prompt assembly."""

    purpose: str = Field(..., description="Purpose of this context bundle")
    tokens: int = Field(..., description="Estimated token count")
    summary: str = Field(..., description="Human-readable summary")
    sources: List[str] = Field(
        ..., description="Source identifiers (paths, cypher IDs)"
    )

    @validator("tokens")
    def validate_tokens(cls, v):
        if v < 0:
            raise ValueError("Token count must be non-negative")
        return v


class RoutingConfig(BaseModel):
    """Routing configuration for model selection."""

    role: str = Field(..., description="Agent role")
    task_type: str = Field(..., description="Task type")
    complexity: str = Field(..., description="Task complexity: low, medium, high")
    confidence_threshold: float = Field(
        ..., description="Confidence threshold for escalation"
    )
    escalation: List[str] = Field(default_factory=list, description="Escalation models")


class Controls(BaseModel):
    """Control parameters for the response."""

    stream: bool = Field(False, description="Enable streaming")
    parallel_tool_calls: bool = Field(False, description="Allow parallel tool calls")
    background: bool = Field(False, description="Run in background mode")
    include: List[str] = Field(default_factory=list, description="Items to include")
    reasoning: Dict[str, str] = Field(
        default_factory=dict, description="Reasoning configuration"
    )
    cache_keys: Dict[str, str] = Field(
        default_factory=dict, description="Cache keys for prompt caching"
    )


class SafetyConfig(BaseModel):
    """Safety and guardrail configuration."""

    guardrails: List[str] = Field(default_factory=list, description="Active guardrails")
    red_flags: List[str] = Field(default_factory=list, description="Red flag patterns")


class PromptPack(BaseModel):
    """Complete prompt configuration for a single Responses API call."""

    # Core fields
    model: str = Field(..., description="Model to use")
    messages: List[Dict[str, Any]] = Field(..., description="Message history")
    tools: List[Dict[str, Any]] = Field(
        default_factory=list, description="Available tools"
    )
    response_format: Dict[str, Any] = Field(
        ..., description="Response format configuration"
    )
    routing: RoutingConfig = Field(..., description="Routing configuration")
    controls: Controls = Field(..., description="Control parameters")

    # Context and safety
    context_bundles: List[ContextBundle] = Field(
        default_factory=list, description="Context bundles"
    )
    safety: SafetyConfig = Field(
        default_factory=SafetyConfig, description="Safety configuration"
    )

    # Metadata
    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique identifier"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    estimated_tokens: int = Field(0, description="Estimated total tokens")

    @validator("messages")
    def validate_messages(cls, v):
        """Validate message structure."""
        for msg in v:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Messages must have 'role' and 'content' fields")
            if msg["role"] not in ["system", "user", "assistant", "tool"]:
                raise ValueError(f"Invalid role: {msg['role']}")
        return v

    @validator("tools")
    def validate_tools(cls, v):
        """Validate tool structure."""
        for tool in v:
            if "type" not in tool:
                raise ValueError("Tools must have 'type' field")
            if tool["type"] == "function":
                if "function" not in tool:
                    raise ValueError("Function tools must have 'function' field")
                func = tool["function"]
                if (
                    "name" not in func
                    or "strict" not in func
                    or "parameters" not in func
                ):
                    raise ValueError(
                        "Function must have 'name', 'strict', and 'parameters' fields"
                    )
        return v

    @validator("response_format")
    def validate_response_format(cls, v):
        """Validate response format structure."""
        if "type" not in v:
            raise ValueError("Response format must have 'type' field")
        if v["type"] == "json_schema":
            if "json_schema" not in v:
                raise ValueError(
                    "JSON schema response format must have 'json_schema' field"
                )
            schema = v["json_schema"]
            if "name" not in schema or "strict" not in schema or "schema" not in schema:
                raise ValueError(
                    "JSON schema must have 'name', 'strict', and 'schema' fields"
                )
        return v

    def compute_cache_keys(self) -> Dict[str, str]:
        """Compute cache keys for prompt caching."""
        # System message hash
        system_messages = [msg for msg in self.messages if msg["role"] == "system"]
        system_content = json.dumps(system_messages, sort_keys=True)
        system_hash = hashlib.sha256(system_content.encode()).hexdigest()[:16]

        # Tools hash
        tools_content = json.dumps(self.tools, sort_keys=True)
        tools_hash = hashlib.sha256(tools_content.encode()).hexdigest()[:16]

        # Context bundles hash
        context_content = json.dumps(
            [bundle.dict() for bundle in self.context_bundles], sort_keys=True
        )
        context_hash = hashlib.sha256(context_content.encode()).hexdigest()[:16]

        return {
            "system_hash": system_hash,
            "tools_hash": tools_hash,
            "context_hash": context_hash,
        }

    def to_openai_params(self) -> Dict[str, Any]:
        """Convert to OpenAI Responses API parameters."""
        params = {
            "model": self.model,
            "input": self.messages[-1]["content"] if self.messages else "",
            "instructions": (
                self.messages[0]["content"]
                if self.messages and self.messages[0]["role"] == "system"
                else None
            ),
        }

        # Add tools if present
        if self.tools:
            params["tools"] = self.tools

        # Add text format for structured outputs
        if self.response_format:
            params["text_format"] = self.response_format

        # Add controls
        if self.controls.background:
            params["background"] = True
        if self.controls.include:
            params["include"] = self.controls.include
        if self.controls.reasoning:
            params["reasoning"] = self.controls.reasoning

        return params


class PromptProfile(BaseModel):
    """Profile for prompt optimization and continuous improvement."""

    role: str = Field(..., description="Agent role")
    task_type: str = Field(..., description="Task type")
    wins: int = Field(0, description="Successful runs")
    fails: int = Field(0, description="Failed runs")
    avg_tokens: float = Field(0.0, description="Average token usage")
    avg_latency: float = Field(0.0, description="Average latency in seconds")
    last_success_model: Optional[str] = Field(None, description="Last successful model")
    last_schema_version: Optional[str] = Field(None, description="Last schema version")
    guardrails: List[str] = Field(default_factory=list, description="Active guardrails")
    confidence_threshold: float = Field(0.9, description="Confidence threshold")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.wins + self.fails
        return self.wins / total if total > 0 else 0.0

    def update_from_result(
        self, success: bool, tokens: int, latency: float, model: str
    ):
        """Update profile from run result."""
        if success:
            self.wins += 1
            self.last_success_model = model
        else:
            self.fails += 1

        # Update averages
        total_runs = self.wins + self.fails
        self.avg_tokens = (self.avg_tokens * (total_runs - 1) + tokens) / total_runs
        self.avg_latency = (self.avg_latency * (total_runs - 1) + latency) / total_runs
        self.updated_at = datetime.utcnow()
