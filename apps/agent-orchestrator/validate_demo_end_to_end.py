#!/usr/bin/env python3
"""
End-to-End Validation for Agent Orchestrator Demo

This script runs a simplified version of the demo to prove the system works
end-to-end with actual agent execution (but shortened to save time).
"""

import asyncio
import sys
import tempfile
from pathlib import Path

from src.generic_orchestrator import AgentTask, GenericOrchestrator


async def run_validation_demo():
    """Run a simplified demo to validate end-to-end functionality"""

    print("🚀 Running End-to-End Validation Demo")
    print("=" * 50)

    # Create temporary output directory
    temp_dir = Path(tempfile.mkdtemp(prefix="validation_demo_"))
    print(f"📁 Output directory: {temp_dir}")

    try:
        # Create simple validation tasks
        tasks = [
            AgentTask(
                task_id="validation_task_1",
                task_type="test_agent",
                prompt="""You are a validation test agent. Your task is to confirm the Agent Orchestrator system is working correctly.

Please provide a brief response (2-3 sentences) confirming:
1. You received this task successfully
2. You can process instructions
3. You can return structured output

Return your response in JSON format with a 'status' field set to 'success' and a 'message' field with your confirmation.""",
                context={"test_type": "basic_functionality"},
                dependencies=[],
            ),
            AgentTask(
                task_id="validation_task_2",
                task_type="dependency_test_agent",
                prompt="""You are a dependency validation agent. Your task depends on the previous validation task completing.

Please confirm:
1. You understand this task runs after the first validation task
2. The dependency management system is working
3. The orchestrator can handle sequential execution

Return your response in JSON format with 'status': 'success' and a brief 'message' confirming dependency handling works.""",
                context={"test_type": "dependency_validation"},
                dependencies=["validation_task_1"],
            ),
        ]

        print(f"📋 Created {len(tasks)} validation tasks")

        # Initialize orchestrator
        orchestrator = GenericOrchestrator(
            output_dir=temp_dir,
            max_parallel=2,
            use_optimizations=True,
            workflow_name="End-to-End Validation Demo",
        )

        print("🤖 Orchestrator initialized")

        # Define task generator
        def task_generator():
            return tasks

        # Track progress
        progress_updates = []

        async def result_processor(results):
            print(f"📊 Processing {len(results)} results...")

            success_count = 0
            for result in results:
                task_id = result.get("task_id", "unknown")
                status = result.get("status", "unknown")

                if status == "completed":
                    success_count += 1
                    print(f"   ✅ {task_id}: SUCCESS")

                    # Check if result has expected structure
                    task_result = result.get("result", {})
                    if isinstance(task_result, dict) and "status" in task_result:
                        print(f"      Result status: {task_result.get('status')}")
                        if "message" in task_result:
                            message = task_result["message"][
                                :100
                            ]  # Truncate for display
                            print(f"      Message: {message}...")
                else:
                    print(
                        f"   ❌ {task_id}: FAILED - {result.get('error', 'Unknown error')}"
                    )

            return success_count == len(results)

        # Run the orchestrated demo
        print("\n🎬 Starting demo execution...")
        result = await orchestrator.run(
            task_generator=task_generator, result_processor=result_processor
        )

        # Check results
        metrics = result.get("metrics", {})
        completed = metrics.get("completed", 0)
        failed = metrics.get("failed", 0)
        total = metrics.get("total", 0)

        print(f"\n📈 Execution Summary:")
        print(f"   Total tasks: {total}")
        print(f"   Completed: {completed}")
        print(f"   Failed: {failed}")
        print(
            f"   Success rate: {completed/total*100:.1f}%"
            if total > 0
            else "   Success rate: 0%"
        )

        # Validate output structure
        expected_files = [
            temp_dir / "metadata" / "workflow_info.json",
            temp_dir / "deliverables" / "workflow_completion_report.json",
            temp_dir / "agents" / "validation_task_1.json",
            temp_dir / "agents" / "validation_task_2.json",
        ]

        print(f"\n📁 Checking output files:")
        files_found = 0
        for file_path in expected_files:
            if file_path.exists():
                files_found += 1
                print(f"   ✅ {file_path.name}")
            else:
                print(f"   ❌ {file_path.name} - NOT FOUND")

        # Overall validation result
        print(f"\n" + "=" * 50)

        validation_success = (
            completed == total
            and failed == 0  # All tasks completed
            and files_found  # No failures
            == len(expected_files)  # All expected files present
        )

        if validation_success:
            print("🎉 END-TO-END VALIDATION SUCCESSFUL!")
            print("   ✅ All tasks completed successfully")
            print("   ✅ All expected output files generated")
            print("   ✅ Agent orchestration working correctly")
            print("\n🚀 The demo system is ready for full demonstrations!")
            return True
        else:
            print("❌ END-TO-END VALIDATION FAILED!")
            print("   Check the issues above and resolve before running full demos")
            return False

    except Exception as e:
        print(f"\n💥 Validation failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Optional cleanup (comment out to preserve results for inspection)
        # import shutil
        # shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n📁 Validation results preserved in: {temp_dir}")


async def main():
    """Main validation runner"""
    print("🧪 AGENT ORCHESTRATOR END-TO-END VALIDATION")
    print("This validation runs actual agents to prove the system works")
    print("=" * 60)

    success = await run_validation_demo()

    if success:
        print("\n✅ VALIDATION COMPLETE - Demo system is fully functional!")
        print("\nYou can now run the full demonstrations:")
        print("  python comprehensive_demo.py basic")
        print("  python comprehensive_demo.py parallel")
        print("  python comprehensive_demo.py dependencies")
        print("  python comprehensive_demo.py monitoring")
        print("  python comprehensive_demo.py full")
        return 0
    else:
        print("\n❌ VALIDATION FAILED - Fix issues before running demos")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
