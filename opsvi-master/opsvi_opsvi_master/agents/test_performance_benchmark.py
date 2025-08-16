#!/usr/bin/env python3
"""Test script for performance benchmark functionality."""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)


async def test_performance_benchmark():
    """Test the performance benchmark system."""
    try:
        print("🔧 Testing performance benchmark imports...")
        from src.agents.performance_benchmark import (
            PerformanceBenchmark,
            run_performance_benchmarks,
        )

        print("✅ Performance benchmark imports successful")

        print("\n🚀 Running basic benchmark test...")
        benchmark = PerformanceBenchmark()

        # Run a simple test
        async def simple_operation():
            await asyncio.sleep(0.001)  # 1ms operation
            return "success"

        result = await benchmark._run_benchmark(
            "test_operation", "test_category", simple_operation, iterations=5
        )

        if result:
            print(f"✅ Basic benchmark test successful:")
            print(f"   - Duration: {result.duration:.3f}s")
            print(f"   - Throughput: {result.throughput:.2f} ops/sec")
            print(f"   - Success: {result.success}")
        else:
            print("❌ Basic benchmark test failed")
            return False

        print("\n📊 Testing benchmark analysis...")
        analysis = benchmark._analyze_results(result.duration)

        if analysis and "execution_summary" in analysis:
            print("✅ Benchmark analysis successful")
            print(
                f"   - Total benchmarks: {analysis['execution_summary']['total_benchmarks']}"
            )
        else:
            print("❌ Benchmark analysis failed")
            return False

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_performance_benchmark())
    if success:
        print("\n🎉 Performance benchmark test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Performance benchmark test failed!")
        sys.exit(1)
