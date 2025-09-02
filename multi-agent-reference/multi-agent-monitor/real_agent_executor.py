#!/usr/bin/env python3
"""
REAL Agent Executor - Actually calls Claude via subprocess
No fake implementations, no hardcoded code, just real agent execution
"""

import asyncio
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RealAgentExecutor:
    """Execute REAL Claude agents via subprocess"""

    def __init__(self, tokens: List[str]):
        """Initialize with list of Claude tokens for parallel execution"""
        self.tokens = tokens
        self.token_index = 0
        self.active_processes = {}

    def get_next_token(self) -> str:
        """Round-robin token selection"""
        token = self.tokens[self.token_index % len(self.tokens)]
        self.token_index += 1
        return token

    async def execute_claude(
        self, task: str, agent_id: str, cwd: Optional[str] = None, timeout: int = 600
    ) -> Dict:
        """
        ACTUALLY execute Claude via subprocess

        This is REAL - it spawns 'claude -p "task"' as a subprocess
        """
        # Get token for this agent
        token = self.get_next_token()

        # Build command - EXACTLY like the working examples
        cmd = ["claude", "--dangerously-skip-permissions", "-p", task]

        # Set up environment with token
        env = os.environ.copy()
        env["CLAUDE_CODE_TOKEN"] = token
        # Remove conflicting vars
        env.pop("ANTHROPIC_API_KEY", None)

        # Log what we're ACTUALLY doing
        print(f"\n🤖 Agent {agent_id} executing REAL Claude:")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Token: ...{token[-8:]}")
        print(f"   CWD: {cwd or os.getcwd()}")

        start_time = datetime.now()

        try:
            # ACTUALLY spawn Claude process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            # Track active process
            self.active_processes[agent_id] = process

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.terminate()
                await process.wait()
                return {
                    "agent_id": agent_id,
                    "success": False,
                    "error": f"Timeout after {timeout}s",
                    "duration": (datetime.now() - start_time).total_seconds(),
                }

            # Get ACTUAL output from REAL Claude
            output = stdout.decode("utf-8")
            error = stderr.decode("utf-8")

            success = process.returncode == 0

            # Log actual results
            if success:
                print(f"   ✅ Agent {agent_id} completed successfully")
                print(f"   Output length: {len(output)} chars")
            else:
                print(f"   ❌ Agent {agent_id} failed: {error[:200]}")

            return {
                "agent_id": agent_id,
                "success": success,
                "output": output,
                "error": error,
                "return_code": process.returncode,
                "duration": (datetime.now() - start_time).total_seconds(),
            }

        except Exception as e:
            print(f"   ❌ Agent {agent_id} exception: {e}")
            return {
                "agent_id": agent_id,
                "success": False,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds(),
            }
        finally:
            # Clean up
            self.active_processes.pop(agent_id, None)

    async def execute_parallel(
        self,
        tasks: List[Tuple[str, str]],  # List of (agent_id, task)
        cwd: Optional[str] = None,
        max_parallel: int = 15,
    ) -> List[Dict]:
        """
        Execute multiple Claude agents in PARALLEL

        This is REAL parallel execution - multiple 'claude' processes at once
        """
        print(f"\n🚀 Launching {len(tasks)} agents in parallel (max {max_parallel})")

        # Limit parallelism to available tokens
        max_parallel = min(max_parallel, len(self.tokens))

        # Create semaphore to limit concurrent agents
        semaphore = asyncio.Semaphore(max_parallel)

        async def run_with_semaphore(agent_id: str, task: str):
            async with semaphore:
                return await self.execute_claude(task, agent_id, cwd)

        # Launch all agents
        agent_tasks = [run_with_semaphore(agent_id, task) for agent_id, task in tasks]

        # Wait for all to complete
        results = await asyncio.gather(*agent_tasks)

        # Summary
        successful = sum(1 for r in results if r["success"])
        print("\n📊 Parallel execution complete:")
        print(f"   ✅ Successful: {successful}/{len(tasks)}")
        print(f"   ⏱️  Total time: {max(r['duration'] for r in results):.1f}s")

        return results

    async def emergency_stop_all(self):
        """Stop all running agents"""
        print("\n🛑 Emergency stop - terminating all agents")
        for agent_id, process in self.active_processes.items():
            print(f"   Terminating {agent_id}...")
            process.terminate()
            await process.wait()
        self.active_processes.clear()


class RealAgentOrchestrator:
    """Orchestrate multiple REAL agents with worktree isolation"""

    def __init__(self, repo_path: Path, tokens: List[str]):
        self.repo_path = repo_path
        self.executor = RealAgentExecutor(tokens)

    async def run_agent_in_worktree(
        self, agent_id: str, task: str, branch_name: str
    ) -> Dict:
        """Run a REAL agent in an isolated git worktree"""

        # Create worktree for this agent
        worktree_path = self.repo_path / f"agent_worktrees/{agent_id}"
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # Create worktree branch
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            cwd=self.repo_path,
            capture_output=True,
        )

        print(f"\n📁 Created worktree for {agent_id} at {worktree_path}")

        try:
            # Execute REAL Claude in the worktree
            result = await self.executor.execute_claude(
                task=task, agent_id=agent_id, cwd=str(worktree_path)
            )

            # If successful, commit whatever the agent created
            if result["success"]:
                # Stage all changes
                subprocess.run(
                    ["git", "add", "-A"], cwd=worktree_path, capture_output=True
                )

                # Commit with real agent ID
                commit_result = subprocess.run(
                    [
                        "git",
                        "commit",
                        "--no-verify",
                        "-m",
                        f"Real agent {agent_id} work\n\nTask: {task[:100]}",
                    ],
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                )

                if commit_result.returncode == 0:
                    print(f"   📝 Committed agent {agent_id} work")
                    result["committed"] = True
                else:
                    print(f"   ℹ️  Nothing to commit for {agent_id}")
                    result["committed"] = False

            return result

        finally:
            # Clean up worktree
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=self.repo_path,
                capture_output=True,
            )
            print(f"   🧹 Cleaned up worktree for {agent_id}")


# Example usage that ACTUALLY WORKS
if __name__ == "__main__":

    async def test_real_execution():
        """Test that ACTUALLY executes Claude"""

        # Load tokens from environment
        tokens = []
        for i in range(1, 16):
            token = os.environ.get(f"CLAUDE_CODE_TOKEN{i}")
            if token:
                tokens.append(token)

        if not tokens:
            print("❌ No tokens found in environment")
            return

        print(f"🔑 Found {len(tokens)} tokens")

        # Create executor
        executor = RealAgentExecutor(tokens)

        # Test single agent
        print("\n=== Testing Single Agent ===")
        result = await executor.execute_claude(
            task="Write a Python function that calculates fibonacci numbers",
            agent_id="test_agent_1",
        )

        if result["success"]:
            print(f"\nAgent output:\n{result['output'][:500]}...")

        # Test parallel agents
        print("\n=== Testing Parallel Agents ===")
        tasks = [
            ("agent_1", "Create a calculator.py with add and subtract functions"),
            ("agent_2", "Create a test_calculator.py with tests"),
            ("agent_3", "Create a README.md documenting the calculator"),
        ]

        results = await executor.execute_parallel(tasks, max_parallel=3)

        for r in results:
            print(f"\n{r['agent_id']}: {'✅' if r['success'] else '❌'}")
            if r["success"] and r.get("output"):
                print(f"  Created files/output preview: {r['output'][:200]}...")

    # Run the test
    asyncio.run(test_real_execution())
