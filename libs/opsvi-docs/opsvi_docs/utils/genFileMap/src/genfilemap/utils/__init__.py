# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Utility Modules for Genfilemap","description":"This package contains utility functions for file operations, templates, and other supporting functionality needed by the genfilemap system.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Docstring","description":"Contains the module-level documentation for the utility functions.","line_start":1,"line_end":6},{"name":"Imports","description":"Imports necessary functions from other utility modules.","line_start":8,"line_end":18},{"name":"Public API","description":"Defines the public API of the module by specifying the exported functions.","line_start":20,"line_end":24}],"key_elements":[{"name":"get_comment_style","description":"Function to get the comment style for files.","line":9},{"name":"calculate_file_hash","description":"Function to calculate the hash of a file.","line":10},{"name":"extract_existing_file_map","description":"Function to extract an existing file map.","line":11},{"name":"get_file_type","description":"Function to determine the type of a file.","line":12},{"name":"should_ignore_file","description":"Function to determine if a file should be ignored.","line":13},{"name":"load_ignore_patterns","description":"Function to load ignore patterns from a configuration.","line":14},{"name":"load_template","description":"Function to load a template for file operations.","line":17}]}
"""
# FILE_MAP_END

"""
Utility modules for genfilemap

This package contains utility functions for file operations, templates, and other 
supporting functionality needed by the genfilemap system.
"""

from genfilemap.utils.file_utils import (
    get_comment_style,
    calculate_file_hash,
    extract_existing_file_map,
    get_file_type,
    should_ignore_file,
    load_ignore_patterns,
)

from genfilemap.utils.template_utils import load_template

__all__ = [
    "get_comment_style",
    "calculate_file_hash",
    "extract_existing_file_map",
    "get_file_type",
    "should_ignore_file",
    "load_ignore_patterns",
    "load_template",
]
