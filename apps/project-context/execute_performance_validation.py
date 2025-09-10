#!/usr/bin/env python3
"""
Enhanced Performance Validation for Phase 1 System
Comprehensive performance testing and benchmarking suite
"""

import asyncio
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil


class PerformanceValidator:
    """Comprehensive performance validation and benchmarking."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "system_info": {},
            "performance_benchmarks": {},
            "resource_utilization": {},
            "scalability_tests": {},
            "overall_performance_score": 0.0,
        }

    async def collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for performance context."""
        print("\n📊 Collecting System Information...")

        system_info = {
            "cpu_count": psutil.cpu_count(logical=True),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(
                psutil.virtual_memory().available / (1024**3), 2
            ),
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "python_version": f"{'.'.join(map(str, __import__('sys').version_info[:3]))}",
            "platform": __import__("platform").platform(),
        }

        print(f"  💻 CPU Cores: {system_info['cpu_count']}")
        print(
            f"  💾 Memory: {system_info['memory_available_gb']:.1f}GB available / {system_info['memory_total_gb']:.1f}GB total"
        )
        print(f"  💿 Disk Usage: {system_info['disk_usage_percent']:.1f}%")

        return system_info

    async def benchmark_core_components(self) -> Dict[str, Any]:
        """Benchmark core component performance."""
        print("\n⚡ Benchmarking Core Components...")

        benchmarks = {
            "component_import_times": {},
            "adapter_initialization_times": {},
            "database_connection_times": {},
            "tool_response_times": {},
        }

        # Benchmark component imports
        components_to_test = [
            "src.project_context.ingestion.adapters.chat_adapter",
            "src.project_context.ingestion.adapters.code_adapter",
            "src.project_context.ingestion.base_adapter",
            "src.project_context.db.connections",
            "src.project_context.tools.analysis",
        ]

        for component in components_to_test:
            try:
                start_time = time.perf_counter()
                __import__(component)
                end_time = time.perf_counter()

                import_time_ms = (end_time - start_time) * 1000
                benchmarks["component_import_times"][component] = import_time_ms

                status = (
                    "✅"
                    if import_time_ms < 100
                    else "⚠️"
                    if import_time_ms < 500
                    else "❌"
                )
                print(f"  {status} {component.split('.')[-1]}: {import_time_ms:.2f}ms")

            except Exception as e:
                benchmarks["component_import_times"][component] = -1
                print(f"  ❌ {component.split('.')[-1]}: FAILED ({e})")

        return benchmarks

    async def test_database_performance(self) -> Dict[str, Any]:
        """Test database connection and query performance."""
        print("\n🗄️ Testing Database Performance...")

        db_performance = {
            "connection_time_ms": 0,
            "simple_query_time_ms": 0,
            "connection_success": False,
            "query_success": False,
        }

        try:
            # Test database connection time
            start_time = time.perf_counter()

            # Simulate database connection test
            from src.project_context.db.connections import get_db_connection

            conn = get_db_connection()
            connection_time = (time.perf_counter() - start_time) * 1000
            db_performance["connection_time_ms"] = connection_time

            if conn:
                db_performance["connection_success"] = True
                print(f"  ✅ Connection Time: {connection_time:.2f}ms")

                # Test simple query performance
                start_time = time.perf_counter()
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                query_time = (time.perf_counter() - start_time) * 1000

                db_performance["simple_query_time_ms"] = query_time
                db_performance["query_success"] = result is not None

                print(f"  ✅ Query Time: {query_time:.2f}ms")

                cursor.close()
                conn.close()
            else:
                print("  ❌ Database connection failed")

        except Exception as e:
            print(f"  ❌ Database performance test failed: {e}")

        return db_performance

    async def test_adapter_performance(self) -> Dict[str, Any]:
        """Test adapter initialization and basic operation performance."""
        print("\n🔄 Testing Adapter Performance...")

        adapter_performance = {
            "chat_adapter": {"init_time_ms": 0, "success": False},
            "code_adapter": {"init_time_ms": 0, "success": False},
        }

        # Test Chat Adapter Performance
        try:
            from src.project_context.ingestion.adapters.chat_adapter import ChatAdapter
            from src.project_context.ingestion.base_adapter import (
                AdapterConfig,
                BatchMode,
            )

            config = AdapterConfig(
                adapter_id="perf_test_chat",
                source_type="chat",
                batch_mode=BatchMode.STREAMING,
                batch_size=10,
                source_config={"input_format": "jsonl"},
            )

            start_time = time.perf_counter()
            chat_adapter = ChatAdapter(config)
            init_time = (time.perf_counter() - start_time) * 1000

            adapter_performance["chat_adapter"]["init_time_ms"] = init_time
            adapter_performance["chat_adapter"]["success"] = True

            status = "✅" if init_time < 50 else "⚠️" if init_time < 200 else "❌"
            print(f"  {status} Chat Adapter Init: {init_time:.2f}ms")

        except Exception as e:
            print(f"  ❌ Chat Adapter failed: {e}")

        # Test Code Adapter Performance
        try:
            from src.project_context.ingestion.adapters.code_adapter import CodeAdapter

            config = AdapterConfig(
                adapter_id="perf_test_code",
                source_type="code",
                batch_mode=BatchMode.BATCH,
                batch_size=10,
                source_config={"scan_directories": []},
            )

            start_time = time.perf_counter()
            code_adapter = CodeAdapter(config)
            init_time = (time.perf_counter() - start_time) * 1000

            adapter_performance["code_adapter"]["init_time_ms"] = init_time
            adapter_performance["code_adapter"]["success"] = True

            status = "✅" if init_time < 50 else "⚠️" if init_time < 200 else "❌"
            print(f"  {status} Code Adapter Init: {init_time:.2f}ms")

        except Exception as e:
            print(f"  ❌ Code Adapter failed: {e}")

        return adapter_performance

    async def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage patterns during component loading."""
        print("\n💾 Testing Memory Usage Patterns...")

        memory_usage = {
            "baseline_memory_mb": 0,
            "peak_memory_mb": 0,
            "memory_growth_mb": 0,
            "memory_efficiency_score": 0.0,
        }

        try:
            # Baseline memory usage
            baseline_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_usage["baseline_memory_mb"] = baseline_memory

            # Load components and measure peak memory
            components = [
                "src.project_context.ingestion.adapters.chat_adapter",
                "src.project_context.ingestion.adapters.code_adapter",
                "src.project_context.tools.analysis",
                "src.project_context.tools.discovery",
            ]

            peak_memory = baseline_memory

            for component in components:
                try:
                    __import__(component)
                    current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    peak_memory = max(peak_memory, current_memory)
                except ImportError:
                    pass  # Skip failed imports

            memory_usage["peak_memory_mb"] = peak_memory
            memory_usage["memory_growth_mb"] = peak_memory - baseline_memory

            # Calculate efficiency score (lower growth = higher score)
            if memory_usage["memory_growth_mb"] < 50:
                memory_usage["memory_efficiency_score"] = 10.0
            elif memory_usage["memory_growth_mb"] < 100:
                memory_usage["memory_efficiency_score"] = 8.0
            elif memory_usage["memory_growth_mb"] < 200:
                memory_usage["memory_efficiency_score"] = 6.0
            else:
                memory_usage["memory_efficiency_score"] = 4.0

            print(f"  📊 Baseline Memory: {baseline_memory:.1f}MB")
            print(f"  📈 Peak Memory: {peak_memory:.1f}MB")
            print(f"  📏 Memory Growth: {memory_usage['memory_growth_mb']:.1f}MB")
            print(
                f"  ⭐ Efficiency Score: {memory_usage['memory_efficiency_score']:.1f}/10"
            )

        except Exception as e:
            print(f"  ❌ Memory usage test failed: {e}")

        return memory_usage

    async def calculate_overall_performance_score(self) -> float:
        """Calculate overall performance score based on all benchmarks."""
        print("\n🏆 Calculating Overall Performance Score...")

        score_components = {
            "import_performance": 0.0,
            "database_performance": 0.0,
            "adapter_performance": 0.0,
            "memory_efficiency": 0.0,
        }

        # Import performance score
        import_times = self.results["performance_benchmarks"].get(
            "component_import_times", {}
        )
        if import_times:
            avg_import_time = sum(t for t in import_times.values() if t > 0) / len(
                [t for t in import_times.values() if t > 0]
            )
            score_components["import_performance"] = max(0, 10 - (avg_import_time / 10))

        # Database performance score
        db_perf = self.results["performance_benchmarks"].get("database_performance", {})
        if db_perf.get("connection_success"):
            conn_time = db_perf.get("connection_time_ms", 1000)
            score_components["database_performance"] = max(0, 10 - (conn_time / 100))

        # Adapter performance score
        adapter_perf = self.results["performance_benchmarks"].get(
            "adapter_performance", {}
        )
        adapter_scores = []
        for adapter_name, adapter_data in adapter_perf.items():
            if adapter_data.get("success"):
                init_time = adapter_data.get("init_time_ms", 1000)
                adapter_scores.append(max(0, 10 - (init_time / 20)))

        if adapter_scores:
            score_components["adapter_performance"] = sum(adapter_scores) / len(
                adapter_scores
            )

        # Memory efficiency score
        score_components["memory_efficiency"] = self.results[
            "resource_utilization"
        ].get("memory_efficiency_score", 0.0)

        # Calculate weighted overall score
        weights = {
            "import_performance": 0.2,
            "database_performance": 0.3,
            "adapter_performance": 0.3,
            "memory_efficiency": 0.2,
        }

        overall_score = sum(
            score_components[component] * weights[component]
            for component in score_components
        )

        print(
            f"  🔍 Import Performance: {score_components['import_performance']:.1f}/10 (Weight: 20%)"
        )
        print(
            f"  🗄️ Database Performance: {score_components['database_performance']:.1f}/10 (Weight: 30%)"
        )
        print(
            f"  🔄 Adapter Performance: {score_components['adapter_performance']:.1f}/10 (Weight: 30%)"
        )
        print(
            f"  💾 Memory Efficiency: {score_components['memory_efficiency']:.1f}/10 (Weight: 20%)"
        )
        print(f"  🏆 Overall Performance Score: {overall_score:.1f}/10")

        return overall_score

    async def execute_performance_validation(self):
        """Execute complete performance validation suite."""
        print("=" * 80)
        print("PHASE 1 PERFORMANCE VALIDATION")
        print("=" * 80)
        print(f"Validation Time: {self.results['validation_timestamp']}")

        try:
            # Execute all performance tests
            self.results["system_info"] = await self.collect_system_info()

            # Performance benchmarks
            benchmarks = await self.benchmark_core_components()
            benchmarks["database_performance"] = await self.test_database_performance()
            benchmarks["adapter_performance"] = await self.test_adapter_performance()
            self.results["performance_benchmarks"] = benchmarks

            # Resource utilization
            self.results["resource_utilization"] = await self.test_memory_usage()

            # Calculate overall score
            self.results[
                "overall_performance_score"
            ] = await self.calculate_overall_performance_score()

            # Generate final report
            await self.generate_performance_report()

        except Exception as e:
            print(f"\n❌ Critical error during performance validation: {e}")
            print(traceback.format_exc())
            self.results["critical_error"] = str(e)

    async def generate_performance_report(self):
        """Generate comprehensive performance report."""
        print(f"\n{'='*80}")
        print("PERFORMANCE VALIDATION REPORT")
        print(f"{'='*80}")

        # Save detailed results
        report_file = self.project_root / "PHASE1_PERFORMANCE_VALIDATION_REPORT.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)

        # Performance assessment
        score = self.results["overall_performance_score"]

        if score >= 8.0:
            print("🎉 EXCELLENT PERFORMANCE - System exceeds performance expectations")
        elif score >= 6.0:
            print("✅ GOOD PERFORMANCE - System meets performance requirements")
        elif score >= 4.0:
            print(
                "⚠️ ACCEPTABLE PERFORMANCE - System functional but could be optimized"
            )
        else:
            print(
                "❌ PERFORMANCE CONCERNS - System needs optimization before production"
            )

        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Overall Score: {score:.1f}/10")
        print(
            f"   System Memory: {self.results['system_info'].get('memory_available_gb', 0):.1f}GB available"
        )
        print(f"   CPU Cores: {self.results['system_info'].get('cpu_count', 0)}")

        if score >= 6.0:
            print(f"\n🚀 PERFORMANCE VALIDATION PASSED - Ready for production!")
        else:
            print(
                f"\n⚠️ Performance optimization recommended before production deployment"
            )

        print(f"\n📁 Detailed performance report saved to: {report_file}")

        return score >= 6.0


async def main():
    """Main performance validation execution."""
    validator = PerformanceValidator()
    await validator.execute_performance_validation()

    # Return appropriate exit code based on performance score
    score = validator.results.get("overall_performance_score", 0)
    if score >= 6.0:
        print(f"\n🎯 PERFORMANCE VALIDATION PASSED!")
        return 0
    else:
        print(f"\n⚠️ PERFORMANCE VALIDATION NEEDS ATTENTION")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
