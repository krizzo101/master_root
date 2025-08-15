import sys
import os
import importlib
import traceback

def get_module_functions(module_path):
    """Get functions from a module."""
    try:
        module = importlib.import_module(module_path)
        functions = []
        
        for name in dir(module):
            attr = getattr(module, name)
            if callable(attr) and attr.__module__ == module.__name__:
                functions.append((name, attr))
                
        return functions
    except Exception as e:
        print(f"Error getting functions from {module_path}: {e}")
        return []

def find_relationship_value_usages():
    """Find places where relationship_type.value might be used."""
    # Modules to check
    modules_to_check = [
        "proj_mapper.models.relationship",
        "proj_mapper.cli.commands.relationship.discovery",
        "proj_mapper.relationship.graph.graph",
        "proj_mapper.relationship.graph.edge",
        "proj_mapper.relationship.mapper"
    ]
    
    for module_path in modules_to_check:
        print(f"Checking {module_path}...")
        functions = get_module_functions(module_path)
        
        for name, func in functions:
            try:
                # Check for function code access
                if hasattr(func, "__code__"):
                    # Check function source if possible
                    import inspect
                    if inspect.isfunction(func) or inspect.ismethod(func):
                        source = inspect.getsource(func)
                        if "relationship_type" in source and ".value" in source:
                            print(f"  Potential usage in {name}: {source}")
            except Exception as e:
                print(f"  Error checking {name}: {e}")

# Define fixes for the enum.value issue
def fix_relationship_enums():
    """Fix the enum.value issue with relationship types."""
    try:
        # 1. Fix the edge_to_dict function in discovery.py
        from proj_mapper.cli.commands.relationship.discovery import _edge_to_dict
        
        def patched_edge_to_dict(edge):
            """Convert an Edge object to a dictionary."""
            return {
                "source_id": edge.source.id,
                "target_id": edge.target.id,
                "relationship_type": edge.relationship_type.name,  # Use name instead of value
                "confidence": edge.confidence,
                "metadata": edge.metadata
            }
        
        # Apply the patch
        import types
        from proj_mapper.cli.commands.relationship import discovery
        discovery._edge_to_dict = patched_edge_to_dict
        print("Patched discovery._edge_to_dict")
        
        # 2. Fix the graph module to use name consistently
        from proj_mapper.relationship.graph import graph
        
        # Find the serialize method in RelationshipGraph
        original_serialize = graph.RelationshipGraph.serialize
        
        def patched_serialize(self):
            """Serialize the graph to a dictionary with consistent name usage."""
            nodes_data = {}
            for node_id, node in self.nodes.items():
                node_type_value = node.node_type
                # Ensure node_type is correctly serialized
                if hasattr(node_type_value, 'name'):
                    node_type_str = node_type_value.name
                else:
                    node_type_str = str(node_type_value)
                    
                node_data = {
                    'id': node.id,
                    'node_type': node_type_str,
                }
                
                # Handle node data similarly
                if hasattr(node.data, '__dict__'):
                    try:
                        from dataclasses import asdict
                        data_dict = asdict(node.data) if hasattr(node.data, '__dataclass_fields__') else node.data.__dict__
                        node_data['data'] = {k: v for k, v in data_dict.items() if not k.startswith('_')}
                    except Exception as e:
                        node_data['data'] = f"Error serializing: {str(e)}"
                
                nodes_data[node_id] = node_data
            
            edges_data = []
            for edge in self.edges:
                # Get relationship type as string
                rel_type = edge.relationship_type
                rel_type_str = rel_type.name if hasattr(rel_type, 'name') else str(rel_type)
                
                edge_data = {
                    'source': edge.source.id,
                    'target': edge.target.id,
                    'relationship_type': rel_type_str,  # Always use name
                    'confidence': edge.confidence,
                    'metadata': edge.metadata
                }
                edges_data.append(edge_data)
            
            return {
                'nodes': nodes_data,
                'edges': edges_data
            }
        
        # Apply the patch
        graph.RelationshipGraph.serialize = patched_serialize
        print("Patched graph.RelationshipGraph.serialize")
        
        # 3. Fix the add_node method to handle node_type consistently
        original_add_node = getattr(graph.RelationshipGraph, 'add_node', None)
        if original_add_node:
            def patched_add_node(self, node_id, node_type, data=None):
                """Add a node with proper node_type handling."""
                # Ensure node_type is correctly handled
                from proj_mapper.models.code import CodeElementType
                from proj_mapper.models.documentation import DocumentationType
                
                # Convert string node_type to enum if needed
                if isinstance(node_type, str):
                    # Try to map string to enum
                    if hasattr(CodeElementType, node_type):
                        node_type = getattr(CodeElementType, node_type)
                    elif hasattr(DocumentationType, node_type):
                        node_type = getattr(DocumentationType, node_type)
                
                # Call original method
                return original_add_node(self, node_id, node_type, data)
            
            # Apply the patch
            graph.RelationshipGraph.add_node = patched_add_node
            print("Patched graph.RelationshipGraph.add_node")
        else:
            print("WARNING: Could not find add_node method to patch")
        
        return True
    except Exception as e:
        print(f"Error applying fixes: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Searching for potential enum.value usages...")
    find_relationship_value_usages()
    
    print("\nApplying fixes...")
    if fix_relationship_enums():
        print("\nFixes applied successfully. Try running the command:")
        print("python -m proj_mapper relationship detect-relationships --code-dir src --docs-dir docs --output-file relationships.json --include-code \"*.py\" --exclude-code \"__pycache__,venv\"")
    else:
        print("\nFailed to apply fixes. Check errors above.") 