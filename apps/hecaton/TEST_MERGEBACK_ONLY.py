#!/usr/bin/env python3
"""
Test script to verify merge-back wiring without actual Claude execution
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hecaton.config.merge_back import MergeBackConfig
from hecaton.orchestration.merger import Merger
from hecaton.orchestration.send_api import OrchestrationState, SendAPIOrchestrator
from hecaton.resources.secure_token_pool import SecureTokenPool
from hecaton.resources.worktree import WorktreeManager


class MockExecutor:
    """Mock executor that simulates patch creation"""

    async def execute_task(self, task):
        """Simulate task execution and return a patch manifest"""
        print(f"  Mock executing: {task['id']}")

        # Simulate creating a patch manifest
        if task.get("run_id"):
            return {
                "status": "completed",
                "output": "Mock changes applied",
                "patch_manifest": {
                    "patch_file": f"/tmp/mock_{task['id']}.patch",
                    "agent_id": task["id"],
                    "agent_role": task.get("agent_type", "code"),
                    "commit_sha": "abc123",
                    "files_changed": ["mock_file.py"],
                    "insertions": 10,
                    "deletions": 5,
                    "task_hash": "hash123",
                    "run_id": task["run_id"],
                    "sequence": task.get("sequence", 0),
                },
            }
        else:
            return {
                "status": "completed",
                "output": "Mock changes (no patch - missing run_id)",
            }


async def test_mergeback_wiring():
    """Test that merge-back is properly wired"""

    print("=== Testing HECATON Merge-Back Wiring ===\n")

    # 1. Initialize components
    print("1. Initializing components...")
    token_pool = SecureTokenPool(tokens=["test-token-1", "test-token-2"])
    worktree_manager = WorktreeManager(
        base_path="/tmp/hecaton_test_worktrees", repo_path=os.getcwd()
    )
    merge_config = MergeBackConfig(
        enabled=True,
        dry_run=True,  # Don't actually create PRs
        gate_commands=[],  # Skip gates for test
    )

    # 2. Create orchestrator with mock executor
    print("2. Creating orchestrator with mock executor...")
    mock_executor = MockExecutor()

    orchestrator = SendAPIOrchestrator(
        executor=mock_executor,
        token_pool=token_pool,
        worktree_manager=worktree_manager,
        merge_config=merge_config,
        max_parallel=2,
    )

    # 3. Test the execute method
    print("3. Running orchestration with 2 agents...\n")

    result = await orchestrator.execute(
        task="Test task for merge-back verification", num_agents=2
    )

    # 4. Check results
    print("\n=== Results ===")
    print(f"Phase: {result.get('phase')}")
    print(f"Agents completed: {len(result.get('results', {}))}")

    # 5. Check if merge-back was attempted
    merge_report = result.get("merge_report")
    if merge_report:
        print("\n✅ MERGE-BACK WAS CALLED!")
        print(f"  Patches applied: {merge_report.get('patches_applied', 0)}")
        print(f"  Conflicts: {merge_report.get('conflicts', 0)}")
        if merge_report.get("error"):
            print(f"  Error: {merge_report['error']}")
    else:
        print("\n❌ MERGE-BACK WAS NOT CALLED")
        print("  This means the wiring is still incomplete")

    # 6. Check for run_id in logs
    if "run_" in str(result):
        print("\n✅ Run ID was generated")
    else:
        print("\n❌ No run_id found in results")

    return merge_report is not None


if __name__ == "__main__":
    # Set test mode
    os.environ["HECATON_TEST_MODE"] = "1"

    # Run test
    success = asyncio.run(test_mergeback_wiring())

    if success:
        print("\n✅ MERGE-BACK WIRING TEST PASSED")
        sys.exit(0)
    else:
        print("\n❌ MERGE-BACK WIRING TEST FAILED")
        sys.exit(1)
