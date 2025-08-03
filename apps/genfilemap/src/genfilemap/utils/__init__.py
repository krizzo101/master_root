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
    create_default_fileignore,
    expand_ignore_patterns
)

from genfilemap.utils.template_utils import load_template
from genfilemap.utils.api_utils import get_api_key

__all__ = [
    "get_comment_style",
    "calculate_file_hash",
    "extract_existing_file_map",
    "get_file_type",
    "should_ignore_file",
    "load_ignore_patterns",
    "create_default_fileignore",
    "expand_ignore_patterns",
    "load_template",
    "get_api_key"
] 