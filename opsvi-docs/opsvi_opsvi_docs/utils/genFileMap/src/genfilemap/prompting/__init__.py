# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Prompting Module for Genfilemap","description":"This package contains prompt templates and generators for different file types.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation string providing an overview of the prompting module.","line_start":1,"line_end":4},{"name":"Imports","description":"Import statements for necessary functions from the prompts module.","line_start":5,"line_end":8},{"name":"Public API Declaration","description":"Declaration of the public API for the prompting module.","line_start":9,"line_end":13}],"key_elements":[{"name":"get_code_system_message","description":"Function to get the system message for code prompts.","line":7},{"name":"get_code_user_prompt","description":"Function to get the user prompt for code prompts.","line":7},{"name":"get_documentation_system_message","description":"Function to get the system message for documentation prompts.","line":7},{"name":"get_documentation_user_prompt","description":"Function to get the user prompt for documentation prompts.","line":7}]}
"""
# FILE_MAP_END

"""
Prompting module for genfilemap.

This package contains prompt templates and generators for different file types.
"""

from genfilemap.prompting.prompts import (
    get_code_system_message,
    get_code_user_prompt,
    get_documentation_system_message,
    get_documentation_user_prompt,
)

__all__ = [
    "get_code_system_message",
    "get_code_user_prompt",
    "get_documentation_system_message",
    "get_documentation_user_prompt",
]
