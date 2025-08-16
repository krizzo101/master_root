"""Node implementation for relationship graph.

This module contains the Node class, which represents elements in the graph.
"""

from typing import List, Optional, Any, Union

from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement, DocumentationType

# Forward reference
if False:  # Only for type checking
    from proj_mapper.relationship.graph.edge import Edge


class Node:
    """Node in the relationship graph.
    
    Represents an element (code or documentation) in the relationship graph.
    """
    
    def __init__(self, 
                id: str, 
                node_type: Union[CodeElementType, DocumentationType], 
                data: Any = None):
        """Initialize a graph node.
        
        Args:
            id: Unique identifier for the node
            node_type: Type of the node
            data: Optional data associated with this node
        """
        self.id = id
        self.node_type = node_type
        self.data = data
        self.outgoing_edges: List['Edge'] = []
        self.incoming_edges: List['Edge'] = []
    
    def add_outgoing_edge(self, edge: 'Edge') -> None:
        """Add an outgoing edge from this node.
        
        Args:
            edge: The edge to add
        """
        self.outgoing_edges.append(edge)
    
    def add_incoming_edge(self, edge: 'Edge') -> None:
        """Add an incoming edge to this node.
        
        Args:
            edge: The edge to add
        """
        self.incoming_edges.append(edge)
    
    def __str__(self) -> str:
        """Get string representation of the node.
        
        Returns:
            String representation with type and edge counts
        """
        return f"{self.node_type}:{self.id} (out:{len(self.outgoing_edges)}, in:{len(self.incoming_edges)})" 