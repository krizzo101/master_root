"""Dynamic rule execution engine for project compliance checking.

This module provides the RuleEngine class that can execute different types of rules
(regex, AST, import analysis, etc.) dynamically based on rule definitions.
"""

import ast
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)
from src.tools.code_generation.o3_code_generator.rule_parser import (
    BrokenImport,
    Rule,
    RuleConfig,
)


class RuleEngine:
    """Executes compliance rules dynamically based on rule type."""

    def __init__(self) -> None:
        """Initialize the rule engine."""
        try:
            self.logger = get_logger()
        except RuntimeError:
            setup_logger(LogConfig())
            self.logger = get_logger()

        self.logger.log_info("Initialized RuleEngine")

    def check_regex_rule(self, rule: Rule, content: str) -> List[Tuple[int, str]]:
        """Check a regex-based rule against file content.

        Args:
            rule: The regex rule to check.
            content: File content to check.

        Returns:
            List of (line_number, matched_line) tuples for violations.
        """
        if not rule.pattern:
            return []

        violations = []
        lines = content.splitlines()

        for line_no, line in enumerate(lines, start=1):
            stripped_line = line.strip()

            # Skip comments, strings, and dictionary definitions
            if self._should_skip_line(stripped_line):
                continue

            # For import-related rules, only check actual import lines
            if rule.category == "imports" and not self._is_import_line(stripped_line):
                continue

            if re.search(rule.pattern, line):
                # Special handling for absolute imports - skip if already absolute
                if (
                    rule.id == "absolute_imports"
                    and "src.tools.code_generation.o3_code_generator" in line
                ):
                    continue

                violations.append((line_no, line.strip()))

        return violations

    def check_ast_rule(
        self, rule: Rule, content: str, file_path: Path
    ) -> List[Tuple[int, str]]:
        """Check an AST-based rule against file content.

        Args:
            rule: The AST rule to check.
            content: File content to check.
            file_path: Path to the file being checked.

        Returns:
            List of (line_number, issue_description) tuples for violations.
        """
        if not rule.check:
            return []

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            if rule.check == "no_syntax_errors":
                return [(e.lineno or 1, f"syntax_error: {e.msg}")]
            return []  # Can't check other AST rules if syntax is invalid

        # Dispatch to appropriate AST check method
        check_method = getattr(self, f"_check_{rule.check}", None)
        if not check_method:
            self.logger.log_error(None, f"Unknown AST check method: {rule.check}")
            return []

        return check_method(tree, content, file_path)

    def check_broken_imports(
        self, broken_imports: List[BrokenImport], content: str
    ) -> List[Tuple[int, str, str]]:
        """Check for broken import patterns.

        Args:
            broken_imports: List of broken import definitions.
            content: File content to check.

        Returns:
            List of (line_number, pattern, replacement) tuples for violations.
        """
        violations = []
        lines = content.splitlines()

        for line_no, line in enumerate(lines, start=1):
            stripped_line = line.strip()

            # Skip comments, strings, and dictionary definitions
            if self._should_skip_line(stripped_line):
                continue

            # Only check actual import lines
            if not self._is_import_line(stripped_line):
                continue

            for broken_import in broken_imports:
                if broken_import.pattern in line:
                    violations.append(
                        (line_no, broken_import.pattern, broken_import.replacement)
                    )

        return violations

    def _should_skip_line(self, line: str) -> bool:
        """Determine if a line should be skipped during rule checking.

        Args:
            line: Stripped line content.

        Returns:
            True if line should be skipped.
        """
        return (
            line.startswith("#")
            or line.startswith('"""')
            or line.startswith("'''")
            # Only skip dictionary-like entries, not all lines with quotes and colons
            or ('"' in line and ":" in line and line.strip().endswith(","))
            or ("'" in line and ":" in line and line.strip().endswith(","))
        )

    def _is_import_line(self, line: str) -> bool:
        """Check if a line is an import statement.

        Args:
            line: Stripped line content.

        Returns:
            True if line is an import statement.
        """
        return line.startswith("from ") or line.startswith("import ")

    # AST check methods
    def _check_has_module_docstring(
        self, tree: ast.AST, content: str, file_path: Path
    ) -> List[Tuple[int, str]]:
        """Check if module has a docstring."""
        if not tree.body:
            return [(1, "missing_module_docstring")]

        first_stmt = tree.body[0]
        if not isinstance(first_stmt, ast.Expr) or not isinstance(
            first_stmt.value, ast.Constant
        ):
            return [(1, "missing_module_docstring")]

        if not isinstance(first_stmt.value.value, str):
            return [(1, "missing_module_docstring")]

        return []

    def _check_class_has_logger_init(
        self, tree: ast.AST, content: str, file_path: Path
    ) -> List[Tuple[int, str]]:
        """Check if classes initialize logger in __init__."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not self._class_has_logger_init(node):
                    violations.append((node.lineno, "missing_class_logger"))

        return violations

    def _check_has_logger_setup(
        self, tree: ast.AST, content: str, file_path: Path
    ) -> List[Tuple[int, str]]:
        """Check if main script has logger setup.

        Only applies to actual main scripts, identified by:
        1. Contains 'if __name__ == "__main__":' block
        2. Has a main() function that's called
        3. Is named 'main.py' or ends with '_main.py'
        """
        # Check if this is actually a main script
        if not self._is_main_script(tree, content, file_path):
            return []  # Skip non-main scripts

        # For main scripts, check if they have logger setup
        if "setup_logger(LogConfig())" not in content:
            return [(1, "missing_logger_setup")]
        return []

    def _is_main_script(self, tree: ast.AST, content: str, file_path: Path) -> bool:
        """Determine if a file is a main script."""
        # Check filename patterns
        filename = file_path.name
        if filename == "main.py" or filename.endswith("_main.py"):
            return True

        # Check for if __name__ == "__main__": pattern
        if (
            'if __name__ == "__main__":' in content
            or "if __name__ == '__main__':" in content
        ):
            return True

        # Check for main() function being called at module level
        has_main_function = False
        calls_main_function = False

        for node in ast.walk(tree):
            # Check for main() function definition
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                has_main_function = True

            # Check for main() function call at module level
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "main":
                    calls_main_function = True

        return has_main_function and calls_main_function

    def _check_no_syntax_errors(
        self, tree: ast.AST, content: str, file_path: Path
    ) -> List[Tuple[int, str]]:
        """Check for syntax errors (already handled in check_ast_rule)."""
        return []  # If we got here, syntax is valid

    def _class_has_logger_init(self, class_node: ast.ClassDef) -> bool:
        """Check if a class initializes logger in __init__."""
        for node in ast.walk(class_node):
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if (
                                isinstance(target, ast.Attribute)
                                and isinstance(target.value, ast.Name)
                                and target.value.id == "self"
                                and target.attr == "logger"
                            ):
                                return True
        return False


class RuleExecutor:
    """High-level rule execution coordinator."""

    def __init__(self, rule_config: RuleConfig) -> None:
        """Initialize with rule configuration.

        Args:
            rule_config: Parsed rule configuration.
        """
        try:
            self.logger = get_logger()
        except RuntimeError:
            setup_logger(LogConfig())
            self.logger = get_logger()

        self.rule_config = rule_config
        self.engine = RuleEngine()
        self.logger.log_info(
            f"Initialized RuleExecutor with {len(rule_config.rules)} rules"
        )

    def check_file(self, file_path: Path) -> Dict[str, Any]:
        """Check a file against all rules.

        Args:
            file_path: Path to file to check.

        Returns:
            Dictionary containing all violations found.
        """
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": f"Could not read file: {e}"}

        violations = {"broken_imports": [], "rule_violations": [], "ast_issues": []}

        # Check broken imports
        broken_import_violations = self.engine.check_broken_imports(
            self.rule_config.broken_imports, content
        )
        for line_no, pattern, replacement in broken_import_violations:
            violations["broken_imports"].append(
                {"line": line_no, "pattern": pattern, "replacement": replacement}
            )

        # Check regex rules
        regex_rules = [r for r in self.rule_config.rules if r.type == "regex"]
        for rule in regex_rules:
            rule_violations = self.engine.check_regex_rule(rule, content)
            for line_no, matched_line in rule_violations:
                violations["rule_violations"].append(
                    {
                        "line": line_no,
                        "rule": rule.id,
                        "message": rule.message,
                        "severity": rule.severity,
                        "matched_line": matched_line,
                    }
                )

        # Check AST rules
        ast_rules = [r for r in self.rule_config.rules if r.type == "ast"]
        for rule in ast_rules:
            ast_violations = self.engine.check_ast_rule(rule, content, file_path)
            for line_no, issue in ast_violations:
                violations["ast_issues"].append(
                    {
                        "line": line_no,
                        "type": issue,
                        "rule": rule.id,
                        "message": rule.message,
                        "severity": rule.severity,
                    }
                )

        return violations


if __name__ == "__main__":
    # Test the rule engine
    from src.tools.code_generation.o3_code_generator.rule_parser import RuleParser

    setup_logger(LogConfig())

    # Parse rules
    parser = RuleParser()
    config = parser.parse_rules()

    # Create executor
    executor = RuleExecutor(config)

    # Test on a sample file
    test_file = Path("src/tools/code_generation/o3_code_generator/main.py")
    if test_file.exists():
        print(f"🔍 Testing rules on {test_file}")
        violations = executor.check_file(test_file)

        print("📊 Results:")
        print(f"   - Broken imports: {len(violations['broken_imports'])}")
        print(f"   - Rule violations: {len(violations['rule_violations'])}")
        print(f"   - AST issues: {len(violations['ast_issues'])}")

        if violations["rule_violations"]:
            print("\n⚠️  Rule violations:")
            for v in violations["rule_violations"][:3]:  # Show first 3
                print(f"   Line {v['line']}: {v['rule']} - {v['message']}")

        if violations["ast_issues"]:
            print("\n🔍 AST issues:")
            for v in violations["ast_issues"][:3]:  # Show first 3
                print(f"   Line {v['line']}: {v['type']} - {v['message']}")
    else:
        print(f"❌ Test file not found: {test_file}")
