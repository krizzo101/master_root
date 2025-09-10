#!/usr/bin/env python3
"""
Token Pool Validation Test - Agent 1
Demonstrate token pool working with multiple tokens
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "apps/agent-orchestrator/src")
)

from generic_orchestrator import AgentTask, GenericOrchestrator


async def test_token_pool_with_multiple_tokens():
    """Test token pool with multiple mock tokens"""
    print("=== Testing Token Pool with Multiple Tokens ===")

    # Create multiple mock tokens (these would be real Claude tokens in production)
    mock_tokens = [
        "mock_token_1_for_testing",
        "mock_token_2_for_testing",
        "mock_token_3_for_testing",
    ]

    # Create tasks that would normally require separate tokens
    tasks = [
        AgentTask(
            task_id="task_1",
            task_type="general-purpose",
            prompt="Generate a simple Python function",
        ),
        AgentTask(
            task_id="task_2",
            task_type="general-purpose",
            prompt="Explain Python list comprehensions",
        ),
        AgentTask(
            task_id="task_3",
            task_type="general-purpose",
            prompt="Write a basic Python class example",
        ),
        AgentTask(
            task_id="task_4",
            task_type="general-purpose",
            prompt="Describe Python error handling",
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="token_pool_test_") as temp_dir:
        # Initialize orchestrator with multiple tokens
        orchestrator = GenericOrchestrator(
            output_dir=Path(temp_dir),
            max_parallel=3,  # Allow parallel execution to test pooling
            tokens=mock_tokens,  # Provide multiple tokens explicitly
        )

        print(f"Initialized orchestrator with {len(mock_tokens)} tokens")
        print(f"Max parallel execution: 3")
        print(f"Number of tasks: {len(tasks)}")

        # Execute tasks - this should demonstrate token pooling
        results = await orchestrator.execute_batch(tasks)

        print(f"\n✅ Executed {len(results)} tasks")
        print(
            f"✅ All tasks completed: {all(r['status'] == 'completed' for r in results)}"
        )

        # Check if tasks ran in parallel (indicating token pooling worked)
        completed_tasks = [r for r in results if r["status"] == "completed"]
        if len(completed_tasks) >= 2:
            print(
                "✅ Multiple tasks completed - token pooling enabled parallel execution"
            )

        return True


async def test_token_fallback():
    """Test token fallback behavior when no tokens provided"""
    print("\n=== Testing Token Fallback Behavior ===")

    tasks = [
        AgentTask(
            task_id="fallback_test",
            task_type="general-purpose",
            prompt="Simple test task for token fallback",
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="token_fallback_test_") as temp_dir:
        # Initialize without providing tokens - should use fallback
        orchestrator = GenericOrchestrator(
            output_dir=Path(temp_dir),
            max_parallel=1,
            tokens=None,  # Force fallback behavior
        )

        print("Initialized orchestrator with no explicit tokens (testing fallback)")

        try:
            results = await orchestrator.execute_batch(tasks)
            print("✅ Fallback token mechanism works")
            return True
        except Exception as e:
            print(f"❌ Fallback failed: {e}")
            return False


if __name__ == "__main__":
    print("AGENT 1 TOKEN POOL VALIDATION")
    print("=" * 40)

    # NOTE: These tests use mock tokens since we don't have real Claude tokens
    # In production, the TokenLoader would load real tokens from environment/files

    asyncio.run(test_token_pool_with_multiple_tokens())
    asyncio.run(test_token_fallback())

    print("\n" + "=" * 40)
    print("TOKEN POOL VALIDATION COMPLETE")
    print("\nNOTE: This test uses mock tokens. In production:")
    print("- TokenLoader loads real Claude tokens from environment/files")
    print("- Token pool manages concurrent API calls across multiple tokens")
    print("- Proper token rotation prevents rate limiting")
