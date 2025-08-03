"""
Data schemas for genfilemap.

This module defines the file map schema and validation functions.
"""

import json
import jsonschema
from typing import Optional, Dict, Any
import os
import re

from genfilemap.utils.file_utils import is_quiet_mode
from genfilemap.logging_utils import debug as log_debug


def debug_print(msg: str) -> None:
    """
    Print debug message only if not in quiet mode.

    Args:
        msg: The message to print
    """
    if not is_quiet_mode():
        log_debug(msg)


# File Map Schema Definition
FILE_MAP_SCHEMA = {
    "type": "object",
    "required": ["file_metadata", "ai_instructions", "sections"],
    "properties": {
        "file_metadata": {
            "type": "object",
            "required": ["title", "description", "last_updated", "type"],
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "last_updated": {"type": "string"},
                "type": {"type": "string"},
            },
        },
        "ai_instructions": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "description", "line_start", "line_end"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "line_start": {"type": "integer"},
                    "line_end": {"type": "integer"},
                },
            },
        },
        "key_elements": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "description", "line"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "line": {"type": "integer"},
                },
            },
        },
        "code_elements": {
            "type": "object",
            "properties": {
                "functions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "signature", "line"],
                        "properties": {
                            "name": {"type": "string"},
                            "signature": {"type": "string"},
                            "line": {"type": "integer"},
                            "return_type": {"type": "string"},
                            "description": {"type": "string"},
                            "parameters": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "type"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                        "default": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
                "classes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "line"],
                        "properties": {
                            "name": {"type": "string"},
                            "line": {"type": "integer"},
                            "inherits_from": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "description": {"type": "string"},
                            "methods": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "signature", "line"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "signature": {"type": "string"},
                                        "line": {"type": "integer"},
                                        "return_type": {"type": "string"},
                                        "description": {"type": "string"},
                                        "parameters": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "required": ["name", "type"],
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "description": {"type": "string"},
                                                    "default": {"type": "string"},
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                            "properties": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "line"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "line": {"type": "integer"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
                "imports": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["statement", "line"],
                        "properties": {
                            "statement": {"type": "string"},
                            "line": {"type": "integer"},
                        },
                    },
                },
                "constants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "line"],
                        "properties": {
                            "name": {"type": "string"},
                            "line": {"type": "integer"},
                            "value": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
}


def validate_file_map_json(file_map_obj: Dict[str, Any]) -> None:
    """Validate the file map JSON against the schema"""
    schema = load_schema()
    try:
        jsonschema.validate(instance=file_map_obj, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"File map validation error: {str(e)}")


def validate_line_numbers(file_map_json: str, content: str) -> bool:
    """Enhanced validation of line numbers in the file map against the actual content"""
    try:
        file_map_obj = json.loads(file_map_json)

        # Count actual lines in the content
        content_lines = content.split("\n")
        actual_lines = len(content_lines)

        # Determine the appropriate offset based on file content and file map
        # Check if this is a documentation file type in the file map
        file_type = file_map_obj.get("file_metadata", {}).get("type", "").lower()
        is_html_format = False

        # Check for documentation file types
        if file_type in ["documentation", "markdown", "html"]:
            is_html_format = True

        # If file type check was inconclusive, also check the first line of content
        # for HTML comment markers (this is a backup check)
        if not is_html_format and (
            "<!--" in content[:200] or "<!-- FILE_MAP_BEGIN" in content[:200]
        ):
            is_html_format = True

        # Set the appropriate offset
        if is_html_format:
            file_map_offset = 6  # 5 lines for HTML comment format + 1 blank line
            debug_print(f"DEBUG: Using HTML comment offset (6 lines)")
        else:
            file_map_offset = 2  # 1 line for other formats + 1 blank line
            debug_print(f"DEBUG: Using standard offset (2 lines)")

        # For very small files or new files, we need to be more lenient with validation
        # since the LLM might generate line numbers that exceed the current file size
        # but are still reasonable

        # For small files (under 100 lines), be especially lenient
        if actual_lines < 100:
            # Allow 5 extra lines or 10% of file size, whichever is greater
            extra_lines_small = max(5, int(actual_lines * 0.1))
            max_allowed_line = actual_lines + file_map_offset + extra_lines_small
            debug_print(
                f"DEBUG: Allowing {extra_lines_small} extra lines for small file (max line: {max_allowed_line})"
            )
        else:
            # For larger files, use the standard allowance
            max_allowed_line = actual_lines + file_map_offset

        # For documentation files, be more lenient with line numbers
        # Allow up to 25% more lines than the actual file for small files
        # or up to 10 additional lines, whichever is greater
        if is_html_format:
            extra_lines = max(10, int(actual_lines * 0.25))
            max_allowed_line += extra_lines
            debug_print(
                f"DEBUG: Allowing extra lines for documentation format (max line: {max_allowed_line})"
            )

        # Check if any section line numbers exceed the adjusted actual line count
        for section in file_map_obj.get("sections", []):
            # The line numbers in the file map should already include the offset
            # So we compare against the max allowed line count
            if (
                section.get("line_start", 0) > max_allowed_line
                or section.get("line_end", 0) > max_allowed_line
            ):
                debug_print(
                    f"Section validation failed: line_start={section.get('line_start', 0)}, line_end={section.get('line_end', 0)}, actual_lines={actual_lines}, max_allowed={max_allowed_line}"
                )
                return False

        # Check if any key element line numbers exceed the adjusted actual line count
        for element in file_map_obj.get("key_elements", []):
            # The line numbers in the file map should already include the offset
            if element.get("line", 0) > max_allowed_line:
                debug_print(
                    f"Element validation failed: line={element.get('line', 0)}, actual_lines={actual_lines}, max_allowed={max_allowed_line}"
                )
                return False

        return True
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        debug_print(f"Validation error in validate_line_numbers: {str(e)}")
        return False


def load_schema(schema_path: Optional[str] = None) -> dict:
    """Load the output schema from file if available, otherwise use the default"""
    if (
        schema_path
        and isinstance(schema_path, str)
        and schema_path.strip()
        and os.path.exists(schema_path)
    ):
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            return schema
        except (json.JSONDecodeError, IOError) as e:
            debug_print(f"Warning: Failed to load schema from {schema_path}: {str(e)}")
            debug_print("Using default schema instead.")

    return FILE_MAP_SCHEMA
