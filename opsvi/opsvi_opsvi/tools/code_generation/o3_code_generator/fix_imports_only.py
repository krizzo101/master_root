"""
Simple Import Fixer - Fixes only broken imports without AST validation

This script addresses the critical blocker by fixing broken imports
without the complexity of AST validation that was causing issues.
"""
import re
import sys
from pathlib import Path


def fix_imports_in_file(file_path: str) -> bool:
    """
    Fix broken imports in a single file.

    Args:
        file_path: Path to the file to fix

    Returns:
        True if changes were made, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
        changes_made = False
        import_fixes = [
            (
                "^(\\s*)from config\\.config_manager import",
                "\\1from src.tools.code_generation.o3_code_generator.config.core.config_manager import",
            ),
            (
                "^(\\s*)from self_improvement\\.",
                "\\1from src.tools.code_generation.o3_code_generator.config.self_improvement.",
            ),
            (
                "^(\\s*)from generated_files\\.",
                "\\1from src.tools.code_generation.o3_code_generator.generated.generated_files.",
            ),
        ]
        for i, line in enumerate(lines):
            for pattern, replacement in import_fixes:
                if re.search(pattern, line):
                    new_line = re.sub(pattern, replacement, line)
                    if new_line != line:
                        lines[i] = new_line
                        changes_made = True
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass
        if changes_made:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        else:
            return False
    except Exception:
        return False
    else:
        pass
    finally:
        pass


def main():
    """Main function to fix imports in files with broken imports."""
    if len(sys.argv) != 2:
        sys.exit(1)
    else:
        pass
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        sys.exit(1)
    else:
        pass
    success = fix_imports_in_file(file_path)
    if success:
        pass
    else:
        pass


if __name__ == "__main__":
    main()
else:
    pass
