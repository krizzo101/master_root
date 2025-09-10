#!/usr/bin/env python3
"""Fix imports in DPO to use agent-orchestrator properly"""

import os
import re
from pathlib import Path


def fix_imports(file_path):
    """Fix imports in a single file"""
    with open(file_path, "r") as f:
        content = f.read()

    # Pattern to replace
    patterns = [
        (r"from \.generic_orchestrator import", "from generic_orchestrator import"),
        (r"from src\.generic_orchestrator import", "from generic_orchestrator import"),
    ]

    modified = False
    for old_pattern, new_pattern in patterns:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_pattern, content)
            modified = True

    # Add sys.path if generic_orchestrator import exists and sys.path not already added
    if (
        "from generic_orchestrator import" in content
        and "/apps/agent-orchestrator/src" not in content
    ):
        # Find the import line
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "from generic_orchestrator import" in line:
                # Add sys.path before this import
                sys_path_code = """import sys
sys.path.insert(0, '/home/opsvi/master_root/apps/agent-orchestrator/src')
"""
                lines[i] = sys_path_code + line
                content = "\n".join(lines)
                modified = True
                break

    if modified:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Fixed: {file_path}")

    return modified


# Fix all Python files in src/
src_dir = Path("/home/opsvi/master_root/apps/dpo/src")
for py_file in src_dir.rglob("*.py"):
    fix_imports(py_file)

print("Import fixes complete!")
