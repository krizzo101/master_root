# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Preprocessor Manager Module","description":"This module provides functionality to manage the preprocessing of extracted content.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and classes for preprocessing functionality.","line_start":3,"line_end":14},{"name":"PreprocessorManager Class","description":"Class that manages the preprocessing of extracted content.","line_start":16,"line_end":82}],"key_elements":[{"name":"PreprocessorManager","description":"Class responsible for managing preprocessors.","line":17},{"name":"__init__","description":"Constructor for PreprocessorManager that initializes configuration and registers default preprocessors.","line":20},{"name":"register_preprocessor","description":"Method to register a new preprocessor.","line":35},{"name":"preprocess","description":"Method that preprocesses the extracted content.","line":45}]}
"""
# FILE_MAP_END

"""
Preprocessor Manager Module.

This module provides functionality to manage the preprocessing of extracted content.
"""

import logging
from typing import Dict, Any, List, Optional

from .base_preprocessor import BasePreprocessor
from .markdown_preprocessor import MarkdownPreprocessor
from .concept_extractor import ConceptExtractor
from .directive_identifier import DirectiveIdentifier

logger = logging.getLogger(__name__)


class PreprocessorManager:
    """Manage the preprocessing of extracted content."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the preprocessor manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._preprocessors = []

        # Register default preprocessors
        self.register_preprocessor(MarkdownPreprocessor(config))
        self.register_preprocessor(ConceptExtractor(config))
        self.register_preprocessor(DirectiveIdentifier(config))

    def register_preprocessor(self, preprocessor: BasePreprocessor) -> None:
        """
        Register a preprocessor.

        Args:
            preprocessor: The preprocessor to register
        """
        self._preprocessors.append(preprocessor)
        logger.debug(f"Registered preprocessor: {preprocessor.__class__.__name__}")

    def preprocess(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess extracted content.

        Args:
            extracted_content: Extracted content from extractor

        Returns:
            Dictionary with preprocessed content
        """
        if not extracted_content or extracted_content.get("status") != "success":
            logger.error("Invalid input for preprocessing")
            return {"status": "error", "error": "Invalid input for preprocessing"}

        # Initialize the preprocessed content
        preprocessed_content = extracted_content.copy()

        # Apply each preprocessor in sequence
        for preprocessor in self._preprocessors:
            try:
                logger.info(f"Applying preprocessor: {preprocessor.__class__.__name__}")

                # Apply preprocessor
                result = preprocessor.preprocess(preprocessed_content)

                # Check if preprocessor succeeded
                if result.get("status") != "success":
                    logger.warning(
                        f"Preprocessor {preprocessor.__class__.__name__} failed: {result.get('error', 'Unknown error')}"
                    )
                    continue

                # Update preprocessed content with result
                preprocessed_content = result

            except Exception as e:
                logger.error(
                    f"Error in preprocessor {preprocessor.__class__.__name__}: {str(e)}"
                )

        # Create a standardized structure if not already present
        if "standardized_markdown" not in preprocessed_content:
            logger.warning(
                "No standardized markdown produced by preprocessors. Using original content."
            )
            preprocessed_content["standardized_markdown"] = extracted_content.get(
                "content", ""
            )

        # Set the overall status
        preprocessed_content["status"] = "success"

        return preprocessed_content
