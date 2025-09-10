"""Advanced language-specific parsers for enhanced code analysis.

This module provides sophisticated parsing capabilities for multiple programming languages,
extracting detailed symbol information, dependencies, and architectural patterns.
"""

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class LanguageParserRegistry:
    """Registry for language-specific parsers."""

    def __init__(self):
        self.parsers = {
            "python": PythonParser(),
            "javascript": JavaScriptParser(),
            "typescript": TypeScriptParser(),
            "java": JavaParser(),
            "go": GoParser(),
            "rust": RustParser(),
            "cpp": CppParser(),
            "c": CParser(),
            "ruby": RubyParser(),
            "php": PHPParser(),
        }

    def get_parser(self, language: str) -> Optional["LanguageParser"]:
        """Get parser for the specified language."""
        return self.parsers.get(language.lower())

    def parse_file(self, content: str, file_path: str, language: str) -> Dict[str, Any]:
        """Parse file content using the appropriate language parser."""
        parser = self.get_parser(language)
        if parser:
            return parser.parse(content, file_path)
        else:
            # Fallback to generic parsing
            return GenericParser().parse(content, file_path)


class LanguageParser:
    """Base class for language-specific parsers."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse content and extract symbols."""
        raise NotImplementedError

    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract import statements."""
        return []

    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        return []

    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        return []

    def _calculate_complexity(self, node_or_content: Any) -> int:
        """Calculate cyclomatic complexity."""
        return 1


class PythonParser(LanguageParser):
    """Advanced Python parser using AST."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse Python code using AST analysis."""
        symbols = {
            "language": "python",
            "file_path": file_path,
            "functions": [],
            "classes": [],
            "variables": [],
            "constants": [],
            "imports": [],
            "decorators": [],
            "type_annotations": [],
            "exception_patterns": [],
            "comprehensions": [],
            "async_patterns": [],
            "complexity_metrics": {},
        }

        try:
            tree = ast.parse(content)

            # Extract all symbols using AST visitors
            symbols["functions"] = self._extract_functions_ast(tree, content)
            symbols["classes"] = self._extract_classes_ast(tree, content)
            symbols["imports"] = self._extract_imports_ast(tree)
            symbols["variables"], symbols["constants"] = self._extract_variables_ast(
                tree
            )
            symbols["decorators"] = self._extract_decorators_ast(tree)
            symbols["type_annotations"] = self._extract_type_annotations_ast(tree)
            symbols["exception_patterns"] = self._extract_exception_patterns_ast(tree)
            symbols["comprehensions"] = self._extract_comprehensions_ast(tree)
            symbols["async_patterns"] = self._extract_async_patterns_ast(tree)

            # Calculate comprehensive complexity metrics
            symbols["complexity_metrics"] = self._calculate_python_complexity(
                tree, content
            )

        except SyntaxError as e:
            logger.warning(f"Python syntax error in {file_path}: {e}")
            # Fallback to regex parsing
            symbols.update(self._fallback_regex_parsing(content))

        return symbols

    def _extract_functions_ast(
        self, tree: ast.AST, content: str
    ) -> List[Dict[str, Any]]:
        """Extract detailed function information using AST."""
        functions = []
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", None),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_generator": any(
                        isinstance(n, (ast.Yield, ast.YieldFrom))
                        for n in ast.walk(node)
                    ),
                    "is_property": any(
                        self._decorator_name(d) == "property"
                        for d in node.decorator_list
                    ),
                    "is_classmethod": any(
                        self._decorator_name(d) == "classmethod"
                        for d in node.decorator_list
                    ),
                    "is_staticmethod": any(
                        self._decorator_name(d) == "staticmethod"
                        for d in node.decorator_list
                    ),
                    "parameters": self._extract_function_parameters(node),
                    "return_annotation": ast.unparse(node.returns)
                    if hasattr(ast, "unparse") and node.returns
                    else None,
                    "decorators": [
                        self._decorator_name(d) for d in node.decorator_list
                    ],
                    "docstring": ast.get_docstring(node),
                    "calls": self._extract_function_calls(node),
                    "variables_used": self._extract_variables_used(node),
                    "raises": self._extract_raised_exceptions(node),
                    "complexity_score": self._calculate_cyclomatic_complexity(node),
                    "nested_functions": len(
                        [
                            n
                            for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        ]
                    ),
                    "conditional_blocks": len(
                        [
                            n
                            for n in ast.walk(node)
                            if isinstance(n, (ast.If, ast.While, ast.For))
                        ]
                    ),
                }

                # Add signature
                params = ", ".join(p["name"] for p in func_info["parameters"])
                async_prefix = "async " if func_info["is_async"] else ""
                func_info["signature"] = f"{async_prefix}def {node.name}({params})"

                functions.append(func_info)

        return functions

    def _extract_classes_ast(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Extract detailed class information using AST."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract methods
                methods = []
                properties = []
                class_methods = []
                static_methods = []

                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            "name": child.name,
                            "line": child.lineno,
                            "is_async": isinstance(child, ast.AsyncFunctionDef),
                            "is_property": any(
                                self._decorator_name(d) == "property"
                                for d in child.decorator_list
                            ),
                            "is_classmethod": any(
                                self._decorator_name(d) == "classmethod"
                                for d in child.decorator_list
                            ),
                            "is_staticmethod": any(
                                self._decorator_name(d) == "staticmethod"
                                for d in child.decorator_list
                            ),
                            "parameters": self._extract_function_parameters(child),
                            "docstring": ast.get_docstring(child),
                            "complexity": self._calculate_cyclomatic_complexity(child),
                        }

                        if method_info["is_property"]:
                            properties.append(method_info)
                        elif method_info["is_classmethod"]:
                            class_methods.append(method_info)
                        elif method_info["is_staticmethod"]:
                            static_methods.append(method_info)
                        else:
                            methods.append(method_info)

                class_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", None),
                    "base_classes": [
                        ast.unparse(base) if hasattr(ast, "unparse") else str(base)
                        for base in node.bases
                    ],
                    "decorators": [
                        self._decorator_name(d) for d in node.decorator_list
                    ],
                    "docstring": ast.get_docstring(node),
                    "methods": methods,
                    "properties": properties,
                    "class_methods": class_methods,
                    "static_methods": static_methods,
                    "method_count": len(methods)
                    + len(properties)
                    + len(class_methods)
                    + len(static_methods),
                    "is_abstract": "ABC"
                    in [
                        ast.unparse(base) if hasattr(ast, "unparse") else str(base)
                        for base in node.bases
                    ],
                    "nested_classes": len(
                        [n for n in node.body if isinstance(n, ast.ClassDef)]
                    ),
                }

                classes.append(class_info)

        return classes

    def _extract_imports_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract detailed import information using AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                            "is_from_import": False,
                            "level": 0,
                            "statement": f"import {alias.name}{' as ' + alias.asname if alias.asname else ''}",
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                            "is_from_import": True,
                            "level": node.level,
                            "is_star_import": alias.name == "*",
                            "statement": f"from {module} import {alias.name}{' as ' + alias.asname if alias.asname else ''}",
                        }
                    )

        return imports

    def _extract_variables_ast(self, tree: ast.AST) -> tuple:
        """Extract module-level variables and constants."""
        variables = []
        constants = []

        for node in tree.body:  # Only top-level assignments
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = {
                            "name": target.id,
                            "line": node.lineno,
                            "type_annotation": None,
                            "is_constant": target.id.isupper(),
                            "value_type": self._get_value_type(node.value),
                        }

                        if target.id.isupper():
                            constants.append(var_info)
                        else:
                            variables.append(var_info)

            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                var_info = {
                    "name": node.target.id,
                    "line": node.lineno,
                    "type_annotation": ast.unparse(node.annotation)
                    if hasattr(ast, "unparse")
                    else str(node.annotation),
                    "is_constant": node.target.id.isupper(),
                    "value_type": self._get_value_type(node.value)
                    if node.value
                    else None,
                }

                if node.target.id.isupper():
                    constants.append(var_info)
                else:
                    variables.append(var_info)

        return variables, constants

    def _extract_decorators_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract decorator usage patterns."""
        decorators = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    decorator_info = {
                        "name": self._decorator_name(decorator),
                        "applied_to": node.name,
                        "applied_to_type": "function"
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        else "class",
                        "line": decorator.lineno
                        if hasattr(decorator, "lineno")
                        else node.lineno,
                        "arguments": self._extract_decorator_arguments(decorator),
                    }
                    decorators.append(decorator_info)

        return decorators

    def _extract_type_annotations_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract type annotations and hints."""
        annotations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Return annotation
                if node.returns:
                    annotations.append(
                        {
                            "type": "return_annotation",
                            "function": node.name,
                            "annotation": ast.unparse(node.returns)
                            if hasattr(ast, "unparse")
                            else str(node.returns),
                            "line": node.lineno,
                        }
                    )

                # Parameter annotations
                for arg in node.args.args:
                    if arg.annotation:
                        annotations.append(
                            {
                                "type": "parameter_annotation",
                                "function": node.name,
                                "parameter": arg.arg,
                                "annotation": ast.unparse(arg.annotation)
                                if hasattr(ast, "unparse")
                                else str(arg.annotation),
                                "line": node.lineno,
                            }
                        )

            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    annotations.append(
                        {
                            "type": "variable_annotation",
                            "variable": node.target.id,
                            "annotation": ast.unparse(node.annotation)
                            if hasattr(ast, "unparse")
                            else str(node.annotation),
                            "line": node.lineno,
                        }
                    )

        return annotations

    def _extract_exception_patterns_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract exception handling patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                pattern = {
                    "line": node.lineno,
                    "handlers": [],
                    "has_else": bool(node.orelse),
                    "has_finally": bool(node.finalbody),
                    "context": self._get_node_context(node),
                }

                for handler in node.handlers:
                    handler_info = {
                        "exception_type": ast.unparse(handler.type)
                        if hasattr(ast, "unparse") and handler.type
                        else "bare_except",
                        "variable": handler.name
                        if hasattr(handler, "name") and handler.name
                        else None,
                        "line": handler.lineno,
                    }
                    pattern["handlers"].append(handler_info)

                patterns.append(pattern)

        return patterns

    def _extract_comprehensions_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract list/dict/set comprehensions."""
        comprehensions = []

        for node in ast.walk(tree):
            if isinstance(
                node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)
            ):
                comp_type = {
                    ast.ListComp: "list",
                    ast.DictComp: "dict",
                    ast.SetComp: "set",
                    ast.GeneratorExp: "generator",
                }[type(node)]

                comprehensions.append(
                    {
                        "type": comp_type,
                        "line": node.lineno,
                        "generators": len(node.generators),
                        "conditions": sum(len(gen.ifs) for gen in node.generators),
                        "complexity": 1 + sum(len(gen.ifs) for gen in node.generators),
                    }
                )

        return comprehensions

    def _extract_async_patterns_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract async/await patterns."""
        patterns = []

        async_functions = []
        await_calls = []
        async_with_statements = []
        async_for_loops = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_functions.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "has_await": any(
                            isinstance(n, ast.Await) for n in ast.walk(node)
                        ),
                    }
                )

            elif isinstance(node, ast.Await):
                await_calls.append(
                    {
                        "line": node.lineno,
                        "awaited": ast.unparse(node.value)
                        if hasattr(ast, "unparse")
                        else str(node.value),
                    }
                )

            elif isinstance(node, ast.AsyncWith):
                async_with_statements.append(
                    {"line": node.lineno, "items": len(node.items)}
                )

            elif isinstance(node, ast.AsyncFor):
                async_for_loops.append(
                    {
                        "line": node.lineno,
                        "target": ast.unparse(node.target)
                        if hasattr(ast, "unparse")
                        else str(node.target),
                    }
                )

        return {
            "async_functions": async_functions,
            "await_calls": await_calls,
            "async_with_statements": async_with_statements,
            "async_for_loops": async_for_loops,
            "total_async_constructs": len(async_functions)
            + len(await_calls)
            + len(async_with_statements)
            + len(async_for_loops),
        }

    def _calculate_python_complexity(
        self, tree: ast.AST, content: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive complexity metrics."""
        lines = content.splitlines()

        metrics = {
            "total_lines": len(lines),
            "code_lines": len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            ),
            "comment_lines": len(
                [line for line in lines if line.strip().startswith("#")]
            ),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "cyclomatic_complexity": self._calculate_total_complexity(tree),
            "nesting_depth": self._calculate_max_nesting_depth(tree),
            "maintainability_index": 0,  # Will be calculated
        }

        # Calculate maintainability index (simplified)
        if metrics["code_lines"] > 0:
            complexity_ratio = metrics["cyclomatic_complexity"] / metrics["code_lines"]
            comment_ratio = metrics["comment_lines"] / metrics["total_lines"]

            metrics["maintainability_index"] = max(
                0, 100 - (complexity_ratio * 50) + (comment_ratio * 20)
            )

        return metrics

    # Helper methods
    def _decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._decorator_name(decorator.func)
        else:
            return str(decorator)

    def _extract_function_parameters(
        self, func_node: ast.FunctionDef
    ) -> List[Dict[str, Any]]:
        """Extract detailed parameter information."""
        parameters = []

        # Regular arguments
        for arg in func_node.args.args:
            param = {
                "name": arg.arg,
                "type_annotation": ast.unparse(arg.annotation)
                if hasattr(ast, "unparse") and arg.annotation
                else None,
                "kind": "positional",
                "default": None,
            }
            parameters.append(param)

        # Add defaults
        if func_node.args.defaults:
            defaults_start = len(parameters) - len(func_node.args.defaults)
            for i, default in enumerate(func_node.args.defaults):
                if defaults_start + i < len(parameters):
                    parameters[defaults_start + i]["default"] = (
                        ast.unparse(default)
                        if hasattr(ast, "unparse")
                        else str(default)
                    )

        # *args
        if func_node.args.vararg:
            parameters.append(
                {
                    "name": func_node.args.vararg.arg,
                    "type_annotation": ast.unparse(func_node.args.vararg.annotation)
                    if hasattr(ast, "unparse") and func_node.args.vararg.annotation
                    else None,
                    "kind": "var_positional",
                    "default": None,
                }
            )

        # **kwargs
        if func_node.args.kwarg:
            parameters.append(
                {
                    "name": func_node.args.kwarg.arg,
                    "type_annotation": ast.unparse(func_node.args.kwarg.annotation)
                    if hasattr(ast, "unparse") and func_node.args.kwarg.annotation
                    else None,
                    "kind": "var_keyword",
                    "default": None,
                }
            )

        return parameters

    def _extract_function_calls(self, node) -> List[str]:
        """Extract function calls within a node."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(
                        f"{ast.unparse(child.func.value) if hasattr(ast, 'unparse') else str(child.func.value)}.{child.func.attr}"
                    )
        return list(set(calls))

    def _extract_variables_used(self, node) -> List[str]:
        """Extract variables used within a node."""
        variables = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                variables.append(child.id)
        return list(set(variables))

    def _extract_raised_exceptions(self, node) -> List[str]:
        """Extract raised exceptions within a node."""
        exceptions = []
        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and child.exc:
                if isinstance(child.exc, ast.Name):
                    exceptions.append(child.exc.id)
                elif isinstance(child.exc, ast.Call) and isinstance(
                    child.exc.func, ast.Name
                ):
                    exceptions.append(child.exc.func.id)
        return list(set(exceptions))

    def _calculate_cyclomatic_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity

    def _calculate_total_complexity(self, tree: ast.AST) -> int:
        """Calculate total cyclomatic complexity for the module."""
        total = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += self._calculate_cyclomatic_complexity(node)
        return total

    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth."""

        def get_depth(node, current_depth=0):
            max_depth = current_depth
            if isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                ),
            ):
                current_depth += 1

            for child in ast.iter_child_nodes(node):
                child_depth = get_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

            return max_depth

        return get_depth(tree)

    def _get_value_type(self, value_node) -> Optional[str]:
        """Get the type of a value from AST node."""
        if isinstance(value_node, ast.Constant):
            return type(value_node.value).__name__
        elif isinstance(value_node, (ast.List, ast.ListComp)):
            return "list"
        elif isinstance(value_node, (ast.Dict, ast.DictComp)):
            return "dict"
        elif isinstance(value_node, (ast.Set, ast.SetComp)):
            return "set"
        elif isinstance(value_node, ast.Tuple):
            return "tuple"
        elif isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                return value_node.func.id
        return None

    def _get_node_context(self, node) -> str:
        """Get context information for a node."""
        # Find the enclosing function or class
        # This would need a more sophisticated implementation
        return "module"

    def _extract_decorator_arguments(self, decorator) -> List[str]:
        """Extract arguments from a decorator call."""
        if isinstance(decorator, ast.Call):
            args = []
            for arg in decorator.args:
                args.append(ast.unparse(arg) if hasattr(ast, "unparse") else str(arg))
            return args
        return []

    def _fallback_regex_parsing(self, content: str) -> Dict[str, Any]:
        """Fallback regex parsing when AST fails."""
        symbols = {
            "functions": self._extract_functions_regex(content),
            "classes": self._extract_classes_regex(content),
            "imports": self._extract_imports_regex(content),
        }
        return symbols

    def _extract_functions_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract functions using regex."""
        functions = []
        pattern = r"^(?:\s*)(?:async\s+)?def\s+(\w+)\s*\([^)]*\):"

        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "signature": match.group(0).strip(),
                    "is_async": "async" in match.group(0),
                }
            )

        return functions

    def _extract_classes_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract classes using regex."""
        classes = []
        pattern = r"^(?:\s*)class\s+(\w+)(?:\([^)]*\))?:"

        for match in re.finditer(pattern, content, re.MULTILINE):
            classes.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "signature": match.group(0).strip(),
                }
            )

        return classes

    def _extract_imports_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract imports using regex."""
        imports = []

        # import statements
        import_pattern = r"^(?:\s*)import\s+(.+)$"
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            imports.append(
                {
                    "type": "import",
                    "statement": match.group(0).strip(),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        # from ... import statements
        from_pattern = r"^(?:\s*)from\s+(.+?)\s+import\s+(.+)$"
        for match in re.finditer(from_pattern, content, re.MULTILINE):
            imports.append(
                {
                    "type": "from_import",
                    "module": match.group(1),
                    "imported": match.group(2),
                    "statement": match.group(0).strip(),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return imports


class JavaScriptParser(LanguageParser):
    """JavaScript/Node.js parser with ES6+ support."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse JavaScript code with comprehensive analysis."""
        symbols = {
            "language": "javascript",
            "file_path": file_path,
            "functions": self._extract_js_functions(content),
            "classes": self._extract_js_classes(content),
            "imports": self._extract_js_imports(content),
            "exports": self._extract_js_exports(content),
            "variables": self._extract_js_variables(content),
            "arrow_functions": self._extract_arrow_functions(content),
            "async_patterns": self._extract_js_async_patterns(content),
            "complexity_metrics": self._calculate_js_complexity(content),
        }

        return symbols

    def _extract_js_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript function declarations."""
        functions = []

        # Regular function declarations
        pattern = r"^\s*(export\s+)?(async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*\{"
        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(3),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_async": bool(match.group(2)),
                    "is_exported": bool(match.group(1)),
                    "parameters": [
                        p.strip() for p in match.group(4).split(",") if p.strip()
                    ],
                    "signature": match.group(0).strip(),
                    "type": "function_declaration",
                }
            )

        # Function expressions
        pattern = (
            r"(const|let|var)\s+(\w+)\s*=\s*(async\s+)?function\s*\(([^)]*)\)\s*\{"
        )
        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_async": bool(match.group(3)),
                    "parameters": [
                        p.strip() for p in match.group(4).split(",") if p.strip()
                    ],
                    "signature": match.group(0).strip(),
                    "type": "function_expression",
                }
            )

        return functions

    def _extract_arrow_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract arrow functions."""
        arrow_functions = []

        # Arrow function assignments
        pattern = r"(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)\s*=>"
        for match in re.finditer(pattern, content, re.MULTILINE):
            arrow_functions.append(
                {
                    "name": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_async": bool(match.group(3)),
                    "parameters": [
                        p.strip() for p in match.group(4).split(",") if p.strip()
                    ],
                    "signature": match.group(0).strip(),
                    "type": "arrow_function",
                }
            )

        return arrow_functions

    def _extract_js_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript class declarations."""
        classes = []

        pattern = r"^\s*(export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{"
        for match in re.finditer(pattern, content, re.MULTILINE):
            class_info = {
                "name": match.group(2),
                "line": content[: match.start()].count("\n") + 1,
                "extends": match.group(3),
                "is_exported": bool(match.group(1)),
                "signature": match.group(0).strip(),
                "methods": self._extract_class_methods(content, match.group(2)),
            }
            classes.append(class_info)

        return classes

    def _extract_class_methods(
        self, content: str, class_name: str
    ) -> List[Dict[str, Any]]:
        """Extract methods from a JavaScript class."""
        methods = []

        # Find class body (simplified approach)
        class_pattern = f"class\\s+{class_name}.*?\\{{"
        match = re.search(class_pattern, content, re.DOTALL)
        if not match:
            return methods

        # Extract methods within class
        method_pattern = r"^\s*(static\s+)?(async\s+)?(\w+)\s*\([^)]*\)\s*\{"
        class_start = match.end()

        # Find class end (simplified)
        brace_count = 1
        class_end = class_start
        for i, char in enumerate(content[class_start:]):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    class_end = class_start + i
                    break

        class_body = content[class_start:class_end]

        for match in re.finditer(method_pattern, class_body, re.MULTILINE):
            methods.append(
                {
                    "name": match.group(3),
                    "line": content[: class_start + match.start()].count("\n") + 1,
                    "is_static": bool(match.group(1)),
                    "is_async": bool(match.group(2)),
                    "signature": match.group(0).strip(),
                }
            )

        return methods

    def _extract_js_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript import statements."""
        imports = []

        # ES6 imports
        patterns = [
            r"import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]",
            r"import\s+['\"]([^'\"]+)['\"]",
            r"const\s+(.+?)\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                import_info = {
                    "line": content[: match.start()].count("\n") + 1,
                    "statement": match.group(0).strip(),
                    "type": "require" if "require" in match.group(0) else "import",
                }

                if len(match.groups()) == 2:
                    import_info["imported"] = match.group(1).strip()
                    import_info["module"] = match.group(2)
                else:
                    import_info["module"] = match.group(1)

                imports.append(import_info)

        return imports

    def _extract_js_exports(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript export statements."""
        exports = []

        patterns = [
            r"export\s+(?:default\s+)?(.+?)(?:\s+from\s+['\"]([^'\"]+)['\"])?",
            r"module\.exports\s*=\s*(.+)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                exports.append(
                    {
                        "line": content[: match.start()].count("\n") + 1,
                        "statement": match.group(0).strip(),
                        "exported": match.group(1).strip(),
                        "is_default": "default" in match.group(0),
                        "type": "module.exports"
                        if "module.exports" in match.group(0)
                        else "export",
                    }
                )

        return exports

    def _extract_js_variables(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript variable declarations."""
        variables = []

        patterns = [
            r"^\s*(const|let|var)\s+(\w+)(?:\s*=\s*(.+?))?(?:;|$)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                variables.append(
                    {
                        "name": match.group(2),
                        "line": content[: match.start()].count("\n") + 1,
                        "type": match.group(1),
                        "has_initializer": bool(match.group(3)),
                        "is_constant": match.group(1) == "const",
                    }
                )

        return variables

    def _extract_js_async_patterns(self, content: str) -> Dict[str, Any]:
        """Extract async/await patterns in JavaScript."""
        async_functions = len(re.findall(r"async\s+function", content))
        async_arrows = len(re.findall(r"async\s*\([^)]*\)\s*=>", content))
        await_calls = len(re.findall(r"\bawait\s+", content))
        promises = len(re.findall(r"\.then\s*\(", content))
        promise_constructors = len(re.findall(r"new\s+Promise\s*\(", content))

        return {
            "async_functions": async_functions,
            "async_arrow_functions": async_arrows,
            "await_calls": await_calls,
            "promise_chains": promises,
            "promise_constructors": promise_constructors,
            "total_async_patterns": async_functions
            + async_arrows
            + await_calls
            + promises
            + promise_constructors,
        }

    def _calculate_js_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate JavaScript complexity metrics."""
        lines = content.splitlines()

        # Count various constructs that add to complexity
        if_statements = len(re.findall(r"\bif\s*\(", content))
        for_loops = len(re.findall(r"\bfor\s*\(", content))
        while_loops = len(re.findall(r"\bwhile\s*\(", content))
        switch_statements = len(re.findall(r"\bswitch\s*\(", content))
        try_blocks = len(re.findall(r"\btry\s*\{", content))
        ternary_operators = len(re.findall(r"\?[^:]+:", content))

        cyclomatic_complexity = (
            1
            + if_statements
            + for_loops
            + while_loops
            + switch_statements
            + try_blocks
            + ternary_operators
        )

        return {
            "total_lines": len(lines),
            "code_lines": len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("//")
                ]
            ),
            "comment_lines": len(
                [line for line in lines if line.strip().startswith("//")]
            ),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "cyclomatic_complexity": cyclomatic_complexity,
            "if_statements": if_statements,
            "loops": for_loops + while_loops,
            "switch_statements": switch_statements,
            "try_blocks": try_blocks,
            "ternary_operators": ternary_operators,
        }


class TypeScriptParser(JavaScriptParser):
    """TypeScript parser extending JavaScript parser."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse TypeScript with additional type information."""
        symbols = super().parse(content, file_path)
        symbols["language"] = "typescript"

        # Add TypeScript-specific parsing
        symbols["interfaces"] = self._extract_ts_interfaces(content)
        symbols["types"] = self._extract_ts_types(content)
        symbols["enums"] = self._extract_ts_enums(content)
        symbols["generics"] = self._extract_ts_generics(content)

        return symbols

    def _extract_ts_interfaces(self, content: str) -> List[Dict[str, Any]]:
        """Extract TypeScript interfaces."""
        interfaces = []

        pattern = r"^\s*(export\s+)?interface\s+(\w+)(?:<[^>]+>)?\s*\{"
        for match in re.finditer(pattern, content, re.MULTILINE):
            interfaces.append(
                {
                    "name": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_exported": bool(match.group(1)),
                    "signature": match.group(0).strip(),
                }
            )

        return interfaces

    def _extract_ts_types(self, content: str) -> List[Dict[str, Any]]:
        """Extract TypeScript type definitions."""
        types = []

        pattern = r"^\s*(export\s+)?type\s+(\w+)(?:<[^>]+>)?\s*="
        for match in re.finditer(pattern, content, re.MULTILINE):
            types.append(
                {
                    "name": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_exported": bool(match.group(1)),
                    "signature": match.group(0).strip(),
                }
            )

        return types

    def _extract_ts_enums(self, content: str) -> List[Dict[str, Any]]:
        """Extract TypeScript enums."""
        enums = []

        pattern = r"^\s*(export\s+)?enum\s+(\w+)\s*\{"
        for match in re.finditer(pattern, content, re.MULTILINE):
            enums.append(
                {
                    "name": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_exported": bool(match.group(1)),
                    "signature": match.group(0).strip(),
                }
            )

        return enums

    def _extract_ts_generics(self, content: str) -> List[Dict[str, Any]]:
        """Extract generic type usage."""
        generics = []

        # This is a simplified extraction - a full parser would be more sophisticated
        pattern = r"(\w+)<([^>]+)>"
        for match in re.finditer(pattern, content):
            if not match.group(1) in ["if", "for", "while"]:  # Avoid false positives
                generics.append(
                    {
                        "base_type": match.group(1),
                        "type_parameters": match.group(2),
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

        return generics


class JavaParser(LanguageParser):
    """Java parser with comprehensive analysis."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse Java code."""
        symbols = {
            "language": "java",
            "file_path": file_path,
            "package": self._extract_package(content),
            "imports": self._extract_java_imports(content),
            "classes": self._extract_java_classes(content),
            "interfaces": self._extract_java_interfaces(content),
            "enums": self._extract_java_enums(content),
            "annotations": self._extract_java_annotations(content),
            "complexity_metrics": self._calculate_java_complexity(content),
        }

        return symbols

    def _extract_package(self, content: str) -> Optional[str]:
        """Extract Java package declaration."""
        match = re.search(r"^\s*package\s+([^;]+);", content, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _extract_java_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java import statements."""
        imports = []

        pattern = r"^\s*import\s+(static\s+)?([^;]+);"
        for match in re.finditer(pattern, content, re.MULTILINE):
            imports.append(
                {
                    "package": match.group(2).strip(),
                    "is_static": bool(match.group(1)),
                    "line": content[: match.start()].count("\n") + 1,
                    "statement": match.group(0).strip(),
                }
            )

        return imports

    def _extract_java_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java class declarations."""
        classes = []

        pattern = r"^\s*(?:@\w+\s+)*(?:(public|private|protected)\s+)?(?:(static|final|abstract)\s+)*(class)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            class_info = {
                "name": match.group(4),
                "line": content[: match.start()].count("\n") + 1,
                "visibility": match.group(1) or "package",
                "modifiers": match.group(2).split() if match.group(2) else [],
                "extends": match.group(5),
                "implements": [i.strip() for i in match.group(6).split(",")]
                if match.group(6)
                else [],
                "signature": match.group(0).strip(),
                "methods": self._extract_java_methods(content, match.group(4)),
                "fields": self._extract_java_fields(content, match.group(4)),
            }
            classes.append(class_info)

        return classes

    def _extract_java_interfaces(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java interface declarations."""
        interfaces = []

        pattern = r"^\s*(?:@\w+\s+)*(?:(public|private|protected)\s+)?interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            interfaces.append(
                {
                    "name": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                    "visibility": match.group(1) or "package",
                    "extends": [i.strip() for i in match.group(3).split(",")]
                    if match.group(3)
                    else [],
                    "signature": match.group(0).strip(),
                }
            )

        return interfaces

    def _extract_java_enums(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java enum declarations."""
        enums = []

        pattern = r"^\s*(?:@\w+\s+)*(?:(public|private|protected)\s+)?enum\s+(\w+)\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            enums.append(
                {
                    "name": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                    "visibility": match.group(1) or "package",
                    "signature": match.group(0).strip(),
                }
            )

        return enums

    def _extract_java_methods(
        self, content: str, class_name: str
    ) -> List[Dict[str, Any]]:
        """Extract methods from a Java class (simplified)."""
        methods = []

        pattern = r"^\s*(?:@\w+\s+)*(?:(public|private|protected)\s+)?(?:(static|final|abstract)\s+)*(\w+)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            if match.group(4) != class_name:  # Skip constructors for now
                methods.append(
                    {
                        "name": match.group(4),
                        "line": content[: match.start()].count("\n") + 1,
                        "visibility": match.group(1) or "package",
                        "modifiers": match.group(2).split() if match.group(2) else [],
                        "return_type": match.group(3),
                        "signature": match.group(0).strip(),
                    }
                )

        return methods

    def _extract_java_fields(
        self, content: str, class_name: str
    ) -> List[Dict[str, Any]]:
        """Extract fields from a Java class (simplified)."""
        fields = []

        pattern = r"^\s*(?:(public|private|protected)\s+)?(?:(static|final)\s+)*(\w+)\s+(\w+)(?:\s*=\s*[^;]+)?;"

        for match in re.finditer(pattern, content, re.MULTILINE):
            fields.append(
                {
                    "name": match.group(4),
                    "line": content[: match.start()].count("\n") + 1,
                    "visibility": match.group(1) or "package",
                    "modifiers": match.group(2).split() if match.group(2) else [],
                    "type": match.group(3),
                    "is_constant": "final" in (match.group(2) or ""),
                }
            )

        return fields

    def _extract_java_annotations(self, content: str) -> List[Dict[str, Any]]:
        """Extract Java annotations."""
        annotations = []

        pattern = r"@(\w+)(?:\([^)]*\))?"
        for match in re.finditer(pattern, content):
            annotations.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "full_annotation": match.group(0),
                }
            )

        return annotations

    def _calculate_java_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate Java complexity metrics."""
        lines = content.splitlines()

        # Count complexity indicators
        if_statements = len(re.findall(r"\bif\s*\(", content))
        for_loops = len(re.findall(r"\bfor\s*\(", content))
        while_loops = len(re.findall(r"\bwhile\s*\(", content))
        switch_statements = len(re.findall(r"\bswitch\s*\(", content))
        try_blocks = len(re.findall(r"\btry\s*\{", content))
        catch_blocks = len(re.findall(r"\bcatch\s*\(", content))

        return {
            "total_lines": len(lines),
            "code_lines": len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("//")
                ]
            ),
            "comment_lines": len(
                [line for line in lines if line.strip().startswith("//")]
            ),
            "cyclomatic_complexity": 1
            + if_statements
            + for_loops
            + while_loops
            + switch_statements
            + catch_blocks,
            "if_statements": if_statements,
            "loops": for_loops + while_loops,
            "switch_statements": switch_statements,
            "exception_handling": try_blocks + catch_blocks,
        }


# Simplified parsers for other languages
class GoParser(LanguageParser):
    """Go language parser."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        return {
            "language": "go",
            "file_path": file_path,
            "package": self._extract_go_package(content),
            "imports": self._extract_go_imports(content),
            "functions": self._extract_go_functions(content),
            "types": self._extract_go_types(content),
            "interfaces": self._extract_go_interfaces(content),
        }

    def _extract_go_package(self, content: str) -> Optional[str]:
        match = re.search(r"^\s*package\s+(\w+)", content, re.MULTILINE)
        return match.group(1) if match else None

    def _extract_go_imports(self, content: str) -> List[Dict[str, Any]]:
        imports = []
        # Single import
        for match in re.finditer(r'import\s+"([^"]+)"', content):
            imports.append(
                {
                    "package": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        # Multi-line imports
        import_block = re.search(r"import\s*\(\s*([^)]+)\s*\)", content, re.DOTALL)
        if import_block:
            for line in import_block.group(1).splitlines():
                line = line.strip()
                if line and '"' in line:
                    package = line.split('"')[1]
                    imports.append(
                        {
                            "package": package,
                            "line": content[: import_block.start()].count("\n") + 1,
                        }
                    )

        return imports

    def _extract_go_functions(self, content: str) -> List[Dict[str, Any]]:
        functions = []
        pattern = r"^\s*func\s+(?:\([^)]+\)\s+)?(\w+)\s*\([^)]*\)(?:\s*[^{]+)?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "signature": match.group(0).strip(),
                }
            )

        return functions

    def _extract_go_types(self, content: str) -> List[Dict[str, Any]]:
        types = []
        pattern = r"^\s*type\s+(\w+)\s+"

        for match in re.finditer(pattern, content, re.MULTILINE):
            types.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return types

    def _extract_go_interfaces(self, content: str) -> List[Dict[str, Any]]:
        interfaces = []
        pattern = r"^\s*type\s+(\w+)\s+interface\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            interfaces.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return interfaces


class RustParser(LanguageParser):
    """Rust language parser."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        return {
            "language": "rust",
            "file_path": file_path,
            "functions": self._extract_rust_functions(content),
            "structs": self._extract_rust_structs(content),
            "enums": self._extract_rust_enums(content),
            "traits": self._extract_rust_traits(content),
            "impls": self._extract_rust_impls(content),
            "use_statements": self._extract_rust_uses(content),
        }

    def _extract_rust_functions(self, content: str) -> List[Dict[str, Any]]:
        functions = []
        pattern = r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)(?:\s*->\s*[^{]+)?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_public": "pub" in match.group(0),
                    "is_async": "async" in match.group(0),
                    "signature": match.group(0).strip(),
                }
            )

        return functions

    def _extract_rust_structs(self, content: str) -> List[Dict[str, Any]]:
        structs = []
        pattern = r"^\s*(?:pub\s+)?struct\s+(\w+)(?:<[^>]*>)?\s*(?:\{|;)"

        for match in re.finditer(pattern, content, re.MULTILINE):
            structs.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_public": "pub" in match.group(0),
                    "signature": match.group(0).strip(),
                }
            )

        return structs

    def _extract_rust_enums(self, content: str) -> List[Dict[str, Any]]:
        enums = []
        pattern = r"^\s*(?:pub\s+)?enum\s+(\w+)(?:<[^>]*>)?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            enums.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_public": "pub" in match.group(0),
                }
            )

        return enums

    def _extract_rust_traits(self, content: str) -> List[Dict[str, Any]]:
        traits = []
        pattern = r"^\s*(?:pub\s+)?trait\s+(\w+)(?:<[^>]*>)?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            traits.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_public": "pub" in match.group(0),
                }
            )

        return traits

    def _extract_rust_impls(self, content: str) -> List[Dict[str, Any]]:
        impls = []
        pattern = r"^\s*impl(?:<[^>]*>)?\s+(?:(\w+)\s+for\s+)?(\w+)(?:<[^>]*>)?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            impls.append(
                {
                    "trait": match.group(1),
                    "type": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return impls

    def _extract_rust_uses(self, content: str) -> List[Dict[str, Any]]:
        uses = []
        pattern = r"^\s*(?:pub\s+)?use\s+([^;]+);"

        for match in re.finditer(pattern, content, re.MULTILINE):
            uses.append(
                {
                    "path": match.group(1).strip(),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_public": "pub" in match.group(0),
                }
            )

        return uses


# Additional language parsers would follow similar patterns
class CppParser(LanguageParser):
    """C++ language parser (simplified)."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        return {
            "language": "cpp",
            "file_path": file_path,
            "includes": self._extract_includes(content),
            "functions": self._extract_cpp_functions(content),
            "classes": self._extract_cpp_classes(content),
            "namespaces": self._extract_namespaces(content),
        }

    def _extract_includes(self, content: str) -> List[Dict[str, Any]]:
        includes = []
        pattern = r'^\s*#include\s*[<"]([^>"]+)[>"]'

        for match in re.finditer(pattern, content, re.MULTILINE):
            includes.append(
                {
                    "header": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_system": match.group(0).strip().endswith(">"),
                }
            )

        return includes

    def _extract_cpp_functions(self, content: str) -> List[Dict[str, Any]]:
        functions = []
        # Simplified function extraction
        pattern = r"^\s*(?:(?:inline|static|virtual|explicit)\s+)*(\w+(?:\s*\*)*)\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:override\s*)?[{;]"

        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(2),
                    "return_type": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "signature": match.group(0).strip(),
                }
            )

        return functions

    def _extract_cpp_classes(self, content: str) -> List[Dict[str, Any]]:
        classes = []
        pattern = r"^\s*(?:template\s*<[^>]*>\s*)?class\s+(\w+)(?:\s*:\s*[^{]+)?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            classes.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                    "is_template": "template" in match.group(0),
                }
            )

        return classes

    def _extract_namespaces(self, content: str) -> List[Dict[str, Any]]:
        namespaces = []
        pattern = r"^\s*namespace\s+(\w+)\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            namespaces.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return namespaces


class CParser(CppParser):
    """C language parser (extends C++)."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        symbols = super().parse(content, file_path)
        symbols["language"] = "c"
        # C doesn't have classes, so remove them
        symbols.pop("classes", None)
        symbols.pop("namespaces", None)
        return symbols


class RubyParser(LanguageParser):
    """Ruby language parser."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        return {
            "language": "ruby",
            "file_path": file_path,
            "classes": self._extract_ruby_classes(content),
            "modules": self._extract_ruby_modules(content),
            "methods": self._extract_ruby_methods(content),
            "requires": self._extract_ruby_requires(content),
        }

    def _extract_ruby_classes(self, content: str) -> List[Dict[str, Any]]:
        classes = []
        pattern = r"^\s*class\s+(\w+)(?:\s*<\s*(\w+))?\s*$"

        for match in re.finditer(pattern, content, re.MULTILINE):
            classes.append(
                {
                    "name": match.group(1),
                    "superclass": match.group(2),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return classes

    def _extract_ruby_modules(self, content: str) -> List[Dict[str, Any]]:
        modules = []
        pattern = r"^\s*module\s+(\w+)\s*$"

        for match in re.finditer(pattern, content, re.MULTILINE):
            modules.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return modules

    def _extract_ruby_methods(self, content: str) -> List[Dict[str, Any]]:
        methods = []
        pattern = r"^\s*def\s+(?:(self)\.)? *(\w+)(?:\([^)]*\))?\s*$"

        for match in re.finditer(pattern, content, re.MULTILINE):
            methods.append(
                {
                    "name": match.group(2),
                    "is_class_method": bool(match.group(1)),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return methods

    def _extract_ruby_requires(self, content: str) -> List[Dict[str, Any]]:
        requires = []
        patterns = [
            r"require\s+['\"]([^'\"]+)['\"]",
            r"require_relative\s+['\"]([^'\"]+)['\"]",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                requires.append(
                    {
                        "library": match.group(1),
                        "line": content[: match.start()].count("\n") + 1,
                        "type": "relative"
                        if "require_relative" in match.group(0)
                        else "absolute",
                    }
                )

        return requires


class PHPParser(LanguageParser):
    """PHP language parser."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        return {
            "language": "php",
            "file_path": file_path,
            "classes": self._extract_php_classes(content),
            "functions": self._extract_php_functions(content),
            "interfaces": self._extract_php_interfaces(content),
            "traits": self._extract_php_traits(content),
            "uses": self._extract_php_uses(content),
        }

    def _extract_php_classes(self, content: str) -> List[Dict[str, Any]]:
        classes = []
        pattern = r"^\s*(?:(?:abstract|final)\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            classes.append(
                {
                    "name": match.group(1),
                    "extends": match.group(2),
                    "implements": [i.strip() for i in match.group(3).split(",")]
                    if match.group(3)
                    else [],
                    "line": content[: match.start()].count("\n") + 1,
                    "is_abstract": "abstract" in match.group(0),
                    "is_final": "final" in match.group(0),
                }
            )

        return classes

    def _extract_php_functions(self, content: str) -> List[Dict[str, Any]]:
        functions = []
        # Class methods
        pattern = r"^\s*(?:(public|private|protected)\s+)?(?:(static)\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(
                {
                    "name": match.group(3),
                    "visibility": match.group(1) or "public",
                    "is_static": bool(match.group(2)),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return functions

    def _extract_php_interfaces(self, content: str) -> List[Dict[str, Any]]:
        interfaces = []
        pattern = r"^\s*interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            interfaces.append(
                {
                    "name": match.group(1),
                    "extends": [i.strip() for i in match.group(2).split(",")]
                    if match.group(2)
                    else [],
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return interfaces

    def _extract_php_traits(self, content: str) -> List[Dict[str, Any]]:
        traits = []
        pattern = r"^\s*trait\s+(\w+)\s*\{"

        for match in re.finditer(pattern, content, re.MULTILINE):
            traits.append(
                {
                    "name": match.group(1),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return traits

    def _extract_php_uses(self, content: str) -> List[Dict[str, Any]]:
        uses = []
        pattern = r"^\s*use\s+([^;]+);"

        for match in re.finditer(pattern, content, re.MULTILINE):
            uses.append(
                {
                    "namespace": match.group(1).strip(),
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return uses


class GenericParser(LanguageParser):
    """Generic parser for unsupported languages."""

    def parse(self, content: str, file_path: str) -> Dict[str, Any]:
        """Basic parsing using common patterns."""
        return {
            "language": "unknown",
            "file_path": file_path,
            "functions": self._extract_generic_functions(content),
            "comments": self._extract_generic_comments(content),
            "imports": self._extract_generic_imports(content),
            "complexity_metrics": self._calculate_generic_complexity(content),
        }

    def _extract_generic_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function-like patterns."""
        functions = []
        patterns = [
            r"^\s*(?:function|def|fn)\s+(\w+)",  # function definitions
            r"^\s*(\w+)\s*:\s*function",  # object method definitions
            r"^\s*(\w+)\s*=\s*function",  # function assignments
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                functions.append(
                    {
                        "name": match.group(1),
                        "line": content[: match.start()].count("\n") + 1,
                        "signature": match.group(0).strip(),
                    }
                )

        return functions

    def _extract_generic_comments(self, content: str) -> List[Dict[str, Any]]:
        """Extract comments using common patterns."""
        comments = []
        patterns = [
            r"^\s*//.*$",  # Single line comments
            r"^\s*#.*$",  # Shell/Python style comments
            r"/\*.*?\*/",  # Multi-line comments
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                comments.append(
                    {
                        "line": content[: match.start()].count("\n") + 1,
                        "text": match.group(0).strip(),
                        "type": "comment",
                    }
                )

        return comments

    def _extract_generic_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract import-like patterns."""
        imports = []
        patterns = [
            r"^\s*import\s+(.+)$",
            r'^\s*require\s*\([\'"]([^\'"]+)[\'"]\)',
            r'^\s*#include\s*[<"]([^>"]+)[>"]',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(
                    {
                        "module": match.group(1).strip(),
                        "line": content[: match.start()].count("\n") + 1,
                        "statement": match.group(0).strip(),
                    }
                )

        return imports

    def _calculate_generic_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate basic complexity metrics."""
        lines = content.splitlines()

        # Count basic constructs
        conditions = len(
            re.findall(r"\b(?:if|elif|else|case|when)\b", content, re.IGNORECASE)
        )
        loops = len(
            re.findall(r"\b(?:for|while|do|repeat|loop)\b", content, re.IGNORECASE)
        )
        functions = len(
            re.findall(r"\b(?:function|def|fn|proc|sub)\b", content, re.IGNORECASE)
        )

        return {
            "total_lines": len(lines),
            "code_lines": len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith(("#", "//", "/*"))
                ]
            ),
            "estimated_complexity": 1 + conditions + loops,
            "functions": functions,
            "conditions": conditions,
            "loops": loops,
        }


# Global registry instance
language_registry = LanguageParserRegistry()
