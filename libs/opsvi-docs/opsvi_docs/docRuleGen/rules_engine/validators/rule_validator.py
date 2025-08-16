# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Rule Validator","description":"This module provides functions for validating the structure and format of rule files, including frontmatter, directive formats, and required sections.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation for the rule validator module, outlining its purpose and functionality.","line_start":3,"line_end":8},{"name":"Imports","description":"Import statements for required libraries and modules.","line_start":9,"line_end":12},{"name":"Logging Setup","description":"Setup for logging within the module.","line_start":13,"line_end":13},{"name":"Function: verify_rule_quality","description":"Verifies the structural quality of a rule file.","line_start":15,"line_end":75},{"name":"Function: extract_frontmatter","description":"Extracts frontmatter from rule content.","line_start":76,"line_end":144},{"name":"Function: validate_frontmatter","description":"Validates frontmatter content for required fields and formats.","line_start":145,"line_end":180},{"name":"Function: validate_directive_format","description":"Validates the format of WHEN/TO/MUST directives in rule content.","line_start":181,"line_end":208},{"name":"Function: validate_required_sections","description":"Validates the presence of required sections in rule content.","line_start":209,"line_end":240},{"name":"Class: RuleValidator","description":"Base class for all rule validators, defining the interface and common functionality.","line_start":241,"line_end":445}],"key_elements":[{"name":"verify_rule_quality","description":"Function to verify the structural quality of a rule file.","line":16},{"name":"extract_frontmatter","description":"Function to extract frontmatter from rule content.","line":76},{"name":"validate_frontmatter","description":"Function to validate frontmatter content.","line":145},{"name":"validate_directive_format","description":"Function to validate directive formats in rule content.","line":181},{"name":"validate_required_sections","description":"Function to validate required sections in rule content.","line":209},{"name":"__init__","description":"Constructor for the RuleValidator class.","line":249},{"name":"validate","description":"Method to validate a rule according to specific criteria.","line":258},{"name":"can_improve","description":"Method to determine if a rule can be improved based on validation results.","line":271},{"name":"improve_rule","description":"Method to improve a rule based on validation feedback.","line":283},{"name":"_extract_sections","description":"Method to extract sections from rule content.","line":299},{"name":"_extract_frontmatter","description":"Method to extract frontmatter from rule content.","line":341},{"name":"_has_directive_pattern","description":"Method to check for directive patterns in rule content.","line":379},{"name":"_extract_directive","description":"Method to extract directive components from rule content.","line":394},{"name":"_has_required_sections","description":"Method to check if required sections are present in rule content.","line":419},{"name":"RuleValidator","description":"Class representing the rule validator.","line":241}]}
"""
# FILE_MAP_END

"""
Rule validator module for structural validation of rules.

This module provides functions for validating the structure and format of rule files,
including frontmatter, directive formats, and required sections.
"""

import os
import re
import yaml
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


def verify_rule_quality(rule_path: str) -> Dict[str, Any]:
    """
    Verify the structural quality of a rule file.

    Args:
        rule_path: Path to the rule file

    Returns:
        Dictionary with validation results
    """
    logger.info(f"Verifying structural quality of rule: {rule_path}")

    issues = []

    # Check if file exists
    if not os.path.exists(rule_path):
        return {
            "status": "error",
            "message": f"Rule file does not exist: {rule_path}",
            "issues": [f"Rule file does not exist: {rule_path}"],
            "passed": False,
        }

    # Read file content
    try:
        with open(rule_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading rule file: {str(e)}",
            "issues": [f"Error reading rule file: {str(e)}"],
            "passed": False,
        }

    # Extract frontmatter
    frontmatter, body = extract_frontmatter(content)

    # Validate frontmatter
    frontmatter_issues = validate_frontmatter(frontmatter)
    issues.extend(frontmatter_issues)

    # Validate directive format
    directive_issues = validate_directive_format(body)
    issues.extend(directive_issues)

    # Validate required sections
    section_issues = validate_required_sections(body)
    issues.extend(section_issues)

    # Determine overall result
    result = {
        "status": "success" if not issues else "warning",
        "issues": issues,
        "frontmatter": frontmatter,
        "passed": len(issues) == 0,
    }

    return result


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract frontmatter from rule content.

    Args:
        content: Rule content

    Returns:
        Tuple of (frontmatter dictionary, body content)
    """
    # First check if the content starts with "Here's an improved version"
    # which indicates it's an LLM-generated rule
    if content.startswith("Here's an improved version") or content.startswith(
        "Here is an improved version"
    ):
        # Find the first actual frontmatter
        frontmatter_start = content.find("---")
        if frontmatter_start != -1:
            # Find the end of frontmatter
            frontmatter_end = content.find("---", frontmatter_start + 3)
            if frontmatter_end != -1:
                # Extract the frontmatter content
                frontmatter_content = content[
                    frontmatter_start + 3 : frontmatter_end
                ].strip()
                # Extract the body (everything after the end of frontmatter)
                body = content[frontmatter_end + 3 :].strip()

                # Parse the frontmatter
                try:
                    # Try standard YAML parsing
                    frontmatter = yaml.safe_load(frontmatter_content)
                    if frontmatter is None:
                        frontmatter = {}
                    return frontmatter, body
                except Exception:
                    # If YAML parsing fails, try parsing manually
                    frontmatter = {}
                    lines = frontmatter_content.split("\n")
                    for line in lines:
                        line = line.strip()
                        if ":" in line:
                            key, value = line.split(":", 1)
                            frontmatter[key.strip()] = value.strip()
                    return frontmatter, body

    # Standard YAML frontmatter parsing
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


def validate_frontmatter(frontmatter: Dict[str, Any]) -> List[str]:
    """
    Validate frontmatter content.

    Args:
        frontmatter: Frontmatter dictionary

    Returns:
        List of validation issues
    """
    issues = []

    # Check for required fields
    required_fields = ["id", "name", "type"]
    for field in required_fields:
        if field not in frontmatter:
            issues.append(f"Missing required frontmatter field: {field}")

    # Validate type field if present
    if "type" in frontmatter:
        valid_types = ["parent", "child", "standalone"]
        if frontmatter["type"] not in valid_types:
            issues.append(
                f"Invalid rule type: {frontmatter['type']}. Must be one of: {', '.join(valid_types)}"
            )

    # Check for parent field if type is child
    if frontmatter.get("type") == "child" and "parent" not in frontmatter:
        issues.append("Child rule must have a parent field in frontmatter")

    # Validate id format
    if "id" in frontmatter:
        id_str = str(frontmatter["id"])
        if not re.match(r"^\d+(\.\d+)*$", id_str):
            issues.append(
                f"Invalid id format: {id_str}. Must be a numeric identifier (e.g., 301 or 301.01)"
            )

    return issues


def validate_directive_format(content: str) -> List[str]:
    """
    Validate WHEN/TO/MUST directive format.

    Args:
        content: Rule content

    Returns:
        List of validation issues
    """
    issues = []

    # Check for WHEN/TO/MUST format anywhere in the content
    directive_pattern = r"WHEN\s+.*?\s+TO\s+.*?\s+(MUST|SHOULD)\s+.*?"
    directive_found = re.search(directive_pattern, content, re.IGNORECASE)

    if not directive_found:
        # Check also in the frontmatter description
        frontmatter_match = re.search(r"description:\s*(.*?)$", content, re.MULTILINE)
        if frontmatter_match:
            description = frontmatter_match.group(1).strip()
            directive_found = re.search(directive_pattern, description, re.IGNORECASE)

    if not directive_found:
        issues.append("Missing WHEN/TO/MUST directive in rule content")

    return issues


def validate_required_sections(content: str) -> List[str]:
    """
    Validate required sections in rule content.

    Args:
        content: Rule content

    Returns:
        List of validation issues
    """
    issues = []

    # Check for required sections
    required_sections = ["Overview"]
    recommended_sections = ["Context", "Requirements", "Examples"]

    # Extract section headers
    section_pattern = r"^##\s+(.*?)$"
    sections = re.findall(section_pattern, content, re.MULTILINE)

    # Check required sections
    for section in required_sections:
        if not any(s.strip() == section for s in sections):
            issues.append(f"Missing required section: {section}")

    # Recommend optional sections
    for section in recommended_sections:
        if not any(s.strip() == section for s in sections):
            issues.append(f"Recommended section missing: {section}")

    return issues


class RuleValidator:
    """
    Base class for all rule validators.

    This class defines the interface for rule validators and provides
    common functionality for validation and improvement.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the rule validator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def validate(
        self, rule_content: str, rule_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a rule according to specific criteria.

        Args:
            rule_content: Content of the rule to validate
            rule_path: Optional path to the rule file

        Returns:
            Dictionary with validation results
        """
        raise NotImplementedError("Validator subclasses must implement validate()")

    def can_improve(self, validation_result: Dict[str, Any]) -> bool:
        """
        Determine if the rule can be improved based on validation results.

        Args:
            validation_result: Validation result dictionary

        Returns:
            True if the rule can be improved, False otherwise
        """
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
        # Default implementation returns original content unchanged
        return {"content": rule_content, "status": "unchanged"}

    def _extract_sections(self, rule_content: str) -> Dict[str, str]:
        """
        Extract sections from rule content.

        Args:
            rule_content: Rule content

        Returns:
            Dictionary with section names and content
        """
        import re

        sections = {}
        current_section = "header"
        current_content = []

        lines = rule_content.split("\n")

        for line in lines:
            # Check if line is a section header
            section_match = re.match(r"^#{1,3}\s+(.+)$", line)

            if section_match:
                # Save current section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []

                # Start new section
                section_name = section_match.group(1).strip().lower()
                # Convert to snake_case for consistent section names
                section_name = re.sub(r"[^\w\s]", "", section_name).replace(" ", "_")
                current_section = section_name
            else:
                current_content.append(line)

        # Save final section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _extract_frontmatter(self, rule_content: str) -> Dict[str, Any]:
        """
        Extract frontmatter from rule content.

        Args:
            rule_content: Rule content

        Returns:
            Dictionary with frontmatter fields
        """
        import re
        import yaml

        frontmatter = {}

        # Check for YAML frontmatter
        frontmatter_match = re.search(
            r"^---\s*$(.+?)^---\s*$", rule_content, re.MULTILINE | re.DOTALL
        )

        if frontmatter_match:
            try:
                # Parse YAML frontmatter
                frontmatter_text = frontmatter_match.group(1).strip()
                frontmatter = yaml.safe_load(frontmatter_text)
                if not isinstance(frontmatter, dict):
                    frontmatter = {}
            except Exception as e:
                logger.warning(f"Error parsing frontmatter YAML: {str(e)}")

                # Try simple key-value parsing as fallback
                frontmatter_text = frontmatter_match.group(1).strip()
                for line in frontmatter_text.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        frontmatter[key.strip()] = value.strip()

        return frontmatter

    def _has_directive_pattern(self, rule_content: str) -> bool:
        """
        Check if rule content contains a WHEN-TO-MUST directive pattern.

        Args:
            rule_content: Rule content

        Returns:
            True if directive pattern is found, False otherwise
        """
        import re

        directive_pattern = r"WHEN\s+.*?\s+TO\s+.*?\s+(MUST|SHOULD)\s+.*?"
        return bool(
            re.search(directive_pattern, rule_content, re.IGNORECASE | re.DOTALL)
        )

    def _extract_directive(self, rule_content: str) -> Dict[str, str]:
        """
        Extract WHEN-TO-MUST directive components from rule content.

        Args:
            rule_content: Rule content

        Returns:
            Dictionary with directive components (when, to, strength, directive)
        """
        import re

        directive_pattern = r"WHEN\s+(.*?)\s+TO\s+(.*?)\s+(MUST|SHOULD)\s+(.*?)(?=$|\n)"
        match = re.search(directive_pattern, rule_content, re.IGNORECASE | re.DOTALL)

        if match:
            return {
                "when": match.group(1).strip(),
                "to": match.group(2).strip(),
                "strength": match.group(3).upper(),
                "directive": match.group(4).strip(),
            }

        return {}

    def _has_required_sections(
        self, sections: Dict[str, str], required_sections: List[str]
    ) -> bool:
        """
        Check if rule content contains required sections.

        Args:
            sections: Dictionary with section names and content
            required_sections: List of required section names

        Returns:
            True if all required sections are present, False otherwise
        """
        for section in required_sections:
            section_found = False
            # Check for exact match
            if section in sections:
                section_found = True
            else:
                # Check for alternative names
                for key in sections.keys():
                    if section.replace("_", " ") in key.replace("_", " "):
                        section_found = True
                        break

            if not section_found:
                return False

        return True
