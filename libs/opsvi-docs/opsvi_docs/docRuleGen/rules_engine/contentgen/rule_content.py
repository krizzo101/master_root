# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Rule Content Generator Module","description":"This module provides functions for generating rule content from documentation, including extracting relevant sections and transforming them to rule format.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Import necessary libraries and modules for the functionality of the rule content generator.","line_start":3,"line_end":21},{"name":"Logging Configuration","description":"Set up logging configuration for the module.","line_start":22,"line_end":23},{"name":"OpenAI Client Initialization","description":"Initialize the OpenAI client to be used for API calls.","line_start":24,"line_end":25},{"name":"RuleContentGenerator Class","description":"Class that generates rule content from documentation files.","line_start":26,"line_end":302}],"key_elements":[{"name":"RuleContentGenerator","description":"Class responsible for generating rule content from documentation files.","line":37},{"name":"__init__","description":"Constructor for RuleContentGenerator that initializes the documentation directory.","line":43},{"name":"extract_documentation","description":"Extracts documentation for a rule from source files.","line":52},{"name":"generate_rule_content","description":"Generates rule content from documentation.","line":110},{"name":"create_rule_file","description":"Creates a rule file from generated content.","line":183},{"name":"_call_openai_with_retries","description":"Calls the OpenAI API with retries to generate/enhance rule content.","line":221},{"name":"enhance_rule_content","description":"Enhances rule content using LLM to fill in missing sections or improve existing ones.","line":291}]}
"""
# FILE_MAP_END

"""
Rule Content Generator Module for Documentation Rule Generator.

This module provides functions for generating rule content from documentation,
including extracting relevant sections and transforming them to rule format.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

from openai import OpenAI

# Import existing extractors and transformers
from ..extractors.documentation_extractor import (
    extract_documentation_for_rule,
    generate_glob_patterns,
)

from ..transformers.markdown_to_rule import (
    transform_to_rule_content,
    generate_rule_description,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI()


class RuleContentGenerator:
    """
    Generates rule content from documentation files, extracting relevant sections
    and transforming them to rule format.
    """

    def __init__(self, doc_dir: str):
        """
        Initialize the content generator.

        Args:
            doc_dir: Base directory for documentation files
        """
        self.doc_dir = Path(doc_dir)

    def extract_documentation(
        self,
        rule_id: str,
        rule_name: str,
        source_files: List[str],
        category: str = "Documentation",
    ) -> Dict[str, Any]:
        """
        Extract documentation for a rule from source files.

        Args:
            rule_id: ID of the rule
            rule_name: Name of the rule
            source_files: List of source file paths (relative to doc_dir)
            category: Category of the rule

        Returns:
            Dictionary containing extracted content
        """
        logger.info(f"Extracting documentation for rule {rule_id}: {rule_name}")

        # Process each source file
        for source_file in source_files:
            file_path = self.doc_dir / source_file
            logger.info(f"Processing source file: {file_path}")

            if not file_path.exists():
                logger.warning(f"Source file not found: {file_path}")
                continue

            # Extract documentation from the file
            try:
                extracted_content = extract_documentation_for_rule(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    source_files=[str(file_path)],
                    doc_dir=str(self.doc_dir),
                )

                if extracted_content:
                    # Transform the extracted content to rule format
                    rule_content = transform_to_rule_content(
                        extracted_content, rule_name
                    )

                    # Get or generate appropriate glob patterns
                    glob_patterns = generate_glob_patterns(rule_name)

                    return {
                        "content": rule_content,
                        "description": generate_rule_description(
                            rule_name, extracted_content
                        ),
                        "glob_patterns": glob_patterns,
                    }
                else:
                    logger.warning(f"No content extracted from {file_path}")
            except Exception as e:
                logger.error(f"Error extracting documentation: {str(e)}")

        # If we reached here, no content was extracted
        logger.error(f"Failed to extract documentation for rule {rule_id}")
        return {"error": f"Failed to extract documentation for rule {rule_id}"}

    def generate_rule_content(
        self,
        rule_id: str,
        rule_name: str,
        source_files: List[str],
        category: str = "Documentation",
        parent_id: Optional[str] = None,
        rule_type: str = None,
    ) -> Dict[str, Any]:
        """
        Generate rule content from documentation.

        Args:
            rule_id: ID of the rule
            rule_name: Name of the rule
            source_files: List of source file paths (relative to doc_dir)
            category: Category of the rule
            parent_id: ID of the parent rule (if any)
            rule_type: Type of rule (parent, child, grandchild)

        Returns:
            Dictionary containing generated content and metadata
        """
        # Determine rule type if not provided
        if rule_type is None:
            if parent_id is None:
                rule_type = "parent"
            else:
                parent_parts = parent_id.count(".") if "." in parent_id else 0
                rule_parts = rule_id.count(".") if "." in rule_id else 0

                if rule_parts == parent_parts + 1:
                    rule_type = "child"
                else:
                    rule_type = "grandchild"

        logger.info(
            f"Rule {rule_id} is a {rule_type} rule"
            + (f" (parent_id: {parent_id})" if parent_id else "")
        )

        # Determine which generation rule to use
        generation_rule = "010" if rule_type == "parent" else "011"
        logger.info(f"Using rule {generation_rule} for generation")

        # Extract documentation
        result = self.extract_documentation(rule_id, rule_name, source_files, category)

        if "error" in result:
            return result

        # Create the rule content structure
        rule_content = result["content"]
        description = result["description"]
        glob_patterns = result["glob_patterns"]

        # Add metadata
        rule_content["rule_name"] = rule_name

        # Add parent reference for child rules
        if parent_id:
            if "metadata" not in rule_content:
                rule_content["metadata"] = {}
            rule_content["metadata"]["parent_id"] = parent_id

        # Build frontmatter
        frontmatter = {"description": description, "globs": glob_patterns}

        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "content": rule_content,
            "frontmatter": frontmatter,
            "description": description,
            "parent_id": parent_id,
        }

    def create_rule_file(self, rule_content: Dict[str, Any], full_path: Path) -> bool:
        """
        Create a rule file from generated content.

        Args:
            rule_content: Generated rule content and metadata
            full_path: Full path where the rule file should be created

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Format the content for file writing
            frontmatter = rule_content.get("frontmatter", {})
            content = rule_content.get("content", {})

            # Create the file content
            file_content = "---\n"
            file_content += yaml.dump(frontmatter, default_flow_style=False)
            file_content += "---\n"
            file_content += json.dumps(content, indent=2)

            # Write to file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            logger.info(f"Generated rule file: {full_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating rule file: {str(e)}")
            return False

    def _call_openai_with_retries(
        self, system_message: str, user_message: str, section: str, rule_id: str
    ) -> Dict[str, Any]:
        """
        Call the OpenAI API with retries to help generate/enhance rule content.

        Args:
            system_message: The system message for the API call
            user_message: The user message for the API call
            section: The section being generated
            rule_id: The ID of the rule

        Returns:
            Dictionary with the generated content
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Sending request to OpenAI API for rule {rule_id}, section {section}:"
                )
                logger.debug(f"System message: {system_message[:200]}...")
                logger.debug(f"User message: {user_message[:200]}...")

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                )

                # Get response content
                content = response.choices[0].message.content
                logger.debug(f"Received response: {content[:200]}...")

                # Try to parse as JSON
                try:
                    data = json.loads(content)
                    logger.info("Successfully parsed response as JSON")
                    return data
                except json.JSONDecodeError:
                    # If it's not valid JSON, try to extract JSON content from markdown code blocks
                    logger.warning(
                        "Response is not valid JSON, attempting to extract JSON from markdown"
                    )

                    # Look for JSON inside markdown code blocks
                    if "```json" in content:
                        try:
                            # Extract content between ```json and ```
                            json_content = (
                                content.split("```json", 1)[1]
                                .split("```", 1)[0]
                                .strip()
                            )
                            data = json.loads(json_content)
                            logger.info(
                                "Successfully extracted JSON from markdown code block"
                            )
                            return data
                        except (IndexError, json.JSONDecodeError) as e:
                            logger.warning(
                                f"Failed to extract JSON from markdown: {str(e)}"
                            )

                    # Try again as this wasn't valid JSON
                    logger.warning(
                        f"Attempt {attempt+1}/{max_retries} failed: invalid JSON"
                    )
                    time.sleep(1)  # Wait before retry

            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
                time.sleep(1)  # Wait before retry

        # If we reach here, all attempts failed
        logger.error(f"All {max_retries} attempts to call OpenAI API failed")

        # Return an empty dictionary or a default response
        return {"error": f"Failed to generate content for section {section}"}

    def enhance_rule_content(self, rule_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance rule content using LLM to fill in missing sections or improve existing ones.

        Args:
            rule_content: The rule content to enhance

        Returns:
            Enhanced rule content
        """
        # This is a placeholder for LLM-based rule enhancement
        # For now, we'll just return the original content
        return rule_content
