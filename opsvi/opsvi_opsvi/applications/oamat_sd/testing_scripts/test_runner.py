#!/usr/bin/env python3
"""
Test Runner for Smart Decomposition MCP Tools

Demonstrates the hybrid testing approach:
- Fast unit tests with mocks for development
- Integration tests with real APIs for validation
- Performance benchmarks for evidence collection

Usage Examples:
    python test_runner.py --fast                    # Unit tests only
    python test_runner.py --integration             # Integration tests
    python test_runner.py --real-api                # Real API tests
    python test_runner.py --performance             # Performance benchmarks
    python test_runner.py --full                    # All tests
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


def setup_environment(real_api=False, slow_tests=True):
    """Setup environment variables for test execution"""
    env = os.environ.copy()

    if real_api:
        env["REAL_MCP_TESTS"] = "1"
        env["SMART_DECOMP_USE_REAL_MCP"] = "true"
        print("🔧 Environment: Real API tests ENABLED")
    else:
        env.pop("REAL_MCP_TESTS", None)
        env.pop("SMART_DECOMP_USE_REAL_MCP", None)
        print("🔧 Environment: Mock-based tests (fast)")

    if slow_tests:
        env["SLOW_TESTS"] = "1"
    else:
        env["SLOW_TESTS"] = "0"

    return env


def run_command(cmd, env=None, description=""):
    """Run a command and return success status"""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    start_time = time.time()
    result = subprocess.run(cmd, env=env, cwd=Path(__file__).parent)
    execution_time = time.time() - start_time

    if result.returncode == 0:
        print(f"✅ SUCCESS ({execution_time:.1f}s): {description}")
    else:
        print(f"❌ FAILED ({execution_time:.1f}s): {description}")

    return result.returncode == 0


def run_fast_tests():
    """Run fast unit tests with mocks"""
    env = setup_environment(real_api=False, slow_tests=False)

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-m",
        "not slow and not real_api",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/unit",
    ]

    return run_command(cmd, env, "Fast Unit Tests (Mock-based)")


def run_integration_tests():
    """Run integration tests with conditional real API usage"""
    env = setup_environment(real_api=False)

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m",
        "integration and not real_api",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/integration",
    ]

    return run_command(cmd, env, "Integration Tests (Registry testing)")


def run_real_api_tests():
    """Run real API tests with actual network calls"""
    env = setup_environment(real_api=True)

    print("⚠️  WARNING: Real API tests will make actual network calls")
    print("   - Ensure API keys are available if needed")
    print("   - Tests may be slower due to network latency")
    print("   - Some tests may fail due to network issues")

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m",
        "real_api",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/real_api",
        "-s",  # Show logging output
    ]

    return run_command(cmd, env, "Real API Tests (Network calls)")


def run_performance_tests():
    """Run performance benchmark tests"""
    env = setup_environment(real_api=True)

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/performance/",
        "-v",
        "--tb=short",
        "-m",
        "benchmark",
        "-s",  # Show performance output
    ]

    return run_command(cmd, env, "Performance Benchmark Tests")


def run_error_handling_tests():
    """Run error handling and edge case tests"""
    env = setup_environment(real_api=False)

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/error_handling/",
        "-v",
        "--tb=short",
        "-m",
        "error_handling",
    ]

    return run_command(cmd, env, "Error Handling Tests")


def run_full_test_suite():
    """Run complete test suite with coverage report"""
    print("🎯 COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    results = []

    # Fast tests
    results.append(("Fast Tests", run_fast_tests()))

    # Integration tests
    results.append(("Integration Tests", run_integration_tests()))

    # Error handling
    results.append(("Error Handling", run_error_handling_tests()))

    # Performance (if requested)
    if os.getenv("INCLUDE_PERFORMANCE", "").lower() in ("1", "true", "yes"):
        results.append(("Performance Tests", run_performance_tests()))

    # Real API tests (if requested)
    if os.getenv("INCLUDE_REAL_API", "").lower() in ("1", "true", "yes"):
        results.append(("Real API Tests", run_real_api_tests()))

    # Generate combined coverage report
    env = setup_environment(real_api=False)
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/combined",
        "--cov-report=xml",
        "-m",
        "not real_api",  # Exclude real API from coverage
    ]

    print("\n📊 GENERATING COMBINED COVERAGE REPORT")
    run_command(cmd, env, "Combined Coverage Report")

    # Summary
    print("\n📋 TEST EXECUTION SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️  Some test suites failed. Check output above.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Smart Decomposition Test Runner")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fast", action="store_true", help="Run fast unit tests only")
    group.add_argument(
        "--integration", action="store_true", help="Run integration tests"
    )
    group.add_argument(
        "--real-api", action="store_true", help="Run real API tests (requires network)"
    )
    group.add_argument(
        "--performance", action="store_true", help="Run performance benchmark tests"
    )
    group.add_argument(
        "--error-handling", action="store_true", help="Run error handling tests"
    )
    group.add_argument(
        "--full", action="store_true", help="Run comprehensive test suite"
    )

    parser.add_argument(
        "--include-performance",
        action="store_true",
        help="Include performance tests in full suite",
    )
    parser.add_argument(
        "--include-real-api",
        action="store_true",
        help="Include real API tests in full suite",
    )

    args = parser.parse_args()

    # Set environment for full suite options
    if args.include_performance:
        os.environ["INCLUDE_PERFORMANCE"] = "1"
    if args.include_real_api:
        os.environ["INCLUDE_REAL_API"] = "1"

    print("🧪 SMART DECOMPOSITION TEST RUNNER")
    print("=" * 60)

    if args.fast:
        success = run_fast_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.real_api:
        success = run_real_api_tests()
    elif args.performance:
        success = run_performance_tests()
    elif args.error_handling:
        success = run_error_handling_tests()
    elif args.full:
        success = run_full_test_suite()
    else:
        # Default: fast tests
        print("No specific test type specified. Running fast tests.")
        print("Use --help to see all options.")
        success = run_fast_tests()

    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILURE'}: Test execution complete")

    # Coverage report location
    coverage_dir = Path(__file__).parent / "htmlcov"
    if coverage_dir.exists():
        print(f"\n📊 Coverage reports available at: {coverage_dir}/")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
