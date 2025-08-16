"""Pipeline stages for relationship analysis.

This module provides pipeline stages for analyzing and enhancing relationships between elements.
"""

import logging
from typing import List

from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.models.relationship import Relationship
from proj_mapper.relationship.scoring import ConfidenceScorer
from proj_mapper.relationship.cross_ref import CrossReferenceResolver

# Configure logging
logger = logging.getLogger(__name__)


class RelationshipScoringStage(PipelineStage):
    """Pipeline stage for scoring relationships.
    
    This stage scores the confidence of relationships between elements.
    """
    
    def __init__(self):
        """Initialize the relationship scoring stage."""
        self.scorer = ConfidenceScorer()
    
    def process(self, context: PipelineContext, input_data: List[Relationship]) -> List[Relationship]:
        """Process relationships to score their confidence.
        
        Args:
            context: The pipeline context
            input_data: The detected relationships to score
            
        Returns:
            List of scored relationships
        """
        # Score relationships
        scored_relationships = self.scorer.score_relationships(input_data)
        
        # Update relationships in context
        context.set_data("relationships", scored_relationships)
        context.set_metadata("relationship_scoring_completed", True)
        
        logger.info(f"Scored {len(scored_relationships)} relationships")
        
        return scored_relationships


class CrossReferenceResolutionStage(PipelineStage):
    """Pipeline stage for resolving cross-references.
    
    This stage resolves references between code and documentation elements.
    """
    
    def __init__(self, fuzzy_threshold: float = 0.7):
        """Initialize the cross-reference resolution stage.
        
        Args:
            fuzzy_threshold: Minimum similarity score for fuzzy matching
        """
        self.resolver = CrossReferenceResolver(fuzzy_threshold=fuzzy_threshold)
    
    def process(self, context: PipelineContext, input_data: List[Relationship]) -> List[Relationship]:
        """Process the pipeline context to resolve cross-references.
        
        Args:
            context: The pipeline context containing elements
            input_data: The relationships from previous stage
            
        Returns:
            Combined list of relationships including resolved references
            
        Raises:
            ValueError: If elements are not available in the context
        """
        # Check if code and doc elements are available
        if not context.has_data("code_elements") or not context.has_data("doc_elements"):
            raise ValueError("Code and documentation elements not available in context")
        
        code_elements = context.get_data("code_elements")
        doc_elements = context.get_data("doc_elements")
        
        # Add elements to resolver
        self.resolver.add_code_elements(code_elements)
        self.resolver.add_documentation_elements(doc_elements)
        
        # Resolve references
        reference_matches = self.resolver.resolve_all_references()
        
        # Convert matches to relationships
        reference_relationships = [match.to_relationship() for match in reference_matches]
        
        # Combine with existing relationships
        all_relationships = input_data + reference_relationships
        
        # Update relationships in context
        context.set_data("relationships", all_relationships)
        context.set_metadata("reference_resolution_count", len(reference_relationships))
        
        logger.info(f"Resolved {len(reference_relationships)} cross-references")
        
        return all_relationships 