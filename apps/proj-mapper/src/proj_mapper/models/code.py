"""Code models for Project Mapper.

This module re-exports code models from the code/ package for backward compatibility.
New code should import directly from the code package modules.
"""

# Re-export code models from the code/ package for backward compatibility
from proj_mapper.models.code.base import (
    CodeElementType,
    Visibility,
    Location,
    LocationModel,
    CodeReference,
    register_serializer,
)
from proj_mapper.models.code.element import CodeElement
from proj_mapper.models.code.legacy import CodeElement as LegacyCodeElement

__all__ = [
    "CodeElementType",
    "Visibility",
    "Location",
    "LocationModel",
    "CodeElement",
    "CodeReference",
] 