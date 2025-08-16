"""
Quick Root Directory Cleanup Script

Moves misplaced files from root directory to proper locations
according to project organization standards.

Usage:
    python cleanup_root_violations.py [--dry-run]
"""

import argparse
from datetime import datetime
from pathlib import Path
import shutil


def cleanup_root_directory(dry_run=True):
    """Clean up root directory violations."""
    today = datetime.now().strftime("%Y-%m-%d")
    artifact_dir = Path(f"data/artifacts/{today}")
    json_files = [
        ".specstory_loader_state.json",
        "collaboration_intelligence_log.json",
        "specstory_intelligence_processed.json",
        "kb_request.json",
        "collaboration_analysis_request.json",
        "project_structure_analysis.json",
        "current_dependency_analysis.json",
    ]
    doc_files = ["SYSTEM_DEMONSTRATION_COMPLETE.md"]
    moved_files = []
    errors = []
    if not dry_run:
        try:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            Path("docs/development").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Failed to create directories: {e}")
            return {"moved": moved_files, "errors": errors}
        else:
            pass
        finally:
            pass
    else:
        pass
    for filename in json_files:
        if Path(filename).exists():
            try:
                if not dry_run:
                    shutil.move(filename, artifact_dir / filename)
                else:
                    pass
                moved_files.append(f"{filename} → data/artifacts/{today}/")
            except Exception as e:
                errors.append(f"Failed to move {filename}: {e}")
            else:
                pass
            finally:
                pass
        else:
            pass
    else:
        pass
    for filename in doc_files:
        if Path(filename).exists():
            try:
                if not dry_run:
                    shutil.move(filename, f"docs/development/{filename}")
                else:
                    pass
                moved_files.append(f"{filename} → docs/development/")
            except Exception as e:
                errors.append(f"Failed to move {filename}: {e}")
            else:
                pass
            finally:
                pass
        else:
            pass
    else:
        pass
    return {"moved": moved_files, "errors": errors}


def check_current_violations():
    """Check what violations currently exist."""
    allowed_files = {
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
        "cleanup_root_violations.py",
        "PROJECT_STRUCTURE_QUICK_REF.md",
    }
    violations = []
    for item in Path(".").iterdir():
        if item.is_file() and (not item.name.startswith(".")):
            if item.name not in allowed_files:
                size = item.stat().st_size
                size_str = (
                    f"{size / 1024 / 1024:.1f}MB"
                    if size > 1024 * 1024
                    else f"{size / 1024:.1f}KB"
                )
                violations.append(f"  📄 {item.name} ({size_str})")
            else:
                pass
        else:
            pass
    else:
        pass
    if violations:
        for violation in violations:
            pass
        else:
            pass
    else:
        pass
    return len(violations)


def main():
    parser = argparse.ArgumentParser(description="Clean up root directory violations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without actually moving files",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for violations, don't clean up",
    )
    args = parser.parse_args()
    if args.check_only:
        violations = check_current_violations()
        if violations > 0:
            pass
        else:
            pass
        return
    else:
        pass
    violations = check_current_violations()
    if violations == 0:
        return
    else:
        pass
    result = cleanup_root_directory(dry_run=args.dry_run)
    if result["errors"]:
        for error in result["errors"]:
            pass
        else:
            pass
    else:
        pass
    if not args.dry_run and result["moved"] or args.dry_run:
        pass
    else:
        pass


if __name__ == "__main__":
    main()
else:
    pass
