# Python Code Analyzer Implementation Guide

## Overview

The Python Code Analyzer is responsible for parsing Python source files and extracting their structure, including modules, classes, functions, and relationships between these elements. This is a critical component for the Project Mapper as it provides the foundation for understanding code structure.

## Current Status

The current Python Analyzer implementation:

- Has basic structural code
- Lacks functional AST processing
- Cannot extract code elements correctly
- Does not identify relationships between elements
- Doesn't handle imports and dependencies

## Implementation Requirements

### Core Functionality

1. **AST Parsing**

   - Parse Python files using the standard `ast` module
   - Handle syntax errors gracefully
   - Support different Python versions
   - Track source locations for all elements

2. **Code Structure Extraction**

   - Extract modules and their structure
   - Identify classes, their methods, and inheritance
   - Extract functions and their parameters
   - Capture variable declarations
   - Process docstrings and comments

3. **Relationship Identification**
   - Detect import relationships
   - Identify class inheritance
   - Track function calls
   - Recognize variable usage
   - Identify decorator relationships

## Implementation Details

### Python AST Visitor

Create or update the file: `src/proj_mapper/analyzers/code/python_ast_visitor.py`

```python
import ast
from typing import List, Dict, Set, Optional, Any, Union, Tuple
from dataclasses import dataclass, field

@dataclass
class CodeElement:
    """Base class for all code elements."""
    name: str
    module_path: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the fully qualified name of this element."""
        return f"{self.module_path}.{self.name}"


@dataclass
class Module(CodeElement):
    """Represents a Python module."""
    imports: List[str] = field(default_factory=list)
    classes: Dict[str, 'Class'] = field(default_factory=dict)
    functions: Dict[str, 'Function'] = field(default_factory=dict)
    variables: Dict[str, 'Variable'] = field(default_factory=dict)


@dataclass
class Class(CodeElement):
    """Represents a Python class."""
    bases: List[str] = field(default_factory=list)
    methods: Dict[str, 'Function'] = field(default_factory=list)
    class_variables: Dict[str, 'Variable'] = field(default_factory=dict)
    instance_variables: Dict[str, 'Variable'] = field(default_factory=dict)
    decorators: List[str] = field(default_factory=list)


@dataclass
class Function(CodeElement):
    """Represents a Python function or method."""
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_method: bool = False
    is_property: bool = False
    called_functions: List[str] = field(default_factory=list)
    referenced_variables: List[str] = field(default_factory=list)


@dataclass
class Variable(CodeElement):
    """Represents a Python variable."""
    var_type: Optional[str] = None
    is_constant: bool = False
    value: Optional[str] = None


class PythonASTVisitor(ast.NodeVisitor):
    """Visits Python AST nodes and extracts code structure."""

    def __init__(self, module_path: str):
        """Initialize the visitor with the module path."""
        self.module_path = module_path
        self.module = Module(
            name=self._extract_module_name(module_path),
            module_path=module_path,
            line_start=1,
            line_end=0  # Will be updated during visit
        )

        # Current context for nested elements
        self.current_class = None
        self.current_function = None

        # Track imports
        self.imports = []

    def _extract_module_name(self, module_path: str) -> str:
        """Extract module name from the path."""
        import os
        return os.path.splitext(os.path.basename(module_path))[0]

    def _get_docstring(self, node: Union[ast.Module, ast.ClassDef, ast.FunctionDef]) -> Optional[str]:
        """Extract docstring from a node."""
        if (isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Str)):
            return node.body[0].value.s
        return None

    def _get_line_range(self, node: ast.AST) -> Tuple[int, int]:
        """Get the line range of a node."""
        # AST nodes have lineno attribute for start line
        # We estimate end line by finding the max line in all child nodes
        start_line = getattr(node, 'lineno', 1)

        # Simple approach: we'll use the last child's line number if available
        end_line = start_line
        if hasattr(node, 'body') and node.body:
            last_node = node.body[-1]
            if hasattr(last_node, 'lineno'):
                end_line = last_node.lineno
                # Look for end line in child's child if possible
                if hasattr(last_node, 'body') and last_node.body:
                    end_line = self._get_line_range(last_node)[1]

        return start_line, end_line

    def visit_Module(self, node: ast.Module) -> None:
        """Visit a module node."""
        self.module.docstring = self._get_docstring(node)
        _, end_line = self._get_line_range(node)
        self.module.line_end = end_line
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit an import node."""
        for name in node.names:
            self.module.imports.append(name.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit an import from node."""
        if node.module:
            for name in node.names:
                import_name = f"{node.module}.{name.name}"
                self.module.imports.append(import_name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition node."""
        start_line, end_line = self._get_line_range(node)

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}")

        # Get decorators
        decorators = []
        if hasattr(node, 'decorator_list'):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
                elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)

        # Create the class
        cls = Class(
            name=node.name,
            module_path=self.module_path,
            line_start=start_line,
            line_end=end_line,
            docstring=self._get_docstring(node) if node.body else None,
            bases=bases,
            decorators=decorators
        )

        # Add to module
        self.module.classes[node.name] = cls

        # Set as current class for context
        prev_class = self.current_class
        self.current_class = cls

        # Visit class body
        self.generic_visit(node)

        # Restore context
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition node."""
        start_line, end_line = self._get_line_range(node)

        # Get parameters
        parameters = []
        for arg in node.args.args:
            parameters.append(arg.arg)

        # Get decorators
        decorators = []
        is_property = False
        if hasattr(node, 'decorator_list'):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorator_name = decorator.id
                    decorators.append(decorator_name)
                    if decorator_name == 'property':
                        is_property = True
                elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)

        # Create the function
        func = Function(
            name=node.name,
            module_path=self.module_path,
            line_start=start_line,
            line_end=end_line,
            docstring=self._get_docstring(node) if node.body else None,
            parameters=parameters,
            is_method=self.current_class is not None,
            is_property=is_property,
            decorators=decorators
        )

        # Add to appropriate parent
        if self.current_class:
            self.current_class.methods[node.name] = func
        else:
            self.module.functions[node.name] = func

        # Set as current function for context
        prev_function = self.current_function
        self.current_function = func

        # Visit function body
        self.generic_visit(node)

        # Restore context
        self.current_function = prev_function

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit an assignment node."""
        # Get line information
        start_line = node.lineno
        end_line = start_line

        # Handle different target types
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id

                # Determine if it's a constant by convention
                is_constant = var_name.isupper()

                # Try to extract value as string representation
                value = None
                if isinstance(node.value, ast.Str):
                    value = node.value.s
                elif isinstance(node.value, ast.Num):
                    value = str(node.value.n)
                elif isinstance(node.value, ast.NameConstant):
                    value = str(node.value.value)

                # Create variable
                var = Variable(
                    name=var_name,
                    module_path=self.module_path,
                    line_start=start_line,
                    line_end=end_line,
                    is_constant=is_constant,
                    value=value
                )

                # Add to appropriate parent
                if self.current_function:
                    self.current_function.referenced_variables.append(var_name)
                elif self.current_class:
                    self.current_class.class_variables[var_name] = var
                else:
                    self.module.variables[var_name] = var

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a function call node."""
        if self.current_function and isinstance(node.func, ast.Name):
            self.current_function.called_functions.append(node.func.id)
        elif self.current_function and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                self.current_function.called_functions.append(f"{node.func.value.id}.{node.func.attr}")

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit a name node."""
        if self.current_function and isinstance(node.ctx, ast.Load):
            self.current_function.referenced_variables.append(node.id)

        self.generic_visit(node)
```

### Python Analyzer Implementation

Create or update the file: `src/proj_mapper/analyzers/code/python.py`

```python
import ast
import os
from typing import Dict, Any, Optional, List

from proj_mapper.analyzers.base import Analyzer, AnalysisResult
from proj_mapper.analyzers.code.python_ast_visitor import PythonASTVisitor, Module


class PythonAnalyzer(Analyzer):
    """Analyzer for Python source files."""

    def can_analyze(self, file_path: str) -> bool:
        """Check if this analyzer can handle the given file."""
        return file_path.endswith('.py')

    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze Python source file and extract code structure."""
        try:
            # Parse the Python file
            tree = ast.parse(content, filename=file_path)

            # Visit the AST and extract code structure
            visitor = PythonASTVisitor(file_path)
            visitor.visit(tree)

            # Create analysis result with extracted module
            result = PythonAnalysisResult(
                file_path=file_path,
                module=visitor.module
            )

            return result

        except SyntaxError as e:
            # Handle syntax errors gracefully
            return ErrorAnalysisResult(
                file_path=file_path,
                error=f"Syntax error: {str(e)}"
            )
        except Exception as e:
            # Handle other errors
            return ErrorAnalysisResult(
                file_path=file_path,
                error=f"Error analyzing file: {str(e)}"
            )


class PythonAnalysisResult(AnalysisResult):
    """Result of Python code analysis."""

    def __init__(self, file_path: str, module: Module):
        """Initialize with file path and module."""
        super().__init__(file_path)
        self.module = module

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": self.file_path,
            "type": "python",
            "module": {
                "name": self.module.name,
                "imports": self.module.imports,
                "classes": [self._class_to_dict(name, cls) for name, cls in self.module.classes.items()],
                "functions": [self._function_to_dict(name, func) for name, func in self.module.functions.items()],
                "variables": [self._variable_to_dict(name, var) for name, var in self.module.variables.items()],
                "docstring": self.module.docstring,
                "line_range": [self.module.line_start, self.module.line_end]
            }
        }

    def _class_to_dict(self, name: str, cls) -> Dict[str, Any]:
        """Convert a class to dictionary representation."""
        return {
            "name": name,
            "bases": cls.bases,
            "methods": [self._function_to_dict(name, method) for name, method in cls.methods.items()],
            "class_variables": [self._variable_to_dict(name, var) for name, var in cls.class_variables.items()],
            "instance_variables": [self._variable_to_dict(name, var) for name, var in cls.instance_variables.items()],
            "decorators": cls.decorators,
            "docstring": cls.docstring,
            "line_range": [cls.line_start, cls.line_end]
        }

    def _function_to_dict(self, name: str, func) -> Dict[str, Any]:
        """Convert a function to dictionary representation."""
        return {
            "name": name,
            "parameters": func.parameters,
            "return_type": func.return_type,
            "decorators": func.decorators,
            "is_method": func.is_method,
            "is_property": func.is_property,
            "called_functions": func.called_functions,
            "referenced_variables": func.referenced_variables,
            "docstring": func.docstring,
            "line_range": [func.line_start, func.line_end]
        }

    def _variable_to_dict(self, name: str, var) -> Dict[str, Any]:
        """Convert a variable to dictionary representation."""
        return {
            "name": name,
            "var_type": var.var_type,
            "is_constant": var.is_constant,
            "value": var.value,
            "line_range": [var.line_start, var.line_end]
        }


class ErrorAnalysisResult(AnalysisResult):
    """Result when analysis encounters an error."""

    def __init__(self, file_path: str, error: str):
        """Initialize with file path and error message."""
        super().__init__(file_path)
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": self.file_path,
            "type": "error",
            "error": self.error
        }
```

### Python Analyzer Pipeline Integration

Update the file: `src/proj_mapper/analyzers/pipeline_stages.py`

```python
from typing import Dict, List, Any
from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.analyzers.base import Analyzer, AnalysisResult
from proj_mapper.analyzers.code.python import PythonAnalyzer
from proj_mapper.core.file_discovery import DiscoveredFile


class AnalyzerRegistry:
    """Registry for analyzer classes."""

    _analyzers = []

    @classmethod
    def register(cls, analyzer_class):
        """Register an analyzer class."""
        cls._analyzers.append(analyzer_class())
        return analyzer_class

    @classmethod
    def get_analyzer_for_file(cls, file_path: str) -> Analyzer:
        """Get the appropriate analyzer for a file."""
        for analyzer in cls._analyzers:
            if analyzer.can_analyze(file_path):
                return analyzer
        return None


# Register analyzers
AnalyzerRegistry.register(PythonAnalyzer)


class CodeAnalysisStage(PipelineStage):
    """Pipeline stage for analyzing code files."""

    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the pipeline context."""
        categorized_files = context.get_data("categorized_files")
        if not categorized_files:
            raise ValueError("No categorized files found in pipeline context")

        # Get Python files
        python_files = categorized_files.get("python", [])

        # Analyze each Python file
        analysis_results = {}
        for file in python_files:
            # Get analyzer
            analyzer = AnalyzerRegistry.get_analyzer_for_file(file.path)
            if not analyzer:
                continue

            # Read file content
            with open(file.path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Analyze file
            result = analyzer.analyze(file.path, content)
            analysis_results[file.path] = result

        # Add analysis results to context
        context.set_data("code_analysis_results", analysis_results)

        return context
```

## Testing Implementation

Create the following test file: `tests/unit/analyzers/code/test_python_analyzer.py`

```python
import ast
import pytest
from pathlib import Path
from proj_mapper.analyzers.code.python import PythonAnalyzer, PythonAnalysisResult
from proj_mapper.analyzers.code.python_ast_visitor import PythonASTVisitor


class TestPythonAnalyzer:
    """Tests for the PythonAnalyzer class."""

    def test_can_analyze(self):
        """Test if analyzer can handle Python files."""
        analyzer = PythonAnalyzer()
        assert analyzer.can_analyze("test.py") is True
        assert analyzer.can_analyze("test.txt") is False
        assert analyzer.can_analyze("test.md") is False

    def test_analyze_simple_module(self, tmp_path):
        """Test analyzing a simple Python module."""
        # Create a simple Python file
        code = """
def hello():
    \"\"\"Say hello.\"\"\"
    print("Hello, world!")

class Person:
    \"\"\"A person class.\"\"\"
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}!"

NAME = "Python"
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        # Analyze the file
        analyzer = PythonAnalyzer()
        with open(file_path, 'r') as f:
            content = f.read()
        result = analyzer.analyze(str(file_path), content)

        # Check result
        assert isinstance(result, PythonAnalysisResult)
        assert result.module.name == "test"

        # Check function
        assert "hello" in result.module.functions
        assert result.module.functions["hello"].docstring == "Say hello."

        # Check class
        assert "Person" in result.module.classes
        assert result.module.classes["Person"].docstring == "A person class."

        # Check methods
        assert "greet" in result.module.classes["Person"].methods
        assert "__init__" in result.module.classes["Person"].methods

        # Check variable
        assert "NAME" in result.module.variables
        assert result.module.variables["NAME"].value == "Python"
        assert result.module.variables["NAME"].is_constant is True

    def test_analyze_with_imports(self, tmp_path):
        """Test analyzing a module with imports."""
        # Create a Python file with imports
        code = """
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

def get_time():
    return datetime.now()
"""
        file_path = tmp_path / "imports.py"
        file_path.write_text(code)

        # Analyze the file
        analyzer = PythonAnalyzer()
        with open(file_path, 'r') as f:
            content = f.read()
        result = analyzer.analyze(str(file_path), content)

        # Check imports
        assert "os" in result.module.imports
        assert "sys" in result.module.imports
        assert "datetime.datetime" in result.module.imports
        assert "datetime.timedelta" in result.module.imports
        assert "pathlib.Path" in result.module.imports

    def test_analyze_with_inheritance(self, tmp_path):
        """Test analyzing a module with class inheritance."""
        # Create a Python file with class inheritance
        code = """
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"
"""
        file_path = tmp_path / "inheritance.py"
        file_path.write_text(code)

        # Analyze the file
        analyzer = PythonAnalyzer()
        with open(file_path, 'r') as f:
            content = f.read()
        result = analyzer.analyze(str(file_path), content)

        # Check inheritance
        assert len(result.module.classes["Dog"].bases) == 1
        assert result.module.classes["Dog"].bases[0] == "Animal"

        assert len(result.module.classes["Cat"].bases) == 1
        assert result.module.classes["Cat"].bases[0] == "Animal"

    def test_analyze_with_function_calls(self, tmp_path):
        """Test analyzing a module with function calls."""
        # Create a Python file with function calls
        code = """
def helper():
    return "Help"

def main():
    result = helper()
    print(result)
    return result
"""
        file_path = tmp_path / "calls.py"
        file_path.write_text(code)

        # Analyze the file
        analyzer = PythonAnalyzer()
        with open(file_path, 'r') as f:
            content = f.read()
        result = analyzer.analyze(str(file_path), content)

        # Check function calls
        assert "helper" in result.module.functions["main"].called_functions
        assert "print" in result.module.functions["main"].called_functions

    def test_analyze_with_syntax_error(self, tmp_path):
        """Test analyzing a file with syntax errors."""
        # Create a Python file with syntax error
        code = """
def broken_function()
    print("Missing colon")
"""
        file_path = tmp_path / "error.py"
        file_path.write_text(code)

        # Analyze the file
        analyzer = PythonAnalyzer()
        with open(file_path, 'r') as f:
            content = f.read()
        result = analyzer.analyze(str(file_path), content)

        # Check error result
        assert "error" in result.to_dict()["type"]
        assert "Syntax error" in result.to_dict()["error"]
```

## Integration with Core System

Ensure the Python Analyzer is properly integrated with the core system:

1. **Register the Analyzer:**

   - Update `src/proj_mapper/analyzers/__init__.py` to register the Python analyzer
   - Ensure it's available to the analyzer registry

2. **Connect with File Discovery:**

   - Make sure discovered Python files are passed to the analyzer
   - Handle file reading and encoding properly

3. **Pipeline Integration:**
   - Add the Python analysis stage to the pipeline
   - Ensure results are properly passed to subsequent stages

## Validation Steps

1. **Verify AST Parsing:**

   - Test with various Python file structures
   - Confirm syntax error handling works properly
   - Validate line range tracking accuracy

2. **Validate Code Extraction:**

   - Verify all modules, classes, and functions are extracted
   - Check that docstrings are correctly associated
   - Confirm inheritance relationships are tracked
   - Validate variable detection

3. **Test Function Analysis:**

   - Verify parameters are correctly captured
   - Check function call detection
   - Test decorator handling

4. **Pipeline Testing:**
   - Verify analyzer results are properly passed through the pipeline
   - Test with multiple Python files
   - Validate performance with larger codebases

## Next Steps

After implementing the Python Code Analyzer, proceed to implementing the Documentation Analyzer which will process Markdown files and extract documentation structure.
