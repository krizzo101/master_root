# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"LLM Validator Module","description":"This module provides validators that use Large Language Models (LLMs) to validate generated rules against quality and correctness criteria.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"This section imports necessary modules and classes for the LLM Validator.","line_start":3,"line_end":14},{"name":"LLMValidator Class","description":"This section defines the LLMValidator class which contains methods for validating and improving rules using LLMs.","line_start":16,"line_end":145}],"key_elements":[{"name":"LLMValidator","description":"The main class that implements validation logic using LLMs.","line":18},{"name":"__init__","description":"Constructor for the LLMValidator class, initializes configuration and orchestrator.","line":26},{"name":"validate","description":"Method to validate a rule using LLM.","line":43},{"name":"can_improve","description":"Method to determine if a rule can be improved based on validation results.","line":97},{"name":"improve_rule","description":"Method to improve a rule based on validation feedback.","line":119}]}
"""
# FILE_MAP_END

"""
LLM Validator Module.

This module provides validators that use Large Language Models (LLMs)
to validate generated rules against quality and correctness criteria.
"""

import logging
from typing import Dict, Any, Optional

from ..connectors.llm_orchestrator import LLMOrchestrator
from .rule_validator import RuleValidator

logger = logging.getLogger(__name__)


class LLMValidator(RuleValidator):
    """
    Validate rules using Large Language Models.

    This validator uses LLMs to assess rule quality, correctness,
    adherence to standards, and overall effectiveness.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM validator.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.config = config or {}
        self.orchestrator = LLMOrchestrator(config)

        # Set up validation thresholds from config
        validation_config = self.config.get("validation", {})
        self.min_score = validation_config.get("min_score", 7.0)

        logger.info("Initialized LLM validator")

    def validate(
        self, rule_content: str, rule_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a rule using LLM.

        Args:
            rule_content: Content of the rule to validate
            rule_path: Optional path to the rule file

        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating rule using LLM: {rule_path or 'unnamed'}")

        # Use the orchestrator to validate the rule
        validation_result = self.orchestrator.validate_rule(rule_content, rule_path)

        # Ensure we have a valid result
        if not validation_result or not isinstance(validation_result, dict):
            logger.error("Failed to get valid validation result from LLM")
            return {
                "status": "error",
                "message": "Failed to get valid validation result from LLM",
                "score": 0,
                "issues": ["LLM validation failed"],
                "pass": False,
            }

        # Extract validation data
        score = float(validation_result.get("score", 0))
        feedback = validation_result.get("feedback", "")
        strengths = validation_result.get("strengths", [])
        weaknesses = validation_result.get("weaknesses", [])
        recommendations = validation_result.get("recommendations", [])

        # Determine overall status
        status = validation_result.get("status", "")
        if not status:
            status = "pass" if score >= self.min_score else "fail"

        # Format result to match the RuleValidator interface
        result = {
            "status": status,
            "score": score,
            "feedback": feedback,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "pass": status == "pass",
            "issues": weaknesses,
        }

        logger.info(f"Rule validation complete with score: {score}")
        return result

    def can_improve(self, validation_result: Dict[str, Any]) -> bool:
        """
        Determine if the rule can be improved based on validation results.

        Args:
            validation_result: Validation result dictionary

        Returns:
            True if the rule can be improved, False otherwise
        """
        if not validation_result or not isinstance(validation_result, dict):
            return False

        # Check if there are significant weaknesses that can be addressed
        if validation_result.get("status") == "fail":
            return True

        if (
            validation_result.get("weaknesses")
            and len(validation_result.get("weaknesses", [])) > 0
        ):
            return True

        return False

    def improve_rule(
        self, rule_content: str, validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Improve a rule based on validation feedback.

        Args:
            rule_content: Original rule content
            validation_result: Validation result dictionary

        Returns:
            Dictionary with improved rule content
        """
        if not self.can_improve(validation_result):
            logger.info("Rule does not require improvement")
            return {"content": rule_content, "status": "unchanged"}

        logger.info("Improving rule based on validation feedback")

        # Use the orchestrator to improve the rule
        improved_result = self.orchestrator.improve_rule(
            rule_content, validation_result
        )

        if not improved_result or "content" not in improved_result:
            logger.error("Failed to improve rule using LLM")
            return {"content": rule_content, "status": "error"}

        logger.info("Successfully improved rule using LLM")
        return improved_result
