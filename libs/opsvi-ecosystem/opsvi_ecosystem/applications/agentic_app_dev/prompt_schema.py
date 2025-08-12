from dataclasses import dataclass, field
import json
from typing import Dict, List, Optional

import yaml


@dataclass
class ReferencedFile:
    path: str
    role: (
        str  # e.g., 'requirements', 'design', 'code', 'config', 'doc', 'example', etc.
    )
    description: Optional[str] = None


@dataclass
class AgentPromptSchema:
    title: str
    description: str
    objectives: List[str]
    requirements: List[str]
    constraints: List[str] = field(default_factory=list)
    context_files: List[str] = field(default_factory=list)
    referenced_files: List[ReferencedFile] = field(default_factory=list)
    standards: List[str] = field(default_factory=list)
    onboarding: Optional[str] = None
    artifact_types: List[str] = field(default_factory=list)
    output_preferences: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, str] = field(default_factory=dict)  # extensibility
    manifest_schema: Optional[str] = None
    config_schema: Optional[str] = None

    @staticmethod
    def from_yaml(yaml_str: str) -> "AgentPromptSchema":
        data = yaml.safe_load(yaml_str)
        data["referenced_files"] = [
            ReferencedFile(**f) for f in data.get("referenced_files", [])
        ]
        return AgentPromptSchema(**data)

    @staticmethod
    def from_json(json_str: str) -> "AgentPromptSchema":
        data = json.loads(json_str)
        data["referenced_files"] = [
            ReferencedFile(**f) for f in data.get("referenced_files", [])
        ]
        return AgentPromptSchema(**data)

    def validate(self) -> List[str]:
        errors = []
        if not self.title:
            errors.append("Missing title")
        if not self.description:
            errors.append("Missing description")
        if not self.objectives:
            errors.append("Missing objectives")
        if not self.requirements:
            errors.append("Missing requirements")
        return errors


# Example YAML schema (for documentation)
EXAMPLE_PROMPT_YAML = """
# --- AGENT PROMPT SCHEMA v1 ---
title: Workflow Runner Implementation
description: |
  Implement a CLI-based agentic workflow runner for the agent_world project, supporting Prefect-based workflows, multi-workflow orchestration, and best practices.
objectives:
  - Generate and execute Prefect workflows
  - Support multi-instance, dependency-aware parallel orchestration
  - Ensure robust config, logging, error handling
requirements:
  - Must support both workflow generation and execution modes
  - Use centralized YAML config
  - Log all actions and errors
constraints:
  - Use only open-source Python libraries
  - Must be compatible with Linux and macOS
context_files:
  - docs/standards/workflow_runner_requirements.md
  - docs/standards/workflow_runner_design.md
referenced_files:
  - path: src/applications/workflow_runner/config.py
    role: code
    description: Workflow runner configuration module
  - path: src/applications/workflow_runner/workflow_runner.py
    role: code
    description: Main workflow runner logic
standards:
  - .archive/rules/800-development-best-practices.md
  - .archive/rules/803-python-dev-standards.md
onboarding: |
  Review all referenced standards and onboarding docs before contributing.
artifact_types:
  - code
  - config
  - doc
  - diagram
output_preferences:
  format: markdown
  language: python
extra:
  reviewer: "agentic-reviewer@agent_world"
"""
