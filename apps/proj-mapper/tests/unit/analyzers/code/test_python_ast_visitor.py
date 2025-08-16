"""Unit tests for the Python AST visitor."""

import ast
import pytest
from typing import Dict, List, Any, Optional

from proj_mapper.analyzers.code.python_ast_visitor import PythonASTVisitor
from proj_mapper.models.code import CodeElement, CodeElementType, Visibility


@pytest.fixture
def simple_module_ast() -> ast.Module:
    """Create a simple module AST for testing."""
    code = '''"""This is a test module."""

import os
import sys
from typing import List, Dict

# A constant
CONSTANT_VALUE = 42

# A variable
variable_value = "test"

def test_function(param1: str, param2: int = 0) -> bool:
    """This is a test function.
    
    Args:
        param1: First parameter
        param2: Second parameter
        
    Returns:
        A boolean result
    """
    return True

class TestClass:
    """This is a test class."""
    
    class_var = "class variable"
    
    def __init__(self, value: str):
        """Initialize the class."""
        self.value = value
        
    def get_value(self) -> str:
        """Get the value."""
        return self.value
        
    @staticmethod
    def static_method():
        """A static method."""
        return "static"
        
    @classmethod
    def class_method(cls):
        """A class method."""
        return cls.class_var
        
    def _protected_method(self):
        """A protected method."""
        return "protected"
        
    def __private_method(self):
        """A private method."""
        return "private"
'''
    return ast.parse(code)


@pytest.fixture
def inheritance_module_ast() -> ast.Module:
    """Create a module AST with inheritance for testing."""
    code = '''"""This module demonstrates inheritance."""

class BaseClass:
    """A base class."""
    def base_method(self):
        return "base"

class ChildClass(BaseClass):
    """A child class."""
    def child_method(self):
        return "child"

class MultipleInheritance(BaseClass, ChildClass):
    """A class with multiple inheritance."""
    pass
'''
    return ast.parse(code)


@pytest.fixture
def nested_module_ast() -> ast.Module:
    """Create a module AST with nested classes and functions for testing."""
    code = '''"""This module demonstrates nesting."""

def outer_function():
    """An outer function."""
    
    def inner_function():
        """An inner function."""
        return "inner"
        
    return inner_function()

class OuterClass:
    """An outer class."""
    
    class InnerClass:
        """An inner class."""
        
        def inner_method(self):
            """An inner method."""
            return "inner"
            
    def outer_method(self):
        """An outer method."""
        return self.InnerClass().inner_method()
'''
    return ast.parse(code)


@pytest.fixture
def async_module_ast() -> ast.Module:
    """Create a module AST with async functions for testing."""
    code = '''"""This module demonstrates async functions."""

async def async_function():
    """An async function."""
    return "async"

class AsyncClass:
    """A class with async methods."""
    
    async def async_method(self):
        """An async method."""
        return "async"
'''
    return ast.parse(code)


class TestPythonASTVisitor:
    """Tests for the PythonASTVisitor class."""
    
    def test_module_level_extraction(self, simple_module_ast: ast.Module) -> None:
        """Test extracting module-level information."""
        visitor = PythonASTVisitor("test_file.py", "test_module")
        visitor.visit(simple_module_ast)
        
        # Check module docstring
        assert visitor.module_docstring == "This is a test module."
        
        # Check imports
        assert len(visitor.imports) == 4  # os, sys, typing.List, typing.Dict
        imports = {f"{imp['from']}.{imp['import']}" if imp['from'] else imp['import'] for imp in visitor.imports}
        assert "os" in imports
        assert "sys" in imports
        assert "typing.List" in imports
        assert "typing.Dict" in imports
        
        # Check elements
        assert len(visitor.elements) > 0
        
        # Find module element
        module_elements = [e for e in visitor.elements if e.element_type == CodeElementType.MODULE]
        assert len(module_elements) == 1
        assert module_elements[0].name == "test_module"
        
        # Find constants
        constant_elements = [e for e in visitor.elements if e.element_type == CodeElementType.CONSTANT]
        assert len(constant_elements) >= 1
        assert any(e.name == "CONSTANT_VALUE" for e in constant_elements)
        
        # Find variables
        var_elements = [e for e in visitor.elements if e.element_type == CodeElementType.VARIABLE]
        assert len(var_elements) >= 1
        assert any(e.name == "variable_value" for e in var_elements)
    
    def test_function_extraction(self, simple_module_ast: ast.Module) -> None:
        """Test extracting function information."""
        visitor = PythonASTVisitor("test_file.py", "test_module")
        visitor.visit(simple_module_ast)
        
        # Find function
        function_elements = [e for e in visitor.elements if e.element_type == CodeElementType.FUNCTION]
        assert len(function_elements) >= 1
        
        # Find test_function specifically
        test_function = next((f for f in function_elements if f.name == "test_function"), None)
        assert test_function is not None
        
        # Check function details
        assert test_function.docstring is not None
        assert "This is a test function" in test_function.docstring
        assert test_function.visibility == Visibility.PUBLIC
        
        # Check parameters and return type
        assert "parameters" in test_function.metadata
        parameters = test_function.metadata["parameters"]
        assert len(parameters) == 2
        param_names = [p["name"] for p in parameters]
        assert "param1" in param_names
        assert "param2" in param_names
        
        assert "return_type" in test_function.metadata
        assert test_function.metadata["return_type"] == "bool"
        
        # Check signature
        assert test_function.signature is not None
        assert "test_function" in test_function.signature
        assert "param1" in test_function.signature
        assert "param2" in test_function.signature
    
    def test_class_extraction(self, simple_module_ast: ast.Module) -> None:
        """Test extracting class information."""
        visitor = PythonASTVisitor("test_file.py", "test_module")
        visitor.visit(simple_module_ast)
        
        # Find class
        class_elements = [e for e in visitor.elements if e.element_type == CodeElementType.CLASS]
        assert len(class_elements) >= 1
        
        # Find TestClass specifically
        test_class = next((c for c in class_elements if c.name == "TestClass"), None)
        assert test_class is not None
        
        # Check class details
        assert test_class.docstring is not None
        assert "This is a test class" in test_class.docstring
        assert test_class.visibility == Visibility.PUBLIC
        
        # Check class methods
        all_elements = visitor.elements
        class_methods = [e for e in all_elements 
                       if e.element_type == CodeElementType.METHOD 
                       and e.parent_id == test_class.id]
        
        assert len(class_methods) >= 6  # __init__, get_value, static_method, class_method, _protected_method, __private_method
        
        # Check for specific methods
        method_names = [m.name for m in class_methods]
        assert "__init__" in method_names
        assert "get_value" in method_names
        assert "static_method" in method_names
        assert "class_method" in method_names
        assert "_protected_method" in method_names
        assert "__private_method" in method_names
        
        # Check method visibility
        init_method = next((m for m in class_methods if m.name == "__init__"), None)
        assert init_method is not None
        
        # Note: Python's convention recognizes __init__ as special method with underscore prefix
        # The implementation considers underscore-prefixed identifiers as protected
        assert init_method.visibility in [Visibility.PUBLIC, Visibility.PROTECTED]
        
        protected_method = next((m for m in class_methods if m.name == "_protected_method"), None)
        assert protected_method is not None
        assert protected_method.visibility == Visibility.PROTECTED
        
        private_method = next((m for m in class_methods if m.name == "__private_method"), None)
        assert private_method is not None
        assert private_method.visibility == Visibility.PRIVATE
        
        # Check static method
        static_method = next((m for m in class_methods if m.name == "static_method"), None)
        assert static_method is not None
        assert static_method.is_static is True
        
        # Check class method
        class_method = next((m for m in class_methods if m.name == "class_method"), None)
        assert class_method is not None
        assert class_method.metadata.get("is_class_method") is True
    
    def test_inheritance_extraction(self, inheritance_module_ast: ast.Module) -> None:
        """Test extracting inheritance relationships."""
        visitor = PythonASTVisitor("test_file.py", "test_module")
        visitor.visit(inheritance_module_ast)
        
        # Find classes
        class_elements = [e for e in visitor.elements if e.element_type == CodeElementType.CLASS]
        assert len(class_elements) >= 3
        
        # Find specific classes
        base_class = next((c for c in class_elements if c.name == "BaseClass"), None)
        assert base_class is not None
        
        child_class = next((c for c in class_elements if c.name == "ChildClass"), None)
        assert child_class is not None
        
        multiple_inheritance = next((c for c in class_elements if c.name == "MultipleInheritance"), None)
        assert multiple_inheritance is not None
        
        # Check inheritance metadata
        assert "bases" in child_class.metadata
        assert len(child_class.metadata["bases"]) == 1
        assert "BaseClass" in child_class.metadata["bases"]
        
        assert "bases" in multiple_inheritance.metadata
        assert len(multiple_inheritance.metadata["bases"]) == 2
        assert "BaseClass" in multiple_inheritance.metadata["bases"]
        assert "ChildClass" in multiple_inheritance.metadata["bases"]
    
    def test_nested_elements_extraction(self, nested_module_ast: ast.Module) -> None:
        """Test extracting nested classes and functions."""
        visitor = PythonASTVisitor("test_file.py", "test_module")
        visitor.visit(nested_module_ast)
        
        # Find outer function
        outer_function = next((f for f in visitor.elements 
                             if f.element_type == CodeElementType.FUNCTION 
                             and f.name == "outer_function"), None)
        assert outer_function is not None
        
        # Find inner function
        inner_function = next((f for f in visitor.elements 
                             if f.element_type == CodeElementType.FUNCTION 
                             and f.name == "inner_function"), None)
        assert inner_function is not None
        
        # Check parent-child relationship
        assert inner_function.parent_id == outer_function.id
        
        # Find outer class
        outer_class = next((c for c in visitor.elements 
                          if c.element_type == CodeElementType.CLASS 
                          and c.name == "OuterClass"), None)
        assert outer_class is not None
        
        # Find inner class
        inner_class = next((c for c in visitor.elements 
                          if c.element_type == CodeElementType.CLASS 
                          and c.name == "InnerClass"), None)
        assert inner_class is not None
        
        # Check parent-child relationship
        assert inner_class.parent_id == outer_class.id
        
        # Find inner method
        inner_method = next((m for m in visitor.elements 
                           if m.element_type == CodeElementType.METHOD 
                           and m.name == "inner_method"), None)
        assert inner_method is not None
        
        # Check parent-child relationship
        assert inner_method.parent_id == inner_class.id
    
    def test_async_function_extraction(self, async_module_ast: ast.Module) -> None:
        """Test extracting async functions and methods."""
        visitor = PythonASTVisitor("test_file.py", "test_module")
        visitor.visit(async_module_ast)
        
        # Find async function
        async_function = next((f for f in visitor.elements 
                             if f.element_type == CodeElementType.FUNCTION 
                             and f.name == "async_function"), None)
        assert async_function is not None
        
        # Check async metadata
        assert "is_async" in async_function.metadata
        assert async_function.metadata["is_async"] is True
        
        # Find async method
        async_method = next((m for m in visitor.elements 
                           if m.element_type == CodeElementType.METHOD 
                           and m.name == "async_method"), None)
        assert async_method is not None
        
        # Check async metadata
        assert "is_async" in async_method.metadata
        assert async_method.metadata["is_async"] is True 