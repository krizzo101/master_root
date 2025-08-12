"""
Dynamic Alignment Scanner for O3 Code Generator

Scans the codebase to identify files that need auto-alignment based on
dynamically loaded rules from project_rules.md. No more hardcoded patterns!
"""

import json
from pathlib import Path
from typing import Any

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)
from src.tools.code_generation.o3_code_generator.rule_engine import RuleExecutor
from src.tools.code_generation.o3_code_generator.rule_parser import (
    RuleParser,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)


class DynamicAlignmentScanner:
    """
    Scans codebase for alignment issues using dynamic rules from project_rules.md.

    This scanner automatically loads rules from the project_rules.md file,
    eliminating the need to modify code when rules change.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize the dynamic alignment scanner.

        Args:
            base_path: Base path to scan. Defaults to o3_code_generator directory.
        """
        try:
            self.logger = get_logger()
        except RuntimeError:
            # Logger not initialized, set it up for this instance
            setup_logger(LogConfig())
            self.logger = get_logger()

        self.base_path: Path = base_path or Path(
            "src/tools/code_generation/o3_code_generator"
        )

        # Load rules dynamically
        self.rule_parser = RuleParser()
        self.rule_config = self.rule_parser.parse_rules()
        self.rule_executor = RuleExecutor(self.rule_config)

        # Convert ignore_dirs to set for faster lookup
        self.ignore_dirs: set[str] = set(self.rule_config.ignore_dirs)

        self.logger.log_info(
            f"Initialized DynamicAlignmentScanner for path: {self.base_path}"
        )
        self.logger.log_info(f"Loaded {len(self.rule_config.rules)} rules dynamically")

    def _should_ignore_path(self, path: Path) -> bool:
        """
        Determine if a given path should be ignored.

        Args:
            path: Path to check.

        Returns:
            True if path is in ignore list; False otherwise.
        """
        return any(part in self.ignore_dirs for part in path.parts)

    def _scan_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Scan a single file for alignment issues.

        Args:
            file_path: Path to the file to scan.

        Returns:
            Dictionary containing scan results with broken_imports, rule_violations, and ast_issues.
        """
        path = Path(file_path)
        violations = self.rule_executor.check_file(path)

        # Add needs_alignment flag for compatibility with ValidationFramework
        has_issues = (
            bool(violations.get("broken_imports"))
            or bool(violations.get("rule_violations"))
            or bool(violations.get("ast_issues"))
        )
        violations["needs_alignment"] = has_issues

        return violations

    def scan_codebase(self) -> dict[str, Any]:
        """
        Scan the entire codebase for alignment issues.

        Returns:
            Dictionary containing scan results and statistics.
        """
        self.logger.log_info("Starting codebase alignment scan...")

        # Find all Python files
        all_files = list(self.base_path.rglob("*.py"))
        self.logger.log_info(f"Found {len(all_files)} Python files")

        # Filter out ignored paths
        python_files = [f for f in all_files if not self._should_ignore_path(f)]
        self.logger.log_info(
            f"{len(python_files)} files after filtering ignored directories"
        )

        files_needing_alignment = []
        files_with_broken_imports = 0
        files_with_rule_violations = 0

        for file_path in python_files:
            violations = self.rule_executor.check_file(file_path)

            # Skip files with read errors
            if "error" in violations:
                self.logger.log_error(
                    None, f"Error checking {file_path}: {violations['error']}"
                )
                continue

            # Check if file has any violations
            has_broken_imports = len(violations["broken_imports"]) > 0
            has_rule_violations = len(violations["rule_violations"]) > 0
            has_ast_issues = len(violations["ast_issues"]) > 0

            if has_broken_imports or has_rule_violations or has_ast_issues:
                files_needing_alignment.append(
                    {"file": str(file_path), "issues": violations}
                )

                if has_broken_imports:
                    files_with_broken_imports += 1
                if has_rule_violations or has_ast_issues:
                    files_with_rule_violations += 1

        total_files = len(python_files)
        files_needing_alignment_count = len(files_needing_alignment)
        alignment_percentage = (
            (total_files - files_needing_alignment_count) / total_files * 100
            if total_files > 0
            else 100
        )

        self.logger.log_info(
            f"Scan complete: {files_needing_alignment_count} files need alignment"
        )

        return {
            "summary": {
                "total_files": total_files,
                "files_needing_alignment": files_needing_alignment_count,
                "files_with_broken_imports": files_with_broken_imports,
                "files_with_rule_violations": files_with_rule_violations,
                "alignment_percentage": round(alignment_percentage, 2),
            },
            "files_needing_alignment": files_needing_alignment,
            "rules_used": {
                "total_rules": len(self.rule_config.rules),
                "regex_rules": len(
                    [r for r in self.rule_config.rules if r.type == "regex"]
                ),
                "ast_rules": len(
                    [r for r in self.rule_config.rules if r.type == "ast"]
                ),
                "broken_import_patterns": len(self.rule_config.broken_imports),
            },
        }

    def generate_alignment_report(self, scan_results: dict[str, Any]) -> str:
        """
        Generate a human-readable alignment report.

        Args:
            scan_results: Results from scan_codebase().

        Returns:
            Formatted report string.
        """
        summary = scan_results["summary"]
        files_needing_alignment = scan_results["files_needing_alignment"]
        rules_used = scan_results["rules_used"]

        report = "=" * 80 + "\n"
        report += "DYNAMIC ALIGNMENT SCANNER REPORT\n"
        report += "=" * 80 + "\n\n"

        # Summary section
        report += "📊 SUMMARY:\n"
        report += f"   Total files scanned: {summary['total_files']}\n"
        report += f"   Files needing alignment: {summary['files_needing_alignment']}\n"
        report += (
            f"   Files with broken imports: {summary['files_with_broken_imports']}\n"
        )
        report += (
            f"   Files with rule violations: {summary['files_with_rule_violations']}\n"
        )
        report += f"   Alignment percentage: {summary['alignment_percentage']}%\n\n"

        # Rules used section
        report += "🔧 RULES CONFIGURATION:\n"
        report += f"   Total rules loaded: {rules_used['total_rules']}\n"
        report += f"   Regex rules: {rules_used['regex_rules']}\n"
        report += f"   AST rules: {rules_used['ast_rules']}\n"
        report += (
            f"   Broken import patterns: {rules_used['broken_import_patterns']}\n\n"
        )

        if files_needing_alignment:
            report += "🔧 FILES NEEDING ALIGNMENT:\n"
            report += "-" * 40 + "\n\n"

            for file_info in files_needing_alignment:
                file_path = file_info["file"]
                issues = file_info["issues"]

                report += f"📁 {file_path}\n"

                # Broken imports
                if issues.get("broken_imports"):
                    report += "   ❌ Broken imports:\n"
                    for imp in issues["broken_imports"]:
                        report += f"      Line {imp['line']}: {imp['pattern']}\n"

                # Rule violations
                if issues.get("rule_violations"):
                    report += "   ⚠️  Rule violations:\n"
                    for violation in issues["rule_violations"]:
                        report += (
                            f"      Line {violation['line']}: {violation['rule']}\n"
                        )

                # AST issues
                if issues.get("ast_issues"):
                    report += "   🔍 AST issues:\n"
                    for ast_issue in issues["ast_issues"]:
                        report += (
                            f"      Line {ast_issue['line']}: {ast_issue['type']}\n"
                        )

                report += "\n"
        else:
            report += "✅ All files are properly aligned!\n"

        report += "=" * 80 + "\n"
        return report

    def save_scan_results(self, scan_results: dict[str, Any]) -> Path:
        """
        Save scan results to JSON file.

        Args:
            scan_results: Results from scan_codebase().

        Returns:
            Path to saved results file.
        """
        output_formatter = OutputFormatter()
        file_generator = FileGenerator()

        output_path = self.base_path / "dynamic_alignment_scan_results.json"

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(scan_results, f, indent=2, ensure_ascii=False)

            self.logger.log_info(f"Scan results saved to: {output_path}")
            return output_path

        except Exception as e:
            self.logger.log_error(e, f"Failed to save scan results to {output_path}")
            raise

    def reload_rules(self) -> None:
        """Reload rules from project_rules.md without restarting the scanner."""
        self.logger.log_info("Reloading rules from project_rules.md...")

        try:
            # Parse rules again
            self.rule_config = self.rule_parser.parse_rules()

            # Create new executor with updated rules
            self.rule_executor = RuleExecutor(self.rule_config)

            # Update ignore directories
            self.ignore_dirs = set(self.rule_config.ignore_dirs)

            self.logger.log_info(
                f"Successfully reloaded {len(self.rule_config.rules)} rules"
            )

        except Exception as e:
            self.logger.log_error(e, "Failed to reload rules")
            raise

    def get_rule_summary(self) -> dict[str, Any]:
        """Get a summary of currently loaded rules."""
        return {
            "total_rules": len(self.rule_config.rules),
            "rules_by_type": {
                "regex": len([r for r in self.rule_config.rules if r.type == "regex"]),
                "ast": len([r for r in self.rule_config.rules if r.type == "ast"]),
            },
            "rules_by_category": {},
            "broken_import_patterns": len(self.rule_config.broken_imports),
            "ignore_directories": len(self.rule_config.ignore_dirs),
        }


def main() -> int:
    """Main function for running the dynamic alignment scanner."""
    scanner = DynamicAlignmentScanner()

    print("🚀 Running Dynamic Alignment Scanner...")
    print(f"📋 Rule Summary: {scanner.get_rule_summary()}")
    print()

    # Run scan
    results = scanner.scan_codebase()

    # Generate and display report
    report = scanner.generate_alignment_report(results)
    print(report)

    # Save results
    output_path = scanner.save_scan_results(results)
    print(f"📄 Detailed results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    setup_logger(LogConfig())
    raise SystemExit(main())
