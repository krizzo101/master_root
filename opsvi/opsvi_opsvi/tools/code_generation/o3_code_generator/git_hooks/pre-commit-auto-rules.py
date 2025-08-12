"""
Pre-commit Git Hook for Auto Rules Generation

This hook intelligently regenerates auto rules only when relevant files have changed.
It ensures that project rules are always current with the latest codebase patterns.

Usage:
    Place this file in .git/hooks/pre-commit (make it executable)
    Or use: ln -s ../../src/tools/code_generation/o3_code_generator/git_hooks/pre-commit-auto-rules.py .git/hooks/pre-commit
"""

import os
import subprocess
import sys
from pathlib import Path


class AutoRulesPreCommitHook:
    """Pre-commit hook for intelligent auto rules generation."""

    RELEVANT_PATTERNS = {
        "*.py",
        "*.yaml",
        "*.yml",
        "*.json",
        "*.toml",
        "*.md",
        "*.txt",
        "requirements*.txt",
        "setup.py",
        "pyproject.toml",
    }
    RELEVANT_DIRECTORIES = {"src/", "tests/", "docs/", "config/", "scripts/", "tools/"}
    EXCLUDED_PATTERNS = {
        "*.log",
        "*.tmp",
        "*.cache",
        "__pycache__/",
        ".git/",
        ".venv/",
        "venv/",
        "node_modules/",
        "*.pyc",
        "*.pyo",
    }

    def __init__(self):
        """Initialize the pre-commit hook."""
        self.project_root = self._find_project_root()
        self.auto_rules_dir = (
            self.project_root
            / "src"
            / "tools"
            / "code_generation"
            / "o3_code_generator"
            / "auto_rules_generation"
        )
        self.rules_dir = (
            self.project_root
            / "src"
            / "tools"
            / "code_generation"
            / "o3_code_generator"
            / "docs"
        )

    def _find_project_root(self) -> Path:
        """Find the project root directory (where .git is located)."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            else:
                pass
            current = current.parent
        else:
            pass
        raise FileNotFoundError("Could not find project root (no .git directory found)")

    def _get_staged_files(self) -> list[str]:
        """Get list of staged files for the current commit."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                return [
                    line.strip() for line in result.stdout.splitlines() if line.strip()
                ]
            else:
                pass
            return []
        except Exception:
            return []
        else:
            pass
        finally:
            pass

    def _is_relevant_file(self, file_path: str) -> bool:
        """Check if a file is relevant for rule regeneration."""
        path = Path(file_path)
        for pattern in self.EXCLUDED_PATTERNS:
            if pattern.endswith("/"):
                if pattern[:-1] in path.parts:
                    return False
                else:
                    pass
            elif path.match(pattern):
                return False
            else:
                pass
        else:
            pass
        for pattern in self.RELEVANT_PATTERNS:
            if path.match(pattern):
                return True
            else:
                pass
        else:
            pass
        for directory in self.RELEVANT_DIRECTORIES:
            if file_path.startswith(directory):
                return True
            else:
                pass
        else:
            pass
        return False

    def _has_relevant_changes(self, staged_files: list[str]) -> bool:
        """Check if any staged files are relevant for rule regeneration."""
        relevant_files = [f for f in staged_files if self._is_relevant_file(f)]
        if relevant_files:
            return True
        else:
            pass
        return False

    def _run_auto_rules_generation(self) -> bool:
        """Run the auto rules generation system."""
        try:
            os.chdir(self.auto_rules_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.tools.code_generation.o3_code_generator.auto_rules_generation.auto_rules_generator",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                return True
            else:
                pass
                return False
        except Exception:
            return False
        else:
            pass
        finally:
            pass

    def _stage_updated_rules(self) -> bool:
        """Stage any updated rule files."""
        try:
            rule_files = [
                self.rules_dir / "project_rules.md",
                self.rules_dir / "universal_rules.md",
            ]
            staged_files = []
            for rule_file in rule_files:
                if rule_file.exists():
                    result = subprocess.run(
                        ["git", "diff", "--quiet", str(rule_file)],
                        cwd=self.project_root,
                    )
                    if result.returncode != 0:
                        subprocess.run(
                            ["git", "add", str(rule_file)],
                            cwd=self.project_root,
                            check=True,
                        )
                        staged_files.append(rule_file.name)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            if staged_files:
                pass
            else:
                pass
            return True
        except Exception:
            return False
        else:
            pass
        finally:
            pass

    def run(self) -> int:
        """Run the pre-commit hook."""
        staged_files = self._get_staged_files()
        if not staged_files:
            return 0
        else:
            pass
        if not self._has_relevant_changes(staged_files):
            return 0
        else:
            pass
        if not self.auto_rules_dir.exists():
            return 0
        else:
            pass
        if not self._run_auto_rules_generation():
            return 0
        else:
            pass
        if not self._stage_updated_rules():
            return 0
        else:
            pass
        return 0


def main():
    """Main entry point for the pre-commit hook."""
    hook = AutoRulesPreCommitHook()
    sys.exit(hook.run())


if __name__ == "__main__":
    main()
else:
    pass
