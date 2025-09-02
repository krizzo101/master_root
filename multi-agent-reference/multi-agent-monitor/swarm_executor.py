#!/usr/bin/env python3
"""
Real Multi-Agent Swarm Executor
Built from working patterns in claude_code MCP servers
"""

import asyncio
import json
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AgentRole(Enum):
    """Agent specializations"""

    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DOCUMENTER = "documenter"
    SECURITY = "security"
    DEVOPS = "devops"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    API = "api"
    PERFORMANCE = "performance"
    REFACTOR = "refactor"
    DEBUGGER = "debugger"
    ANALYST = "analyst"


@dataclass
class AgentTask:
    """Task for an agent"""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    role: AgentRole = AgentRole.DEVELOPER
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    timeout: int = 600
    workspace: Optional[Path] = None


@dataclass
class AgentResult:
    """Result from agent execution"""

    task_id: str
    agent_role: AgentRole
    success: bool
    output: str = ""
    error: str = ""
    duration: float = 0.0
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)


class TokenPool:
    """
    Token pool management - adapted from claude_code/job_manager.py
    Round-robin distribution with tracking
    """

    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.index = 0
        self.usage = {i: 0 for i in range(len(tokens))}
        self.active = {i: None for i in range(len(tokens))}

    def acquire(self, agent_id: str) -> Tuple[int, str]:
        """Get next available token"""
        token_idx = self.index % len(self.tokens)
        self.index += 1
        self.usage[token_idx] += 1
        self.active[token_idx] = agent_id
        return token_idx, self.tokens[token_idx]

    def release(self, token_idx: int):
        """Release token back to pool"""
        self.active[token_idx] = None

    def get_status(self) -> Dict:
        """Get pool status"""
        return {
            "total": len(self.tokens),
            "active": sum(1 for v in self.active.values() if v),
            "available": sum(1 for v in self.active.values() if not v),
            "usage": self.usage,
        }


class SwarmExecutor:
    """
    Real swarm executor using subprocess to call Claude
    Based on working patterns from claude_code and v3 servers
    """

    def __init__(self, repo_path: Path, tokens: List[str]):
        self.repo_path = repo_path
        self.token_pool = TokenPool(tokens)
        self.active_processes = {}
        self.results = []

    async def execute_agent(
        self, task: AgentTask, worktree_path: Optional[Path] = None
    ) -> AgentResult:
        """
        Execute a single agent with real Claude subprocess
        Pattern from v3/server.py and claude_code/job_manager.py
        """
        start_time = datetime.now()

        # Get token from pool
        token_idx, token = self.token_pool.acquire(task.id)

        # Build command (from v3/server.py pattern)
        cmd = ["claude", "--dangerously-skip-permissions"]

        # Add output format
        cmd.extend(["--output-format", "json"])

        # Add role-specific prompt prefix (from v3)
        prompt_prefix = self._get_role_prefix(task.role)
        full_task = f"{prompt_prefix}{task.description}"

        # Add the task
        cmd.extend(["-p", full_task])

        # Setup environment (from claude_code/job_manager.py)
        env = os.environ.copy()
        env["CLAUDE_CODE_TOKEN"] = token
        # Critical: Remove ANTHROPIC_API_KEY
        env.pop("ANTHROPIC_API_KEY", None)

        # Set working directory
        cwd = str(worktree_path) if worktree_path else str(self.repo_path)

        print(f"\n🤖 Agent {task.role.value} #{task.id} starting")
        print(f"   📝 Task: {task.description[:100]}...")
        print(f"   🔑 Token: #{token_idx}")
        print(f"   📁 CWD: {cwd}")

        try:
            # Execute Claude (from v3 async pattern)
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            # Track active process
            self.active_processes[task.id] = process

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=task.timeout
                )
            except asyncio.TimeoutError:
                process.terminate()
                await process.wait()
                raise TimeoutError(f"Task timed out after {task.timeout}s")

            # Parse output
            output = stdout.decode("utf-8")
            error = stderr.decode("utf-8")

            if process.returncode == 0:
                print(f"   ✅ Agent {task.role.value} completed")

                # Try to parse JSON output
                try:
                    result_data = json.loads(output)
                    files_created = result_data.get("files_created", [])
                    files_modified = result_data.get("files_modified", [])
                except json.JSONDecodeError:
                    # Plain text output
                    files_created = []
                    files_modified = []

                result = AgentResult(
                    task_id=task.id,
                    agent_role=task.role,
                    success=True,
                    output=output,
                    duration=(datetime.now() - start_time).total_seconds(),
                    files_created=files_created,
                    files_modified=files_modified,
                )
            else:
                print(f"   ❌ Agent {task.role.value} failed")
                result = AgentResult(
                    task_id=task.id,
                    agent_role=task.role,
                    success=False,
                    error=error or f"Exit code {process.returncode}",
                    duration=(datetime.now() - start_time).total_seconds(),
                )

        except Exception as e:
            print(f"   ❌ Agent {task.role.value} exception: {e}")
            result = AgentResult(
                task_id=task.id,
                agent_role=task.role,
                success=False,
                error=str(e),
                duration=(datetime.now() - start_time).total_seconds(),
            )

        finally:
            # Clean up
            self.active_processes.pop(task.id, None)
            self.token_pool.release(token_idx)

        self.results.append(result)
        return result

    async def execute_swarm(
        self, tasks: List[AgentTask], max_parallel: Optional[int] = None
    ) -> List[AgentResult]:
        """
        Execute multiple agents in parallel
        Pattern from v3 task decomposition and claude_code parallel execution
        """
        if not max_parallel:
            max_parallel = min(len(self.token_pool.tokens), len(tasks))

        print(f"\n🐝 SWARM EXECUTION: {len(tasks)} agents, max {max_parallel} parallel")
        print(f"🔑 Token pool: {self.token_pool.get_status()}")

        # Create semaphore for parallelism control
        semaphore = asyncio.Semaphore(max_parallel)

        async def run_with_limit(task: AgentTask):
            async with semaphore:
                # Create worktree for isolation (from our working worktree_manager)
                worktree_path = None
                if task.workspace:
                    worktree_path = await self._create_worktree(task)

                try:
                    return await self.execute_agent(task, worktree_path)
                finally:
                    if worktree_path:
                        await self._cleanup_worktree(worktree_path)

        # Execute all tasks
        results = await asyncio.gather(*[run_with_limit(task) for task in tasks])

        # Summary
        successful = sum(1 for r in results if r.success)
        total_duration = max(r.duration for r in results)

        print("\n📊 SWARM COMPLETE:")
        print(f"   ✅ Successful: {successful}/{len(tasks)}")
        print(f"   ⏱️  Total time: {total_duration:.1f}s")
        print(f"   📈 Parallelism: {min(max_parallel, len(tasks))}x")

        return results

    async def emergency_stop(self):
        """Stop all running agents"""
        print("\n🛑 EMERGENCY STOP - Terminating all agents")
        for task_id, process in self.active_processes.items():
            print(f"   Killing {task_id}...")
            process.terminate()
            await process.wait()
        self.active_processes.clear()

    def _get_role_prefix(self, role: AgentRole) -> str:
        """Get role-specific prompt prefix (from v3 pattern)"""
        prefixes = {
            AgentRole.TESTER: "Write comprehensive tests for: ",
            AgentRole.DOCUMENTER: "Write detailed documentation for: ",
            AgentRole.REVIEWER: "Review and provide feedback on: ",
            AgentRole.DEBUGGER: "Debug and fix issues in: ",
            AgentRole.SECURITY: "Perform security analysis on: ",
            AgentRole.PERFORMANCE: "Optimize performance of: ",
            AgentRole.REFACTOR: "Refactor and improve: ",
            AgentRole.ARCHITECT: "Design architecture for: ",
            AgentRole.FRONTEND: "Implement frontend for: ",
            AgentRole.BACKEND: "Implement backend for: ",
            AgentRole.DATABASE: "Design database schema for: ",
            AgentRole.API: "Design and implement API for: ",
            AgentRole.DEVOPS: "Create deployment configuration for: ",
            AgentRole.ANALYST: "Analyze requirements for: ",
        }
        return prefixes.get(role, "")

    async def _create_worktree(self, task: AgentTask) -> Path:
        """Create git worktree for agent isolation"""
        worktree_path = (
            self.repo_path / "agent_worktrees" / f"{task.role.value}_{task.id}"
        )
        branch_name = (
            f"agent/{datetime.now().strftime('%Y%m%d_%H%M%S')}/{task.role.value}"
        )

        # Create branch without checking out
        subprocess.run(
            ["git", "branch", branch_name], cwd=self.repo_path, capture_output=True
        )

        # Create worktree
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=self.repo_path,
            capture_output=True,
        )

        print(f"   📁 Created worktree: {worktree_path}")
        return worktree_path

    async def _cleanup_worktree(self, worktree_path: Path):
        """Clean up worktree"""
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=self.repo_path,
            capture_output=True,
        )


# Task decomposer adapted from v3
class TaskDecomposer:
    """Decompose complex tasks into agent subtasks"""

    @staticmethod
    def decompose(description: str) -> List[AgentTask]:
        """
        Decompose a high-level task into agent subtasks
        This is simplified - v3 has more sophisticated analysis
        """
        tasks = []

        # Keywords to detect needed agents
        if any(word in description.lower() for word in ["api", "endpoint", "rest"]):
            tasks.append(
                AgentTask(
                    role=AgentRole.API,
                    description=f"Design REST API for: {description}",
                    priority=1,
                )
            )

        if any(word in description.lower() for word in ["frontend", "ui", "interface"]):
            tasks.append(
                AgentTask(
                    role=AgentRole.FRONTEND,
                    description=f"Create frontend for: {description}",
                    priority=2,
                )
            )

        if any(
            word in description.lower() for word in ["backend", "server", "service"]
        ):
            tasks.append(
                AgentTask(
                    role=AgentRole.BACKEND,
                    description=f"Implement backend for: {description}",
                    priority=2,
                )
            )

        if any(word in description.lower() for word in ["database", "schema", "model"]):
            tasks.append(
                AgentTask(
                    role=AgentRole.DATABASE,
                    description=f"Design database for: {description}",
                    priority=1,
                )
            )

        if any(word in description.lower() for word in ["test", "testing", "quality"]):
            tasks.append(
                AgentTask(
                    role=AgentRole.TESTER,
                    description=f"Create tests for: {description}",
                    priority=3,
                )
            )

        if any(word in description.lower() for word in ["document", "docs", "readme"]):
            tasks.append(
                AgentTask(
                    role=AgentRole.DOCUMENTER,
                    description=f"Document: {description}",
                    priority=3,
                )
            )

        # Default to developer if no specific roles detected
        if not tasks:
            tasks.append(
                AgentTask(role=AgentRole.DEVELOPER, description=description, priority=1)
            )

        return tasks


if __name__ == "__main__":

    async def test_swarm():
        """Test the swarm with real execution"""

        # Load tokens
        tokens = []
        # Check primary token first
        primary = os.environ.get("CLAUDE_CODE_TOKEN")
        if primary:
            tokens.append(primary)

        # Check numbered tokens
        for i in range(1, 16):
            token = os.environ.get(f"CLAUDE_CODE_TOKEN{i}")
            if token:
                tokens.append(token)

        if not tokens:
            print("❌ No tokens found")
            return

        print(f"🔑 Loaded {len(tokens)} tokens")

        # Create swarm executor
        repo_path = Path("/home/opsvi/master_root")
        swarm = SwarmExecutor(repo_path, tokens)

        # Decompose a task
        main_task = (
            "Create a REST API with user authentication, database models, and tests"
        )
        tasks = TaskDecomposer.decompose(main_task)

        print(f"\n📋 Decomposed into {len(tasks)} agent tasks:")
        for task in tasks:
            print(f"   - {task.role.value}: {task.description[:50]}...")

        # Execute swarm
        results = await swarm.execute_swarm(tasks, max_parallel=5)

        # Show results
        print("\n📈 Results:")
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.agent_role.value}: {result.duration:.1f}s")
            if result.files_created:
                print(f"      Created: {result.files_created}")
            if result.error:
                print(f"      Error: {result.error[:100]}")

    # Run test
    asyncio.run(test_swarm())
