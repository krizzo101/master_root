"""
Base processor interface for opsvi-rag.

Provides abstract base classes and common functionality for document processors.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class ProcessorError(ComponentError):
    """Raised when document processing fails."""


class ProcessorType(str, Enum):
    """Supported processor types."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    JSON = "json"
    WEB = "web"
    EMAIL = "email"


class ProcessingStatus(str, Enum):
    """Processing status values."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProcessingMetadata:
    """Metadata extracted during document processing."""

    title: str | None = None
    author: str | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None
    language: str | None = None
    page_count: int | None = None
    word_count: int | None = None
    file_size: int | None = None
    mime_type: str | None = None
    encoding: str | None = None
    custom_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of document processing."""

    content: str
    metadata: ProcessingMetadata
    status: ProcessingStatus
    error_message: str | None = None
    processing_time: float = 0.0
    extracted_text: str | None = None
    structured_data: dict[str, Any] | None = None
    links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)


class ProcessorConfig(BaseModel):
    """Base configuration for document processors."""

    processor_type: ProcessorType
    max_file_size: int = Field(
        default=100 * 1024 * 1024, description="Max file size in bytes"
    )
    timeout: float = Field(default=300.0, description="Processing timeout in seconds")
    extract_metadata: bool = Field(
        default=True, description="Extract document metadata"
    )
    extract_links: bool = Field(
        default=True, description="Extract links from documents"
    )
    extract_images: bool = Field(default=True, description="Extract image references")
    extract_tables: bool = Field(default=True, description="Extract table data")
    clean_text: bool = Field(default=True, description="Clean and normalize text")
    preserve_formatting: bool = Field(
        default=False, description="Preserve original formatting"
    )
    custom_options: dict[str, Any] = Field(
        default_factory=dict, description="Processor-specific options"
    )


class BaseProcessor(BaseComponent, ABC):
    """Abstract base class for document processors."""

    def __init__(self, config: ProcessorConfig, **kwargs):
        """
        Initialize the processor.

        Args:
            config: Processor configuration
            **kwargs: Additional arguments
        """
        super().__init__(**kwargs)
        self.config = config
        self.logger = get_logger(f"{self.__class__.__name__}")

    @abstractmethod
    async def can_process(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the processor can handle this file type
        """
        pass

    @abstractmethod
    async def process(self, file_path: Path) -> ProcessingResult:
        """
        Process a document file.

        Args:
            file_path: Path to the file to process

        Returns:
            Processing result with extracted content and metadata

        Raises:
            ProcessorError: If processing fails
        """
        pass

    async def process_with_timeout(self, file_path: Path) -> ProcessingResult:
        """
        Process a document with timeout.

        Args:
            file_path: Path to the file to process

        Returns:
            Processing result

        Raises:
            ProcessorError: If processing fails or times out
        """
        try:
            return await asyncio.wait_for(
                self.process(file_path), timeout=self.config.timeout
            )
        except TimeoutError:
            raise ProcessorError(f"Processing timed out after {self.config.timeout}s")

    def _validate_file_size(self, file_path: Path) -> None:
        """
        Validate file size against configuration limits.

        Args:
            file_path: Path to the file to validate

        Raises:
            ProcessorError: If file is too large
        """
        if not file_path.exists():
            raise ProcessorError(f"File not found: {file_path}")

        file_size = file_path.stat().st_size
        if file_size > self.config.max_file_size:
            raise ProcessorError(
                f"File too large: {file_size} bytes (max: {self.config.max_file_size})"
            )

    def _extract_basic_metadata(self, file_path: Path) -> ProcessingMetadata:
        """
        Extract basic file metadata.

        Args:
            file_path: Path to the file

        Returns:
            Basic metadata
        """
        stat = file_path.stat()
        return ProcessingMetadata(
            file_size=stat.st_size,
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
            mime_type=self._detect_mime_type(file_path),
        )

    def _detect_mime_type(self, file_path: Path) -> str | None:
        """
        Detect MIME type of the file.

        Args:
            file_path: Path to the file

        Returns:
            MIME type or None if detection fails
        """
        import mimetypes

        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not self.config.clean_text:
            return text

        # Remove excessive whitespace
        text = " ".join(text.split())

        # Remove control characters
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t\r")

        return text.strip()

    async def health_check(self) -> bool:
        """
        Perform a health check on the processor.

        Returns:
            True if the processor is healthy
        """
        try:
            # Basic health check - processor can be instantiated
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
