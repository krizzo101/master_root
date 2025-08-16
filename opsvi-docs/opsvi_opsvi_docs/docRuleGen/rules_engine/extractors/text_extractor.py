# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Text Extractor Module","description":"This module provides functionality to extract content from plain text files.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Import necessary modules and libraries for the text extraction functionality.","line_start":3,"line_end":12},{"name":"TextExtractor Class","description":"Class that implements the text extraction logic from plain text files.","line_start":14,"line_end":156},{"name":"validate_source Method","description":"Method to validate if the provided source path is a valid text file.","line_start":18,"line_end":41},{"name":"extract Method","description":"Method to extract content from a text file and return it in a structured format.","line_start":48,"line_end":85},{"name":"_parse_sections Method","description":"Method to parse the text content into sections based on empty lines and potential headers.","line_start":83,"line_end":136},{"name":"_extract_metadata Method","description":"Method to extract metadata from the text content.","line_start":136,"line_end":156}],"key_elements":[{"name":"TextExtractor","description":"Class responsible for extracting content from text files.","line":16},{"name":"validate_source","description":"Method to validate if the source is a text file.","line":19},{"name":"extract","description":"Method to extract content from a text file.","line":49},{"name":"_parse_sections","description":"Method to parse text content into sections.","line":84},{"name":"_extract_metadata","description":"Method to extract metadata from text content.","line":137},{"name":"logger","description":"Logger instance for logging warnings and errors.","line":11}]}
"""
# FILE_MAP_END

"""
Text Extractor Module.

This module provides functionality to extract content from plain text files.
"""

import re
import os
import logging
from typing import Dict, Any, List, Optional

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class TextExtractor(BaseExtractor):
    """Extract content from plain text files."""

    def validate_source(self, source_path: str) -> bool:
        """
        Validate if the source is a text file.

        Args:
            source_path: Path to the source file

        Returns:
            True if the source is a valid text file, False otherwise
        """
        # Check if the file exists and has a text extension
        if not os.path.exists(source_path):
            return False

        # Check if file has a text extension
        text_extensions = (".txt", ".text", ".log", ".md", ".rst", ".asc")
        if source_path.lower().endswith(text_extensions):
            return True

        # Try to detect if the file is text by reading a few bytes
        try:
            with open(source_path, "rb") as f:
                sample = f.read(1024)
                # A simple heuristic: check if the bytes are mostly ASCII
                text_chars = len(
                    [b for b in sample if 32 <= b <= 126 or b in (9, 10, 13)]
                )
                return text_chars / len(sample) > 0.9 if sample else False
        except Exception as e:
            logger.warning(f"Error checking if {source_path} is text: {str(e)}")
            return False

    def extract(self, source_path: str) -> Dict[str, Any]:
        """
        Extract content from a text file.

        Args:
            source_path: Path to the text file

        Returns:
            Dictionary with extracted content
        """
        # Read the file
        content = self._read_file(source_path)
        if not content:
            return {"status": "error", "error": f"Could not read file: {source_path}"}

        # Parse the content into sections based on empty lines
        sections = self._parse_sections(content)

        # Extract metadata
        metadata = self._extract_metadata(content)

        # Create result
        result = {
            "status": "success",
            "source_path": source_path,
            "content": content,
            "sections": sections,
            "metadata": metadata,
        }

        return result

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """
        Parse text content into sections based on empty lines and potential headers.

        Args:
            content: Text content

        Returns:
            Dictionary with section name as key and section content as value
        """
        sections = {}

        # Split by double newlines (paragraphs)
        paragraphs = re.split(r"\n\s*\n", content)

        if not paragraphs:
            sections["main"] = content.strip()
            return sections

        # The first paragraph is often a title/header
        if paragraphs:
            title = paragraphs[0].strip()
            sections["title"] = title

            # Try to detect if there are section headers
            section_name = "main"
            section_content = []

            for i, para in enumerate(paragraphs[1:], 1):
                para = para.strip()

                # Check if paragraph looks like a section header
                # (short, ends with colon, all caps, etc.)
                if len(para) < 50 and (
                    para.endswith(":")
                    or para.isupper()
                    or para.count("\n") == 0
                    and all(c.isupper() for c in para[0:1])
                ):
                    # Store previous section
                    if section_content:
                        sections[section_name] = "\n\n".join(section_content)
                        section_content = []

                    # Set new section name
                    section_name = para.rstrip(":").lower()
                else:
                    # Add to current section
                    section_content.append(para)

            # Add the last section
            if section_content:
                sections[section_name] = "\n\n".join(section_content)

        return sections

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from text content.

        Args:
            content: Text content

        Returns:
            Dictionary with metadata
        """
        metadata = super()._extract_metadata(content)

        # Try to extract title from first line
        lines = content.strip().split("\n")
        if lines:
            metadata["title"] = lines[0].strip()

            # If there's a second non-empty line, use it as description
            if len(lines) > 1:
                for line in lines[1:]:
                    if line.strip():
                        metadata["description"] = line.strip()
                        break

        return metadata
