"""Python analyzer module.

This module provides the analyzer for Python files.
"""

import ast
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from proj_mapper.analyzers.base import Analyzer, AnalysisResult
from proj_mapper.models.file import DiscoveredFile, FileType

# Configure logging
logger = logging.getLogger(__name__)


class PythonVisitor(ast.NodeVisitor):
    """AST visitor for Python files."""
    
    def __init__(self, file: DiscoveredFile):
        """Initialize the visitor.
        
        Args:
            file: The file being analyzed
        """
        self.file = file
        self.imports = []
        self.exports = []
        self.dependencies = []
        self.module_name = None
        self.module_docstring = None
        
        # Track visited nodes to avoid duplicates
        self._visited_imports = set()
        self._visited_exports = set()
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit an Import node.
        
        Args:
            node: The AST node
        """
        for name in node.names:
            import_path = name.name
            if import_path not in self._visited_imports:
                self.imports.append({
                    "path": import_path,
                    "alias": name.asname,
                    "lineno": node.lineno
                })
                self._visited_imports.add(import_path)
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit an ImportFrom node.
        
        Args:
            node: The AST node
        """
        module = node.module or ""
        for name in node.names:
            import_path = f"{module}.{name.name}" if module else name.name
            if import_path not in self._visited_imports:
                self.imports.append({
                    "path": import_path,
                    "alias": name.asname,
                    "lineno": node.lineno,
                    "level": node.level
                })
                self._visited_imports.add(import_path)
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a ClassDef node.
        
        Args:
            node: The AST node
        """
        if node.name not in self._visited_exports:
            self.exports.append({
                "name": node.name,
                "kind": "class",
                "lineno": node.lineno,
                "docstring": ast.get_docstring(node)
            })
            self._visited_exports.add(node.name)
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a FunctionDef node.
        
        Args:
            node: The AST node
        """
        if node.name not in self._visited_exports:
            self.exports.append({
                "name": node.name,
                "kind": "function",
                "lineno": node.lineno,
                "docstring": ast.get_docstring(node)
            })
            self._visited_exports.add(node.name)
        
        self.generic_visit(node)
    
    def visit_Module(self, node: ast.Module) -> None:
        """Visit a Module node.
        
        Args:
            node: The AST node
        """
        # Get module docstring
        self.module_docstring = ast.get_docstring(node)
        
        # Try to determine module name from file path
        file_path = Path(self.file.relative_path)
        if file_path.stem != "__init__":
            self.module_name = file_path.stem
        else:
            # For __init__.py, use parent directory name
            self.module_name = file_path.parent.name
        
        self.generic_visit(node)


class PythonAnalyzer(Analyzer):
    """Analyzer for Python files."""
    
    def can_analyze(self, file: DiscoveredFile) -> bool:
        """Check if this analyzer can handle the given file.
        
        Args:
            file: The file to check
            
        Returns:
            True if this analyzer can handle the file
        """
        return file.file_type == FileType.PYTHON and not file.is_binary
    
    def get_file_filter(self) -> List[str]:
        """Get file patterns for selecting Python files.
        
        Returns:
            List of glob patterns for Python files
        """
        return ["**/*.py"]
    
    def analyze_file(self, file_path: Path, content: str) -> List:
        """Analyze a Python file and extract code elements.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of extracted code elements
        """
        # Get file stat information for modified time
        stat_info = file_path.stat()
        
        # Create a DiscoveredFile object
        file = DiscoveredFile(
            path=str(file_path),
            relative_path=str(file_path.name),
            file_type=FileType.PYTHON,
            size=len(content),
            is_binary=False,
            modified_time=datetime.fromtimestamp(stat_info.st_mtime)
        )
        
        # Use existing analyze method
        result = self.analyze(file)
        
        # Return elements
        return result.elements if result and hasattr(result, 'elements') else []
    
    def analyze(self, file: DiscoveredFile) -> Optional[AnalysisResult]:
        """Analyze a Python file.
        
        Args:
            file: The file to analyze
            
        Returns:
            Analysis results or None if analysis failed
        """
        try:
            # Read file content
            with open(file.path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Create visitor and analyze
            visitor = PythonVisitor(file)
            visitor.visit(tree)
            
            # Create analysis result
            result = AnalysisResult(file)
            
            # Add imports
            for imp in visitor.imports:
                result.add_import(imp["path"])
            
            # Add exports
            for exp in visitor.exports:
                result.add_export(exp["name"], exp["kind"])
            
            # Set module information
            if visitor.module_name:
                result.set_module(visitor.module_name, "module")
            
            # Set documentation
            if visitor.module_docstring:
                result.set_documentation(visitor.module_docstring)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing Python file {file.relative_path}: {e}")
            return None 