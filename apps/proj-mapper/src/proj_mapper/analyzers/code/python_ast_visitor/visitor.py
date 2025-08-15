"""Python AST visitor core implementation.

This module contains the core implementation of the Python AST visitor class
responsible for traversing the AST and coordinating the extraction of code elements.
"""

import ast
import logging
from typing import Dict, List, Optional, Any, Set, Union, cast

from proj_mapper.models.code import CodeElement, CodeElementType, Location, Visibility
from proj_mapper.analyzers.code.python_ast_visitor.node_processors import NodeProcessors
from proj_mapper.analyzers.code.python_ast_visitor.metadata import MetadataExtractor
from proj_mapper.analyzers.code.python_ast_visitor.utils import ASTUtils

# Configure logging
logger = logging.getLogger(__name__)


class PythonASTVisitor(ast.NodeVisitor):
    """Visitor for traversing Python's AST and extracting code elements.
    
    This class visits AST nodes and extracts information about classes, functions,
    methods, and other code elements.
    """
    
    def __init__(self, file_path: str, module_name: Optional[str] = None):
        """Initialize the AST visitor.
        
        Args:
            file_path: Path to the file being analyzed
            module_name: Name of the module (optional)
        """
        self.file_path = file_path
        self.module_name = module_name
        self.current_class: Optional[str] = None
        self.current_parent_id: Optional[str] = None
        self.elements: List[CodeElement] = []
        self.imports: List[Dict[str, Any]] = []
        self.module_docstring: Optional[str] = None
        self.id_counter = 0
        
        # Keep track of assignments for name resolution
        self.assignments: Dict[str, str] = {}
        
        # Keep track of parent-child relationships
        self.children: Dict[str, List[str]] = {}
        
        # Initialize helper components
        self.utils = ASTUtils()
        self.metadata = MetadataExtractor(self)
        self.node_processors = NodeProcessors(self)
    
    def _get_next_id(self) -> str:
        """Get the next unique ID.
        
        Returns:
            A unique ID string
        """
        self.id_counter += 1
        return f"py_{self.id_counter}"
    
    def _add_child_relationship(self, parent_id: str, child_id: str) -> None:
        """Add a parent-child relationship.
        
        Args:
            parent_id: ID of the parent element
            child_id: ID of the child element
        """
        if parent_id not in self.children:
            self.children[parent_id] = []
        self.children[parent_id].append(child_id)
    
    def _get_qualified_name(self, name: str) -> str:
        """Get a qualified name including module and class.
        
        Args:
            name: The base name
            
        Returns:
            The qualified name
        """
        if self.current_class:
            if self.module_name:
                return f"{self.module_name}.{self.current_class}.{name}"
            return f"{self.current_class}.{name}"
        elif self.module_name:
            return f"{self.module_name}.{name}"
        else:
            return name
    
    def _get_visibility(self, name: str) -> Visibility:
        """Determine visibility from name based on Python conventions.
        
        Args:
            name: The name to check
            
        Returns:
            The visibility level
        """
        if name.startswith('__') and not name.endswith('__'):
            return Visibility.PRIVATE
        elif name.startswith('_'):
            return Visibility.PROTECTED
        else:
            return Visibility.PUBLIC
    
    def visit_Module(self, node: ast.Module) -> None:
        """Visit a module node.
        
        Args:
            node: The module node
        """
        # Extract module docstring
        self.module_docstring = self.metadata.get_docstring(node)
        
        # Create a module element
        module_id = self._get_next_id()
        module_name = self.module_name or ""
        
        module_element = CodeElement(
            id=module_id,
            name=module_name,
            element_type=CodeElementType.MODULE,
            file_path=self.file_path,
            line_start=1,
            line_end=None,  # We don't know the end line yet
            module=None,  # A module doesn't have a parent module in this context
            docstring=self.module_docstring,
            visibility=Visibility.PUBLIC
        )
        
        self.elements.append(module_element)
        
        # Set this as the current parent
        old_parent = self.current_parent_id
        self.current_parent_id = module_id
        
        # Visit all children
        self.generic_visit(node)
        
        # Restore parent
        self.current_parent_id = old_parent
        
        # Update the module element with the end line
        module_element.line_end = len(node.body)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition.
        
        Args:
            node: The class definition node
        """
        self.node_processors.process_class_def(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition.
        
        Args:
            node: The function definition node
        """
        self.node_processors.process_function_def(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an async function definition.
        
        Args:
            node: The async function definition node
        """
        self.node_processors.process_async_function_def(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit an import statement.
        
        Args:
            node: The import statement node
        """
        self.node_processors.process_import(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit an import from statement.
        
        Args:
            node: The import from statement node
        """
        self.node_processors.process_import_from(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit an assignment statement.
        
        Args:
            node: The assignment statement node
        """
        self.node_processors.process_assign(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit an annotated assignment statement.
        
        Args:
            node: The annotated assignment statement node
        """
        self.node_processors.process_ann_assign(node) 