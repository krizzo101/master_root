"""
Quality gates for code validation and testing.
"""

import ast
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QualityGates:
    """Quality gates for code validation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize quality gates.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.run_tests = self.config.get("run_tests", True)
        self.compile_check = self.config.get("compile_check", True)
        self.auto_fix_attempts = self.config.get("auto_fix_attempts", 1)

    def check_python_syntax(self, file_path: Path) -> Dict[str, Any]:
        """
        Check Python file syntax.

        Args:
            file_path: Path to Python file

        Returns:
            Check result dictionary
        """
        try:
            with open(file_path, "r") as f:
                code = f.read()

            ast.parse(code)

            return {
                "status": "passed",
                "file": str(file_path),
                "errors": [],
            }

        except SyntaxError as e:
            return {
                "status": "failed",
                "file": str(file_path),
                "errors": [
                    {
                        "line": e.lineno,
                        "column": e.offset,
                        "message": str(e.msg),
                    }
                ],
            }
        except Exception as e:
            return {
                "status": "error",
                "file": str(file_path),
                "errors": [{"message": str(e)}],
            }

    def run_pytest(
        self,
        test_path: Path,
        args: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run pytest on a directory or file.

        Args:
            test_path: Path to test directory or file
            args: Additional pytest arguments

        Returns:
            Test result dictionary
        """
        cmd = ["pytest", str(test_path)]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "command": " ".join(cmd),
                "output": result.stdout,
                "errors": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "command": " ".join(cmd),
                "errors": "Test execution timed out",
            }
        except Exception as e:
            return {
                "status": "error",
                "command": " ".join(cmd),
                "errors": str(e),
            }

    def run_lint(
        self,
        file_path: Path,
        linter: str = "ruff",
    ) -> Dict[str, Any]:
        """
        Run linter on a file.

        Args:
            file_path: Path to file
            linter: Linter to use

        Returns:
            Lint result dictionary
        """
        cmd = [linter, "check", str(file_path)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "command": " ".join(cmd),
                "output": result.stdout,
                "errors": result.stderr if result.returncode != 0 else None,
            }

        except Exception as e:
            return {
                "status": "error",
                "command": " ".join(cmd),
                "errors": str(e),
            }

    def validate_all(self, directory: Path) -> Dict[str, Any]:
        """
        Run all quality checks on a directory.

        Args:
            directory: Directory to validate

        Returns:
            Validation results
        """
        results = {
            "syntax": [],
            "tests": [],
            "lint": [],
            "overall": "passed",
        }

        # Check syntax for all Python files
        if self.compile_check:
            for py_file in directory.rglob("*.py"):
                result = self.check_python_syntax(py_file)
                results["syntax"].append(result)
                if result["status"] != "passed":
                    results["overall"] = "failed"

        # Run tests
        if self.run_tests:
            test_dir = directory / "tests"
            if test_dir.exists():
                test_result = self.run_pytest(test_dir)
                results["tests"].append(test_result)
                if test_result["status"] != "passed":
                    results["overall"] = "failed"

        return results
