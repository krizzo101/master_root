import sys
import traceback
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from proj_mapper.models.relationship import RelationshipType
    from proj_mapper.cli.commands.relationship.discovery import _build_relationship_graph
    
    # Create test relationships that mimic the real data
    test_relationships = [
        {
            "source_id": "test_source_1",
            "target_id": "test_target_1",
            "relationship_type": "DOCUMENTS",  # String version
            "confidence": 0.9,
            "metadata": {}
        },
        {
            "source_id": "test_source_2",
            "target_id": "test_target_2",
            "relationship_type": RelationshipType.REFERENCES,  # Enum version
            "confidence": 0.85,
            "metadata": {}
        }
    ]
    
    # Create a patched version of _build_relationship_graph with detailed debug info
    def debug_build_graph(relationships):
        """Debug version of _build_relationship_graph with extra tracing."""
        print(f"Building graph with {len(relationships)} relationships")
        
        # Process each relationship to ensure consistency
        for i, rel in enumerate(relationships):
            print(f"Processing relationship {i+1}:")
            for key, value in rel.items():
                print(f"  {key}: {repr(value)} (type: {type(value)})")
                
                # Handle relationship_type specifically
                if key == "relationship_type":
                    if isinstance(value, str):
                        print("    relationship_type is a string")
                    elif hasattr(value, "name"):
                        print(f"    relationship_type has name: {value.name}")
                        # Update the relationship to use name consistently
                        rel[key] = value.name
                        print(f"    Updated to: {rel[key]}")
            print()
        
        # Now try to use the original function with our preprocessed data
        try:
            print("Calling original _build_relationship_graph...")
            graph = _build_relationship_graph(relationships)
            print("Graph built successfully!")
            return graph
        except Exception as e:
            print(f"Error building graph: {e}")
            traceback.print_exc()
            return None
    
    # Test the original function directly
    print("Testing original _build_relationship_graph with test data...")
    try:
        graph = _build_relationship_graph(test_relationships)
        print("Original function succeeded!")
    except Exception as e:
        print(f"Original function failed: {e}")
        traceback.print_exc()
    
    # Test our debug version
    print("\nTesting debug_build_graph with test data...")
    graph = debug_build_graph(test_relationships)
    
    if graph:
        print("Graph built successfully!")
        
        # Try to serialize the graph
        try:
            serialized = graph.serialize()
            print("Graph serialized successfully!")
            
            # Write to file for inspection
            with open("debug_graph.json", "w") as f:
                json.dump(serialized, f, indent=2)
            print("Graph saved to debug_graph.json")
        except Exception as e:
            print(f"Error serializing graph: {e}")
            traceback.print_exc()
    
except Exception as e:
    print(f"Error in script execution: {e}")
    traceback.print_exc() 