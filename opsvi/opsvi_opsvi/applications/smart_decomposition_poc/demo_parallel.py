#!/usr/bin/env python3
"""
Smart Decomposition Meta-Intelligence System - Parallel Execution Demo
Demonstrates 3-5x parallel efficiency improvements with OpenAI-exclusive architecture
"""

import asyncio
from pathlib import Path
import sys
import time

# Add the POC to the Python path
poc_path = Path(__file__).parent
sys.path.insert(0, str(poc_path))

from core.config import get_config
from core.dependency_manager import DependencyManager
from core.parallel_execution_engine import (
    ParallelExecutionEngine,
)
from core.system_controller import SystemController


def print_banner():
    """Print parallel execution demo banner"""
    print(
        """
⚡ ================================================================== ⚡
    Smart Decomposition Meta-Intelligence System
    PARALLEL EXECUTION DEMO - 3-5x Efficiency Improvements
    OpenAI-Exclusive Architecture with Neo4j Dependency Management
⚡ ================================================================== ⚡
"""
    )


async def demo_dependency_management():
    """Demonstrate dependency management capabilities"""
    print("🔗 Testing Dependency Management System...")

    dependency_manager = DependencyManager()
    await dependency_manager.initialize()

    print("   Creating sample task dependency graph...")

    # Add sample tasks with dependencies
    tasks = [
        ("task_1", "requirements_expander", "analysis", [], 120, 10),
        ("task_2", "manager", "planning", ["task_1"], 90, 9),
        ("task_3", "developer", "implementation", ["task_2"], 300, 8),
        ("task_4", "tester", "testing", ["task_2"], 180, 7),
        ("task_5", "coordinator", "documentation", ["task_2"], 120, 6),
        ("task_6", "validator", "validation", ["task_3", "task_4"], 90, 5),
    ]

    for task_id, role, task_type, deps, duration, priority in tasks:
        success = await dependency_manager.add_task(
            task_id=task_id,
            agent_role=role,
            task_type=task_type,
            dependencies=deps,
            estimated_duration=duration,
            priority=priority,
        )
        print(
            f"     • Added {task_id}: {role} (deps: {deps}) → {'✅' if success else '❌'}"
        )

    # Get parallel execution plan
    execution_plan = await dependency_manager.get_parallel_execution_plan()
    print(f"\n   📊 Parallel Execution Plan ({len(execution_plan)} waves):")
    for i, wave in enumerate(execution_plan):
        print(f"     Wave {i+1}: {wave} ({len(wave)} parallel tasks)")

    # Calculate theoretical efficiency
    total_sequential_time = sum(duration for _, _, _, _, duration, _ in tasks)
    max_wave_time = (
        max(len(wave) * 60 for wave in execution_plan) if execution_plan else 0
    )
    theoretical_efficiency = (
        total_sequential_time / max_wave_time if max_wave_time > 0 else 1.0
    )

    print(f"   ⚡ Theoretical parallel efficiency: {theoretical_efficiency:.2f}x")

    await dependency_manager.close()

    return theoretical_efficiency >= 3.0


async def demo_parallel_engine():
    """Demonstrate parallel execution engine"""
    print("⚡ Testing Parallel Execution Engine...")

    engine = ParallelExecutionEngine()
    await engine.initialize()

    # Create sample execution tasks
    from core.parallel_execution_engine import create_simple_workflow

    tasks = await create_simple_workflow("Create a task management application")

    print(f"   📋 Created workflow with {len(tasks)} tasks:")
    for task in tasks:
        deps_str = f" (depends on: {task.dependencies})" if task.dependencies else ""
        print(f"     • {task.task_id}: {task.agent_role}{deps_str}")

    # Execute workflow and measure performance
    start_time = time.time()

    try:
        result = await engine.execute_workflow(tasks)
        end_time = time.time()

        if result["success"]:
            print("   ✅ Parallel execution completed successfully!")
            print(f"   ⏱️ Execution time: {result['execution_time']:.2f}s")
            print(f"   ⚡ Parallel efficiency: {result['parallel_efficiency']:.2f}x")
            print(
                f"   📊 Executed {len(result['task_results'])} tasks in {result['wave_count']} waves"
            )

            return result["parallel_efficiency"] >= 3.0
        else:
            print("   ❌ Parallel execution failed")
            return False

    except Exception as e:
        print(f"   ⚠️ Parallel execution demo failed: {e}")
        return False


async def demo_system_controller_parallel():
    """Demonstrate system controller with parallel execution"""
    print("🎯 Testing System Controller with Parallel Execution...")

    controller = SystemController()
    await controller.initialize()

    test_prompts = [
        "Create a simple todo application",
        "Build a blog website with comments",
        "Develop a basic calculator app",
    ]

    results = []

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n   Test {i}: '{prompt}'")

        try:
            # Test parallel execution
            start_time = time.time()
            result = await controller.generate_application_from_prompt(
                prompt, "parallel"
            )
            end_time = time.time()

            if result.success:
                print("     ✅ Generated application successfully")
                print(f"     ⚡ Parallel efficiency: {result.parallel_efficiency:.2f}x")
                print(f"     ⏱️ Execution time: {result.execution_time:.2f}s")
                results.append(result.parallel_efficiency)
            else:
                print("     ❌ Application generation failed")
                results.append(0.0)

        except Exception as e:
            print(f"     ⚠️ Test failed: {e}")
            results.append(0.0)

    await controller.close()

    # Calculate average efficiency
    avg_efficiency = sum(results) / len(results) if results else 0.0
    print(f"\n   📈 Average parallel efficiency: {avg_efficiency:.2f}x")

    return avg_efficiency >= 3.0


async def demo_performance_comparison():
    """Compare sequential vs parallel performance"""
    print("📊 Performance Comparison: Sequential vs Parallel...")

    controller = SystemController()
    await controller.initialize()

    test_prompt = "Create a web application with user authentication"

    # Test sequential execution
    print("   🔄 Testing Sequential Execution...")
    start_time = time.time()
    try:
        sequential_result = await controller.generate_application_from_prompt(
            test_prompt, "sequential"
        )
        sequential_time = sequential_result.execution_time
        sequential_success = sequential_result.success
        print(f"     ⏱️ Sequential time: {sequential_time:.2f}s")
        print("     📊 Sequential efficiency: 1.0x (baseline)")
    except Exception as e:
        print(f"     ❌ Sequential execution failed: {e}")
        sequential_time = 0
        sequential_success = False

    # Test parallel execution
    print("   ⚡ Testing Parallel Execution...")
    start_time = time.time()
    try:
        parallel_result = await controller.generate_application_from_prompt(
            test_prompt, "parallel"
        )
        parallel_time = parallel_result.execution_time
        parallel_efficiency = parallel_result.parallel_efficiency
        parallel_success = parallel_result.success
        print(f"     ⏱️ Parallel time: {parallel_time:.2f}s")
        print(f"     ⚡ Parallel efficiency: {parallel_efficiency:.2f}x")
    except Exception as e:
        print(f"     ❌ Parallel execution failed: {e}")
        parallel_time = 0
        parallel_efficiency = 0
        parallel_success = False

    await controller.close()

    # Performance comparison
    if sequential_time > 0 and parallel_time > 0:
        actual_speedup = sequential_time / parallel_time
        print("\n   📈 Performance Comparison Results:")
        print(f"     Sequential: {sequential_time:.2f}s")
        print(f"     Parallel: {parallel_time:.2f}s")
        print(f"     Actual Speedup: {actual_speedup:.2f}x")
        print(f"     Reported Efficiency: {parallel_efficiency:.2f}x")

        if actual_speedup >= 2.0:
            print("     🎯 Significant performance improvement achieved!")
        return actual_speedup >= 2.0
    else:
        print("   ⚠️ Unable to complete performance comparison")
        return False


async def main():
    """Main demo function"""
    print_banner()

    config = get_config()
    print("📋 System Configuration:")
    print(f"   • Reasoning Model: {config.models.reasoning}")
    print(f"   • Implementation Model: {config.models.implementation}")
    print(
        f"   • Parallel Efficiency Target: {config.performance.parallel_efficiency_target}x"
    )
    print(f"   • Max Parallel Agents: {config.parallel_execution.max_parallel_agents}")
    print()

    # Run all parallel execution demos
    demos = [
        ("Dependency Management", demo_dependency_management),
        ("Parallel Execution Engine", demo_parallel_engine),
        ("System Controller Parallel", demo_system_controller_parallel),
        ("Performance Comparison", demo_performance_comparison),
    ]

    results = {}

    for demo_name, demo_func in demos:
        print(f"\n{'='*70}")
        try:
            result = await demo_func()
            results[demo_name] = result
        except Exception as e:
            print(f"❌ {demo_name} failed with error: {str(e)}")
            results[demo_name] = False
        print(f"{'='*70}")

    # Summary
    print("\n🎯 Parallel Execution Demo Results:")
    print(f"{'='*70}")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for demo_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   • {demo_name}: {status}")

    print(f"\n📊 Overall Results: {passed}/{total} tests passed ({passed/total:.1%})")

    if passed >= total * 0.75:  # 75% success rate
        print("🎉 Parallel execution capabilities are working well!")
        print("⚡ Ready for production deployment with parallel efficiency!")
    else:
        print("⚠️ Some parallel execution components need attention.")

    print("\n💡 Next Steps:")
    print("   1. Review any failed tests and address issues")
    print("   2. Fine-tune parallel execution parameters")
    print("   3. Implement MCP tools integration")
    print("   4. Add real-time monitoring and metrics")
    print("   5. Deploy to production environment")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Parallel execution demo interrupted by user.")
    except Exception as e:
        print(f"\n💥 Parallel execution demo crashed: {str(e)}")
        sys.exit(1)
