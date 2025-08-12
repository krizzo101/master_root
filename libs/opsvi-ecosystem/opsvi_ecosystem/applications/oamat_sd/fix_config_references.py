#!/usr/bin/env python3
"""
Systematic Config Reference Fixer
=================================

Fixes all F821 undefined config references by:
1. Adding proper ConfigManager imports where missing
2. Replacing direct config.* usage with ConfigManager().*
3. Ensuring all config access follows the correct pattern

Usage:
    python fix_config_references.py
"""

import re
import sys
from pathlib import Path


class ConfigReferenceFixer:
    """Systematically fixes config references throughout the codebase"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixes_applied = 0
        self.files_processed = 0

    def fix_all_files(self) -> None:
        """Fix all Python files in the oamat_sd application"""
        oamat_path = self.project_root / "src" / "applications" / "oamat_sd"

        for py_file in oamat_path.rglob("*.py"):
            # Skip certain files
            if any(
                skip in str(py_file)
                for skip in [
                    "__pycache__",
                    ".git",
                    "test_",
                    "/tests/",
                    "fix_config_references.py",
                    "automate_compliance_fixes.py",
                ]
            ):
                continue

            try:
                self.fix_file(py_file)
                self.files_processed += 1
            except Exception as e:
                print(f"❌ Error processing {py_file}: {e}")

    def fix_file(self, file_path: Path) -> None:
        """Fix a single file"""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Check if file has config references that need fixing
        if not re.search(r"\bconfig\.[a-zA-Z_]", content):
            return

        # Add ConfigManager import if missing
        if (
            "from src.applications.oamat_sd.src.config.config_manager import ConfigManager"
            not in content
        ):
            content = self._add_config_import(content)

        # Replace direct config references with ConfigManager() calls
        content = self._replace_config_references(content)

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(
                f"✅ Fixed config references in {file_path.relative_to(self.project_root)}"
            )
            self.fixes_applied += 1

    def _add_config_import(self, content: str) -> str:
        """Add ConfigManager import to the file"""
        lines = content.split("\n")

        # Find the best place to insert the import
        import_insert_line = 0
        in_imports = False

        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                in_imports = True
                import_insert_line = i + 1
            elif in_imports and line.strip() == "":
                # End of import block
                break
            elif in_imports and not (line.startswith(" ") or line.startswith("\t")):
                # End of multiline import
                import_insert_line = i
                break

        # Insert the import
        import_line = "from src.applications.oamat_sd.src.config.config_manager import ConfigManager"
        lines.insert(import_insert_line, import_line)

        return "\n".join(lines)

    def _replace_config_references(self, content: str) -> str:
        """Replace direct config references with ConfigManager() calls"""

        # Pattern to match config.something but not ConfigManager().config.something
        pattern = r"(?<!ConfigManager\(\)\.)(?<!ConfigManager\(\)\s\.\s)\bconfig\."

        # Replace with ConfigManager().
        content = re.sub(pattern, "ConfigManager().", content)

        return content

    def print_summary(self) -> None:
        """Print fix summary"""
        print("\n📊 Fix Summary:")
        print(f"Files processed: {self.files_processed}")
        print(f"Files with fixes: {self.fixes_applied}")


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

    print(f"🔧 Fixing config references in project: {project_root}")

    fixer = ConfigReferenceFixer(project_root)
    fixer.fix_all_files()
    fixer.print_summary()

    print("\n✅ Config reference fixing complete!")


if __name__ == "__main__":
    main()
