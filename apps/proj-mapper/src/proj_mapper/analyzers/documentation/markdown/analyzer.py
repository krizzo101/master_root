"""Markdown analyzer implementation.

This module provides the analyzer for Markdown documentation files.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple

from proj_mapper.analyzers.documentation.markdown.elements import (
    detect_code_references,
    detect_markdown_links,
)
from proj_mapper.analyzers.documentation.markdown.parser import MarkdownParser
from proj_mapper.claude_code_adapter import Analyzer
from proj_mapper.models.analysis import DocumentationAnalysisResult
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.file import DiscoveredFile, FileType

# Configure logging
logger = logging.getLogger(__name__)


class MarkdownAnalyzer(Analyzer):
    """Analyzer for Markdown documentation files.

    This class analyzes Markdown files and extracts document structure elements
    like headings, sections, code blocks, and references.
    """

    # File extensions this analyzer can handle
    supported_extensions: ClassVar[Set[str]] = {".md", ".markdown", ".mdown", ".mkd"}

    def __init__(self):
        """Initialize the Markdown analyzer."""
        self.parser = MarkdownParser()

    def can_analyze(self, file: DiscoveredFile) -> bool:
        """Check if this analyzer can analyze the given file.

        Args:
            file: The file to check

        Returns:
            True if this is a Markdown file, False otherwise
        """
        return (
            file.file_type == FileType.MARKDOWN
            or file.get_extension() in self.supported_extensions
        )

    def get_file_filter(self) -> List[str]:
        """Get file patterns for selecting Markdown files.

        Returns:
            List of glob patterns for Markdown files
        """
        return ["**/*.md", "**/*.markdown", "**/*.mdown", "**/*.mkd"]

    def analyze_file(self, file_path: Path, content: str) -> List[DocumentationElement]:
        """Analyze a Markdown file and extract documentation elements.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of extracted documentation elements
        """
        # Get file stat information for modified time
        stat_info = file_path.stat()

        # Create a DiscoveredFile object
        file = DiscoveredFile(
            path=str(file_path),
            relative_path=str(file_path.name),
            file_type=FileType.MARKDOWN,
            size=len(content),
            is_binary=False,
            modified_time=datetime.fromtimestamp(stat_info.st_mtime),
        )

        # Use existing analyze method
        result = self.analyze(file, content)

        # Return elements
        return result.elements if result and hasattr(result, "elements") else []

    def analyze(
        self, file: DiscoveredFile, content: Optional[str] = None
    ) -> DocumentationAnalysisResult:
        """Analyze a Markdown file and extract document structure.

        Args:
            file: The file to analyze
            content: Optional file content (if already loaded)

        Returns:
            Analysis results with extracted documentation elements

        Raises:
            ValueError: If the file cannot be analyzed
        """
        if not self.can_analyze(file):
            raise ValueError(f"Cannot analyze non-Markdown file: {file.relative_path}")

        logger.debug(f"Analyzing Markdown file: {file.relative_path}")

        # Load the file content if not provided
        if content is None:
            try:
                with open(file.path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error reading Markdown file {file.relative_path}: {e}")
                return DocumentationAnalysisResult(
                    file_path=str(file.path),
                    success=False,
                    error_message=f"Error reading file: {str(e)}",
                )

        # Create result object
        result = DocumentationAnalysisResult(file_path=str(file.path))

        try:
            # Extract front matter
            content, metadata = self.parser.extract_front_matter(content)
            if metadata:
                result.metadata = metadata
                if "title" in metadata:
                    result.title = metadata["title"]

            # Parse the Markdown content
            elements = self.parser.parse(content, str(file.path))
            result.elements = elements

            # Analyze element references
            self._analyze_references(elements)

            # Extract title if not already found in metadata
            if not result.title and elements:
                for elem in elements:
                    if elem.element_type == DocumentationType.SECTION:
                        result.title = elem.title
                        break

            # Create a summary based on the first paragraph
            for elem in elements:
                if elem.element_type == DocumentationType.PARAGRAPH:
                    # Use first paragraph as summary
                    summary = elem.content.strip()
                    if summary:
                        # Limit to first sentence or certain length
                        if "." in summary[:100]:
                            summary = summary.split(".")[0] + "."
                        else:
                            summary = summary[:100] + (
                                "..." if len(summary) > 100 else ""
                            )
                        result.summary = summary
                        break

            logger.debug(
                f"Extracted {len(elements)} elements from {file.relative_path}"
            )

        except Exception as e:
            logger.error(f"Error analyzing Markdown file {file.relative_path}: {e}")
            result.success = False
            result.error_message = f"Analysis error: {str(e)}"

        return result

    def _analyze_references(self, elements: List[DocumentationElement]) -> None:
        """Analyze elements to detect references.

        Args:
            elements: List of documentation elements to analyze
        """
        for element in elements:
            # Process paragraphs for Markdown links
            if element.element_type == DocumentationType.PARAGRAPH:
                detect_markdown_links(element)

            # Process code blocks for code references
            elif element.element_type == DocumentationType.CODE_BLOCK:
                detect_code_references(element)
