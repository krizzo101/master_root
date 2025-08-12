#!/usr/bin/env python3
"""
Clean Performance Tests - Remove performance assertions from functional tests

This script identifies performance-related test code that should be moved
to a separate performance test suite, keeping functional tests focused on correctness.
"""

import re
from pathlib import Path

# Performance-related patterns to identify
PERFORMANCE_PATTERNS = [
    # Timing assertions
    r"time\.time\(\)",
    r"start.*time",
    r"end.*time",
    r"duration",
    r"timeout.*=.*\d+",
    r"assert.*<.*\d+.*s",
    r"assert.*time.*<",
    # Performance metrics
    r"parallel.*efficiency",
    r"improvement.*\d+\.?\d*x",
    r"benchmark",
    r"performance",
    r"memory.*usage",
    r"execution.*time",
    r"processing.*time",
    r"<.*second",
    r"under.*load",
    # Concurrency performance
    r"concurrent.*creation",
    r"parallel.*execution",
    r"scalability",
    r"thread.*safety",
    r"async.*performance",
]


def scan_test_file(file_path: Path) -> dict[str, list[tuple[int, str]]]:
    """Scan a test file for performance-related code"""
    results = {}

    try:
        with open(file_path) as f:
            lines = f.readlines()

        for pattern in PERFORMANCE_PATTERNS:
            matches = []
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append((i, line.strip()))

            if matches:
                results[pattern] = matches

    except Exception as e:
        print(f"Error scanning {file_path}: {e}")

    return results


def scan_all_tests() -> dict[str, dict[str, list[tuple[int, str]]]]:
    """Scan all test files for performance-related code"""
    test_dir = Path("tests")
    all_results = {}

    for test_file in test_dir.rglob("test_*.py"):
        results = scan_test_file(test_file)
        if results:
            all_results[str(test_file)] = results

    return all_results


def generate_report(results: dict[str, dict[str, list[tuple[int, str]]]]) -> None:
    """Generate a report of performance-related code found"""
    print("🔍 PERFORMANCE CODE SCAN REPORT")
    print("=" * 60)
    print("Found performance-related code that should be moved to separate tests:")
    print()

    if not results:
        print("✅ No performance-related test code found!")
        print("All tests appear to be focused on functional correctness.")
        return

    for file_path, patterns in results.items():
        print(f"📄 {file_path}")
        print("-" * 40)

        for pattern, matches in patterns.items():
            print(f"  Pattern: {pattern}")
            for line_num, line_content in matches:
                print(f"    Line {line_num}: {line_content}")
            print()
        print()


def suggest_functional_alternatives() -> None:
    """Suggest functional test alternatives for common performance tests"""
    print("💡 FUNCTIONAL TEST ALTERNATIVES")
    print("=" * 60)

    alternatives = [
        {
            "performance": "assert execution_time < 1.0",
            "functional": "assert result is not None and result.success == True",
            "reason": "Test that operation completes successfully, not how fast",
        },
        {
            "performance": "assert parallel_efficiency > 3.0",
            "functional": "assert all(agent.status == 'completed' for agent in agents)",
            "reason": "Test that all agents complete their work correctly",
        },
        {
            "performance": "assert memory_usage < 2048",
            "functional": "assert model.factors is not None and len(model.factors) == 6",
            "reason": "Test that required data structures are created properly",
        },
        {
            "performance": "benchmark_tool_execution()",
            "functional": "assert tool.execute(data).status == 'success'",
            "reason": "Test that tools execute and return expected results",
        },
    ]

    for alt in alternatives:
        print(f"❌ Performance: {alt['performance']}")
        print(f"✅ Functional:  {alt['functional']}")
        print(f"   Reason: {alt['reason']}")
        print()


if __name__ == "__main__":
    print("🧪 CLEANING PERFORMANCE TESTS FROM FUNCTIONAL TDD SUITE")
    print("=" * 70)
    print()

    # Scan for performance-related code
    results = scan_all_tests()
    generate_report(results)

    # Suggest alternatives
    suggest_functional_alternatives()

    # Action recommendations
    print("📋 RECOMMENDED ACTIONS")
    print("=" * 60)
    print("1. Review flagged lines in test files")
    print("2. Replace performance assertions with functional equivalents")
    print("3. Move performance tests to tests/performance/ directory")
    print("4. Run: make test-functional (should focus on correctness)")
    print("5. Later: make test-performance (after implementation complete)")
    print()
    print("🎯 Goal: Functional tests pass → Implement → Optimize performance separately")
