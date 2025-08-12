# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Validation Manager Module","description":"This module provides functionality for coordinating rule validation using different validation strategies.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"This section imports necessary modules and classes for validation management.","line_start":3,"line_end":18},{"name":"ValidationManager Class","description":"This section defines the ValidationManager class which coordinates rule validation.","line_start":20,"line_end":196}],"key_elements":[{"name":"ValidationManager","description":"Class that manages the selection and application of appropriate validators based on rule type and validation requirements.","line":22},{"name":"__init__","description":"Constructor for the ValidationManager class that initializes the validation manager.","line":30},{"name":"validate","description":"Method to validate a rule using specified strategies.","line":57},{"name":"improve_rule","description":"Method to improve a rule based on validation results.","line":138},{"name":"register_validator","description":"Method to register a custom validator.","line":185},{"name":"get_validator","description":"Method to retrieve a validator by name.","line":196},{"name":"logger","description":"Logger instance for logging validation processes.","line":19}]}
"""
# FILE_MAP_END

"""
Validation Manager Module.

This module provides functionality for coordinating rule validation
using different validation strategies.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .rule_validator import RuleValidator
from .section_validator import SectionValidator
from .example_validator import ExampleValidator
from .deep_validator import DeepValidator
from .practical_validator import PracticalValidator
from .llm_validator import LLMValidator

logger = logging.getLogger(__name__)


class ValidationManager:
    """
    Coordinate rule validation using multiple validation strategies.

    This class manages the selection and application of appropriate validators
    based on rule type and validation requirements.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the validation manager.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Initialize validators
        self.validators = {
            "section": SectionValidator(),
            "example": ExampleValidator(),
            "deep": DeepValidator(),
            "practical": PracticalValidator(),
            "llm": LLMValidator(config) if config else LLMValidator(),
        }

        # Set up validation strategies
        validation_config = self.config.get("validation", {})
        self.default_strategy = validation_config.get(
            "default_strategy", ["section", "example"]
        )
        self.use_llm = validation_config.get("use_llm", False)

        logger.info(
            f"Initialized validation manager with strategies: {self.default_strategy}"
        )
        if self.use_llm:
            logger.info("LLM validation is enabled")

    def validate(
        self,
        rule_content: str,
        rule_path: Optional[str] = None,
        strategies: Optional[List[str]] = None,
        use_llm: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Validate a rule using specified strategies.

        Args:
            rule_content: Content of the rule to validate
            rule_path: Optional path to the rule file
            strategies: List of validation strategies to use
            use_llm: Whether to use LLM validation

        Returns:
            Dictionary with validation results
        """
        if not rule_content:
            logger.error("Cannot validate empty rule content")
            return {"status": "error", "message": "Empty rule content", "pass": False}

        # Use provided strategies or default
        strategies = strategies or self.default_strategy

        # Determine whether to use LLM
        use_llm_validation = self.use_llm if use_llm is None else use_llm

        logger.info(f"Validating rule: {rule_path or 'unnamed'}")
        logger.info(f"Using validation strategies: {strategies}")

        # Collect results from each validator
        results = {}
        issues = []
        all_passed = True

        for strategy in strategies:
            if strategy not in self.validators:
                logger.warning(f"Unknown validation strategy: {strategy}")
                continue

            validator = self.validators[strategy]
            result = validator.validate(rule_content, rule_path)

            # Add result to collection
            results[strategy] = result

            # Track pass/fail status
            if not result.get("pass", False):
                all_passed = False

            # Collect issues
            if "issues" in result and isinstance(result["issues"], list):
                issues.extend(result["issues"])

        # Add LLM validation if requested
        if use_llm_validation and "llm" in self.validators:
            logger.info("Performing LLM validation")
            llm_result = self.validators["llm"].validate(rule_content, rule_path)
            results["llm"] = llm_result

            # Track LLM validation status
            if not llm_result.get("pass", False):
                all_passed = False

            # Collect LLM issues
            if "issues" in llm_result and isinstance(llm_result["issues"], list):
                issues.extend(llm_result["issues"])

        # Compile final result
        final_result = {
            "status": "pass" if all_passed else "fail",
            "pass": all_passed,
            "results": results,
            "issues": issues,
        }

        logger.info(f"Validation complete. Status: {final_result['status']}")
        return final_result

    def improve_rule(
        self,
        rule_content: str,
        validation_result: Dict[str, Any],
        use_llm: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Improve a rule based on validation results.

        Args:
            rule_content: Original rule content
            validation_result: Validation result dictionary
            use_llm: Whether to use LLM for improvement

        Returns:
            Dictionary with improved rule content
        """
        if validation_result.get("status") == "pass" and not validation_result.get(
            "issues"
        ):
            logger.info("Rule passed validation, no improvement needed")
            return {"content": rule_content, "status": "unchanged"}

        # Determine whether to use LLM
        use_llm_improvement = self.use_llm if use_llm is None else use_llm

        if use_llm_improvement and "llm" in self.validators:
            logger.info("Improving rule using LLM")

            # Get LLM validation result if available
            llm_validation = validation_result.get("results", {}).get("llm")

            # If no LLM validation result is available, perform LLM validation first
            if not llm_validation and "llm" in self.validators:
                llm_validation = self.validators["llm"].validate(rule_content)

            # Use LLM validator to improve rule
            improvement_result = self.validators["llm"].improve_rule(
                rule_content, llm_validation or validation_result
            )

            if "content" in improvement_result:
                logger.info("Successfully improved rule using LLM")
                return improvement_result

        # If LLM improvement failed or wasn't requested, return original content
        logger.info("No improvement method available or improvement failed")
        return {"content": rule_content, "status": "unchanged"}

    def register_validator(self, name: str, validator: RuleValidator):
        """
        Register a custom validator.

        Args:
            name: Name of the validator
            validator: Validator instance
        """
        self.validators[name] = validator
        logger.info(f"Registered custom validator: {name}")

    def get_validator(self, name: str) -> Optional[RuleValidator]:
        """
        Get a validator by name.

        Args:
            name: Name of the validator

        Returns:
            Validator instance or None if not found
        """
        return self.validators.get(name)
