"""Python AST utilities.

This module contains utility functions for working with Python's AST.
"""

import ast
from typing import Optional, Any

class ASTUtils:
    """Utility functions for working with Python's AST.
    
    This class provides utility functions for extracting information
    from AST nodes and converting them to string representations.
    """
    
    def extract_annotation(self, annotation: Optional[ast.AST]) -> Optional[str]:
        """Extract a type annotation as a string.
        
        Args:
            annotation: The annotation AST node
            
        Returns:
            The annotation as a string, or None if no annotation
        """
        if annotation is None:
            return None
            
        return self.node_to_str(annotation)
    
    def base_to_str(self, node: ast.AST) -> str:
        """Convert a base class AST node to a string.
        
        Args:
            node: The AST node for a base class
            
        Returns:
            String representation of the base class
        """
        return self.node_to_str(node)
    
    def node_to_str(self, node: Optional[ast.AST]) -> Optional[str]:
        """Convert an AST node to a string representation.
        
        Args:
            node: The AST node to convert
            
        Returns:
            String representation of the node, or None if node is None
        """
        if node is None:
            return None
            
        try:
            # Use ast.unparse in Python 3.9+
            return ast.unparse(node)
        except (AttributeError, ValueError):
            # Fallback for Python < 3.9
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Str):
                return f'"{node.s}"'
            elif isinstance(node, ast.Num):
                return str(node.n)
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, str):
                    return f'"{node.value}"'
                return str(node.value)
            return repr(node)
            
    def get_full_name(self, node: ast.AST) -> str:
        """Get the full name of an attribute or name node.
        
        Args:
            node: The AST node
            
        Returns:
            The full name as a string
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_name(node.value)}.{node.attr}"
        return self.node_to_str(node) 