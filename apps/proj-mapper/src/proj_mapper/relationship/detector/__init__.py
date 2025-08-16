"""Relationship detector package.

This package provides functionality for detecting relationships between code and documentation elements.
"""

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
    # Base
    "RelationshipRule",
    
    # Rules
    "ImportRelationshipRule",
    "InheritanceRelationshipRule",
    "FunctionCallRelationshipRule",
    "DocumentationReferenceRule",
    "NameMatchRelationshipRule",
    "ContentSimilarityRule",
    
    # Detector
    "RelationshipDetector"
] 