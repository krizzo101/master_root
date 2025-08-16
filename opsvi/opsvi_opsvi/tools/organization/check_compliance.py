"""
Project Organization Compliance Checker

Validates current project structure against organization standards.
Identifies violations and suggests corrections.

Usage:
    python src/tools/organization/check_compliance.py [--fix] [--report]
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List


class OrganizationComplianceChecker:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.violations = []
        self.suggestions = []

    def check_root_directory(self) -> Dict:
        """Check root directory for violations."""
        allowed_in_root = {
            "README.md",
            "docker-compose.yml",
            ".gitignore",
            ".editorconfig",
            "package.json",
            "Makefile",
            "LICENSE",
            "env.example",
            ".pre-commit-config.yaml",
            "Dockerfile",
            "CONTRIBUTING.md",
        }
        allowed_dirs_in_root = {
            "src",
            "config",
            "docs",
            "data",
            "archive",
            "scripts",
            "templates",
            "infra",
            "db",
            "foxx",
            "misc",
            "reference",
            "projects",
            "diagrams",
            "adr",
        }
        violations = []
        suggestions = []
        for item in self.project_root.iterdir():
            if item.name.startswith(".") and item.name not in allowed_in_root:
                continue
            else:
                pass
            if item.is_file():
                if item.name not in allowed_in_root:
                    violation_type = self._classify_file_violation(item)
                    violations.append(
                        {
                            "file": str(item),
                            "type": violation_type,
                            "size": item.stat().st_size if item.exists() else 0,
                        }
                    )
                    suggestions.append(self._suggest_file_location(item))
                else:
                    pass
            elif item.is_dir():
                if item.name not in allowed_dirs_in_root:
                    violations.append(
                        {"directory": str(item), "type": "unauthorized_directory"}
                    )
                else:
                    pass
            else:
                pass
        else:
            pass
        return {
            "violations": violations,
            "suggestions": suggestions,
            "compliant_files": len(
                [
                    f
                    for f in self.project_root.iterdir()
                    if f.is_file() and f.name in allowed_in_root
                ]
            ),
        }

    def _classify_file_violation(self, file_path: Path) -> str:
        """Classify the type of file violation."""
        suffix = file_path.suffix.lower()
        if suffix == ".py":
            return "python_source_in_root"
        elif suffix == ".json":
            return "json_artifact_in_root"
        elif suffix == ".log":
            return "log_file_in_root"
        elif suffix in [".md", ".txt"]:
            return "documentation_in_root"
        elif suffix in [".yml", ".yaml"]:
            return "config_in_root"
        else:
            return "misc_file_in_root"

    def _suggest_file_location(self, file_path: Path) -> Dict:
        """Suggest proper location for misplaced file."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        if suffix == ".py":
            if "test" in name:
                suggested_location = "src/tools/testing/"
            elif any(keyword in name for keyword in ["script", "tool", "util"]):
                suggested_location = "src/tools/utilities/"
            else:
                suggested_location = "src/applications/{app_name}/"
        elif suffix == ".json":
            if any(keyword in name for keyword in ["config", "settings"]):
                suggested_location = "config/development/"
            else:
                suggested_location = (
                    f"data/artifacts/{datetime.now().strftime('%Y-%m-%d')}/"
                )
        elif suffix == ".log":
            suggested_location = f"data/logs/{datetime.now().strftime('%Y-%m-%d')}/"
        elif suffix in [".md", ".txt"]:
            if "readme" in name or any(
                keyword in name for keyword in ["guide", "doc", "manual"]
            ):
                suggested_location = "docs/user/"
            elif any(keyword in name for keyword in ["arch", "design"]):
                suggested_location = "docs/architecture/"
            else:
                suggested_location = "docs/development/"
        elif suffix in [".yml", ".yaml"]:
            suggested_location = "config/development/"
        else:
            suggested_location = (
                f"data/artifacts/{datetime.now().strftime('%Y-%m-%d')}/"
            )
        return {
            "file": str(file_path),
            "suggested_location": suggested_location,
            "reason": f"{suffix} files should not be in root directory",
        }

    def check_directory_structure(self) -> Dict:
        """Check if required directories exist."""
        required_dirs = [
            "src/applications",
            "src/shared",
            "src/tools",
            "config/production",
            "config/development",
            "config/testing",
            "docs/api",
            "docs/architecture",
            "docs/user",
            "data/artifacts",
            "data/backups",
            "data/logs",
            "data/tmp",
        ]
        missing_dirs = []
        existing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                existing_dirs.append(dir_path)
            else:
                missing_dirs.append(dir_path)
        else:
            pass
        return {
            "missing_directories": missing_dirs,
            "existing_directories": existing_dirs,
            "compliance_percentage": len(existing_dirs) / len(required_dirs) * 100,
        }

    def generate_report(self) -> Dict:
        """Generate comprehensive compliance report."""
        root_check = self.check_root_directory()
        structure_check = self.check_directory_structure()
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "root_directory_compliance": root_check,
            "directory_structure_compliance": structure_check,
            "overall_score": self._calculate_overall_score(root_check, structure_check),
            "immediate_actions": self._generate_action_items(
                root_check, structure_check
            ),
        }
        return report

    def _calculate_overall_score(
        self, root_check: Dict, structure_check: Dict
    ) -> float:
        """Calculate overall compliance score."""
        root_violations = len(root_check["violations"])
        structure_compliance = structure_check["compliance_percentage"]
        root_penalty = min(root_violations * 10, 50)
        overall_score = max(0, structure_compliance - root_penalty)
        return round(overall_score, 1)

    def _generate_action_items(
        self, root_check: Dict, structure_check: Dict
    ) -> List[str]:
        """Generate prioritized action items."""
        actions = []
        if root_check["violations"]:
            actions.append(
                f"🚨 URGENT: Move {len(root_check['violations'])} files out of root directory"
            )
        else:
            pass
        if structure_check["missing_directories"]:
            actions.append(
                f"📁 Create {len(structure_check['missing_directories'])} missing directories"
            )
        else:
            pass
        large_files = [
            v for v in root_check["violations"] if v.get("size", 0) > 1024 * 1024
        ]
        if large_files:
            actions.append(
                f"💾 Priority: Move {len(large_files)} large files (>1MB) from root"
            )
        else:
            pass
        return actions

    def fix_violations(self, dry_run: bool = True) -> Dict:
        """Attempt to fix violations automatically."""
        root_check = self.check_root_directory()
        structure_check = self.check_directory_structure()
        fixed = []
        errors = []
        for missing_dir in structure_check["missing_directories"]:
            try:
                if not dry_run:
                    (self.project_root / missing_dir).mkdir(parents=True, exist_ok=True)
                else:
                    pass
                fixed.append(f"Created directory: {missing_dir}")
            except Exception as e:
                errors.append(f"Failed to create {missing_dir}: {e}")
            else:
                pass
            finally:
                pass
        else:
            pass
        for suggestion in root_check["suggestions"]:
            if "json" in suggestion["file"].lower():
                try:
                    source = Path(suggestion["file"])
                    dest_dir = self.project_root / suggestion["suggested_location"]
                    if not dry_run:
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        source.rename(dest_dir / source.name)
                    else:
                        pass
                    fixed.append(
                        f"Moved {source.name} to {suggestion['suggested_location']}"
                    )
                except Exception as e:
                    errors.append(f"Failed to move {source.name}: {e}")
                else:
                    pass
                finally:
                    pass
            else:
                pass
        else:
            pass
        return {"fixed": fixed, "errors": errors, "dry_run": dry_run}


def main():
    parser = argparse.ArgumentParser(
        description="Check project organization compliance"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix violations automatically"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    parser.add_argument(
        "--report",
        default="compliance_report.json",
        help="Output file for compliance report",
    )
    args = parser.parse_args()
    checker = OrganizationComplianceChecker()
    if args.fix or args.dry_run:
        fix_result = checker.fix_violations(
            dry_run=True if args.dry_run else not args.fix
        )
        for fix in fix_result["fixed"]:
            pass
        else:
            pass
        if fix_result["errors"]:
            for error in fix_result["errors"]:
                pass
            else:
                pass
        else:
            pass
    else:
        pass
    report = checker.generate_report()
    with open(args.report, "w") as f:
        json.dump(report, f, indent=2)
    if report["immediate_actions"]:
        for action in report["immediate_actions"]:
            pass
        else:
            pass
    else:
        pass


if __name__ == "__main__":
    main()
else:
    pass
