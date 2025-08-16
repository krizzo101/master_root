"""Relationship graph implementation.

This module contains the RelationshipGraph class, which stores and provides 
methods for querying relationships between code and documentation elements.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Iterator, Union
from dataclasses import asdict
import json
import itertools
from pydantic import BaseModel
import os
from enum import Enum

from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.relationship.graph.node import Node
from proj_mapper.relationship.graph.edge import Edge
from proj_mapper.utils.json_encoder import EnumEncoder

logger = logging.getLogger(__name__)


class RelationshipGraph:
    """Graph for storing and querying relationships between elements.
    
    The graph consists of nodes (representing code and documentation elements)
    and edges (representing relationships between elements).
    """
    
    def __init__(self):
        """Initialize an empty relationship graph."""
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._node_type_cache: Dict[Union[CodeElementType, DocumentationType], Set[str]] = {}
    
    def add_node(self, node_id: str, node_type: Union[str, Enum], data: Any = None) -> Node:
        """Add a generic node to the graph.
        
        Args:
            node_id: ID for the node
            node_type: Type of the node (string or enum)
            data: Optional data for the node
            
        Returns:
            The created or existing node
        """
        if node_id in self.nodes:
            # Node already exists, update data if provided
            if data is not None:
                self.nodes[node_id].data = data
            return self.nodes[node_id]
        
        # Create a new node
        node = Node(id=node_id, node_type=node_type, data=data)
        self.nodes[node_id] = node
        
        # Update type cache if node_type is an enum
        if isinstance(node_type, Enum):
            if node_type not in self._node_type_cache:
                self._node_type_cache[node_type] = set()
            self._node_type_cache[node_type].add(node_id)
        
        logger.debug(f"Added node: {node_id} ({node_type})")
        return node
    
    def add_code_element(self, element: CodeElement) -> Node:
        """Add a code element to the graph.
        
        Args:
            element: The code element to add
            
        Returns:
            The created or existing node
        """
        node_id = element.id
        if node_id not in self.nodes:
            node = Node(id=node_id, node_type=element.element_type, data=element)
            self.nodes[node_id] = node
            
            # Update type cache
            element_type = element.element_type
            if element_type not in self._node_type_cache:
                self._node_type_cache[element_type] = set()
            self._node_type_cache[element_type].add(node_id)
            
            logger.debug(f"Added code element node: {node_id} ({element.element_type})")
        return self.nodes[node_id]
    
    def add_documentation_element(self, element: DocumentationElement) -> Node:
        """Add a documentation element to the graph.
        
        Args:
            element: The documentation element to add
            
        Returns:
            The created or existing node
        """
        node_id = element.title
        if node_id not in self.nodes:
            node = Node(id=node_id, node_type=element.element_type, data=element)
            self.nodes[node_id] = node
            
            # Update type cache
            element_type = element.element_type
            if element_type not in self._node_type_cache:
                self._node_type_cache[element_type] = set()
            self._node_type_cache[element_type].add(node_id)
            
            logger.debug(f"Added documentation element node: {node_id} ({element.element_type})")
        return self.nodes[node_id]
    
    def add_edge(self, 
                source_id: str, 
                target_id: str, 
                relationship_type: Union[RelationshipType, str],
                confidence: float,
                metadata: Dict[str, Any] = None) -> Optional[Edge]:
        """Add a relationship edge to the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            relationship_type: Type of relationship (enum or string)
            confidence: Confidence score for the relationship (0.0-1.0)
            metadata: Additional data about the relationship
            
        Returns:
            The created edge, or None if source or target nodes don't exist
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Can't add edge: source or target node not found "
                         f"(source={source_id}, target={target_id})")
            return None
        
        source_node = self.nodes[source_id]
        target_node = self.nodes[target_id]
        
        # Convert string relationship type to enum if needed
        if isinstance(relationship_type, str):
            try:
                relationship_type = getattr(RelationshipType, relationship_type)
                logger.debug(f"Converted string relationship type '{relationship_type}' to enum")
            except AttributeError:
                logger.warning(f"Unknown relationship type: {relationship_type}, using OTHER")
                relationship_type = RelationshipType.OTHER
        
        edge = Edge(
            source=source_node,
            target=target_node,
            relationship_type=relationship_type,
            confidence=confidence,
            metadata=metadata
        )
        
        self.edges.append(edge)
        source_node.add_outgoing_edge(edge)
        target_node.add_incoming_edge(edge)
        
        logger.debug(f"Added edge: {edge}")
        return edge
    
    def add_relationship(self, relationship: Relationship) -> Optional[Edge]:
        """Add a relationship to the graph.
        
        Args:
            relationship: The relationship to add
            
        Returns:
            The created edge, or None if source or target nodes don't exist
        """
        return self.add_edge(
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            relationship_type=relationship.relationship_type,
            confidence=relationship.confidence,
            metadata=relationship.metadata
        )
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID.
        
        Args:
            node_id: The ID of the node to get
            
        Returns:
            The node, or None if not found
        """
        return self.nodes.get(node_id)
    
    def get_nodes_by_type(self, node_type: Union[CodeElementType, DocumentationType]) -> List[Node]:
        """Get all nodes of a specific type.
        
        Args:
            node_type: The type of nodes to get
            
        Returns:
            List of nodes with the specified type
        """
        if node_type not in self._node_type_cache:
            return []
        
        return [self.nodes[node_id] for node_id in self._node_type_cache[node_type]]
    
    def get_edges_by_type(self, relationship_type: RelationshipType) -> List[Edge]:
        """Get all edges of a specific relationship type.
        
        Args:
            relationship_type: The type of relationship to filter by
            
        Returns:
            List of edges with the specified relationship type
        """
        return [edge for edge in self.edges if edge.relationship_type == relationship_type]
    
    def get_relationships(self, 
                        source_id: Optional[str] = None,
                        target_id: Optional[str] = None,
                        relationship_type: Optional[RelationshipType] = None,
                        min_confidence: float = 0.0) -> List[Relationship]:
        """Get relationships matching the specified criteria.
        
        Args:
            source_id: Optional source node ID to filter by
            target_id: Optional target node ID to filter by
            relationship_type: Optional relationship type to filter by
            min_confidence: Minimum confidence score to include
            
        Returns:
            List of relationships matching the criteria
        """
        relationships = []
        
        for edge in self.edges:
            if (source_id is None or edge.source.id == source_id) and \
               (target_id is None or edge.target.id == target_id) and \
               (relationship_type is None or edge.relationship_type == relationship_type) and \
               edge.confidence >= min_confidence:
                
                relationships.append(edge.to_relationship())
        
        return relationships
    
    def get_related_nodes(self, 
                        node_id: str, 
                        relationship_type: Optional[RelationshipType] = None,
                        min_confidence: float = 0.0,
                        outgoing: bool = True,
                        incoming: bool = True) -> List[Node]:
        """Get nodes related to the specified node.
        
        Args:
            node_id: ID of the node to find relations for
            relationship_type: Optional relationship type to filter by
            min_confidence: Minimum confidence score to include
            outgoing: Whether to include outgoing relationships
            incoming: Whether to include incoming relationships
            
        Returns:
            List of related nodes
        """
        if node_id not in self.nodes:
            return []
        
        node = self.nodes[node_id]
        related_nodes = set()
        
        if outgoing:
            for edge in node.outgoing_edges:
                if (relationship_type is None or edge.relationship_type == relationship_type) and \
                   edge.confidence >= min_confidence:
                    related_nodes.add(edge.target)
        
        if incoming:
            for edge in node.incoming_edges:
                if (relationship_type is None or edge.relationship_type == relationship_type) and \
                   edge.confidence >= min_confidence:
                    related_nodes.add(edge.source)
        
        return list(related_nodes)
    
    def find_paths(self, 
                  source_id: str, 
                  target_id: str, 
                  max_depth: int = 3) -> List[List[Edge]]:
        """Find all paths between two nodes up to a maximum depth.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            max_depth: Maximum path depth/length
            
        Returns:
            List of paths, where each path is a list of edges
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        
        # Use BFS to find paths
        paths = []
        queue = [(self.nodes[source_id], [])]  # (node, path_so_far)
        
        while queue:
            current_node, current_path = queue.pop(0)
            
            # Skip if we've reached max depth
            if len(current_path) >= max_depth:
                continue
            
            # Check outgoing edges
            for edge in current_node.outgoing_edges:
                new_path = current_path + [edge]
                
                # If we found the target, add the path
                if edge.target.id == target_id:
                    paths.append(new_path)
                    continue
                
                # Otherwise, add to queue to explore further
                queue.append((edge.target, new_path))
        
        return paths
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize the graph to a dictionary.
        
        Returns:
            Dictionary representation of the graph
        """
        nodes_data = {}
        for node_id, node in self.nodes.items():
            # Handle both string and enum node types
            node_type_str = node.node_type
            if hasattr(node.node_type, 'name'):
                node_type_str = node.node_type.name
                
            node_data = {
                'id': node.id,
                'node_type': node_type_str,
            }
            
            if hasattr(node.data, '__dict__'):
                data_dict = asdict(node.data) if hasattr(node.data, '__dataclass_fields__') else node.data.__dict__
                node_data['data'] = {k: v for k, v in data_dict.items() if not k.startswith('_')}
            
            nodes_data[node_id] = node_data
        
        edges_data = []
        for edge in self.edges:
            # Ensure relationship_type is properly serialized
            rel_type_str = edge.relationship_type
            if hasattr(edge.relationship_type, 'name'):
                rel_type_str = edge.relationship_type.name
                
            edge_data = {
                'source': edge.source.id,
                'target': edge.target.id,
                'relationship_type': rel_type_str,
                'confidence': edge.confidence,
                'metadata': edge.metadata
            }
            edges_data.append(edge_data)
        
        return {
            'nodes': nodes_data,
            'edges': edges_data
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert the graph to JSON.
        
        Args:
            indent: Optional indentation level
            
        Returns:
            JSON string representation
        """
        return json.dumps(self.serialize(), indent=indent, default=str, cls=EnumEncoder)
    
    @classmethod
    def from_json(cls, json_data: Union[str, Dict[str, Any]]) -> 'RelationshipGraph':
        """Create a graph from JSON data.
        
        Args:
            json_data: JSON string or parsed dictionary
            
        Returns:
            Constructed relationship graph
        """
        # This is a placeholder - full implementation would require
        # reconstructing the actual CodeElement and DocumentationElement
        # objects from the serialized data
        raise NotImplementedError("Deserialization not fully implemented yet")
    
    def __str__(self) -> str:
        """Get a string representation of the graph.
        
        Returns:
            String with node and edge counts
        """
        return f"RelationshipGraph(nodes={len(self.nodes)}, edges={len(self.edges)})"
        
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph.
        
        Returns:
            Dictionary with node and edge counts and other statistics
        """
        # Count code and doc nodes
        code_nodes = sum(1 for node in self.nodes.values() if node.node_type in CodeElementType)
        doc_nodes = sum(1 for node in self.nodes.values() if node.node_type in DocumentationType)
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "code_nodes": code_nodes,
            "doc_nodes": doc_nodes
        } 