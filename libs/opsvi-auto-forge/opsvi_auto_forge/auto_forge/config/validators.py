"""Configuration validators for DSL and pipeline settings."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ValidationError

from .models import Project, Run, TaskRecord
from opsvi_auto_forge.application.orchestrator.dsl_processor import DSLProcessor

logger = logging.getLogger(__name__)


class DSLValidator:
    """Validator for DSL configuration."""

    def __init__(self, config_path: str = "config/pipeline.schema.yml"):
        """Initialize DSL validator."""
        self.config_path = config_path
        self.dsl_processor = DSLProcessor(config_path)

    def validate_reasoning_config(self) -> List[str]:
        """Validate reasoning configuration."""
        issues = []

        if not self.dsl_processor:
            issues.append("DSL processor not initialized")
            return issues

        reasoning = self.dsl_processor.get_reasoning_config()

        # Validate strategy
        valid_strategies = [
            "auto",
            "single",
            "self_consistency",
            "solver_verifier",
            "tot",
            "debate",
            "reflexion",
        ]
        if reasoning.strategy not in valid_strategies:
            issues.append(f"Invalid reasoning strategy: {reasoning.strategy}")

        # Validate k_samples
        if reasoning.k_samples < 1 or reasoning.k_samples > 20:
            issues.append(
                f"k_samples must be between 1 and 20, got {reasoning.k_samples}"
            )

        # Validate max_thoughts
        if reasoning.max_thoughts < 1 or reasoning.max_thoughts > 100:
            issues.append(
                f"max_thoughts must be between 1 and 100, got {reasoning.max_thoughts}"
            )

        # Validate k_samples <= max_thoughts
        if reasoning.k_samples > reasoning.max_thoughts:
            issues.append(
                f"k_samples ({reasoning.k_samples}) cannot be greater than max_thoughts ({reasoning.max_thoughts})"
            )

        # Validate min_confidence
        if reasoning.min_confidence < 0.0 or reasoning.min_confidence > 1.0:
            issues.append(
                f"min_confidence must be between 0.0 and 1.0, got {reasoning.min_confidence}"
            )

        return issues

    def validate_knowledge_config(self) -> List[str]:
        """Validate knowledge configuration."""
        issues = []

        if not self.dsl_processor:
            issues.append("DSL processor not initialized")
            return issues

        knowledge = self.dsl_processor.get_knowledge_config()

        # Validate retrievers
        if not knowledge.retrievers:
            issues.append("At least one retriever must be configured")
        else:
            for i, retriever in enumerate(knowledge.retrievers):
                if not retriever.name:
                    issues.append(f"Retriever {i} must have a name")

                if retriever.top_k < 1 or retriever.top_k > 50:
                    issues.append(
                        f"Retriever {i} top_k must be between 1 and 50, got {retriever.top_k}"
                    )

                if retriever.bm25_k and (retriever.bm25_k < 1 or retriever.bm25_k > 50):
                    issues.append(
                        f"Retriever {i} bm25_k must be between 1 and 50, got {retriever.bm25_k}"
                    )

        # Validate freshness_days
        if knowledge.freshness_days < 1 or knowledge.freshness_days > 365:
            issues.append(
                f"freshness_days must be between 1 and 365, got {knowledge.freshness_days}"
            )

        # Validate max_ctx_chars
        if knowledge.max_ctx_chars < 1000 or knowledge.max_ctx_chars > 500000:
            issues.append(
                f"max_ctx_chars must be between 1000 and 500000, got {knowledge.max_ctx_chars}"
            )

        return issues

    def validate_quality_gates_config(self) -> List[str]:
        """Validate quality gates configuration."""
        issues = []

        if not self.dsl_processor:
            issues.append("DSL processor not initialized")
            return issues

        gates = self.dsl_processor.get_quality_gates_config()

        # Validate overall_threshold
        if gates.overall_threshold < 0.0 or gates.overall_threshold > 1.0:
            issues.append(
                f"overall_threshold must be between 0.0 and 1.0, got {gates.overall_threshold}"
            )

        # Validate policy_threshold
        if gates.policy_threshold < 0.0 or gates.policy_threshold > 1.0:
            issues.append(
                f"policy_threshold must be between 0.0 and 1.0, got {gates.policy_threshold}"
            )

        # Validate overall_threshold >= policy_threshold
        if gates.overall_threshold < gates.policy_threshold:
            issues.append(
                f"overall_threshold ({gates.overall_threshold}) should be >= policy_threshold ({gates.policy_threshold})"
            )

        return issues

    def validate_auto_repair_config(self) -> List[str]:
        """Validate auto-repair configuration."""
        issues = []

        if not self.dsl_processor:
            issues.append("DSL processor not initialized")
            return issues

        repair = self.dsl_processor.get_auto_repair_config()

        # Validate max_repair_attempts
        if repair.max_repair_attempts < 0 or repair.max_repair_attempts > 10:
            issues.append(
                f"max_repair_attempts must be between 0 and 10, got {repair.max_repair_attempts}"
            )

        return issues

    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all configuration sections."""
        return {
            "reasoning": self.validate_reasoning_config(),
            "knowledge": self.validate_knowledge_config(),
            "quality_gates": self.validate_quality_gates_config(),
            "auto_repair": self.validate_auto_repair_config(),
        }

    def is_valid(self) -> bool:
        """Check if all configurations are valid."""
        all_issues = self.validate_all()
        return all(not issues for issues in all_issues.values())

    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        all_issues = self.validate_all()
        total_issues = sum(len(issues) for issues in all_issues.values())

        return {
            "valid": self.is_valid(),
            "total_issues": total_issues,
            "sections": {
                section: {
                    "valid": len(issues) == 0,
                    "issue_count": len(issues),
                    "issues": issues,
                }
                for section, issues in all_issues.items()
            },
        }


class PipelineValidator(BaseModel):
    """Validator for pipeline configuration."""

    def validate_pipeline_name(self, name: str) -> List[str]:
        """Validate pipeline name."""
        issues = []

        if not name:
            issues.append("Pipeline name cannot be empty")
        elif len(name) > 100:
            issues.append("Pipeline name too long (max 100 characters)")
        elif not name.replace("-", "").replace("_", "").isalnum():
            issues.append(
                "Pipeline name must be alphanumeric with hyphens/underscores only"
            )

        return issues

    def validate_pipeline_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate pipeline configuration."""
        issues = []

        # Validate required fields
        required_fields = ["name", "nodes"]
        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")

        # Validate nodes
        if "nodes" in config:
            nodes = config["nodes"]
            if not isinstance(nodes, list):
                issues.append("Nodes must be a list")
            elif len(nodes) == 0:
                issues.append("Pipeline must have at least one node")
            else:
                for i, node in enumerate(nodes):
                    node_issues = self.validate_node(node, i)
                    issues.extend(node_issues)

        return issues

    def validate_node(self, node: Dict[str, Any], index: int) -> List[str]:
        """Validate a pipeline node."""
        issues = []

        # Validate required node fields
        required_fields = ["id", "type", "agent"]
        for field in required_fields:
            if field not in node:
                issues.append(f"Node {index} missing required field: {field}")

        # Validate node ID
        if "id" in node:
            node_id = node["id"]
            if not isinstance(node_id, str) or len(node_id) == 0:
                issues.append(f"Node {index} ID must be a non-empty string")

        # Validate node type
        if "type" in node:
            node_type = node["type"]
            valid_types = ["task", "gate", "decision", "loop"]
            if node_type not in valid_types:
                issues.append(
                    f"Node {index} type must be one of {valid_types}, got {node_type}"
                )

        # Validate agent
        if "agent" in node:
            agent = node["agent"]
            if not isinstance(agent, str) or len(agent) == 0:
                issues.append(f"Node {index} agent must be a non-empty string")

        return issues


class ConfigValidator:
    """Main configuration validator."""

    def __init__(self):
        """Initialize validator."""
        self.dsl_validator = DSLValidator()
        self.pipeline_validator = PipelineValidator()

    def validate_dsl_config(self) -> Dict[str, Any]:
        """Validate DSL configuration."""
        return self.dsl_validator.get_summary()

    def validate_pipeline_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate pipeline configuration."""
        return self.pipeline_validator.validate_pipeline_config(config)

    def validate_pipeline_name(self, name: str) -> List[str]:
        """Validate pipeline name."""
        return self.pipeline_validator.validate_pipeline_name(name)

    def get_validation_report(self) -> Dict[str, Any]:
        """Get comprehensive validation report."""
        dsl_summary = self.validate_dsl_config()

        return {
            "dsl_config": dsl_summary,
            "overall_valid": dsl_summary["valid"],
            "timestamp": "2025-01-28T00:00:00Z",
        }
