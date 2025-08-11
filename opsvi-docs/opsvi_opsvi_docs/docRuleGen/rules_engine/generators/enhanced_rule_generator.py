# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Enhanced Rule Generator","description":"This module contains utilities for generating and verifying high-quality rule files. It extends the basic rule generator with validation, verification, and automatic fixing.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary libraries and modules for the functionality of the rule generator.","line_start":3,"line_end":24},{"name":"Constants","description":"Defines constants used throughout the module, including paths for rules and guidance files.","line_start":26,"line_end":30},{"name":"ValidationError Class","description":"Defines a custom exception for validation errors in rule content.","line_start":32,"line_end":43},{"name":"Function Definitions","description":"Contains all function definitions for generating, validating, and fixing rules.","line_start":45,"line_end":1098}],"key_elements":[{"name":"ValidationError","description":"Custom exception raised when rule content fails validation.","line":43},{"name":"__init__","description":"Constructor for the ValidationError class.","line":52},{"name":"generate_and_validate_section","description":"Generates a section and validates it with retries if needed.","line":59},{"name":"create_placeholder_section","description":"Creates a placeholder section as a fallback when generation fails.","line":118},{"name":"create_rule_file","description":"Creates a complete rule file by generating all sections with validation.","line":190},{"name":"_format_rule_content","description":"Formats the rule content into the correct .mdc format.","line":333},{"name":"verify_rule_quality","description":"Performs thorough verification of a generated rule.","line":388},{"name":"read_file_content","description":"Reads a file and returns its content.","line":549},{"name":"fix_rule_section","description":"Fixes a specific section in a rule file.","line":567},{"name":"create_and_verify_rule","description":"Creates a rule file and verifies its quality, with automatic fixing of issues.","line":679},{"name":"create_rule_with_feedback","description":"Creates an improved rule based on validation feedback.","line":735},{"name":"format_list_for_prompt","description":"Formats a list as bullet points for inclusion in a prompt.","line":1038},{"name":"generate_rules_batch","description":"Generates multiple rules from a taxonomy file.","line":1045}]}
"""
# FILE_MAP_END

"""
Enhanced Rule Generator

This module contains utilities for generating and verifying high-quality rule files.
It extends the basic rule generator with validation, verification, and automatic fixing.
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from openai import OpenAI

from rules_engine.generators.section_generator import generate_rule_section
from rules_engine.generators.example_generator import generate_detailed_example
from rules_engine.validators.rule_validator import verify_rule_quality
from rules_engine.validators.section_validator import (
    validate_section,
    post_process_danger_section,
)
from rules_engine.utils.file_utils import (
    ensure_rules_dir,
    rule_file_exists,
    get_rule_file_path,
    read_rule_file,
)
from rules_engine.utils.reasoning import apply_reasoning_method
from rules_engine.generators.rule_generator import analyze_dependencies

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Base path for rules
RULES_DIR = ".cursor/rules/"

# Base path for rule guidance files - adjust this to the parent directory for proper file access
RULE_GUIDANCE_DIR = "../.cursor/rules/"


class ValidationError(Exception):
    """Exception raised when rule content fails validation.

    Attributes:
        message -- explanation of the error
        section -- section that failed validation
        feedback -- validation feedback
    """

    def __init__(self, message: str, section: str = None, feedback: str = None):
        self.message = message
        self.section = section
        self.feedback = feedback
        super().__init__(self.message)


def generate_and_validate_section(
    rule_id: str,
    rule_name: str,
    section: str,
    category: str,
    previous_sections: Optional[Dict[str, Any]] = None,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Generate a section and validate it, with retries if needed.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule
        section: The section to generate
        category: The category of the rule
        previous_sections: Previously generated sections for context
        max_attempts: Maximum number of attempts to generate a valid section

    Returns:
        Dictionary with the validated section content

    Raises:
        ValidationError: If section fails validation after max attempts
    """
    print(f"  Generating {section} for rule {rule_id}...")

    for attempt in range(max_attempts):
        # Generate the section
        content = generate_rule_section(
            rule_id, rule_name, section, category, previous_sections
        )

        # Validate the section
        is_valid, feedback = validate_section(rule_id, rule_name, section, content)

        if is_valid:
            print(f"  ✓ Generated valid {section}")
            return content

        # If not valid and we have more attempts, try again with feedback
        if attempt < max_attempts - 1:
            print(f"  ! Validation issues with {section}: {feedback}, regenerating...")
            # Use the feedback to guide the next generation attempt
            if previous_sections is None:
                previous_sections = {}
            previous_sections[f"{section}_feedback"] = feedback
        else:
            # After max attempts with no valid result, raise an exception
            error_message = f"Failed to generate valid {section} for rule {rule_id} after {max_attempts} attempts. Last feedback: {feedback}"
            print(f"  ! {error_message}")
            raise ValidationError(error_message, section=section, feedback=feedback)

    # This should never be reached due to the exception above, but as a failsafe:
    raise ValidationError(
        f"Failed to generate valid {section} for rule {rule_id}", section=section
    )


def create_placeholder_section(
    section: str, rule_id: str, rule_name: str
) -> Dict[str, Any]:
    """
    Create a placeholder section as a fallback when generation fails.

    Args:
        section: The section name
        rule_id: The ID of the rule
        rule_name: The name of the rule

    Returns:
        Dictionary with placeholder content
    """
    if section == "frontmatter":
        return {
            "description": f"MUST FOLLOW {rule_name} standards WHEN implementing related functionality TO ensure quality and consistency",
            "globs": ["**/*"],
        }
    elif section == "metadata":
        return {
            "rule_id": f"{rule_id}-{rule_name.lower().replace(' ', '-')}",
            "taxonomy": {
                "category": "Core",
                "parent": "CoreRule",
                "ancestors": ["Rule", "CoreRule"],
                "children": [],
            },
            "tags": [rule_name.lower().replace(" ", "-")],
            "priority": 50,
            "inherits": [],
        }
    elif section == "overview":
        return {
            "purpose": f"Define standards for {rule_name}",
            "application": "Apply these standards consistently",
            "importance": "Ensures quality and consistency",
        }
    elif section == "main_sections":
        return {
            "requirements": {
                "description": f"Core requirements for {rule_name}",
                "requirements": [
                    f"Follow best practices for {rule_name}",
                    "Ensure consistency across implementations",
                    "Document any deviations from standards",
                ],
            }
        }
    elif section == "examples":
        return {
            "title": f"{rule_name} Example",
            "code": f"```python\n# Example for {rule_name}\ndef example():\n    # Implement according to standards\n    pass\n```",
            "explanation": f"This example demonstrates how to implement {rule_name} according to the standards.",
        }
    elif section == "danger":
        return {
            "critical_violations": [
                f"NEVER ignore {rule_name} standards",
                f"NEVER implement {rule_name} without proper documentation",
                f"NEVER use anti-patterns that violate {rule_name} principles",
            ],
            "specific_risks": [
                f"Ignoring {rule_name} standards leads to inconsistent implementations",
                f"Poor {rule_name} implementations result in maintenance challenges",
                f"Security vulnerabilities may arise from improper {rule_name} implementations",
            ],
        }
    else:
        return {"placeholder": f"Content for {section} section"}


def create_rule_file(rule_id: str, rule_name: str, category: str) -> str:
    """
    Create a complete rule file by generating all sections with validation.

    If any section fails validation after maximum attempts, the entire rule
    generation process will fail with a clear error message.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        category: Category of the rule

    Returns:
        Path to the created rule file

    Raises:
        ValidationError: If any section fails validation
    """
    # Ensure rules directory exists
    ensure_rules_dir(RULES_DIR)

    # Create a slug version of the rule name
    rule_slug = rule_name.lower().replace(" ", "-")

    # Check if the rule already exists
    if rule_file_exists(rule_id, rule_slug):
        print(f"Rule {rule_id} already exists. Skipping.")
        return str(get_rule_file_path(rule_id, rule_slug))

    print(f"Generating rule {rule_id}: {rule_name} with validation")

    generation_log = {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "category": category,
        "status": "started",
        "sections_generated": [],
        "sections_failed": [],
        "error": None,
    }

    try:
        # Generate each section with validation
        frontmatter = generate_and_validate_section(
            rule_id, rule_name, "frontmatter", category
        )
        generation_log["sections_generated"].append("frontmatter")

        # Get rule dependencies for metadata
        dependencies = analyze_dependencies(rule_id, rule_name, category)

        # Generate metadata with dependencies
        metadata = generate_and_validate_section(
            rule_id, rule_name, "metadata", category
        )
        metadata["inherits"] = dependencies
        generation_log["sections_generated"].append("metadata")

        # Generate overview with previous sections for context
        previous_sections = {"frontmatter": frontmatter, "metadata": metadata}

        overview = generate_and_validate_section(
            rule_id, rule_name, "overview", category, previous_sections
        )
        generation_log["sections_generated"].append("overview")
        previous_sections["overview"] = overview

        # Generate main sections
        main_sections = generate_and_validate_section(
            rule_id, rule_name, "main_sections", category, previous_sections
        )
        generation_log["sections_generated"].append("main_sections")
        previous_sections["main_sections"] = main_sections

        # Generate examples using detailed example generator
        examples = generate_detailed_example(
            rule_id, rule_name, category, previous_sections
        )
        generation_log["sections_generated"].append("examples")
        previous_sections["examples"] = examples

        # Generate danger section
        danger = generate_and_validate_section(
            rule_id, rule_name, "danger", category, previous_sections
        )
        generation_log["sections_generated"].append("danger")

        # Create the complete rule content
        rule_content = {
            "frontmatter": frontmatter,
            "metadata": metadata,
            "overview": overview,
            "main_sections": main_sections,
            "examples": examples,
            "danger": danger,
        }

        # Format and save the rule
        rule_text = _format_rule_content(rule_id, rule_name, rule_content)

        # Save to file
        file_path = get_rule_file_path(rule_id, rule_slug)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rule_text)

        generation_log["status"] = "success"
        print(f"✅ Successfully created rule file: {file_path}")
        return str(file_path)

    except ValidationError as ve:
        # Log the validation error and clearly indicate failure
        error_message = f"Rule generation failed: {ve.message}"
        generation_log["status"] = "failed_validation"
        generation_log["error"] = error_message
        generation_log["sections_failed"].append(ve.section)

        # Save the generation log for debugging
        log_path = f".cursor/logs/rule_{rule_id}_generation_failure.json"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(generation_log, f, indent=2)

        print(f"❌ Rule generation FAILED: {error_message}")
        print(f"   Generation log saved to: {log_path}")
        raise

    except Exception as e:
        # Log any other errors
        error_message = f"Unexpected error during rule generation: {str(e)}"
        generation_log["status"] = "failed_error"
        generation_log["error"] = error_message

        # Save the generation log for debugging
        log_path = f".cursor/logs/rule_{rule_id}_generation_error.json"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(generation_log, f, indent=2)

        print(f"❌ Rule generation FAILED with error: {error_message}")
        print(f"   Generation log saved to: {log_path}")
        raise


def _format_rule_content(
    rule_id: str, rule_name: str, rule_content: Dict[str, Any]
) -> str:
    """
    Format the rule content into the correct .mdc format.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        rule_content: Dictionary with all rule sections

    Returns:
        Formatted rule text
    """
    # Extract sections
    frontmatter = rule_content["frontmatter"]
    metadata = rule_content["metadata"]
    overview = rule_content["overview"]
    main_sections = rule_content["main_sections"]
    examples = rule_content["examples"]
    danger = rule_content["danger"]

    # Build the rule file content
    rule_text = f"""---
description: {frontmatter["description"]}
globs: {json.dumps(frontmatter["globs"])}
---
# {rule_name}

<version>1.0.0</version>

## Metadata
{json.dumps(metadata, indent=2)}

## Overview
{json.dumps(overview, indent=2)}

"""

    # Add main section content
    for section_name, section_content in main_sections.items():
        rule_text += f"## {section_name}\n\n{json.dumps(section_content, indent=2)}\n\n"

    # Add examples section (avoiding f-string backslash issue)
    example_title = examples.get("title", rule_name + " Example")
    example_code = examples.get("code", "```\n# Example code\n```")
    example_explanation = examples.get("explanation", "Example explanation")
    rule_text += f"<example>\n{example_title}\n\n{example_code}\n\n{example_explanation}\n</example>\n\n"

    # Add danger section
    rule_text += f"<danger>\n{json.dumps(danger, indent=2)}\n</danger>\n"

    return rule_text


def verify_rule_quality(file_path: str) -> Dict[str, Any]:
    """
    Perform thorough verification of a generated rule.

    Args:
        file_path: Path to the rule file

    Returns:
        Dictionary with verification results
    """
    print(f"Verifying rule quality: {file_path}")

    try:
        rule_content = read_file_content(file_path)
        if not rule_content:
            return {
                "status": "error",
                "message": f"Could not read file: {file_path}",
                "checks": {},
                "issues": ["File could not be read"],
                "suggestions": ["Check file permissions and if the file exists"],
            }

        # Get rule ID and name from filename
        file_name = Path(file_path).name
        rule_id_match = re.match(r"(\d+)-(.+)\.mdc", file_name)
        rule_id = rule_id_match.group(1) if rule_id_match else "Unknown"
        rule_name = (
            rule_id_match.group(2).replace("-", " ").title()
            if rule_id_match
            else "Unknown"
        )

        # Initialize verification results
        verification = {
            "file_path": file_path,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "status": "verifying",
            "checks": {
                "frontmatter_format": False,
                "structure_completeness": False,
                "content_quality": False,
                "description_format": False,
                "example_quality": False,
                "danger_format": False,
            },
            "issues": [],
            "suggestions": [],
        }

        # Check 1: Verify frontmatter format
        frontmatter_pattern = re.compile(
            r"^---\ndescription: MUST .+ WHEN .+ TO .+\nglobs: \[.+\]\n---$",
            re.MULTILINE,
        )
        if frontmatter_pattern.search(rule_content):
            verification["checks"]["frontmatter_format"] = True
        else:
            verification["issues"].append(
                "Frontmatter does not follow the required format"
            )

        # Check 2: Verify structure completeness
        required_sections = [
            "# ",
            "<version>",
            "## Metadata",
            "## Overview",
            "<example>",
            "<danger>",
        ]
        missing_sections = []
        for section in required_sections:
            if section not in rule_content:
                missing_sections.append(section)

        if not missing_sections:
            verification["checks"]["structure_completeness"] = True
        else:
            verification["issues"].append(
                f"Missing required sections: {', '.join(missing_sections)}"
            )

        # Check 3: Verify description format
        description_pattern = re.compile(r"description: MUST .+ WHEN .+ TO .+")
        if description_pattern.search(rule_content):
            verification["checks"]["description_format"] = True
        else:
            verification["issues"].append(
                "Description does not follow MUST-WHEN-TO format"
            )

        # Check 4: Verify content quality
        # This is a basic check for now - could be enhanced with LLM evaluation
        if (
            len(rule_content) > 500
            and "## " in rule_content
            and "{" in rule_content
            and "}" in rule_content
        ):
            verification["checks"]["content_quality"] = True
        else:
            verification["issues"].append(
                "Rule content may lack sufficient detail or structure"
            )

        # Check 5: Verify example quality
        example_pattern = re.compile(r"<example>.*```.*```.*</example>", re.DOTALL)
        if example_pattern.search(rule_content):
            verification["checks"]["example_quality"] = True
        else:
            verification["issues"].append("Example section does not contain code block")

        # Check 6: Verify danger format
        danger_pattern = re.compile(r"<danger>.*NEVER.*</danger>", re.DOTALL)
        if danger_pattern.search(rule_content):
            verification["checks"]["danger_format"] = True
        else:
            verification["issues"].append(
                "Danger section may not properly list critical violations (NEVER statements)"
            )

        # Determine overall status
        passed_checks = sum(1 for check in verification["checks"].values() if check)
        total_checks = len(verification["checks"])
        verification["checks_passed"] = passed_checks
        verification["total_checks"] = total_checks

        if passed_checks == total_checks:
            verification["status"] = "verified"
            verification["message"] = "Rule passes all quality checks"
        elif passed_checks >= total_checks * 0.75:
            verification["status"] = "verified_with_warnings"
            verification[
                "message"
            ] = f"Rule passes most checks ({passed_checks}/{total_checks}) but has some issues"
            verification["suggestions"].append(
                "Consider manual review of the identified issues"
            )
        else:
            verification["status"] = "verification_failed"
            verification[
                "message"
            ] = f"Rule fails multiple quality checks ({passed_checks}/{total_checks})"
            verification["suggestions"].append(
                "Rule may need to be regenerated or manually fixed"
            )

        return verification

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error verifying rule: {str(e)}",
            "checks": {},
            "issues": [f"Exception during verification: {str(e)}"],
            "suggestions": ["Check file permissions and content format"],
        }


def read_file_content(file_path: str) -> Optional[str]:
    """
    Read a file and return its content.

    Args:
        file_path: Path to the file

    Returns:
        The file content as a string, or None if the file could not be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None


def fix_rule_section(
    rule_id: str, rule_name: str, section: str, file_path: str
) -> bool:
    """
    Fix a specific section in a rule file.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule
        section: The section to fix ('frontmatter', 'metadata', 'overview', etc.)
        file_path: Path to the rule file

    Returns:
        True if the section was fixed, False otherwise
    """
    print(f"Fixing {section} in rule {rule_id}...")

    try:
        # Read the current file content
        current_content = read_file_content(file_path)
        if not current_content:
            print(f"  ❌ Could not read file: {file_path}")
            return False

        # Extract the category from the filename or content
        category_match = re.search(r'"category":\s*"([^"]+)"', current_content)
        category = category_match.group(1) if category_match else "Unknown"

        # Regenerate the specific section
        if section == "frontmatter":
            # Extract and fix the frontmatter
            new_section = generate_rule_section(
                rule_id, rule_name, "frontmatter", category
            )
            # Update the frontmatter in the file
            updated_content = re.sub(
                r"^---\ndescription:.*\nglobs:.*\n---",
                f'---\ndescription: {new_section["description"]}\nglobs: {json.dumps(new_section["globs"])}\n---',
                current_content,
                flags=re.MULTILINE,
            )

        elif section == "metadata":
            # Extract and fix the metadata
            new_section = generate_rule_section(
                rule_id, rule_name, "metadata", category
            )
            # Update the metadata in the file
            updated_content = re.sub(
                r"## Metadata\n\{.*?\}",
                f"## Metadata\n{json.dumps(new_section, indent=2)}",
                current_content,
                flags=re.DOTALL,
            )

        elif section == "overview":
            # Extract and fix the overview
            new_section = generate_rule_section(
                rule_id, rule_name, "overview", category
            )
            # Update the overview in the file
            updated_content = re.sub(
                r"## Overview\n\{.*?\}",
                f"## Overview\n{json.dumps(new_section, indent=2)}",
                current_content,
                flags=re.DOTALL,
            )

        elif section == "examples":
            # Extract and fix the examples
            new_section = generate_detailed_example(rule_id, rule_name, category, {})
            # Update the examples in the file
            example_title = new_section.get("title", rule_name + " Example")
            example_code = new_section.get("code", "```\n# Example code\n```")
            example_explanation = new_section.get("explanation", "Example explanation")
            examples_content = f"<example>\n{example_title}\n\n{example_code}\n\n{example_explanation}\n</example>"
            updated_content = re.sub(
                r"<example>.*?</example>",
                examples_content,
                current_content,
                flags=re.DOTALL,
            )

        elif section == "danger":
            # Extract and fix the danger section
            new_section = generate_rule_section(rule_id, rule_name, "danger", category)
            # Process the danger section to fix common issues
            new_section = post_process_danger_section(new_section, rule_name)
            # Update the danger section in the file
            updated_content = re.sub(
                r"<danger>.*?</danger>",
                f"<danger>\n{json.dumps(new_section, indent=2)}\n</danger>",
                current_content,
                flags=re.DOTALL,
            )

        else:
            print(f"  ❌ Unsupported section for fixing: {section}")
            return False

        # Write the updated content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(f"  ✓ Fixed {section} in rule {rule_id}")
        return True

    except Exception as e:
        print(f"  ❌ Error fixing {section} in rule {rule_id}: {str(e)}")
        return False


def create_and_verify_rule(
    rule_id: str, rule_name: str, category: str, max_fix_attempts: int = 2
) -> str:
    """
    Create a rule file and verify its quality, with automatic fixing of issues.

    Args:
        rule_id: The ID of the rule to generate
        rule_name: The name of the rule
        category: The category of the rule
        max_fix_attempts: Maximum number of attempts to fix issues

    Returns:
        Path to the generated rule file
    """
    # Create the initial rule file
    file_path = create_rule_file(rule_id, rule_name, category)
    print(f"Generated rule file: {file_path}")

    # Verify the quality
    verification = verify_rule_quality(file_path)

    # If verification failed, attempt to fix the issues
    if verification["status"] != "verified":
        print(f"Verification issues: {', '.join(verification['feedback'])}")

        for attempt in range(max_fix_attempts):
            fixed_sections = []

            for section in ["frontmatter", "overview", "content", "example", "danger"]:
                if section not in verification["checks"] or not verification[
                    "checks"
                ].get(section, False):
                    print(f"  Attempting to fix {section} section...")
                    if fix_rule_section(rule_id, rule_name, section, file_path):
                        fixed_sections.append(section)

            if fixed_sections:
                print(f"  Fixed sections: {', '.join(fixed_sections)}")
                verification = verify_rule_quality(file_path)
                if verification["status"] == "verified":
                    print("  Verification passed after fixes")
                    break
            else:
                # If no sections were fixed, break the loop
                break

            if attempt == max_fix_attempts - 1:
                print(
                    f"  Could not fully fix all issues after {max_fix_attempts} attempts"
                )

    print(f"Rule generation completed: {file_path}")
    return file_path


def create_rule_with_feedback(
    rule_id: str,
    rule_name: str,
    category: str,
    original_content: str,
    feedback: Dict[str, List[str]],
) -> str:
    """
    Create an improved rule based on validation feedback, using advanced reasoning methods.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule
        category: The category of the rule
        original_content: The original rule content
        feedback: Dictionary containing strengths, weaknesses, and suggestions

    Returns:
        Improved rule content
    """
    import re

    print(f"Creating improved rule for {rule_id}: {rule_name} based on feedback")

    # Extract sections from the original content
    frontmatter_match = re.search(r"^---\n(.*?)\n---", original_content, re.DOTALL)
    frontmatter = frontmatter_match.group(0) if frontmatter_match else ""

    # Extract title
    title_match = re.search(r"# (.+)", original_content)
    title = title_match.group(0) if title_match else f"# {rule_name}"

    # Extract version tag
    version_match = re.search(r"<version>(.+?)</version>", original_content)
    version_tag = (
        version_match.group(0) if version_match else "<version>1.0.0</version>"
    )

    # Extract sections
    sections = {}
    section_pattern = r"## ([A-Za-z0-9 ]+)\n(.*?)(?=\n## [A-Za-z0-9 ]+\n|$)"
    for section_match in re.finditer(section_pattern, original_content, re.DOTALL):
        section_name = section_match.group(1).strip()
        section_content = section_match.group(2).strip()
        sections[section_name.lower()] = section_content

    # Extract example and danger sections
    example_match = re.search(
        r"<example>\n(.*?)\n</example>", original_content, re.DOTALL
    )
    example = (
        example_match.group(0)
        if example_match
        else "<example>\nExample content\n</example>"
    )

    danger_match = re.search(r"<danger>\n(.*?)\n</danger>", original_content, re.DOTALL)
    danger = danger_match.group(0) if danger_match else "<danger>\n{}\n</danger>"

    # Load rule 012 for standalone rule generation standards
    standalone_rules_generation_path = Path(
        RULE_GUIDANCE_DIR + "012-standalone-rules-generation.mdc"
    )
    standalone_rules_generation_content = None
    if standalone_rules_generation_path.exists():
        try:
            with open(standalone_rules_generation_path, "r", encoding="utf-8") as f:
                standalone_rules_generation_content = f.read()
            print(
                f"Successfully loaded rule 012 for standalone rule generation standards"
            )
        except Exception as e:
            print(f"Could not load rule 012: {str(e)}")

    # Load rule 015 for AI interpretability standards
    ai_interpretability_path = Path(
        RULE_GUIDANCE_DIR + "015-rule-ai-interpretability.mdc"
    )
    ai_interpretability_content = None
    if ai_interpretability_path.exists():
        try:
            with open(ai_interpretability_path, "r", encoding="utf-8") as f:
                ai_interpretability_content = f.read()
            print(f"Successfully loaded rule 015 for AI interpretability standards")
        except Exception as e:
            print(f"Could not load rule 015: {str(e)}")

    # Note: Rule 030 doesn't exist, so we'll skip loading it
    reasoning_methods_content = None

    # Prepare prompt for LLM to improve the rule
    strengths = feedback.get("strengths", [])
    weaknesses = feedback.get("weaknesses", [])
    suggestions = feedback.get("improvement_suggestions", [])

    prompt = f"""
# Rule Improvement Task

## Context
You are enhancing a rule that will be consumed by an AI assistant integrated into an IDE. This rule guides the AI's behavior when responding to user requests for code generation, documentation, and other development tasks.

When improving this rule, prioritize making requirements explicit using clear markers (like 'MUST' statements). The AI processing these rules needs to clearly identify what is required versus suggested.

Your improvements should focus on:
1. Making the rule algorithmically processable by the AI
2. Using consistent explicit directives (MUST, SHOULD, NEVER) throughout the rule
3. Providing unambiguous guidance the AI can follow when making decisions
4. Enabling the AI to explain its decisions to developers by citing specific rule requirements
5. Ensuring the rule can be applied consistently across different situations

## Original Rule Content
```
{original_content}
```

## Improvement Requirements

### Strengths to Preserve and Enhance
{format_list_for_prompt(strengths)}

### Weaknesses to Address
{format_list_for_prompt(weaknesses)}

### Specific Improvement Suggestions
{format_list_for_prompt(suggestions)}

## Quality Target
Your goal is to achieve a quality level of 9/10 or better. To reach this level:

1. Use explicit directives (MUST, SHOULD, NEVER) consistently throughout the rule
2. Make all guidance extremely specific and actionable
3. Provide concrete examples for complex concepts
4. Cover all relevant edge cases and variations
5. Clearly explain consequences of violations with specific impacts
6. Maintain perfect internal consistency
7. Demonstrate technical precision and domain expertise

## Improvement Guidelines

1. **Keep the Same Structure**: Maintain all existing sections and their order.

2. **Preserve Technical Elements**: Keep the frontmatter, title, version tag unchanged.

3. **Enhance Content Quality**:
   - Add explicit MUST/SHOULD/NEVER directives to all requirements
   - Replace vague guidance with specific, concrete directives
   - Add precise technical details where lacking
   - Ensure each requirement is actionable and measurable
   - Use the MUST-WHEN-TO format consistently in descriptions
"""

    # Add rule structure standards if available
    if standalone_rules_generation_content:
        prompt += f"""
## Rule Structure Standards

Apply these rule structure standards from Rule 012:
```
{standalone_rules_generation_content}
```

Follow these structural standards precisely while maintaining the rule's purpose and intent.
"""

    # Add AI interpretability standards if available
    if ai_interpretability_content:
        prompt += f"""
## AI Interpretability Standards

Follow these AI interpretability standards from Rule 015:
```
{ai_interpretability_content}
```

Apply these standards to ensure the rule can be effectively processed by an AI system.
"""

    # Add reasoning methods content if available
    if reasoning_methods_content:
        prompt += f"""
## Advanced Reasoning Methods

Apply these reasoning methods from rule 030 in your improvement process:
```
{reasoning_methods_content}
```

Demonstrate use of these methods by:
1. Considering multiple improvement strategies and selecting the optimal approach
2. Breaking down improvements section-by-section with logical connections
3. Refining each improvement iteratively for maximum quality
4. Maintaining awareness of how each improvement affects the overall rule
5. Acknowledging domain-specific aspects that require special attention
"""

    # Process any scenario insights from practical testing
    if "scenario_insights" in feedback:
        scenario_insights = feedback.get("scenario_insights", [])
        prompt += f"""
## Practical Testing Insights

The following insights were gathered from practical testing of this rule in real-world scenarios.
Each insight shows how the rule performed when applied by an AI in specific contexts:

{format_list_for_prompt(scenario_insights)}

Incorporate these practical insights into your improvements to ensure the rule works effectively in real situations.
"""

    prompt += """
## Response Format
Provide ONLY the complete improved rule content with no additional commentary. Do not include backticks or markdown formatting around your response.
"""

    # Use the OpenAI client to get the improved content
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    try:
        # Prepare our advanced system message
        advanced_system_message = (
            """You are a master rule architect specializing in creating precise, actionable guidelines for AI assistants.

## Project-Specific Context
You are currently improving rules for the Rule Generator Enhancement Project. This project aims to:

1. Enhance the existing rule generation system to support hierarchical parent/child rules
2. Integrate documentation content when generating rules
3. Create proper directory and file organization for different rule types
4. Support parallel generation workflows for efficiency

The rule you are improving (ID: """
            + rule_id
            + """, Name: """
            + rule_name
            + """) is a project-specific rule in the 900-999 range, 
which will guide the implementation of the enhanced rule generation system. These rules will ultimately be used to 
generate documentation standard rules based on comprehensive guidelines in the docs/doc-standards/ directory.

When improving this rule, focus on implementation requirements related to:
- Parent/child rule relationships and hierarchy
- Documentation content extraction and integration
- Rule file path management and directory organization
- Parallel workflow management for efficiency
- Consistency validation across rule sets

## Expertise Areas
Your expertise includes:
- Creating unambiguous directives using MUST/SHOULD/NEVER language
- Designing decision-tree-like structures that an AI can algorithmically follow
- Balancing precision with practical applicability
- Adding specific examples that demonstrate rule implementation
- Defining explicit consequences for rule violations
- Optimizing rules for machine interpretation while maintaining human readability
"""
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o-mini as we don't have access to GPT-4o
            messages=[
                {"role": "system", "content": advanced_system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,  # Balanced creativity and consistency
            max_tokens=4000,
        )

        # Extract the improved content
        improved_content = response.choices[0].message.content.strip()

        # Clean up the content - remove any markdown code block formatting
        # Remove opening markdown/code block indicators
        improved_content = re.sub(r"^```(\w*)\s*\n", "", improved_content)
        # Remove closing code block indicators
        improved_content = re.sub(r"\n```\s*$", "", improved_content)
        # Remove any explanatory text before the content
        if improved_content.lstrip().startswith("Here's") and "---" in improved_content:
            improved_content = improved_content[improved_content.find("---") :]

        # Improve version number to reflect significant enhancement
        current_version = "1.0.0"
        if version_match:
            current_version = version_match.group(1)

        # Parse current version and increment minor version for significant improvements
        try:
            version_parts = current_version.split(".")
            new_version = f"{version_parts[0]}.{int(version_parts[1]) + 1}.0"
            improved_content = improved_content.replace(
                f"<version>{current_version}</version>",
                f"<version>{new_version}</version>",
            )
        except Exception as e:
            print(f"Error updating version: {str(e)}")

        print(f"Generated improved rule content for {rule_id}: {rule_name}")
        return improved_content

    except Exception as e:
        print(f"Error generating improved rule: {str(e)}")
        # If there's an error, return the original content
        return original_content


def format_list_for_prompt(items: List[str]) -> str:
    """Format a list as bullet points for inclusion in a prompt."""
    if not items:
        return "- None identified"
    return "\n".join(f"- {item}" for item in items)


def generate_rules_batch(
    taxonomy_file: str, max_workers=2, max_rules=None
) -> List[str]:
    """
    Generate multiple rules from a taxonomy file.

    Args:
        taxonomy_file: Path to taxonomy file
        max_workers: Maximum number of concurrent workers
        max_rules: Maximum number of rules to generate

    Returns:
        List of paths to generated rule files
    """
    print(f"Generating rules from taxonomy: {taxonomy_file}")

    # Load the taxonomy
    with open(taxonomy_file, "r", encoding="utf-8") as f:
        taxonomy = yaml.safe_load(f)

    # Extract rules to generate
    rules_to_generate = []
    for category in taxonomy.get("categories", []):
        category_name = category.get("name", "Unknown")
        for rule in category.get("rules", []):
            rules_to_generate.append(
                {
                    "rule_id": rule.get("id", "000"),
                    "rule_name": rule.get("name", "Unknown Rule"),
                    "category": category_name,
                }
            )

    # Limit number of rules if specified
    if max_rules is not None and max_rules > 0:
        rules_to_generate = rules_to_generate[:max_rules]

    print(f"Will generate {len(rules_to_generate)} rules")

    # Generate each rule
    generated_files = []
    for rule in rules_to_generate:
        try:
            rule_id = rule["rule_id"]
            rule_name = rule["rule_name"]
            category = rule["category"]

            # Generate the rule file with validation and fixing
            file_path = create_and_verify_rule(rule_id, rule_name, category)
            generated_files.append(file_path)

        except Exception as e:
            print(f"Error generating rule {rule['rule_id']}: {str(e)}")

    return generated_files
