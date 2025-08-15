import sys, os
import traceback
from enum import Enum

try:
    from proj_mapper.models.relationship import RelationshipType
    from proj_mapper.relationship.graph.edge import Edge
    from proj_mapper.relationship.graph.node import Node
    
    print("Imported successfully")
    
    # Create a node instance
    node1 = Node(id='test1', node_type='TEST', data=None)
    node2 = Node(id='test2', node_type='TEST', data=None)
    
    # Create an edge
    edge = Edge(
        source=node1,
        target=node2,
        relationship_type=RelationshipType.REFERENCES,
        confidence=0.9
    )
    
    # Test the to_relationship method
    rel = edge.to_relationship()
    print('Relationship created successfully')
    print(f'Relationship type: {rel.relationship_type}')
    print(f'Has .name: {hasattr(rel.relationship_type, "name")}')
    print(f'Has .value: {hasattr(rel.relationship_type, "value")}')
    
    # Try to access the value
    print(f'Value: {rel.relationship_type.value}')
    
    # Check serialization process
    try:
        import json
        from proj_mapper.utils.json_encoder import EnumEncoder
        data = {
            "relationship_type": rel.relationship_type
        }
        serialized = json.dumps(data, cls=EnumEncoder)
        print(f"Serialized: {serialized}")
    except Exception as e:
        print(f"Serialization error: {e}")
        traceback.print_exc()
    
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc() 