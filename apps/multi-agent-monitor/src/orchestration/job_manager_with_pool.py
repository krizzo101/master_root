"""
Enhanced Job Manager with Token Pool Support
Uses rotating tokens for parallel agent execution
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..claude_code.token_pool import (
    create_safe_environment_with_token,
    token_pool_manager,
)
from .job_manager import FireAndForgetJobManager


class TokenPoolJobManager(FireAndForgetJobManager):
    """Job manager that uses token pool for parallel execution"""

    def __init__(self, config):
        super().__init__(config)

        # Initialize token pool with provided tokens if any
        self._initialize_token_pool()

    def _initialize_token_pool(self):
        """Initialize the token pool with available tokens"""

        # Check if tokens are provided via environment
        tokens = []

        # The user provided 3 tokens - set them as environment variables first
        # In production, these would be loaded from secure storage

        # For now, check if they're in environment
        for i in range(1, 10):
            token_key = f"CLAUDE_CODE_TOKEN{i}"
            token = os.environ.get(token_key)
            if token:
                tokens.append(token)

        if tokens:
            token_pool_manager.initialize_with_tokens(tokens)
            self.logger.info(f"Token pool initialized with {len(tokens)} tokens")
        else:
            # Fall back to single token if available
            primary = os.environ.get("CLAUDE_CODE_TOKEN")
            if primary:
                token_pool_manager.initialize_with_tokens([primary])
                self.logger.info("Token pool initialized with primary token")
            else:
                self.logger.warning("No tokens found for pool initialization")

    def _build_agent_command(self, job_info: Dict[str, Any]) -> list:
        """Build command with token from pool"""

        # Get base command from parent
        cmd = super()._build_agent_command(job_info)

        # Log which token is being used (safely)
        job_id = job_info.get("job_id", "unknown")
        self.logger.info(f"[{job_id}] Using token from pool for agent")

        return cmd

    async def spawn_agent(self, job_info: Dict[str, Any]) -> None:
        """Spawn agent with token from pool"""

        job_id = job_info["job_id"]

        try:
            # Update status
            job_info["status"] = "preparing"

            # Get environment with token from pool
            env, token_id = create_safe_environment_with_token()

            # Log token allocation (safely)
            self.logger.info(f"[{job_id}] Allocated {token_id} from pool")
            job_info["token_id"] = token_id  # Safe to log

            # Build command
            cmd = self._build_agent_command(job_info)

            # Log the command
            self.logger.info(f"[{job_id}] Spawning: {' '.join(cmd[:3])}...")

            # Update status
            job_info["status"] = "spawning"

            # Start the agent process with pooled token
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,  # Environment with token from pool
                cwd=job_info.get("output_dir", "."),
            )

            # Update job info
            job_info["pid"] = process.pid
            job_info["status"] = "running"
            job_info["started_at"] = datetime.now().isoformat()

            self.logger.info(
                f"[{job_id}] Agent spawned with PID {process.pid} using {token_id}"
            )

            # Wait for completion
            stdout, stderr = process.communicate(timeout=job_info.get("timeout", 600))

            # Process completed
            job_info["status"] = "completed" if process.returncode == 0 else "failed"
            job_info["completed_at"] = datetime.now().isoformat()
            job_info["return_code"] = process.returncode
            job_info["stdout"] = stdout[:1000]  # Truncate for storage
            job_info["stderr"] = stderr[:1000]

            # Save result
            result_file = Path(job_info["result_file"])
            with open(result_file, "w") as f:
                json.dump(job_info, f, indent=2)

            self.logger.info(f"[{job_id}] Completed with status: {job_info['status']}")

        except subprocess.TimeoutExpired:
            self.logger.error(f"[{job_id}] Timed out")
            job_info["status"] = "timeout"
            job_info["error"] = f"Timed out after {job_info.get('timeout', 600)}s"

        except Exception as e:
            self.logger.error(f"[{job_id}] Failed: {e}")
            job_info["status"] = "error"
            job_info["error"] = str(e)

        finally:
            # Always save final status
            try:
                result_file = Path(job_info["result_file"])
                with open(result_file, "w") as f:
                    json.dump(job_info, f, indent=2)
            except:
                pass

    async def spawn_parallel_agents(
        self, tasks: list[str], output_dir: str, max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """Spawn multiple agents using token pool for true parallelism"""

        # Check token availability
        token_count = token_pool_manager.pool.get_token_count()
        if token_count < max_concurrent:
            self.logger.warning(
                f"Only {token_count} tokens available, limiting concurrency to {token_count}"
            )
            max_concurrent = min(max_concurrent, token_count)

        # Create jobs
        jobs = []
        for i, task in enumerate(tasks):
            job_info = {
                "job_id": f"parallel_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "task": task,
                "output_dir": output_dir,
                "result_file": f"{output_dir}/result_{i}.json",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
            jobs.append(job_info)

        # Run with limited concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_limit(job):
            async with semaphore:
                await self.spawn_agent(job)

        # Launch all jobs
        tasks = [run_with_limit(job) for job in jobs]
        await asyncio.gather(*tasks)

        # Collect results
        results = {
            "total": len(jobs),
            "completed": sum(1 for j in jobs if j.get("status") == "completed"),
            "failed": sum(
                1 for j in jobs if j.get("status") in ["failed", "error", "timeout"]
            ),
            "jobs": jobs,
        }

        # Get token usage stats
        stats = token_pool_manager.get_pool_status()
        results["token_usage"] = stats["usage_stats"]

        self.logger.info(
            f"Parallel execution complete: {results['completed']}/{results['total']} succeeded"
        )

        return results


def test_token_pool():
    """Test the token pool functionality"""

    print("Testing Token Pool Integration")
    print("=" * 60)

    # Check pool status
    status = token_pool_manager.get_pool_status()
    print(f"Tokens in pool: {status['token_count']}")

    if status["token_count"] == 0:
        print("\n⚠️  No tokens in pool!")
        print("Add tokens using:")
        print("  export CLAUDE_CODE_TOKEN1='your-token-1'")
        print("  export CLAUDE_CODE_TOKEN2='your-token-2'")
        print("  export CLAUDE_CODE_TOKEN3='your-token-3'")
        return

    print("\nToken rotation test:")
    for i in range(6):
        env, token_id = create_safe_environment_with_token()
        print(f"  Request {i+1}: Allocated {token_id}")
        # Verify ANTHROPIC_API_KEY is removed
        assert "ANTHROPIC_API_KEY" not in env
        assert "CLAUDE_CODE_TOKEN" in env

    print("\nUsage statistics:")
    status = token_pool_manager.get_pool_status()
    for token_id, stats in status["usage_stats"].items():
        print(f"  {token_id}: {stats['usage_count']} uses")

    print("\n✅ Token pool integration working correctly!")


if __name__ == "__main__":
    test_token_pool()
