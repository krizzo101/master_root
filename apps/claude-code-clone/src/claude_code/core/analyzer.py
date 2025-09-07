"""Code analyzer for Claude Code Clone."""

import logging
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import ast
import re

from opsvi_foundation import BaseComponent, ComponentError
from ..config import ClaudeCodeConfig

logger = logging.getLogger(__name__)


class CodeAnalyzerError(ComponentError):
    """Error in code analyzer operations."""

    pass


class CodeAnalyzer(BaseComponent):
    """Code analyzer for static analysis and metrics."""

    def __init__(self, config: ClaudeCodeConfig):
        """Initialize the code analyzer."""
        super().__init__(name="CodeAnalyzer")
        self.config = config
        self.working_directory = Path(config.working_directory).resolve()

        logger.info(f"Initialized code analyzer in {self.working_directory}")

    async def _initialize_impl(self) -> None:
        """Initialize the code analyzer."""
        logger.info("Code analyzer initialized")

    async def _shutdown_impl(self) -> None:
        """Shutdown the code analyzer."""
        logger.info("Code analyzer shutdown")

    async def _health_check_impl(self) -> bool:
        """Check if the code analyzer is healthy."""
        try:
            return self.working_directory.exists()
        except Exception as e:
            logger.error(f"Code analyzer health check failed: {e}")
            return False

    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for metrics and issues."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Collect metrics
            metrics = {
                "lines_of_code": len(content.splitlines()),
                "functions": [],
                "classes": [],
                "imports": [],
                "complexity": 0,
                "issues": [],
            }

            # Analyze AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics["functions"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "args": len(node.args.args),
                            "complexity": self._calculate_complexity(node),
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    metrics["classes"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "methods": len(
                                [n for n in node.body if isinstance(n, ast.FunctionDef)]
                            ),
                        }
                    )
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            metrics["imports"].append(alias.name)
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            metrics["imports"].append(f"{module}.{alias.name}")

            # Calculate overall complexity
            metrics["complexity"] = sum(
                func["complexity"] for func in metrics["functions"]
            )

            # Check for common issues
            metrics["issues"] = self._check_python_issues(content)

            return metrics

        except Exception as e:
            logger.error(f"Failed to analyze Python file {file_path}: {e}")
            raise CodeAnalyzerError(f"Python file analysis failed: {e}") from e

    def analyze_javascript_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a JavaScript file for metrics and issues."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            metrics = {
                "lines_of_code": len(content.splitlines()),
                "functions": [],
                "classes": [],
                "imports": [],
                "complexity": 0,
                "issues": [],
            }

            # Find functions (basic regex approach)
            function_pattern = r"function\s+(\w+)\s*\([^)]*\)\s*\{"
            for match in re.finditer(function_pattern, content):
                metrics["functions"].append(
                    {
                        "name": match.group(1),
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

            # Find arrow functions
            arrow_pattern = r"(\w+)\s*=\s*\([^)]*\)\s*=>"
            for match in re.finditer(arrow_pattern, content):
                metrics["functions"].append(
                    {
                        "name": match.group(1),
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

            # Find classes
            class_pattern = r"class\s+(\w+)"
            for match in re.finditer(class_pattern, content):
                metrics["classes"].append(
                    {
                        "name": match.group(1),
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

            # Find imports
            import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
            for match in re.finditer(import_pattern, content):
                metrics["imports"].append(match.group(1))

            # Check for common issues
            metrics["issues"] = self._check_javascript_issues(content)

            return metrics

        except Exception as e:
            logger.error(f"Failed to analyze JavaScript file {file_path}: {e}")
            raise CodeAnalyzerError(f"JavaScript file analysis failed: {e}") from e

    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze the overall project structure."""
        try:
            structure = {
                "total_files": 0,
                "file_types": {},
                "directories": [],
                "largest_files": [],
                "complexity_summary": {
                    "total_functions": 0,
                    "total_classes": 0,
                    "total_complexity": 0,
                },
            }

            # Walk through project directory
            for file_path in self.working_directory.rglob("*"):
                if file_path.is_file() and self._is_allowed_file(file_path):
                    structure["total_files"] += 1

                    # Count file types
                    ext = file_path.suffix or "no_extension"
                    structure["file_types"][ext] = (
                        structure["file_types"].get(ext, 0) + 1
                    )

                    # Track largest files
                    size = file_path.stat().st_size
                    structure["largest_files"].append(
                        {
                            "path": str(file_path.relative_to(self.working_directory)),
                            "size": size,
                        }
                    )

                    # Analyze specific file types
                    if file_path.suffix == ".py":
                        try:
                            metrics = self.analyze_python_file(file_path)
                            structure["complexity_summary"]["total_functions"] += len(
                                metrics["functions"]
                            )
                            structure["complexity_summary"]["total_classes"] += len(
                                metrics["classes"]
                            )
                            structure["complexity_summary"][
                                "total_complexity"
                            ] += metrics["complexity"]
                        except Exception as e:
                            logger.warning(f"Failed to analyze {file_path}: {e}")

                    elif file_path.suffix in [".js", ".ts", ".jsx", ".tsx"]:
                        try:
                            metrics = self.analyze_javascript_file(file_path)
                            structure["complexity_summary"]["total_functions"] += len(
                                metrics["functions"]
                            )
                            structure["complexity_summary"]["total_classes"] += len(
                                metrics["classes"]
                            )
                        except Exception as e:
                            logger.warning(f"Failed to analyze {file_path}: {e}")

                elif file_path.is_dir():
                    structure["directories"].append(
                        str(file_path.relative_to(self.working_directory))
                    )

            # Sort largest files by size
            structure["largest_files"].sort(key=lambda x: x["size"], reverse=True)
            structure["largest_files"] = structure["largest_files"][:10]  # Top 10

            return structure

        except Exception as e:
            logger.error(f"Failed to analyze project structure: {e}")
            raise CodeAnalyzerError(f"Project structure analysis failed: {e}") from e

    def find_duplicate_code(self, file_patterns: List[str]) -> Dict[str, List[str]]:
        """Find potential duplicate code blocks."""
        try:
            duplicates = {}
            file_contents = {}

            # Read all matching files
            for pattern in file_patterns:
                for file_path in self.working_directory.glob(pattern):
                    if file_path.is_file() and self._is_allowed_file(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            file_contents[str(file_path)] = content

            # Find similar code blocks (simplified approach)
            for file1, content1 in file_contents.items():
                for file2, content2 in file_contents.items():
                    if file1 >= file2:  # Avoid duplicate comparisons
                        continue

                    # Find common lines
                    lines1 = set(content1.splitlines())
                    lines2 = set(content2.splitlines())
                    common_lines = lines1.intersection(lines2)

                    if len(common_lines) > 5:  # Threshold for similarity
                        key = f"{file1} <-> {file2}"
                        duplicates[key] = list(common_lines)[:10]  # Limit output

            return duplicates

        except Exception as e:
            logger.error(f"Failed to find duplicate code: {e}")
            raise CodeAnalyzerError(f"Duplicate code detection failed: {e}") from e

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _check_python_issues(self, content: str) -> List[str]:
        """Check for common Python issues."""
        issues = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            # Check for long lines
            if len(line) > 88:
                issues.append(f"Line {i}: Line too long ({len(line)} characters)")

            # Check for TODO/FIXME comments
            if re.search(r"#\s*(TODO|FIXME|HACK)", line, re.IGNORECASE):
                issues.append(f"Line {i}: {line.strip()}")

            # Check for print statements (in production code)
            if re.search(r"\bprint\s*\(", line):
                issues.append(f"Line {i}: Print statement found")

            # Check for bare except
            if re.search(r"except\s*:", line):
                issues.append(f"Line {i}: Bare except clause")

        return issues

    def _check_javascript_issues(self, content: str) -> List[str]:
        """Check for common JavaScript issues."""
        issues = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            # Check for console.log
            if re.search(r"console\.log\s*\(", line):
                issues.append(f"Line {i}: Console.log statement found")

            # Check for var declarations
            if re.search(r"\bvar\s+", line):
                issues.append(f"Line {i}: Use let/const instead of var")

            # Check for == instead of ===
            if re.search(r"==\s*[^=]", line):
                issues.append(f"Line {i}: Use === instead of ==")

            # Check for TODO/FIXME comments
            if re.search(r"//\s*(TODO|FIXME|HACK)", line, re.IGNORECASE):
                issues.append(f"Line {i}: {line.strip()}")

        return issues

    def _is_allowed_file(self, file_path: Path) -> bool:
        """Check if file is allowed based on configuration."""
        if not self.config.enable_file_operations:
            return False

        if file_path.suffix not in self.config.allowed_file_extensions:
            return False

        if file_path.stat().st_size > self.config.max_file_size:
            return False

        return True
