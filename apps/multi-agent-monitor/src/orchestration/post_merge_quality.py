"""
Post-Merge Quality Assurance
Runs linting, formatting, and tests after agent merges complete
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class PostMergeQuality:
    """
    Handles quality checks after agent work is merged.
    Runs linters, formatters, and tests without blocking merges.
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.results = {
            "linting": [],
            "formatting": [],
            "tests": [],
            "type_checking": [],
        }

    def run_quality_checks(self, agent_workspaces: List[Path]) -> Dict:
        """
        Run comprehensive quality checks on merged code.

        Args:
            agent_workspaces: List of agent workspace paths to check

        Returns:
            Dict with quality check results
        """

        print("\n🔍 Running Post-Merge Quality Checks...")

        # Collect all Python files from agent workspaces
        python_files = []
        for workspace in agent_workspaces:
            if workspace.exists():
                python_files.extend(workspace.glob("**/*.py"))

        if python_files:
            # Run Black formatter
            self._run_black(python_files)

            # Run Ruff linter
            self._run_ruff(python_files)

            # Run mypy type checker (if applicable)
            self._run_mypy(python_files)

            # Run unit tests
            self._run_tests(python_files)

        # Format and fix any issues found
        self._apply_fixes()

        # Generate quality report
        return self._generate_report()

    def _run_black(self, files: List[Path]) -> None:
        """Run Black formatter on Python files"""

        try:
            print("   📝 Running Black formatter...")

            file_paths = [str(f) for f in files]
            result = subprocess.run(
                ["black", "--check", "--diff"] + file_paths,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Files need formatting
                self.results["formatting"].append(
                    {
                        "tool": "black",
                        "status": "needs_formatting",
                        "files": len(
                            [
                                l
                                for l in result.stdout.split("\n")
                                if l.startswith("---")
                            ]
                        ),
                    }
                )

                # Apply formatting
                subprocess.run(
                    ["black"] + file_paths, cwd=self.repo_path, capture_output=True
                )
                print("      ✅ Applied Black formatting")
            else:
                self.results["formatting"].append(
                    {"tool": "black", "status": "clean", "files": 0}
                )
                print("      ✅ Code already formatted")

        except FileNotFoundError:
            logger.warning("Black not installed, skipping formatting")
        except Exception as e:
            logger.error(f"Black formatting failed: {e}")

    def _run_ruff(self, files: List[Path]) -> None:
        """Run Ruff linter on Python files"""

        try:
            print("   🔍 Running Ruff linter...")

            file_paths = [str(f) for f in files]
            result = subprocess.run(
                ["ruff", "check"] + file_paths,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            issues = []
            if result.returncode != 0:
                # Parse issues
                for line in result.stdout.split("\n"):
                    if ".py:" in line:
                        issues.append(line.strip())

                self.results["linting"].append(
                    {
                        "tool": "ruff",
                        "status": "has_issues",
                        "issue_count": len(issues),
                        "sample_issues": issues[:5],  # First 5 issues as sample
                    }
                )

                # Try to auto-fix
                fix_result = subprocess.run(
                    ["ruff", "check", "--fix"] + file_paths,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )

                if fix_result.returncode == 0:
                    print("      ✅ Auto-fixed Ruff issues")
                else:
                    remaining = len(
                        [l for l in fix_result.stdout.split("\n") if ".py:" in l]
                    )
                    print(f"      ⚠️  {remaining} issues need manual review")
            else:
                self.results["linting"].append(
                    {"tool": "ruff", "status": "clean", "issue_count": 0}
                )
                print("      ✅ No linting issues")

        except FileNotFoundError:
            logger.warning("Ruff not installed, skipping linting")
        except Exception as e:
            logger.error(f"Ruff linting failed: {e}")

    def _run_mypy(self, files: List[Path]) -> None:
        """Run mypy type checker on Python files"""

        try:
            print("   🔎 Running mypy type checker...")

            file_paths = [str(f) for f in files]
            result = subprocess.run(
                ["mypy", "--ignore-missing-imports"] + file_paths,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Parse type errors
                errors = [l for l in result.stdout.split("\n") if ": error:" in l]

                self.results["type_checking"].append(
                    {
                        "tool": "mypy",
                        "status": "has_errors",
                        "error_count": len(errors),
                        "sample_errors": errors[:5],
                    }
                )
                print(f"      ⚠️  {len(errors)} type errors found")
            else:
                self.results["type_checking"].append(
                    {"tool": "mypy", "status": "clean", "error_count": 0}
                )
                print("      ✅ No type errors")

        except FileNotFoundError:
            # Mypy is optional
            pass
        except Exception as e:
            logger.error(f"Mypy type checking failed: {e}")

    def _run_tests(self, files: List[Path]) -> None:
        """Run unit tests for Python files"""

        test_files = [f for f in files if f.name.startswith("test_")]

        if not test_files:
            print("   🧪 No test files to run")
            return

        print(f"   🧪 Running {len(test_files)} test files...")

        for test_file in test_files:
            try:
                result = subprocess.run(
                    ["python", str(test_file)],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                success = result.returncode == 0
                self.results["tests"].append(
                    {
                        "file": test_file.name,
                        "status": "passed" if success else "failed",
                        "output": result.stdout if not success else None,
                    }
                )

                status = "✅" if success else "❌"
                print(f"      {status} {test_file.name}")

            except subprocess.TimeoutExpired:
                self.results["tests"].append(
                    {"file": test_file.name, "status": "timeout"}
                )
                print(f"      ⏱️  {test_file.name} (timeout)")
            except Exception as e:
                logger.error(f"Test execution failed for {test_file}: {e}")

    def _apply_fixes(self) -> None:
        """Commit any automatic fixes applied"""

        try:
            # Check if there are changes from formatting/linting
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                # Commit the fixes
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )

                subprocess.run(
                    [
                        "git",
                        "commit",
                        "--no-verify",
                        "-m",
                        "fix: apply post-merge quality fixes",
                    ],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )

                print("\n   📝 Committed quality fixes")

        except subprocess.CalledProcessError:
            # No changes to commit
            pass

    def _generate_report(self) -> Dict:
        """Generate comprehensive quality report"""

        report = {
            "summary": {
                "formatting_clean": all(
                    r["status"] == "clean" for r in self.results["formatting"]
                ),
                "linting_clean": all(
                    r["status"] == "clean" for r in self.results["linting"]
                ),
                "types_clean": all(
                    r["status"] == "clean" for r in self.results["type_checking"]
                ),
                "tests_passed": all(
                    r["status"] == "passed" for r in self.results["tests"]
                )
                if self.results["tests"]
                else True,
            },
            "details": self.results,
        }

        # Print summary
        print("\n📊 Quality Check Summary:")
        print(
            f"   Formatting: {'✅ Clean' if report['summary']['formatting_clean'] else '⚠️ Fixed'}"
        )
        print(
            f"   Linting:    {'✅ Clean' if report['summary']['linting_clean'] else '⚠️ Has issues'}"
        )
        print(
            f"   Types:      {'✅ Clean' if report['summary']['types_clean'] else '⚠️ Has errors'}"
        )
        print(
            f"   Tests:      {'✅ Passed' if report['summary']['tests_passed'] else '❌ Failed'}"
        )

        return report

    def run_on_branch(self, branch: str) -> Dict:
        """
        Run quality checks on a specific branch.

        Args:
            branch: Branch name to check

        Returns:
            Quality report
        """

        # Switch to branch
        subprocess.run(
            ["git", "checkout", branch],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        # Find all agent workspaces
        monitor_path = self.repo_path / "apps/multi-agent-monitor"
        workspaces = list(monitor_path.glob("agent_workspace_*"))

        # Run quality checks
        return self.run_quality_checks(workspaces)
