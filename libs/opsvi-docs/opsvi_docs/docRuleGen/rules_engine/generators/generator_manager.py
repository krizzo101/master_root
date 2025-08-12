# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Generator Manager Module","description":"This module provides functionality to generate rule files from transformed content.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for logging, file handling, and template rendering.","line_start":3,"line_end":12},{"name":"GeneratorManager Class","description":"Class that manages the generation of rule files from transformed content.","line_start":14,"line_end":103},{"name":"generate Method","description":"Method to generate a rule file from transformed content.","line_start":60,"line_end":103}],"key_elements":[{"name":"GeneratorManager","description":"Class responsible for managing rule file generation.","line":16},{"name":"__init__","description":"Constructor for initializing the GeneratorManager class.","line":19},{"name":"generate","description":"Method for generating rule files from transformed content.","line":60},{"name":"logger","description":"Logger instance for logging information and errors.","line":13}]}
"""
# FILE_MAP_END

"""
Generator Manager Module.

This module provides functionality to generate rule files from transformed content.
"""

import os
import logging
import jinja2
import re
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GeneratorManager:
    """Manage the generation of rule files from transformed content."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the generator manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Initialize Jinja2 environment with absolute path
        template_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "config",
            "templates",
        )
        logger.info(f"Using template directory: {template_dir}")

        # Ensure the template directory exists
        if not os.path.exists(template_dir):
            logger.warning(f"Template directory not found: {template_dir}")
            # Try alternative path
            alt_template_dir = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ),
                "docRuleGen",
                "config",
                "templates",
            )
            if os.path.exists(alt_template_dir):
                logger.info(f"Using alternative template directory: {alt_template_dir}")
                template_dir = alt_template_dir

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.jinja_env.filters["tojson"] = lambda obj: jinja2.utils.htmlsafe_json_dumps(
            obj
        )

    def generate(
        self, transformed_content: Dict[str, Any], output_path: str
    ) -> Dict[str, Any]:
        """
        Generate a rule file from transformed content.

        Args:
            transformed_content: Transformed content to generate rule from
            output_path: Path to save the generated rule

        Returns:
            Dictionary with generation result
        """
        logger.info(f"Generating rule file at {output_path}")

        # Debug log to show what we're working with
        if isinstance(transformed_content, dict):
            logger.debug(
                f"Transformed content keys: {list(transformed_content.keys())}"
            )
        else:
            logger.error(
                f"Transformed content is not a dictionary: {type(transformed_content)}"
            )
            return {
                "status": "error",
                "message": "Transformed content must be a dictionary",
            }

        if transformed_content.get("status") != "success":
            logger.error("Cannot generate rule from content with error status")
            return {
                "status": "error",
                "message": "Cannot generate rule from content with error status",
            }

        try:
            # Check if content is already in the right format or needs processing
            content = transformed_content.get("content", {})

            # Handle cases where content might be a string, dict, or list
            rule_data = None
            if isinstance(content, str):
                # Try to parse as JSON if it's a string
                try:
                    rule_data = json.loads(content)
                    logger.info("Successfully parsed string content as JSON")
                except json.JSONDecodeError:
                    logger.warning(
                        "Content is a string but not valid JSON, treating as raw content"
                    )
                    rule_data = {"raw_content": content}
            elif isinstance(content, (dict, list)):
                # Content is already a dict or list, use directly
                rule_data = content
                logger.info("Using dict/list content directly")
            else:
                # Use the transformed content itself if no specific content field
                rule_data = transformed_content
                logger.info(
                    "No specific content field found, using transformed_content directly"
                )

            # Determine the rule type
            rule_type = transformed_content.get("metadata", {}).get("type", "parent")

            # Select the appropriate template
            template_name = f"{rule_type}_rule.md.jinja2"
            try:
                template = self.jinja_env.get_template(template_name)
            except jinja2.exceptions.TemplateNotFound:
                # Fallback to parent_rule.md.jinja2 if the specific template is not found
                logger.warning(
                    f"Template '{template_name}' not found, falling back to parent_rule.md.jinja2"
                )
                template = self.jinja_env.get_template("parent_rule.md.jinja2")

            # Get the metadata, ensuring it exists
            metadata = transformed_content.get("metadata", {})
            if not metadata:
                logger.warning(
                    "No metadata found in transformed content, using defaults"
                )
                metadata = {
                    "id": transformed_content.get("rule_id", "000"),
                    "name": transformed_content.get("rule_name", "untitled-rule"),
                    "type": rule_type,
                    "title": transformed_content.get("title", "Untitled Rule"),
                    "description": transformed_content.get("description", ""),
                }

            # Ensure metadata has descriptions that include directives if possible
            if "description" not in metadata and transformed_content.get(
                "directive_candidates"
            ):
                directives = transformed_content.get("directive_candidates", [])
                for directive in directives:
                    if "when_context" in directive and "to_purpose" in directive:
                        when_ctx = directive.get("when_context", "")
                        to_purpose = directive.get("to_purpose", "")
                        strength = directive.get("strength", "MUST")
                        directive_text = directive.get(
                            "directive", "follow these guidelines"
                        )
                        metadata[
                            "description"
                        ] = f"WHEN {when_ctx} TO {to_purpose} {strength} {directive_text}"
                        break

            # If we have rule_content but not overview, context, etc., try to extract them
            rule_content = transformed_content.get("rule_content", "")
            if rule_content and isinstance(rule_content, str):
                logger.debug("Found rule_content, extracting sections for template")

                # Only process if we don't already have these sections
                if not transformed_content.get("overview"):
                    # Simple extraction of sections from rule_content
                    overview_match = re.search(
                        r"## Overview\s+(.*?)(?=##|\Z)", rule_content, re.DOTALL
                    )
                    if overview_match:
                        transformed_content["overview"] = overview_match.group(
                            1
                        ).strip()

                if not transformed_content.get("context"):
                    context_match = re.search(
                        r"## Context\s+(.*?)(?=##|\Z)", rule_content, re.DOTALL
                    )
                    if context_match:
                        transformed_content["context"] = context_match.group(1).strip()

                if not transformed_content.get("requirements"):
                    requirements_match = re.search(
                        r"## Requirements\s+(.*?)(?=##|\Z)", rule_content, re.DOTALL
                    )
                    if requirements_match:
                        transformed_content["requirements"] = requirements_match.group(
                            1
                        ).strip()

            # Render the template with the content
            rule_content = template.render(
                rule=rule_data, metadata=metadata, content=transformed_content
            )

            # Determine the output file path
            rule_id = metadata.get("id", "000")
            rule_name = metadata.get("name", "unnamed").lower().replace(" ", "-")
            filename = f"{rule_id}-{rule_name}.mdc"
            file_path = os.path.join(output_path, filename)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write the rule file
            with open(file_path, "w") as f:
                f.write(rule_content)

            logger.info(f"Generated rule file: {file_path}")

            return {"status": "success", "path": file_path, "content": rule_data}

        except Exception as e:
            logger.error(f"Error generating rule file: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating rule file: {str(e)}",
            }
