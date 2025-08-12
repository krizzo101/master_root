"""
Batch Auto-Align Script for O3 Code Generator

Processes multiple files in parallel using auto-align to fix:
- Broken imports
- Rule violations
- Structural issues
- Missing imports
"""

import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List

from src.tools.code_generation.o3_code_generator.alignment_scanner import (
    AlignmentScanner,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


class BatchAutoAlign:
    """
    Multi-threaded auto-align processor for systematic codebase fixes.

    Processes multiple files in parallel using auto-align to fix
    broken imports, rule violations, and structural issues.
    """

    def __init__(self, base_path: Path = None, max_workers: int = 4):
        """Initialize the batch auto-align processor."""
        setup_logger(LogConfig())
        self.logger = get_logger()
        self.base_path = base_path or Path(
            "src/tools/code_generation/o3_code_generator"
        )
        self.max_workers = max_workers
        self.alignment_scanner = AlignmentScanner(self.base_path)
        self.results = {"processed_files": [], "processing_time": 0, "total_files": 0}
        self.logger.log_info(f"Initialized BatchAutoAlign with {max_workers} workers")

    def load_alignment_map(self, scan_results_path: Path = None) -> List[str]:
        """
        Load the list of files needing alignment from scan results.

        Args:
            scan_results_path: Path to alignment scan results (optional)

        Returns:
            List of file paths that need alignment
        """
        if scan_results_path is None:
            scan_results_path = self.base_path / "alignment_scan_results.json"
        else:
            pass
        if not scan_results_path.exists():
            self.logger.log_info("No existing scan results found, running new scan...")
            scan_results = self.alignment_scanner.scan_codebase()
            self.alignment_scanner.save_scan_results(scan_results, scan_results_path)
        else:
            with open(scan_results_path) as f:
                scan_results = json.load(f)
        files_needing_alignment = [
            file_info["file"] for file_info in scan_results["files_needing_alignment"]
        ]
        self.logger.log_info(
            f"Loaded {len(files_needing_alignment)} files needing alignment"
        )
        return files_needing_alignment

    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file with auto-align using progressive fixing approach.

        Implements intelligent attempt limits based on file complexity:
        - Simple files: 3 attempts
        - Complex files (multiple issues): 8 attempts
        - Critical files (syntax errors, broken imports): 10 attempts
        """
        complexity = self._assess_file_complexity(file_path)
        max_attempts = self._get_max_attempts(complexity)
        attempts = 0
        diffs = []
        scan_results = []
        partial_successes = []
        self.logger.log_info(
            f"Processing: {file_path} (complexity: {complexity}, max attempts: {max_attempts})"
        )
        while attempts < max_attempts:
            attempts += 1
            self.logger.log_info(
                f"Processing: {file_path} (attempt {attempts}/{max_attempts})"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.tools.code_generation.o3_code_generator.auto_align",
                    file_path,
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
            )
            diff = result.stdout
            diffs.append(diff)
            scan_issue = self.alignment_scanner._scan_file(file_path)
            scan_results.append(scan_issue)
            if not scan_issue.get("needs_alignment", False):
                self.logger.log_info(
                    f"✅ Successfully aligned: {file_path} after {attempts} attempt(s)"
                )
                return {
                    "file": file_path,
                    "status": "success",
                    "attempts": attempts,
                    "complexity": complexity,
                    "diffs": diffs,
                    "scan_results": scan_results,
                    "output": result.stdout,
                    "error": None,
                }
            else:
                pass
            improvement_score = self._calculate_improvement_score(scan_issue, attempts)
            if improvement_score > 0:
                partial_successes.append(
                    {
                        "attempt": attempts,
                        "score": improvement_score,
                        "issues_remaining": len(scan_issue.get("issues", [])),
                    }
                )
                self.logger.log_info(
                    f"⚠️ Partial improvement on attempt {attempts} for {file_path} (score: {improvement_score}, issues remaining: {len(scan_issue.get('issues', []))})"
                )
            else:
                self.logger.log_warning(
                    f"⚠️ No improvement on attempt {attempts} for {file_path}"
                )
            if attempts >= 3 and (not partial_successes):
                self.logger.log_warning(
                    f"❌ No progress made after 3 attempts for {file_path}, stopping"
                )
                break
            else:
                pass
        else:
            pass
        final_status = self._determine_final_status(
            partial_successes, attempts, max_attempts
        )
        self.logger.log_warning(
            f"❌ {final_status}: {file_path} after {attempts} attempts"
        )
        return {
            "file": file_path,
            "status": final_status,
            "attempts": attempts,
            "complexity": complexity,
            "diffs": diffs,
            "scan_results": scan_results,
            "partial_successes": partial_successes,
            "output": result.stdout,
            "error": result.stderr,
        }

    def _assess_file_complexity(self, file_path: str) -> str:
        """
        Assess the complexity of a file based on its issues.

        Returns:
            "simple", "complex", or "critical"
        """
        try:
            scan_issue = self.alignment_scanner._scan_file(file_path)
            issues = scan_issue.get("issues", [])
            syntax_errors = sum(1 for issue in issues if "syntax_error" in str(issue))
            broken_imports = sum(1 for issue in issues if "broken_import" in str(issue))
            total_issues = len(issues)
            if syntax_errors > 0 or broken_imports > 3:
                return "critical"
            elif total_issues > 5:
                return "complex"
            else:
                return "simple"
        except Exception as e:
            self.logger.log_warning(f"Error assessing complexity for {file_path}: {e}")
            return "complex"
        else:
            pass
        finally:
            pass

    def _get_max_attempts(self, complexity: str) -> int:
        """
        Get maximum attempts based on file complexity.

        Args:
            complexity: "simple", "complex", or "critical"

        Returns:
            Maximum number of attempts
        """
        attempt_limits = {"simple": 3, "complex": 8, "critical": 10}
        return attempt_limits.get(complexity, 5)

    def _calculate_improvement_score(
        self, scan_issue: Dict[str, Any], attempt: int
    ) -> int:
        """
        Calculate improvement score based on remaining issues.

        Args:
            scan_issue: Current scan results
            attempt: Current attempt number

        Returns:
            Improvement score (higher is better)
        """
        issues = scan_issue.get("issues", [])
        total_issues = len(issues)
        critical_issues = sum(
            1
            for issue in issues
            if "syntax_error" in str(issue) or "broken_import" in str(issue)
        )
        regular_issues = total_issues - critical_issues
        score = 100 - critical_issues * 20 - regular_issues * 5
        if attempt > 1:
            score += 10
        else:
            pass
        return max(0, score)

    def _determine_final_status(
        self, partial_successes: List[Dict], attempts: int, max_attempts: int
    ) -> str:
        """
        Determine final status based on partial successes and attempts.

        Args:
            partial_successes: List of partial improvement records
            attempts: Number of attempts made
            max_attempts: Maximum attempts allowed

        Returns:
            "failed", "partial_success", or "timeout"
        """
        if partial_successes:
            best_score = max(ps["score"] for ps in partial_successes)
            if best_score >= 50:
                return "partial_success"
            else:
                return "failed"
        elif attempts >= max_attempts:
            return "timeout"
        else:
            return "failed"

    def process_files_parallel(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Process multiple files in parallel using ThreadPoolExecutor.

        Args:
            file_paths: List of file paths to process

        Returns:
            Dict containing batch processing results
        """
        start_time = time.time()
        self.results["total_files"] = len(file_paths)
        self.logger.log_info(
            f"Starting parallel processing of {len(file_paths)} files with {self.max_workers} workers"
        )
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_file = {
                executor.submit(self.process_single_file, file_path): file_path
                for file_path in file_paths
            }
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    self.results["processed_files"].append(result)
                    status = result["status"]
                    if status == "success":
                        self.logger.log_info(f"✅ Successfully processed: {file_path}")
                    elif status == "partial_success":
                        best_score = max(
                            ps["score"] for ps in result.get("partial_successes", [])
                        )
                        self.logger.log_info(
                            f"⚠️  Partial success for: {file_path} (score: {best_score})"
                        )
                    elif status == "timeout":
                        self.logger.log_warning(f"⏰ Timeout for: {file_path}")
                    else:
                        self.logger.log_warning(f"❌ Failed to process: {file_path}")
                except Exception as e:
                    self.logger.log_error(
                        f"❌ Exception in parallel processing for {file_path}: {e}"
                    )
                    self.results["processed_files"].append(
                        {
                            "file": file_path,
                            "status": "exception",
                            "complexity": "unknown",
                            "attempts": 0,
                            "diffs": [],
                            "scan_results": [],
                            "partial_successes": [],
                            "output": None,
                            "error": str(e),
                        }
                    )
                else:
                    pass
                finally:
                    pass
            else:
                pass
        self.results["processing_time"] = time.time() - start_time
        total_processed = len(self.results["processed_files"])
        successful = len(
            [r for r in self.results["processed_files"] if r["status"] == "success"]
        )
        partial_success = len(
            [
                r
                for r in self.results["processed_files"]
                if r["status"] == "partial_success"
            ]
        )
        failed = len(
            [r for r in self.results["processed_files"] if r["status"] == "failed"]
        )
        timeout = len(
            [r for r in self.results["processed_files"] if r["status"] == "timeout"]
        )
        exception = len(
            [r for r in self.results["processed_files"] if r["status"] == "exception"]
        )
        self.logger.log_info(
            f"Parallel processing complete in {self.results['processing_time']:.2f} seconds"
        )
        self.logger.log_info(
            f"Results: {successful} success, {partial_success} partial, {failed} failed, {timeout} timeout, {exception} exception"
        )
        return self.results

    def generate_batch_report(self) -> str:
        """
        Generate a comprehensive batch processing report.

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("BATCH AUTO-ALIGN PROCESSING REPORT")
        report.append("=" * 80)
        report.append("")
        total_files = self.results["total_files"]
        successful = len(
            [r for r in self.results["processed_files"] if r["status"] == "success"]
        )
        partial_success = len(
            [
                r
                for r in self.results["processed_files"]
                if r["status"] == "partial_success"
            ]
        )
        failed = len(
            [r for r in self.results["processed_files"] if r["status"] == "failed"]
        )
        timeout = len(
            [r for r in self.results["processed_files"] if r["status"] == "timeout"]
        )
        processing_time = self.results["processing_time"]
        total_processed = len(self.results["processed_files"])
        full_success_rate = (
            successful / total_processed * 100 if total_processed > 0 else 0
        )
        partial_success_rate = (
            (successful + partial_success) / total_processed * 100
            if total_processed > 0
            else 0
        )
        report.append("📊 BATCH PROCESSING SUMMARY:")
        report.append(f"   Total files processed: {total_files}")
        report.append(f"   Fully successful fixes: {successful}")
        report.append(f"   Partial successes: {partial_success}")
        report.append(f"   Failed fixes: {failed}")
        report.append(f"   Timeout: {timeout}")
        report.append(f"   Full success rate: {full_success_rate:.1f}%")
        report.append(f"   Partial success rate: {partial_success_rate:.1f}%")
        report.append(f"   Processing time: {processing_time:.2f} seconds")
        report.append(
            f"   Average time per file: {processing_time / total_files:.2f} seconds"
            if total_files > 0
            else "   Average time per file: 0 seconds"
        )
        report.append("")
        complexity_stats = {}
        for result in self.results["processed_files"]:
            complexity = result.get("complexity", "unknown")
            complexity_stats[complexity] = complexity_stats.get(complexity, 0) + 1
        else:
            pass
        if complexity_stats:
            report.append("🔍 COMPLEXITY BREAKDOWN:")
            report.append("-" * 40)
            for complexity, count in complexity_stats.items():
                success_count = len(
                    [
                        r
                        for r in self.results["processed_files"]
                        if r.get("complexity") == complexity
                        and r["status"] == "success"
                    ]
                )
                success_rate = success_count / count * 100 if count > 0 else 0
                report.append(
                    f"   {complexity.capitalize()}: {count} files ({success_rate:.1f}% success)"
                )
            else:
                pass
            report.append("")
        else:
            pass
        successful_files = [
            r for r in self.results["processed_files"] if r["status"] == "success"
        ]
        if successful_files:
            report.append("✅ FULLY SUCCESSFUL FIXES:")
            report.append("-" * 40)
            for result in successful_files:
                report.append(
                    f"   📁 {result['file']} ({result['attempts']} attempts, {result.get('complexity', 'unknown')})"
                )
            else:
                pass
            report.append("")
        else:
            pass
        partial_files = [
            r
            for r in self.results["processed_files"]
            if r["status"] == "partial_success"
        ]
        if partial_files:
            report.append("⚠️  PARTIAL SUCCESSES:")
            report.append("-" * 40)
            for result in partial_files:
                best_score = max(
                    ps["score"] for ps in result.get("partial_successes", [])
                )
                report.append(
                    f"   📁 {result['file']} (score: {best_score}, {result['attempts']} attempts)"
                )
            else:
                pass
            report.append("")
        else:
            pass
        failed_files = [
            r
            for r in self.results["processed_files"]
            if r["status"] in ["failed", "timeout"]
        ]
        if failed_files:
            report.append("❌ FAILED FIXES:")
            report.append("-" * 40)
            for result in failed_files:
                status_text = "TIMEOUT" if result["status"] == "timeout" else "FAILED"
                report.append(
                    f"   📁 {result['file']} ({status_text}, {result['attempts']} attempts)"
                )
            else:
                pass
            report.append("")
        else:
            pass
        if self.results["processed_files"]:
            report.append("🔍 DETAILED RESULTS:")
            report.append("-" * 40)
            for result in self.results["processed_files"]:
                status_icon = {
                    "success": "✅",
                    "partial_success": "⚠️",
                    "failed": "❌",
                    "timeout": "⏰",
                }.get(result["status"], "❓")
                complexity = result.get("complexity", "unknown")
                attempts = result["attempts"]
                report.append(
                    f"{status_icon} {result['file']} ({result['status'].upper()})"
                )
                report.append(f"   Complexity: {complexity}, Attempts: {attempts}")
                if result.get("partial_successes"):
                    best_score = max(ps["score"] for ps in result["partial_successes"])
                    report.append(f"   Best improvement score: {best_score}")
                else:
                    pass
                if result["error"]:
                    error_preview = (
                        result["error"][:100] + "..."
                        if len(result["error"]) > 100
                        else result["error"]
                    )
                    report.append(f"   Error: {error_preview}")
                else:
                    pass
                report.append("")
            else:
                pass
            report.append("")
        else:
            pass
        report.append("=" * 80)
        return "\n".join(report)

    def save_batch_results(self, output_path: Path = None) -> Path:
        """
        Save batch processing results to a JSON file.

        Args:
            output_path: Path to save results (optional)

        Returns:
            Path where results were saved
        """
        if output_path is None:
            output_path = self.base_path / "batch_auto_align_results.json"
        else:
            pass
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)
        self.logger.log_info(f"Batch results saved to: {output_path}")
        return output_path

    def run_batch_alignment(
        self, scan_results_path: Path = None, max_files: int = None
    ) -> Dict[str, Any]:
        """
        Run the complete batch alignment process.

        Args:
            scan_results_path: Path to alignment scan results (optional)
            max_files: Maximum number of files to process (optional, for testing)

        Returns:
            Dict containing batch processing results
        """
        self.logger.log_info("🚀 Starting batch auto-alignment process")
        files_needing_alignment = self.load_alignment_map(scan_results_path)
        if max_files and max_files < len(files_needing_alignment):
            files_needing_alignment = files_needing_alignment[:max_files]
            self.logger.log_info(f"Limited to {max_files} files for testing")
        else:
            pass
        results = self.process_files_parallel(files_needing_alignment)
        report = self.generate_batch_report()
        output_path = self.save_batch_results()
        self.logger.log_info(f"📄 Detailed results saved to: {output_path}")
        return results


def main():
    """Main function to run batch auto-alignment."""
    setup_logger(LogConfig())
    logger = get_logger()
    logger.log_info("🚀 Starting Batch Auto-Align")
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch auto-align for O3 Code Generator"
    )
    parser.add_argument(
        "--max-workers", type=int, default=4, help="Maximum number of parallel workers"
    )
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to process (for testing)"
    )
    parser.add_argument(
        "--scan-results", type=str, help="Path to alignment scan results"
    )
    args = parser.parse_args()
    batch_processor = BatchAutoAlign(max_workers=args.max_workers)
    scan_results_path = Path(args.scan_results) if args.scan_results else None
    results = batch_processor.run_batch_alignment(
        scan_results_path=scan_results_path, max_files=args.max_files
    )
    processed_files = results.get("processed_files", [])
    successful = len([r for r in processed_files if r["status"] == "success"])
    partial_success = len(
        [r for r in processed_files if r["status"] == "partial_success"]
    )
    failed = len(
        [
            r
            for r in processed_files
            if r["status"] in ["failed", "timeout", "exception"]
        ]
    )
    total_processed = len(processed_files)
    success_rate = successful / total_processed * 100 if total_processed > 0 else 0
    partial_success_rate = (
        (successful + partial_success) / total_processed * 100
        if total_processed > 0
        else 0
    )
    if failed > 0:
        logger.log_warning(
            f"⚠️  {failed} files failed to align - check results for details"
        )
        logger.log_info(
            f"Success rate: {success_rate:.1f}% (partial: {partial_success_rate:.1f}%)"
        )
        return 1
    else:
        logger.log_info("✅ All files successfully aligned!")
        logger.log_info(
            f"Success rate: {success_rate:.1f}% (partial: {partial_success_rate:.1f}%)"
        )
        return 0


if __name__ == "__main__":
    exit(main())
else:
    pass
