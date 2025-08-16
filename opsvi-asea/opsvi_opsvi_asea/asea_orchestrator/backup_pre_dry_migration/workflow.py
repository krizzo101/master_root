from __future__ import annotations
from typing import Dict, Any, List, Literal, Optional, TypedDict
from dataclasses import dataclass, field
from datetime import datetime


class RetryConfig(TypedDict):
    count: int
    delay: float


@dataclass
class WorkflowState:
    """Represents the state of a single workflow execution."""

    run_id: str
    workflow_name: str
    status: Literal["RUNNING", "COMPLETED", "FAILED"]
    current_step: int
    state: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_db_document(self) -> Dict[str, Any]:
        """Serializes the state to a dictionary for ArangoDB."""
        doc = self.__dict__.copy()
        doc["_key"] = self.run_id
        doc["created_at"] = self.created_at.isoformat()
        doc["updated_at"] = self.updated_at.isoformat()
        return doc

    @staticmethod
    def from_db_document(doc: Dict[str, Any]) -> WorkflowState:
        """Creates a WorkflowState instance from a database document."""
        state_instance = WorkflowState(
            run_id=doc["_key"],
            workflow_name=doc["workflow_name"],
            status=doc["status"],
            current_step=doc["current_step"],
            state=doc["state"],
        )
        state_instance.created_at = datetime.fromisoformat(doc["created_at"])
        state_instance.updated_at = datetime.fromisoformat(doc["updated_at"])
        return state_instance


@dataclass
class WorkflowStep:
    """Defines a single step in a workflow."""

    id: str
    plugin_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    step_type: Literal["single", "parallel"] = "single"
    parallel_steps: Optional[List[WorkflowStep]] = field(default_factory=list)
    retry: Optional[RetryConfig] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.plugin_name = kwargs.get("plugin_name") or kwargs.get("plugin", "")
        self.parameters = kwargs.get("parameters", {})

        # Consolidate 'method' and 'data' from JSON into 'parameters'
        if "method" in kwargs:
            self.parameters["method"] = kwargs["method"]
        if "data" in kwargs:
            self.parameters["data"] = kwargs["data"]

        self.inputs = kwargs.get("inputs", {})
        self.outputs = kwargs.get("outputs", {})
        self.step_type = kwargs.get("step_type", "single")
        self.parallel_steps = kwargs.get("parallel_steps", [])
        self.retry = kwargs.get("retry")
        self.on_success = kwargs.get("on_success")
        self.on_failure = kwargs.get("on_failure")

        # Recursively hydrate parallel_steps if they are provided as dicts
        if self.parallel_steps and isinstance(self.parallel_steps[0], dict):
            self.parallel_steps = [WorkflowStep(**s) for s in self.parallel_steps]


@dataclass
class Workflow:
    """Represents a named sequence of workflow steps."""

    name: str
    steps: List[WorkflowStep] = field(default_factory=list)

    def __post_init__(self):
        # Hydrate the top-level steps if they are provided as dicts
        if self.steps and isinstance(self.steps[0], dict):
            self.steps = [WorkflowStep(**s) for s in self.steps]


class WorkflowManager:
    """
    Manages loading and accessing workflow definitions.
    """

    def __init__(self, workflow_definitions: Dict[str, Dict]):
        self.workflows: Dict[str, Workflow] = {}
        for name, data in workflow_definitions.items():
            # Accommodate both 'steps' and 'tasks' as keys for the step list
            step_list_data = data.get("steps") or data.get("tasks", [])
            steps = [WorkflowStep(**step_data) for step_data in step_list_data]
            self.workflows[name] = Workflow(name=name, steps=steps)
        print("WorkflowManager loaded with the following workflows:")
        for name in self.workflows:
            print(f"- {name}")

    def get_workflow(self, name: str) -> Workflow:
        """
        Retrieves a workflow by name.
        """
        if name not in self.workflows:
            raise ValueError(f"Workflow '{name}' not found.")
        return self.workflows[name]
