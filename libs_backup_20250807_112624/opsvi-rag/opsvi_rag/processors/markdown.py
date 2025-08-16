"""
Markdown processor for opsvi-rag.

Handles markdown files with link extraction, code block handling, and structure preservation.
"""

import re
import time
from pathlib import Path

from pydantic import Field

from .base import (
    BaseProcessor,
    ProcessingMetadata,
    ProcessingResult,
    ProcessingStatus,
    ProcessorConfig,
    ProcessorType,
)


class MarkdownProcessorConfig(ProcessorConfig):
    """Configuration for markdown processor."""

    processor_type: ProcessorType = Field(
        default=ProcessorType.MARKDOWN, description="Processor type"
    )
    extract_links: bool = Field(default=True, description="Extract links from markdown")
    extract_code_blocks: bool = Field(default=True, description="Extract code blocks")
    extract_images: bool = Field(default=True, description="Extract image references")
    extract_headers: bool = Field(default=True, description="Extract header structure")
    preserve_formatting: bool = Field(
        default=False, description="Preserve markdown formatting"
    )
    extract_frontmatter: bool = Field(
        default=True, description="Extract YAML frontmatter"
    )
    clean_html_tags: bool = Field(
        default=True, description="Clean HTML tags from content"
    )


class MarkdownProcessor(BaseProcessor):
    """Processor for markdown files."""

    def __init__(self, config: MarkdownProcessorConfig, **kwargs):
        """
        Initialize markdown processor.

        Args:
            config: Markdown processor configuration
            **kwargs: Additional arguments
        """
        super().__init__(config, **kwargs)
        self.config = config

        # Regex patterns for markdown elements
        self.header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        self.link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        self.image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
        self.code_block_pattern = re.compile(r"```[\w]*\n(.*?)\n```", re.DOTALL)
        self.inline_code_pattern = re.compile(r"`([^`]+)`")
        self.bold_pattern = re.compile(r"\*\*([^*]+)\*\*")
        self.italic_pattern = re.compile(r"\*([^*]+)\*")
        self.html_tag_pattern = re.compile(r"<[^>]+>")

    async def can_process(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the processor can handle this file type
        """
        if not file_path.exists():
            return False

        # Check file extension
        markdown_extensions = {".md", ".markdown", ".mdown", ".mkd"}
        if file_path.suffix.lower() in markdown_extensions:
            return True

        # Check MIME type
        mime_type = self._detect_mime_type(file_path)
        if mime_type in ["text/markdown", "text/x-markdown"]:
            return True

        return False

    async def process(self, file_path: Path) -> ProcessingResult:
        """
        Process a markdown file.

        Args:
            file_path: Path to the file to process

        Returns:
            Processing result with extracted content and metadata

        Raises:
            ProcessorError: If processing fails
        """
        start_time = time.time()

        try:
            # Validate file
            self._validate_file_size(file_path)

            # Extract basic metadata
            metadata = self._extract_basic_metadata(file_path)

            # Read file content
            content = await self._read_file_content(file_path)

            # Extract frontmatter if configured
            frontmatter = {}
            if self.config.extract_frontmatter:
                frontmatter = self._extract_frontmatter(content)
                content = self._remove_frontmatter(content)

            # Extract markdown elements
            extracted_data = await self._extract_markdown_elements(content)

            # Extract additional metadata
            metadata = await self._extract_markdown_metadata(
                content, metadata, frontmatter
            )

            # Clean content if configured
            if self.config.clean_text:
                content = self._clean_markdown_content(content)

            processing_time = time.time() - start_time

            return ProcessingResult(
                content=content,
                metadata=metadata,
                status=ProcessingStatus.COMPLETED,
                processing_time=processing_time,
                extracted_text=content,
                structured_data=extracted_data,
                links=extracted_data.get("links", []),
                images=extracted_data.get("images", []),
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Failed to process markdown file {file_path}: {e}")

            return ProcessingResult(
                content="",
                metadata=ProcessingMetadata(),
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=processing_time,
            )

    async def _read_file_content(self, file_path: Path) -> str:
        """
        Read markdown file content.

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            ProcessorError: If reading fails
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with encoding detection
            return await self._read_with_encoding_detection(file_path)

    def _extract_frontmatter(self, content: str) -> dict:
        """
        Extract YAML frontmatter from markdown content.

        Args:
            content: Markdown content

        Returns:
            Frontmatter as dictionary
        """
        import yaml

        frontmatter_pattern = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
        match = frontmatter_pattern.match(content)

        if match:
            try:
                frontmatter_text = match.group(1)
                return yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError:
                self.logger.warning("Failed to parse YAML frontmatter")
                return {}

        return {}

    def _remove_frontmatter(self, content: str) -> str:
        """
        Remove YAML frontmatter from markdown content.

        Args:
            content: Markdown content with frontmatter

        Returns:
            Content without frontmatter
        """
        frontmatter_pattern = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
        return frontmatter_pattern.sub("", content)

    async def _extract_markdown_elements(self, content: str) -> dict:
        """
        Extract various elements from markdown content.

        Args:
            content: Markdown content

        Returns:
            Dictionary of extracted elements
        """
        extracted_data = {
            "headers": [],
            "links": [],
            "images": [],
            "code_blocks": [],
            "inline_code": [],
            "tables": [],
            "lists": [],
        }

        # Extract headers
        if self.config.extract_headers:
            headers = self.header_pattern.findall(content)
            extracted_data["headers"] = [
                {"level": len(level), "text": text.strip()} for level, text in headers
            ]

        # Extract links
        if self.config.extract_links:
            links = self.link_pattern.findall(content)
            extracted_data["links"] = [
                {"text": text, "url": url} for text, url in links
            ]

        # Extract images
        if self.config.extract_images:
            images = self.image_pattern.findall(content)
            extracted_data["images"] = [{"alt": alt, "src": src} for alt, src in images]

        # Extract code blocks
        if self.config.extract_code_blocks:
            code_blocks = self.code_block_pattern.findall(content)
            extracted_data["code_blocks"] = [
                {"content": block.strip(), "type": "block"} for block in code_blocks
            ]

            # Extract inline code
            inline_code = self.inline_code_pattern.findall(content)
            extracted_data["inline_code"] = [
                {"content": code, "type": "inline"} for code in inline_code
            ]

        # Extract tables (basic regex-based extraction)
        table_pattern = re.compile(
            r"\|(.+)\|\n\|[\s\-:|]+\|\n((?:\|.+\|\n?)+)", re.MULTILINE
        )
        tables = table_pattern.findall(content)
        extracted_data["tables"] = [
            {"headers": headers.strip(), "rows": rows.strip()}
            for headers, rows in tables
        ]

        # Extract lists
        list_pattern = re.compile(r"^[\s]*[-*+]\s+(.+)$", re.MULTILINE)
        lists = list_pattern.findall(content)
        extracted_data["lists"] = [item.strip() for item in lists]

        return extracted_data

    async def _extract_markdown_metadata(
        self, content: str, metadata: ProcessingMetadata, frontmatter: dict
    ) -> ProcessingMetadata:
        """
        Extract metadata from markdown content.

        Args:
            content: Markdown content
            metadata: Base metadata
            frontmatter: Extracted frontmatter

        Returns:
            Enhanced metadata
        """
        # Extract from frontmatter
        if frontmatter:
            metadata.title = frontmatter.get("title") or metadata.title
            metadata.author = frontmatter.get("author") or metadata.author
            metadata.language = frontmatter.get("language") or metadata.language

            # Handle dates
            if "date" in frontmatter:
                try:
                    from datetime import datetime

                    if isinstance(frontmatter["date"], str):
                        metadata.created_date = datetime.fromisoformat(
                            frontmatter["date"].replace("Z", "+00:00")
                        )
                    else:
                        metadata.created_date = frontmatter["date"]
                except (ValueError, TypeError):
                    pass

        # Extract title from first header if not in frontmatter
        if not metadata.title:
            headers = self.header_pattern.findall(content)
            if headers:
                metadata.title = headers[0][1].strip()

        # Count words (excluding code blocks)
        clean_content = self._remove_code_blocks(content)
        words = clean_content.split()
        metadata.word_count = len(words)

        # Count headers
        header_count = len(self.header_pattern.findall(content))
        metadata.custom_fields["header_count"] = header_count

        # Count links
        link_count = len(self.link_pattern.findall(content))
        metadata.custom_fields["link_count"] = link_count

        # Count images
        image_count = len(self.image_pattern.findall(content))
        metadata.custom_fields["image_count"] = image_count

        return metadata

    def _remove_code_blocks(self, content: str) -> str:
        """
        Remove code blocks from content for word counting.

        Args:
            content: Markdown content

        Returns:
            Content without code blocks
        """
        # Remove code blocks
        content = self.code_block_pattern.sub("", content)

        # Remove inline code
        content = self.inline_code_pattern.sub("", content)

        return content

    def _clean_markdown_content(self, content: str) -> str:
        """
        Clean and normalize markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Cleaned markdown content
        """
        if not self.config.preserve_formatting:
            # Remove markdown formatting
            content = self.bold_pattern.sub(r"\1", content)
            content = self.italic_pattern.sub(r"\1", content)
            content = self.inline_code_pattern.sub(r"\1", content)

            # Remove headers (keep text)
            content = self.header_pattern.sub(r"\2", content)

            # Remove link formatting (keep text)
            content = self.link_pattern.sub(r"\1", content)

            # Remove image formatting
            content = self.image_pattern.sub("", content)

            # Remove code blocks
            content = self.code_block_pattern.sub("", content)

        # Clean HTML tags if configured
        if self.config.clean_html_tags:
            content = self.html_tag_pattern.sub("", content)

        # Apply base text cleaning
        content = self._clean_text(content)

        return content
