#!/usr/bin/env python3
"""
PracticalOrchestrator Example - Optimized for 10 Parallel Execution
"""

import asyncio
import sys
from pathlib import Path

sys.path.append("src")
from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator


async def phase1_completion_example():
    """Example showing how to use PracticalOrchestrator for Phase 1 completion"""

    print("🚀 PRACTICAL ORCHESTRATOR - PHASE 1 COMPLETION EXAMPLE")
    print("=" * 60)

    # Create orchestrator with optimal settings
    orchestrator = PracticalOrchestrator(
        output_dir="./phase1_completion_output",
        max_parallel=10,  # Now properly supported!
        enable_monitoring=True,
        enable_quality_reports=True,
    )

    # Progress monitoring
    def progress_monitor(event_type: str, data: dict):
        import time

        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] 📊 {event_type}: {data}")

    orchestrator.set_progress_callback(progress_monitor)

    # Create Phase 1 completion tasks (realistic example)
    tasks = [
        PracticalAgentTask(
            task_id="implement_chat_adapter",
            task_type="development-specialist",
            prompt="""Implement the chat adapter for the unified context system.

            Requirements:
            1. Create ChatAdapter class in src/project_context/ingestion/adapters/chat_adapter.py
            2. Implement async methods for chat data ingestion
            3. Support JSONL and JSON format inputs
            4. Include proper error handling and logging
            5. Add deduplication and checkpoint functionality
            """,
            phase_id="adapters",
            priority="high",
            tags=["adapter", "chat", "ingestion"],
        ),
        PracticalAgentTask(
            task_id="implement_code_adapter",
            task_type="development-specialist",
            prompt="""Implement the code adapter for the unified context system.

            Requirements:
            1. Create CodeAdapter class in src/project_context/ingestion/adapters/code_adapter.py
            2. Implement file system scanning and code analysis
            3. Support multiple programming languages
            4. Extract functions, classes, and module information
            5. Include IDE integration capabilities
            """,
            dependencies=[],  # Can run in parallel with chat_adapter
            phase_id="adapters",
            priority="high",
            tags=["adapter", "code", "analysis"],
        ),
        PracticalAgentTask(
            task_id="integrate_with_mcp",
            task_type="api-integration-specialist",
            prompt="""Integrate the adapters with MCP (Model Context Protocol) tools.

            Requirements:
            1. Update existing MCP tools to use new backend
            2. Ensure proper API compatibility
            3. Test integration with chat and code adapters
            4. Update tool documentation
            5. Handle backwards compatibility
            """,
            dependencies=["implement_chat_adapter", "implement_code_adapter"],
            phase_id="integration",
            priority="normal",
            tags=["mcp", "integration", "api"],
        ),
        PracticalAgentTask(
            task_id="comprehensive_testing",
            task_type="qa-testing-guru",
            prompt="""Create comprehensive test suite for the unified context system.

            Requirements:
            1. Unit tests for all adapters
            2. Integration tests for the complete pipeline
            3. Database validation tests
            4. Performance benchmarks
            5. Error handling validation
            """,
            dependencies=["integrate_with_mcp"],
            phase_id="testing",
            priority="normal",
            tags=["testing", "validation", "qa"],
        ),
        PracticalAgentTask(
            task_id="create_documentation",
            task_type="technical-writer",
            prompt="""Create complete documentation for Phase 1 implementation.

            Requirements:
            1. Architecture overview and design decisions
            2. API reference for all adapters
            3. Installation and setup guide
            4. Usage examples and tutorials
            5. Troubleshooting guide
            """,
            dependencies=["comprehensive_testing"],
            phase_id="documentation",
            priority="low",
            tags=["documentation", "api", "guide"],
        ),
    ]

    print(f"📋 Created {len(tasks)} tasks with proper dependencies")
    print(f"⚡ Will execute with up to {orchestrator.max_parallel} parallel tasks")
    print(f"🔧 Token pool size: {orchestrator.token_pool.size()}")

    # Show session mapping before execution
    print(f"\n🔍 Session ID Mapping (for monitoring):")
    for task in tasks:
        print(f"  {task.task_id} → {task.session_id}")
        print(f"    Monitor: tail -f {task.get_log_path()}")

    print(f"\n🚀 Starting execution...")

    # Execute tasks
    results = await orchestrator.execute_batch(tasks)

    # Show final results
    completed = len(
        [r for r in results if isinstance(r, dict) and r.get("status") == "completed"]
    )
    failed = len(
        [r for r in results if isinstance(r, dict) and r.get("status") == "failed"]
    )

    print(f"\n📊 EXECUTION COMPLETE")
    print(f"✅ Completed: {completed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {completed/len(tasks):.1%}")

    # Show output locations
    print(f"\n📁 Generated Files:")
    print(f"   Task outputs: ./phase1_completion_output/tasks/")
    print(f"   Quality report: ./phase1_completion_output/quality_report.json")

    return results


async def simple_parallel_demo():
    """Simple demo showing 10 parallel tasks"""

    print("\n🧪 SIMPLE PARALLEL EXECUTION DEMO")
    print("=" * 40)

    orchestrator = PracticalOrchestrator(
        output_dir="./parallel_demo_output", max_parallel=10
    )

    # Create 10 simple parallel tasks
    tasks = []
    for i in range(10):
        task = PracticalAgentTask(
            task_id=f"parallel_task_{i+1:02d}",
            task_type="development-specialist",
            prompt=f"Create a simple Python function called 'task_{i+1}' that returns 'Task {i+1} completed'",
            phase_id="parallel_demo",
            priority="normal",
            tags=["demo", "parallel"],
        )
        tasks.append(task)

    print(f"🚀 Executing {len(tasks)} tasks in parallel...")

    import time

    start_time = time.time()
    results = await orchestrator.execute_batch(tasks)
    end_time = time.time()

    completed = len(
        [r for r in results if isinstance(r, dict) and r.get("status") == "completed"]
    )

    print(
        f"⚡ Completed {completed}/{len(tasks)} tasks in {end_time - start_time:.2f} seconds"
    )
    print(f"🎉 Parallel execution working perfectly!")

    return results


if __name__ == "__main__":
    print("Choose demo:")
    print("1. Phase 1 Completion Example (realistic workflow)")
    print("2. Simple Parallel Demo (10 tasks)")

    try:
        choice = input("Enter choice [1/2]: ").strip()

        if choice == "1":
            results = asyncio.run(phase1_completion_example())
        elif choice == "2":
            results = asyncio.run(simple_parallel_demo())
        else:
            print("Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Demo cancelled")
    except EOFError:
        print("\n🤖 Running Phase 1 completion example by default...")
        results = asyncio.run(phase1_completion_example())
