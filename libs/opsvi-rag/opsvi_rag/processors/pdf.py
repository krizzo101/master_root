"""
PDF processor for opsvi-rag.

Handles PDF files with PyPDF2/pdfplumber integration, OCR support, and metadata extraction.
"""

import time
from pathlib import Path

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
    import PyPDF2

    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class PDFProcessorConfig(ProcessorConfig):
    """Configuration for PDF processor."""

    processor_type: ProcessorType = Field(
        default=ProcessorType.PDF, description="Processor type"
    )
    extract_text: bool = Field(default=True, description="Extract text content")
    extract_images: bool = Field(default=True, description="Extract images for OCR")
    extract_metadata: bool = Field(default=True, description="Extract PDF metadata")
    use_ocr: bool = Field(default=False, description="Use OCR for text extraction")
    ocr_language: str = Field(default="eng", description="OCR language code")
    extract_tables: bool = Field(default=True, description="Extract table data")
    preserve_layout: bool = Field(default=True, description="Preserve document layout")
    page_range: tuple[int, int] | None = Field(
        default=None, description="Page range to process (start, end)"
    )
    password: str | None = Field(default=None, description="PDF password if encrypted")


class PDFProcessor(BaseProcessor):
    """PDF document processor with PyPDF2/pdfplumber integration."""

    def __init__(self, config: PDFProcessorConfig):
        """Initialize PDF processor."""
        super().__init__(config)
        self.config = config
        self.logger = get_logger(__name__)

        if not PYPDF2_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            raise ProcessorError(
                "PDF processing requires either PyPDF2 or pdfplumber. "
                "Install with: pip install PyPDF2 pdfplumber"
            )

        if self.config.use_ocr and not OCR_AVAILABLE:
            raise ProcessorError(
                "OCR requires pytesseract and Pillow. "
                "Install with: pip install pytesseract Pillow"
            )

    def can_process(self, file_path: Path) -> bool:
        """Check if file can be processed."""
        return file_path.suffix.lower() == ".pdf"

    def _extract_metadata_pypdf2(self, file_path: Path) -> dict[str, any]:
        """Extract metadata using PyPDF2."""
        metadata = {}

        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                if self.config.password:
                    reader.decrypt(self.config.password)

                # Document info
                if reader.metadata:
                    metadata.update(reader.metadata)

                # Page count
                metadata["page_count"] = len(reader.pages)

                # Document properties
                metadata["is_encrypted"] = reader.is_encrypted

        except Exception as e:
            self.logger.warning(f"Failed to extract metadata with PyPDF2: {e}")

        return metadata

    def _extract_text_pypdf2(self, file_path: Path) -> str:
        """Extract text using PyPDF2."""
        text_parts = []

        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                if self.config.password:
                    reader.decrypt(self.config.password)

                start_page = 0
                end_page = len(reader.pages)

                if self.config.page_range:
                    start_page = max(0, self.config.page_range[0])
                    end_page = min(len(reader.pages), self.config.page_range[1])

                for page_num in range(start_page, end_page):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        except Exception as e:
            self.logger.warning(f"Failed to extract text with PyPDF2: {e}")

        return "\n\n".join(text_parts)

    def _extract_text_pdfplumber(self, file_path: Path) -> str:
        """Extract text using pdfplumber."""
        text_parts = []
        tables_data = []

        try:
            with pdfplumber.open(file_path, password=self.config.password) as pdf:
                start_page = 0
                end_page = len(pdf.pages)

                if self.config.page_range:
                    start_page = max(0, self.config.page_range[0])
                    end_page = min(len(pdf.pages), self.config.page_range[1])

                for page_num in range(start_page, end_page):
                    page = pdf.pages[page_num]

                    # Extract text
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

                    # Extract tables
                    if self.config.extract_tables:
                        tables = page.extract_tables()
                        if tables:
                            for table_num, table in enumerate(tables):
                                table_text = f"\n--- Table {table_num + 1} on Page {page_num + 1} ---\n"
                                for row in table:
                                    if row and any(cell for cell in row if cell):
                                        table_text += (
                                            " | ".join(
                                                str(cell) if cell else ""
                                                for cell in row
                                            )
                                            + "\n"
                                        )
                                tables_data.append(table_text)

        except Exception as e:
            self.logger.warning(f"Failed to extract text with pdfplumber: {e}")

        # Combine text and tables
        all_content = text_parts + tables_data
        return "\n\n".join(all_content)

    def _extract_images_for_ocr(self, file_path: Path) -> list[str]:
        """Extract images from PDF for OCR processing."""
        ocr_texts = []

        if not OCR_AVAILABLE:
            return ocr_texts

        try:
            with pdfplumber.open(file_path, password=self.config.password) as pdf:
                start_page = 0
                end_page = len(pdf.pages)

                if self.config.page_range:
                    start_page = max(0, self.config.page_range[0])
                    end_page = min(len(pdf.pages), self.config.page_range[1])

                for page_num in range(start_page, end_page):
                    page = pdf.pages[page_num]

                    # Extract images from page
                    images = page.images
                    for img in images:
                        try:
                            # Convert image to PIL Image
                            pil_image = Image.frombytes(
                                img["format"],
                                (img["width"], img["height"]),
                                img["stream"].get_data(),
                            )

                            # Perform OCR
                            ocr_text = pytesseract.image_to_string(
                                pil_image, lang=self.config.ocr_language
                            )

                            if ocr_text.strip():
                                ocr_texts.append(
                                    f"--- OCR Text from Page {page_num + 1} ---\n{ocr_text}"
                                )

                        except Exception as e:
                            self.logger.warning(
                                f"OCR failed for image on page {page_num + 1}: {e}"
                            )

        except Exception as e:
            self.logger.warning(f"Failed to extract images for OCR: {e}")

        return ocr_texts

    def process(self, file_path: Path) -> ProcessingResult:
        """Process PDF file."""
        start_time = time.time()

        try:
            # Extract metadata
            metadata = {}
            if self.config.extract_metadata:
                if PYPDF2_AVAILABLE:
                    metadata = self._extract_metadata_pypdf2(file_path)

            # Extract text content
            text_content = ""
            if self.config.extract_text:
                if PDFPLUMBER_AVAILABLE:
                    text_content = self._extract_text_pdfplumber(file_path)
                elif PYPDF2_AVAILABLE:
                    text_content = self._extract_text_pypdf2(file_path)

            # Extract OCR text if enabled
            ocr_content = ""
            if self.config.use_ocr and self.config.extract_images:
                ocr_texts = self._extract_images_for_ocr(file_path)
                ocr_content = "\n\n".join(ocr_texts)

            # Combine all text content
            all_content = text_content
            if ocr_content:
                if all_content:
                    all_content += "\n\n" + ocr_content
                else:
                    all_content = ocr_content

            # Create processing metadata
            processing_metadata = ProcessingMetadata(
                file_size=file_path.stat().st_size,
                processing_time=time.time() - start_time,
                text_length=len(all_content),
                block_count=len(all_content.split("\n\n")) if all_content else 0,
                link_count=0,  # PDFs don't have links
                image_count=metadata.get("image_count", 0),
                metadata_count=len(metadata),
            )

            return ProcessingResult(
                content=all_content,
                metadata=metadata,
                processing_metadata=processing_metadata,
                status=ProcessingStatus.SUCCESS,
                error_message=None,
            )

        except Exception as e:
            self.logger.error(f"Error processing PDF file {file_path}: {e}")
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
