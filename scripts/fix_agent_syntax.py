#!/usr/bin/env python3
"""
Fix syntax errors in opsvi-agents library files.
This script automatically corrects common syntax issues in the agent library.
"""

import re
from pathlib import Path


def fix_init_file(file_path):
    """Fix syntax errors in __init__.py files."""
    with open(file_path) as f:
        content = f.read()

    original_content = content

    # Fix empty class names
    content = re.sub(r"class\s+\(", "class BaseAgent(", content)

    # Fix empty imports
    content = re.sub(r"from\s+\.[\w.]+\s+import\s*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"from\s+\.[\w.]+\s+import\s+,", "", content)

    # Fix trailing commas in __all__
    content = re.sub(r",\s*,", ",", content)
    content = re.sub(r",\s*\]", "]", content)

    # Remove template placeholders
    content = re.sub(r"\{\{[\w_]+\}\}", "", content)

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    return False


def fix_base_file(file_path):
    """Fix syntax errors in base.py files."""
    with open(file_path) as f:
        content = f.read()

    original_content = content

    # Fix class definitions with missing names
    content = re.sub(
        r"class\s+\(BaseComponent\):", "class BaseAgent(BaseComponent):", content
    )

    # Fix empty configuration items
    content = re.sub(
        r"# Component-specific configuration\s*\n\s*\n",
        "# Component-specific configuration\n    max_retries: int = 3\n    timeout: int = 30\n\n",
        content,
    )

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    return False


def main():
    """Main function to fix all syntax errors."""
    libs_path = Path("libs")
    fixed_files = []

    # Fix opsvi-agents
    agents_path = libs_path / "opsvi-agents" / "opsvi_agents"
    if agents_path.exists():
        # Fix __init__.py files
        for init_file in agents_path.rglob("__init__.py"):
            if fix_init_file(init_file):
                fixed_files.append(str(init_file))

        # Fix base.py files
        for base_file in agents_path.rglob("base.py"):
            if fix_base_file(base_file):
                fixed_files.append(str(base_file))

    # Report results
    if fixed_files:
        print(f"✅ Fixed {len(fixed_files)} files:")
        for f in fixed_files:
            print(f"  - {f}")
    else:
        print("✅ No syntax errors found or all already fixed.")

    return 0


if __name__ == "__main__":
    exit(main())
