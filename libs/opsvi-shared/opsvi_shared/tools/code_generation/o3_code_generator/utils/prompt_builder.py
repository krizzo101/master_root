"""
Module Name: prompt_builder.py

Purpose: Centralized prompt construction utility for the O3 code generator with automatic rule injection.

Functionality:
- Load project_rules.md and universal_rules.md on initialization
- Prepend rules to every system prompt in analysis and generation methods
- Provide DRY prompt building via a private helper
- Log warnings if rule files are missing or prompts exceed length limits

Author: O3 Code Generator
Version: 1.2.0
"""

import json
from pathlib import Path
from typing import Any, Optional

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)


class PromptBuilder:
    """
    Centralized prompt construction for O3 models with automatic rule injection.

    On initialization, loads project-specific and universal rules and injects them
    at the top of every system prompt in analysis and generation methods.

    Attributes:
        max_prompt_length: Maximum allowed prompt length.
        default_templates: Default templates for prompts.
        project_rules: Contents of project_rules.md or empty string if unavailable.
        universal_rules: Contents of universal_rules.md or empty string if unavailable.
        logger: Logger instance.
        loader: UniversalInputLoader instance.
    """

    def __init__(self) -> None:
        """
        Initialize PromptBuilder.

        Loads project and universal rules, sets up default prompt templates,
        and maximum prompt length.
        """
        self.logger = get_logger()
        self.loader = UniversalInputLoader()
        self.max_prompt_length: int = 32000
        self.default_templates = self._get_default_templates()
        self.project_rules: str = ""
        self.universal_rules: str = ""
        self._load_rules()
        self.logger.log_info("Initialized PromptBuilder with loaded rules")

    def _load_rules(self) -> None:
        """
        Load project_rules.md and universal_rules.md into memory.

        Logs a warning if either file is missing or unreadable.
        """
        rules_dir = Path(__file__).parent.parent / "docs"
        for name, attr in (
            ("project_rules.md", "project_rules"),
            ("universal_rules.md", "universal_rules"),
        ):
            path = rules_dir / name
            try:
                if path.suffix == ".md":
                    setattr(self, attr, path.read_text(encoding="utf-8"))
                else:
                    rules = self.loader.load_file_by_extension(path)
                    content = (
                        rules if isinstance(rules, str) else json.dumps(rules, indent=2)
                    )
                    setattr(self, attr, content)
            except Exception as e:
                self.logger.log_warning(f"Could not load {name}: {e}")
                setattr(self, attr, "")
            else:
                pass
            finally:
                pass
        else:
            pass

    def _prepend_rules(self, system_prompt: str) -> str:
        """
        Prepend loaded project and universal rules to the system prompt.

        Args:
            system_prompt: Original system prompt.

        Returns:
            Combined prompt string with rules at the top.
        """
        parts = []
        if self.project_rules:
            parts.append(self.project_rules)
        else:
            pass
        if self.universal_rules:
            parts.append(self.universal_rules)
        else:
            pass
        parts.append(system_prompt)
        return "\n".join(parts)

    def _build_prompt(
        self,
        template_key: str,
        input_data: Any,
        system_prompt: str,
        **template_vars: Any,
    ) -> str:
        """
        Generic prompt builder that handles rule injection, formatting, and validation.

        Args:
            template_key: Key for default_templates to use.
            input_data: Input data object for the prompt.
            system_prompt: Base system prompt.
            template_vars: Additional variables required by the template.

        Returns:
            Formatted prompt string with rules prepended.

        Raises:
            ValueError: If input_data is None.
        """
        if input_data is None:
            raise ValueError("Input data cannot be None")
        else:
            pass
        if hasattr(input_data, "dict"):
            input_dict = input_data.dict()
        elif hasattr(input_data, "__dict__"):
            input_dict = input_data.__dict__
        else:
            input_dict = (
                dict(input_data)
                if hasattr(input_data, "__iter__")
                else {"data": input_data}
            )
        full_system = self._prepend_rules(system_prompt)
        safe_vars = {
            "system_prompt": full_system,
            "input_data": json.dumps(input_dict, indent=2, default=str),
        }
        for key, value in template_vars.items():
            safe_vars[key] = (
                json.dumps(value, indent=2, default=str)
                if isinstance(value, (dict, list))
                else str(value)
            )
        else:
            pass
        template = self.default_templates[template_key]
        prompt = template.format(**safe_vars)
        if not self.validate_prompt_length(prompt):
            self.logger.log_warning(
                f"Generated {template_key} prompt is too long ({len(prompt)} characters)"
            )
        else:
            pass
        self.logger.log_debug(f"Built {template_key} prompt ({len(prompt)} characters)")
        return prompt

    def build_analysis_prompt(
        self,
        input_data: Any,
        analysis_data: dict[str, Any],
        system_prompt: str,
        instructions: Optional[str] = None,
    ) -> str:
        """
        Build comprehensive prompt for analysis with prepended rules.

        Args:
            input_data: Input data object containing analysis parameters.
            analysis_data: Dictionary containing analysis context and results.
            system_prompt: Base system prompt (cannot be empty).
            instructions: Optional additional instructions.

        Returns:
            Formatted prompt string for analysis.

        Raises:
            ValueError: If input_data is None or system_prompt is empty.
        """
        if not system_prompt or not system_prompt.strip():
            raise ValueError("System prompt cannot be empty")
        else:
            pass
        return self._build_prompt(
            template_key="analysis",
            input_data=input_data,
            system_prompt=system_prompt,
            analysis_context=analysis_data,
            instructions=instructions
            or "Please analyze the provided data and generate comprehensive results.",
        )

    def build_generation_prompt(
        self,
        input_data: Any,
        context: Optional[dict[str, Any]] = None,
        system_prompt: str = "",
        format_instructions: Optional[str] = None,
    ) -> str:
        """
        Build prompt for code generation with prepended rules.

        Args:
            input_data: Input data object containing generation parameters.
            context: Optional context dictionary for generation.
            system_prompt: Base system prompt.
            format_instructions: Optional format instructions.

        Returns:
            Formatted prompt string for code generation.

        Raises:
            ValueError: If input_data is None.
        """
        return self._build_prompt(
            template_key="generation",
            input_data=input_data,
            system_prompt=system_prompt,
            context=context or {},
            format_instructions=format_instructions
            or "Please generate the requested output following the specified format and requirements.",
        )

    def validate_prompt_length(
        self, prompt: str, max_length: Optional[int] = None
    ) -> bool:
        """
        Validate prompt length for model limits.

        Args:
            prompt: Prompt string to validate.
            max_length: Maximum allowed length (defaults to instance max_prompt_length).

        Returns:
            True if prompt is within length limits, False otherwise.
        """
        limit = max_length if max_length is not None else self.max_prompt_length
        if not isinstance(prompt, str):
            return False
        else:
            pass
        length = len(prompt)
        if length <= limit:
            self.logger.log_debug(f"Prompt length validated: {length}/{limit}")
            return True
        else:
            pass
        self.logger.log_warning(f"Prompt length ({length}) exceeds maximum ({limit})")
        return False

    def _get_default_templates(self) -> dict[str, str]:
        """
        Get default prompt templates.

        Returns:
            Dictionary of default prompt templates.
        """
        return {
            "analysis": "{system_prompt}\n\n## Input Data\n{input_data}\n\n## Analysis Context\n{analysis_context}\n\n## Instructions\n{instructions}\n\nPlease provide a comprehensive analysis based on the above information.",
            "generation": "{system_prompt}\n\n## Input Parameters\n{input_data}\n\n## Context Information\n{context}\n\n## Format Instructions\n{format_instructions}\n\nPlease generate the requested output following the specified format and requirements.",
            "simple": "{system_prompt}\n\n## Input\n{input_data}\n\n## Instructions\n{instructions}",
        }
