#!/usr/bin/env python3
"""
Fix Remaining Syntax Errors Script
==================================

Fixes all remaining syntax errors from malformed imports and invalid statements
"""

import re
from pathlib import Path


def fix_all_syntax_errors():
    """Fix all remaining syntax errors"""
    oamat_path = Path("src/applications/oamat_sd")

    fixes_applied = 0

    # Define patterns to fix
    fixes = [
        # Fix malformed imports with ConfigManager().
        (
            r"from src\.applications\.oamat_sd\.src\.ConfigManager\(\)\.config_manager import \(",
            "from src.applications.oamat_sd.src.config.config_manager import (",
        ),
        (
            r"from src\.applications\.oamat_sd\.src\.ConfigManager\(\)\.dynamic_config_generator import \(",
            "from src.applications.oamat_sd.src.config.dynamic_config_generator import (",
        ),
        # Fix malformed return statements with "for type-specific research"
        (
            r"return ConfigManager\(\)\.analysis\.confidence\.very_high_confidence for type-specific research",
            "return ConfigManager().analysis.confidence.very_high_confidence  # for type-specific research",
        ),
        (
            r"return ConfigManager\(\)\.analysis\.confidence\.default_confidence for default research",
            "return ConfigManager().analysis.confidence.default_confidence  # for default research",
        ),
        # Fix console_interface.py import error
        (
            r"TimeElapsedColumn,\nfrom src\.applications\.oamat_sd\.src\.config\.config_manager import ConfigManager\n\)",
            "TimeElapsedColumn,\n)\nfrom src.applications.oamat_sd.src.config.config_manager import ConfigManager",
        ),
    ]

    for py_file in oamat_path.rglob("*.py"):
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Apply all fixes
            for pattern, replacement in fixes:
                content = re.sub(pattern, replacement, content)

            # Write back if changed
            if content != original_content:
                with open(py_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print(
                    f"✅ Fixed syntax errors in {py_file.relative_to(Path('src/applications/oamat_sd').parent.parent)}"
                )
                fixes_applied += 1

        except Exception as e:
            print(f"❌ Error processing {py_file}: {e}")

    print(f"\n📊 Fixed {fixes_applied} files with syntax errors")


if __name__ == "__main__":
    fix_all_syntax_errors()
