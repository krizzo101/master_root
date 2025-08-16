# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Base Preprocessor Module","description":"This module provides the base class for all content preprocessors.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and types for the preprocessor.","line_start":6,"line_end":9},{"name":"Class Definition","description":"Defines the BasePreprocessor class and its methods.","line_start":11,"line_end":106}],"key_elements":[{"name":"BasePreprocessor","description":"Base class for all preprocessors.","line":12},{"name":"__init__","description":"Constructor for the BasePreprocessor class.","line":15},{"name":"preprocess","description":"Method to preprocess the extracted content.","line":24},{"name":"process","description":"Method to process the extracted content, to be implemented by subclasses.","line":53},{"name":"validate_input","description":"Method to validate the input extracted content.","line":68},{"name":"_create_standardized_structure","description":"Method to create a standardized structure for preprocessed content.","line":90},{"name":"logger","description":"Logger instance for logging errors and information.","line":10}]}
"""
# FILE_MAP_END

"""
Base Preprocessor Module.

This module provides the base class for all content preprocessors.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BasePreprocessor:
    """Base class for all preprocessors."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the preprocessor.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

    def preprocess(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess the extracted content.

        This method should be implemented by subclasses to perform
        specific preprocessing operations.

        Args:
            extracted_content: The extracted content to preprocess

        Returns:
            Preprocessed content
        """
        if not self.validate_input(extracted_content):
            logger.error(f"Invalid input for {self.__class__.__name__}")
            return {
                "status": "error",
                "message": f"Invalid input for {self.__class__.__name__}",
            }

        # Process the content
        result = self.process(extracted_content)

        # Ensure status is set
        if "status" not in result:
            result["status"] = "success"

        return result

    def process(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the extracted content.

        This method should be implemented by subclasses to perform
        specific processing operations.

        Args:
            extracted_content: The extracted content to process

        Returns:
            Processed content
        """
        raise NotImplementedError("Subclasses must implement this method")

    def validate_input(self, extracted_content: Dict[str, Any]) -> bool:
        """
        Validate the input extracted content.

        Args:
            extracted_content: Extracted content to validate

        Returns:
            True if the content is valid, False otherwise
        """
        # Check for required fields
        if not extracted_content:
            return False

        if extracted_content.get("status") != "success":
            return False

        if "content" not in extracted_content:
            return False

        return True

    def _create_standardized_structure(self) -> Dict[str, Any]:
        """
        Create a standardized structure for preprocessed content.

        Returns:
            Dictionary with standardized structure
        """
        return {
            "metadata": {},
            "overview": "",
            "context": "",
            "requirements": "",
            "examples": [],
            "warnings": [],
            "concepts": [],
            "directive_candidates": [],
            "standardized_markdown": "",
        }
