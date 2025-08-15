"""Pipeline stages for relationship output generation.

This module provides pipeline stages for generating and exposing relationship data.
"""

import logging
from typing import Dict, List, Any, Optional

from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.relationship.graph import RelationshipGraph

# Configure logging
logger = logging.getLogger(__name__)


class RelationshipGraphBuildingStage(PipelineStage):
    """Pipeline stage for building the relationship graph.
    
    This stage builds a graph representation of the relationships.
    """
    
    def __init__(self):
        """Initialize the graph building stage."""
        self.graph = RelationshipGraph()
    
    def process(self, context: PipelineContext, input_data: List[Relationship]) -> RelationshipGraph:
        """Process relationships to build a graph.
        
        Args:
            context: The pipeline context
            input_data: The relationships to add to the graph
            
        Returns:
            The built relationship graph
        """
        # Check if code and doc elements are available
        code_elements = context.get_data("code_elements", [])
        doc_elements = context.get_data("doc_elements", [])
        
        # Add elements to graph
        for element in code_elements:
            self.graph.add_code_element(element)
        
        for element in doc_elements:
            self.graph.add_documentation_element(element)
        
        # Add relationships to graph
        for relationship in input_data:
            self.graph.add_relationship(relationship)
        
        # Store graph in context
        context.set_data("relationship_graph", self.graph)
        
        # Store graph statistics in metadata
        stats = self.graph.get_stats()
        for key, value in stats.items():
            context.set_metadata(f"graph_{key}", value)
        
        logger.info(f"Built relationship graph with {stats['total_nodes']} nodes and {stats['total_edges']} edges")
        
        return self.graph


class RelationshipServiceStage(PipelineStage):
    """Pipeline stage for creating the relationship service.
    
    This stage creates a service that provides access to relationships.
    """
    
    def process(self, context: PipelineContext, input_data: RelationshipGraph) -> Dict[str, Any]:
        """Process the graph to create a relationship service.
        
        Args:
            context: The pipeline context
            input_data: The relationship graph
            
        Returns:
            The relationship service object
        """
        # Create relationship service
        service = RelationshipService(input_data)
        
        # Store service in context
        context.set_data("relationship_service", service)
        
        logger.info("Created relationship service")
        
        return service


class RelationshipService:
    """Service for accessing and querying relationships.
    
    This service provides a high-level API for working with relationships.
    """
    
    def __init__(self, graph: RelationshipGraph):
        """Initialize the relationship service.
        
        Args:
            graph: The relationship graph
        """
        self.graph = graph
    
    def get_related_elements(self, 
                            element_id: str, 
                            relationship_types: Optional[List[RelationshipType]] = None,
                            min_confidence: float = 0.5,
                            max_depth: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Get elements related to the given element.
        
        Args:
            element_id: ID of the element
            relationship_types: Types of relationships to include (all if None)
            min_confidence: Minimum confidence score
            max_depth: Maximum relationship depth
            
        Returns:
            Dictionary of related elements grouped by relationship type
        """
        # Get node for the element
        node = self.graph.get_node(element_id)
        if not node:
            return {}
        
        # Initialize result
        related_elements = {}
        
        # Filter by relationship types if provided
        if relationship_types:
            edge_types = relationship_types
        else:
            # Use all relationship types
            edge_types = list(set(edge.relationship_type for edge in node.outgoing_edges))
        
        # Process each relationship type
        for rel_type in edge_types:
            elements = []
            
            # If max_depth is 1, just get direct relationships
            if max_depth == 1:
                # Get outgoing edges of the specified type
                edges = [e for e in node.outgoing_edges 
                        if e.relationship_type == rel_type and e.confidence >= min_confidence]
                
                # Convert target nodes to elements
                for edge in edges:
                    target_node = edge.target
                    elements.append({
                        "id": target_node.id,
                        "type": target_node.node_type,
                        "confidence": edge.confidence,
                        "metadata": edge.metadata.copy()
                    })
            else:
                # For deeper relationships, use graph search
                for target_id in self.graph.nodes:
                    if target_id == element_id:
                        continue
                    
                    # Find paths to the target
                    paths = self.graph.find_paths(element_id, target_id, max_depth)
                    
                    # Filter paths by relationship type and confidence
                    valid_paths = []
                    for path in paths:
                        # Check if path contains the requested relationship type
                        if any(edge.relationship_type == rel_type for edge in path):
                            # Calculate minimum confidence in the path
                            min_path_confidence = min(edge.confidence for edge in path)
                            if min_path_confidence >= min_confidence:
                                valid_paths.append((path, min_path_confidence))
                    
                    # If valid paths exist, add target to elements
                    if valid_paths:
                        # Get path with highest confidence
                        best_path, best_confidence = max(valid_paths, key=lambda x: x[1])
                        
                        # Get target node
                        target_node = self.graph.get_node(target_id)
                        
                        elements.append({
                            "id": target_node.id,
                            "type": target_node.node_type,
                            "confidence": best_confidence,
                            "path_length": len(best_path),
                            "metadata": {
                                "path": [str(edge) for edge in best_path]
                            }
                        })
            
            # Add elements to result if any found
            if elements:
                related_elements[rel_type] = elements
        
        return related_elements
    
    def find_relationships(self, 
                         source_id: Optional[str] = None,
                         target_id: Optional[str] = None,
                         relationship_types: Optional[List[RelationshipType]] = None,
                         min_confidence: float = 0.0) -> List[Relationship]:
        """Find relationships matching the given criteria.
        
        Args:
            source_id: ID of the source element (optional)
            target_id: ID of the target element (optional)
            relationship_types: Types of relationships to include (all if None)
            min_confidence: Minimum confidence score
            
        Returns:
            List of matching relationships
        """
        matching_relationships = []
        
        # Start with all edges
        edges = []
        if relationship_types:
            for rel_type in relationship_types:
                edges.extend(self.graph.get_edges_by_type(rel_type))
        else:
            edges = self.graph.edges
        
        # Filter by source and target
        for edge in edges:
            # Skip if confidence is too low
            if edge.confidence < min_confidence:
                continue
            
            # Filter by source if provided
            if source_id is not None and edge.source.id != source_id:
                continue
            
            # Filter by target if provided
            if target_id is not None and edge.target.id != target_id:
                continue
            
            # Add matching edge as relationship
            matching_relationships.append(edge.to_relationship())
        
        return matching_relationships
    
    def get_relationship_stats(self) -> Dict[str, Any]:
        """Get statistics about the relationships.
        
        Returns:
            Dictionary with relationship statistics
        """
        return self.graph.get_stats() 