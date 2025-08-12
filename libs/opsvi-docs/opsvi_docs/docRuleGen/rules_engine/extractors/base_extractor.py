# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Base Extractor Module","description":"This module provides the base class for all content extractors.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for the extractor functionality.","line_start":3,"line_end":10},{"name":"Class Definition","description":"Definition of the BaseExtractor class and its methods.","line_start":12,"line_end":84}],"key_elements":[{"name":"BaseExtractor","description":"Base class for all content extractors.","line":13},{"name":"__init__","description":"Initializer for the BaseExtractor class.","line":16},{"name":"extract","description":"Method to extract content from the source.","line":25},{"name":"validate_source","description":"Method to validate if the source can be processed.","line":37},{"name":"_read_file","description":"Method to read a file and return its content.","line":49},{"name":"_extract_metadata","description":"Method to extract metadata from content.","line":70},{"name":"logger","description":"Logger instance for logging errors and information.","line":6}]}
"""
# FILE_MAP_END

"""
Base Extractor Module.

This module provides the base class for all content extractors.
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BaseExtractor:
    """Base class for all content extractors."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the extractor.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

    def extract(self, source_path: str) -> Dict[str, Any]:
        """
        Extract content from the source.

        Args:
            source_path: Path to the source file

        Returns:
            Dictionary with extracted content
        """
        raise NotImplementedError("Subclasses must implement this method")

    def validate_source(self, source_path: str) -> bool:
        """
        Validate if the source can be processed by this extractor.

        Args:
            source_path: Path to the source file

        Returns:
            True if the source can be processed, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")

    def _read_file(self, file_path: str) -> str:
        """
        Read a file and return its content.

        Args:
            file_path: Path to the file

        Returns:
            File content
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return ""

            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return ""

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from content.

        Args:
            content: Content to extract metadata from

        Returns:
            Dictionary with metadata
        """
        # Default implementation (to be overridden by subclasses)
        return {"title": "", "description": "", "type": "documentation"}
