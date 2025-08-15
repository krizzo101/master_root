import sys
import os
from enum import Enum
import traceback
import types
import inspect
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def patch_module(module_path, function_name, replacement):
    try:
        # Import the module
        module = importlib.import_module(module_path)
        
        # Get the original function
        original_func = getattr(module, function_name)
        
        # Set our patched function
        setattr(module, function_name, replacement)
        
        print(f"Successfully patched {module_path}.{function_name}")
        return original_func
    except Exception as e:
        print(f"Failed to patch {module_path}.{function_name}: {e}")
        traceback.print_exc()
        return None

def patch_enum_access():
    """Monkey patch all the places where Enum.value might be used incorrectly."""
    try:
        # 1. Patch RelationshipType to handle .value correctly
        from proj_mapper.models.relationship import RelationshipType
        from proj_mapper.models.code import CodeElementType
        from proj_mapper.models.documentation import DocumentationType
        
        # Patch all enums that use auto()
        for enum_cls in [RelationshipType, CodeElementType, DocumentationType]:
            # Add a property to get the value as name if it's accessed directly
            original_get = enum_cls.__getattribute__
            
            def new_getattribute(self, name):
                if name == 'value':
                    # Log this access to find where it's happening
                    stack = traceback.extract_stack()
                    caller = stack[-2]  # Stack is: 1. this function, 2. caller
                    logger.debug(f"Enum.value accessed at {caller.filename}:{caller.lineno} for {self}")
                    
                    # If value is accessed and it's an auto() enum, return the name
                    # This handles the case where enum.auto() is used
                    return self.name
                return original_get(self, name)
            
            enum_cls.__getattribute__ = new_getattribute
            print(f"Successfully patched {enum_cls.__name__}.__getattribute__")
        
        # 2. Patch other potential issue areas
        
        # Patch add_edge in the graph to use name instead of value
        from proj_mapper.relationship.graph.graph import RelationshipGraph
        original_add_edge = RelationshipGraph.add_edge
        
        def patched_add_edge(self, source_id, target_id, relationship_type, confidence, metadata=None):
            # Ensure relationship_type is handled properly
            if hasattr(relationship_type, 'name'):
                # Use name attribute if it exists
                logger.debug(f"Using name for relationship_type in add_edge: {relationship_type.name}")
                return original_add_edge(self, source_id, target_id, relationship_type, confidence, metadata)
            else:
                # Handle string relationship type
                logger.debug(f"Converting string relationship_type to enum: {relationship_type}")
                enum_type = getattr(RelationshipType, relationship_type, RelationshipType.OTHER)
                return original_add_edge(self, source_id, target_id, enum_type, confidence, metadata)
        
        RelationshipGraph.add_edge = patched_add_edge
        print("Successfully patched RelationshipGraph.add_edge")
        
        # 3. Patch _build_relationship_graph in discovery
        from proj_mapper.cli.commands.relationship.discovery import _build_relationship_graph
        original_build_graph = _build_relationship_graph
        
        def patched_build_graph(relationships):
            # Log the relationship data
            logger.debug(f"Building graph with {len(relationships)} relationships")
            for i, rel in enumerate(relationships):
                logger.debug(f"Relationship {i}: {rel}")
                # Ensure relationship_type is a string
                if isinstance(rel.get('relationship_type'), str):
                    logger.debug(f"Relationship_type is already a string: {rel['relationship_type']}")
                elif hasattr(rel.get('relationship_type'), 'name'):
                    logger.debug(f"Converting relationship_type to string: {rel['relationship_type'].name}")
                    rel['relationship_type'] = rel['relationship_type'].name
            
            return original_build_graph(relationships)
        
        # Apply the patch
        patch_module("proj_mapper.cli.commands.relationship.discovery", "_build_relationship_graph", patched_build_graph)
        
        return True
    except Exception as e:
        print(f"Failed to patch enum handling: {e}")
        traceback.print_exc()
        return False

# Define patched functions that use name instead of value
def patched_edge_to_dict(edge):
    """Convert an Edge object to a dictionary."""
    return {
        "source_id": edge.source.id,
        "target_id": edge.target.id,
        "relationship_type": edge.relationship_type.name,  # Use name instead of value
        "confidence": edge.confidence,
        "metadata": edge.metadata
    }

# Now apply the patches
print("Applying patches to use enum names instead of values...")

# Patch the edge_to_dict function to use name instead of value
original_edge_to_dict = patch_module(
    "proj_mapper.cli.commands.relationship.discovery", 
    "_edge_to_dict", 
    patched_edge_to_dict
)

# Print the original and patched functions for comparison
if original_edge_to_dict:
    print("\nOriginal function:")
    print(inspect.getsource(original_edge_to_dict))
    
    print("\nPatched function:")
    print(inspect.getsource(patched_edge_to_dict))
    
    print("\nPatches applied successfully. Try running the command again.")
    print("python -m proj_mapper relationship detect-relationships [args]")
else:
    print("Failed to apply patches. Check error messages above.")

# Apply enum access patch
print("Applying comprehensive enum patches...")
if patch_enum_access():
    print("\nEnum patches applied successfully. Try running the command again.")
    print("python -m proj_mapper relationship detect-relationships [args]")
else:
    print("\nFailed to apply enum patches. Check error messages above.") 