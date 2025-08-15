"""Relationship graph for Project Mapper.

This module implements a graph structure for storing and querying relationships
between code and documentation elements. This package exports the same interface
as the original module to maintain backward compatibility.
"""

from proj_mapper.relationship.graph.node import Node
from proj_mapper.relationship.graph.edge import Edge
from proj_mapper.relationship.graph.graph import RelationshipGraph

__all__ = ["Node", "Edge", "RelationshipGraph"] 