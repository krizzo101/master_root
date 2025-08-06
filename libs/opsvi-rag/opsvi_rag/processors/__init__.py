"""
Processors module for opsvi-rag.

Provides document processing capabilities for various file formats.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base processor interface
from .base import BaseProcessor, ProcessorConfig, ProcessorResult
from .csv import CSVProcessor, CSVProcessorConfig
from .docx import DocxProcessor, DocxProcessorConfig
from .email import EmailProcessor, EmailProcessorConfig

# Processor factory
from .factory import ProcessorFactory, ProcessorType
from .html import HTMLProcessor, HTMLProcessorConfig
from .json import JSONProcessor, JSONProcessorConfig
from .markdown import MarkdownProcessor, MarkdownProcessorConfig
from .pdf import PDFProcessor, PDFProcessorConfig

# Document processors
from .text import TextProcessor, TextProcessorConfig
from .web import WebProcessor, WebProcessorConfig

__all__ = [
    # Foundation imports
    "BaseComponent",
    "ComponentError",
    "get_logger",
    # Base processor
    "BaseProcessor",
    "ProcessorConfig",
    "ProcessorResult",
    # Document processors
    "TextProcessor",
    "TextProcessorConfig",
    "MarkdownProcessor",
    "MarkdownProcessorConfig",
    "HTMLProcessor",
    "HTMLProcessorConfig",
    "PDFProcessor",
    "PDFProcessorConfig",
    "DocxProcessor",
    "DocxProcessorConfig",
    "CSVProcessor",
    "CSVProcessorConfig",
    "JSONProcessor",
    "JSONProcessorConfig",
    "WebProcessor",
    "WebProcessorConfig",
    "EmailProcessor",
    "EmailProcessorConfig",
    # Factory
    "ProcessorFactory",
    "ProcessorType",
]

__version__ = "1.0.0"
