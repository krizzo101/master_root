#!/usr/bin/env python3
"""Test script for relationship graph serialization fixes."""

import sys
import json
import logging
from pathlib import Path

# Setup logging to file
log_dir = Path("./log")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "test_fix.log"

# Configure file logger
file_handler = logging.FileHandler(filename=log_file, mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)

# Configure console logger (INFO only)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_file}")

def main():
    """Test the relationship graph with serialization fixes."""
    logger.info("Testing relationship graph serialization...")
    
    try:
        # Import the relationship graph
        from proj_mapper.relationship.graph.graph import RelationshipGraph
        from proj_mapper.models.code import CodeElementType
        from proj_mapper.models.relationship import RelationshipType
        from proj_mapper.models.documentation import DocumentationType
        
        # Create a new graph
        graph = RelationshipGraph()
        
        # Test with enum and string node types
        logger.debug("Adding nodes with both enum and string types...")
        
        # Add code elements
        graph.add_node("code_element_1", CodeElementType.CLASS)
        graph.add_node("code_element_2", "FUNCTION")  # String type
        
        # Add documentation elements  
        graph.add_node("doc_element_1", DocumentationType.MARKDOWN)
        graph.add_node("doc_element_2", "DOCSTRING")  # String type
        
        # Log node types
        for node_id, node in graph.nodes.items():
            logger.debug(f"Node {node_id}: type={type(node.node_type)}, value={node.node_type}")
        
        # Add edges with both enum and string relationship types
        logger.debug("Adding edges with both enum and string relationship types...")
        
        # Add edges with enum types
        graph.add_edge("code_element_1", "doc_element_1", RelationshipType.DOCUMENTS, 0.9)
        
        # Add edges with string types
        graph.add_edge("code_element_2", "doc_element_2", "REFERENCES", 0.85)
        
        # Log edge types
        for edge in graph.edges:
            logger.debug(f"Edge {edge.source.id} -> {edge.target.id}: " 
                        f"type={type(edge.relationship_type)}, value={edge.relationship_type}")
        
        # Serialize the graph
        logger.info("Serializing graph...")
        serialized = graph.serialize()
        
        # Convert to JSON
        json_data = json.dumps(serialized, indent=2)
        
        # Save to file
        output_file = "test_graph.json"
        with open(output_file, "w") as f:
            f.write(json_data)
        
        logger.info(f"Serialization successful! Saved to {output_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.debug("Traceback:", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 