# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Documentation Rule Generator","description":"This module coordinates the extraction of content from documentation files, transformation to rule format, and generation of documentation rules.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation for the purpose of the module.","line_start":2,"line_end":5},{"name":"Imports","description":"All necessary imports for the module functionality.","line_start":7,"line_end":35},{"name":"Client Initialization","description":"Initialization of the OpenAI client and logging configuration.","line_start":36,"line_end":48},{"name":"Constants","description":"Definition of constants used throughout the module.","line_start":50,"line_end":62},{"name":"Cache","description":"Cache for rule content to avoid reloading from files.","line_start":63,"line_end":63},{"name":"Function: load_rule_content","description":"Loads rule content from a file or cache.","line_start":64,"line_end":82},{"name":"Function: generate_doc_rule","description":"Generates a documentation rule from documentation standard files using LLM.","line_start":83,"line_end":303},{"name":"Function: build_rule_file","description":"Builds the rule file with frontmatter and content.","line_start":304,"line_end":384},{"name":"Function: create_parent_child_relationships","description":"Updates parent rule to include references to child rules and organize child rules into subdirectories.","line_start":385,"line_end":645},{"name":"Function: generate_rules_from_taxonomy","description":"Generates documentation rules from a taxonomy file.","line_start":646,"line_end":923}],"key_elements":[{"name":"load_rule_content","description":"Loads rule content from a file or cache.","line":64},{"name":"generate_doc_rule","description":"Generates a documentation rule from documentation standard files using LLM.","line":83},{"name":"build_rule_file","description":"Builds the rule file with frontmatter and content.","line":304},{"name":"create_parent_child_relationships","description":"Updates parent rule to include references to child rules and organize child rules into subdirectories.","line":385},{"name":"generate_rules_from_taxonomy","description":"Generates documentation rules from a taxonomy file.","line":646}]}
"""
# FILE_MAP_END

"""
Documentation Rule Generator Module for Documentation Standards Rule Generation.

This module coordinates the extraction of content from documentation files,
transformation to rule format, and generation of documentation rules.
"""

import os
import json
import yaml  # Add YAML import
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time

from ..extractors.documentation_extractor import (
    extract_documentation_for_rule,
    generate_glob_patterns,
)

from ..transformers.markdown_to_rule import (
    transform_to_rule_content,
    generate_rule_description,
)

# Import existing LLM-based generators

# Import OpenAI client
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load rule generation rules - Updated to use absolute paths
PROJECT_ROOT = "/home/opsvi/cursor_rules"
RULES_DIR = f"{PROJECT_ROOT}/.cursor/rules/"
RULE_010_PATH = f"{RULES_DIR}010-cursor-rules-generation.mdc"
RULE_011_PATH = f"{RULES_DIR}011-subrule-generation.mdc"

# Cache for rule content
rule_cache = {}


def load_rule_content(rule_path: str) -> str:
    """Load rule content from file or cache."""
    if rule_path in rule_cache:
        return rule_cache[rule_path]

    try:
        with open(rule_path, "r", encoding="utf-8") as f:
            content = f.read()
            rule_cache[rule_path] = content
            return content
    except FileNotFoundError:
        logger.warning(f"Rule file not found: {rule_path}")
        return ""


def generate_doc_rule(
    rule_id: str,
    rule_name: str,
    doc_paths: List[str],
    category: str,
    doc_dir: str,
    parent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a documentation rule from documentation standard files using LLM.

    Args:
        rule_id: ID of the rule to generate
        rule_name: Name of the rule
        doc_paths: Paths to documentation files to extract from (relative to doc_dir)
        category: Category of the rule
        doc_dir: Base directory for documentation files
        parent_id: Optional parent rule ID for child rules

    Returns:
        Dictionary containing the rule file path and rule content
    """
    logger.info(f"Generating documentation rule {rule_id}: {rule_name}")

    # Extract content from documentation files for context
    extracted_content = extract_documentation_for_rule(
        rule_id=rule_id, rule_name=rule_name, source_files=doc_paths, doc_dir=doc_dir
    )

    if "error" in extracted_content:
        logger.error(f"Error extracting content: {extracted_content['error']}")
        return {"error": extracted_content["error"]}

    # Add parent reference if provided
    if parent_id:
        extracted_content["parent_rule"] = parent_id

    # Determine if this is a parent rule or child rule - Use parent_id as the definitive indicator
    # If parent_id is None or empty, this is a parent rule
    is_parent_rule = not parent_id

    # Log the rule type determination
    if is_parent_rule:
        logger.info(
            f"Rule {rule_id} is a parent rule (no parent_id), using rule 010 for generation"
        )
    else:
        logger.info(
            f"Rule {rule_id} is a child rule (parent_id: {parent_id}), using rule 011 for generation"
        )

    # Load appropriate rule generation rule
    rule_generation_content = ""
    if is_parent_rule:
        # This is a parent rule, load rule 010
        rule_generation_content = load_rule_content(RULE_010_PATH)
    else:
        # This is a child rule, load rule 011
        rule_generation_content = load_rule_content(RULE_011_PATH)

    # Add has_children flag to extracted content based on taxonomy data
    extracted_content["has_children"] = "child_rules" in extracted_content

    # Transform extracted content to a structured format for the prompt
    doc_context = json.dumps(extracted_content, indent=2)

    # Generate glob patterns
    glob_patterns = generate_glob_patterns(rule_name)

    # Create prompt for the LLM
    system_message = f"""You are an expert rule architect specializing in creating documentation rules 
for AI assistants. You translate documentation standards into actionable rules
that guide AI behavior. Follow these rule generation guidelines carefully:

{rule_generation_content}

Focus specifically on creating a high-quality rule for documentation standards
that an AI can use to guide its behavior when helping with documentation tasks.
"""

    has_children_text = (
        "Yes (this is a parent rule with child rules to reference)"
        if extracted_content.get("has_children", False)
        else "No (this is a leaf rule with no children)"
    )
    child_guidance_text = (
        "References child rules appropriately"
        if extracted_content.get("has_children", False)
        else "Provides detailed guidance for implementation"
    )

    user_message = f"""# Documentation Rule Generation Request

## Rule Information
- Rule ID: {rule_id}
- Rule Name: {rule_name}
- Category: {category}
- Parent Rule ID: {parent_id if parent_id else "None (this is a top-level rule)"}
- Has Child Rules: {has_children_text}

## Documentation Context
The following content was extracted from documentation standards files:

```json
{doc_context}
```

## Task
Create a comprehensive rule that:
1. Follows the rule generation standards provided in the system message
2. Incorporates the documentation standards from the context
3. Uses proper "MUST", "SHOULD", "NEVER" statements for clarity
4. Includes clear examples and danger sections
5. {child_guidance_text}

## Output Format
Return a complete rule in JSON format with the following structure:
{{
  "rule_name": "Documentation Standard Name",
  "overview": {{ ... }},
  "requirements": {{ ... }},
  "examples": [ ... ],
  "danger": {{ ... }}
  // Additional sections as appropriate
}}
"""

    # Call OpenAI with retries
    try:
        # We need to implement a special version of _call_openai_with_retries because
        # the one from section_generator.py expects a specific JSON format,
        # but we want a more flexible response for complete rules
        max_retries = 3
        llm_response = None

        # Try up to max_retries times
        for attempt in range(max_retries):
            try:
                # Make the API call
                logger.debug(f"Sending request to OpenAI API for rule {rule_id}:")
                logger.debug(f"System message: {system_message[:200]}...")
                logger.debug(f"User message: {user_message[:200]}...")

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},  # Explicitly request JSON
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                )

                # Extract the response content
                llm_response = response.choices[0].message.content
                logger.debug(f"Received response from OpenAI API for rule {rule_id}:")
                logger.debug(f"Response (first 200 chars): {llm_response[:200]}...")

                # Try to parse as JSON
                try:
                    rule_content = json.loads(llm_response)
                    logger.info(f"Successfully generated rule {rule_id} with LLM")
                    break
                except json.JSONDecodeError:
                    # If not valid JSON, clean it up and try again
                    logger.warning(
                        f"LLM response for rule {rule_id} was not valid JSON, attempting to clean up"
                    )
                    # Try to extract JSON content if it's wrapped in backticks
                    if "```json" in llm_response and "```" in llm_response:
                        json_content = (
                            llm_response.split("```json")[1].split("```")[0].strip()
                        )
                        try:
                            rule_content = json.loads(json_content)
                            logger.info(
                                f"Successfully extracted JSON content from LLM response for rule {rule_id}"
                            )
                            break
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Could not extract valid JSON from LLM response on attempt {attempt+1}"
                            )

                    if attempt == max_retries - 1:
                        raise ValueError(
                            f"LLM response was not valid JSON after {max_retries} attempts"
                        )

            except Exception as e:
                logger.warning(
                    f"Error in LLM call for rule {rule_id}, attempt {attempt+1}/{max_retries}: {str(e)}"
                )
                # Special handling for "expected string or bytes-like object, got 'list'" error
                if "expected string" in str(e) and "got 'list'" in str(e):
                    logger.info(
                        "Detected list instead of string error, attempting to convert response"
                    )
                    try:
                        # If we have a list, try to convert it to a string
                        if isinstance(llm_response, (dict, list)):
                            rule_content = llm_response  # Use the list/dict directly
                            logger.info(
                                f"Successfully converted list/dict response for rule {rule_id}"
                            )
                            break
                    except Exception as inner_e:
                        logger.warning(
                            f"Failed to convert list response: {str(inner_e)}"
                        )

                if attempt == max_retries - 1:
                    raise
                time.sleep(2)  # Add a short delay before retrying

        # Generate rule description from content or use provided one
        description = extracted_content.get(
            "description",
            generate_rule_description(rule_type=rule_name, content=rule_content),
        )

        # Build the rule file
        rule_file_path, full_content = build_rule_file(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            description=description,
            glob_patterns=glob_patterns,
            content=rule_content,
        )

        return {
            "file_path": rule_file_path,
            "content": rule_content,
            "full_content": full_content,
            "line_count": len(full_content.splitlines()),
        }
    except Exception as e:
        logger.error(f"Error generating rule with LLM: {str(e)}")

        # Fallback to direct extraction if LLM fails
        logger.info(f"Falling back to direct extraction for rule {rule_id}")

        # Transform to rule format directly from extracted content
        rule_content = transform_to_rule_content(
            extracted_content=extracted_content, rule_type=rule_name
        )

        # Generate rule description
        description = generate_rule_description(
            rule_type=rule_name, content=rule_content
        )

        # Build the rule file
        rule_file_path, full_content = build_rule_file(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            description=description,
            glob_patterns=glob_patterns,
            content=rule_content,
        )

        return {
            "file_path": rule_file_path,
            "content": rule_content,
            "full_content": full_content,
            "line_count": len(full_content.splitlines()),
        }


def build_rule_file(
    rule_id: str,
    rule_name: str,
    category: str,
    description: str,
    glob_patterns: List[str],
    content: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Build the rule file with frontmatter and content.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        category: Category of the rule
        description: WHEN/TO/MUST description
        glob_patterns: List of glob patterns for the rule
        content: Rule content structure

    Returns:
        Tuple of (path to the generated rule file, full file content as string)
    """
    # Ensure the rules directory exists
    rules_dir = Path(".cursor/rules")
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Check if this is a child rule
    parent_rule_id = content.get("parent_rule")

    if parent_rule_id:
        # Find the parent rule file to get its full name
        parent_files = list(rules_dir.glob(f"{parent_rule_id}-*.mdc"))

        if parent_files:
            parent_file = parent_files[0]
            parent_rule_filename = (
                parent_file.stem
            )  # Get the filename without extension

            # Create subdirectory for child rules if it doesn't exist
            # The directory should be named exactly like the parent rule file (without .mdc extension)
            parent_subdir = rules_dir / parent_rule_filename
            parent_subdir.mkdir(parents=True, exist_ok=True)

            # Convert dot notation in ID to hyphen format for filename
            filename_id = rule_id.replace(".", "-")

            # Place the child rule in the parent's subdirectory
            rule_file_path = parent_subdir / f"{filename_id}-{rule_name}.mdc"
            logger.info(
                f"Placing child rule {rule_id} in parent directory {parent_subdir}"
            )
        else:
            # Parent not found yet, place in main rules directory temporarily
            # It will be moved later by create_parent_child_relationships
            # Convert dot notation in ID to hyphen format for filename
            filename_id = rule_id.replace(".", "-")
            rule_file_path = rules_dir / f"{filename_id}-{rule_name}.mdc"
            logger.warning(
                f"Parent rule {parent_rule_id} not found, placing child rule in main directory temporarily"
            )
    else:
        # This is a parent rule, place in main rules directory
        rule_file_path = rules_dir / f"{rule_id}-{rule_name}.mdc"

    # Build the frontmatter
    frontmatter = f"""---
description: {description}
globs: {json.dumps(glob_patterns)}
---
"""

    # Format the content as JSON
    formatted_content = json.dumps(content, indent=2)
    full_content = frontmatter + formatted_content

    # Write the rule file
    with open(rule_file_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    logger.info(f"Generated rule file: {rule_file_path}")
    return str(rule_file_path), full_content


def create_parent_child_relationships(
    parent_rule_id: str,
    child_rules: List[Dict[str, Any]],
    rules_dir: str = ".cursor/rules",
) -> None:
    """
    Update parent rule to include references to child rules and organize child rules into subdirectories.

    Args:
        parent_rule_id: ID of the parent rule
        child_rules: List of child rule information with file_path, content, and line_count
        rules_dir: Directory containing rule files
    """
    # Find the parent rule file
    parent_files = list(Path(rules_dir).glob(f"{parent_rule_id}-*.mdc"))
    if not parent_files:
        logger.error(f"Parent rule file not found: {parent_rule_id}")
        return

    parent_file = parent_files[0]
    parent_rule_filename = parent_file.stem  # Get the filename without extension

    # Create subdirectory for child rules - use exact parent filename (without .mdc extension)
    parent_subdir = Path(rules_dir) / parent_rule_filename
    parent_subdir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Created parent directory: {parent_subdir}")

    # Process each child rule
    child_rule_references = []
    for child in child_rules:
        child_id = child.get("rule_id", child.get("id"))
        child_name = child.get("name")
        child_path = child.get("file_path")
        child_line_count = child.get("line_count", 0)

        if not child_id or not child_path:
            logger.warning(
                f"Incomplete child rule data: id={child_id}, path={child_path}"
            )
            continue

        # If name is still missing, extract it from the file path
        if not child_name and child_path:
            filename = os.path.basename(child_path)
            filename_no_ext = os.path.splitext(filename)[0]
            parts = filename_no_ext.split("-", 1)
            if len(parts) > 1:
                child_name = parts[1]
            else:
                child_name = filename_no_ext

        logger.info(
            f"Processing child rule: id={child_id}, name={child_name}, path={child_path}"
        )

        # Convert string path to Path object
        child_file = Path(child_path)

        if child_file.exists():
            # Format filename properly - handle both dot and hyphen formats
            # Clean up the ID format for filename (replacing dots with hyphens)
            if "." in child_id:
                # This is using dot notation (e.g., 301.01)
                filename_id = child_id.replace(".", "-")
            else:
                # This is already using hyphen notation
                filename_id = child_id

            # Determine if this is a grandchild rule by counting dots in the ID
            is_grandchild = (
                (child_id.count(".") >= 2)
                if "." in child_id
                else ("-" in child_id and child_id.count("-") >= 2)
            )

            child_subdir_file = None

            if is_grandchild and "." in child_id:
                # This is a grandchild rule - parse the rule_id to get parent and grandparent parts
                id_parts = child_id.split(".")

                # Construct the parent's rule ID (first two parts)
                parent_of_child_id = ".".join(id_parts[0:2])
                parent_of_child_filename = parent_of_child_id.replace(".", "-")

                # Find the parent rule name and create correct directory path
                parent_of_child_name = None
                for potential_parent in child_rules:
                    potential_parent_id = potential_parent.get(
                        "rule_id", potential_parent.get("id")
                    )
                    if potential_parent_id == parent_of_child_id:
                        parent_of_child_name = potential_parent.get("name")
                        break

                if parent_of_child_name:
                    # Create the parent directory path using correct formatting
                    parent_dir_name = (
                        f"{parent_of_child_filename}-{parent_of_child_name}"
                    )

                    # Create nested directory structure: parent/child_parent
                    nested_dir = parent_subdir / parent_dir_name
                    nested_dir.mkdir(parents=True, exist_ok=True)

                    # Create proper filename for the grandchild in the nested directory
                    # Extract the last part of the ID after the last dot
                    last_id_part = id_parts[-1]
                    grandchild_filename = (
                        f"{parent_of_child_filename}-{last_id_part}-{child_name}.mdc"
                    )

                    child_subdir_file = nested_dir / grandchild_filename
                    logger.info(
                        f"Placing grandchild rule {child_id} in nested directory {nested_dir}"
                    )
                else:
                    # If we couldn't find the parent, place directly in the parent directory
                    child_subdir_file = (
                        parent_subdir / f"{filename_id}-{child_name}.mdc"
                    )
                    logger.warning(
                        f"Could not find parent for grandchild rule {child_id}, placing in parent directory"
                    )
            else:
                # Regular child rule - place in parent subdirectory
                # For child rule, format filename as parent-id-childname.mdc
                # Extract the last part of the ID after the last dot or hyphen
                if "." in child_id:
                    id_parts = child_id.split(".")
                    last_id_part = id_parts[-1]
                    child_subdir_file = (
                        parent_subdir / f"{filename_id}-{child_name}.mdc"
                    )
                else:
                    # Handle hyphenated IDs
                    child_subdir_file = (
                        parent_subdir / f"{filename_id}-{child_name}.mdc"
                    )

                logger.info(
                    f"Placing child rule {child_id} in parent directory {parent_subdir}"
                )

            # Move the child file to the appropriate subdirectory
            if child_subdir_file and str(child_file) != str(child_subdir_file):
                try:
                    # Get exact line count from file if not provided
                    if child_line_count <= 0:
                        with open(child_file, "r", encoding="utf-8") as f:
                            child_content = f.read()
                            child_line_count = len(child_content.splitlines())

                    # Check if child rule exceeds 250 lines
                    if child_line_count > 250:
                        logger.warning(
                            f"Child rule {child_id} exceeds 250 lines ({child_line_count}). Consider splitting it."
                        )

                    # Make sure parent directory exists first
                    child_subdir_file.parent.mkdir(parents=True, exist_ok=True)

                    # Read content from original file
                    with open(child_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Write to new location
                    with open(child_subdir_file, "w", encoding="utf-8") as f:
                        f.write(content)

                    # Only remove original file if copy was successful
                    if child_subdir_file.exists():
                        child_file.unlink()
                        logger.info(
                            f"Successfully moved child rule {child_id} to {child_subdir_file}"
                        )
                    else:
                        logger.error(f"Failed to create {child_subdir_file}")

                except Exception as e:
                    logger.error(f"Error moving child rule {child_id}: {str(e)}")
                    # Still try to include in references even if move failed

                # Update the file path to reflect the new location
                child_path = str(child_subdir_file)

            # Add reference to the child rule with line count
            relative_path = Path(child_path).relative_to(Path(rules_dir).parent)
            child_rule_references.append(
                {
                    "id": child_id,
                    "name": child_name,
                    "line_count": child_line_count,
                    "path": str(relative_path),
                }
            )
        else:
            logger.warning(f"Child rule file not found: {child_path}")

    # Update the parent rule content with proper read_file references
    with open(parent_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract the frontmatter and JSON content
    parts = content.split("---", 2)
    if len(parts) < 3:
        logger.error(f"Invalid rule file format: {parent_file}")
        return

    frontmatter = parts[1]
    json_content = parts[2].strip()

    try:
        # Parse the JSON content
        rule_content = json.loads(json_content)

        # Add rule_selection section if it doesn't exist
        if "rule_selection" not in rule_content:
            rule_content["rule_selection"] = {
                "description": "Select the appropriate rule based on your current task:",
                "contexts": {},
            }
        elif "contexts" not in rule_content["rule_selection"]:
            rule_content["rule_selection"]["contexts"] = {}

        # Add line_count_metadata section if it doesn't exist
        if "line_count_metadata" not in rule_content:
            rule_content["line_count_metadata"] = {"rules": []}

        # Add fetch_read_mapping section if it doesn't exist
        if "fetch_read_mapping" not in rule_content:
            rule_content["fetch_read_mapping"] = {
                "table": "| Rule Reference | Access Method |\n|----|----|\n"
            }

        # Clear existing sections to rebuild them
        rule_content["line_count_metadata"]["rules"] = []

        # Create a fresh table header for fetch_read_mapping
        rule_content["fetch_read_mapping"][
            "table"
        ] = "| Rule Reference | Access Method |\n|----|----|\n"

        # Add parent rule to fetch_read_mapping
        parent_mapping_entry = (
            f'| {parent_rule_id} | `fetch_rules(["{parent_rule_id}"])` |'
        )
        rule_content["fetch_read_mapping"]["table"] += parent_mapping_entry + "\n"

        # Add each child rule reference
        contexts = {}
        for child in child_rule_references:
            # Add to line_count_metadata
            # Use the original ID (with dots) for display
            rule_content["line_count_metadata"]["rules"].append(
                f"`{child['id']}-{child['name']}.mdc` - {child['line_count']} lines"
            )

            # Add to fetch_read_mapping table
            read_file_cmd = f"read_file(\"{child['path']}\", should_read_entire_file=false, start_line_one_indexed=1, end_line_one_indexed_inclusive={child['line_count']})"
            mapping_entry = f"| {child['id']} | `{read_file_cmd}` |"
            rule_content["fetch_read_mapping"]["table"] += mapping_entry + "\n"

            # Format for rule_selection section
            child_key = f"{child['name'].replace('-', '_')}"

            # Try to extract or create a clearer description for the child rule
            # The description should follow the WHEN/TO/MUST format and include THESE
            child_description = f"WHEN working with {child['name'].replace('-', ' ')} TO ensure quality you MUST follow THESE {child['name'].replace('-', ' ')} guidelines"

            # Create the context entry for rule_selection
            contexts[child_key] = {
                "description": child_description,
                "command": f"read_file(\"{child['path']}\", should_read_entire_file=false, start_line_one_indexed=1, end_line_one_indexed_inclusive={child['line_count']})",
            }

        # Replace the rule_selection section with the new contexts
        rule_content["rule_selection"]["contexts"] = contexts

        # Write the updated content back to the file
        with open(parent_file, "w", encoding="utf-8") as f:
            f.write("---")
            f.write(frontmatter)
            f.write("---\n")
            f.write(json.dumps(rule_content, indent=2))

        logger.info(
            f"Updated parent rule {parent_rule_id} with references to {len(child_rule_references)} child rules"
        )

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON content in {parent_file}: {str(e)}")


def generate_rules_from_taxonomy(
    taxonomy_file: str,
    doc_dir: str,
    output_dir: str = ".cursor/rules",
    max_workers: int = 4,
) -> List[Dict[str, Any]]:
    """
    Generate documentation rules from a taxonomy file.

    Args:
        taxonomy_file: Path to the taxonomy file
        doc_dir: Base directory for documentation files
        output_dir: Directory to write the generated rules to
        max_workers: Maximum number of parallel workers

    Returns:
        List of results for generated rules
    """
    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load the taxonomy
    try:
        with open(taxonomy_file, "r", encoding="utf-8") as f:
            # Use YAML instead of JSON for loading the taxonomy
            taxonomy = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading taxonomy file: {str(e)}")
        return [{"error": f"Error loading taxonomy file: {str(e)}"}]

    results = []
    parent_rule_cache = {}  # Cache to track parent rules that have been generated

    # Define a worker function for parallel rule generation
    def _generate_rule_worker(rule_data):
        try:
            rule_id = rule_data.get("id", "")
            rule_name = rule_data.get("name", "")
            doc_paths = rule_data.get("source_files", [])
            parent_id = rule_data.get("parent_id")
            category_name = rule_data.get("category", "Documentation")

            # Skip rules without source files
            if not doc_paths:
                logger.warning(
                    f"No source files specified for rule {rule_id}: {rule_name}"
                )
                return {
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "status": "skipped",
                    "reason": "No source files",
                }

            # Generate the rule
            result = generate_doc_rule(
                rule_id=rule_id,
                rule_name=rule_name,
                doc_paths=doc_paths,
                category=category_name,
                doc_dir=doc_dir,
                parent_id=parent_id,
            )

            if "error" in result:
                return {
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "status": "error",
                    "error": result["error"],
                }

            # Add rule data to result
            result["rule_id"] = rule_id
            result["rule_name"] = rule_name
            result["status"] = "success"
            result["description"] = rule_data.get("description", "")
            result["parent_id"] = parent_id

            # If this rule has children, store it in the cache
            if "child_rules" in rule_data:
                child_ids = [
                    child.get("id") for child in rule_data.get("child_rules", [])
                ]
                parent_rule_cache[rule_id] = {
                    "file_path": result["file_path"],
                    "child_ids": child_ids,
                    "child_rules": [],  # Will be populated later
                }

            return result
        except Exception as e:
            logger.error(f"Error generating rule {rule_data.get('id')}: {str(e)}")
            return {
                "rule_id": rule_data.get("id", "unknown"),
                "rule_name": rule_data.get("name", "unknown"),
                "status": "error",
                "error": str(e),
            }

    # Three-pass approach: generate parent rules, then child rules, then grandchild rules
    logger.info(
        "Step 1: Generating parent rules with placeholders for child rule references"
    )

    # Process each category
    for category in taxonomy.get("categories", []):
        category_name = category.get("name", "Unknown")
        logger.info(f"Processing category: {category_name}")

        # First pass: Generate all parent rules
        parent_rules = []
        for rule in category.get("rules", []):
            if not rule.get("parent_id"):  # Only top-level rules
                # Add category to rule data
                rule_data = rule.copy()
                rule_data["category"] = category_name
                parent_rules.append(rule_data)

        # Use parallel processing for parent rules if there's more than one
        if len(parent_rules) > 1 and max_workers > 1:
            with ThreadPoolExecutor(
                max_workers=min(max_workers, len(parent_rules))
            ) as executor:
                parent_results = list(executor.map(_generate_rule_worker, parent_rules))
                results.extend(parent_results)

            logger.info(f"Generated {len(parent_results)} parent rules in parallel")
        else:
            # Process parent rules sequentially if only one or parallel disabled
            for rule_data in parent_rules:
                result = _generate_rule_worker(rule_data)
                results.append(result)

            logger.info(f"Generated {len(parent_rules)} parent rules sequentially")

    logger.info("Step 2: Generating child rules")

    # Second pass: Generate all child rules (first level of nesting)
    child_rules_by_parent = {}
    for category in taxonomy.get("categories", []):
        category_name = category.get("name", "Unknown")

        for parent_rule in category.get("rules", []):
            parent_id = parent_rule.get("id")

            # Skip if not a parent rule or doesn't have children
            if not parent_id or "child_rules" not in parent_rule:
                continue

            # Collect all children for this parent
            children = []
            for child_rule in parent_rule.get("child_rules", []):
                child_data = child_rule.copy()
                child_data["parent_id"] = parent_id
                child_data["category"] = category_name
                children.append(child_data)

            if children:
                if parent_id not in child_rules_by_parent:
                    child_rules_by_parent[parent_id] = []
                child_rules_by_parent[parent_id].extend(children)

    # Process children for each parent
    for parent_id, children in child_rules_by_parent.items():
        logger.info(f"Generating {len(children)} child rules for parent {parent_id}")

        # Use parallel processing for children if there's more than one
        if len(children) > 1 and max_workers > 1:
            with ThreadPoolExecutor(
                max_workers=min(max_workers, len(children))
            ) as executor:
                child_results = list(executor.map(_generate_rule_worker, children))

                # Store successful results for parent-child relationship updates
                successful_children = []
                for result in child_results:
                    results.append(result)
                    if result.get("status") == "success":
                        successful_children.append(result)

                # Update parent-child relationships if we have the parent in cache
                if parent_id in parent_rule_cache and successful_children:
                    parent_rule_cache[parent_id]["child_rules"] = successful_children
                    create_parent_child_relationships(
                        parent_rule_id=parent_id,
                        child_rules=successful_children,
                        rules_dir=output_dir,
                    )
                    logger.info(
                        f"Updated parent rule {parent_id} with references to {len(successful_children)} child rules"
                    )
        else:
            # Process children sequentially
            successful_children = []
            for child_data in children:
                result = _generate_rule_worker(child_data)
                results.append(result)
                if result.get("status") == "success":
                    successful_children.append(result)

            # Update parent-child relationships
            if parent_id in parent_rule_cache and successful_children:
                parent_rule_cache[parent_id]["child_rules"] = successful_children
                create_parent_child_relationships(
                    parent_rule_id=parent_id,
                    child_rules=successful_children,
                    rules_dir=output_dir,
                )
                logger.info(
                    f"Updated parent rule {parent_id} with references to {len(successful_children)} child rules"
                )

    logger.info("Step 3: Generating grandchild rules")

    # Third pass: Generate all grandchild rules
    grandchild_rules_by_parent = {}
    for category in taxonomy.get("categories", []):
        category_name = category.get("name", "Unknown")

        # Recursively find all grandchildren in the taxonomy
        for parent_rule in category.get("rules", []):
            for child_rule in parent_rule.get("child_rules", []):
                child_id = child_rule.get("id")

                # Skip if not a parent rule or doesn't have children
                if not child_id or "child_rules" not in child_rule:
                    continue

                # Collect all grandchildren for this child
                grandchildren = []
                for grandchild_rule in child_rule.get("child_rules", []):
                    grandchild_data = grandchild_rule.copy()
                    grandchild_data["parent_id"] = child_id
                    grandchild_data["category"] = category_name
                    grandchildren.append(grandchild_data)

                if grandchildren:
                    if child_id not in grandchild_rules_by_parent:
                        grandchild_rules_by_parent[child_id] = []
                    grandchild_rules_by_parent[child_id].extend(grandchildren)

    # Process grandchildren for each parent
    for parent_id, grandchildren in grandchild_rules_by_parent.items():
        logger.info(
            f"Generating {len(grandchildren)} grandchild rules for parent {parent_id}"
        )

        # Use parallel processing for grandchildren if there's more than one
        if len(grandchildren) > 1 and max_workers > 1:
            with ThreadPoolExecutor(
                max_workers=min(max_workers, len(grandchildren))
            ) as executor:
                grandchild_results = list(
                    executor.map(_generate_rule_worker, grandchildren)
                )

                # Store successful results for parent-child relationship updates
                successful_grandchildren = []
                for result in grandchild_results:
                    results.append(result)
                    if result.get("status") == "success":
                        successful_grandchildren.append(result)

                # Update parent-child relationships
                if successful_grandchildren:
                    create_parent_child_relationships(
                        parent_rule_id=parent_id,
                        child_rules=successful_grandchildren,
                        rules_dir=output_dir,
                    )
                    logger.info(
                        f"Updated child rule {parent_id} with references to {len(successful_grandchildren)} grandchild rules"
                    )
        else:
            # Process grandchildren sequentially
            successful_grandchildren = []
            for grandchild_data in grandchildren:
                result = _generate_rule_worker(grandchild_data)
                results.append(result)
                if result.get("status") == "success":
                    successful_grandchildren.append(result)

            # Update parent-child relationships
            if successful_grandchildren:
                create_parent_child_relationships(
                    parent_rule_id=parent_id,
                    child_rules=successful_grandchildren,
                    rules_dir=output_dir,
                )
                logger.info(
                    f"Updated child rule {parent_id} with references to {len(successful_grandchildren)} grandchild rules"
                )

    # Generate summary statistics
    total_rules = len(results)
    successful_rules = sum(1 for result in results if result.get("status") == "success")

    logger.info(f"Generated {successful_rules} of {total_rules} rules successfully")
    logger.info(
        f"Created {len(parent_rule_cache)} parent rules and {successful_rules - len(parent_rule_cache)} child rules"
    )

    return results
