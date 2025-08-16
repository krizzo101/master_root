# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"File Utilities for Genfilemap","description":"This module provides helper functions for common file operations, including file type detection, comment style retrieval, and file hash calculation.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for file handling and operations.","line_start":3,"line_end":14},{"name":"Constants","description":"Defines comment styles for different file types and a default comment style.","line_start":16,"line_end":31},{"name":"Function Definitions","description":"Contains various utility functions for file operations.","line_start":33,"line_end":182}],"key_elements":[{"name":"COMMENT_STYLES","description":"A dictionary mapping file extensions to their respective comment styles.","line":16},{"name":"DEFAULT_COMMENT_STYLE","description":"The default comment style used for unknown file types.","line":31},{"name":"get_comment_style","description":"Function to get the appropriate comment style for a given file type.","line":36},{"name":"calculate_file_hash","description":"Function to calculate a hash for the file content to detect changes.","line":41},{"name":"extract_existing_file_map","description":"Function to extract an existing file map from the content if it exists.","line":45},{"name":"get_file_type","description":"Function to determine the file type based on extension and content.","line":126},{"name":"should_ignore_file","description":"Function to check if a file should be ignored based on ignore patterns.","line":156},{"name":"load_ignore_patterns","description":"Function to load ignore patterns from a file.","line":174}]}
"""
# FILE_MAP_END

"""
File handling utilities for genfilemap.

This module provides helper functions for common file operations.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from fnmatch import fnmatch
from typing import List

# File comment styles for different file types
COMMENT_STYLES = {
    # Format: (start_multi, end_multi, single_line)
    ".py": ('"""', '"""', "# "),
    ".js": ("/*", "*/", "// "),
    ".ts": ("/*", "*/", "// "),
    ".tsx": ("/*", "*/", "// "),
    ".jsx": ("/*", "*/", "// "),
    ".css": ("/*", "*/", "/* "),
    ".html": ("<!--", "-->", "<!-- "),
    ".md": ("<!--", "-->", "<!-- "),
    ".sql": ("/*", "*/", "-- "),
    ".sh": (":<<!EOF", "!EOF", "# "),
    ".bash": (":<<!EOF", "!EOF", "# "),
    ".txt": ("", "", ""),
    # Add more file types as needed
}

# Default comment style for unknown file types
DEFAULT_COMMENT_STYLE = ("/*", "*/", "// ")


def get_comment_style(file_path):
    """Get the appropriate comment style for the file type"""
    ext = Path(file_path).suffix.lower()
    return COMMENT_STYLES.get(ext, DEFAULT_COMMENT_STYLE)


def calculate_file_hash(content: str) -> str:
    """Calculate a hash for the file content to detect changes"""
    return hashlib.md5(content.encode()).hexdigest()


def extract_existing_file_map(content, comment_style):
    """Extract existing file map from the content if it exists"""
    start_multi, end_multi, single_line = comment_style

    # Special pattern for HTML comments (used in Markdown and HTML files)
    if start_multi == "<!--":
        # This pattern matches the new 5-line format with properly separated comments
        # Format: <!-- FILE_MAP_BEGIN \n<!--\n{json}\n-->\n<!-- FILE_MAP_END -->
        pattern = (
            r"<!-- FILE_MAP_BEGIN\s*\n<!--\s*\n(.*?)\n\s*-->\s*\n<!-- FILE_MAP_END -->"
        )
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                file_map_json = match.group(1).strip()
                json_obj = json.loads(file_map_json)
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                print(f"Failed to parse JSON in HTML comment file map: {str(e)}")
                # If JSON is invalid, continue checking other patterns

        # Also try the old format (will be removed in a future version)
        pattern = r"<!-- FILE_MAP_BEGIN -->(?:\s*|\s+)<!--\s*(\{.*?\})\s*-->(?:\s*|\s+)<!-- FILE_MAP_END -->"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                file_map_json = match.group(1).strip()
                json_obj = json.loads(file_map_json)
                print(
                    "WARNING: Found old HTML comment format. This will be updated to the new format."
                )
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError):
                # If JSON is invalid, continue checking other patterns
                pass

    # Pattern for Python single-line comment with triple-quoted string format:
    # # FILE_MAP_BEGIN
    # """
    # {json}
    # """
    # # FILE_MAP_END
    if start_multi == '"""':
        # First try the new Python-compatible format
        pattern = (
            r'# FILE_MAP_BEGIN\s*\n"""(?:\s*)\n(.*?)\n(?:\s*)"""\s*\n# FILE_MAP_END'
        )
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                file_map_json = match.group(1).strip()
                json_obj = json.loads(file_map_json)
                print("DEBUG: Found Python-compatible file map format with # markers")
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                print(f"Failed to parse JSON in Python-compatible file map: {str(e)}")
                # If JSON is invalid, continue checking other patterns

        # Then try the old format (for backward compatibility)
        pattern = r'"""\s*FILE_MAP_BEGIN\s*"""(?:\s*)(.*?)(?:\s*)"""\s*"""\s*FILE_MAP_END\s*"""'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                file_map_json = match.group(1).strip()
                json_obj = json.loads(file_map_json)
                print(
                    "DEBUG: Found old Python triple-quoted file map format. This will be updated to the new format."
                )
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                print(
                    f"Failed to parse JSON in Python triple-quoted file map: {str(e)}"
                )
                # If JSON is invalid, continue checking other patterns

    # Pattern to match file map section in multi-line or single-line format for other file types
    if start_multi and end_multi:
        pattern = re.escape(start_multi) + r"\s*FILE MAP.*?" + re.escape(end_multi)
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(0), content[match.end() :].lstrip()

    # Try to match single-line comment style file maps
    if single_line:
        pattern = (
            f"^{re.escape(single_line)}FILE MAP.*?{re.escape(single_line)}END FILE MAP"
        )
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        if match:
            return match.group(0), content[match.end() :].lstrip()

    return None, content


def get_file_type(file_path: str) -> str:
    """Determine the file type based on extension and content"""
    ext = Path(file_path).suffix.lower()

    # Map extensions to file types
    if ext in [".py", ".pyx", ".pyw"]:
        return "python"
    elif ext in [".js", ".jsx", ".ts", ".tsx"]:
        return "javascript"
    elif ext in [".html", ".htm", ".xhtml"]:
        return "html"
    elif ext in [".css", ".scss", ".sass", ".less"]:
        return "stylesheet"
    elif ext in [".md", ".markdown", ".mdown"]:
        return "documentation"
    elif ext in [".json", ".jsonl"]:
        return "data"
    elif ext in [".yml", ".yaml"]:
        return "configuration"
    elif ext in [".sql"]:
        return "database"
    elif ext in [".sh", ".bash", ".zsh"]:
        return "shell_script"
    elif ext in [".c", ".cpp", ".h", ".hpp"]:
        return "c_cpp"
    elif ext in [".java"]:
        return "java"
    else:
        return "text"


def should_ignore_file(file_path: str, ignore_patterns: List[str]) -> bool:
    """Check if a file should be ignored based on patterns"""
    if not ignore_patterns:
        return False

    # Convert to relative path if it's absolute
    if os.path.isabs(file_path):
        rel_path = os.path.relpath(file_path)
    else:
        rel_path = file_path

    # Check if file matches any ignore pattern
    for pattern in ignore_patterns:
        if fnmatch(rel_path, pattern) or fnmatch(os.path.basename(rel_path), pattern):
            return True

    return False


def load_ignore_patterns(ignore_file: str) -> List[str]:
    """Load ignore patterns from a file (gitignore-style)"""
    patterns = []
    if os.path.exists(ignore_file):
        with open(ignore_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns
