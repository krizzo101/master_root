"""
🔍 Project Structure Compliance Checker
Based on PROJECT_STRUCTURE_QUICK_REF.md guidelines

Checks for violations of the project structure rules:
- No Python files (*.py) in root
- No JSON artifacts (*.json) in root
- No log files (*.log) in root
- Only approved config files allowed in root
"""

import os
from pathlib import Path


def check_compliance():
    """Check project root for structure violations"""
    violations = []
    root_path = Path(".")
    python_files = list(root_path.glob("*.py"))
    if python_files:
        violations.extend([("Python file", str(f)) for f in python_files])
    else:
        pass
    json_files = list(root_path.glob("*.json"))
    if json_files:
        violations.extend([("JSON file", str(f)) for f in json_files])
    else:
        pass
    log_files = list(root_path.glob("*.log"))
    if log_files:
        violations.extend([("Log file", str(f)) for f in log_files])
    else:
        pass
    hidden_json = list(root_path.glob(".*.json"))
    if hidden_json:
        violations.extend([("Hidden JSON file", str(f)) for f in hidden_json])
    else:
        pass
    allowed_files = {
        "README.md",
        "docker-compose.yml",
        ".gitignore",
        ".editorconfig",
        "package.json",
        "Makefile",
        "LICENSE",
        "CONTRIBUTING.md",
        "Dockerfile",
        "env.example",
        ".pre-commit-config.yaml",
    }
    workspace_files = list(root_path.glob("*.code-workspace"))
    allowed_files.update(str(f.name) for f in workspace_files)
    if violations:
        for violation_type, file_path in violations:
            pass
        else:
            pass
        return False
    else:
        root_files = [f for f in os.listdir(".") if os.path.isfile(f)]
        for file in sorted(root_files):
            if file in allowed_files or file.startswith("."):
                pass
            else:
                pass
        else:
            pass
        return True


def show_structure_summary():
    """Show summary of organized structure"""
    directories = {
        "src/applications/": "Production applications",
        "src/shared/": "Shared utilities and frameworks",
        "src/tools/": "Development and maintenance tools",
        "data/artifacts/": "JSON artifacts and analysis results",
        "docs/": "All documentation",
        "config/": "Configuration files",
        "archive/": "Archived and deprecated content",
    }
    for directory, description in directories.items():
        if os.path.exists(directory):
            file_count = sum((len(files) for _, _, files in os.walk(directory)))
        else:
            pass
    else:
        pass


if __name__ == "__main__":
    compliance = check_compliance()
    show_structure_summary()
    if compliance:
        exit(0)
    else:
        pass
        exit(1)
else:
    pass
