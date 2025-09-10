"""
Code context extraction utilities for chat analytics.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class CodeContextExtractor:
    """Extracts and analyzes code context from chat messages."""

    def __init__(self, project_root: str = "/home/opsvi/master_root"):
        self.project_root = Path(project_root)

        # Enhanced patterns for code extraction
        self.patterns = {
            "file_path": re.compile(
                r'(?:(?:^|\s)|["\'])([./]?(?:[\w\-]+/)*[\w\-]+\.(?:py|js|ts|tsx|jsx|md|json|yaml|yml|txt|sh|sql|html|css|xml|toml|ini|cfg|conf|env))(?:["\':\s]|$)',
                re.MULTILINE,
            ),
            "function_def": re.compile(
                r"(?:def|function|const|let|var|async\s+function)\s+(\w+)\s*(?:\(|=)",
                re.MULTILINE,
            ),
            "class_def": re.compile(
                r"(?:class|interface|struct|enum)\s+(\w+)(?:\s*(?:\([\w\s,]*\)|{|:))",
                re.MULTILINE,
            ),
            "import_stmt": re.compile(
                r'(?:import|from|require|use)\s+(?:[\w\s,{}]+\s+from\s+)?["\']?([\w\-./]+)["\']?',
                re.MULTILINE,
            ),
            "variable_def": re.compile(
                r"(?:const|let|var|self\.|this\.)\s*(\w+)\s*=", re.MULTILINE
            ),
            "method_call": re.compile(r"(\w+)\s*\.\s*(\w+)\s*\(", re.MULTILINE),
            "decorator": re.compile(r"@(\w+)(?:\(.*?\))?", re.MULTILINE),
            "sql_query": re.compile(
                r"(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+.*?(?:FROM|INTO|TABLE|INDEX)\s+(\w+)",
                re.IGNORECASE | re.MULTILINE,
            ),
            "api_endpoint": re.compile(
                r'(?:@app\.(?:get|post|put|delete|patch)|router\.(?:get|post|put|delete|patch))\s*\(["\']([^"\']+)["\']',
                re.MULTILINE,
            ),
            "test_function": re.compile(
                r'(?:def\s+test_|it\(|describe\(|test\()["\']?([\w\s]+)', re.MULTILINE
            ),
            "error_pattern": re.compile(
                r"(?:Error|Exception|Traceback|Failed|FAILED).*?:\s*(.*?)(?:\n|$)",
                re.MULTILINE,
            ),
            "todo_comment": re.compile(
                r"(?:#|//|/\*)\s*(?:TODO|FIXME|HACK|NOTE|XXX):\s*(.*?)(?:\n|\*/|$)",
                re.MULTILINE,
            ),
            "config_key": re.compile(
                r'(?:os\.environ\[|process\.env\.|ENV\[)["\'](\w+)["\']', re.MULTILINE
            ),
            "url_pattern": re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.MULTILINE),
            "git_ref": re.compile(
                r"(?:commit|branch|tag|ref)(?:\s+|:\s*)([a-f0-9]{7,40}|\w+(?:[-/]\w+)*)",
                re.IGNORECASE | re.MULTILINE,
            ),
        }

        # Code block extraction
        self.code_block_pattern = re.compile(r"```(?:(\w+)\n)?(.*?)```", re.DOTALL)

        # Line reference pattern (file:line_number)
        self.line_ref_pattern = re.compile(
            r"([\w\-./]+\.(?:py|js|ts|tsx|jsx)):(\d+)", re.MULTILINE
        )

        # Tool usage patterns
        self.tool_patterns = {
            "read": re.compile(r'Read tool.*?file_path["\']:\s*["\']([^"\']+)["\']'),
            "edit": re.compile(r'Edit tool.*?file_path["\']:\s*["\']([^"\']+)["\']'),
            "write": re.compile(r'Write tool.*?file_path["\']:\s*["\']([^"\']+)["\']'),
            "grep": re.compile(r'Grep tool.*?path["\']:\s*["\']([^"\']+)["\']'),
            "bash": re.compile(r"Bash.*?(?:cd\s+([^\s;]+)|python\s+([^\s;]+)\.py)"),
        }

    def extract_context(self, message: str) -> Dict[str, Any]:
        """
        Extract comprehensive code context from a message.

        Args:
            message: The chat message content

        Returns:
            Dictionary containing extracted code context
        """
        context = {
            "files": self._extract_file_paths(message),
            "symbols": {
                "functions": self._extract_functions(message),
                "classes": self._extract_classes(message),
                "variables": self._extract_variables(message),
                "methods": self._extract_methods(message),
                "decorators": self._extract_decorators(message),
            },
            "imports": self._extract_imports(message),
            "code_blocks": self._extract_code_blocks(message),
            "line_references": self._extract_line_references(message),
            "sql_tables": self._extract_sql_tables(message),
            "api_endpoints": self._extract_api_endpoints(message),
            "tests": self._extract_tests(message),
            "errors": self._extract_errors(message),
            "todos": self._extract_todos(message),
            "config_keys": self._extract_config_keys(message),
            "urls": self._extract_urls(message),
            "git_refs": self._extract_git_refs(message),
            "tool_usage": self._extract_tool_usage(message),
        }

        # Add metadata
        context["metadata"] = {
            "total_symbols": sum(len(v) for v in context["symbols"].values()),
            "has_code_blocks": len(context["code_blocks"]) > 0,
            "has_errors": len(context["errors"]) > 0,
            "has_tests": len(context["tests"]) > 0,
            "content_hash": self._hash_content(message),
        }

        return context

    def _extract_file_paths(self, message: str) -> List[Dict[str, str]]:
        """Extract file paths with context."""
        paths = []
        seen = set()

        for match in self.patterns["file_path"].finditer(message):
            path = match.group(1)
            if path not in seen:
                seen.add(path)
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(message), match.end() + 50)
                context = message[start:end].strip()

                # Determine if it's absolute or relative
                is_absolute = path.startswith("/")
                full_path = path if is_absolute else str(self.project_root / path)

                paths.append(
                    {
                        "path": path,
                        "full_path": full_path,
                        "exists": Path(full_path).exists(),
                        "context": context,
                        "position": match.start(),
                    }
                )

        return sorted(paths, key=lambda x: x["position"])

    def _extract_functions(self, message: str) -> List[str]:
        """Extract function names."""
        return list(set(self.patterns["function_def"].findall(message)))

    def _extract_classes(self, message: str) -> List[str]:
        """Extract class names."""
        return list(set(self.patterns["class_def"].findall(message)))

    def _extract_variables(self, message: str) -> List[str]:
        """Extract variable names."""
        return list(set(self.patterns["variable_def"].findall(message)))

    def _extract_methods(self, message: str) -> List[Dict[str, str]]:
        """Extract method calls."""
        methods = []
        seen = set()

        for match in self.patterns["method_call"].finditer(message):
            obj = match.group(1)
            method = match.group(2)
            key = f"{obj}.{method}"

            if key not in seen:
                seen.add(key)
                methods.append({"object": obj, "method": method, "full": key})

        return methods

    def _extract_decorators(self, message: str) -> List[str]:
        """Extract decorator names."""
        return list(set(self.patterns["decorator"].findall(message)))

    def _extract_imports(self, message: str) -> List[str]:
        """Extract import statements."""
        imports = []
        for match in self.patterns["import_stmt"].finditer(message):
            import_str = match.group(1)
            if import_str and not import_str.startswith("http"):
                imports.append(import_str)
        return list(set(imports))

    def _extract_code_blocks(self, message: str) -> List[Dict[str, Any]]:
        """Extract code blocks with language hints."""
        blocks = []

        for match in self.code_block_pattern.finditer(message):
            language = match.group(1) or "unknown"
            code = match.group(2).strip()

            if code:
                blocks.append(
                    {
                        "language": language,
                        "code": code,
                        "lines": len(code.splitlines()),
                        "hash": hashlib.md5(code.encode()).hexdigest()[:8],
                    }
                )

        return blocks

    def _extract_line_references(self, message: str) -> List[Dict[str, Any]]:
        """Extract file:line_number references."""
        refs = []

        for match in self.line_ref_pattern.finditer(message):
            refs.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "reference": match.group(0),
                }
            )

        return refs

    def _extract_sql_tables(self, message: str) -> List[str]:
        """Extract SQL table names."""
        return list(set(self.patterns["sql_query"].findall(message)))

    def _extract_api_endpoints(self, message: str) -> List[str]:
        """Extract API endpoint paths."""
        return list(set(self.patterns["api_endpoint"].findall(message)))

    def _extract_tests(self, message: str) -> List[str]:
        """Extract test function/description names."""
        tests = []
        for match in self.patterns["test_function"].finditer(message):
            test_name = match.group(1)
            if test_name:
                tests.append(test_name.strip())
        return list(set(tests))

    def _extract_errors(self, message: str) -> List[Dict[str, str]]:
        """Extract error messages and types."""
        errors = []
        seen = set()

        for match in self.patterns["error_pattern"].finditer(message):
            error_msg = match.group(0)
            error_detail = match.group(1) if match.lastindex else ""

            if error_msg not in seen:
                seen.add(error_msg)
                errors.append(
                    {
                        "message": error_msg.strip(),
                        "detail": error_detail.strip(),
                        "position": match.start(),
                    }
                )

        return errors

    def _extract_todos(self, message: str) -> List[str]:
        """Extract TODO/FIXME comments."""
        todos = []
        for match in self.patterns["todo_comment"].finditer(message):
            todo = match.group(1)
            if todo:
                todos.append(todo.strip())
        return todos

    def _extract_config_keys(self, message: str) -> List[str]:
        """Extract configuration/environment variable keys."""
        return list(set(self.patterns["config_key"].findall(message)))

    def _extract_urls(self, message: str) -> List[str]:
        """Extract URLs mentioned."""
        return list(set(self.patterns["url_pattern"].findall(message)))

    def _extract_git_refs(self, message: str) -> List[str]:
        """Extract git references (commits, branches, tags)."""
        refs = []
        for match in self.patterns["git_ref"].finditer(message):
            ref = match.group(1)
            if ref and len(ref) > 3:  # Avoid false positives
                refs.append(ref)
        return list(set(refs))

    def _extract_tool_usage(self, message: str) -> Dict[str, List[str]]:
        """Extract tool usage patterns."""
        usage = {}

        for tool_name, pattern in self.tool_patterns.items():
            matches = pattern.findall(message)
            if matches:
                # Flatten tuples if regex has multiple groups
                flattened = []
                for match in matches:
                    if isinstance(match, tuple):
                        flattened.extend([m for m in match if m])
                    else:
                        flattened.append(match)

                usage[tool_name] = list(set(flattened))

        return usage

    def _hash_content(self, content: str) -> str:
        """Generate a hash of the content for tracking."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def analyze_code_density(self, message: str) -> Dict[str, Any]:
        """
        Analyze the code density and technical depth of a message.

        Returns:
            Dictionary with density metrics
        """
        context = self.extract_context(message)
        total_length = len(message)

        # Calculate code block coverage
        code_chars = sum(len(block["code"]) for block in context["code_blocks"])
        code_percentage = (code_chars / total_length * 100) if total_length > 0 else 0

        # Count technical elements
        technical_elements = (
            len(context["files"])
            + context["metadata"]["total_symbols"]
            + len(context["imports"])
            + len(context["line_references"])
            + len(context["sql_tables"])
            + len(context["api_endpoints"])
        )

        return {
            "code_percentage": round(code_percentage, 2),
            "technical_elements": technical_elements,
            "code_blocks": len(context["code_blocks"]),
            "files_mentioned": len(context["files"]),
            "symbols_referenced": context["metadata"]["total_symbols"],
            "has_errors": context["metadata"]["has_errors"],
            "has_tests": context["metadata"]["has_tests"],
            "complexity_score": self._calculate_complexity_score(context),
        }

    def _calculate_complexity_score(self, context: Dict) -> int:
        """Calculate a complexity score based on extracted context."""
        score = 0

        # Weight different elements
        weights = {
            "files": 2,
            "functions": 3,
            "classes": 5,
            "methods": 2,
            "imports": 1,
            "errors": 4,
            "sql_tables": 3,
            "api_endpoints": 3,
            "tests": 2,
        }

        score += len(context["files"]) * weights["files"]
        score += len(context["symbols"]["functions"]) * weights["functions"]
        score += len(context["symbols"]["classes"]) * weights["classes"]
        score += len(context["symbols"]["methods"]) * weights["methods"]
        score += len(context["imports"]) * weights["imports"]
        score += len(context["errors"]) * weights["errors"]
        score += len(context["sql_tables"]) * weights["sql_tables"]
        score += len(context["api_endpoints"]) * weights["api_endpoints"]
        score += len(context["tests"]) * weights["tests"]

        # Bonus for code blocks
        score += len(context["code_blocks"]) * 10

        return score
