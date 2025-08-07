"""
Text processor for opsvi-rag.

Handles plain text files with encoding detection and text cleaning.
"""

import time
from pathlib import Path

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


class TextProcessorConfig(ProcessorConfig):
    """Configuration for text processor."""

    processor_type: ProcessorType = Field(
        default=ProcessorType.TEXT, description="Processor type"
    )
    detect_encoding: bool = Field(default=True, description="Auto-detect text encoding")
    encoding: str | None = Field(default=None, description="Force specific encoding")
    remove_empty_lines: bool = Field(default=True, description="Remove empty lines")
    normalize_whitespace: bool = Field(default=True, description="Normalize whitespace")
    extract_paragraphs: bool = Field(
        default=True, description="Extract paragraph structure"
    )


class TextProcessor(BaseProcessor):
    """Processor for plain text files."""

    def __init__(self, config: TextProcessorConfig, **kwargs):
        """
        Initialize text processor.

        Args:
            config: Text processor configuration
            **kwargs: Additional arguments
        """
        super().__init__(config, **kwargs)
        self.config = config

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
        text_extensions = {".txt", ".text", ".md", ".markdown", ".log", ".csv", ".tsv"}
        if file_path.suffix.lower() in text_extensions:
            return True

        # Check MIME type
        mime_type = self._detect_mime_type(file_path)
        if mime_type and mime_type.startswith("text/"):
            return True

        return False

    async def process(self, file_path: Path) -> ProcessingResult:
        """
        Process a text file.

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

            # Extract additional metadata
            metadata = await self._extract_text_metadata(content, metadata)

            # Clean text if configured
            if self.config.clean_text:
                content = self._clean_text_content(content)

            # Extract paragraphs if configured
            paragraphs = []
            if self.config.extract_paragraphs:
                paragraphs = self._extract_paragraphs(content)

            processing_time = time.time() - start_time

            return ProcessingResult(
                content=content,
                metadata=metadata,
                status=ProcessingStatus.COMPLETED,
                processing_time=processing_time,
                extracted_text=content,
                structured_data={
                    "paragraphs": paragraphs,
                    "word_count": metadata.word_count,
                    "line_count": len(content.splitlines()),
                },
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Failed to process text file {file_path}: {e}")

            return ProcessingResult(
                content="",
                metadata=ProcessingMetadata(),
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=processing_time,
            )

    async def _read_file_content(self, file_path: Path) -> str:
        """
        Read file content with encoding detection.

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            ProcessorError: If reading fails
        """
        if self.config.encoding:
            # Use specified encoding
            try:
                return file_path.read_text(encoding=self.config.encoding)
            except UnicodeDecodeError as e:
                raise ProcessorError(
                    f"Failed to read file with encoding {self.config.encoding}: {e}"
                )

        if self.config.detect_encoding:
            # Auto-detect encoding
            return await self._read_with_encoding_detection(file_path)
        else:
            # Use default encoding
            try:
                return file_path.read_text()
            except UnicodeDecodeError as e:
                raise ProcessorError(f"Failed to read file with default encoding: {e}")

    async def _read_with_encoding_detection(self, file_path: Path) -> str:
        """
        Read file with automatic encoding detection.

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            ProcessorError: If reading fails
        """
        import chardet

        # Read raw bytes
        raw_data = file_path.read_bytes()

        # Detect encoding
        result = chardet.detect(raw_data)
        encoding = result["encoding"]
        confidence = result["confidence"]

        if not encoding or confidence < 0.7:
            # Try common encodings
            common_encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]

            for enc in common_encodings:
                try:
                    return raw_data.decode(enc)
                except UnicodeDecodeError:
                    continue

            raise ProcessorError("Could not detect file encoding")

        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError as e:
            raise ProcessorError(
                f"Failed to decode with detected encoding {encoding}: {e}"
            )

    async def _extract_text_metadata(
        self, content: str, metadata: ProcessingMetadata
    ) -> ProcessingMetadata:
        """
        Extract metadata from text content.

        Args:
            content: Text content
            metadata: Base metadata

        Returns:
            Enhanced metadata
        """
        # Count words
        words = content.split()
        metadata.word_count = len(words)

        # Detect language (basic implementation)
        metadata.language = self._detect_language(content)

        # Try to extract title from first line
        lines = content.splitlines()
        if lines and lines[0].strip():
            first_line = lines[0].strip()
            if len(first_line) < 100 and not first_line.endswith("."):
                metadata.title = first_line

        return metadata

    def _detect_language(self, text: str) -> str | None:
        """
        Basic language detection.

        Args:
            text: Text to analyze

        Returns:
            Language code or None
        """
        # Simple heuristic-based language detection
        # This is a basic implementation - in production, use a proper language detection library

        # Count common English words
        english_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        words = set(text.lower().split())
        english_count = len(words.intersection(english_words))

        if english_count > 0:
            return "en"

        return None

    def _clean_text_content(self, content: str) -> str:
        """
        Clean and normalize text content.

        Args:
            content: Raw text content

        Returns:
            Cleaned text content
        """
        # Remove empty lines if configured
        if self.config.remove_empty_lines:
            lines = [line for line in content.splitlines() if line.strip()]
            content = "\n".join(lines)

        # Normalize whitespace if configured
        if self.config.normalize_whitespace:
            content = " ".join(content.split())

        return content.strip()

    def _extract_paragraphs(self, content: str) -> list[str]:
        """
        Extract paragraphs from text content.

        Args:
            content: Text content

        Returns:
            List of paragraphs
        """
        # Split by double newlines (paragraph breaks)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        # If no double newlines, split by single newlines
        if not paragraphs:
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

        return paragraphs
