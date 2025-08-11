#!/usr/bin/env python3
"""
Logging Enhancement Utility for Autonomous Systems

This utility systematically adds comprehensive logging to all autonomous systems scripts
that don't already have proper logging. It analyzes scripts, identifies logging needs,
and implements consistent logging patterns.

Features:
- Automatic detection of scripts needing logging enhancement
- Pattern-based logging insertion
- Backup creation before modification
- Validation of logging implementation
- Batch processing of multiple scripts
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple
import ast
import subprocess
from datetime import datetime

from core_systems.comprehensive_logging_config import get_logger


class LoggingEnhancer:
    """
    Utility to systematically add comprehensive logging to Python scripts.
    """

    def __init__(self, base_directory: str):
        """
        Initialize the logging enhancer.

        Args:
            base_directory: Base directory to scan for scripts
        """
        self.base_directory = Path(base_directory)
        self.logger = get_logger("logging_enhancer", log_level="DEBUG")
        self.log = self.logger.get_logger()

        # Patterns to identify logging needs
        self.logging_indicators = {
            "import logging",
            "logger =",
            "log.info",
            "log.debug",
            "log.error",
            "log.warning",
            'print(f"❌',
            'print(f"✅',
            "except Exception as",
            "try:",
            "async def",
            "def __init__",
            "class ",
            "API",
            "client",
            "database",
            "error",
            "failed",
            "success",
        }

        # Files to skip (already have good logging or are test files)
        self.skip_files = {
            "comprehensive_logging_config.py",
            "autonomous_openai_client_fixed.py",
            "external_reasoning_service.py",
            "knowledge_context_gatherer.py",
            "__init__.py",
            "test_",
            "_test.py",
            "debug_",
        }

    def scan_directory(self) -> List[Dict[str, any]]:
        """
        Scan directory for Python scripts that need logging enhancement.

        Returns:
            List of script analysis results
        """
        correlation_id = self.logger.start_operation(
            "scan_directory", {"base_directory": str(self.base_directory)}
        )

        try:
            scripts = []

            for py_file in self.base_directory.rglob("*.py"):
                if self._should_skip_file(py_file):
                    continue

                analysis = self._analyze_script(py_file)
                if analysis["needs_enhancement"]:
                    scripts.append(analysis)

            self.log.info(f"Found {len(scripts)} scripts needing logging enhancement")

            self.logger.end_operation(
                correlation_id,
                success=True,
                result_context={"scripts_found": len(scripts)},
            )

            return scripts

        except Exception as e:
            self.logger.log_error_with_context(
                e, {"base_directory": str(self.base_directory)}, correlation_id
            )
            self.logger.end_operation(correlation_id, success=False)
            raise

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        file_name = file_path.name

        # Skip files in skip list
        for skip_pattern in self.skip_files:
            if skip_pattern in file_name:
                return True

        # Skip very small files (likely not significant)
        try:
            if file_path.stat().st_size < 500:
                return True
        except:
            return True

        return False

    def _analyze_script(self, file_path: Path) -> Dict[str, any]:
        """
        Analyze a script to determine logging enhancement needs.

        Args:
            file_path: Path to the script

        Returns:
            Analysis results dictionary
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            analysis = {
                "file_path": file_path,
                "file_name": file_path.name,
                "size": len(content),
                "lines": len(content.splitlines()),
                "has_logging": False,
                "has_error_handling": False,
                "has_async_functions": False,
                "has_classes": False,
                "has_api_calls": False,
                "complexity_score": 0,
                "needs_enhancement": False,
                "enhancement_priority": "low",
            }

            # Check for existing logging
            if any(
                pattern in content
                for pattern in ["import logging", "logger =", "log.info", "log.debug"]
            ):
                analysis["has_logging"] = True

            # Check for error handling
            if "except Exception" in content or "try:" in content:
                analysis["has_error_handling"] = True
                analysis["complexity_score"] += 2

            # Check for async functions
            if "async def" in content:
                analysis["has_async_functions"] = True
                analysis["complexity_score"] += 1

            # Check for classes
            if re.search(r"^class\s+\w+", content, re.MULTILINE):
                analysis["has_classes"] = True
                analysis["complexity_score"] += 1

            # Check for API calls
            api_indicators = [
                "client",
                "api",
                "request",
                "response",
                "http",
                "openai",
                "arango",
            ]
            if any(indicator in content.lower() for indicator in api_indicators):
                analysis["has_api_calls"] = True
                analysis["complexity_score"] += 2

            # Count functions and methods
            function_count = len(re.findall(r"def\s+\w+", content))
            analysis["function_count"] = function_count
            analysis["complexity_score"] += function_count // 5

            # Determine if enhancement is needed
            if not analysis["has_logging"] and analysis["complexity_score"] > 2:
                analysis["needs_enhancement"] = True

                # Determine priority
                if analysis["complexity_score"] > 5 or analysis["has_api_calls"]:
                    analysis["enhancement_priority"] = "high"
                elif analysis["complexity_score"] > 3:
                    analysis["enhancement_priority"] = "medium"

            return analysis

        except Exception as e:
            self.log.error(f"Failed to analyze {file_path}: {e}")
            return {
                "file_path": file_path,
                "file_name": file_path.name,
                "error": str(e),
                "needs_enhancement": False,
            }

    def enhance_script(
        self, script_analysis: Dict[str, any], backup: bool = True
    ) -> bool:
        """
        Enhance a script with comprehensive logging.

        Args:
            script_analysis: Analysis results from _analyze_script
            backup: Whether to create backup before modification

        Returns:
            True if enhancement was successful
        """
        file_path = script_analysis["file_path"]
        correlation_id = self.logger.start_operation(
            "enhance_script",
            {
                "file_path": str(file_path),
                "priority": script_analysis.get("enhancement_priority"),
            },
        )

        try:
            # Create backup if requested
            if backup:
                backup_path = file_path.with_suffix(
                    f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                )
                shutil.copy2(file_path, backup_path)
                self.log.info(f"Created backup: {backup_path}")

            # Read original content
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            # Enhance content with logging
            enhanced_content = self._add_logging_to_content(
                original_content, script_analysis
            )

            # Write enhanced content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(enhanced_content)

            self.log.info(f"Enhanced logging for {file_path}")

            self.logger.end_operation(
                correlation_id, success=True, result_context={"backup_created": backup}
            )

            return True

        except Exception as e:
            self.logger.log_error_with_context(
                e, {"file_path": str(file_path)}, correlation_id
            )
            self.logger.end_operation(correlation_id, success=False)
            return False

    def _add_logging_to_content(self, content: str, analysis: Dict[str, any]) -> str:
        """
        Add comprehensive logging to script content.

        Args:
            content: Original script content
            analysis: Script analysis results

        Returns:
            Enhanced script content
        """
        lines = content.splitlines()
        enhanced_lines = []

        # Track state
        in_class = False
        in_function = False
        current_class = None
        current_function = None
        indent_level = 0

        # Add imports at the top (after existing imports)
        import_added = False
        shebang_found = False

        for i, line in enumerate(lines):
            # Handle shebang
            if line.startswith("#!") and not shebang_found:
                enhanced_lines.append(line)
                shebang_found = True
                continue

            # Add logging imports after existing imports
            if (
                not import_added
                and (line.startswith("import ") or line.startswith("from "))
                and "logging" not in line
            ):
                # Look ahead to find end of imports
                j = i
                while j < len(lines) and (
                    lines[j].startswith("import ")
                    or lines[j].startswith("from ")
                    or lines[j].strip() == ""
                ):
                    j += 1

                # Add logging import after existing imports
                if j > i:
                    enhanced_lines.append(line)
                    # Add more imports if this is the last import
                    if j == i + 1 or not (
                        lines[i + 1].startswith("import ")
                        or lines[i + 1].startswith("from ")
                    ):
                        enhanced_lines.append("")
                        enhanced_lines.append(
                            "from core_systems.comprehensive_logging_config import get_logger"
                        )
                        enhanced_lines.append("")
                        import_added = True
                    continue

            # Add logging imports at the beginning if no imports found
            if not import_added and i == 0 and not line.startswith("#"):
                enhanced_lines.append(
                    "from core_systems.comprehensive_logging_config import get_logger"
                )
                enhanced_lines.append("")
                import_added = True

            # Detect class definitions
            class_match = re.match(r"^(\s*)class\s+(\w+)", line)
            if class_match:
                enhanced_lines.append(line)
                indent_level = len(class_match.group(1))
                current_class = class_match.group(2)
                in_class = True

                # Add logger initialization to __init__ method
                self._add_class_logger_init(
                    enhanced_lines, lines, i, indent_level, current_class
                )
                continue

            # Detect function definitions
            func_match = re.match(r"^(\s*)(async\s+)?def\s+(\w+)", line)
            if func_match:
                enhanced_lines.append(line)
                func_indent = len(func_match.group(1))
                current_function = func_match.group(3)
                in_function = True

                # Add logging to significant functions
                if self._should_log_function(current_function, analysis):
                    self._add_function_logging(
                        enhanced_lines, func_indent, current_function, analysis
                    )

                continue

            # Detect try/except blocks and add error logging
            if "except Exception" in line and "as " in line:
                enhanced_lines.append(line)
                exception_var = line.split("as ")[-1].split(":")[0].strip()
                indent = len(line) - len(line.lstrip())

                # Add error logging
                enhanced_lines.append(
                    f"{' ' * (indent + 4)}self.log.error(f\"Exception in {current_function or 'unknown'}: {{str({exception_var})}}\")"
                )
                continue

            enhanced_lines.append(line)

        # Add logging import at the top if not added yet
        if not import_added:
            enhanced_lines.insert(
                0, "from core_systems.comprehensive_logging_config import get_logger"
            )
            enhanced_lines.insert(1, "")

        return "\n".join(enhanced_lines)

    def _add_class_logger_init(
        self,
        enhanced_lines: List[str],
        original_lines: List[str],
        class_line_index: int,
        indent_level: int,
        class_name: str,
    ):
        """Add logger initialization to class __init__ method."""
        # Look for __init__ method
        init_found = False
        for j in range(
            class_line_index + 1, min(class_line_index + 20, len(original_lines))
        ):
            line = original_lines[j]
            if re.match(rf'^{" " * (indent_level + 4)}def __init__', line):
                init_found = True
                break

        if not init_found:
            # Add __init__ method with logger
            enhanced_lines.append(f"{' ' * (indent_level + 4)}def __init__(self):")
            enhanced_lines.append(
                f"{' ' * (indent_level + 8)}self.logger = get_logger('{class_name.lower()}')"
            )
            enhanced_lines.append(
                f"{' ' * (indent_level + 8)}self.log = self.logger.get_logger()"
            )
            enhanced_lines.append("")

    def _should_log_function(
        self, function_name: str, analysis: Dict[str, any]
    ) -> bool:
        """Determine if a function should have logging added."""
        # Always log these function types
        important_functions = {
            "__init__",
            "main",
            "run",
            "execute",
            "process",
            "analyze",
            "create",
            "update",
            "delete",
            "save",
            "load",
            "connect",
            "send",
            "receive",
            "handle",
            "parse",
            "validate",
        }

        if function_name in important_functions:
            return True

        # Log functions in high-priority scripts
        if analysis.get("enhancement_priority") == "high":
            return True

        # Log async functions (likely important)
        if analysis.get("has_async_functions"):
            return True

        return False

    def _add_function_logging(
        self,
        enhanced_lines: List[str],
        indent: int,
        function_name: str,
        analysis: Dict[str, any],
    ):
        """Add logging statements to a function."""
        # Add entry logging
        enhanced_lines.append(
            f"{' ' * (indent + 4)}self.log.debug(f\"Entering {function_name}\")"
        )

        # Add performance tracking for important functions
        if function_name in ["execute", "run", "process", "analyze"]:
            enhanced_lines.append(f"{' ' * (indent + 4)}start_time = time.time()")

    def enhance_all_scripts(self, priority_filter: str = None) -> Dict[str, any]:
        """
        Enhance all scripts that need logging improvements.

        Args:
            priority_filter: Filter by priority ('high', 'medium', 'low')

        Returns:
            Enhancement results summary
        """
        correlation_id = self.logger.start_operation(
            "enhance_all_scripts", {"priority_filter": priority_filter}
        )

        try:
            # Scan for scripts needing enhancement
            scripts = self.scan_directory()

            # Filter by priority if specified
            if priority_filter:
                scripts = [
                    s
                    for s in scripts
                    if s.get("enhancement_priority") == priority_filter
                ]

            results = {
                "total_scripts": len(scripts),
                "enhanced": 0,
                "failed": 0,
                "skipped": 0,
                "details": [],
            }

            for script in scripts:
                try:
                    if self.enhance_script(script):
                        results["enhanced"] += 1
                        results["details"].append(
                            {
                                "file": script["file_name"],
                                "status": "enhanced",
                                "priority": script.get("enhancement_priority"),
                            }
                        )
                    else:
                        results["failed"] += 1
                        results["details"].append(
                            {
                                "file": script["file_name"],
                                "status": "failed",
                                "priority": script.get("enhancement_priority"),
                            }
                        )

                except Exception as e:
                    self.log.error(f"Failed to enhance {script['file_name']}: {e}")
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "file": script["file_name"],
                            "status": "error",
                            "error": str(e),
                        }
                    )

            self.logger.end_operation(
                correlation_id,
                success=True,
                result_context={
                    "enhanced": results["enhanced"],
                    "failed": results["failed"],
                },
            )

            return results

        except Exception as e:
            self.logger.log_error_with_context(
                e, {"priority_filter": priority_filter}, correlation_id
            )
            self.logger.end_operation(correlation_id, success=False)
            raise

    def generate_report(self) -> str:
        """Generate a comprehensive report of logging enhancement needs."""
        scripts = self.scan_directory()

        report = []
        report.append("# Autonomous Systems Logging Enhancement Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Summary
        total = len(scripts)
        high_priority = len(
            [s for s in scripts if s.get("enhancement_priority") == "high"]
        )
        medium_priority = len(
            [s for s in scripts if s.get("enhancement_priority") == "medium"]
        )
        low_priority = len(
            [s for s in scripts if s.get("enhancement_priority") == "low"]
        )

        report.append("## Summary")
        report.append(f"- Total scripts needing enhancement: {total}")
        report.append(f"- High priority: {high_priority}")
        report.append(f"- Medium priority: {medium_priority}")
        report.append(f"- Low priority: {low_priority}")
        report.append("")

        # Detailed breakdown
        report.append("## Detailed Analysis")

        for priority in ["high", "medium", "low"]:
            priority_scripts = [
                s for s in scripts if s.get("enhancement_priority") == priority
            ]
            if priority_scripts:
                report.append(f"### {priority.title()} Priority Scripts")

                for script in priority_scripts:
                    report.append(f"- **{script['file_name']}**")
                    report.append(f"  - Size: {script['lines']} lines")
                    report.append(f"  - Complexity: {script['complexity_score']}")
                    report.append(f"  - Has API calls: {script['has_api_calls']}")
                    report.append(
                        f"  - Has error handling: {script['has_error_handling']}"
                    )
                    report.append(
                        f"  - Has async functions: {script['has_async_functions']}"
                    )
                    report.append("")

        return "\n".join(report)


def main():
    """Main function to run logging enhancement."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Autonomous Systems Logging Enhancement Utility"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (for human use)",
    )
    parser.add_argument(
        "--enhance-priority",
        choices=["high", "medium", "low", "all"],
        help="Automatically enhance scripts of specified priority",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report only, no enhancements",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).parent
    enhancer = LoggingEnhancer(base_dir)

    print("🔍 Scanning for scripts needing logging enhancement...")

    # Generate report
    report = enhancer.generate_report()
    report_file = (
        base_dir
        / "logs"
        / f"logging_enhancement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )

    with open(report_file, "w") as f:
        f.write(report)

    print(f"📊 Report generated: {report_file}")

    if args.report_only:
        print("📋 Report-only mode: Enhancement skipped")
        return

    # Non-interactive mode (default for agent execution)
    if not args.interactive:
        if args.enhance_priority:
            priority_filter = (
                None if args.enhance_priority == "all" else args.enhance_priority
            )
            print(f"🚀 Auto-enhancing {args.enhance_priority} priority scripts...")
            results = enhancer.enhance_all_scripts(priority_filter=priority_filter)

            print(f"\n✅ Enhancement completed:")
            print(f"  - Enhanced: {results['enhanced']}")
            print(f"  - Failed: {results['failed']}")
            print(f"  - Total: {results['total_scripts']}")

            if results["failed"] > 0:
                print("\n❌ Failed enhancements:")
                for detail in results["details"]:
                    if detail["status"] in ["failed", "error"]:
                        print(
                            f"  - {detail['file']}: {detail.get('error', 'Unknown error')}"
                        )
        else:
            print(
                "📋 Non-interactive mode: Use --enhance-priority to automatically enhance scripts"
            )
            print("📋 Available options: --enhance-priority high|medium|low|all")
        return

    # Interactive mode (only when explicitly requested)
    print("\n" + "=" * 60)
    print(report[:1000] + "..." if len(report) > 1000 else report)
    print("=" * 60)

    response = input("\n🤖 Enhance high-priority scripts? (y/n): ").lower()

    if response == "y":
        print("🚀 Enhancing high-priority scripts...")
        results = enhancer.enhance_all_scripts(priority_filter="high")

        print(f"\n✅ Enhancement completed:")
        print(f"  - Enhanced: {results['enhanced']}")
        print(f"  - Failed: {results['failed']}")
        print(f"  - Total: {results['total_scripts']}")

        if results["failed"] > 0:
            print("\n❌ Failed enhancements:")
            for detail in results["details"]:
                if detail["status"] in ["failed", "error"]:
                    print(
                        f"  - {detail['file']}: {detail.get('error', 'Unknown error')}"
                    )

    else:
        print("🔧 Enhancement skipped. Use the report to manually enhance scripts.")


if __name__ == "__main__":
    main()
