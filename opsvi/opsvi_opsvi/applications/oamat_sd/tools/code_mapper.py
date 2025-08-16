#!/usr/bin/env python3
"""
Code Mapper - Comprehensive Code Analysis System

Extracts all function signatures, class definitions, variables, imports, and other
code elements from the OAMAT_SD codebase to prevent dev agents from guessing
instead of checking actual code.

Usage:
    python code_mapper.py analyze    # Generate code map
    python code_mapper.py search     # Search for functions/classes
    python code_mapper.py validate   # Validate proposed changes
"""

import argparse
import ast
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional


@dataclass
class FunctionInfo:
    """Information about a function"""

    name: str
    file_path: str
    line_number: int
    parameters: List[str]
    default_values: Dict[str, Any]
    return_type: Optional[str]
    docstring: Optional[str]
    decorators: List[str]
    is_async: bool
    is_method: bool
    class_name: Optional[str]


@dataclass
class ClassInfo:
    """Information about a class"""

    name: str
    file_path: str
    line_number: int
    bases: List[str]
    methods: List[str]
    attributes: List[str]
    docstring: Optional[str]
    decorators: List[str]


@dataclass
class VariableInfo:
    """Information about a variable"""

    name: str
    file_path: str
    line_number: int
    scope: str  # 'module', 'class', 'function'
    type_hint: Optional[str]
    is_constant: bool


@dataclass
class ImportInfo:
    """Information about imports"""

    module: str
    file_path: str
    line_number: int
    imports: List[str]  # What's being imported
    alias: Optional[str]  # If imported with 'as'


@dataclass
class CodeMap:
    """Complete code map of the project"""

    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    variables: List[VariableInfo]
    imports: List[ImportInfo]
    modules: List[str]
    generated_at: str


class CodeAnalyzer:
    """AST-based code analyzer"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.variables: List[VariableInfo] = []
        self.imports: List[ImportInfo] = []
        self.modules: List[str] = []

    def analyze_project(self) -> CodeMap:
        """Analyze the entire project"""
        print(f"🔍 Analyzing project: {self.project_root}")

        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        print(f"📁 Found {len(python_files)} Python files")

        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")

        return CodeMap(
            functions=self.functions,
            classes=self.classes,
            variables=self.variables,
            imports=self.imports,
            modules=self.modules,
            generated_at=datetime.now().isoformat(),
        )

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "__pycache__",
            ".venv",
            "venv",
            "env",
            ".git",
            "node_modules",
            "tests",
            "test_",
            "_test.py",
            "conftest.py",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = FileAnalyzer(str(file_path))
            analyzer.visit(tree)

            self.functions.extend(analyzer.functions)
            self.classes.extend(analyzer.classes)
            self.variables.extend(analyzer.variables)
            self.imports.extend(analyzer.imports)
            self.modules.append(str(file_path))

        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")


class FileAnalyzer(ast.NodeVisitor):
    """AST visitor for analyzing a single file"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.variables: List[VariableInfo] = []
        self.imports: List[ImportInfo] = []
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions"""
        self._process_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions"""
        self._process_function(node, is_async=True)

    def _process_function(self, node, is_async: bool):
        """Process both regular and async function definitions"""
        # Extract parameters
        parameters = []
        default_values = {}

        for arg in node.args.args:
            param_name = arg.arg
            parameters.append(param_name)

            # Check for default values - handle different AST versions
            try:
                if hasattr(arg, "default") and arg.default is not None:
                    default_values[param_name] = self._get_literal_value(arg.default)
            except AttributeError:
                # Skip default value extraction if not available
                pass

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            decorators.append(ast.unparse(decorator))

        function_info = FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            parameters=parameters,
            default_values=default_values,
            return_type=return_type,
            docstring=docstring,
            decorators=decorators,
            is_async=is_async,
            is_method=self.current_class is not None,
            class_name=self.current_class,
        )

        self.functions.append(function_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions"""
        # Extract base classes
        bases = []
        for base in node.bases:
            bases.append(ast.unparse(base))

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            decorators.append(ast.unparse(decorator))

        # Store current class for method analysis
        previous_class = self.current_class
        self.current_class = node.name

        # Visit class body to find methods and attributes
        self.generic_visit(node)

        # Extract methods and attributes
        methods = [f.name for f in self.functions if f.class_name == node.name]
        attributes = [v.name for v in self.variables if v.scope == f"class:{node.name}"]

        class_info = ClassInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            bases=bases,
            methods=methods,
            attributes=attributes,
            docstring=docstring,
            decorators=decorators,
        )

        self.classes.append(class_info)
        self.current_class = previous_class

    def visit_Assign(self, node: ast.Assign):
        """Visit variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                variable_info = VariableInfo(
                    name=target.id,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    scope=self._get_current_scope(),
                    type_hint=None,  # TODO: Extract type hints
                    is_constant=False,  # TODO: Detect constants
                )
                self.variables.append(variable_info)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignments"""
        if isinstance(node.target, ast.Name):
            type_hint = ast.unparse(node.annotation) if node.annotation else None

            variable_info = VariableInfo(
                name=node.target.id,
                file_path=self.file_path,
                line_number=node.lineno,
                scope=self._get_current_scope(),
                type_hint=type_hint,
                is_constant=False,
            )
            self.variables.append(variable_info)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Visit import statements"""
        for alias in node.names:
            import_info = ImportInfo(
                module=alias.name,
                file_path=self.file_path,
                line_number=node.lineno,
                imports=[alias.name],
                alias=alias.asname,
            )
            self.imports.append(import_info)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from ... import statements"""
        module = node.module or ""

        for alias in node.names:
            import_info = ImportInfo(
                module=module,
                file_path=self.file_path,
                line_number=node.lineno,
                imports=[alias.name],
                alias=alias.asname,
            )
            self.imports.append(import_info)

        self.generic_visit(node)

    def _get_current_scope(self) -> str:
        """Get current scope (module, class, or function)"""
        if self.current_class:
            return f"class:{self.current_class}"
        elif self.current_function:
            return f"function:{self.current_function}"
        else:
            return "module"

    def _get_literal_value(self, node: ast.AST) -> Any:
        """Extract literal value from AST node"""
        try:
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.Num):
                return node.n
            else:
                return ast.unparse(node)
        except:
            return str(node)


class CodeMapManager:
    """Manager for code map operations"""

    def __init__(self, map_file: str = "code_map.json"):
        self.map_file = map_file
        self.code_map: Optional[CodeMap] = None

    def generate_map(self, project_root: str):
        """Generate code map for project"""
        analyzer = CodeAnalyzer(project_root)
        self.code_map = analyzer.analyze_project()
        self._save_map()
        print(
            f"✅ Code map generated: {len(self.code_map.functions)} functions, {len(self.code_map.classes)} classes"
        )

    def load_map(self):
        """Load existing code map"""
        if os.path.exists(self.map_file):
            with open(self.map_file) as f:
                data = json.load(f)

                # Reconstruct dataclass objects from JSON
                functions = [FunctionInfo(**func) for func in data.get("functions", [])]
                classes = [ClassInfo(**cls) for cls in data.get("classes", [])]
                variables = [VariableInfo(**var) for var in data.get("variables", [])]
                imports = [ImportInfo(**imp) for imp in data.get("imports", [])]

                self.code_map = CodeMap(
                    functions=functions,
                    classes=classes,
                    variables=variables,
                    imports=imports,
                    modules=data.get("modules", []),
                    generated_at=data.get("generated_at", ""),
                )
            print(
                f"📋 Code map loaded: {len(self.code_map.functions)} functions, {len(self.code_map.classes)} classes"
            )
        else:
            print("❌ No code map found. Run 'analyze' first.")
            sys.exit(1)

    def _save_map(self):
        """Save code map to file"""
        with open(self.map_file, "w") as f:
            json.dump(asdict(self.code_map), f, indent=2, default=str)
        print(f"💾 Code map saved to {self.map_file}")

    def search_functions(self, query: str) -> List[FunctionInfo]:
        """Search for functions by name"""
        if not self.code_map:
            self.load_map()

        results = []
        query_lower = query.lower()

        for func in self.code_map.functions:
            if query_lower in func.name.lower():
                results.append(func)

        return results

    def search_classes(self, query: str) -> List[ClassInfo]:
        """Search for classes by name"""
        if not self.code_map:
            self.load_map()

        results = []
        query_lower = query.lower()

        for cls in self.code_map.classes:
            if query_lower in cls.name.lower():
                results.append(cls)

        return results

    def get_function_signature(
        self, function_name: str, file_path: Optional[str] = None
    ) -> Optional[FunctionInfo]:
        """Get function signature by name"""
        if not self.code_map:
            self.load_map()

        for func in self.code_map.functions:
            if func.name == function_name:
                if file_path is None or file_path in func.file_path:
                    return func

        return None

    def validate_function_call(
        self, function_name: str, parameters: List[str], file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a function call against actual signature"""
        func = self.get_function_signature(function_name, file_path)

        if not func:
            return {
                "valid": False,
                "error": f"Function '{function_name}' not found",
                "suggestions": self._get_similar_functions(function_name),
            }

        # Check parameter count
        if len(parameters) < len(func.parameters) - len(func.default_values):
            return {
                "valid": False,
                "error": f"Function '{function_name}' requires {len(func.parameters)} parameters, got {len(parameters)}",
                "signature": f"{function_name}({', '.join(func.parameters)})",
                "file": func.file_path,
                "line": func.line_number,
            }

        return {
            "valid": True,
            "signature": f"{function_name}({', '.join(func.parameters)})",
            "file": func.file_path,
            "line": func.line_number,
        }

    def _get_similar_functions(self, function_name: str) -> List[str]:
        """Get similar function names for suggestions"""
        if not self.code_map:
            return []

        suggestions = []
        for func in self.code_map.functions:
            if (
                function_name.lower() in func.name.lower()
                or func.name.lower() in function_name.lower()
            ):
                suggestions.append(func.name)

        return suggestions[:5]  # Return top 5 suggestions


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Code Mapper - Comprehensive Code Analysis"
    )
    parser.add_argument(
        "command",
        choices=["analyze", "search", "validate", "info"],
        help="Command to run",
    )
    parser.add_argument(
        "--project", default="src/applications/oamat_sd", help="Project root directory"
    )
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--function", help="Function name for validation")
    parser.add_argument("--parameters", nargs="*", help="Parameters for validation")

    args = parser.parse_args()

    manager = CodeMapManager()

    if args.command == "analyze":
        manager.generate_map(args.project)

    elif args.command == "search":
        if not args.query:
            print("❌ Please provide a search query with --query")
            sys.exit(1)

        manager.load_map()

        print(f"🔍 Searching for: {args.query}")
        print("\n📋 Functions:")
        functions = manager.search_functions(args.query)
        for func in functions:
            print(
                f"  {func.name}({', '.join(func.parameters)}) - {func.file_path}:{func.line_number}"
            )

        print("\n🏗️  Classes:")
        classes = manager.search_classes(args.query)
        for cls in classes:
            print(f"  {cls.name} - {cls.file_path}:{cls.line_number}")

    elif args.command == "validate":
        if not args.function:
            print("❌ Please provide a function name with --function")
            sys.exit(1)

        manager.load_map()
        result = manager.validate_function_call(args.function, args.parameters or [])

        if result["valid"]:
            print(f"✅ Valid function call: {result['signature']}")
            print(f"   File: {result['file']}:{result['line']}")
        else:
            print(f"❌ Invalid function call: {result['error']}")
            if "suggestions" in result:
                print(f"💡 Suggestions: {', '.join(result['suggestions'])}")

    elif args.command == "info":
        manager.load_map()
        print("📊 Code Map Information:")
        print(f"   Generated: {manager.code_map.generated_at}")
        print(f"   Functions: {len(manager.code_map.functions)}")
        print(f"   Classes: {len(manager.code_map.classes)}")
        print(f"   Variables: {len(manager.code_map.variables)}")
        print(f"   Imports: {len(manager.code_map.imports)}")
        print(f"   Modules: {len(manager.code_map.modules)}")


if __name__ == "__main__":
    main()
