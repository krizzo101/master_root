#!/usr/bin/env python3
"""
Migration Status Dashboard
Shows the current migration status of all apps in the project
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class MigrationStatus:
    """Track and report app migration status"""

    def __init__(self):
        self.project_root = Path("/home/opsvi/master_root")
        self.apps_dir = self.project_root / "apps"

    def check_app_status(self, app_path: Path) -> Dict:
        """Check migration status of a single app"""

        status = {
            "name": app_path.name,
            "path": str(app_path),
            "is_symlink": app_path.is_symlink(),
            "has_venv": (app_path / ".venv").exists() or (app_path / "venv").exists(),
            "has_wrapper": (self.project_root / "scripts" / app_path.name).exists(),
            "uses_shared_libs": False,
            "has_claude_adapter": (app_path / "claude_code_adapter.py").exists()
            or (
                app_path
                / "src"
                / app_path.name.replace("-", "_")
                / "claude_code_adapter.py"
            ).exists(),
            "migration_status": "not_started",
            "files_count": 0,
            "python_files": 0,
        }

        # Count files
        if app_path.exists() and not app_path.is_symlink():
            all_files = list(app_path.rglob("*"))
            py_files = [
                f for f in all_files if f.suffix == ".py" and ".venv" not in str(f)
            ]
            status["files_count"] = len(all_files)
            status["python_files"] = len(py_files)

            # Check for shared lib usage
            for py_file in py_files[:10]:  # Sample first 10 files
                try:
                    content = py_file.read_text()
                    if "from opsvi_" in content or "import opsvi_" in content:
                        status["uses_shared_libs"] = True
                        break
                except:
                    pass

        # Determine migration status
        if status["is_symlink"]:
            status["migration_status"] = "symlink"
        elif (
            status["has_wrapper"]
            and status["uses_shared_libs"]
            and not status["has_venv"]
        ):
            status["migration_status"] = "completed"
        elif status["has_claude_adapter"] or status["uses_shared_libs"]:
            status["migration_status"] = "in_progress"
        elif not status["has_venv"]:
            status["migration_status"] = "partial"
        else:
            status["migration_status"] = "not_started"

        return status

    def get_all_apps_status(self) -> List[Dict]:
        """Get status of all apps"""

        apps = []

        for app_path in self.apps_dir.iterdir():
            if app_path.is_dir() or app_path.is_symlink():
                # Skip hidden directories
                if app_path.name.startswith("."):
                    continue

                status = self.check_app_status(app_path)
                apps.append(status)

        return sorted(apps, key=lambda x: x["name"])

    def generate_report(self) -> str:
        """Generate migration status report"""

        apps = self.get_all_apps_status()

        # Count by status
        status_counts = {
            "completed": 0,
            "in_progress": 0,
            "partial": 0,
            "not_started": 0,
            "symlink": 0,
        }

        for app in apps:
            status_counts[app["migration_status"]] += 1

        # Build report
        report = []
        report.append("=" * 70)
        report.append("APP MIGRATION STATUS DASHBOARD")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 30)
        report.append(f"Total Apps: {len(apps)}")
        report.append(f"✅ Completed: {status_counts['completed']}")
        report.append(f"🔄 In Progress: {status_counts['in_progress']}")
        report.append(f"⚠️  Partial: {status_counts['partial']}")
        report.append(f"❌ Not Started: {status_counts['not_started']}")
        report.append(f"🔗 Symlinks: {status_counts['symlink']}")
        report.append("")

        # Detailed status
        report.append("DETAILED STATUS")
        report.append("-" * 30)

        # Group by status
        for status in ["completed", "in_progress", "partial", "not_started", "symlink"]:
            status_apps = [a for a in apps if a["migration_status"] == status]

            if status_apps:
                status_emoji = {
                    "completed": "✅",
                    "in_progress": "🔄",
                    "partial": "⚠️",
                    "not_started": "❌",
                    "symlink": "🔗",
                }[status]

                report.append(f"\n{status_emoji} {status.upper().replace('_', ' ')}:")

                for app in status_apps:
                    details = []

                    if app["is_symlink"]:
                        details.append("symlink")
                    else:
                        details.append(f"{app['python_files']} py files")

                        if app["has_venv"]:
                            details.append("has venv")
                        if app["has_wrapper"]:
                            details.append("has wrapper")
                        if app["uses_shared_libs"]:
                            details.append("uses shared libs")
                        if app["has_claude_adapter"]:
                            details.append("has claude adapter")

                    report.append(f"  - {app['name']}: {', '.join(details)}")

        # Recommendations
        report.append("")
        report.append("RECOMMENDATIONS")
        report.append("-" * 30)

        # Find next candidates for migration
        candidates = [
            a
            for a in apps
            if a["migration_status"] == "not_started" and not a["is_symlink"]
        ]

        if candidates:
            # Sort by complexity (fewer files = easier)
            candidates.sort(key=lambda x: x["python_files"])

            report.append("Next migration candidates (easiest first):")
            for app in candidates[:3]:
                report.append(
                    f"  1. {app['name']} ({app['python_files']} Python files)"
                )

        # Special cases
        in_progress = [a for a in apps if a["migration_status"] == "in_progress"]
        if in_progress:
            report.append("")
            report.append("Apps needing completion:")
            for app in in_progress:
                report.append(f"  - {app['name']}")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)


def main():
    """Main execution"""

    dashboard = MigrationStatus()
    report = dashboard.generate_report()
    print(report)

    # Save report
    report_path = Path("/home/opsvi/master_root/docs/migration_status.txt")
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")

    # Also save JSON for programmatic use
    apps_status = dashboard.get_all_apps_status()
    json_path = Path("/home/opsvi/master_root/docs/migration_status.json")

    with open(json_path, "w") as f:
        json.dump(
            {"timestamp": datetime.now().isoformat(), "apps": apps_status}, f, indent=2
        )

    print(f"JSON data saved to: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
