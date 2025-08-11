"""
Test Coverage Analyzer

Runs pytest with coverage and parses the output for coverage percentage.
"""

import subprocess
import re
from typing import Dict


def analyze_coverage(
    target_path: str = "src/", test_path: str = "tests/"
) -> Dict[str, float]:
    """Analyze test coverage for the specified target path.

    Args:
        target_path: Path to source code to analyze coverage for
        test_path: Path to tests to run for coverage analysis

    Returns:
        Dict containing coverage percentage, return code, and output
    """
    import os

    # SECURITY: Prevent recursive pytest execution (fork bomb protection)
    if os.environ.get("VALIDATION_COVERAGE_RUNNING"):
        print(
            "[Validator] Coverage analysis skipped - already running in test context",
            flush=True,
        )
        return {
            "coverage": -1.0,
            "returncode": -2,  # Special code for skipped due to recursion
            "output": "[recursion-prevented]",
            "raw_stderr": "Coverage analysis prevented recursive execution",
        }

    try:
        # Ensure we're running from project root and add current directory to
        # Python path
        env = os.environ.copy()
        current_dir = os.getcwd()
        env["PYTHONPATH"] = current_dir + ":" + env.get("PYTHONPATH", "")

        # Set guard flag to prevent recursive execution
        env["VALIDATION_COVERAGE_RUNNING"] = "1"

        # Run tests with coverage for the target path
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                test_path,
                "--cov",
                target_path,
                "--cov-report=term-missing",
                "--cov-report=json:coverage.json",
                "-v",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            cwd=current_dir,
        )

        output = result.stdout[:2000]  # Increased output capture

        # Try to extract coverage from terminal output first
        coverage = -1.0
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            try:
                coverage = float(match.group(1))
            except (ValueError, AttributeError):
                pass

        # Fallback: try to read from JSON report if terminal parsing failed
        if coverage == -1.0:
            try:
                import json
                import os

                if os.path.exists("coverage.json"):
                    with open("coverage.json", "r") as f:
                        cov_data = json.load(f)
                        coverage = round(
                            cov_data.get("totals", {}).get("percent_covered", -1.0),
                            2,
                        )
                    os.remove("coverage.json")  # Clean up
            except Exception:
                pass

        print(
            f"[Validator] pytest coverage completed, coverage: {coverage}%, "
            f"return_code: {result.returncode}",
            flush=True,
        )
        return {
            "coverage": coverage,
            "returncode": result.returncode,
            "output": output,
            "raw_stderr": result.stderr[:1000] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        print("[Validator] pytest coverage timed out!", flush=True)
        return {
            "coverage": -1.0,
            "returncode": -1,
            "output": "[timeout]",
            "raw_stderr": "",
        }
