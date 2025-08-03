#!/usr/bin/env python3
"""
Intelligent Model Selection Engine for o3_agent Tool

This module provides intelligent model selection based on task characteristics,
time constraints, quality requirements, and complexity levels. It uses a
comprehensive decision matrix derived from extensive SDLC testing results.

Author: AI Assistant
Date: 2025-07-30
Version: 1.0.0
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """Represents the context for model selection decision making."""

    task_type: str = "general_development"
    time_constraint: str = "normal"
    quality_requirement: str = "detailed"
    complexity_level: str = "moderate"
    prompt_text: str = ""
    user_override: str | None = None


@dataclass
class ModelDecision:
    """Represents the final model selection decision."""

    selected_model: str
    confidence_score: float
    reasoning: str
    alternatives: list[str]
    task_analysis: dict[str, Any]


class ModelSelectionEngine:
    """
    Intelligent model selection engine based on comprehensive SDLC testing results.

    This engine analyzes task context and selects the optimal model based on:
    - Task type (requirements, architecture, implementation, etc.)
    - Time constraints (urgent, normal, thorough)
    - Quality requirements (overview, detailed, comprehensive)
    - Complexity levels (simple, moderate, complex)
    """

    def __init__(self, config_path: str = "model_selection_config.json"):
        """Initialize the model selection engine with configuration."""
        # If config_path is relative, make it relative to this module's directory
        if not Path(config_path).is_absolute():
            module_dir = Path(__file__).parent
            self.config_path = module_dir / config_path
        else:
            self.config_path = Path(config_path)
        self.config = self._load_config()
        self.valid_models = ["gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1", "o4-mini", "o3"]

    def _load_config(self) -> dict[str, Any]:
        """Load the model selection configuration from JSON file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Loaded model selection config: {config['version']}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise

    def analyze_prompt(self, prompt_text: str) -> dict[str, Any]:
        """
        Analyze the prompt text to determine task characteristics.

        Args:
            prompt_text: The user's prompt text

        Returns:
            Dictionary containing task analysis results
        """
        prompt_lower = prompt_text.lower()
        analysis = {
            "task_type": "general_development",
            "time_constraint": "normal",
            "quality_requirement": "detailed",
            "complexity_level": "moderate",
            "confidence": 0.0,
            "keywords_found": [],
        }

        # Task type detection
        task_keywords = {
            "requirements_gathering": [
                "user story",
                "user stories",
                "acceptance criteria",
                "requirements",
                "functional requirements",
                "non-functional requirements",
                "user needs",
                "stakeholder",
                "business requirements",
                "use case",
            ],
            "system_architecture": [
                "architecture",
                "architectural",
                "system design",
                "microservices",
                "service design",
                "component design",
                "system structure",
                "event-driven",
                "distributed system",
                "scalable architecture",
            ],
            "code_implementation": [
                "design pattern",
                "implementation",
                "code structure",
                "coding",
                "programming",
                "development",
                "build",
                "create",
                "implement",
                "code example",
                "snippet",
                "algorithm",
            ],
            "testing_strategy": [
                "testing",
                "test strategy",
                "test plan",
                "quality assurance",
                "test coverage",
                "unit test",
                "integration test",
                "performance test",
                "security test",
                "automated testing",
            ],
            "devops_deployment": [
                "ci/cd",
                "pipeline",
                "deployment",
                "devops",
                "infrastructure",
                "kubernetes",
                "docker",
                "container",
                "automation",
                "deploy",
                "production",
                "staging",
                "environment",
            ],
            "database_design": [
                "database",
                "data model",
                "schema",
                "entity",
                "relationship",
                "table design",
                "indexing",
                "query optimization",
                "data modeling",
                "database architecture",
                "orm",
                "migration",
            ],
            "security_analysis": [
                "security",
                "authentication",
                "authorization",
                "encryption",
                "vulnerability",
                "threat",
                "compliance",
                "hipaa",
                "gdpr",
                "pci",
                "security architecture",
                "penetration test",
            ],
            "performance_optimization": [
                "performance",
                "optimization",
                "scaling",
                "load balancing",
                "caching",
                "throughput",
                "latency",
                "response time",
                "efficiency",
                "performance tuning",
                "bottleneck",
            ],
            "code_review": [
                "code review",
                "quality",
                "standards",
                "best practices",
                "code quality",
                "review process",
                "quality framework",
                "coding standards",
                "linting",
                "static analysis",
            ],
            "technical_documentation": [
                "documentation",
                "api documentation",
                "technical writing",
                "openapi",
                "swagger",
                "api spec",
                "documentation standards",
                "technical docs",
                "user guide",
                "developer guide",
            ],
        }

        # Find matching task types
        task_matches = {}
        for task_type, keywords in task_keywords.items():
            matches = [kw for kw in keywords if kw in prompt_lower]
            if matches:
                task_matches[task_type] = len(matches)
                analysis["keywords_found"].extend(matches)

        # Select task type with most matches
        if task_matches:
            analysis["task_type"] = max(task_matches, key=task_matches.get)
            analysis["confidence"] += 0.3

        # Time constraint detection
        time_keywords = {
            "urgent": ["urgent", "quick", "fast", "asap", "immediately", "rush"],
            "thorough": [
                "thorough",
                "comprehensive",
                "detailed",
                "complete",
                "extensive",
                "in-depth",
            ],
        }

        for constraint, keywords in time_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                analysis["time_constraint"] = constraint
                analysis["confidence"] += 0.2
                break

        # Quality requirement detection
        quality_keywords = {
            "overview": [
                "overview",
                "summary",
                "high-level",
                "brief",
                "quick overview",
            ],
            "comprehensive": [
                "comprehensive",
                "detailed",
                "thorough",
                "complete",
                "extensive",
            ],
        }

        for quality, keywords in quality_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                analysis["quality_requirement"] = quality
                analysis["confidence"] += 0.2
                break

        # Complexity level detection
        complexity_keywords = {
            "simple": ["simple", "basic", "straightforward", "easy", "standard"],
            "complex": [
                "complex",
                "advanced",
                "sophisticated",
                "challenging",
                "difficult",
                "architectural",
            ],
        }

        for complexity, keywords in complexity_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                analysis["complexity_level"] = complexity
                analysis["confidence"] += 0.2
                break

        # Adjust confidence based on prompt length and specificity
        if len(prompt_text) > 500:
            analysis["confidence"] += 0.1

        analysis["confidence"] = min(analysis["confidence"], 1.0)

        return analysis

    def select_model(self, context: TaskContext) -> ModelDecision:
        """
        Select the optimal model based on task context.

        Args:
            context: TaskContext object containing decision parameters

        Returns:
            ModelDecision object with selected model and reasoning
        """
        # Handle user override
        if context.user_override:
            if context.user_override in self.valid_models:
                return ModelDecision(
                    selected_model=context.user_override,
                    confidence_score=1.0,
                    reasoning=f"User override: {context.user_override}",
                    alternatives=self.valid_models,
                    task_analysis={"override": True},
                )
            else:
                logger.warning(f"Invalid user override model: {context.user_override}")

        # Get decision matrix
        decision_matrix = self.config["decision_matrix"]

        # Validate inputs
        if context.task_type not in decision_matrix:
            logger.warning(
                f"Unknown task type: {context.task_type}, using general_development"
            )
            context.task_type = "general_development"

        task_matrix = decision_matrix[context.task_type]

        if context.time_constraint not in task_matrix:
            logger.warning(
                f"Unknown time constraint: {context.time_constraint}, using normal"
            )
            context.time_constraint = "normal"

        time_matrix = task_matrix[context.time_constraint]

        if context.quality_requirement not in time_matrix:
            logger.warning(
                f"Unknown quality requirement: {context.quality_requirement}, using detailed"
            )
            context.quality_requirement = "detailed"

        # Get primary model selection
        selected_model = time_matrix[context.quality_requirement]

        # Apply complexity override
        fallback_rules = self.config["fallback_rules"]
        if (
            context.complexity_level == "complex"
            and "complexity_override" in fallback_rules
        ):
            selected_model = fallback_rules["complexity_override"]["complex"]

        # Generate alternatives based on model characteristics
        alternatives = self._get_alternatives(context)

        # Calculate confidence score
        confidence = self._calculate_confidence(context)

        # Generate reasoning
        reasoning = self._generate_reasoning(context, selected_model)

        return ModelDecision(
            selected_model=selected_model,
            confidence_score=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            task_analysis={
                "task_type": context.task_type,
                "time_constraint": context.time_constraint,
                "quality_requirement": context.quality_requirement,
                "complexity_level": context.complexity_level,
            },
        )

    def _get_alternatives(self, context: TaskContext) -> list[str]:
        """Get alternative models based on context."""
        alternatives = []

        # Add models based on time constraint priority
        time_priorities = self.config["decision_rules"]["time_constraints"][
            context.time_constraint
        ]["model_priority"]
        alternatives.extend(time_priorities[:3])  # Top 3 alternatives

        # Add models based on quality requirement priority
        quality_priorities = self.config["decision_rules"]["quality_requirements"][
            context.quality_requirement
        ]["model_priority"]
        for model in quality_priorities[:2]:
            if model not in alternatives:
                alternatives.append(model)

        return alternatives[:5]  # Limit to 5 alternatives

    def _calculate_confidence(self, context: TaskContext) -> float:
        """Calculate confidence score for the model selection."""
        confidence = 0.5  # Base confidence

        # Task type confidence
        task_rules = self.config["decision_rules"]["task_types"]
        if context.task_type in task_rules:
            confidence += 0.2

        # Time constraint confidence
        time_rules = self.config["decision_rules"]["time_constraints"]
        if context.time_constraint in time_rules:
            confidence += 0.1

        # Quality requirement confidence
        quality_rules = self.config["decision_rules"]["quality_requirements"]
        if context.quality_requirement in quality_rules:
            confidence += 0.1

        # Complexity level confidence
        complexity_rules = self.config["decision_rules"]["complexity_levels"]
        if context.complexity_level in complexity_rules:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_reasoning(self, context: TaskContext, selected_model: str) -> str:
        """Generate human-readable reasoning for the model selection."""
        model_info = self.config["model_characteristics"][selected_model]

        reasoning_parts = [
            f"Selected {selected_model} for {context.task_type.replace('_', ' ')} task"
        ]

        # Add reasoning based on characteristics
        if model_info["speed"] == "fastest":
            reasoning_parts.append("(fastest execution)")
        elif model_info["speed"] == "fast":
            reasoning_parts.append("(fast execution)")

        if context.time_constraint == "urgent":
            reasoning_parts.append("due to urgent time constraint")
        elif context.time_constraint == "thorough":
            reasoning_parts.append("for thorough analysis")

        if context.quality_requirement == "comprehensive":
            reasoning_parts.append("with comprehensive coverage")
        elif context.quality_requirement == "overview":
            reasoning_parts.append("for overview-level response")

        if context.complexity_level == "complex":
            reasoning_parts.append("handling complex requirements")

        return " ".join(reasoning_parts)

    def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a specific model."""
        if model_name in self.config["model_characteristics"]:
            return self.config["model_characteristics"][model_name]
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def list_available_models(self) -> list[str]:
        """List all available models."""
        return list(self.config["model_characteristics"].keys())

    def get_task_types(self) -> list[str]:
        """List all available task types."""
        return list(self.config["decision_rules"]["task_types"].keys())


def create_task_context(
    prompt_text: str,
    task_type: str | None = None,
    time_constraint: str | None = None,
    quality_requirement: str | None = None,
    complexity_level: str | None = None,
    user_override: str | None = None,
) -> TaskContext:
    """
    Create a TaskContext object with automatic prompt analysis.

    Args:
        prompt_text: The user's prompt text
        task_type: Optional explicit task type
        time_constraint: Optional explicit time constraint
        quality_requirement: Optional explicit quality requirement
        complexity_level: Optional explicit complexity level
        user_override: Optional user-specified model override

    Returns:
        TaskContext object with all parameters set
    """
    engine = ModelSelectionEngine()

    # Analyze prompt if not all parameters are provided
    if not all([task_type, time_constraint, quality_requirement, complexity_level]):
        analysis = engine.analyze_prompt(prompt_text)
        task_type = task_type or analysis["task_type"]
        time_constraint = time_constraint or analysis["time_constraint"]
        quality_requirement = quality_requirement or analysis["quality_requirement"]
        complexity_level = complexity_level or analysis["complexity_level"]

    return TaskContext(
        task_type=task_type,
        time_constraint=time_constraint,
        quality_requirement=quality_requirement,
        complexity_level=complexity_level,
        prompt_text=prompt_text,
        user_override=user_override,
    )


def select_optimal_model(
    prompt_text: str,
    task_type: str | None = None,
    time_constraint: str | None = None,
    quality_requirement: str | None = None,
    complexity_level: str | None = None,
    user_override: str | None = None,
    config_path: str = "model_selection_config.json",
) -> ModelDecision:
    """
    Convenience function to select the optimal model for a given prompt.

    Args:
        prompt_text: The user's prompt text
        task_type: Optional explicit task type
        time_constraint: Optional explicit time constraint
        quality_requirement: Optional explicit quality requirement
        complexity_level: Optional explicit complexity level
        user_override: Optional user-specified model override
        config_path: Path to configuration file

    Returns:
        ModelDecision object with selected model and reasoning
    """
    engine = ModelSelectionEngine(config_path)
    context = create_task_context(
        prompt_text=prompt_text,
        task_type=task_type,
        time_constraint=time_constraint,
        quality_requirement=quality_requirement,
        complexity_level=complexity_level,
        user_override=user_override,
    )

    return engine.select_model(context)


if __name__ == "__main__":
    # Example usage
    engine = ModelSelectionEngine()

    # Test prompt analysis
    test_prompt = "Create a comprehensive testing strategy for a financial transaction processing system"
    analysis = engine.analyze_prompt(test_prompt)
    print(f"Prompt Analysis: {analysis}")

    # Test model selection
    context = create_task_context(test_prompt)
    decision = engine.select_model(context)
    print(f"Model Decision: {decision}")
