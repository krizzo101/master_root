# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Base File Processor","description":"This module defines the base FileProcessor class that all file type-specific processors must implement.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and functions for file processing.","line_start":3,"line_end":15},{"name":"FileProcessor Class","description":"Defines the base class for file processors with initialization and methods for structure analysis, file map generation, and validation.","line_start":16,"line_end":80},{"name":"get_processor_for_file Function","description":"Factory function to get the appropriate processor for a file based on its type.","line_start":81,"line_end":103}],"key_elements":[{"name":"FileProcessor","description":"Base class for file processors.","line":16},{"name":"__init__","description":"Constructor for the FileProcessor class.","line":19},{"name":"analyze_structure","description":"Analyzes the file structure to provide hints for the LLM.","line":27},{"name":"generate_file_map","description":"Generates a file map for the given content.","line":39},{"name":"validate_generated_map","description":"Validates the generated file map for accuracy.","line":55},{"name":"get_processor_for_file","description":"Factory function to get the appropriate processor for a file.","line":81}]}
"""
# FILE_MAP_END

"""
Base file processor for genfilemap.

This module defines the base FileProcessor class that all file type-specific processors must implement.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json

from genfilemap.utils.file_utils import (
    get_file_type,
)
from genfilemap.api.base import APIClient
from genfilemap.models.schemas import validate_file_map_json, validate_line_numbers


class FileProcessor:
    """Base class for file processors"""

    def __init__(self, file_path: str, api_client: APIClient, model: str):
        """Initialize the file processor with file path and API client"""
        self.file_path = file_path
        self.api_client = api_client
        self.model = model
        self.file_type = get_file_type(file_path)

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
        self, content: str, comment_style: Tuple[str, str, str]
    ) -> Optional[str]:
        """
        Generate a file map for the given content.

        Args:
            content: The file content to generate a map for
            comment_style: The comment style tuple (start_multi, end_multi, single_line)

        Returns:
            The generated file map or None if the existing map is valid and up-to-date
        """
        # This should be implemented by subclasses
        raise NotImplementedError("Must be implemented by subclass")

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
            print(f"Validation error for {self.file_path}: {str(e)}")
            return False


def get_processor_for_file(
    file_path: str, api_client: APIClient, model: str
) -> FileProcessor:
    """
    Factory function to get the appropriate processor for a file.

    Args:
        file_path: Path to the file
        api_client: API client for LLM requests
        model: Model to use for LLM requests

    Returns:
        An instance of the appropriate FileProcessor subclass
    """
    file_type = get_file_type(file_path)

    # Import here to avoid circular imports
    from genfilemap.processors.code_processor import CodeFileProcessor
    from genfilemap.processors.doc_processor import DocumentationFileProcessor

    # Select processor based on file type
    if file_type == "documentation":
        return DocumentationFileProcessor(file_path, api_client, model)
    else:
        # Default to code processor for all code-like files
        return CodeFileProcessor(file_path, api_client, model)
