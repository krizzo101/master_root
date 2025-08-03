"""
Processors module for genfilemap

This package contains file-type specific processors for generating
file maps for different types of files.
"""

from genfilemap.processors.base import FileProcessor, get_processor_for_file
from genfilemap.processors.code_processor import CodeFileProcessor
from genfilemap.processors.doc_processor import DocumentationFileProcessor

__all__ = [
    "FileProcessor",
    "get_processor_for_file",
    "CodeFileProcessor",
    "DocumentationFileProcessor"
] 