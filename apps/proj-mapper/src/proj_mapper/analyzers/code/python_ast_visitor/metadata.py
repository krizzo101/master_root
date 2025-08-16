"""Python AST metadata extraction.

This module contains utilities for extracting metadata from AST nodes,
such as docstrings and location information.
"""

import ast
from typing import Optional, Union, TYPE_CHECKING

from proj_mapper.models.code import Location, LocationModel

# Avoid circular import while keeping type checking
if TYPE_CHECKING:
    from proj_mapper.analyzers.code.python_ast_visitor.visitor import PythonASTVisitor


class MetadataExtractor:
    """Extractor for metadata from AST nodes.
    
    This class provides utilities for extracting metadata like docstrings
    and location information from AST nodes.
    """
    
    def __init__(self, visitor: 'PythonASTVisitor'):
        """Initialize the metadata extractor.
        
        Args:
            visitor: The AST visitor that will use this extractor
        """
        self.visitor = visitor
    
    def get_docstring(self, node: Union[ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]:
        """Extract docstring from a node.
        
        Args:
            node: The AST node
            
        Returns:
            The docstring, or None if no docstring found
        """
        if not node.body:
            return None
            
        # Look for docstring (first statement in body is a string)
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Str):
            return first.value.s
            
        # Handle Python 3.8+ style docstrings with Constant
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            return first.value.value
            
        return None
    
    def get_location(self, node: ast.AST) -> LocationModel:
        """Get a LocationModel object for an AST node.
        
        Args:
            node: The AST node
            
        Returns:
            A LocationModel object
        """
        # Get line information if available
        start_line = getattr(node, 'lineno', 0)
        end_line = getattr(node, 'end_lineno', start_line)
        
        # Get column information if available
        start_col = getattr(node, 'col_offset', None)
        end_col = getattr(node, 'end_col_offset', None)
        
        return LocationModel(
            file_path=self.visitor.file_path,
            start_line=start_line,
            end_line=end_line,
            start_column=start_col,
            end_column=end_col
        ) 