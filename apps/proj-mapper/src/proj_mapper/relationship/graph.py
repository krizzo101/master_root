"""Graph structure for storing and querying relationships.

This module is kept for backward compatibility and imports
from the refactored submodules.
"""

# Import from the refactored modules
from proj_mapper.relationship.graph.node import Node
from proj_mapper.relationship.graph.edge import Edge
from proj_mapper.relationship.graph.graph import RelationshipGraph

# Re-export the classes
__all__ = ['Node', 'Edge', 'RelationshipGraph'] 