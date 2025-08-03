"""
Base file processor for genfilemap.

This module defines the base FileProcessor class that all file type-specific processors must implement.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json

from genfilemap.utils.file_utils import (
    get_file_type,
    calculate_file_hash,
    extract_existing_file_map,
)
from genfilemap.api.base import APIClient
from genfilemap.config import get_config_value
from genfilemap.models.schemas import validate_file_map_json, validate_line_numbers
from genfilemap.logging_utils import debug as log_debug


class FileProcessor:
    """Base class for file processors"""

    def __init__(self, file_path: str, api_client: APIClient, model: str, config=None):
        """
        Initialize the file processor with file path and API client

        Args:
            file_path: Path to the file to process
            api_client: API client for LLM requests
            model: Model to use for LLM requests
            config: Optional configuration object
        """
        self.file_path = file_path
        self.api_client = api_client
        self.model = model
        self.file_type = get_file_type(file_path)
        self.config = config or {}

    def debug_print(self, msg: str) -> None:
        """
        Print debug message only if debug mode is enabled.

        Args:
            msg: The message to print
        """
        debug_enabled = get_config_value(self.config, "debug", False)
        if debug_enabled:
            # Use logging system so output gets captured by --log-file
            log_debug(msg)

    async def analyze_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze the file structure to provide hints for the LLM.

        This should be implemented by subclasses to provide file type-specific analysis.
        """
        # Base implementation provides minimal analysis
        line_count = content.count("\n") + 1

        return {
            "line_count": line_count,
            "file_type": self.file_type,
            "extension": Path(self.file_path).suffix.lower(),
            "filename": os.path.basename(self.file_path),
        }

    async def generate_file_map(
        self, content: str, comment_style: Tuple[str, str, str], force: bool = False
    ) -> Optional[str]:
        """
        Generate a file map for the given content.

        Args:
            content: The file content to generate a map for
            comment_style: The comment style tuple (start_multi, end_multi, single_line)
            force: Whether to force generation even if hash matches

        Returns:
            The generated file map or None if the existing map is valid and up-to-date
        """
        # This should be implemented by subclasses
        raise NotImplementedError("Must be implemented by subclass")

    async def fallback_generation(
        self,
                               system_message: str,
                               user_prompt: str,
                               content: str,
                               comment_style: Tuple[str, str, str],
        complexity_ratio: float = 0.5,
    ) -> Optional[str]:
        """
        Implements fallback complexity reduction when initial generation fails.

        This method tries to generate a file map with reduced complexity when the
        initial generation attempt fails. It reduces the complexity by the specified
        ratio and tries again.

        Args:
            system_message: The original system message
            user_prompt: The original user prompt
            content: The file content to generate a map for
            comment_style: The comment style tuple (start_multi, end_multi, single_line)
            complexity_ratio: The ratio by which to reduce complexity (default: 0.5)

        Returns:
            The generated file map JSON string or None if generation still fails
        """
        # Check if fallback is enabled in the config
        fallback_enabled = True
        if hasattr(self, "config") and isinstance(self.config, dict):
            fallback_enabled = get_config_value(self.config, "fallback.enabled", True)
            # Override complexity_ratio if specified in config
            if "fallback.complexity_ratio" in self.config:
                complexity_ratio = get_config_value(
                    self.config, "fallback.complexity_ratio"
                )

        # If fallback is disabled, return None immediately
        if not fallback_enabled:
            self.debug_print("DEBUG: Fallback generation is disabled in configuration")
            return None

        self.debug_print(
            f"DEBUG: Starting fallback generation with complexity ratio: {complexity_ratio}"
        )

        # Add simplification directive to the system message
        simplified_system_message = (
            system_message
            + f"""

FALLBACK SIMPLIFICATION REQUIREMENTS:
1. Due to previous generation failure, you MUST reduce complexity by approximately {int(complexity_ratio * 100)}%.
2. Focus ONLY on the most important top-level sections and elements.
3. Reduce the number of sections and key elements identified.
4. Keep descriptions shorter and more concise.
5. Focus on the highest-level headings and most critical structural elements.
6. Include ONLY the most essential information needed for navigation.
7. Prioritize accuracy over completeness in this fallback mode.

This simplification is necessary to avoid truncation and ensure a complete file map can be generated.
"""
        )
        # Try the simplified generation
        try:
            result = await self.api_client.generate_completion(
                simplified_system_message, user_prompt, self.model
            )

            # Try to parse as JSON
            try:
                file_map_obj = json.loads(result)

                # Validate against our schema
                valid = await self.validate_generated_map(
                    json.dumps(file_map_obj), content
                )

                if valid:
                    self.debug_print("DEBUG: Fallback generation successful")
                    return json.dumps(file_map_obj, separators=(",", ":"))
                else:
                    self.debug_print(
                        "DEBUG: Fallback generation produced invalid file map"
                    )
                    return None
            except json.JSONDecodeError as e:
                self.debug_print(
                    f"DEBUG: Fallback generation produced invalid JSON: {str(e)}"
                )
                return None
        except Exception as e:
            self.debug_print(f"DEBUG: Error in fallback generation: {str(e)}")
            return None

    async def validate_generated_map(self, file_map_json: str, content: str) -> bool:
        """
        Validate the generated file map for accuracy.

        Args:
            file_map_json: The JSON string of the generated file map
            content: The original file content

        Returns:
            True if the file map is valid, False otherwise
        """
        # Base validation using schema and line numbers
        try:
            file_map_obj = json.loads(file_map_json)

            # Validate against schema
            validate_file_map_json(file_map_obj)

            # Validate line numbers
            return validate_line_numbers(file_map_json, content)

        except (json.JSONDecodeError, ValueError) as e:
            self.debug_print(f"Validation error for {self.file_path}: {str(e)}")
            return False


def get_processor_for_file(
    file_path: str, api_client: APIClient, model: str, config=None
) -> FileProcessor:
    """
    Factory function to get the appropriate processor for a file.

    Args:
        file_path: Path to the file
        api_client: API client for LLM requests
        model: Model to use for LLM requests
        config: Optional configuration object

    Returns:
        An instance of the appropriate FileProcessor subclass
    """
    file_type = get_file_type(file_path)

    # Import here to avoid circular imports
    from genfilemap.processors.code_processor import CodeFileProcessor
    from genfilemap.processors.doc_processor import DocumentationFileProcessor

    # Select processor based on file type
    if file_type == "documentation":
        return DocumentationFileProcessor(file_path, api_client, model, config)
    else:
        # Default to code processor for all code-like files
        return CodeFileProcessor(file_path, api_client, model, config)
