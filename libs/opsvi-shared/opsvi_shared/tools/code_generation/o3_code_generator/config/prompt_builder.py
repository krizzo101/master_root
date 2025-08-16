"""
PromptBuilder Utility Module

This module provides the PromptBuilder class for centralized construction of prompts
in the O3 code generator. It supports loading templates from strings or files,
adding contextual snippets, managing variable substitution, and building the final
prompt string. All operations are logged via O3Logger for debugging and error tracking.

Usage:
    from src.tools.code_generation.o3_code_generator.utils.prompt_builder import PromptBuilder

    builder = PromptBuilder()
    builder.load_template_from_file("path/to/template.txt")
    builder.add_context_from_file("path/to/context.txt")
    builder.add_variables({"name": "World", "language": "Python"})
    prompt = builder.build()
"""

from typing import Any, Dict, List, Optional

from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.utils.logging.o3_logger import O3Logger


class PromptBuilder:
    """
    A utility for constructing prompts with template management, context integration,
    and variable substitution.

    Attributes:
        logger: O3Logger instance for logging debug and error messages.
        template: The raw prompt template string.
        context_parts: List of context snippets to prepend to the template.
        variables: Dictionary of keys and values for template substitution.
    """

    def __init__(self, template: Optional[str] = None) -> None:
        """
        Initialize the PromptBuilder.

        Args:
            template: Optional initial template string.
        """
        self.logger = O3Logger().get_logger()
        self.template: str = template or ""
        self.context_parts: List[str] = []
        self.variables: Dict[str, Any] = {}

    def load_template(self, template_str: str) -> None:
        """
        Set the prompt template from a string.

        Args:
            template_str: The template content.
        """
        try:
            self.template = template_str
            self.logger.log_debug("Template loaded from string.")
        except Exception as e:
            self.logger.log_error(f"Error in load_template: {e}")
            raise

    def load_template_from_file(self, file_path: str) -> None:
        """
        Load the prompt template from a file.

        Args:
            file_path: Path to the template file.
        """
        try:
            loader = UniversalInputLoader(file_path)
            content = loader.load()
            self.template = content
            self.logger.log_debug(f"Template loaded from file: {file_path}")
        except Exception as e:
            self.logger.log_error(f"Error loading template from file {file_path}: {e}")
            raise

    def add_context_from_file(self, file_path: str) -> None:
        """
        Append a context snippet loaded from a file.

        Args:
            file_path: Path to the context file.
        """
        try:
            loader = UniversalInputLoader(file_path)
            content = loader.load()
            self.context_parts.append(content)
            self.logger.log_debug(f"Context added from file: {file_path}")
        except Exception as e:
            self.logger.log_error(f"Error adding context from file {file_path}: {e}")
            raise

    def add_variable(self, key: str, value: Any) -> None:
        """
        Add a single variable for template substitution.

        Args:
            key: The placeholder name in the template.
            value: The value to substitute.
        """
        try:
            self.variables[key] = value
            self.logger.log_debug(f"Variable added: {key}={value}")
        except Exception as e:
            self.logger.log_error(f"Error adding variable {key}: {e}")
            raise

    def add_variables(self, vars_dict: Dict[str, Any]) -> None:
        """
        Add multiple variables for template substitution.

        Args:
            vars_dict: Dictionary of placeholder names and values.
        """
        try:
            self.variables.update(vars_dict)
            self.logger.log_debug("Multiple variables added.")
        except Exception as e:
            self.logger.log_error(f"Error adding variables: {e}")
            raise

    def build(self) -> str:
        """
        Construct and return the final prompt string.

        Combines context snippets, applies the template, and substitutes variables.

        Returns:
            The fully constructed prompt.
        """
        try:
            parts: List[str] = []
            if self.context_parts:
                parts.extend(self.context_parts)
            parts.append(self.template)
            prompt = "\n".join(parts)
            if self.variables:
                prompt = prompt.format(**self.variables)
            self.logger.log_debug("Prompt built successfully.")
            return prompt
        except Exception as e:
            self.logger.log_error(f"Error building prompt: {e}")
            raise


__all__ = ["PromptBuilder"]
