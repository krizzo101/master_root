"""
Import Fix Script for O3 Code Generator

Automatically fixes common broken import patterns identified in the alignment scanner.
This script runs before auto-align to resolve critical import issues that prevent
successful code generation.
"""

import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
try:
    from o3_logger.logger import LogConfig, get_logger, setup_logger
except ImportError:
    import logging

    class LogConfig:
        def __init__(self):
            self.level = "INFO"
            self.log_dir = "logs"

    def setup_logger(config):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("import_fixer")

    def get_logger():
        return logging.getLogger("import_fixer")

else:
    pass
finally:
    pass


class ImportFixer:
    """
    Automatically fixes common broken import patterns in Python files.

    Handles the most common import issues identified by the alignment scanner:
    - config.config_manager → config.core.config_manager
    - self_improvement → config.self_improvement
    - generated_files → generated.generated_files
    """

    def __init__(self):
        """Initialize the import fixer."""
        setup_logger(LogConfig())
        self.logger = get_logger()
        self.import_fixes = {
            "^(\\s*)from config\\.config_manager import": "\\1from src.tools.code_generation.o3_code_generator.config.core.config_manager import",
            "^(\\s*)from \\.config\\.config_manager import": "\\1from src.tools.code_generation.o3_code_generator.config.core.config_manager import",
            "^(\\s*)from src\\.tools\\.code_generation\\.o3_code_generator\\.config\\.config_manager import": "\\1from src.tools.code_generation.o3_code_generator.config.core.config_manager import",
            "^(\\s*)from self_improvement\\.": "\\1from src.tools.code_generation.o3_code_generator.config.self_improvement.",
            "^(\\s*)from \\.self_improvement\\.": "\\1from src.tools.code_generation.o3_code_generator.config.self_improvement.",
            "^(\\s*)from src\\.tools\\.code_generation\\.o3_code_generator\\.self_improvement\\.": "\\1from src.tools.code_generation.o3_code_generator.config.self_improvement.",
            "^(\\s*)from generated_files\\.": "\\1from src.tools.code_generation.o3_code_generator.generated.generated_files.",
            "^(\\s*)from \\.o3_logger\\.logger import": "\\1from src.tools.code_generation.o3_code_generator.o3_logger.logger import",
            "^(\\s*)from \\.utils\\.": "\\1from src.tools.code_generation.o3_code_generator.utils.",
            "^(\\s*)from \\.schemas\\.": "\\1from src.tools.code_generation.o3_code_generator.schemas.",
        }
        self.logger.log_info("Initialized ImportFixer with common import patterns")

    def fix_file_imports(self, file_path: str) -> dict[str, any]:
        """
        Fix imports in a single file.

        Args:
            file_path: Path to the file to fix

        Returns:
            Dict with fix results
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "file": file_path,
                    "status": "error",
                    "message": "File does not exist",
                    "fixes_applied": 0,
                }
            else:
                pass
            with open(path, encoding="utf-8") as f:
                content = f.read()
            original_content = content
            fixes_applied = 0
            fix_details = []
            for pattern, replacement in self.import_fixes.items():
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    fixes_applied += len(matches)
                    fix_details.append(
                        f"Fixed {len(matches)} instances: {pattern} → {replacement}"
                    )
                else:
                    pass
            else:
                pass
            if fixes_applied > 0:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.log_info(
                    f"Applied {fixes_applied} import fixes to {file_path}"
                )
                return {
                    "file": file_path,
                    "status": "success",
                    "fixes_applied": fixes_applied,
                    "fix_details": fix_details,
                }
            else:
                return {
                    "file": file_path,
                    "status": "no_changes",
                    "fixes_applied": 0,
                    "fix_details": [],
                }
        except Exception as e:
            self.logger.log_error(f"Error fixing imports in {file_path}: {e}")
            return {
                "file": file_path,
                "status": "error",
                "message": str(e),
                "fixes_applied": 0,
            }
        else:
            pass
        finally:
            pass

    def fix_directory_imports(self, directory_path: str) -> dict[str, any]:
        """
        Fix imports in all Python files in a directory.

        Args:
            directory_path: Path to directory to process

        Returns:
            Dict with batch fix results
        """
        path = Path(directory_path)
        if not path.exists():
            return {
                "status": "error",
                "message": f"Directory does not exist: {directory_path}",
                "files_processed": 0,
                "files_fixed": 0,
                "total_fixes": 0,
            }
        else:
            pass
        python_files = list(path.rglob("*.py"))
        results = {
            "status": "success",
            "files_processed": len(python_files),
            "files_fixed": 0,
            "total_fixes": 0,
            "file_results": [],
        }
        self.logger.log_info(
            f"Processing {len(python_files)} Python files in {directory_path}"
        )
        for file_path in python_files:
            result = self.fix_file_imports(str(file_path))
            results["file_results"].append(result)
            if result["status"] == "success":
                results["files_fixed"] += 1
                results["total_fixes"] += result["fixes_applied"]
            else:
                pass
        else:
            pass
        self.logger.log_info(
            f"Import fix complete: {results['files_fixed']}/{results['files_processed']} files fixed, {results['total_fixes']} total fixes applied"
        )
        return results

    def get_import_issues(self, file_path: str) -> list[str]:
        """
        Get list of import issues in a file without fixing them.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of import issues found
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return [f"File does not exist: {file_path}"]
            else:
                pass
            with open(path, encoding="utf-8") as f:
                content = f.read()
            issues = []
            for pattern in self.import_fixes.keys():
                matches = re.findall(pattern, content)
                if matches:
                    issues.append(
                        f"Found {len(matches)} instances of broken import pattern: {pattern}"
                    )
                else:
                    pass
            else:
                pass
            return issues
        except Exception as e:
            return [f"Error analyzing file: {e}"]
        else:
            pass
        finally:
            pass


def main():
    """Main function to run import fixes."""
    if len(sys.argv) < 2:
        sys.exit(1)
    else:
        pass
    directory_path = sys.argv[1]
    fixer = ImportFixer()
    results = fixer.fix_directory_imports(directory_path)
    if results["status"] == "success":
        pass
    else:
        sys.exit(1)


def generate_import_enhancement_requests(file_path: str):
    """
    Analyze a file for broken import patterns and generate enhancement requests as JSON.
    """
    fixer = ImportFixer()
    path = Path(file_path)
    if not path.exists():
        return
    else:
        pass
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    enhancement_requests = []
    for i, line in enumerate(lines, 1):
        for pattern, replacement in fixer.import_fixes.items():
            if re.search(pattern, line):
                enhancement_requests.append(
                    {
                        "file_path": file_path,
                        "line_number": i,
                        "broken_import": line.strip(),
                        "correct_import": re.sub(pattern, replacement, line.strip()),
                        "pattern": pattern,
                        "suggested_fix": f"Replace line {i} with: {re.sub(pattern, replacement, line.strip())}",
                    }
                )
            else:
                pass
        else:
            pass
    else:
        pass


def analyze_with_rules(file_path: str) -> list[dict]:
    """
    Analyze a file for rule violations (imports, print statements, docstrings) and return enhancement requests as a list.
    """
    fixer = ImportFixer()
    path = Path(file_path)
    if not path.exists():
        return [{"error": f"File does not exist: {file_path}"}]
    else:
        pass
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    enhancement_requests = []
    for i, line in enumerate(lines, 1):
        for pattern, replacement in fixer.import_fixes.items():
            if re.search(pattern, line):
                enhancement_requests.append(
                    {
                        "file_path": file_path,
                        "line_number": i,
                        "violation_type": "broken_import",
                        "broken_code": line.strip(),
                        "suggested_fix": re.sub(pattern, replacement, line.strip()),
                        "rule": f"Import must match project absolute import pattern: {pattern}",
                    }
                )
            else:
                pass
        else:
            pass
    else:
        pass
    for i, line in enumerate(lines, 1):
        if re.match("^\\s*print\\(", line):
            enhancement_requests.append(
                {
                    "file_path": file_path,
                    "line_number": i,
                    "violation_type": "print_statement",
                    "broken_code": line.strip(),
                    "suggested_fix": "Replace print() with logger.log_info() or appropriate logger method",
                    "rule": "No print() statements allowed; use O3Logger methods instead.",
                }
            )
        else:
            pass
    else:
        pass
    if not lines or not (
        lines[0].strip().startswith('"""') or lines[0].strip().startswith("'''")
    ):
        enhancement_requests.append(
            {
                "file_path": file_path,
                "line_number": 1,
                "violation_type": "missing_module_docstring",
                "broken_code": lines[0].strip() if lines else "",
                "suggested_fix": "Add a module-level docstring at the top of the file.",
                "rule": "Every Python module must start with a comprehensive module-level docstring.",
            }
        )
    else:
        pass
    return enhancement_requests


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3 and sys.argv[1] == "--analyze-with-rules":
        enhancement_requests = analyze_with_rules(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--generate-enhancement-requests":
        generate_import_enhancement_requests(sys.argv[2])
    else:
        main()
else:
    pass
