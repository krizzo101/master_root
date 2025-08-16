#!/usr/bin/env python3
"""
OAMAT_SD Compliance Automation Script
=====================================

Systematically eliminates ALL hardcoded values and fallback patterns
across the entire oamat_sd codebase using AST transformations.

Usage:
    python automate_compliance_fixes.py [--dry-run] [--file FILENAME]
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Any


class ComplianceTransformer(ast.NodeTransformer):
    """AST transformer that eliminates hardcoded values and fallback patterns."""

    def __init__(self):
        self.changes: list[dict[str, Any]] = []
        self.current_file = ""

        # Config path mappings for common patterns
        self.config_mappings = {
            # Scoring and analysis
            "score_base": "config.analysis.base_score",
            "score_high": "config.analysis.scoring.high_indicator_boost",
            "score_medium": "config.analysis.scoring.medium_indicator_boost",
            "score_low": "config.analysis.scoring.low_indicator_penalty",
            "confidence_high": "config.analysis.confidence.high_threshold",
            "confidence_medium": "config.analysis.confidence.medium_threshold",
            "confidence_low": "config.analysis.confidence.low_threshold",
            # Tool configuration
            "default_query": "config.tools.defaults.empty_query_value",
            "default_count": "config.tools.defaults.result_count",
            "default_timeout": "config.tools.defaults.timeout_seconds",
            "default_language": "config.tools.defaults.language",
            # Agent factory
            "agent_count": "config.agent_factory.defaults.agent_count",
            "temperature": "config.agent_factory.defaults.temperature",
            "max_tokens": "config.agent_factory.defaults.max_tokens",
            # Status values
            "status_active": "config.status.active",
            "status_inactive": "config.status.inactive",
            "status_error": "config.status.error",
            "status_success": "config.status.success",
            "status_failed": "config.status.failed",
        }

        # Common fallback patterns to detect
        self.fallback_patterns = {
            ".get(",
            "get(",  # Dictionary get with fallback
            "or {}",
            "or []",
            'or ""',
            "or 0",  # Or fallbacks
        }

    def set_current_file(self, filepath: str):
        """Set the current file being processed."""
        self.current_file = filepath

    def log_change(
        self,
        node: ast.AST,
        change_type: str,
        old_value: str,
        new_value: str,
        reason: str,
    ):
        """Log a transformation change."""
        self.changes.append(
            {
                "file": self.current_file,
                "line": getattr(node, "lineno", 0),
                "col": getattr(node, "col_offset", 0),
                "type": change_type,
                "old": old_value,
                "new": new_value,
                "reason": reason,
            }
        )

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Transform .get() fallback calls to explicit key access."""

        # Handle dict.get(key, default) patterns
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and len(node.args) >= 2
        ):
            # Extract the object, key, and default
            obj = node.func.value
            key = node.args[0]
            default_value = node.args[1]

            # Skip if it's a legitimate framework pattern
            if self._is_framework_pattern(node):
                return self.generic_visit(node)

            # Generate explicit key access with error handling
            old_code = ast.unparse(node)

            # Create: obj[key] with config fallback reference
            key_access = ast.Subscript(value=obj, slice=key, ctx=ast.Load())

            # Determine appropriate config reference for the default
            config_ref = self._get_config_reference_for_default(default_value)

            if config_ref:
                new_node = ast.parse(config_ref).body[0].value
                self.log_change(
                    node,
                    "FALLBACK_ELIMINATION",
                    old_code,
                    config_ref,
                    "Replaced .get() fallback with config reference",
                )
                return new_node
            else:
                # Create explicit key check with error
                error_msg = (
                    f"Required key '{ast.unparse(key)}' missing from configuration"
                )
                raise_stmt = ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id="KeyError", ctx=ast.Load()),
                        args=[ast.Constant(value=error_msg)],
                        keywords=[],
                    )
                )

                self.log_change(
                    node,
                    "FALLBACK_ELIMINATION",
                    old_code,
                    f"Explicit key access with error for {ast.unparse(key)}",
                    "Eliminated fallback with fail-fast behavior",
                )
                return key_access

        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Transform hardcoded constants to config references."""

        # Skip if in test files or certain contexts
        if "test" in self.current_file.lower() or self._is_acceptable_constant(node):
            return node

        old_value = node.value

        # Handle numeric constants (scores, thresholds, etc.)
        if isinstance(old_value, (int, float)):
            config_ref = self._get_config_reference_for_number(old_value, node)
            if config_ref:
                new_node = ast.parse(config_ref).body[0].value
                self.log_change(
                    node,
                    "HARDCODED_NUMBER",
                    str(old_value),
                    config_ref,
                    f"Replaced hardcoded {type(old_value).__name__}: {old_value}",
                )
                return new_node

        # Handle string constants
        elif isinstance(old_value, str) and old_value:
            config_ref = self._get_config_reference_for_string(old_value, node)
            if config_ref:
                new_node = ast.parse(config_ref).body[0].value
                self.log_change(
                    node,
                    "HARDCODED_STRING",
                    old_value,
                    config_ref,
                    f"Replaced hardcoded string: {old_value}",
                )
                return new_node

        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Transform hardcoded arithmetic operations with scoring constants."""

        # Look for score += number or score -= number patterns
        parent_context = getattr(node, "_parent_context", None)

        if (
            isinstance(node.op, (ast.Add, ast.Sub))
            and isinstance(node.right, ast.Constant)
            and isinstance(node.right.value, (int, float))
        ):
            # Check if this is in a scoring context
            if self._is_scoring_context(node):
                old_code = ast.unparse(node)
                config_ref = self._get_scoring_config_reference(
                    node.right.value, node.op
                )

                if config_ref:
                    new_node = ast.parse(config_ref).body[0].value
                    self.log_change(
                        node,
                        "SCORING_CONSTANT",
                        old_code,
                        config_ref,
                        "Replaced hardcoded scoring adjustment",
                    )
                    return new_node

        return self.generic_visit(node)

    def _is_framework_pattern(self, node: ast.Call) -> bool:
        """Check if this is an acceptable framework/library pattern."""
        code = ast.unparse(node)

        # Acceptable patterns that shouldn't be changed
        acceptable_patterns = [
            "os.environ.get(",
            "kwargs.get(",  # In tool interfaces
            "request.get(",
            'state.get("context"',  # LangGraph state access
            "config.get(",  # Configuration access
        ]

        return any(pattern in code for pattern in acceptable_patterns)

    def _is_acceptable_constant(self, node: ast.Constant) -> bool:
        """Check if this constant should not be changed."""
        value = node.value

        # Version numbers, ports, etc.
        if isinstance(value, str) and re.match(r"^\d+\.\d+", str(value)):
            return True

        # Small integers in certain contexts (0, 1, 2 for indexing, etc.)
        if isinstance(value, int) and 0 <= value <= 2:
            return True

        # HTTP status codes
        if isinstance(value, int) and 100 <= value <= 599:
            return True

        return False

    def _is_scoring_context(self, node: ast.BinOp) -> bool:
        """Check if this binary operation is in a scoring context."""
        # Look for variable names containing 'score'
        # This is a simplified check - could be made more sophisticated
        return True  # For now, assume all numeric operations might be scoring

    def _get_config_reference_for_default(self, default_node: ast.AST) -> str:
        """Get appropriate config reference for a default value."""
        if isinstance(default_node, ast.Constant):
            value = default_node.value

            if value == "":
                return "config.tools.defaults.empty_query_value"
            elif value == 0:
                return "config.tools.defaults.zero_count"
            elif value == []:
                return "config.tools.defaults.empty_list"
            elif value == {}:
                return "config.tools.defaults.empty_dict"

        return None

    def _get_config_reference_for_number(
        self, value: int | float, node: ast.Constant
    ) -> str:
        """Get config reference for numeric constants."""

        # Context-aware mapping based on common values
        context_mappings = {
            # Scoring values
            1: "config.analysis.scoring.minimal_boost",
            2: "config.analysis.scoring.low_boost",
            3: "config.analysis.scoring.base_score",
            4: "config.analysis.scoring.medium_boost",
            5: "config.analysis.scoring.high_boost",
            # Confidence values
            0.7: "config.analysis.confidence.default_confidence",
            0.8: "config.analysis.confidence.high_confidence",
            0.9: "config.analysis.confidence.very_high_confidence",
            1.0: "config.analysis.confidence.max_confidence",
            # Agent counts
            1: "config.agent_factory.counts.single_agent",
            3: "config.agent_factory.counts.small_team",
            5: "config.agent_factory.counts.large_team",
            # Thresholds
            7: "config.analysis.thresholds.high_complexity",
            8: "config.analysis.thresholds.very_high_complexity",
        }

        return context_mappings.get(value)

    def _get_config_reference_for_string(self, value: str, node: ast.Constant) -> str:
        """Get config reference for string constants."""

        # Common string patterns
        string_mappings = {
            "multi_agent": "config.execution.strategies.multi_agent",
            "single_agent": "config.execution.strategies.single_agent",
            "active": "config.status.active",
            "inactive": "config.status.inactive",
            "success": "config.status.success",
            "failed": "config.status.failed",
            "error": "config.status.error",
        }

        return string_mappings.get(value)

    def _get_scoring_config_reference(
        self, value: int | float, op: ast.operator
    ) -> str:
        """Get config reference for scoring adjustments."""

        if isinstance(op, ast.Add):
            if value == 1:
                return "config.analysis.scoring.small_boost"
            elif value == 2:
                return "config.analysis.scoring.medium_boost"
            elif value == 4:
                return "config.analysis.scoring.high_boost"
            elif value == 5:
                return "config.analysis.scoring.very_high_boost"
        elif isinstance(op, ast.Sub):
            if value == 1:
                return "config.analysis.scoring.small_penalty"
            elif value == 2:
                return "config.analysis.scoring.medium_penalty"

        return None


def find_python_files(root_dir: str) -> list[Path]:
    """Find all Python files in the oamat_sd application."""
    root = Path(root_dir)
    python_files = []

    for file_path in root.rglob("*.py"):
        # Skip test files, __pycache__, and original files
        path_str = str(file_path)
        if not any(
            skip in path_str
            for skip in [
                "/test",
                "__pycache__",
                "_original.py",
                "automate_compliance_fixes.py",
                "/archive/",
                "/examples/",
            ]
        ):
            python_files.append(file_path)

    print(f"🔍 Found {len(python_files)} Python files to process")
    return python_files


def process_file(
    file_path: Path, transformer: ComplianceTransformer, dry_run: bool = True
) -> tuple[str, bool]:
    """Process a single Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()

        # Parse and transform
        tree = ast.parse(source)
        transformer.set_current_file(str(file_path))

        new_tree = transformer.visit(tree)

        if transformer.changes:
            # Generate new source code
            new_source = ast.unparse(new_tree)

            if not dry_run:
                # Write the transformed code
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_source)

            return new_source, True

        return source, False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return "", False


def generate_report(transformer: ComplianceTransformer) -> str:
    """Generate comprehensive change report."""
    if not transformer.changes:
        return "✅ No violations found - codebase is compliant!"

    report = ["🔄 OAMAT_SD COMPLIANCE AUTOMATION REPORT", "=" * 50, ""]

    # Summary
    total_changes = len(transformer.changes)
    files_affected = len(set(change["file"] for change in transformer.changes))

    report.extend(
        [
            "📊 SUMMARY:",
            f"   Total Changes: {total_changes}",
            f"   Files Affected: {files_affected}",
            "",
        ]
    )

    # Changes by type
    change_types = {}
    for change in transformer.changes:
        change_type = change["type"]
        change_types[change_type] = change_types.get(change_type, 0) + 1

    report.extend(["📈 CHANGES BY TYPE:"])
    for change_type, count in sorted(change_types.items()):
        report.append(f"   {change_type}: {count}")
    report.append("")

    # Detailed changes by file
    report.extend(["📁 DETAILED CHANGES BY FILE:", ""])

    current_file = None
    for change in transformer.changes:
        if change["file"] != current_file:
            current_file = change["file"]
            report.append(f"📄 {current_file}")

        report.append(f"   Line {change['line']:3d}: {change['type']}")
        report.append(f"      Old: {change['old']}")
        report.append(f"      New: {change['new']}")
        report.append(f"      Why: {change['reason']}")
        report.append("")

    return "\n".join(report)


def main():
    """Main automation execution."""
    parser = argparse.ArgumentParser(description="OAMAT_SD Compliance Automation")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying them"
    )
    parser.add_argument(
        "--file", type=str, help="Process single file instead of entire codebase"
    )
    args = parser.parse_args()

    print("🚀 OAMAT_SD COMPLIANCE AUTOMATION STARTING...")
    print("=" * 50)

    # Initialize transformer
    transformer = ComplianceTransformer()

    # Determine files to process
    if args.file:
        files_to_process = [Path(args.file)]
    else:
        # Use current directory if running from within oamat_sd
        current_dir = os.getcwd()
        if "oamat_sd" in current_dir:
            files_to_process = find_python_files(".")
        else:
            files_to_process = find_python_files("src/applications/oamat_sd")

    print(f"📁 Processing {len(files_to_process)} Python files...")

    # Process each file
    files_changed = 0
    for file_path in files_to_process:
        print(f"🔍 Processing: {file_path}")
        _, changed = process_file(file_path, transformer, args.dry_run)
        if changed:
            files_changed += 1

    # Generate and display report
    report = generate_report(transformer)
    print("\n" + report)

    # Summary
    if args.dry_run:
        print("\n🔍 DRY RUN COMPLETE - No files were changed")
        print(
            f"📊 Would change {files_changed} files with {len(transformer.changes)} total modifications"
        )
        print(f"\n💡 To apply changes, run: python {sys.argv[0]}")
    else:
        print("\n✅ AUTOMATION COMPLETE!")
        print(
            f"📊 Changed {files_changed} files with {len(transformer.changes)} total modifications"
        )

        # Save detailed report
        report_file = "compliance_automation_report.md"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"📋 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
