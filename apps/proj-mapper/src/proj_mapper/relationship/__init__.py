"""Relationship Mapping Subsystem.

This package provides functionality for mapping relationships between code and documentation elements.
"""

from proj_mapper.relationship.detector import (
    RelationshipDetector, 
    RelationshipRule,
    ImportRelationshipRule,
    InheritanceRelationshipRule,
    DocumentationReferenceRule,
    NameMatchRelationshipRule,
    ContentSimilarityRule
)

from proj_mapper.relationship.scoring import (
    ConfidenceScorer, 
    ScoringStrategy,
    RelationshipTypeScoring,
    ContextualProximityScoring,
    MultipleDetectionScoring
)

from proj_mapper.relationship.cross_ref import (
    CrossReferenceResolver,
    ReferenceCandidate,
    ReferenceMatch
)

from proj_mapper.relationship.graph import (
    RelationshipGraph,
    Node,
    Edge
)

# Pipeline stages have been refactored into separate modules under pipeline_stages/
# The imports below use the new modular structure through the pipeline_stages/__init__.py
from proj_mapper.relationship.pipeline_stages import (
    RelationshipDetectionStage,
    RelationshipScoringStage,
    CrossReferenceResolutionStage,
    RelationshipGraphBuildingStage,
    RelationshipServiceStage,
    RelationshipService
)

from proj_mapper.relationship.mapper import (
    RelationshipMapper,
    RelationshipMappingStage
)

__all__ = [
    # Detector
    "RelationshipDetector",
    "RelationshipRule",
    "ImportRelationshipRule",
    "InheritanceRelationshipRule",
    "DocumentationReferenceRule",
    "NameMatchRelationshipRule",
    "ContentSimilarityRule",
    
    # Scoring
    "ConfidenceScorer",
    "ScoringStrategy",
    "RelationshipTypeScoring",
    "ContextualProximityScoring",
    "MultipleDetectionScoring",
    
    # Cross-reference
    "CrossReferenceResolver",
    "ReferenceCandidate",
    "ReferenceMatch",
    
    # Graph
    "RelationshipGraph",
    "Node",
    "Edge",
    
    # Pipeline stages
    "RelationshipDetectionStage",
    "RelationshipScoringStage",
    "CrossReferenceResolutionStage",
    "RelationshipGraphBuildingStage",
    "RelationshipServiceStage",
    "RelationshipService",
    
    # Mapper
    "RelationshipMapper",
    "RelationshipMappingStage"
]
