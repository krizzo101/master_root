# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Example Validator Module","description":"This module provides a validator for checking examples in rules, ensuring that rules have examples that demonstrate the rule's application.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and classes for the validator.","line_start":3,"line_end":11},{"name":"ExampleValidator Class","description":"Defines the ExampleValidator class which validates rules for proper examples.","line_start":12,"line_end":127},{"name":"validate_example_quality Function","description":"Validates the quality of a generated example.","line_start":129,"line_end":175}],"key_elements":[{"name":"ExampleValidator","description":"Class responsible for validating examples in rules.","line":14},{"name":"__init__","description":"Constructor for ExampleValidator class.","line":22},{"name":"validate","description":"Method to validate a rule's examples.","line":43},{"name":"validate_example_quality","description":"Function to validate the quality of a generated example.","line":129},{"name":"logger","description":"Logger instance for logging validation processes.","line":9}]}
"""
# FILE_MAP_END

"""
Example Validator Module.

This module provides a validator for checking examples in rules.
"""

import logging
from typing import Dict, Any, List, Optional

from .rule_validator import RuleValidator

logger = logging.getLogger(__name__)


class ExampleValidator(RuleValidator):
    """
    Validate rules for proper examples.

    This validator checks that rules have examples that demonstrate
    the rule's application.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the example validator.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

        # Configuration
        self.min_examples = 1

        # Override from config if provided
        if config and "validation" in config:
            validation_config = config.get("validation", {})
            example_config = validation_config.get("example", {})
            if "min_examples" in example_config:
                self.min_examples = example_config.get("min_examples")

        logger.info(
            f"Initialized example validator with min_examples: {self.min_examples}"
        )

    def validate(
        self, rule_content: str, rule_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a rule's examples.

        Args:
            rule_content: Content of the rule to validate
            rule_path: Optional path to the rule file

        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating rule examples: {rule_path or 'unnamed'}")

        issues = []

        # Extract sections
        sections = self._extract_sections(rule_content)

        # Check for examples section
        has_examples_section = False
        for section_name in sections:
            if "example" in section_name.lower():
                has_examples_section = True
                break

        if not has_examples_section:
            issues.append("Missing examples section")

            # Early return if no examples section
            return {
                "status": "fail",
                "pass": False,
                "issues": issues,
                "examples_count": 0,
                "min_examples": self.min_examples,
            }

        # Count examples
        examples_count = 0
        code_blocks = 0

        # Examine examples section(s)
        for section_name in sections:
            if "example" in section_name.lower():
                section_content = sections[section_name]

                # Count code blocks
                import re

                code_blocks += len(
                    re.findall(r"```[\w\s]*\n[\s\S]*?```", section_content)
                )

                # Count bullet points
                bullet_points = len(
                    re.findall(r"^\s*[-*]\s+", section_content, re.MULTILINE)
                )

                # Count numbered lists
                numbered_lists = len(
                    re.findall(r"^\s*\d+\.\s+", section_content, re.MULTILINE)
                )

                # Update examples count
                examples_count += max(code_blocks, bullet_points, numbered_lists)

        # Check if there are enough examples
        if examples_count < self.min_examples:
            issues.append(
                f"Insufficient examples: found {examples_count}, need at least {self.min_examples}"
            )

        # Check if examples section is too short
        for section_name in sections:
            if "example" in section_name.lower():
                section_content = sections[section_name]
                if len(section_content.strip()) < 50:
                    issues.append("Examples section is too short")
                    break

        # Determine overall status
        status = "pass" if not issues else "fail"

        result = {
            "status": status,
            "pass": status == "pass",
            "issues": issues,
            "examples_count": examples_count,
            "min_examples": self.min_examples,
        }

        logger.info(f"Example validation complete. Status: {result['status']}")
        return result


def validate_example_quality(
    example: Dict[str, Any], rule_id: str, rule_name: str, category: str
) -> Dict[str, Any]:
    """
    Validate the quality of a generated example.

    Args:
        example: The generated example
        rule_id: ID of the rule
        rule_name: Name of the rule
        category: Category of the rule

    Returns:
        Dictionary with validation results
    """
    results = {"is_valid": True, "feedback": ""}

    # Check code length
    code = example.get("code", "")
    if len(code.split("\n")) < 10:
        results["is_valid"] = False
        results[
            "feedback"
        ] += "Code example is too short. It should demonstrate a complete implementation. "

    # Check explanation length
    explanation = example.get("explanation", "")
    if len(explanation) < 200:
        results["is_valid"] = False
        results[
            "feedback"
        ] += "Explanation is too brief. It should thoroughly explain the example implementation. "

    # Check for error handling in code
    if (
        "try" not in code
        and "except" not in code
        and "error" not in code.lower()
        and "exception" not in code.lower()
    ):
        results[
            "feedback"
        ] += "Warning: Code lacks error handling, which is generally important for robust implementations. "

    # Check for comments in code
    if "#" not in code and "'''" not in code and '"""' not in code:
        results[
            "feedback"
        ] += "Warning: Code lacks comments, which are important for understanding the implementation. "

    # Check for code formatting
    if "```" not in code:
        results[
            "feedback"
        ] += "Warning: Code should be formatted with code blocks (```). "

    # Check title
    title = example.get("title", "")
    if not title or len(title) < 5:
        results[
            "feedback"
        ] += "Warning: Title is missing or too short. It should clearly describe the example. "

    return results
