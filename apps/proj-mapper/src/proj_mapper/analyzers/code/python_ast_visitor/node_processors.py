"""Python AST node processors.

This module contains processors for different AST node types.
"""

import ast
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING

from proj_mapper.models.code import CodeElement, CodeElementType, Location, Visibility

# Avoid circular import while keeping type checking
if TYPE_CHECKING:
    from proj_mapper.analyzers.code.python_ast_visitor.visitor import PythonASTVisitor


class NodeProcessors:
    """Processors for different AST node types.
    
    This class contains methods for processing different types of AST nodes
    and extracting code elements from them.
    """
    
    def __init__(self, visitor: 'PythonASTVisitor'):
        """Initialize the node processors.
        
        Args:
            visitor: The AST visitor that will use these processors
        """
        self.visitor = visitor
    
    def process_class_def(self, node: ast.ClassDef) -> None:
        """Process a class definition.
        
        Args:
            node: The class definition node
        """
        # Extract information
        class_name = node.name
        docstring = self.visitor.metadata.get_docstring(node)
        bases = [self.visitor.utils.base_to_str(base) for base in node.bases]
        location = self.visitor.metadata.get_location(node)
        visibility = self.visitor._get_visibility(class_name)
        
        # Generate ID and create element
        class_id = self.visitor._get_next_id()
        qualified_name = self.visitor._get_qualified_name(class_name)
        
        class_element = CodeElement(
            id=class_id,
            name=class_name,
            element_type=CodeElementType.CLASS,
            file_path=self.visitor.file_path,
            line_start=location.start_line,
            line_end=location.end_line,
            module=self.visitor.module_name,
            parent_id=self.visitor.current_parent_id,
            docstring=docstring,
            visibility=visibility,
            metadata={
                "bases": bases,
                "qualified_name": qualified_name
            }
        )
        
        self.visitor.elements.append(class_element)
        
        # Add to parent's children
        if self.visitor.current_parent_id:
            self.visitor._add_child_relationship(self.visitor.current_parent_id, class_id)
            
        # Set as current class and parent
        old_class = self.visitor.current_class
        old_parent = self.visitor.current_parent_id
        self.visitor.current_class = class_name
        self.visitor.current_parent_id = class_id
        
        # Visit all children
        self.visitor.generic_visit(node)
        
        # Restore class and parent
        self.visitor.current_class = old_class
        self.visitor.current_parent_id = old_parent
    
    def process_function_def(self, node: ast.FunctionDef) -> None:
        """Process a function definition.
        
        Args:
            node: The function definition node
        """
        self._process_function(node)
    
    def process_async_function_def(self, node: ast.AsyncFunctionDef) -> None:
        """Process an async function definition.
        
        Args:
            node: The async function definition node
        """
        self._process_function(node, is_async=True)
    
    def _process_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool = False) -> None:
        """Process a function or method definition.
        
        Args:
            node: The function definition node
            is_async: Whether this is an async function
        """
        # Extract information
        func_name = node.name
        docstring = self.visitor.metadata.get_docstring(node)
        location = self.visitor.metadata.get_location(node)
        visibility = self.visitor._get_visibility(func_name)
        
        # Determine if this is a method or function
        element_type = CodeElementType.METHOD if self.visitor.current_class else CodeElementType.FUNCTION
        
        # Extract parameter information
        parameters = []
        for arg in node.args.args:
            param_name = arg.arg
            param_type = self.visitor.utils.extract_annotation(arg.annotation)
            parameters.append({
                "name": param_name,
                "type": param_type
            })
        
        # Handle varargs and kwargs
        if node.args.vararg:
            parameters.append({
                "name": f"*{node.args.vararg.arg}",
                "type": self.visitor.utils.extract_annotation(node.args.vararg.annotation)
            })
        
        if node.args.kwarg:
            parameters.append({
                "name": f"**{node.args.kwarg.arg}",
                "type": self.visitor.utils.extract_annotation(node.args.kwarg.annotation)
            })
        
        # Extract return type
        return_type = self.visitor.utils.extract_annotation(node.returns)
        
        # Check for staticmethod or classmethod decorators
        is_static = False
        is_class_method = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'staticmethod':
                    is_static = True
                elif decorator.id == 'classmethod':
                    is_class_method = True
        
        # Generate ID and create element
        func_id = self.visitor._get_next_id()
        qualified_name = self.visitor._get_qualified_name(func_name)
        
        # Create signature
        args_str = ", ".join([p["name"] for p in parameters])
        signature = f"{func_name}({args_str})"
        if return_type:
            signature += f" -> {return_type}"
        
        func_element = CodeElement(
            id=func_id,
            name=func_name,
            element_type=element_type,
            file_path=self.visitor.file_path,
            line_start=location.start_line,
            line_end=location.end_line,
            module=self.visitor.module_name,
            parent_id=self.visitor.current_parent_id,
            docstring=docstring,
            visibility=visibility,
            is_static=is_static,
            signature=signature,
            metadata={
                "parameters": parameters,
                "return_type": return_type,
                "is_async": is_async,
                "is_class_method": is_class_method,
                "qualified_name": qualified_name
            }
        )
        
        self.visitor.elements.append(func_element)
        
        # Add to parent's children
        if self.visitor.current_parent_id:
            self.visitor._add_child_relationship(self.visitor.current_parent_id, func_id)
        
        # Visit function body
        old_parent = self.visitor.current_parent_id
        self.visitor.current_parent_id = func_id
        self.visitor.generic_visit(node)
        self.visitor.current_parent_id = old_parent
    
    def process_import(self, node: ast.Import) -> None:
        """Process an import statement.
        
        Args:
            node: The import statement node
        """
        for name in node.names:
            self.visitor.imports.append({
                "from": None,
                "import": name.name,
                "alias": name.asname
            })
        
        # Continue visiting
        self.visitor.generic_visit(node)
    
    def process_import_from(self, node: ast.ImportFrom) -> None:
        """Process an import from statement.
        
        Args:
            node: The import from statement node
        """
        module = node.module
        for name in node.names:
            self.visitor.imports.append({
                "from": module,
                "import": name.name,
                "alias": name.asname
            })
        
        # Continue visiting
        self.visitor.generic_visit(node)
    
    def process_assign(self, node: ast.Assign) -> None:
        """Process an assignment statement.
        
        Args:
            node: The assignment statement node
        """
        # Track top-level assignments
        if self.visitor.current_parent_id and not self.visitor.current_class:
            # Only handle simple assignments to names
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    visibility = self.visitor._get_visibility(var_name)
                    location = self.visitor.metadata.get_location(node)
                    
                    # Check if this is a constant by convention
                    is_constant = var_name.isupper()
                    element_type = CodeElementType.CONSTANT if is_constant else CodeElementType.VARIABLE
                    
                    var_id = self.visitor._get_next_id()
                    qualified_name = self.visitor._get_qualified_name(var_name)
                    
                    # Try to get a string representation of the value
                    value_str = self.visitor.utils.node_to_str(node.value)
                    
                    var_element = CodeElement(
                        id=var_id,
                        name=var_name,
                        element_type=element_type,
                        file_path=self.visitor.file_path,
                        line_start=location.start_line,
                        line_end=location.end_line,
                        module=self.visitor.module_name,
                        parent_id=self.visitor.current_parent_id,
                        visibility=visibility,
                        metadata={
                            "value": value_str,
                            "qualified_name": qualified_name
                        }
                    )
                    
                    self.visitor.elements.append(var_element)
                    
                    # Add to parent's children
                    if self.visitor.current_parent_id:
                        self.visitor._add_child_relationship(self.visitor.current_parent_id, var_id)
        
        # Continue visiting
        self.visitor.generic_visit(node)
    
    def process_ann_assign(self, node: ast.AnnAssign) -> None:
        """Process an annotated assignment statement.
        
        Args:
            node: The annotated assignment statement node
        """
        # Track top-level annotated assignments
        if self.visitor.current_parent_id:
            # Only handle assignments to names
            if isinstance(node.target, ast.Name):
                var_name = node.target.id
                visibility = self.visitor._get_visibility(var_name)
                location = self.visitor.metadata.get_location(node)
                
                # Extract type annotation
                annotation = self.visitor.utils.extract_annotation(node.annotation)
                
                # Check if this is a constant by convention
                is_constant = var_name.isupper()
                element_type = CodeElementType.CONSTANT if is_constant else CodeElementType.VARIABLE
                
                var_id = self.visitor._get_next_id()
                qualified_name = self.visitor._get_qualified_name(var_name)
                
                # Try to get a string representation of the value if it exists
                value_str = None
                if node.value:
                    value_str = self.visitor.utils.node_to_str(node.value)
                
                var_element = CodeElement(
                    id=var_id,
                    name=var_name,
                    element_type=element_type,
                    file_path=self.visitor.file_path,
                    line_start=location.start_line,
                    line_end=location.end_line,
                    module=self.visitor.module_name,
                    parent_id=self.visitor.current_parent_id,
                    visibility=visibility,
                    annotations={"type": annotation} if annotation else {},
                    metadata={
                        "value": value_str,
                        "qualified_name": qualified_name
                    }
                )
                
                self.visitor.elements.append(var_element)
                
                # Add to parent's children
                if self.visitor.current_parent_id:
                    self.visitor._add_child_relationship(self.visitor.current_parent_id, var_id)
        
        # Continue visiting
        self.visitor.generic_visit(node) 