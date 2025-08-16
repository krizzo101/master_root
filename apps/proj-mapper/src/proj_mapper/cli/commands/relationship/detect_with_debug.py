"""Run relationship detection with debug tracing enabled.

This script runs a simplified relationship detection test with debug tracing
to help identify issues with relationship_type handling.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir.parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('log/debug_detect.log', mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('proj_mapper.detect_debug')
logger.info("Initializing debug detection script")

try:
    # Import necessary modules
    from proj_mapper.models.relationship import RelationshipType, Relationship
    from proj_mapper.relationship.graph.graph import RelationshipGraph
    from proj_mapper.relationship.graph.edge import Edge
    from proj_mapper.cli.commands.relationship.debug_tracer import setup_debug_tracing
    
    # Install the debug tracer
    logger.info("Setting up debug tracing")
    tracer = setup_debug_tracing()
    
    # Create a custom string wrapper class for relationship types
    logger.info("Setting up string wrapper for relationship types")
    
    class EnumString(str):
        """String subclass that mimics enum behavior by adding value and name properties."""
        
        @property
        def value(self):
            """Mimic the value property of an enum."""
            logger.debug(f"EnumString.value accessed for '{self}'")
            return self
            
        @property
        def name(self):
            """Mimic the name property of an enum."""
            logger.debug(f"EnumString.name accessed for '{self}'")
            return self
    
    # Direct test of RelationshipType enum
    logger.info("Testing RelationshipType enum directly")
    
    # Test with enum
    rel_type_enum = RelationshipType.IMPLEMENTS
    logger.info(f"Created enum: {rel_type_enum}, type: {type(rel_type_enum)}")
    logger.info(f"Enum name: {rel_type_enum.name}, value: {rel_type_enum.value}")
    
    # Test with string
    rel_type_str = "IMPLEMENTS"
    rel_type_enum_str = EnumString(rel_type_str)
    logger.info(f"Created string: {rel_type_str}, type: {type(rel_type_str)}")
    logger.info(f"String with enum behavior: {rel_type_enum_str}, type: {type(rel_type_enum_str)}")
    logger.info(f"String name: {rel_type_enum_str.name}, value: {rel_type_enum_str.value}")
    
    # Test creating relationships with both types
    logger.info("Testing Relationship creation")
    
    # With enum
    rel_enum = Relationship(
        source_id="source1",
        target_id="target1",
        relationship_type=RelationshipType.IMPLEMENTS,
        confidence=0.9
    )
    logger.info(f"Created relationship with enum: {rel_enum}")
    logger.info(f"Relationship type: {rel_enum.relationship_type}, type: {type(rel_enum.relationship_type)}")
    
    # With string
    rel_str = Relationship(
        source_id="source2",
        target_id="target2",
        relationship_type="IMPLEMENTS",
        confidence=0.8
    )
    logger.info(f"Created relationship with string: {rel_str}")
    logger.info(f"Relationship type: {rel_str.relationship_type}, type: {type(rel_str.relationship_type)}")
    
    # Test Edge creation and conversion
    logger.info("Testing Edge creation and conversion")
    
    # Create a graph
    graph = RelationshipGraph()
    
    # Add edges with both types
    graph.add_node("source1", "code", {})
    graph.add_node("target1", "doc", {})
    graph.add_node("source2", "code", {})
    graph.add_node("target2", "doc", {})
    
    # Add edge with enum
    graph.add_edge("source1", "target1", RelationshipType.IMPLEMENTS, 0.9)
    logger.info("Added edge with enum relationship type")
    
    # Add edge with string
    graph.add_edge("source2", "target2", "IMPLEMENTS", 0.8)
    logger.info("Added edge with string relationship type")
    
    # Serialize the graph
    logger.info("Testing graph serialization")
    graph_data = graph.serialize()
    logger.info(f"Serialized graph with {len(graph_data['edges'])} edges")
    
    # Look at the edges
    for i, edge in enumerate(graph.edges):
        logger.info(f"Edge {i}: {edge}, relationship_type: {edge.relationship_type}, type: {type(edge.relationship_type)}")
        
        # Convert to relationship
        rel = edge.to_relationship()
        logger.info(f"Converted to relationship: {rel}, relationship_type: {rel.relationship_type}, type: {type(rel.relationship_type)}")
    
    # Test serialization to dict
    logger.info("Testing edge to dict conversion")
    
    from proj_mapper.cli.commands.relationship.discovery import _edge_to_dict
    
    for i, edge in enumerate(graph.edges):
        edge_dict = _edge_to_dict(edge)
        logger.info(f"Edge {i} dict: {edge_dict}")
        logger.info(f"relationship_type in dict: {edge_dict['relationship_type']}, type: {type(edge_dict['relationship_type'])}")
    
    logger.info("All direct tests completed successfully")
    
except ImportError as e:
    logger.exception(f"Import error: {e}")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
finally:
    if 'tracer' in locals():
        logger.info("Unpatching debug tracer")
        tracer.unpatch_all()
    
logger.info("Debug detection script completed") 