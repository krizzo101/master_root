# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Markdown Extractor Module","description":"This module provides functionality to extract content from Markdown files.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary libraries and modules for the Markdown extractor functionality.","line_start":3,"line_end":12},{"name":"MarkdownExtractor Class","description":"Class that implements methods to extract content from Markdown files.","line_start":15,"line_end":181}],"key_elements":[{"name":"MarkdownExtractor","description":"Class for extracting content from Markdown files.","line":16},{"name":"validate_source","description":"Method to validate if the source is a Markdown file.","line":19},{"name":"extract","description":"Method to extract content from a Markdown file.","line":31},{"name":"_extract_frontmatter_and_content","description":"Method to extract frontmatter and content from Markdown.","line":72},{"name":"_parse_sections","description":"Method to parse Markdown content into sections based on headers.","line":100},{"name":"_extract_metadata","description":"Method to extract metadata from Markdown content.","line":153}]}
"""
# FILE_MAP_END

"""
Markdown Extractor Module.

This module provides functionality to extract content from Markdown files.
"""

import re
import yaml
import logging
from typing import Dict, Any, List, Tuple, Optional

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class MarkdownExtractor(BaseExtractor):
    """Extract content from Markdown files."""

    def validate_source(self, source_path: str) -> bool:
        """
        Validate if the source is a Markdown file.

        Args:
            source_path: Path to the source file

        Returns:
            True if the source is a valid Markdown file, False otherwise
        """
        return source_path.lower().endswith((".md", ".markdown", ".mdown"))

    def extract(self, source_path: str) -> Dict[str, Any]:
        """
        Extract content from a Markdown file.

        Args:
            source_path: Path to the Markdown file

        Returns:
            Dictionary with extracted content
        """
        # Read the file
        content = self._read_file(source_path)
        if not content:
            return {"status": "error", "error": f"Could not read file: {source_path}"}

        # Extract frontmatter and content
        frontmatter, main_content = self._extract_frontmatter_and_content(content)

        # Parse sections
        sections = self._parse_sections(main_content)

        # Extract metadata
        metadata = self._extract_metadata(content)
        metadata.update(frontmatter)

        # Create result
        result = {
            "status": "success",
            "source_path": source_path,
            "content": content,
            "frontmatter": frontmatter,
            "main_content": main_content,
            "sections": sections,
            "metadata": metadata,
        }

        return result

    def _extract_frontmatter_and_content(
        self, content: str
    ) -> Tuple[Dict[str, Any], str]:
        """
        Extract frontmatter and content from Markdown.

        Args:
            content: Markdown content

        Returns:
            Tuple of (frontmatter dict, content without frontmatter)
        """
        frontmatter = {}
        main_content = content

        # Look for YAML frontmatter
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if frontmatter_match:
            frontmatter_yaml = frontmatter_match.group(1)
            try:
                frontmatter = yaml.safe_load(frontmatter_yaml) or {}
            except Exception as e:
                logger.warning(f"Error parsing frontmatter: {str(e)}")
                frontmatter = {}

            # Remove frontmatter from content
            main_content = content[frontmatter_match.end() :]

        return frontmatter, main_content

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """
        Parse Markdown content into sections based on headers.

        Args:
            content: Markdown content

        Returns:
            Dictionary with section name as key and section content as value
        """
        sections = {}

        # Find all headers (## Header)
        headers = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)

        if not headers:
            # If no headers, treat the whole content as one section
            sections["main"] = content.strip()
            return sections

        # Process each header and its content
        for i, (hashes, header) in enumerate(headers):
            header_level = len(hashes)
            header_text = header.strip()

            # Only process level 2 headers (##) as main sections
            if header_level != 2:
                continue

            # Find the content for this section
            start_pos = content.find(f"{hashes} {header}")
            if start_pos == -1:
                continue

            # Move past the header
            start_pos = content.find("\n", start_pos) + 1

            # Find the end of this section (next header of same or higher level or end of content)
            end_pos = len(content)
            for j, (next_hashes, next_header) in enumerate(headers[i + 1 :], i + 1):
                next_level = len(next_hashes)
                if next_level <= header_level:
                    next_pos = content.find(f"{next_hashes} {next_header}")
                    if next_pos != -1 and next_pos < end_pos:
                        end_pos = next_pos
                        break

            # Extract section content
            section_content = content[start_pos:end_pos].strip()
            sections[header_text.lower()] = section_content

        return sections

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from Markdown content.

        Args:
            content: Markdown content

        Returns:
            Dictionary with metadata
        """
        metadata = super()._extract_metadata(content)

        # Try to extract title from first level 1 header
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Try to extract description from first paragraph after title
        if "title" in metadata and metadata["title"]:
            title_pos = content.find(f"# {metadata['title']}")
            if title_pos != -1:
                # Find first paragraph after title
                para_start = content.find("\n\n", title_pos) + 2
                para_end = content.find("\n\n", para_start)
                if para_end != -1:
                    para = content[para_start:para_end].strip()
                    if para and not para.startswith("#"):
                        metadata["description"] = para

        return metadata
