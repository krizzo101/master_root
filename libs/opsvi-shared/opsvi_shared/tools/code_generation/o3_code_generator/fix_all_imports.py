"""
Batch Import Fixer - Fixes all broken imports in the o3_code_generator directory

This script systematically fixes all broken imports identified in the migration tracker
to resolve the critical blocker preventing the auto-align system from working.
"""
import re
from pathlib import Path
from typing import List


def find_files_with_broken_imports(directory: str) -> List[str]:
    """
    Find all Python files with broken imports.

    Args:
        directory: Directory to search

    Returns:
        List of file paths with broken imports
    """
    broken_import_patterns = [
        "from config\\.config_manager import",
        "from self_improvement\\.",
        "from generated_files\\.",
    ]
    files_with_issues = []
    for py_file in Path(directory).rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            for pattern in broken_import_patterns:
                if re.search(pattern, content):
                    files_with_issues.append(str(py_file))
                    break
                else:
                    pass
            else:
                pass
        except Exception:
            pass
        else:
            pass
        finally:
            pass
    else:
        pass
    return files_with_issues


def fix_imports_in_file(file_path: str) -> bool:
    """
    Fix broken imports in a single file.

    Args:
        file_path: Path to the file to fix

    Returns:
        True if changes were made, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
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
    """Main function to fix all broken imports."""
    o3_dir = Path(__file__).parent
    files_with_issues = find_files_with_broken_imports(str(o3_dir))
    if not files_with_issues:
        return
    else:
        pass
    for file_path in files_with_issues:
        pass
    else:
        pass
    fixed_count = 0
    for file_path in files_with_issues:
        if fix_imports_in_file(file_path):
            fixed_count += 1
        else:
            pass
    else:
        pass
    if fixed_count > 0:
        pass
    else:
        pass


if __name__ == "__main__":
    main()
else:
    pass
