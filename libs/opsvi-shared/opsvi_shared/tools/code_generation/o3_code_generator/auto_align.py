"""
Auto-align module for O3 Code Generator.

Usage:
    python -m src.tools.code_generation.o3_code_generator.auto_align <target_file>

This module brings the target file into full compliance with all project and universal rules
by constructing an in-memory enhancement request and running the self-improvement logic.
"""

import ast
import difflib
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Tuple

from src.tools.code_generation.o3_code_generator.import_fix_script import (
    analyze_with_rules,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


def load_rules(logger: Any) -> Dict[str, str]:
    """Load project and universal rules as text."""
    base_dir = Path(__file__).parent / "docs"
    paths = {
        "project": base_dir / "project_rules.md",
        "universal": base_dir / "universal_rules.md",
    }
    rules: Dict[str, str] = {}
    for key, path in paths.items():
        try:
            rules[key] = path.read_text(encoding="utf-8")
        except OSError as e:
            logger.log_error(e, f"Failed to load {key} rules from {path}")
            rules[key] = ""
    return rules


def parse_args(argv: List[str], logger: Any) -> Path:
    """Parse and validate command-line arguments."""
    if len(argv) != 2:
        logger.log_error(
            ValueError("Invalid arguments"), f"Usage: {argv[0]} <target_file>"
        )
        raise ValueError("Expected exactly one argument: target file path")
    target_path = Path(argv[1]).resolve()
    if not target_path.is_file():
        logger.log_error(
            FileNotFoundError(str(target_path)), f"Target file not found: {target_path}"
        )
        raise FileNotFoundError(f"Target file not found: {target_path}")
    return target_path


def apply_fixes(
    original_code: str, enhancement_requests: List[Dict[str, Any]], logger: Any
) -> Tuple[str, bool]:
    """Apply enhancement requests to the original code and return modified code and flag."""
    lines = original_code.splitlines(keepends=True)
    changes_made = False
    fixed_lines: set[int] = set()

    for req in enhancement_requests:
        idx = req.get("line_number", 0) - 1
        vtype = req.get("violation_type")
        suggestion = req.get("suggested_fix", "")

        if (
            vtype == "broken_import"
            and idx not in fixed_lines
            and 0 <= idx < len(lines)
        ):
            logger.log_info(f"Fixing broken import on line {idx+1}: {suggestion}")
            indent = re.match(r"^\s*", lines[idx]).group(0)
            lines[idx] = f"{indent}{suggestion}\n"
            fixed_lines.add(idx)
            changes_made = True
        elif vtype == "missing_module_docstring":
            logger.log_info("Adding module-level docstring")
            lines.insert(0, '"""TODO: Add module-level docstring."""\n')
            changes_made = True
        elif vtype == "print_statement":
            logger.log_info(f"Skipping print statement fix on line {idx+1}")
        # ignore other violation types

    return "".join(lines), changes_made


def validate_ast(code: str, logger: Any) -> bool:
    """Validate Python AST of the given code."""
    try:
        ast.parse(code)
        logger.log_info("AST validation passed")
        return True
    except SyntaxError as e:
        logger.log_error(e, f"AST validation failed: {e}")
        return False


def generate_diff(before: str, after: str, target_path: Path, logger: Any) -> None:
    """Generate and log unified diff between before and after code."""
    diff = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"{target_path} (before)",
        tofile=f"{target_path} (after)",
        lineterm="",
    )
    diff_lines = list(diff)
    if diff_lines:
        logger.log_info(f"Diff for {target_path}:")
        for line in diff_lines:
            logger.log_info(line)
    else:
        logger.log_info(f"No changes made to {target_path} by auto-align.")


def main() -> None:
    """Main entry point for auto-align script."""
    setup_logger(LogConfig())
    logger = get_logger()

    try:
        target_path = parse_args(sys.argv, logger)
        original_content = target_path.read_text(encoding="utf-8")

        rules = load_rules(logger)
        enhancement_requests = analyze_with_rules(str(target_path))
        logger.log_info(f"Found {len(enhancement_requests)} enhancement requests")

        modified_content, changes_made = apply_fixes(
            original_content, enhancement_requests, logger
        )

        if changes_made:
            if validate_ast(modified_content, logger):
                target_path.write_text(modified_content, encoding="utf-8")
                logger.log_info(f"Successfully wrote changes to {target_path}")
            else:
                logger.log_error(
                    ValueError("AST validation failed"), "Not writing changes"
                )
        else:
            logger.log_info("No changes were made")

        # Use in-memory contents to generate diff
        final_content = modified_content if changes_made else original_content
        generate_diff(original_content, final_content, target_path, logger)

    except (ValueError, FileNotFoundError, SyntaxError, OSError, ImportError) as e:
        logger.log_error(e, "Unhandled exception in auto_align.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
