# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"LLM Orchestrator Module","description":"This module orchestrates LLM interactions for the DocRuleGen application, providing a unified interface for taxonomy generation, rule generation, validation, and improvement cycles.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary libraries and modules for the LLM Orchestrator.","line_start":3,"line_end":17},{"name":"LLMOrchestrator Class","description":"Class that orchestrates LLM-based operations including taxonomy generation, rule generation, validation, and improvement.","line_start":19,"line_end":469}],"key_elements":[{"name":"LLMOrchestrator","description":"Class responsible for managing LLM interactions.","line":20},{"name":"__init__","description":"Constructor for initializing the LLMOrchestrator with configuration.","line":33},{"name":"generate_taxonomy","description":"Method to generate a taxonomy from document content using LLM.","line":66},{"name":"generate_rule","description":"Method to generate a rule from document content and taxonomy.","line":189},{"name":"validate_rule","description":"Method to validate a rule using LLM.","line":344},{"name":"improve_rule","description":"Method to improve a rule based on validation feedback using LLM.","line":417}]}
"""
# FILE_MAP_END

"""
LLM Orchestrator Module.

This module orchestrates LLM interactions for the DocRuleGen application,
providing a unified interface for taxonomy generation, rule generation,
validation, and improvement cycles.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from .llm_client import get_completion, is_provider_available
from ..utils.config_loader import load_prompt_config, load_config

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Orchestrate LLM-based operations across the DocRuleGen application.

    This class coordinates all LLM interactions, including:
    - Taxonomy generation
    - Rule generation
    - Rule validation
    - Rule improvement

    It maintains context across operations and ensures proper prompt management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM orchestrator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or load_config("app_config", "app_config")
        self.llm_config = self.config.get("llm", {})

        # Default provider and model settings
        self.default_provider = self.llm_config.get(
            "default_provider", os.environ.get("DEFAULT_LLM_PROVIDER", "openai")
        )
        self.default_model = self.llm_config.get(
            f"default_{self.default_provider}_model",
            os.environ.get(
                f"DEFAULT_{self.default_provider.upper()}_MODEL",
                "gpt-4o-mini"
                if self.default_provider == "openai"
                else "claude-3-haiku-20240307",
            ),
        )
        self.default_temperature = float(
            self.llm_config.get(
                "default_temperature", os.environ.get("DEFAULT_TEMPERATURE", "0.3")
            )
        )
        self.default_max_tokens = int(
            self.llm_config.get(
                "default_max_tokens", os.environ.get("DEFAULT_MAX_TOKENS", "4000")
            )
        )

        # Ensure provider is available
        if not is_provider_available(self.default_provider):
            available_providers = [
                p for p in ["openai", "anthropic"] if is_provider_available(p)
            ]
            if available_providers:
                logger.warning(
                    f"Default provider '{self.default_provider}' not available. "
                    f"Falling back to '{available_providers[0]}'"
                )
                self.default_provider = available_providers[0]
            else:
                logger.error(
                    "No LLM providers available. Install openai or anthropic packages and set API keys."
                )

        logger.info(
            f"Initialized LLM Orchestrator with provider: {self.default_provider}, "
            f"model: {self.default_model}"
        )

    def generate_taxonomy(self, document_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a taxonomy from document content using LLM.

        Args:
            document_content: Extracted document content

        Returns:
            Generated taxonomy dictionary
        """
        logger.info("Generating taxonomy from document content")

        # Load taxonomy generation prompt
        prompt_config = load_prompt_config("taxonomy_generation")
        if not prompt_config:
            logger.error("Failed to load taxonomy generation prompt")
            return {"error": "Failed to load taxonomy generation prompt"}

        # Extract prompt content from the correct structure
        system_message = prompt_config.get("prompt", {}).get("system", "")
        user_prompt_template = prompt_config.get("prompt", {}).get("user", "")

        # Extract text content for the prompt
        content_text = document_content.get("text", "")
        if not content_text and "content" in document_content:
            content_text = document_content.get("content", "")

        if not content_text:
            logger.error("No document content found for taxonomy generation")
            return {"error": "No document content found for taxonomy generation"}

        if isinstance(content_text, dict):
            # Convert dictionary to string representation if needed
            content_text = json.dumps(content_text, indent=2)

        # Prepare user prompt - only use document_content parameter which is in the template
        try:
            # Check if the required parameter is in the template
            if "{document_content}" not in user_prompt_template:
                logger.warning("Missing document_content parameter in prompt template")
                # Create a simplified prompt
                user_prompt = f"Generate a taxonomy for the following document content:\n\n{content_text}"
            else:
                # Format the prompt with the document content
                user_prompt = user_prompt_template.format(document_content=content_text)
        except Exception as e:
            logger.error(f"Error formatting user prompt: {str(e)}")
            # Fallback to a simpler approach if formatting fails
            user_prompt = f"Generate a taxonomy for the following document content:\n\n{content_text}"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Get completion from LLM
            response = get_completion(
                messages=messages,
                provider=self.default_provider,
                model=self.default_model,
                max_tokens=self.default_max_tokens,
                temperature=self.default_temperature,
                json_response=True,
            )

            # Parse JSON response
            try:
                # First try direct parsing
                taxonomy = json.loads(response)

                # Validate that the taxonomy has the expected structure
                if "categories" not in taxonomy:
                    logger.warning("Taxonomy response missing 'categories' key")
                    # Try to extract JSON from the response if it's wrapped in text
                    import re

                    json_match = re.search(
                        r"```json\s*(.*?)\s*```", response, re.DOTALL
                    )
                    if json_match:
                        try:
                            taxonomy = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            pass

                    # If still no categories, create a default structure
                    if "categories" not in taxonomy:
                        logger.warning("Creating default taxonomy structure")
                        taxonomy = {"categories": [], "relationships": []}

                logger.info("Successfully generated taxonomy")
                return taxonomy
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse taxonomy JSON response: {str(e)}")
                logger.debug(f"Raw response: {response}")

                # Try to extract JSON from the response if it's wrapped in text
                import re

                json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
                if json_match:
                    try:
                        taxonomy = json.loads(json_match.group(1))
                        logger.info("Successfully extracted JSON from code block")
                        return taxonomy
                    except json.JSONDecodeError:
                        pass

                # Return error with default structure
                return {
                    "error": f"Failed to parse taxonomy JSON response: {str(e)}",
                    "categories": [],
                    "relationships": [],
                }

        except Exception as e:
            logger.error(f"Error generating taxonomy: {str(e)}")
            return {
                "error": f"Error generating taxonomy: {str(e)}",
                "categories": [],
                "relationships": [],
            }

    def generate_rule(
        self,
        doc_content: Dict[str, Any],
        taxonomy: Dict[str, Any],
        rule_type: str = "standard",
        cursor_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a rule from document content and taxonomy.

        Args:
            doc_content: Extracted document content
            taxonomy: Taxonomy dictionary
            rule_type: Type of rule to generate (standard, parent, child, standalone)
            cursor_rules: Optional list of cursor rules to guide generation

        Returns:
            Generated rule dictionary
        """
        logger.info(f"Generating {rule_type} rule from document content")

        # Load rule generation prompt
        prompt_config = load_prompt_config("rule_generation")
        if not prompt_config:
            logger.error("Failed to load rule generation prompt")
            return {"error": "Failed to load rule generation prompt"}

        # Extract prompt content from the correct structure
        system_message = prompt_config.get("prompt", {}).get("system", "")
        user_prompt_template = prompt_config.get("prompt", {}).get("user", "")

        # Extract text content for the prompt
        content_text = doc_content.get("text", "")
        if not content_text and "content" in doc_content:
            content_text = doc_content.get("content", "")

        # Ensure we have content to work with
        if not content_text:
            logger.error("No markdown content found in document content")
            return {
                "error": "No markdown content found in document content",
                "status": "error",
            }

        if isinstance(content_text, dict):
            # Convert dictionary to string representation if needed
            content_text = json.dumps(content_text, indent=2)

        # Prepare taxonomy text
        taxonomy_text = json.dumps(taxonomy, indent=2) if taxonomy else "{}"

        # Generate a rule ID (3-digit number)
        rule_id = "301"  # Default rule ID

        # Determine rule name from document title or taxonomy
        rule_name = doc_content.get("title", "")
        if not rule_name and taxonomy and "categories" in taxonomy:
            # Use the first category name as a fallback
            categories = taxonomy.get("categories", [])
            if categories and len(categories) > 0:
                rule_name = categories[0].get("name", "")

        # Default rule name if still empty
        if not rule_name:
            rule_name = "Generated Rule"

        # Determine file pattern from document type
        file_pattern = "*.*"  # Default pattern
        doc_type = doc_content.get("document_type", "").lower()
        if not doc_type and "format" in doc_content:
            doc_type = doc_content.get("format", "").lower()

        if doc_type == "python" or "python" in rule_name.lower():
            file_pattern = "*.py"
        elif doc_type == "javascript":
            file_pattern = "*.js"
        elif doc_type == "typescript":
            file_pattern = "*.ts"

        # Prepare user prompt
        try:
            # Check if the template contains placeholders that we need to fill
            import re

            placeholders = re.findall(r"\{([^}]+)\}", user_prompt_template)

            # Create a dictionary with all possible parameters
            format_params = {
                "document_content": content_text,
                "rule_id": rule_id,
                "rule_name": rule_name,
                "file_pattern": file_pattern,
                "taxonomy": taxonomy_text,
                # Add default values for other possible placeholders
                "action": "follow formatting standards",
                "context": "writing Python code",
                "purpose": "ensure readability and consistency",
                "language": "python",
                "good_example_code": "# Example code here",
                "good_example_explanation": "This follows the standards",
                "bad_example_code": "# Bad example here",
                "bad_example_explanation": "This violates the standards",
                "critical_violation_1": "mix tabs and spaces",
                "critical_violation_2": "exceed line length limits",
                "specific_risk_1": "Inconsistent formatting reduces readability",
                "specific_risk_2": "Poor organization makes code harder to maintain",
                # Add more default values for all possible placeholders
                "purpose_description": "This rule establishes consistent formatting standards for Python code to improve readability, maintainability, and collaboration among developers.",
                "application_description": "This rule applies to all Python files (*.py) in the codebase, including scripts, modules, and packages.",
                "importance_description": "Consistent code formatting reduces cognitive load when reading code, minimizes unnecessary differences in version control, and helps new developers quickly understand the codebase.",
                "requirements_list": "1. **Indentation**: Use 4 spaces per indentation level.\n2. **Line Length**: Limit lines to a maximum of 88 characters.\n3. **Imports**: Group imports by standard library, third-party, and local.",
                "version": "1.0.0",
                "description": "MUST follow Python formatting standards WHEN writing Python code TO ensure readability and consistency",
            }

            # Only include parameters that are actually in the template
            required_params = {
                k: v for k, v in format_params.items() if k in placeholders
            }

            # Format the prompt with the required parameters
            user_prompt = user_prompt_template.format(**required_params)

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ]

            # Get completion from LLM
            response = get_completion(
                messages=messages,
                provider=self.default_provider,
                model=self.default_model,
                max_tokens=self.default_max_tokens,
                temperature=self.default_temperature,
            )

            # Return the generated rule content
            return {"content": response, "status": "success"}

        except Exception as e:
            logger.error(f"Error formatting prompt: {str(e)}")
            # Try a simplified approach
            try:
                simplified_prompt = f"Generate a cursor rule from the following document content:\n\n{content_text}\n\nThe rule should have ID {rule_id}, name '{rule_name}', and apply to files matching '{file_pattern}'."
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": simplified_prompt},
                ]

                response = get_completion(
                    messages=messages,
                    provider=self.default_provider,
                    model=self.default_model,
                    max_tokens=self.default_max_tokens,
                    temperature=self.default_temperature,
                )

                return {"content": response, "status": "success"}
            except Exception as e2:
                logger.error(f"Error with simplified prompt: {str(e2)}")
                return {
                    "error": f"Failed to generate rule: {str(e)}",
                    "status": "error",
                }

    def validate_rule(
        self, rule_content: str, rule_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a rule using LLM.

        Args:
            rule_content: Content of the rule to validate
            rule_path: Optional path to the rule file

        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating rule using LLM: {rule_path or 'unnamed'}")

        # Load rule validation prompt
        prompt_config = load_prompt_config("rule_validation")
        if not prompt_config:
            logger.error("Failed to load rule validation prompt")
            return {"error": "Failed to load rule validation prompt"}

        # Extract prompt content from the correct structure
        system_message = prompt_config.get("prompt", {}).get("system", "")
        user_prompt_template = prompt_config.get("prompt", {}).get("user", "")

        # Prepare user prompt with error handling
        try:
            user_prompt = user_prompt_template.format(
                rule_content=rule_content, rule_path=rule_path or "unknown"
            )
        except KeyError as e:
            logger.error(f"Error formatting user prompt: {str(e)}")
            # Provide a default validation response if an error occurs
            return {
                "status": "fail",
                "score": 0,
                "error": f"Error formatting validation prompt: {str(e)}",
                "issues": [
                    {
                        "severity": "critical",
                        "section": "validation",
                        "description": f"Prompt formatting error: {str(e)}",
                        "suggestion": "Check the validation prompt template for required fields",
                    }
                ],
                "feedback": "Validation failed due to prompt formatting error",
            }

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Get completion from LLM
            response = get_completion(
                messages=messages,
                provider=self.default_provider,
                model=self.default_model,
                max_tokens=self.default_max_tokens,
                temperature=self.default_temperature,
                json_response=True,
            )

            # Parse JSON response
            validation_result = json.loads(response)

            return validation_result
        except Exception as e:
            logger.error(f"Error in LLM validation: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to validate rule using LLM",
            }

    def improve_rule(
        self, rule_content: str, validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Improve a rule based on validation feedback using LLM.

        Args:
            rule_content: The rule content to improve
            validation_result: Validation result dictionary

        Returns:
            Improved rule dictionary
        """
        logger.info("Improving rule based on validation feedback")

        # Load rule improvement prompt
        prompt_config = load_prompt_config("rule_improvement")
        if not prompt_config:
            logger.error("Failed to load rule improvement prompt")
            return {"error": "Failed to load rule improvement prompt"}

        # Extract prompt content from the correct structure
        system_message = prompt_config.get("prompt", {}).get("system", "")
        user_prompt_template = prompt_config.get("prompt", {}).get("user", "")

        # Format validation feedback
        validation_feedback = json.dumps(validation_result, indent=2)

        # Prepare user prompt
        user_prompt = user_prompt_template.format(
            rule_content=rule_content, validation_feedback=validation_feedback
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Get completion from LLM
            response = get_completion(
                messages=messages,
                provider=self.default_provider,
                model=self.default_model,
                max_tokens=self.default_max_tokens,
                temperature=self.default_temperature,
            )

            # Return the improved rule content
            logger.info("Successfully improved rule")
            return {"content": response, "status": "success"}

        except Exception as e:
            logger.error(f"Error improving rule: {str(e)}")
            return {"error": f"Error improving rule: {str(e)}", "status": "error"}
