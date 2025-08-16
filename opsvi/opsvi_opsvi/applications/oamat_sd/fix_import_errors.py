#!/usr/bin/env python3
"""
Fix Import Errors Script
========================

Fixes malformed imports like:
from src.applications.oamat_sd.src.config.config_manager import ConfigManager

to:
from src.applications.oamat_sd.src.config.config_manager import ConfigManager
"""

from pathlib import Path
import re
import sys


def fix_malformed_imports(project_root: str):
    """Fix all malformed import statements"""
    oamat_path = Path(project_root) / "src" / "applications" / "oamat_sd"

    fixes_applied = 0

    for py_file in oamat_path.rglob("*.py"):
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Fix malformed imports
            malformed_pattern = r"from src\.applications\.oamat_sd\.src\.ConfigManager\(\)\.config_manager import ConfigManager"
            correct_import = "from src.applications.oamat_sd.src.config.config_manager import ConfigManager"

            content = re.sub(malformed_pattern, correct_import, content)

            # Write back if changed
            if content != original_content:
                with open(py_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print(
                    f"✅ Fixed malformed import in {py_file.relative_to(Path(project_root))}"
                )
                fixes_applied += 1

        except Exception as e:
            print(f"❌ Error processing {py_file}: {e}")

    print(f"\n📊 Fixed {fixes_applied} malformed imports")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # Auto-detect project root
        current = Path(__file__).resolve()
        while current.name != "agent_world" and current != current.parent:
            current = current.parent
        project_root = str(current)

    print(f"🔧 Fixing malformed imports in project: {project_root}")
    fix_malformed_imports(project_root)
    print("✅ Import fixing complete!")


if __name__ == "__main__":
    main()
