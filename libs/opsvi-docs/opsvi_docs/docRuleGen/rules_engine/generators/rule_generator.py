# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Rule Generator","description":"This module contains utilities for generating complete rule files.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"This section contains all the necessary imports for the module.","line_start":3,"line_end":27},{"name":"Global Variables","description":"This section initializes global variables used throughout the module.","line_start":29,"line_end":32},{"name":"analyze_dependencies Function","description":"This function analyzes which rules a given rule might depend on or inherit from.","line_start":34,"line_end":69},{"name":"generate_rule_sections_parallel Function","description":"This function generates all sections of a rule in parallel where possible.","line_start":95,"line_end":153},{"name":"create_rule_file Function","description":"This function creates a rule file with all necessary sections.","line_start":154,"line_end":198},{"name":"_format_rule_content Function","description":"This function formats the rule content into the correct .mdc format.","line_start":200,"line_end":253},{"name":"generate_rules_batch Function","description":"This function generates multiple rules from a taxonomy file.","line_start":255,"line_end":312}],"key_elements":[{"name":"analyze_dependencies","description":"Analyzes dependencies for a given rule.","line":35},{"name":"generate_rule_sections_parallel","description":"Generates rule sections in parallel.","line":96},{"name":"create_rule_file","description":"Creates a complete rule file.","line":155},{"name":"_format_rule_content","description":"Formats rule content into .mdc format.","line":199},{"name":"generate_rules_batch","description":"Generates multiple rules from a taxonomy file.","line":254},{"name":"client","description":"OpenAI client initialized with API key.","line":28},{"name":"RULES_DIR","description":"Base path for rules.","line":30}]}
"""
# FILE_MAP_END

"""
Rule Generator

This module contains utilities for generating complete rule files.
"""

import os
import json
import time
import re
import yaml
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from rules_engine.generators.section_generator import generate_rule_section
from rules_engine.generators.example_generator import generate_detailed_example
from rules_engine.validators.rule_validator import verify_rule_quality
from rules_engine.utils.file_utils import (
    ensure_rules_dir,
    rule_file_exists,
    get_rule_file_path,
)
from rules_engine.utils.reasoning import apply_reasoning_method

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Base path for rules
RULES_DIR = ".cursor/rules/"


def analyze_dependencies(rule_id: str, rule_name: str, category: str) -> List[str]:
    """
    Analyze which rules this rule might depend on or inherit from.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        category: Category of the rule

    Returns:
        List of rule IDs that this rule depends on
    """
    # Core rules that most rules depend on
    core_dependencies = ["000", "020", "030"]

    # Category-specific dependencies
    category_dependencies = {
        # Python best practices, Python async
        "LLM Integration": ["1000", "1005"],
        # LLM API integration, Python best practices
        "Multi-Agent": ["1050", "1000"],
        # Python best practices, LLM API integration
        "Knowledge Management": ["1000", "1050"],
        "Python Engine": ["1000"],  # Python best practices
        # Python best practices, Memory management
        "System Interface": ["1000", "1010"],
    }

    # Rule-specific dependencies
    rule_specific_dependencies = {
        "1055": ["1050"],  # Prompt Engineering depends on LLM API Integration
        # Output Parsing depends on API Integration and Prompt Engineering
        "1060": ["1050", "1055"],
        "1105": ["1100"],  # Agent Communication depends on Agent Architecture
        # Agent Orchestration depends on Architecture and Communication
        "1110": ["1100", "1105"],
        # Embedding Strategies depends on Knowledge Retrieval
        "1155": ["1150"],
    }

    # Start with core dependencies
    dependencies = core_dependencies.copy()

    # Add category-specific dependencies
    if category in category_dependencies:
        for dep in category_dependencies[category]:
            if dep not in dependencies and dep != rule_id:  # Avoid self-dependency
                dependencies.append(dep)

    # Add rule-specific dependencies
    if rule_id in rule_specific_dependencies:
        for dep in rule_specific_dependencies[rule_id]:
            if dep not in dependencies and dep != rule_id:  # Avoid self-dependency
                dependencies.append(dep)

    # Remove any dependencies with higher numbers (can't depend on future rules)
    dependencies = [dep for dep in dependencies if dep < rule_id]

    return dependencies


def generate_rule_sections_parallel(
    rule_id: str, rule_name: str, category: str
) -> Dict[str, Any]:
    """
    Generate all sections of a rule in parallel where possible.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        category: Category of the rule

    Returns:
        Dictionary with all rule sections
    """
    print(f"Generating rule {rule_id}: {rule_name}")

    # Initial sections that don't have dependencies
    frontmatter = generate_rule_section(rule_id, rule_name, "frontmatter", category)
    print(f"  ✓ Generated frontmatter")

    # Get rule dependencies for metadata
    dependencies = analyze_dependencies(rule_id, rule_name, category)

    # Generate metadata with dependencies
    metadata = generate_rule_section(rule_id, rule_name, "metadata", category)
    metadata["inherits"] = dependencies
    print(f"  ✓ Generated metadata")

    # Generate overview
    overview = generate_rule_section(rule_id, rule_name, "overview", category)
    print(f"  ✓ Generated overview")

    # Create initial section results
    rule_content = {
        "frontmatter": frontmatter,
        "metadata": metadata,
        "overview": overview,
    }

    # Generate main sections
    main_sections = generate_rule_section(
        rule_id, rule_name, "main_sections", category, rule_content
    )
    print(f"  ✓ Generated main sections")
    rule_content["main_sections"] = main_sections

    # Generate examples using detailed example generator
    examples = generate_detailed_example(rule_id, rule_name, category, rule_content)
    print(f"  ✓ Generated examples")
    rule_content["examples"] = examples

    # Generate danger section
    danger = generate_rule_section(rule_id, rule_name, "danger", category, rule_content)
    print(f"  ✓ Generated danger section")
    rule_content["danger"] = danger

    return rule_content


def create_rule_file(rule_id: str, rule_name: str, category: str) -> str:
    """
    Create a rule file with all necessary sections.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        category: Category of the rule

    Returns:
        Path to the created rule file
    """
    # Validate rule ID format
    if rule_id.endswith("00"):
        raise ValueError(
            f"Rule ID {rule_id} ends with '00', which is reserved for section headers. Use x01, x11, x21, etc."
        )

    # Create a slug version of the rule name
    rule_slug = rule_name.lower().replace(" ", "-")

    # Check if the rule already exists
    if rule_file_exists(rule_id, rule_slug):
        print(f"Rule {rule_id} already exists. Skipping.")
        return get_rule_file_path(rule_id, rule_slug)

    # Generate all rule content
    rule_content = generate_rule_sections_parallel(rule_id, rule_name, category)

    # Format the rule content
    rule_text = _format_rule_content(rule_id, rule_name, rule_content)

    # Ensure the rules directory exists
    ensure_rules_dir()

    # Write to file
    file_path = get_rule_file_path(rule_id, rule_slug)
    with open(file_path, "w") as f:
        f.write(rule_text)

    print(f"Rule {rule_id} written to {file_path}")
    return file_path


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

    # Add examples section
    example_title = examples.get("title", rule_name + " Example")
    example_code = examples.get("code", "```\n# Example code\n```")
    example_explanation = examples.get("explanation", "Example explanation")
    rule_text += f"<example>\n{example_title}\n\n{example_code}\n\n{example_explanation}\n</example>\n\n"

    # Add danger section
    rule_text += f"<danger>\n{json.dumps(danger, indent=2)}\n</danger>\n"

    return rule_text


def generate_rules_batch(
    taxonomy_file: str, max_workers=2, max_rules=None
) -> List[str]:
    """
    Generate multiple rules from a taxonomy file.

    Args:
        taxonomy_file: Path to the YAML taxonomy file
        max_workers: Maximum number of concurrent workers
        max_rules: Maximum number of rules to generate (for testing)

    Returns:
        List of paths to created rule files
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

            # Generate the rule file
            file_path = create_rule_file(rule_id, rule_name, category)
            generated_files.append(file_path)

            # Optional: Verify the rule quality
            verification = verify_rule_quality(file_path)
            status = verification.get("status", "unknown")
            print(f"Rule {rule_id} verification status: {status}")

        except Exception as e:
            print(f"Error generating rule {rule['rule_id']}: {str(e)}")

    return generated_files
