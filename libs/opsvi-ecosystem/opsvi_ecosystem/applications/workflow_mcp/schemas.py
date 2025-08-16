from typing import Any

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    """Schema for creating a new workflow."""

    name: str
    type: str
    spec: Any
    template: Any | None = None
    profile: Any | None = None
    metadata: dict[str, Any] | None = None
    version: str | None = None
    status: str | None = Field(default="active")


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""

    name: str | None = None
    type: str | None = None
    spec: Any | None = None
    template: Any | None = None
    profile: Any | None = None
    metadata: dict[str, Any] | None = None
    version: str | None = None
    status: str | None = None


class WorkflowResponse(BaseModel):
    """Schema for returning a workflow document."""

    _key: str
    name: str
    type: str
    spec: Any
    template: Any | None = None
    profile: Any | None = None
    metadata: dict[str, Any] | None = None
    created_at: str
    updated_at: str
    version: str | None = None
    status: str | None = None


class WorkflowRunCreate(BaseModel):
    """Schema for creating a new workflow run."""

    workflow_id: str
    input: Any | None = None
    agent_info: dict[str, Any] | None = None
    status: str | None = Field(default="pending")


class WorkflowRunUpdate(BaseModel):
    """Schema for updating a workflow run."""

    input: Any | None = None
    result: Any | None = None
    logs: list[Any] | None = None
    status: str | None = None
    agent_info: dict[str, Any] | None = None
    finished_at: str | None = None


class WorkflowRunResponse(BaseModel):
    """Schema for returning a workflow run document."""

    _key: str
    workflow_id: str
    input: Any | None = None
    result: Any | None = None
    logs: list[Any] | None = None
    started_at: str
    finished_at: str | None = None
    status: str
    agent_info: dict[str, Any] | None = None
