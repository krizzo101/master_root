"""Pipeline stages for relationship mapping.

This module provides pipeline stages that integrate relationship components with the pipeline.

This module has been refactored into separate files in the pipeline_stages/ directory.
Import from the specific modules in that directory for better organization:
- proj_mapper.relationship.pipeline_stages.discovery
- proj_mapper.relationship.pipeline_stages.analysis
- proj_mapper.relationship.pipeline_stages.output

This file is maintained for backward compatibility.
"""

# Re-export all pipeline stages for backward compatibility
from proj_mapper.relationship.pipeline_stages.discovery import RelationshipDetectionStage
from proj_mapper.relationship.pipeline_stages.analysis import (
    RelationshipScoringStage,
    CrossReferenceResolutionStage
)
from proj_mapper.relationship.pipeline_stages.output import (
    RelationshipGraphBuildingStage,
    RelationshipServiceStage,
    RelationshipService
)

__all__ = [
    "RelationshipDetectionStage",
    "RelationshipScoringStage",
    "CrossReferenceResolutionStage",
    "RelationshipGraphBuildingStage",
    "RelationshipServiceStage",
    "RelationshipService",
] 