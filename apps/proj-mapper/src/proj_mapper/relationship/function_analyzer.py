"""Function call analysis using AST parsing.

This module provides advanced function call detection using Python's AST module.
"""

import ast
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class CallContext:
    """Context information for a function call."""
    caller_id: str
    callee_name: str
    confidence: float = 1.0
    is_method_call: bool = False
    qualifier: Optional[str] = None
    line_number: int = 0
    context_before: str = ""
    context_after: str = ""

@dataclass
class ScopeInfo:
    """Information about the current scope."""
    imports: Dict[str, str] = field(default_factory=dict)
    aliases: Dict[str, str] = field(default_factory=dict)
    class_methods: Set[str] = field(default_factory=set)
    instance_methods: Set[str] = field(default_factory=set)

class FunctionCallAnalyzer(ast.NodeVisitor):
    """AST visitor for analyzing function calls in Python code."""
    
    def __init__(self, code: str):
        """Initialize the analyzer.
        
        Args:
            code: Python source code to analyze
        """
        self.code = code
        self.calls: List[CallContext] = []
        self.scope = ScopeInfo()
        self.current_function: Optional[str] = None
        self.source_lines = code.splitlines()
        
    def analyze(self) -> List[CallContext]:
        """Analyze the code and return found function calls.
        
        Returns:
            List of CallContext objects representing function calls
        """
        try:
            tree = ast.parse(self.code)
            self.visit(tree)
            return self.calls
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            return []
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return []
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition node.
        
        Args:
            node: AST node for function definition
        """
        prev_function = self.current_function
        self.current_function = node.name
        
        # Track instance and class methods
        if self._is_method(node):
            if self._is_classmethod(node):
                self.scope.class_methods.add(node.name)
            else:
                self.scope.instance_methods.add(node.name)
        
        self.generic_visit(node)
        self.current_function = prev_function
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit a function call node.
        
        Args:
            node: AST node for function call
        """
        if not self.current_function:
            return
            
        call_context = self._analyze_call(node)
        if call_context:
            self.calls.append(call_context)
            
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit an import node.
        
        Args:
            node: AST node for import statement
        """
        for name in node.names:
            self.scope.imports[name.asname or name.name] = name.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit an import from node.
        
        Args:
            node: AST node for import from statement
        """
        module = node.module or ""
        for name in node.names:
            imported_name = name.asname or name.name
            full_name = f"{module}.{name.name}" if module else name.name
            self.scope.imports[imported_name] = full_name
        self.generic_visit(node)
    
    def _analyze_call(self, node: ast.Call) -> Optional[CallContext]:
        """Analyze a function call node.
        
        Args:
            node: AST node for function call
            
        Returns:
            CallContext if a valid function call is found, None otherwise
        """
        if isinstance(node.func, ast.Name):
            # Direct function call
            return self._create_call_context(
                callee_name=node.func.id,
                line_number=node.lineno,
                confidence=1.0
            )
        elif isinstance(node.func, ast.Attribute):
            # Method call or qualified name
            return self._analyze_attribute_call(node.func)
        return None
    
    def _analyze_attribute_call(self, node: ast.Attribute) -> Optional[CallContext]:
        """Analyze an attribute-based function call.
        
        Args:
            node: AST attribute node representing the function call
            
        Returns:
            CallContext if a valid method call is found, None otherwise
        """
        if isinstance(node.value, ast.Name):
            # Simple method call (obj.method)
            qualifier = node.value.id
            confidence = 0.9  # Slightly lower confidence for method calls
            
            # Check if this is a known instance method
            if qualifier == "self" and node.attr in self.scope.instance_methods:
                confidence = 1.0
            
            return self._create_call_context(
                callee_name=node.attr,
                line_number=node.lineno,
                confidence=confidence,
                is_method_call=True,
                qualifier=qualifier
            )
        elif isinstance(node.value, ast.Attribute):
            # Chained method call (obj.attr.method)
            confidence = 0.8  # Lower confidence for chained calls
            qualifier = self._get_attribute_chain(node.value)
            
            return self._create_call_context(
                callee_name=node.attr,
                line_number=node.lineno,
                confidence=confidence,
                is_method_call=True,
                qualifier=qualifier
            )
        return None
    
    def _create_call_context(self, callee_name: str, line_number: int,
                           confidence: float, is_method_call: bool = False,
                           qualifier: Optional[str] = None) -> CallContext:
        """Create a call context object.
        
        Args:
            callee_name: Name of the called function
            line_number: Line number of the call
            confidence: Confidence score for the call
            is_method_call: Whether this is a method call
            qualifier: Qualifier for method calls (e.g., object name)
            
        Returns:
            CallContext object with call information
        """
        # Get context from surrounding lines
        context_before = self._get_line_context(line_number, before=True)
        context_after = self._get_line_context(line_number, before=False)
        
        return CallContext(
            caller_id=self.current_function,
            callee_name=callee_name,
            confidence=confidence,
            is_method_call=is_method_call,
            qualifier=qualifier,
            line_number=line_number,
            context_before=context_before,
            context_after=context_after
        )
    
    def _get_line_context(self, line_number: int, before: bool = True,
                         context_lines: int = 2) -> str:
        """Get context lines around a specific line.
        
        Args:
            line_number: Target line number
            before: Whether to get context before (True) or after (False)
            context_lines: Number of context lines to include
            
        Returns:
            String containing the context lines
        """
        if not self.source_lines:
            return ""
            
        start = max(0, line_number - context_lines - 1) if before else line_number
        end = line_number - 1 if before else min(len(self.source_lines),
                                               line_number + context_lines)
        
        return "\n".join(self.source_lines[start:end])
    
    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """Get the full chain of attributes.
        
        Args:
            node: AST attribute node
            
        Returns:
            String representing the attribute chain
        """
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    
    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if a function definition is a method.
        
        Args:
            node: AST function definition node
            
        Returns:
            True if the function is a method, False otherwise
        """
        return bool(node.args.args and node.args.args[0].arg == "self")
    
    def _is_classmethod(self, node: ast.FunctionDef) -> bool:
        """Check if a function definition is a classmethod.
        
        Args:
            node: AST function definition node
            
        Returns:
            True if the function is a classmethod, False otherwise
        """
        return any(isinstance(d, ast.Name) and d.id == "classmethod"
                  for d in node.decorator_list) 