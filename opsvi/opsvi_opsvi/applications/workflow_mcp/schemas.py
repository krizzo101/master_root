from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    """Schema for creating a new workflow."""

    name: str
    type: str
    spec: Any
    template: Optional[Any] = None
    profile: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    status: Optional[str] = Field(default="active")


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""

    name: Optional[str] = None
    type: Optional[str] = None
    spec: Optional[Any] = None
    template: Optional[Any] = None
    profile: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    status: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Schema for returning a workflow document."""

    _key: str
    name: str
    type: str
    spec: Any
    template: Optional[Any] = None
    profile: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
    version: Optional[str] = None
    status: Optional[str] = None


class WorkflowRunCreate(BaseModel):
    """Schema for creating a new workflow run."""

    workflow_id: str
    input: Optional[Any] = None
    agent_info: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(default="pending")


class WorkflowRunUpdate(BaseModel):
    """Schema for updating a workflow run."""

    input: Optional[Any] = None
    result: Optional[Any] = None
    logs: Optional[List[Any]] = None
    status: Optional[str] = None
    agent_info: Optional[Dict[str, Any]] = None
    finished_at: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    """Schema for returning a workflow run document."""

    _key: str
    workflow_id: str
    input: Optional[Any] = None
    result: Optional[Any] = None
    logs: Optional[List[Any]] = None
    started_at: str
    finished_at: Optional[str] = None
    status: str
    agent_info: Optional[Dict[str, Any]] = None
