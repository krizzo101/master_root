"""
Alignment Scanner for O3 Code Generator

Scans the codebase to identify files that need auto-alignment based on:
- Broken imports (config.config_manager, etc.)
- Rule violations
- Directory structure mismatches
- Missing module docstrings and print statements
"""

import ast
import re
from pathlib import Path
from typing import Any

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)


class AlignmentScanner:
    """
    Scans the codebase to identify files that need auto-alignment.

    Attributes:
        logger: O3Logger instance for logging.
        base_path: Root path to start scanning from.
        ignore_dirs: Set of directory names to ignore.
        broken_imports: Mapping of broken import patterns to correct patterns.
        rule_violations: Mapping of rule violation names to regex patterns.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """
        Initialize the alignment scanner.

        Args:
            base_path: Optional base directory to scan. Defaults to project root.
        """
        # Initialize logger if not already set up
        try:
            self.logger = get_logger()
        except RuntimeError:
            # Logger not initialized, set it up for this instance
            setup_logger(LogConfig())
            self.logger = get_logger()

        self.base_path: Path = base_path or Path(
            "src/tools/code_generation/o3_code_generator"
        )
        self.ignore_dirs: set[str] = {
            "venv",
            ".venv",
            "env",
            ".env",
            "virtualenv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".git",
            ".svn",
            ".hg",
            ".vscode",
            ".idea",
            ".vs",
            ".sublime-project",
            ".sublime-workspace",
            "build",
            "dist",
            "*.egg-info",
            "*.egg",
            "node_modules",
            "npm-debug.log",
            ".DS_Store",
            "Thumbs.db",
            "archive",
            "backups",
            "temp",
            "tmp",
            "logs",
        }
        self.broken_imports: dict[str, str] = {
            # Only flag actual broken import patterns, not mentions in strings
            "from config.config_manager import": "from src.tools.code_generation.o3_code_generator.config.core.config_manager import",
            "from self_improvement.": "from src.tools.code_generation.o3_code_generator.config.self_improvement.",
            "from generated_files.": "from src.tools.code_generation.o3_code_generator.generated.generated_files.",
            # Flag non-absolute imports that should be absolute
            "from alignment_scanner import": "from src.tools.code_generation.o3_code_generator.alignment_scanner import",
            "from batch_auto_align import": "from src.tools.code_generation.o3_code_generator.batch_auto_align import",
        }
        self.rule_violations: dict[str, str] = {
            "relative_imports": r"^\s*from\s+\.+\w",  # Only actual relative imports
            "wrong_logger_import": r"^\s*from\s+logging\s+import",  # Only actual logging imports
            "print_statements": r"^\s*print\s*\(",  # Only actual print calls
            # Only flag non-absolute imports for project modules (not stdlib)
            "non_absolute_imports": r"^\s*from\s+(?!src\.|ast|pathlib|re|typing|json|concurrent|subprocess|sys|time|tempfile|os)[a-zA-Z_][a-zA-Z0-9_]*\s+import",
        }
        self.logger.log_info(f"Initialized AlignmentScanner for path: {self.base_path}")

    def _should_ignore_path(self, path: Path) -> bool:
        """
        Determine if a given path should be ignored.

        Args:
            path: Path to check.

        Returns:
            True if path is in ignore list; False otherwise.
        """
        return any(part in self.ignore_dirs for part in path.parts)

    def scan_codebase(self) -> dict[str, Any]:
        """
        Scan the entire codebase for alignment issues.

        Returns:
            A dictionary containing scan results.
        """
        self.logger.log_info("Starting codebase alignment scan...")
        all_python_files: list[Path] = [
            f for f in self.base_path.rglob("*.py") if f.is_file()
        ]
        python_files: list[Path] = [
            f for f in all_python_files if not self._should_ignore_path(f)
        ]
        self.logger.log_info(
            f"Found {len(all_python_files)} Python files, {len(python_files)} after filtering ignored directories"
        )
        scan_results: dict[str, Any] = {
            "total_files": len(python_files),
            "files_needing_alignment": [],
            "broken_imports": [],
            "rule_violations": [],
            "summary": {},
        }
        for file_path in python_files:
            file_issues: dict[str, Any] = self._scan_file(file_path)
            if file_issues.get("needs_alignment", False):
                scan_results["files_needing_alignment"].append(
                    {"file": str(file_path), "issues": file_issues}
                )
                if file_issues.get("broken_imports"):
                    scan_results["broken_imports"].append(str(file_path))
                else:
                    pass
                if file_issues.get("rule_violations"):
                    scan_results["rule_violations"].append(str(file_path))
                else:
                    pass
            else:
                pass
        else:
            pass
        total = len(python_files)
        needing = len(scan_results["files_needing_alignment"])
        broken = len(scan_results["broken_imports"])
        violations = len(scan_results["rule_violations"])
        alignment_percentage = (
            round((total - needing) / total * 100, 2) if total > 0 else 100.0
        )
        scan_results["summary"] = {
            "total_files": total,
            "files_needing_alignment": needing,
            "files_with_broken_imports": broken,
            "files_with_rule_violations": violations,
            "alignment_percentage": alignment_percentage,
        }
        self.logger.log_info(f"Scan complete: {needing} files need alignment")
        return scan_results

    def _scan_file(self, file_path: Path | str) -> dict[str, Any]:
        """
        Scan a single file for alignment issues.

        Args:
            file_path: Path to the Python file.

        Returns:
            A dictionary of issues found.
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            else:
                pass
            content = file_path.read_text(encoding="utf-8")
            issues: dict[str, Any] = {
                "needs_alignment": False,
                "broken_imports": [],
                "rule_violations": [],
                "ast_issues": [],
            }
            broken = self._check_broken_imports(content)
            if broken:
                issues["broken_imports"] = broken
                issues["needs_alignment"] = True
            else:
                pass
            violations = self._check_rule_violations(content)
            if violations:
                issues["rule_violations"] = violations
                issues["needs_alignment"] = True
            else:
                pass
            ast_issues = self._check_ast_issues(content)
            if ast_issues:
                issues["ast_issues"] = ast_issues
                issues["needs_alignment"] = True
            else:
                pass
            return issues
        except Exception as e:
            self.logger.log_error(f"Error scanning {file_path}: {e}")
            raise
        else:
            pass
        finally:
            pass

    def _check_broken_imports(self, content: str) -> list[dict[str, Any]]:
        """
        Identify broken import patterns in content, ignoring comments and strings.

        Args:
            content: File content as string.

        Returns:
            List of broken import issue dicts.
        """
        issues: list[dict[str, Any]] = []
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped_line = line.strip()

            # Skip comments, strings, and dictionary definitions
            if (
                stripped_line.startswith("#")
                or stripped_line.startswith('"""')
                or stripped_line.startswith("'''")
                or '"' in stripped_line
                and ":" in stripped_line  # Dictionary entries
                or "'" in stripped_line
                and ":" in stripped_line
            ):  # Dictionary entries
                continue

            # Only check actual import lines
            if not (
                stripped_line.startswith("from ") or stripped_line.startswith("import ")
            ):
                continue

            for pattern, correct in self.broken_imports.items():
                if pattern in line:
                    issues.append(
                        {
                            "line": line_no,
                            "pattern": pattern,
                            "correct_pattern": correct,
                            "content": line.strip(),
                            "type": "broken_import",
                        }
                    )
        return issues

    def _check_rule_violations(self, content: str) -> list[dict[str, Any]]:
        """
        Identify rule violations using regex patterns, ignoring comments and strings.

        Args:
            content: File content as string.

        Returns:
            List of rule violation dicts.
        """
        issues: list[dict[str, Any]] = []
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped_line = line.strip()

            # Skip comments, strings, and dictionary definitions
            if (
                stripped_line.startswith("#")
                or stripped_line.startswith('"""')
                or stripped_line.startswith("'''")
                or '"' in stripped_line
                and ":" in stripped_line  # Dictionary entries
                or "'" in stripped_line
                and ":" in stripped_line
            ):  # Dictionary entries
                continue

            for name, pattern in self.rule_violations.items():
                # Special handling for non_absolute_imports - skip if it's already absolute
                if (
                    name == "non_absolute_imports"
                    and "src.tools.code_generation.o3_code_generator" in line
                ):
                    continue

                if re.search(pattern, line):
                    issues.append(
                        {
                            "line": line_no,
                            "rule": name,
                            "pattern": pattern,
                            "content": line.strip(),
                            "type": "rule_violation",
                        }
                    )
        return issues

    def _check_ast_issues(self, content: str) -> list[dict[str, Any]]:
        """
        Analyze AST for structural issues like missing docstrings, print calls, and logger setup.

        Args:
            content: File content as string.

        Returns:
            List of AST issue dicts.
        """
        issues: list[dict[str, Any]] = []
        try:
            tree = ast.parse(content)
            if not ast.get_docstring(tree):
                issues.append(
                    {
                        "type": "missing_module_docstring",
                        "description": "Module is missing a docstring",
                        "line": 1,
                    }
                )
            else:
                pass
            is_main_script = self._is_main_script(tree)
            if is_main_script and (not self._has_logger_setup(content)):
                issues.append(
                    {
                        "type": "missing_logger_setup",
                        "description": "Main script missing setup_logger(LogConfig()) call",
                        "line": 1,
                    }
                )
            else:
                pass
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and (node.func.id == "print")
                ):
                    issues.append(
                        {
                            "type": "print_statement",
                            "description": "Found print statement - should use logger",
                            "line": node.lineno,
                        }
                    )
                else:
                    pass
                if isinstance(node, ast.ClassDef):
                    if not self._class_has_logger_init(node):
                        issues.append(
                            {
                                "type": "missing_class_logger",
                                "description": f"Class '{node.name}' missing logger initialization in __init__",
                                "line": node.lineno,
                            }
                        )
                    else:
                        pass
                else:
                    pass
            else:
                pass
        except SyntaxError as e:
            issues.append(
                {
                    "type": "syntax_error",
                    "description": f"Syntax error: {e}",
                    "line": e.lineno or 0,
                }
            )
        else:
            pass
        finally:
            pass
        return issues

    def _is_main_script(self, tree: ast.Module) -> bool:
        """
        Check if the file is a main script (has if __name__ == "__main__" or is CLI script).

        Args:
            tree: Parsed AST module.

        Returns:
            True if this appears to be a main script.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if (
                    isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and (node.test.left.id == "__name__")
                    and (len(node.test.ops) == 1)
                    and isinstance(node.test.ops[0], ast.Eq)
                    and (len(node.test.comparators) == 1)
                    and isinstance(node.test.comparators[0], ast.Constant)
                    and (node.test.comparators[0].value == "__main__")
                ):
                    return True
                else:
                    pass
            else:
                pass
        else:
            pass
        return False

    def _has_logger_setup(self, content: str) -> bool:
        """
        Check if the file has proper logger setup.

        Args:
            content: File content as string.

        Returns:
            True if logger setup is present.
        """
        # Check if setup_logger is called anywhere in the file
        if "setup_logger(LogConfig())" in content:
            return True
        return False

    def _class_has_logger_init(self, class_node: ast.ClassDef) -> bool:
        """
        Check if a class has logger initialization in its __init__ method.

        Args:
            class_node: AST class definition node.

        Returns:
            True if class has logger initialization.
        """
        for node in ast.walk(class_node):
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                # Walk through all nodes in the __init__ method, including nested ones
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

    def generate_alignment_report(self, scan_results: dict[str, Any]) -> str:
        """
        Generate a human-readable alignment report.

        Args:
            scan_results: Results from scan_codebase().

        Returns:
            Formatted report string.
        """
        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("ALIGNMENT SCANNER REPORT")
        lines.append("=" * 80)
        lines.append("")
        summary = scan_results["summary"]
        lines.append("📊 SUMMARY:")
        lines.append(f"   Total files scanned: {summary['total_files']}")
        lines.append(
            f"   Files needing alignment: {summary['files_needing_alignment']}"
        )
        lines.append(
            f"   Files with broken imports: {summary['files_with_broken_imports']}"
        )
        lines.append(
            f"   Files with rule violations: {summary['files_with_rule_violations']}"
        )
        lines.append(f"   Alignment percentage: {summary['alignment_percentage']}%")
        lines.append("")
        if scan_results["files_needing_alignment"]:
            lines.append("🔧 FILES NEEDING ALIGNMENT:")
            lines.append("-" * 40)
            for entry in scan_results["files_needing_alignment"]:
                lines.append(f"\n📁 {entry['file']}")
                issues = entry["issues"]
                if issues.get("broken_imports"):
                    lines.append("   ❌ Broken imports:")
                    for imp in issues["broken_imports"]:
                        lines.append(
                            f"      Line {imp['line']}: {imp['pattern']} → {imp['correct_pattern']}"
                        )
                    else:
                        pass
                else:
                    pass
                if issues.get("rule_violations"):
                    lines.append("   ⚠️  Rule violations:")
                    for rv in issues["rule_violations"]:
                        lines.append(f"      Line {rv['line']}: {rv['rule']}")
                    else:
                        pass
                else:
                    pass
                if issues.get("ast_issues"):
                    lines.append("   🔍 AST issues:")
                    for ai in issues["ast_issues"]:
                        lines.append(f"      Line {ai['line']}: {ai['type']}")
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            lines.append("✅ All files are properly aligned!")
        lines.append("")
        lines.append("=" * 80)
        return "\n".join(lines)

    def save_scan_results(
        self, scan_results: dict[str, Any], output_path: Path | None = None
    ) -> Path:
        """
        Save scan results to a JSON file using OutputFormatter and FileGenerator.

        Args:
            scan_results: Results from scan_codebase().
            output_path: Destination path for the JSON file.

        Returns:
            Path where results were saved.
        """
        output_path = output_path or self.base_path / "alignment_scan_results.json"
        formatter = OutputFormatter()
        content = formatter.to_json(scan_results, pretty=True)
        file_generator = FileGenerator()
        file_generator.save_file(content, output_path)
        self.logger.log_info(f"Scan results saved to: {output_path}")
        return output_path


def main() -> int:
    """
    Main function to run the alignment scanner.

    Returns:
        Exit code: 0 if no alignment needed, 1 otherwise.
    """
    logger = get_logger()
    logger.log_info("🚀 Starting Alignment Scanner")
    scanner = AlignmentScanner()
    results = scanner.scan_codebase()
    report = scanner.generate_alignment_report(results)
    logger.log_info(report)
    output_path = scanner.save_scan_results(results)
    logger.log_info(f"📄 Detailed results saved to: {output_path}")
    if results["summary"]["files_needing_alignment"] > 0:
        logger.log_warning("⚠️  Files need alignment - consider running auto-align")
        return 1
    else:
        pass
    logger.log_info("✅ All files are properly aligned!")
    return 0


if __name__ == "__main__":
    setup_logger(LogConfig())  # Moved setup_logger call here
    raise SystemExit(main())
else:
    pass
