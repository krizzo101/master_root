"""
Solution using Claude's built-in Task tool for true parallelism
"""
import json
import subprocess
from typing import List, Dict, Any
import asyncio


class TaskToolOrchestrator:
    """Uses Claude's Task tool for parallel agent execution"""

    async def execute_parallel_via_task_tool(self, tasks: List[str]) -> Dict[str, Any]:
        """Execute tasks in parallel using Claude's Task tool"""

        # Build prompt that instructs Claude to use Task tool
        task_descriptions = "\n".join(
            [f"{i+1}. {task}" for i, task in enumerate(tasks)]
        )

        prompt = f"""
        Use the Task tool to execute these {len(tasks)} tasks in parallel:
        
        {task_descriptions}
        
        IMPORTANT:
        - Launch all tasks simultaneously using the Task tool
        - Each task should be given to a separate specialized agent
        - Wait for all tasks to complete
        - Return a JSON summary with the results from each task
        
        Output format:
        {{
            "tasks_completed": {len(tasks)},
            "results": [
                {{"task_id": 1, "status": "success", "output": "..."}},
                ...
            ]
        }}
        """

        # Execute via single Claude instance that will spawn parallel agents
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--json",  # Request JSON output
            "-p",
            prompt,
        ]

        # Run the orchestration
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"CLAUDE_CODE_TOKEN": self._get_token()},
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            try:
                # Parse JSON response
                result = json.loads(stdout.decode())
                return {
                    "status": "success",
                    "parallel_execution": True,
                    "results": result,
                }
            except json.JSONDecodeError:
                # Fallback to text response
                return {
                    "status": "success",
                    "parallel_execution": True,
                    "output": stdout.decode(),
                }
        else:
            return {"status": "error", "error": stderr.decode()}

    def _get_token(self) -> str:
        """Get Claude token from environment"""
        import os

        token = os.getenv("CLAUDE_CODE_TOKEN")
        if not token:
            raise ValueError("CLAUDE_CODE_TOKEN not set")
        return token


# Integration example:
async def execute_batch_with_task_tool(tasks: List[str]):
    """Execute batch using Task tool for true parallelism"""
    orchestrator = TaskToolOrchestrator()

    # Single Claude instance spawns multiple parallel agents
    result = await orchestrator.execute_parallel_via_task_tool(tasks)

    return result
