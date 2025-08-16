"""Code models for Project Mapper.

This module contains models related to code elements such as classes, functions, and variables.
It provides a consistent API for representing code structures across different languages.
"""

# Re-export all code model classes to maintain backward compatibility
from proj_mapper.models.code.base import (
    Location, 
    LocationModel, 
    CodeElementType, 
    Visibility,
    register_serializer,
    CodeReference
)
from proj_mapper.models.code.element import CodeElement
from proj_mapper.models.code.legacy import CodeElement as LegacyCodeElement

# Maintain backward compatibility - keep original class names available
__all__ = [
    "Location",
    "LocationModel",
    "CodeElementType",
    "Visibility",
    "CodeElement",
    "CodeReference",
] 