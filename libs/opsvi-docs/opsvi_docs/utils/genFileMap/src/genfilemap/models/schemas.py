# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Data Schemas for Genfilemap","description":"This module defines the file map schema and validation functions.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Import statements for required modules.","line_start":3,"line_end":11},{"name":"File Map Schema Definition","description":"Definition of the JSON schema for the file map.","line_start":13,"line_end":54},{"name":"Validation Functions","description":"Functions for validating the file map JSON and line numbers.","line_start":56,"line_end":94},{"name":"Schema Loading Function","description":"Function to load the schema from a file or use the default.","line_start":95,"line_end":106}],"key_elements":[{"name":"FILE_MAP_SCHEMA","description":"The JSON schema that defines the structure of the file map.","line":13},{"name":"validate_file_map_json","description":"Function to validate the file map JSON against the schema.","line":56},{"name":"validate_line_numbers","description":"Function to validate line numbers in the file map against actual content.","line":63},{"name":"load_schema","description":"Function to load the output schema from a file or return the default schema.","line":95}]}
"""
# FILE_MAP_END

"""
Data schemas for genfilemap.

This module defines the file map schema and validation functions.
"""

import json
import jsonschema
from typing import Optional, Dict, Any
import os

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
    },
}


def validate_file_map_json(file_map_obj: Dict[str, Any]) -> None:
    """Validate the file map JSON against the schema"""
    try:
        jsonschema.validate(instance=file_map_obj, schema=FILE_MAP_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"File map validation error: {str(e)}")


def validate_line_numbers(file_map_json: str, content: str) -> bool:
    """Enhanced validation of line numbers in the file map against the actual content"""
    try:
        file_map_obj = json.loads(file_map_json)

        # Count actual lines in the content
        content_lines = content.split("\n")
        actual_lines = len(content_lines)

        # Account for the 2-line offset that will be added by the file map insertion
        # (1 line for the file map + 1 blank line)
        file_map_offset = 2

        # Check if any section line numbers exceed the adjusted actual line count
        for section in file_map_obj.get("sections", []):
            # The line numbers in the file map should already include the offset
            # So we compare against the content lines + offset
            if (
                section.get("line_start", 0) > actual_lines + file_map_offset
                or section.get("line_end", 0) > actual_lines + file_map_offset
            ):
                print(
                    f"Section validation failed: line_start={section.get('line_start', 0)}, line_end={section.get('line_end', 0)}, actual_lines={actual_lines}, with_offset={actual_lines + file_map_offset}"
                )
                return False

        # Check if any key element line numbers exceed the adjusted actual line count
        for element in file_map_obj.get("key_elements", []):
            # The line numbers in the file map should already include the offset
            if element.get("line", 0) > actual_lines + file_map_offset:
                print(
                    f"Element validation failed: line={element.get('line', 0)}, actual_lines={actual_lines}, with_offset={actual_lines + file_map_offset}"
                )
                return False

        return True
    except (json.JSONDecodeError, KeyError, TypeError):
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
            print(f"Warning: Failed to load schema from {schema_path}: {str(e)}")
            print("Using default schema instead.")

    return FILE_MAP_SCHEMA
