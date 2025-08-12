# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Documentation Extractor Module","description":"Module for extracting content from documentation standards files and preparing it for conversion to rule format","last_updated":"2023-03-10","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":1,"line_end":18},{"name":"Configure Logging","description":"Logging configuration for the module","line_start":19,"line_end":22},{"name":"Extract Documentation for Rule","description":"Main function to extract content for a specific rule","line_start":23,"line_end":77},{"name":"Combine Sections","description":"Function to combine sections from multiple sources","line_start":78,"line_end":121},{"name":"Generate Glob Patterns","description":"Function to generate glob patterns for documentation files","line_start":122,"line_end":173},{"name":"Extract Documentation for Taxonomy","description":"Function to extract content for all rules in a taxonomy","line_start":174,"line_end":288}],"key_elements":[{"name":"extract_documentation_for_rule","description":"Main extraction function for a single rule","line":23},{"name":"combine_sections","description":"Helper to combine content from multiple sources","line":78},{"name":"generate_glob_patterns","description":"Helper to generate file patterns","line":122},{"name":"extract_documentation_for_taxonomy","description":"Function to process entire taxonomy","line":174}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Documentation Extractor Module","description":"Module for extracting content from documentation standards files and preparing it for conversion to rule format","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":1,"line_end":18},
# {"name":"Extract Documentation for Rule","description":"Main function to extract content for a specific rule","line_start":21,"line_end":77},
# {"name":"Combine Sections","description":"Function to combine sections from multiple sources","line_start":80,"line_end":121},
# {"name":"Generate Glob Patterns","description":"Function to generate glob patterns for documentation files","line_start":124,"line_end":173},
# {"name":"Extract Documentation for Taxonomy","description":"Function to extract content for all rules in a taxonomy","line_start":176,"line_end":288}
# ],
# "key_elements":[
# {"name":"extract_documentation_for_rule","description":"Main extraction function for a single rule","line":21},
# {"name":"combine_sections","description":"Helper to combine content from multiple sources","line":80},
# {"name":"generate_glob_patterns","description":"Helper to generate file patterns","line":124},
# {"name":"extract_documentation_for_taxonomy","description":"Function to process entire taxonomy","line":176}
# ]
# }
# FILE_MAP_END

"""
Documentation Extractor Module for Documentation Rule Generator.

This module orchestrates the extraction of content from documentation standards files
and prepares them for conversion to rule format.
"""

import os
import glob
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .markdown_parser import parse_markdown_file
from .section_extractor import extract_rule_sections

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_documentation_for_rule(
    rule_id: str, rule_name: str, source_files: List[str], doc_dir: str
) -> Dict[str, Any]:
    """
    Extract documentation content for a specific rule.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        source_files: List of source file paths (relative to doc_dir)
        doc_dir: Base directory for documentation files

    Returns:
        Extracted content structured for rule generation
    """
    logger.info(f"Extracting documentation for rule {rule_id}: {rule_name}")

    # Normalize paths
    doc_dir_path = Path(doc_dir)
    if not doc_dir_path.exists():
        logger.error(f"Documentation directory not found: {doc_dir}")
        return {"error": f"Documentation directory not found: {doc_dir}"}

    # Process each source file
    extracted_content = {"rule_id": rule_id, "rule_name": rule_name, "sources": []}

    combined_sections = {
        "overview": {"purpose": "", "application": "", "importance": ""},
        "requirements": [],
        "examples": [],
        "danger": {"critical_violations": [], "specific_risks": []},
    }

    for source_file in source_files:
        # Improved path resolution to avoid double-prepending doc_dir
        if os.path.isabs(source_file):
            source_path = Path(source_file)
        else:
            # Handle relative paths correctly
            source_path = doc_dir_path / source_file

        # Check if the file exists at the constructed path
        if not source_path.exists():
            # Try alternate path formats
            alt_path = Path(doc_dir) / Path(source_file).name
            if alt_path.exists():
                source_path = alt_path
                logger.info(f"Using alternate path: {source_path}")
            else:
                logger.warning(f"Source file not found: {source_path}")
                continue

        # Extract sections from this source file
        logger.info(f"Processing source file: {source_path}")
        sections = extract_rule_sections(str(source_path), rule_name)

        if "error" in sections:
            logger.error(f"Error extracting from {source_path}: {sections['error']}")
            continue

        # Add to the sources list
        extracted_content["sources"].append(
            {"file": str(source_path), "title": sections["_source"]["title"]}
        )

        # Combine sections
        combine_sections(combined_sections, sections)

    # Add the combined sections
    extracted_content.update(combined_sections)

    # If we didn't find any content, report an error
    if not extracted_content["sources"]:
        logger.error(f"No valid source files found for rule {rule_id}")
        return {"error": f"No valid source files found for rule {rule_id}"}

    return extracted_content


def combine_sections(combined: Dict[str, Any], new_sections: Dict[str, Any]) -> None:
    """
    Combine new sections into the combined sections dictionary.

    Args:
        combined: The combined sections dictionary to update
        new_sections: New sections to add
    """
    # Handle overview sections - use the first non-empty section found
    if "overview" in new_sections:
        overview = new_sections["overview"]
        if not combined["overview"]["purpose"] and overview.get("purpose"):
            combined["overview"]["purpose"] = overview["purpose"]
        if not combined["overview"]["application"] and overview.get("application"):
            combined["overview"]["application"] = overview["application"]
        if not combined["overview"]["importance"] and overview.get("importance"):
            combined["overview"]["importance"] = overview["importance"]

    # Append requirements
    if "requirements" in new_sections:
        combined["requirements"].extend(new_sections["requirements"])

    # Append examples
    if "examples" in new_sections:
        combined["examples"].extend(new_sections["examples"])

    # Combine danger statements
    if "danger" in new_sections:
        danger = new_sections["danger"]
        if "critical_violations" in danger:
            combined["danger"]["critical_violations"].extend(
                danger["critical_violations"]
            )
        if "specific_risks" in danger:
            combined["danger"]["specific_risks"].extend(danger["specific_risks"])

    # Add any specialized sections that might be present
    for key in ["principles", "structure", "templates", "workflow", "formatting"]:
        if key in new_sections and key not in combined:
            combined[key] = new_sections[key]


def generate_glob_patterns(rule_type: str) -> List[str]:
    """
    Generate glob patterns for a documentation rule type.

    Args:
        rule_type: Type of documentation rule

    Returns:
        List of glob patterns for matching documentation files
    """
    # Split the rule type into words
    words = rule_type.replace("-", " ").split()

    # Build patterns based on these words
    patterns = []

    # Add a documentation path pattern
    patterns.append("**/docs/**/*.md")

    # Add patterns based on rule type words
    for word in words:
        if len(word) > 3:  # Only use words with significant length
            patterns.append(f"**/*{word}*/**/*.md")
            patterns.append(f"**/*.{word}.*")
            patterns.append(f"**/*{word}*.*")

    # Add specific patterns based on rule type
    if "readme" in rule_type:
        patterns.append("**/README.md")
        patterns.append("**/*.md")
    elif "architecture" in rule_type:
        patterns.append("**/architecture/**/*.md")
        patterns.append("**/design/**/*.md")
    elif "technical" in rule_type:
        patterns.append("**/technical/**/*.md")
        patterns.append("**/spec/**/*.md")
    elif "implementation" in rule_type:
        patterns.append("**/implementation/**/*.md")
        patterns.append("**/dev/**/*.md")
    elif "user" in rule_type:
        patterns.append("**/user/**/*.md")
        patterns.append("**/guide/**/*.md")
        patterns.append("**/manual/**/*.md")
    elif "template" in rule_type:
        patterns.append("**/template/**/*.md")
        patterns.append("**/templates/**/*.md")
    elif "process" in rule_type:
        patterns.append("**/process/**/*.md")
        patterns.append("**/workflow/**/*.md")

    return patterns


def extract_documentation_for_taxonomy(
    taxonomy: Dict[str, Any], doc_dir: str
) -> Dict[str, Dict[str, Any]]:
    """
    Extract documentation content for all rules in a taxonomy.

    Args:
        taxonomy: Taxonomy dictionary
        doc_dir: Base directory for documentation files

    Returns:
        Dictionary mapping rule IDs to extracted content
    """
    logger.info(
        f"Extracting documentation for taxonomy: {taxonomy.get('taxonomy_name', 'Unknown')}"
    )

    extracted_content = {}

    # Process each category and rule
    for category in taxonomy.get("categories", []):
        category_name = category.get("name", "Unknown")
        logger.info(f"Processing category: {category_name}")

        for rule in category.get("rules", []):
            rule_id = rule.get("id", "")
            rule_name = rule.get("name", "")
            source_files = rule.get("source_files", [])

            # Skip rules without source files
            if not source_files:
                logger.warning(
                    f"No source files specified for rule {rule_id}: {rule_name}"
                )
                continue

            # Extract content for this rule
            rule_content = extract_documentation_for_rule(
                rule_id=rule_id,
                rule_name=rule_name,
                source_files=source_files,
                doc_dir=doc_dir,
            )

            extracted_content[rule_id] = rule_content

            # Process child rules if they exist
            for child_rule in rule.get("child_rules", []):
                child_id = child_rule.get("id", "")
                child_name = child_rule.get("name", "")
                child_sources = child_rule.get("source_files", [])

                # Skip child rules without source files
                if not child_sources:
                    logger.warning(
                        f"No source files specified for child rule {child_id}: {child_name}"
                    )
                    continue

                # Extract content for this child rule
                child_content = extract_documentation_for_rule(
                    rule_id=child_id,
                    rule_name=child_name,
                    source_files=child_sources,
                    doc_dir=doc_dir,
                )

                # Add parent rule reference
                child_content["parent_rule"] = rule_id

                extracted_content[child_id] = child_content

                # Process grandchild rules if they exist (limit to 3 levels)
                for grandchild_rule in child_rule.get("child_rules", []):
                    gc_id = grandchild_rule.get("id", "")
                    gc_name = grandchild_rule.get("name", "")
                    gc_sources = grandchild_rule.get("source_files", [])

                    # Skip grandchild rules without source files
                    if not gc_sources:
                        logger.warning(
                            f"No source files specified for grandchild rule {gc_id}: {gc_name}"
                        )
                        continue

                    # Extract content for this grandchild rule
                    gc_content = extract_documentation_for_rule(
                        rule_id=gc_id,
                        rule_name=gc_name,
                        source_files=gc_sources,
                        doc_dir=doc_dir,
                    )

                    # Add parent references
                    gc_content["parent_rule"] = child_id
                    gc_content["grandparent_rule"] = rule_id

                    extracted_content[gc_id] = gc_content

    logger.info(f"Extracted content for {len(extracted_content)} rules")
    return extracted_content
