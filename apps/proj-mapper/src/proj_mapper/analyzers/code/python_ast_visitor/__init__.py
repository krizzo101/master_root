"""Python AST visitor for code analysis.

This module provides a visitor for traversing Python's abstract syntax tree (AST)
and extracting code elements. This is a backward compatibility layer that re-exports
the PythonASTVisitor class from its new location.
"""

from proj_mapper.analyzers.code.python_ast_visitor.visitor import PythonASTVisitor

__all__ = ["PythonASTVisitor"] 