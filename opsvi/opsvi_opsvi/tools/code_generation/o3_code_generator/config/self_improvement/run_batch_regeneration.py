#!/usr/bin/env python3
"""
Batch regeneration script for all utility modules.
Runs all enhancement requests in parallel to regenerate utility modules with project rules.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_enhancement(enhancement_file: str) -> bool:
    """Run a single enhancement request."""
    try:
        print(f"🔄 Running enhancement: {enhancement_file}")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.tools.code_generation.o3_code_generator.config.self_improvement.run_self_improvement",
                "--improvement",
                enhancement_file,
            ],
            capture_output=True,
            text=True,
            cwd="/home/opsvi/agent_world",
        )

        if result.returncode == 0:
            print(f"✅ Success: {enhancement_file}")
            return True
        else:
            print(f"❌ Failed: {enhancement_file}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception in {enhancement_file}: {e}")
        return False


def main():
    """Run all enhancement requests."""
    enhancement_files = [
        "test_simple_improvement.json",
    ]

    print("🚀 Starting batch regeneration of utility modules...")
    print(f"📁 Working directory: {Path.cwd()}")

    # Run enhancements sequentially for now (parallel might cause conflicts)
    results = []
    for enhancement_file in enhancement_files:
        success = run_enhancement(enhancement_file)
        results.append((enhancement_file, success))
        time.sleep(2)  # Small delay between runs

    # Report results
    print("\n📊 Batch regeneration results:")
    success_count = 0
    for enhancement_file, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {enhancement_file}")
        if success:
            success_count += 1

    print(f"\n🎯 Summary: {success_count}/{len(results)} enhancements successful")

    if success_count == len(results):
        print("🎉 All utility modules regenerated successfully!")
        print("🧪 Running smoke test...")

        # Run smoke test
        smoke_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.tools.code_generation.o3_code_generator.utils.test_utils_smoke",
            ],
            capture_output=True,
            text=True,
            cwd="/home/opsvi/agent_world",
        )

        print("Smoke test output:")
        print(smoke_result.stdout)
        if smoke_result.stderr:
            print("Smoke test errors:")
            print(smoke_result.stderr)
    else:
        print("⚠️  Some enhancements failed. Check the logs above.")


if __name__ == "__main__":
    main()
