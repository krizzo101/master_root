#!/usr/bin/env python3
"""
HECATON - Multi-Agent Claude Orchestration System
Single entry point for all execution modes
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hecaton.agents.agent_registry import AgentRegistry  # noqa: E402
from hecaton.agents.real_claude_executor import (  # noqa: E402
    RealClaudeSubprocessExecutor as RealClaudeExecutor,
)
from hecaton.monitoring.performance_monitor import PerformanceMonitor  # noqa: E402
from hecaton.resources.secure_token_pool import SecureTokenPool  # noqa: E402
from hecaton.resources.worktree import WorktreeManager  # noqa: E402


class HecatonApp:
    """Main application class with Send API as default orchestration"""

    def __init__(
        self, mode: str = "send-api", verbose: bool = False, merge_config=None
    ):
        self.mode = mode
        self.verbose = verbose

        # CRITICAL: Ensure ANTHROPIC_API_KEY is not set (it interferes with CLAUDE_CODE_TOKEN)
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        # Initialize real components only - no mocks
        self.token_pool = self._init_token_pool()
        self.worktree_manager = WorktreeManager(
            base_path="/tmp/hecaton_worktrees",  # nosec B108 - Temp dir for isolation
            repo_path=os.getcwd(),
        )
        self.agent_registry = AgentRegistry()
        self.performance_monitor = PerformanceMonitor()

        # Initialize orchestrator based on mode
        if mode == "send-api":
            # DEFAULT: Send API for true parallel execution
            print("🚀 Running HECATON with Send API parallel orchestration")
            try:
                from hecaton.orchestration.send_api import SendAPIOrchestrator

                self.executor = RealClaudeExecutor(
                    token_pool=self.token_pool,
                    worktree_manager=self.worktree_manager,
                )
                self.orchestrator = SendAPIOrchestrator(
                    executor=self.executor,
                    token_pool=self.token_pool,
                    worktree_manager=self.worktree_manager,
                    performance_monitor=self.performance_monitor,
                    merge_config=merge_config,
                )
                self.use_send_api = True
            except ImportError as e:
                print(f"⚠️  Send API not available ({e}), falling back to simple mode")
                mode = "simple"
                self.mode = mode

        if mode == "simple":
            # FALLBACK: Simple orchestration for debugging/testing
            print("🔧 Running HECATON in simple mode (sequential/limited parallel)")
            self.executor = RealClaudeExecutor(
                token_pool=self.token_pool,
                worktree_manager=self.worktree_manager,
            )
            self.orchestrator = None  # Will use direct executor
            self.use_send_api = False

    def _init_token_pool(self) -> SecureTokenPool:
        """Initialize token pool with real tokens only"""
        # Check for test mode
        if os.getenv("HECATON_TEST_MODE") == "1":
            # Use test tokens for dry-run testing
            test_config = (
                Path(__file__).parent.parent.parent / "config" / "test_tokens.json"
            )
            if test_config.exists():
                import json

                with open(test_config) as f:
                    config = json.load(f)
                    return SecureTokenPool(
                        tokens=config.get("tokens", ["test-token-1"])
                    )

        # Load real tokens from config
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "claude_tokens.json"
        )
        if config_path.exists():
            import json

            with open(config_path) as f:
                config = json.load(f)
                tokens = config.get("tokens", [])
                if tokens:
                    return SecureTokenPool(tokens=tokens)

        # Fall back to CLAUDE_CODE_TOKEN environment variable
        token = os.getenv("CLAUDE_CODE_TOKEN")
        if token:
            return SecureTokenPool(tokens=[token])

        raise ValueError(
            "No tokens found! Set CLAUDE_CODE_TOKEN or add tokens to config/claude_tokens.json"
        )

    async def run(self, task: str, agents: int = 2, agent_types: Optional[list] = None):
        """Run the actual HECATON system with specified number of agents"""
        print(f"\n{'='*60}")
        print(f"HECATON: Running {agents} agents")
        print(f"Task: {task}")
        mode_type = "(True Parallel)" if self.use_send_api else "(Sequential/Limited)"
        print(f"Mode: {self.mode.upper()} {mode_type}")
        print(f"{'='*60}\n")

        # Use Send API orchestrator if available
        if self.use_send_api and self.orchestrator:
            # Send API handles everything internally
            result = await self.orchestrator.execute(task, num_agents=agents)

            # Process Send API results
            successes = result["metrics"].get("successful", 0)
            total = result["metrics"].get("total_agents", agents)

            # Display results
            for agent_id, agent_result in result["results"].items():
                status = agent_result.get("status", "unknown")
                agent_type = agent_result.get(
                    "type", "unknown"
                )  # Changed from agent_type to type
                if status == "completed":
                    print(f"✅ {agent_type}: Success")
                    if self.verbose and agent_result.get("result"):
                        output = str(agent_result["result"])[:200]
                        print(f"   Output: {output}...")
                else:
                    print(f"❌ {agent_type}: Failed")
                    if self.verbose and agent_result.get("error"):
                        print(f"   Error: {agent_result['error']}")

            # Performance metrics from Send API
            metrics = result.get("metrics", {})
            results = result  # For return value

        else:
            # Simple mode: direct executor with limited parallelism
            # Default agent types if not specified
            if agent_types is None:
                agent_types = ["code", "research", "test", "review", "docs"][:agents]

            # Track performance for the overall run
            run_id = "run_" + "_".join(agent_types)
            self.performance_monitor.start_tracking(run_id)

            # Execute tasks in parallel
            tasks = []
            for i, agent_type in enumerate(agent_types):
                agent_task = {
                    "id": f"agent_{i}_{agent_type}",
                    "prompt": f"{task} - {agent_type} perspective",
                    "agent_type": agent_type,
                    "model": "claude-3-sonnet-20240229",  # Default to sonnet for speed
                }
                if self.verbose:
                    print(f"🤖 Launching {agent_type} agent...")
                tasks.append(self.executor.execute_task(agent_task))

            # Wait for all agents to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process simple mode results
            successes = 0
            total = agents

            # Process simple mode results
            for i, (agent_type, result) in enumerate(zip(agent_types, results)):
                if isinstance(result, Exception):
                    print(f"❌ {agent_type}: Failed - {result}")
                elif result.get("status") == "completed" or result.get("success"):
                    successes += 1
                    print(f"✅ {agent_type}: Success")
                    if self.verbose:
                        output = result.get("output", result.get("result", ""))[:200]
                        print(f"   Output: {output}...")
                else:
                    print(f"⚠️  {agent_type}: {result.get('status', 'Unknown status')}")

            # Stop monitoring for simple mode
            self.performance_monitor.end_tracking(run_id, successes > 0)

            metrics = self.performance_monitor.calculate_statistics()

        # Summary
        print(f"\n{'='*60}")
        print(f"Completed: {successes}/{total} agents succeeded")

        if metrics:
            avg_time = metrics.get("avg_execution_time", 0)
            if avg_time:
                print(f"Performance: Avg time: {avg_time:.2f}s")
            if self.use_send_api:
                print("Parallelism: True parallel execution via Send API")
                if metrics.get("success_rate"):
                    print(f"Success Rate: {metrics['success_rate']*100:.1f}%")

        print(f"{'='*60}\n")

        return results

    async def benchmark(self, iterations: int = 3):
        """Run benchmark tests"""
        print("🏁 Running benchmark...")

        times = []
        for i in range(iterations):
            start = asyncio.get_event_loop().time()
            await self.run("Simple test task", agents=3)
            elapsed = asyncio.get_event_loop().time() - start
            times.append(elapsed)
            print(f"Iteration {i+1}: {elapsed:.2f}s")

        avg_time = sum(times) / len(times)
        print(f"\nAverage time: {avg_time:.2f}s")

        return {"iterations": iterations, "times": times, "average": avg_time}

    async def test(self):
        """Run self-tests"""
        print("🧪 Running self-test...")

        # Test with single agent
        results = await self.run("Write hello world", agents=1)

        if results and results[0].get("success"):
            print("✅ Self-test PASSED")
            return 0
        else:
            print("❌ Self-test FAILED")
            return 1


def main():
    """Main entry point with proper argument parsing"""
    # Ensure clean environment for Claude Code execution
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]
        if "--verbose" in sys.argv or "-v" in sys.argv:
            print("ℹ️  Cleared ANTHROPIC_API_KEY (interferes with CLAUDE_CODE_TOKEN)")

    parser = argparse.ArgumentParser(
        description="HECATON - Multi-Agent Claude Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with real API calls
  python -m hecaton run "Build a REST API"

  # Run with Send API (default)
  python -m hecaton run "Build a REST API" --mode send-api

  # Run in simple mode (debugging)
  python -m hecaton run "Build a REST API" --mode simple

  # Run with 5 agents
  python -m hecaton run "Complex task" --agents 5

  # Run benchmark
  python -m hecaton benchmark

  # Run self-test
  python -m hecaton test
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run HECATON with a task")
    run_parser.add_argument("task", help="Task to execute")
    run_parser.add_argument(
        "--agents", type=int, default=2, help="Number of agents (default: 2)"
    )
    run_parser.add_argument(
        "--mode",
        choices=["send-api", "simple"],
        default="send-api",
        help="Orchestration mode (default: send-api for parallel execution)",
    )
    run_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Merge-back arguments
    run_parser.add_argument(
        "--merge-back/--no-merge-back",
        dest="merge_back",
        action="store_true",
        default=True,
        help="Enable/disable merge-back of patches (default: enabled)",
    )
    run_parser.add_argument(
        "--target-branch",
        default="main",
        help="Target branch for merge-back (default: main)",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run merge-back in dry-run mode (no push/PR)",
    )
    run_parser.add_argument(
        "--keep-worktrees", action="store_true", help="Keep worktrees after execution"
    )
    run_parser.add_argument(
        "--land-direct",
        action="store_true",
        help="Directly merge to target branch instead of creating PR",
    )

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run performance benchmark")
    bench_parser.add_argument(
        "--iterations", type=int, default=3, help="Number of iterations (default: 3)"
    )

    # Test command
    subparsers.add_parser("test", help="Run self-test")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create merge config if needed
    merge_config = None
    if args.command == "run" and getattr(args, "merge_back", True):
        from hecaton.config.merge_back import MergeBackConfig

        merge_config = MergeBackConfig(
            enabled=True,
            target_branch=getattr(args, "target_branch", "main"),
            dry_run=getattr(args, "dry_run", False),
            keep_worktrees=getattr(args, "keep_worktrees", False),
            land_direct=getattr(args, "land_direct", False),
        )

    # Create app instance with configuration
    app = HecatonApp(
        mode=getattr(args, "mode", "send-api"),
        verbose=getattr(args, "verbose", False),
        merge_config=merge_config,
    )

    # Run the appropriate command
    try:
        if args.command == "run":
            result = asyncio.run(app.run(args.task, args.agents))
        elif args.command == "benchmark":
            result = asyncio.run(app.benchmark(args.iterations))
        elif args.command == "test":
            result = asyncio.run(app.test())
        else:
            parser.print_help()
            return 1

        return 0 if result else 1

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
