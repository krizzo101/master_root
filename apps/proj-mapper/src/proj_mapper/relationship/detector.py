"""Relationship detector for Project Mapper.

This module provides components for detecting relationships between code and documentation elements.

Note: This module is maintained for backward compatibility.
For new code, import from proj_mapper.relationship.detector instead.
"""

# Re-export from new module structure for backward compatibility
from proj_mapper.relationship.detector.base import RelationshipRule
from proj_mapper.relationship.detector.rules import (
    ImportRelationshipRule,
    InheritanceRelationshipRule,
    FunctionCallRelationshipRule,
    DocumentationReferenceRule,
    NameMatchRelationshipRule,
    ContentSimilarityRule
)
from proj_mapper.relationship.detector.detector import RelationshipDetector

__all__ = [
    "RelationshipRule",
    "ImportRelationshipRule",
    "InheritanceRelationshipRule",
    "FunctionCallRelationshipRule",
    "DocumentationReferenceRule",
    "NameMatchRelationshipRule",
    "ContentSimilarityRule",
    "RelationshipDetector"
] 