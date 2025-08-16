#!/usr/bin/env python3
"""
Comprehensive model testing script for the O3 code generator.
Tests all approved models and compares their performance and quality.
"""

import sys
import time
import json
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.code_generation.o3_code_generator.utils.o3_model_generator import (
    O3ModelGenerator,
)


def test_models():
    """Test all approved models and compare results."""

    # Test all approved models
    models_to_test = [
        "o3-mini",
        "o3",
        "o4-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "codex-mini-latest",
    ]

    test_prompt = "Write a Python function that validates email addresses using regex, with comprehensive error handling and unit tests."

    results = []

    print("🧪 COMPREHENSIVE MODEL TESTING")
    print("=" * 50)

    for model in models_to_test:
        print(f"\n🔍 Testing {model}...")

        try:
            start_time = time.time()
            generator = O3ModelGenerator(model=model)
            messages = [{"role": "user", "content": test_prompt}]

            result = generator.generate(messages)
            end_time = time.time()

            response_time = end_time - start_time
            result_length = len(result)

            # Basic quality indicators
            has_code_block = "```python" in result
            has_function_def = "def " in result
            has_tests = "test" in result.lower() or "assert" in result.lower()
            has_error_handling = (
                "try:" in result or "except" in result or "error" in result.lower()
            )

            model_result = {
                "model": model,
                "status": "SUCCESS",
                "response_time": round(response_time, 2),
                "result_length": result_length,
                "has_code_block": has_code_block,
                "has_function_def": has_function_def,
                "has_tests": has_tests,
                "has_error_handling": has_error_handling,
                "preview": result[:200] + "..." if len(result) > 200 else result,
                "full_result": result,
            }

            print(f"✅ {model}: {response_time:.2f}s, {result_length} chars")
            print(
                f"   Code block: {has_code_block}, Function: {has_function_def}, Tests: {has_tests}, Error handling: {has_error_handling}"
            )

        except Exception as e:
            model_result = {
                "model": model,
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__,
            }
            print(f"❌ {model}: {type(e).__name__} - {str(e)}")

        results.append(model_result)

    # Sort by response time (faster is better)
    working_models = [r for r in results if r["status"] == "SUCCESS"]
    working_models.sort(key=lambda x: x["response_time"])

    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)

    print("\n🏆 PERFORMANCE RANKING (by speed):")
    for i, result in enumerate(working_models, 1):
        print(
            f'{i}. {result["model"]}: {result["response_time"]}s ({result["result_length"]} chars)'
        )

    print("\n📈 QUALITY ANALYSIS:")
    for result in working_models:
        quality_score = sum(
            [
                result["has_code_block"],
                result["has_function_def"],
                result["has_tests"],
                result["has_error_handling"],
            ]
        )
        print(f'{result["model"]}: Quality score {quality_score}/4')

    print("\n❌ FAILED MODELS:")
    failed_models = [r for r in results if r["status"] == "ERROR"]
    for result in failed_models:
        print(f'{result["model"]}: {result["error_type"]} - {result["error"]}')

    # Save detailed results
    output_file = Path(__file__).parent / "model_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to {output_file}")

    return results


if __name__ == "__main__":
    test_models()
