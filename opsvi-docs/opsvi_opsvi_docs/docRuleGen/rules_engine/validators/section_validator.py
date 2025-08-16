# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Section Validator","description":"This module contains utilities for validating rule sections.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for functionality.","line_start":3,"line_end":11},{"name":"SectionValidator Class","description":"Class that provides methods for validating different sections of a rule against requirements and standards.","line_start":12,"line_end":182},{"name":"Validation Functions","description":"Standalone functions for validating sections and post-processing danger sections.","line_start":183,"line_end":340}],"key_elements":[{"name":"SectionValidator","description":"Validator for rule sections.","line":14},{"name":"__init__","description":"Initializes the section validator.","line":22},{"name":"validate","description":"Validates a rule against section requirements.","line":32},{"name":"validate_section","description":"Validates a specific section of a rule against requirements.","line":70},{"name":"post_process_danger","description":"Post-processes the danger section content.","line":86},{"name":"_extract_frontmatter","description":"Extracts frontmatter from rule content.","line":99},{"name":"_extract_sections","description":"Extracts sections from rule content.","line":135},{"name":"validate_section","description":"Standalone function to validate a specific section of a rule.","line":283},{"name":"post_process_danger_section","description":"Fixes common issues with the danger section.","line":295}]}
"""
# FILE_MAP_END

"""
Section Validator

This module contains utilities for validating rule sections.
"""

from typing import Dict, Any, Tuple, Optional, List
import logging
import re
import yaml

logger = logging.getLogger(__name__)


class SectionValidator:
    """
    Validator for rule sections.

    This class provides methods for validating different sections of a rule
    against requirements and standards.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the section validator.

        Args:
            config: Optional configuration dictionary (not used by this validator)
        """
        # This validator doesn't need configuration
        logger.info("Initialized section validator")

    def validate(
        self, rule_content: str, rule_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a rule against section requirements.

        Args:
            rule_content: Content of the rule to validate
            rule_path: Optional path to the rule file

        Returns:
            Dictionary with validation results
        """
        # Extract frontmatter and rule ID/name
        frontmatter, _ = self._extract_frontmatter(rule_content)
        rule_id = str(frontmatter.get("id", "000"))
        rule_name = frontmatter.get("name", "Unnamed Rule")

        # Extract sections
        sections = self._extract_sections(rule_content)

        # Validate each section
        issues = []
        for section_name, section_content in sections.items():
            is_valid, feedback = self.validate_section(
                rule_id, rule_name, section_name, {"content": section_content}
            )
            if not is_valid:
                issues.append(f"Section '{section_name}' validation failed: {feedback}")

        # Return validation result
        return {
            "pass": len(issues) == 0,
            "issues": issues,
            "details": {
                "sections_validated": list(sections.keys()),
                "rule_id": rule_id,
                "rule_name": rule_name,
            },
        }

    @staticmethod
    def validate_section(
        rule_id: str, rule_name: str, section: str, content: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate a specific section of a rule against requirements.

        Args:
            rule_id: The ID of the rule
            rule_name: The name of the rule
            section: The section name ('frontmatter', 'metadata', etc.)
            content: The content of the section

        Returns:
            Tuple of (is_valid, feedback)
        """
        return validate_section(rule_id, rule_name, section, content)

    @staticmethod
    def post_process_danger(
        danger_content: Dict[str, Any], rule_name: str
    ) -> Dict[str, Any]:
        """
        Post-process the danger section content.

        Args:
            danger_content: The content of the danger section
            rule_name: The name of the rule

        Returns:
            Processed danger content
        """
        return post_process_danger_section(danger_content, rule_name)

    def _extract_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract frontmatter from rule content.

        Args:
            content: Rule content

        Returns:
            Tuple of (frontmatter dictionary, body content)
        """
        frontmatter_pattern = r"^---\s*$(.*?)^---\s*$"
        match = re.search(frontmatter_pattern, content, re.MULTILINE | re.DOTALL)

        if not match:
            return {}, content

        frontmatter_content = match.group(1).strip()
        body = content[match.end() :].strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_content)
            if frontmatter is None:
                frontmatter = {}
        except Exception as e:
            logger.error(f"Error parsing frontmatter: {str(e)}")
            # Try a simpler approach - extract key-value pairs manually
            frontmatter = {}
            lines = frontmatter_content.split("\n")
            for line in lines:
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()

        return frontmatter, body

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """
        Extract sections from rule content.

        Args:
            content: Rule content

        Returns:
            Dictionary mapping section names to content
        """
        # Extract frontmatter
        _, body = self._extract_frontmatter(content)

        # Extract sections
        sections = {}

        # Find all level 2 headers (##)
        section_pattern = r"^##\s+(.*?)$"
        section_matches = re.finditer(section_pattern, body, re.MULTILINE)

        # Get positions of all section headings
        positions = [(m.group(1).strip(), m.start()) for m in section_matches]

        # If no sections found, treat entire body as a single section
        if not positions:
            sections["content"] = body.strip()
            return sections

        # Extract content for each section
        for i, (section_name, start_pos) in enumerate(positions):
            # Get content until next section or end of body
            if i < len(positions) - 1:
                end_pos = positions[i + 1][1]
                section_content = body[start_pos:end_pos].strip()
            else:
                section_content = body[start_pos:].strip()

            # Remove the section heading
            section_content = re.sub(
                r"^##\s+.*?$", "", section_content, 1, re.MULTILINE
            ).strip()

            sections[section_name] = section_content

        return sections


def validate_section(
    rule_id: str, rule_name: str, section: str, content: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Validate a specific section of a rule against requirements.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule
        section: The section name ('frontmatter', 'metadata', etc.)
        content: The content of the section

    Returns:
        Tuple of (is_valid, feedback)
    """
    validation_results = {"is_valid": True, "feedback": ""}

    # Validation for frontmatter
    if section == "frontmatter":
        # Check description format (MUST-WHEN-TO)
        if "description" not in content:
            validation_results["is_valid"] = False
            validation_results["feedback"] += "Missing 'description' field. "
        else:
            desc = content["description"]
            if (
                not desc.startswith("MUST ")
                or " WHEN " not in desc
                or " TO " not in desc
            ):
                validation_results["is_valid"] = False
                validation_results[
                    "feedback"
                ] += "Description doesn't follow MUST-WHEN-TO format. "
            if len(desc) > 100:
                validation_results["feedback"] += "Description exceeds 100 characters. "

        # Check globs
        if (
            "globs" not in content
            or not isinstance(content["globs"], list)
            or len(content["globs"]) == 0
        ):
            validation_results["is_valid"] = False
            validation_results[
                "feedback"
            ] += "Missing or invalid 'globs' field. Must be a non-empty array. "

    # Validation for metadata
    elif section == "metadata":
        # Check required fields
        required_fields = ["rule_id", "taxonomy"]
        for field in required_fields:
            if field not in content:
                validation_results["is_valid"] = False
                validation_results["feedback"] += f"Missing '{field}' in metadata. "

        # Check taxonomy structure
        if "taxonomy" in content:
            taxonomy = content["taxonomy"]
            if not isinstance(taxonomy, dict):
                validation_results["is_valid"] = False
                validation_results["feedback"] += "Taxonomy must be a dictionary. "
            else:
                taxonomy_fields = ["category", "parent", "ancestors"]
                for field in taxonomy_fields:
                    if field not in taxonomy:
                        validation_results["is_valid"] = False
                        validation_results[
                            "feedback"
                        ] += f"Missing '{field}' in taxonomy. "

    # Validation for overview
    elif section == "overview":
        # Check required fields
        required_fields = ["purpose", "application", "importance"]
        for field in required_fields:
            if field not in content:
                validation_results["is_valid"] = False
                validation_results["feedback"] += f"Missing '{field}' in overview. "

    # Validation for examples
    elif section == "examples":
        # Check if there's a code block
        if (
            "code" not in content
            or not isinstance(content["code"], str)
            or "```" not in content["code"]
        ):
            validation_results["is_valid"] = False
            validation_results[
                "feedback"
            ] += "Missing or invalid code block in examples. "

        # Check if there's an explanation
        if (
            "explanation" not in content
            or not isinstance(content["explanation"], str)
            or len(content["explanation"]) < 50
        ):
            validation_results["is_valid"] = False
            validation_results[
                "feedback"
            ] += "Missing or insufficient explanation in examples. "

    # Validation for danger
    elif section == "danger":
        # Check critical violations
        if (
            "critical_violations" not in content
            or not isinstance(content["critical_violations"], list)
            or len(content["critical_violations"]) == 0
        ):
            validation_results["is_valid"] = False
            validation_results[
                "feedback"
            ] += "Missing or invalid 'critical_violations'. Must be a non-empty array. "
        else:
            # Check if all critical violations start with NEVER
            for violation in content["critical_violations"]:
                if not violation.startswith("NEVER"):
                    validation_results["is_valid"] = False
                    validation_results[
                        "feedback"
                    ] += "Critical violations must start with 'NEVER'. "
                    break

        # Check specific risks
        if (
            "specific_risks" not in content
            or not isinstance(content["specific_risks"], list)
            or len(content["specific_risks"]) == 0
        ):
            validation_results["is_valid"] = False
            validation_results[
                "feedback"
            ] += "Missing or invalid 'specific_risks'. Must be a non-empty array. "

    # Return validation results
    return validation_results["is_valid"], validation_results["feedback"]


def post_process_danger_section(
    danger_content: Dict[str, Any], rule_name: str
) -> Dict[str, Any]:
    """
    Fix common issues with the danger section.

    Args:
        danger_content: The original danger section content
        rule_name: The name of the rule

    Returns:
        The fixed danger section content
    """
    # Deep copy the content to avoid modifying the original
    import copy

    fixed_content = copy.deepcopy(danger_content)

    # Fix nested danger object
    if "danger" in fixed_content:
        nested_danger = fixed_content.pop("danger")
        # Merge the nested content with the top level
        if isinstance(nested_danger, dict):
            for key, value in nested_danger.items():
                if key not in fixed_content:
                    fixed_content[key] = value

    # Ensure critical violations start with NEVER
    if "critical_violations" in fixed_content and isinstance(
        fixed_content["critical_violations"], list
    ):
        violations = fixed_content["critical_violations"]
        for i, violation in enumerate(violations):
            if not violation.startswith("NEVER"):
                violations[i] = f"NEVER {violation}"

    # Remove generic placeholder violations
    if "critical_violations" in fixed_content and isinstance(
        fixed_content["critical_violations"], list
    ):
        specific_rule_name = rule_name.lower()
        fixed_content["critical_violations"] = [
            v
            for v in fixed_content["critical_violations"]
            if not v.endswith("principles") and not "rules" in v.lower()
        ]

        # If we removed too many, add at least one specific one
        if not fixed_content["critical_violations"]:
            fixed_content["critical_violations"] = [
                f"NEVER violate key {specific_rule_name} requirements as it can lead to system failures",
                f"NEVER implement {specific_rule_name} without proper error handling",
                f"NEVER ignore security considerations in {specific_rule_name} implementations",
            ]

    # Ensure specific risks exist
    if (
        "specific_risks" not in fixed_content
        or not isinstance(fixed_content["specific_risks"], list)
        or not fixed_content["specific_risks"]
    ):
        specific_rule_name = rule_name.lower()
        fixed_content["specific_risks"] = [
            f"Improper {specific_rule_name} implementation may cause system failures",
            f"Ignoring {specific_rule_name} best practices can lead to maintenance challenges",
            f"Security vulnerabilities may arise from incorrect {specific_rule_name} implementations",
        ]

    return fixed_content
