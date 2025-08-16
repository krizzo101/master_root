# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Processors Module for Genfilemap","description":"This package contains file-type specific processors for generating file maps for different types of files.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Docstring","description":"Documentation string providing an overview of the processors module.","line_start":2,"line_end":6},{"name":"Imports","description":"Import statements for the necessary file processors.","line_start":8,"line_end":10},{"name":"Public API","description":"Definition of the public API for the module, specifying which classes and functions are accessible.","line_start":12,"line_end":15}],"key_elements":[{"name":"FileProcessor","description":"Class for processing files in a generic manner.","line":8},{"name":"get_processor_for_file","description":"Function to retrieve the appropriate processor for a given file type.","line":8},{"name":"CodeFileProcessor","description":"Class for processing code files specifically.","line":9},{"name":"DocumentationFileProcessor","description":"Class for processing documentation files specifically.","line":10}]}
"""
# FILE_MAP_END

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
    "DocumentationFileProcessor",
]
