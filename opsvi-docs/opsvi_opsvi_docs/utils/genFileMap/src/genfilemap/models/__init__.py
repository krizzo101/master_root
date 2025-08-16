"""
Models module for genfilemap

This package contains data structures and schemas used by the genfilemap system.
"""

from genfilemap.models.schemas import (
    validate_file_map_json,
    validate_line_numbers,
    load_schema,
)

__all__ = ["validate_file_map_json", "validate_line_numbers", "load_schema"]
