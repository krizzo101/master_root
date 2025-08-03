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
from typing import Dict, Tuple, List, Optional, Set, Any
import sys
import pathspec
from genfilemap.logging_utils import debug as log_debug

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


def is_quiet_mode():
    """Check if quiet mode is enabled based on CLI args or env var."""
    # Check environment variable first
    if os.environ.get("GENFILEMAP_QUIET") == "1":
        return True

    # Try to get from sys.argv
    try:
        return "--quiet" in sys.argv
    except:
        return False


def debug_print(msg: str):
    """Print debug message only if not in quiet mode."""
    if not is_quiet_mode():
        log_debug(msg)


def calculate_file_hash(content: str) -> str:
    """Calculate a hash for the file content to detect changes"""
    content_preview = content[:50].replace("\n", "\\n")
    debug_print(
        f"DEBUG-HASH: Calculating hash for content starting with: {content_preview}"
    )
    debug_print(f"DEBUG-HASH: Content length: {len(content)} characters")

    # Check if content starts with a file map
    if content.lstrip().startswith("# FILE_MAP_BEGIN"):
        debug_print(
            f"DEBUG-HASH: WARNING - Content appears to start with a file map, which should have been removed!"
        )

    hash_value = hashlib.md5(content.encode()).hexdigest()
    debug_print(f"DEBUG-HASH: Generated hash: {hash_value}")
    return hash_value


def extract_existing_file_map(content, comment_style):
    """Extract existing file map from the content if it exists"""
    start_marker, end_marker, line_prefix = comment_style

    content_preview = content[:50].replace(chr(10), "[newline]")
    debug_print(f"DEBUG-EXTRACT: Content first 50 chars: {content_preview}")
    debug_print(f"DEBUG-EXTRACT: Comment style: {comment_style}")

    # Define pattern based on comment style for improved readability and simplicity
    file_map_pattern = None

    # HTML-style comments (used in Markdown and HTML files)
    if start_marker == "<!--":
        debug_print(f"DEBUG-EXTRACT: Using HTML comment pattern")
        file_map_pattern = (
            r"<!-- FILE_MAP_BEGIN\s*\n<!--\s*\n(.*?)\n\s*-->\s*\n<!-- FILE_MAP_END -->"
        )

    # Python triple-quoted strings
    elif start_marker == '"""':
        debug_print(f"DEBUG-EXTRACT: Using Python format patterns")

        # Try the new single-line format first: # FILE_MAP_BEGIN {json} FILE_MAP_END
        single_line_pattern = r"# FILE_MAP_BEGIN (.*?) FILE_MAP_END"
        match = re.search(single_line_pattern, content)
        if match:
            try:
                json_content = match.group(1)
                json_obj = json.loads(json_content)
                debug_print(
                    f"DEBUG-EXTRACT: Successfully parsed JSON from Python single-line file map"
                )
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                debug_print(
                    f"DEBUG-EXTRACT: Failed to parse JSON in Python single-line file map: {str(e)}"
                )

        # Try the old multi-line comment format (for backward compatibility)
        file_map_pattern = r"# FILE_MAP_BEGIN\s*\n((?:# .*\n)+)# FILE_MAP_END"
        match = re.search(file_map_pattern, content, re.DOTALL)
        if match:
            captured_content = match.group(1)
            # Remove the "# " prefix from each line
            json_lines = [
                line[2:]
                for line in captured_content.split("\n")
                if line.startswith("# ")
            ]
            json_content = "\n".join(json_lines)
            try:
                json_obj = json.loads(json_content)
                debug_print(
                    f"DEBUG-EXTRACT: Successfully parsed JSON from Python multi-line comment file map"
                )
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                debug_print(
                    f"DEBUG-EXTRACT: Failed to parse JSON in Python multi-line file map: {str(e)}"
                )

        # Fallback for Python triple-quoted string (old format)
        debug_print(
            f"DEBUG-EXTRACT: Trying Python triple-quoted string fallback pattern"
        )
        pattern = r'"""\s*FILE_MAP_BEGIN\s*"""(?:\s*)(.*?)(?:\s*)"""\s*"""\s*FILE_MAP_END\s*"""'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            debug_print(
                f"DEBUG-EXTRACT: Found Python triple-quoted file map (old format)"
            )
            try:
                file_map_json = match.group(1).strip()
                json_obj = json.loads(file_map_json)
                debug_print(
                    f"DEBUG-EXTRACT: Found old Python format. This will be updated to the new format."
                )
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                debug_print(
                    f"DEBUG-EXTRACT: Failed to parse JSON in Python file map: {str(e)}"
                )

        # Fall back to the old triple-quoted string format
        debug_print(f"DEBUG-EXTRACT: Trying Python triple-quoted string pattern")
        file_map_pattern = (
            r'# FILE_MAP_BEGIN\s*\n"""\s*\n(.*?)\n\s*"""\s*\n# FILE_MAP_END'
        )

    # Special pattern for JavaScript files (no nested comments)
    elif start_marker == "/*" and line_prefix == "// ":
        debug_print(
            f"DEBUG-EXTRACT: Using JavaScript special pattern without nested comments"
        )
        file_map_pattern = r"/\* FILE_MAP_BEGIN\s*\n(.*?)\s*\*/\s*//\s*FILE_MAP_END"
        debug_print(f"DEBUG-EXTRACT: JavaScript pattern: {file_map_pattern}")

    # Special pattern for CSS files (uses /* */ for both markers)
    elif start_marker == "/*" and line_prefix == "/* ":
        debug_print(f"DEBUG-EXTRACT: Using CSS special pattern with /* */ markers")
        file_map_pattern = r"/\* FILE_MAP_BEGIN\s*\n(.*?)\s*\*/\s*/\*\s*FILE_MAP_END"
        debug_print(f"DEBUG-EXTRACT: CSS pattern: {file_map_pattern}")

    # Multi-line comments for other languages (C, Java, etc.)
    elif start_marker and end_marker:
        debug_print(
            f"DEBUG-EXTRACT: Using multi-line comment pattern for {start_marker}{end_marker}"
        )
        # Escape special characters in the comment markers
        escaped_start = re.escape(start_marker)
        escaped_end = re.escape(end_marker)
        file_map_pattern = f"{escaped_start}\\s*FILE_MAP_BEGIN\\s*{escaped_start}\\s*(.*?)\\s*{escaped_end}\\s*{escaped_end}\\s*FILE_MAP_END\\s*{escaped_end}"

    # Single-line comments for languages without multi-line comment support
    elif line_prefix:
        debug_print(
            f"DEBUG-EXTRACT: Using single-line comment pattern for {line_prefix}"
        )
        escaped_single = re.escape(line_prefix)
        file_map_pattern = f"{escaped_single}FILE_MAP_BEGIN\\s*{escaped_single}\\s*(.*?)\\s*{escaped_single}\\s*FILE_MAP_END"

    # Apply the pattern if one was selected
    if file_map_pattern:
        debug_print(f"DEBUG-EXTRACT: Searching with pattern: {file_map_pattern}")
        match = re.search(file_map_pattern, content, re.DOTALL)

        if match:
            debug_print(f"DEBUG-EXTRACT: Found file map match!")
            try:
                file_map_json = match.group(1).strip()
                # Print debug information about what we're extracting
                debug_print(
                    f"DEBUG-EXTRACT: Extracted JSON starts with: {file_map_json[:50]}..."
                )
                json_obj = json.loads(file_map_json)
                debug_print(f"DEBUG-EXTRACT: Successfully parsed JSON from file map")

                # Return the full match and the remaining content (everything after the match)
                # Note: We use lstrip() to remove any leading whitespace, which includes the blank line
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                debug_print(
                    f"DEBUG-EXTRACT: Failed to parse JSON in file map: {str(e)}"
                )
        else:
            debug_print(f"DEBUG-EXTRACT: No match for pattern")
            # Try fallbacks for special file types

            # Fallback for JS/CSS files with various formats
            if start_marker == "/*":
                # Try all possible combinations for JS/CSS
                debug_print(f"DEBUG-EXTRACT: Trying fallback patterns for JS/CSS")
                fallback_patterns = [
                    r"/\*\s*FILE_MAP_BEGIN\s*\n(.*?)\*/\s*//\s+FILE_MAP_END",  # JS with space after //
                    r"/\*\s*FILE_MAP_BEGIN\s*\n(.*?)\*/\s*/\*\s+FILE_MAP_END",  # CSS with space after /*
                    r"/\*\s*FILE_MAP_BEGIN\s*\n(.*?)\*/\s*/\*\s*FILE_MAP_END",  # CSS with no space
                ]

                for pattern in fallback_patterns:
                    debug_print(f"DEBUG-EXTRACT: Trying fallback pattern: {pattern}")
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        debug_print(
                            f"DEBUG-EXTRACT: Found file map with fallback pattern!"
                        )
                        try:
                            file_map_json = match.group(1).strip()
                            json_obj = json.loads(file_map_json)
                            debug_print(
                                f"DEBUG-EXTRACT: Successfully parsed JSON from fallback pattern"
                            )
                            return match.group(0), content[match.end() :].lstrip()
                        except (json.JSONDecodeError, NameError) as e:
                            debug_print(
                                f"DEBUG-EXTRACT: Failed to parse JSON from fallback pattern: {str(e)}"
                            )

            # Dump the first part of the content for debugging
            content_preview = content[:200].replace("\n", "\\n")
            debug_print(f"DEBUG-EXTRACT: Content start: {content_preview}")

    # If no file map is found with the primary pattern, try the fallback patterns for backward compatibility

    # Fallback for HTML comments (old format)
    if start_marker == "<!--" and not file_map_pattern:
        debug_print(f"DEBUG-EXTRACT: Trying HTML comment fallback pattern")
        pattern = r"<!-- FILE_MAP_BEGIN -->(?:\s*|\s+)<!--\s*(\{.*?\})\s*-->(?:\s*|\s+)<!-- FILE_MAP_END -->"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            debug_print(f"DEBUG-EXTRACT: Found HTML comment file map (old format)")
            try:
                file_map_json = match.group(1).strip()
                json_obj = json.loads(file_map_json)
                debug_print(
                    "WARNING: Found old HTML comment format. This will be updated to the new format."
                )
                return match.group(0), content[match.end() :].lstrip()
            except (json.JSONDecodeError, NameError) as e:
                debug_print(
                    f"DEBUG-EXTRACT: Failed to parse JSON in HTML file map: {str(e)}"
                )

    # If all patterns fail, indicate that clearly in debug output
    debug_print(
        "DEBUG-EXTRACT: No existing file map found in content after trying all patterns"
    )
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


def should_ignore_file(
    file_path: str, ignore_patterns: list = None, pathspec_obj=None
) -> bool:
    """Check if a file should be ignored based on .gitignore-style patterns using pathspec."""
    if pathspec_obj is not None:
        rel_path = os.path.relpath(file_path)
        rel_path = rel_path.replace(os.sep, "/")
        return pathspec_obj.match_file(rel_path)
    if not ignore_patterns:
        return False
    import pathspec

    spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_patterns)
    rel_path = os.path.relpath(file_path)
    rel_path = rel_path.replace(os.sep, "/")
    return spec.match_file(rel_path)


def expand_ignore_patterns(patterns: List[str]) -> List[str]:
    """
    Expand any home directory references in ignore patterns.

    This ensures consistent pattern interpretation across processes.

    Args:
        patterns: List of ignore patterns

    Returns:
        List of expanded patterns
    """
    expanded_patterns = []
    for pattern in patterns:
        if "~" in pattern:
            expanded_pattern = os.path.expanduser(pattern)
            expanded_patterns.append(expanded_pattern)
        else:
            expanded_patterns.append(pattern)
    return expanded_patterns


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


def create_default_fileignore(ignore_file_path: str) -> bool:
    """
    Creates a default .fileignore file if it doesn't exist.

    Args:
        ignore_file_path: Path where the ignore file should be created

    Returns:
        True if file was created, False if it already exists or couldn't be created
    """
    if os.path.exists(ignore_file_path):
        return False

    try:
        # Get the template file path
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "schema", "fileignore.template"
        )

        # Check if template exists
        if not os.path.exists(template_path):
            debug_print(
                f"Warning: Could not find fileignore template at {template_path}"
            )
            return False

        # Copy template content to target location
        with open(template_path, "r") as src, open(ignore_file_path, "w") as dest:
            dest.write(src.read())

        debug_print(f"Created default .fileignore file at {ignore_file_path}")
        return True
    except Exception as e:
        debug_print(f"Error creating default .fileignore file: {str(e)}")
        return False


def extract_all_file_maps(content: str) -> str:
    """
    Extract all file maps from the content and return only the actual content.

    This function removes all file map blocks from the content to ensure the hash
    calculation is based only on the actual file content.

    Args:
        content: The file content

    Returns:
        The content with all file maps removed
    """
    # Common patterns for file maps in different formats
    patterns = [
        # Python single-line format (new): # FILE_MAP_BEGIN {json} FILE_MAP_END
        r"# FILE_MAP_BEGIN .*? FILE_MAP_END\s*\n?",
        # Python multi-line comment format (old)
        r"# FILE_MAP_BEGIN\s*\n(?:# .*\n)+# FILE_MAP_END\s*\n?",
        # Python format with # markers (old)
        r'# FILE_MAP_BEGIN.*?\n""".*?\n.*?\n.*?""".*?\n# FILE_MAP_END\s*\n?',
        # Older Python triple-quoted format
        r'"""\s*FILE_MAP_BEGIN\s*"""(?:\s*).*?(?:\s*)"""\s*"""\s*FILE_MAP_END\s*"""\s*\n?',
        # HTML/Markdown format
        r"<!-- FILE_MAP_BEGIN\s*\n<!--\s*\n.*?\n\s*-->\s*\n<!-- FILE_MAP_END -->\s*\n?",
        # Older HTML format
        r"<!-- FILE_MAP_BEGIN -->(?:\s*|\s+)<!--\s*\{.*?\}\s*-->(?:\s*|\s+)<!-- FILE_MAP_END -->\s*\n?",
        # Generic multi-line format
        r"/\*\s*FILE_MAP_BEGIN\s*/\*\s*.*?\s*\*/\s*\*/\s*FILE_MAP_END\s*\*/\s*\n?",
        # JS special format (// for end marker)
        r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\s*\*/\s*//\s*FILE_MAP_END\s*\n?",
        # CSS special format (/* */ for both markers)
        r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\s*\*/\s*/\*\s*FILE_MAP_END\s*\n?",
        # JS with space after //
        r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\*/\s*//\s+FILE_MAP_END\s*\n?",
        # CSS with space after /*
        r"/\*\s*FILE_MAP_BEGIN\s*\n.*?\*/\s*/\*\s+FILE_MAP_END\s*\n?",
    ]

    # Apply each pattern to remove all file maps
    cleaned_content = content
    for pattern in patterns:
        cleaned_content = re.sub(pattern, "", cleaned_content, flags=re.DOTALL)

    return cleaned_content.lstrip()
