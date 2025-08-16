"""Confidence scoring for relationships.

This module provides components for scoring the confidence of relationships between elements.
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Set

from proj_mapper.models.relationship import Relationship, RelationshipType

# Configure logging
logger = logging.getLogger(__name__)


class ScoringStrategy(ABC):
    """Abstract base class for relationship scoring strategies.
    
    Strategies define specific methods for adjusting confidence scores.
    """
    
    @abstractmethod
    def score(self, relationship: Relationship) -> float:
        """Score the confidence of a relationship.
        
        Args:
            relationship: The relationship to score
            
        Returns:
            The adjusted confidence score (0.0-1.0)
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of the scoring strategy.
        
        Returns:
            The name of the strategy
        """
        return self.__class__.__name__


class RelationshipTypeScoring(ScoringStrategy):
    """Strategy for adjusting scores based on relationship type.
    
    Different relationship types have different base confidence levels.
    """
    
    def __init__(self):
        """Initialize with default type-based confidence adjustments."""
        self.type_confidence_adjustments: Dict[RelationshipType, float] = {
            RelationshipType.IMPORTS: 0.95,       # Strong relationship
            RelationshipType.IMPORTED_BY: 0.95,   # Strong relationship
            RelationshipType.INHERITS_FROM: 0.9,  # Strong relationship
            RelationshipType.INHERITED_BY: 0.9,   # Strong relationship
            RelationshipType.CALLS: 0.85,         # Strong relationship
            RelationshipType.CALLED_BY: 0.85,     # Strong relationship
            RelationshipType.CONTAINS: 0.8,       # Strong relationship
            RelationshipType.DOCUMENTS: 0.7,      # Moderate relationship
            RelationshipType.DOCUMENTED_BY: 0.7,  # Moderate relationship
            RelationshipType.REFERENCES: 0.6,     # Moderate relationship
            RelationshipType.RELATED_TO: 0.5,     # Weaker relationship
            RelationshipType.OTHER: 0.4,          # Weakest relationship
        }
    
    def score(self, relationship: Relationship) -> float:
        """Score based on relationship type.
        
        Args:
            relationship: The relationship to score
            
        Returns:
            The adjusted confidence score
        """
        # Get the base confidence
        base_confidence = relationship.confidence
        
        # Get the type adjustment factor
        type_adjustment = self.type_confidence_adjustments.get(
            relationship.relationship_type, 0.5
        )
        
        # Calculate adjusted score - weighted average of base and type adjustment
        adjusted_score = (base_confidence * 0.7) + (type_adjustment * 0.3)
        
        return min(adjusted_score, 1.0)


class ContextualProximityScoring(ScoringStrategy):
    """Strategy for adjusting scores based on contextual proximity.
    
    Elements that are contextually close (e.g., in the same file, module, or document)
    are more likely to be related.
    """
    
    def score(self, relationship: Relationship) -> float:
        """Score based on contextual proximity.
        
        Args:
            relationship: The relationship to score
            
        Returns:
            The adjusted confidence score
        """
        # Get the base confidence
        base_confidence = relationship.confidence
        
        # Default proximity adjustment
        proximity_adjustment = 0.0
        
        # Check if we have file information in metadata
        source_file = relationship.metadata.get("source_file")
        target_file = relationship.metadata.get("target_file")
        
        if source_file and target_file:
            # Same file is a strong proximity indicator
            if source_file == target_file:
                proximity_adjustment = 0.2
            # Same directory is a moderate proximity indicator
            elif source_file.split("/")[:-1] == target_file.split("/")[:-1]:
                proximity_adjustment = 0.1
        
        # Calculate adjusted score
        adjusted_score = base_confidence + proximity_adjustment
        
        return min(adjusted_score, 1.0)


class MultipleDetectionScoring(ScoringStrategy):
    """Strategy for adjusting scores based on detection by multiple rules.
    
    Relationships detected by multiple rules have higher confidence.
    """
    
    def score(self, relationship: Relationship) -> float:
        """Score based on detection by multiple rules.
        
        Args:
            relationship: The relationship to score
            
        Returns:
            The adjusted confidence score
        """
        # Get the base confidence
        base_confidence = relationship.confidence
        
        # Check if we have detection rule information
        detection_rules = relationship.metadata.get("detection_rules", [])
        
        # Convert to list if it's a single string
        if isinstance(detection_rules, str):
            detection_rules = [detection_rules]
        
        # Single detection rule in metadata
        detection_rule = relationship.metadata.get("detection_rule")
        if detection_rule and detection_rule not in detection_rules:
            detection_rules.append(detection_rule)
        
        # Adjust based on number of detection rules
        if len(detection_rules) > 1:
            # Multiple detections increase confidence
            # Each additional detection adds confidence up to a cap
            rule_adjustment = min(0.05 * (len(detection_rules) - 1), 0.2)
            adjusted_score = base_confidence + rule_adjustment
            return min(adjusted_score, 1.0)
        
        return base_confidence


class ConfidenceScorer:
    """Main component for scoring relationship confidence.
    
    This scorer manages a set of scoring strategies and applies them to adjust
    the confidence scores of relationships.
    """
    
    def __init__(self):
        """Initialize with default scoring strategies."""
        self.strategies: List[ScoringStrategy] = [
            RelationshipTypeScoring(),
            ContextualProximityScoring(),
            MultipleDetectionScoring()
        ]
    
    def add_strategy(self, strategy: ScoringStrategy) -> None:
        """Add a scoring strategy.
        
        Args:
            strategy: The strategy to add
        """
        self.strategies.append(strategy)
        logger.debug(f"Added scoring strategy: {strategy.get_name()}")
    
    def score_relationship(self, relationship: Relationship) -> Relationship:
        """Score a single relationship using all strategies.
        
        Args:
            relationship: The relationship to score
            
        Returns:
            The relationship with updated confidence score
        """
        # Start with the original confidence
        original_confidence = relationship.confidence
        current_confidence = original_confidence
        
        # Record scoring details for explanation
        scoring_details: Dict[str, float] = {}
        
        # Apply each strategy
        for strategy in self.strategies:
            strategy_score = strategy.score(relationship)
            scoring_details[strategy.get_name()] = strategy_score
            
            # Simple averaging of strategy scores
            current_confidence = (current_confidence + strategy_score) / 2
        
        # Store scoring details in metadata
        if "scoring" not in relationship.metadata:
            relationship.metadata["scoring"] = {}
        
        relationship.metadata["scoring"]["original"] = original_confidence
        relationship.metadata["scoring"]["details"] = scoring_details
        relationship.metadata["scoring"]["final"] = current_confidence
        
        # Update the relationship confidence
        relationship.confidence = current_confidence
        
        return relationship
    
    def score_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Score a list of relationships.
        
        Args:
            relationships: The relationships to score
            
        Returns:
            The relationships with updated confidence scores
        """
        scored_relationships = []
        
        for relationship in relationships:
            scored_relationship = self.score_relationship(relationship)
            scored_relationships.append(scored_relationship)
        
        logger.info(f"Scored {len(scored_relationships)} relationships")
        return scored_relationships
    
    def get_explanation(self, relationship: Relationship) -> str:
        """Get a human-readable explanation of the scoring.
        
        Args:
            relationship: The relationship to explain
            
        Returns:
            A string explaining how the confidence was calculated
        """
        scoring = relationship.metadata.get("scoring", {})
        if not scoring:
            return "No scoring information available"
        
        original = scoring.get("original", "unknown")
        final = scoring.get("final", "unknown")
        details = scoring.get("details", {})
        
        explanation = [
            f"Original confidence: {original:.2f}",
            f"Final confidence: {final:.2f}",
            "Strategy scores:"
        ]
        
        for strategy_name, score in details.items():
            explanation.append(f"  - {strategy_name}: {score:.2f}")
        
        return "\n".join(explanation) 