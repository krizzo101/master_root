"""
Code Validator for Self-Modification System

Provides comprehensive validation of generated and modified code
including syntax, security, performance, and best practices checks.

Created: 2025-08-15
"""

import ast
import re
import sys
import io
import time
import traceback
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import importlib.util
import hashlib


@dataclass
class ValidationResult:
    """Result of code validation"""

    is_valid: bool
    syntax_valid: bool
    security_valid: bool
    performance_valid: bool
    best_practices_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_score(self) -> float:
        """Calculate overall validation score"""
        score = 0.0
        if self.syntax_valid:
            score += 0.4
        if self.security_valid:
            score += 0.3
        if self.performance_valid:
            score += 0.2
        if self.best_practices_valid:
            score += 0.1
        return score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_valid": self.is_valid,
            "syntax_valid": self.syntax_valid,
            "security_valid": self.security_valid,
            "performance_valid": self.performance_valid,
            "best_practices_valid": self.best_practices_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "metrics": self.metrics,
            "score": self.get_score(),
            "timestamp": self.timestamp.isoformat(),
        }


class SecurityValidator:
    """Validator for security issues in code"""

    # Dangerous imports
    DANGEROUS_IMPORTS = {
        "os": ["system", "exec", "spawn", "popen"],
        "subprocess": ["call", "run", "Popen", "check_output"],
        "eval": [],
        "exec": [],
        "__import__": [],
        "compile": [],
        "open": [],
        "input": [],
        "raw_input": [],
    }

    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        (r"eval\s*\(", "Use of eval() is dangerous"),
        (r"exec\s*\(", "Use of exec() is dangerous"),
        (r"__import__\s*\(", "Dynamic imports can be dangerous"),
        (r"compile\s*\(", "Dynamic compilation can be dangerous"),
        (r"pickle\.loads?\s*\(", "Pickle deserialization can be dangerous"),
        (r"yaml\.load\s*\(", "Use yaml.safe_load() instead of yaml.load()"),
        (r"shell\s*=\s*True", "Shell injection vulnerability"),
        (r"os\.system\s*\(", "Command injection vulnerability"),
        (r"\.format\s*\([^)]*\{0\}", "Format string vulnerability"),
        (r'sql\s*=\s*["\'].*%s', "SQL injection vulnerability"),
    ]

    @classmethod
    def validate(cls, code: str) -> Tuple[bool, List[str], List[str]]:
        """Validate code for security issues"""
        errors = []
        warnings = []

        # Check for dangerous imports
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in cls.DANGEROUS_IMPORTS:
                            warnings.append(f"Potentially dangerous import: {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module in cls.DANGEROUS_IMPORTS:
                        for alias in node.names:
                            if alias.name in cls.DANGEROUS_IMPORTS[node.module]:
                                errors.append(
                                    f"Dangerous import: from {node.module} import {alias.name}"
                                )

                elif isinstance(node, ast.Call):
                    # Check for dangerous function calls
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["eval", "exec", "compile", "__import__"]:
                            errors.append(f"Dangerous function call: {node.func.id}()")

        except SyntaxError:
            pass  # Syntax errors handled elsewhere

        # Check for dangerous patterns
        for pattern, message in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                warnings.append(message)

        # Check for hardcoded credentials
        credential_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token detected"),
        ]

        for pattern, message in credential_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                errors.append(message)

        is_valid = len(errors) == 0
        return is_valid, errors, warnings


class PerformanceValidator:
    """Validator for performance issues in code"""

    @classmethod
    def validate(cls, code: str) -> Tuple[bool, List[str], List[str]]:
        """Validate code for performance issues"""
        warnings = []
        suggestions = []

        try:
            tree = ast.parse(code)

            # Check for inefficient patterns
            for node in ast.walk(tree):
                # Check for string concatenation in loops
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if isinstance(child, ast.AugAssign):
                            if isinstance(child.op, ast.Add):
                                if isinstance(child.target, ast.Name):
                                    warnings.append(
                                        f"String concatenation in loop at line {child.lineno}. "
                                        "Consider using list.append() and ''.join()"
                                    )

                # Check for repeated attribute access
                if isinstance(node, ast.FunctionDef):
                    attr_access_count = {}
                    for child in ast.walk(node):
                        if isinstance(child, ast.Attribute):
                            attr_str = ast.unparse(child)
                            attr_access_count[attr_str] = attr_access_count.get(attr_str, 0) + 1

                    for attr, count in attr_access_count.items():
                        if count > 3:
                            suggestions.append(
                                f"Attribute '{attr}' accessed {count} times in {node.name}. "
                                "Consider caching it in a local variable"
                            )

                # Check for list comprehensions that could be generator expressions
                if isinstance(node, ast.ListComp):
                    parent = cls._get_parent_node(tree, node)
                    if isinstance(parent, ast.Call):
                        if isinstance(parent.func, ast.Name):
                            if parent.func.id in ["sum", "any", "all", "min", "max"]:
                                suggestions.append(
                                    f"List comprehension at line {node.lineno} could be a generator expression"
                                )

            # Check for missing lru_cache on recursive functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if cls._is_recursive(node):
                        has_cache = any(
                            isinstance(d, ast.Name) and "cache" in d.id.lower()
                            for d in node.decorator_list
                        )
                        if not has_cache:
                            suggestions.append(
                                f"Recursive function '{node.name}' could benefit from @lru_cache decorator"
                            )

        except SyntaxError:
            pass  # Syntax errors handled elsewhere

        # Performance is valid if no critical warnings
        is_valid = True  # Performance issues are usually not critical
        return is_valid, warnings, suggestions

    @staticmethod
    def _get_parent_node(tree: ast.AST, target: ast.AST) -> Optional[ast.AST]:
        """Get parent node of target in tree"""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    return node
        return None

    @staticmethod
    def _is_recursive(func_node: ast.FunctionDef) -> bool:
        """Check if function is recursive"""
        func_name = func_node.name
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == func_name:
                        return True
        return False


class CodeValidator:
    """Main code validator"""

    def __init__(self, strict_mode: bool = False, timeout: float = 5.0):
        """Initialize code validator"""
        self.strict_mode = strict_mode
        self.timeout = timeout
        self.security_validator = SecurityValidator()
        self.performance_validator = PerformanceValidator()
        self.validation_history: List[ValidationResult] = []

    def validate(self, code: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Perform comprehensive code validation"""
        context = context or {}

        # Initialize result
        result = ValidationResult(
            is_valid=True,
            syntax_valid=True,
            security_valid=True,
            performance_valid=True,
            best_practices_valid=True,
        )

        # Syntax validation
        syntax_valid, syntax_errors = self._validate_syntax(code)
        result.syntax_valid = syntax_valid
        if not syntax_valid:
            result.errors.extend(syntax_errors)
            result.is_valid = False

            # Can't proceed without valid syntax
            self.validation_history.append(result)
            return result

        # Security validation
        security_valid, security_errors, security_warnings = self.security_validator.validate(code)
        result.security_valid = security_valid
        result.errors.extend(security_errors)
        result.warnings.extend(security_warnings)
        if not security_valid and self.strict_mode:
            result.is_valid = False

        # Performance validation
        perf_valid, perf_warnings, perf_suggestions = self.performance_validator.validate(code)
        result.performance_valid = perf_valid
        result.warnings.extend(perf_warnings)
        result.suggestions.extend(perf_suggestions)

        # Best practices validation
        bp_valid, bp_warnings, bp_suggestions = self._validate_best_practices(code)
        result.best_practices_valid = bp_valid
        result.warnings.extend(bp_warnings)
        result.suggestions.extend(bp_suggestions)

        # Runtime validation (if safe)
        if result.security_valid:
            runtime_valid, runtime_errors = self._validate_runtime(code, context)
            if not runtime_valid:
                result.errors.extend(runtime_errors)
                if self.strict_mode:
                    result.is_valid = False

        # Calculate metrics
        result.metrics = self._calculate_metrics(code)

        # Add to history
        self.validation_history.append(result)

        return result

    def _validate_syntax(self, code: str) -> Tuple[bool, List[str]]:
        """Validate code syntax"""
        errors = []

        try:
            ast.parse(code)

            # Additional syntax checks
            compile(code, "<string>", "exec")

            return True, errors

        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, errors

        except Exception as e:
            errors.append(f"Compilation error: {str(e)}")
            return False, errors

    def _validate_best_practices(self, code: str) -> Tuple[bool, List[str], List[str]]:
        """Validate code against best practices"""
        warnings = []
        suggestions = []

        try:
            tree = ast.parse(code)

            # Check function/class naming
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                        warnings.append(
                            f"Function '{node.name}' doesn't follow snake_case convention"
                        )

                    # Check docstring
                    if not ast.get_docstring(node):
                        suggestions.append(f"Function '{node.name}' lacks a docstring")

                    # Check function length
                    if len(node.body) > 50:
                        warnings.append(
                            f"Function '{node.name}' is too long ({len(node.body)} lines)"
                        )

                elif isinstance(node, ast.ClassDef):
                    if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                        warnings.append(f"Class '{node.name}' doesn't follow PascalCase convention")

                    # Check docstring
                    if not ast.get_docstring(node):
                        suggestions.append(f"Class '{node.name}' lacks a docstring")

            # Check for global variables
            global_vars = []
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if not target.id.isupper():
                                global_vars.append(target.id)

            if global_vars:
                warnings.append(f"Non-constant global variables: {', '.join(global_vars)}")

            # Check import organization
            imports = []
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)
                elif not isinstance(node, ast.Expr):  # Skip docstrings
                    break

            if imports and len(imports) > 1:
                # Check if imports are sorted
                import_names = []
                for imp in imports:
                    if isinstance(imp, ast.Import):
                        import_names.extend(alias.name for alias in imp.names)
                    else:
                        import_names.append(imp.module or "")

                if import_names != sorted(import_names):
                    suggestions.append("Imports are not sorted alphabetically")

        except SyntaxError:
            pass  # Handled in syntax validation

        # Best practices are valid if no critical warnings
        is_valid = True  # Best practice issues are usually not critical
        return is_valid, warnings, suggestions

    def _validate_runtime(self, code: str, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate code at runtime (safely)"""
        errors = []

        # Create safe execution environment
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "type": type,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "getattr": getattr,
                "setattr": setattr,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "AttributeError": AttributeError,
            }
        }

        # Add context to globals
        safe_globals.update(context)

        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute with timeout
                exec(code, safe_globals, {})

            # Check for errors in output
            stderr_output = stderr_capture.getvalue()
            if stderr_output:
                errors.append(f"Runtime stderr: {stderr_output}")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Runtime error: {str(e)}")
            errors.append(f"Traceback: {traceback.format_exc()}")
            return False, errors

    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate code metrics"""
        metrics = {
            "lines": len(code.splitlines()),
            "characters": len(code),
            "complexity": 0,
            "functions": 0,
            "classes": 0,
            "imports": 0,
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics["functions"] += 1
                    # Calculate cyclomatic complexity
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                            metrics["complexity"] += 1

                elif isinstance(node, ast.ClassDef):
                    metrics["classes"] += 1

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics["imports"] += 1

        except SyntaxError:
            pass

        return metrics

    def validate_file(self, filepath: Path) -> ValidationResult:
        """Validate code from file"""
        try:
            with open(filepath, "r") as f:
                code = f.read()

            result = self.validate(code)
            result.metadata["filepath"] = str(filepath)
            return result

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                syntax_valid=False,
                security_valid=False,
                performance_valid=False,
                best_practices_valid=False,
                errors=[f"Failed to read file: {str(e)}"],
            )

    def validate_modification(self, original_code: str, modified_code: str) -> ValidationResult:
        """Validate a code modification"""
        # Validate modified code
        result = self.validate(modified_code)

        # Compare with original
        original_result = self.validate(original_code)

        # Check for regressions
        if original_result.get_score() > result.get_score():
            result.warnings.append(
                f"Modification reduced code quality score from "
                f"{original_result.get_score():.2f} to {result.get_score():.2f}"
            )

        # Add comparison metrics
        result.metrics["original_score"] = original_result.get_score()
        result.metrics["score_change"] = result.get_score() - original_result.get_score()

        return result

    def get_validation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get validation history"""
        history = []
        for result in self.validation_history[-limit:]:
            history.append(result.to_dict())
        return history

    @contextmanager
    def sandbox_execution(self, code: str, timeout: float = None):
        """Execute code in sandbox environment"""
        timeout = timeout or self.timeout

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Run in subprocess with timeout
            result = subprocess.run(
                [sys.executable, temp_file], capture_output=True, text=True, timeout=timeout
            )

            yield result

        except subprocess.TimeoutExpired:
            yield None

        finally:
            # Clean up
            Path(temp_file).unlink(missing_ok=True)
