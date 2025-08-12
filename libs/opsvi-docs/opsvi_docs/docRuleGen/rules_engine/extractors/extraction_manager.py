# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Extraction Manager Module","description":"This module provides functionality to manage the extraction process.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and classes for the extraction manager.","line_start":3,"line_end":14},{"name":"ExtractionManager Class","description":"Defines the ExtractionManager class responsible for managing the extraction process.","line_start":16,"line_end":78},{"name":"Error Handling","description":"Handles errors related to source file extraction.","line_start":44,"line_end":78}],"key_elements":[{"name":"ExtractionManager","description":"Class that manages the extraction process.","line":17},{"name":"__init__","description":"Constructor for the ExtractionManager class.","line":20},{"name":"register_extractor","description":"Method to register an extractor.","line":34},{"name":"extract","description":"Method to extract content from a source file.","line":44},{"name":"_find_extractor","description":"Method to find a suitable extractor for the source.","line":76},{"name":"logger","description":"Logger instance for logging messages.","line":14}]}
"""
# FILE_MAP_END

"""
Extraction Manager Module.

This module provides functionality to manage the extraction process.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Type

from .base_extractor import BaseExtractor
from .markdown_extractor import MarkdownExtractor
from .text_extractor import TextExtractor

logger = logging.getLogger(__name__)


class ExtractionManager:
    """Manage the extraction process."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the extraction manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._extractors = []

        # Register default extractors
        self.register_extractor(MarkdownExtractor(config))
        self.register_extractor(TextExtractor(config))

    def register_extractor(self, extractor: BaseExtractor) -> None:
        """
        Register an extractor.

        Args:
            extractor: The extractor to register
        """
        self._extractors.append(extractor)
        logger.debug(f"Registered extractor: {extractor.__class__.__name__}")

    def extract(self, source_path: str) -> Dict[str, Any]:
        """
        Extract content from the source.

        Args:
            source_path: Path to the source file

        Returns:
            Dictionary with extracted content
        """
        if not os.path.exists(source_path):
            logger.error(f"Source file not found: {source_path}")
            return {"status": "error", "error": f"Source file not found: {source_path}"}

        # Find suitable extractor
        extractor = self._find_extractor(source_path)
        if not extractor:
            logger.error(f"No suitable extractor found for: {source_path}")
            return {
                "status": "error",
                "error": f"No suitable extractor found for: {source_path}",
            }

        # Extract content
        logger.info(
            f"Extracting content from {source_path} using {extractor.__class__.__name__}"
        )
        result = extractor.extract(source_path)

        return result

    def _find_extractor(self, source_path: str) -> Optional[BaseExtractor]:
        """
        Find a suitable extractor for the source.

        Args:
            source_path: Path to the source file

        Returns:
            Suitable extractor or None if not found
        """
        for extractor in self._extractors:
            if extractor.validate_source(source_path):
                return extractor

        return None
