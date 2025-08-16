"""Relationship graph edge implementation.

This module contains the Edge class, which represents a relationship 
between nodes in the relationship graph.
"""

from typing import Dict, Any, Optional

from proj_mapper.models.relationship import Relationship, RelationshipType

# Forward references
from proj_mapper.relationship.graph.node import Node


class Edge:
    """Represents a relationship edge between two nodes in the graph.
    
    Attributes:
        source: The source node
        target: The target node
        relationship_type: The type of relationship
        confidence: Confidence score for the relationship (0.0-1.0)
        metadata: Additional metadata about the relationship
    """
    
    def __init__(
        self,
        source: Node,
        target: Node,
        relationship_type: RelationshipType,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a relationship edge.
        
        Args:
            source: Source node
            target: Target node
            relationship_type: Type of relationship
            confidence: Confidence score (0.0-1.0)
            metadata: Additional information about the relationship
        """
        self.source = source
        self.target = target
        self.relationship_type = relationship_type
        self.confidence = confidence
        self.metadata = metadata or {}
    
    def to_relationship(self) -> Relationship:
        """Convert edge to a relationship model.

        Returns:
            A Relationship model representing this edge
        """
        source_data = self.source.data
        target_data = self.target.data
        
        return Relationship(
            source_id=self.source.id,
            source_type=source_data.__class__.__name__ if source_data else "unknown",
            target_id=self.target.id,
            target_type=target_data.__class__.__name__ if target_data else "unknown",
            relationship_type=self.relationship_type,
            confidence=self.confidence,
            metadata=self.metadata,
        )
    
    def __str__(self) -> str:
        """Get string representation of the edge.
        
        Returns:
            String representation
        """
        # Handle both string and enum relationship types
        rel_type_str = self.relationship_type
        if hasattr(self.relationship_type, 'name'):
            rel_type_str = self.relationship_type.name
            
        return (
            f"{self.source.id} -> {self.target.id} "
            f"({rel_type_str}, {self.confidence:.2f})"
        ) 