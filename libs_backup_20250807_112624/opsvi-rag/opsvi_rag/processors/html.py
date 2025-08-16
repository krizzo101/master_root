"""
HTML processor for opsvi-rag.

Handles HTML files with BeautifulSoup integration, content extraction, and metadata parsing.
"""

import time
from pathlib import Path
from urllib.parse import urljoin

from opsvi_foundation import get_logger
from pydantic import Field

from .base import (
    BaseProcessor,
    ProcessingMetadata,
    ProcessingResult,
    ProcessingStatus,
    ProcessorConfig,
    ProcessorError,
    ProcessorType,
)

try:
    from bs4 import BeautifulSoup

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


class HTMLProcessorConfig(ProcessorConfig):
    """Configuration for HTML processor."""

    processor_type: ProcessorType = Field(
        default=ProcessorType.HTML, description="Processor type"
    )
    extract_links: bool = Field(default=True, description="Extract and normalize links")
    extract_images: bool = Field(default=True, description="Extract image information")
    extract_metadata: bool = Field(
        default=True, description="Extract meta tags and structured data"
    )
    remove_scripts: bool = Field(default=True, description="Remove script tags")
    remove_styles: bool = Field(default=True, description="Remove style tags")
    remove_comments: bool = Field(default=True, description="Remove HTML comments")
    preserve_structure: bool = Field(
        default=True, description="Preserve document structure"
    )
    base_url: str | None = Field(
        default=None, description="Base URL for link normalization"
    )
    allowed_tags: list[str] | None = Field(
        default=None, description="Allowed HTML tags"
    )
    block_tags: list[str] = Field(
        default=[
            "p",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "section",
            "article",
            "header",
            "footer",
        ],
        description="Tags that create content blocks",
    )


class HTMLProcessor(BaseProcessor):
    """HTML document processor with BeautifulSoup integration."""

    def __init__(self, config: HTMLProcessorConfig):
        """Initialize HTML processor."""
        super().__init__(config)
        self.config = config
        self.logger = get_logger(__name__)

        if not BEAUTIFULSOUP_AVAILABLE:
            raise ProcessorError(
                "BeautifulSoup is required for HTML processing. Install with: pip install beautifulsoup4"
            )

    def can_process(self, file_path: Path) -> bool:
        """Check if file can be processed."""
        return file_path.suffix.lower() in [".html", ".htm", ".xhtml"]

    def _extract_metadata(self, soup: BeautifulSoup) -> dict[str, any]:
        """Extract metadata from HTML."""
        metadata = {}

        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[f"meta_{name}"] = content

        # Title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        # Structured data (JSON-LD)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json

                data = json.loads(script.string)
                metadata["structured_data"] = data
            except (json.JSONDecodeError, AttributeError):
                continue

        # Open Graph tags
        og_tags = {}
        for meta in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
            property_name = meta.get("property", "").replace("og:", "")
            content = meta.get("content")
            if content:
                og_tags[property_name] = content

        if og_tags:
            metadata["open_graph"] = og_tags

        return metadata

    def _extract_links(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Extract and normalize links."""
        links = []

        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()
            if not href:
                continue

            # Normalize URL if base_url is provided
            if self.config.base_url and not href.startswith(
                ("http://", "https://", "mailto:", "tel:")
            ):
                href = urljoin(self.config.base_url, href)

            link_info = {
                "url": href,
                "text": link.get_text(strip=True),
                "title": link.get("title", ""),
                "rel": link.get("rel", []),
            }
            links.append(link_info)

        return links

    def _extract_images(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Extract image information."""
        images = []

        for img in soup.find_all("img"):
            src = img.get("src", "").strip()
            if not src:
                continue

            # Normalize URL if base_url is provided
            if self.config.base_url and not src.startswith(
                ("http://", "https://", "data:")
            ):
                src = urljoin(self.config.base_url, src)

            image_info = {
                "src": src,
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
                "width": img.get("width", ""),
                "height": img.get("height", ""),
            }
            images.append(image_info)

        return images

    def _clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Clean HTML by removing unwanted elements."""
        # Remove scripts
        if self.config.remove_scripts:
            for script in soup.find_all("script"):
                script.decompose()

        # Remove styles
        if self.config.remove_styles:
            for style in soup.find_all("style"):
                style.decompose()

        # Remove comments
        if self.config.remove_comments:
            from bs4 import Comment

            for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()

        return soup

    def _extract_text_blocks(self, soup: BeautifulSoup) -> list[str]:
        """Extract text content in logical blocks."""
        blocks = []

        # Find all block-level elements
        for tag in soup.find_all(self.config.block_tags):
            text = tag.get_text(strip=True)
            if text:
                blocks.append(text)

        # If no blocks found, extract all text
        if not blocks:
            text = soup.get_text(strip=True)
            if text:
                blocks = [text]

        return blocks

    def process(self, file_path: Path) -> ProcessingResult:
        """Process HTML file."""
        start_time = time.time()

        try:
            # Read file content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")

            # Clean HTML
            soup = self._clean_html(soup)

            # Extract content
            text_blocks = self._extract_text_blocks(soup)
            content_text = "\n\n".join(text_blocks)

            # Extract metadata
            metadata = {}
            if self.config.extract_metadata:
                metadata = self._extract_metadata(soup)

            # Extract links
            links = []
            if self.config.extract_links:
                links = self._extract_links(soup)
                metadata["links"] = links

            # Extract images
            images = []
            if self.config.extract_images:
                images = self._extract_images(soup)
                metadata["images"] = images

            # Create processing metadata
            processing_metadata = ProcessingMetadata(
                file_size=file_path.stat().st_size,
                processing_time=time.time() - start_time,
                text_length=len(content_text),
                block_count=len(text_blocks),
                link_count=len(links),
                image_count=len(images),
                metadata_count=len(metadata),
            )

            return ProcessingResult(
                content=content_text,
                metadata=metadata,
                processing_metadata=processing_metadata,
                status=ProcessingStatus.SUCCESS,
                error_message=None,
            )

        except Exception as e:
            self.logger.error(f"Error processing HTML file {file_path}: {e}")
            return ProcessingResult(
                content="",
                metadata={},
                processing_metadata=ProcessingMetadata(
                    file_size=file_path.stat().st_size if file_path.exists() else 0,
                    processing_time=time.time() - start_time,
                    text_length=0,
                    block_count=0,
                    link_count=0,
                    image_count=0,
                    metadata_count=0,
                ),
                status=ProcessingStatus.ERROR,
                error_message=str(e),
            )
