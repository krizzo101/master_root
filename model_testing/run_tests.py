#!/usr/bin/env python3
"""
Test Runner for GPT-5 vs GPT-4.1 Comprehensive Testing Framework

This script provides an easy way to run the comprehensive testing framework
with different configurations and options.

Usage:
    python run_tests.py [--quick] [--reasoning-only] [--full]
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime

# Add the current directory to the path so we can import the framework
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpt5_vs_gpt41_comprehensive_test_framework import (
    ComprehensiveTestRunner,
    ReasoningEffort,
    TestCategory,
)


async def run_quick_tests() -> dict:
    """Run a quick subset of tests for rapid evaluation."""
    print("🚀 Running Quick Tests (GPT-5 vs GPT-4.1 Mini only)")

    # Create a modified runner for quick tests
    runner = ComprehensiveTestRunner()

    # Test only the mini model pair
    gpt41_model, gpt5_model = ("gpt-4.1-mini", "gpt-5-mini")
    print(f"\n🔍 Testing {gpt41_model} vs {gpt5_model}")

    pair_results = await runner._test_model_pair(gpt41_model, gpt5_model)
    runner.results[f"{gpt41_model}_vs_{gpt5_model}"] = pair_results

    # Run reasoning effort tests with only medium effort
    print(f"\n🧠 Testing GPT-5 Reasoning Effort (Medium only)")
    reasoning_results = await runner._test_gpt5_reasoning_efforts()
    runner.results["gpt5_reasoning_effort_analysis"] = reasoning_results

    # Generate and save report
    report = runner._generate_comprehensive_report(0)  # Time will be calculated
    runner._save_results(report)

    return report


async def run_reasoning_effort_tests() -> dict:
    """Run only the reasoning effort tests for GPT-5."""
    print("🧠 Running GPT-5 Reasoning Effort Tests Only")

    runner = ComprehensiveTestRunner()
    reasoning_results = await runner._test_gpt5_reasoning_efforts()

    # Create a minimal report structure
    report = {
        "test_metadata": {
            "total_execution_time": 0,
            "model_pairs_tested": 0,
            "categories_tested": len(
                [
                    TestCategory.CODE_GENERATION,
                    TestCategory.CODING_REASONING,
                    TestCategory.ALGORITHM_DESIGN,
                    TestCategory.CODE_OPTIMIZATION,
                ]
            ),
            "total_tests": 0,
            "test_date": datetime.now().isoformat(),
        },
        "overall_summary": {
            "average_improvement": 0,
            "median_improvement": 0,
            "std_improvement": 0,
            "best_improvement": 0,
            "worst_improvement": 0,
        },
        "category_summaries": {},
        "detailed_results": {"gpt5_reasoning_effort_analysis": reasoning_results},
    }

    runner._save_results(report)
    return report


async def run_full_tests() -> dict:
    """Run the complete comprehensive testing framework."""
    print("🚀 Running Full Comprehensive Tests")

    runner = ComprehensiveTestRunner()
    report = await runner.run_comprehensive_tests()

    return report


def main() -> dict:
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run GPT-5 vs GPT-4.1 comprehensive testing framework"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests (mini models only, medium reasoning effort only)",
    )
    parser.add_argument(
        "--reasoning-only",
        action="store_true",
        help="Run only GPT-5 reasoning effort tests",
    )
    parser.add_argument(
        "--full", action="store_true", help="Run full comprehensive tests (default)"
    )

    args = parser.parse_args()

    # Determine which tests to run
    if args.quick:
        print("🎯 Quick Test Mode Selected")
        report = asyncio.run(run_quick_tests())
    elif args.reasoning_only:
        print("🧠 Reasoning Effort Test Mode Selected")
        report = asyncio.run(run_reasoning_effort_tests())
    else:
        print("🎯 Full Test Mode Selected")
        report = asyncio.run(run_full_tests())

    print(f"\n✅ Testing completed successfully!")
    print(f"📊 Results saved to: results/")

    return report


if __name__ == "__main__":
    main()
