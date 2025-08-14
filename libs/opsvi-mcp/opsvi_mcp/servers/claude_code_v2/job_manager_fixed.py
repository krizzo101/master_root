"""
Fire-and-Forget Job Manager - Fixed to use real Claude Code CLI
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import signal
from dataclasses import dataclass, field
import traceback

from .config import ServerConfig

logger = logging.getLogger(__name__)


@dataclass
class AgentJob:
    """Represents a spawned agent job"""

    job_id: str
    task: str
    agent_profile: Optional[str]
    output_dir: str
    result_file: str
    status: str = "pending"
    spawned_at: str = ""
    completed_at: str = ""
    process: Optional[subprocess.Popen] = None
    error: Optional[str] = None
    depth: int = 0
    parent_id: Optional[str] = None


class FireAndForgetJobManager:
    """Manages fire-and-forget jobs with real Claude Code execution"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.active_jobs: Dict[str, AgentJob] = {}

    async def spawn_agent(self, job_info: Dict[str, Any]) -> None:
        """Spawn a first-level agent that runs Claude Code independently"""
        try:
            job_id = job_info["job_id"]

            # Create agent job
            job = AgentJob(
                job_id=job_id,
                task=job_info["task"],
                agent_profile=job_info.get("agent_profile"),
                output_dir=job_info["output_dir"],
                result_file=job_info["result_file"],
                status="spawning",
                spawned_at=datetime.now().isoformat(),
                depth=0,
            )

            # Store in active jobs
            self.active_jobs[job_id] = job

            # Create the agent script that calls real Claude Code
            agent_script = self._create_claude_agent_script(job_info)

            # Write script to temp file
            script_path = f"/tmp/agent_{job_id}.py"
            with open(script_path, "w") as f:
                f.write(agent_script)

            # Spawn the agent process
            env = os.environ.copy()
            env.update(
                {
                    "CLAUDE_CODE_TOKEN": self.config.claude_token or "",
                    "AGENT_JOB_ID": job_id,
                    "AGENT_OUTPUT_DIR": job_info.get(
                        "output_dir", "/tmp/claude_results"
                    ),
                    "AGENT_RESULT_FILE": job_info.get(
                        "result_file", f"/tmp/claude_results/{job_id}.json"
                    ),
                }
            )

            # Start process detached
            process = subprocess.Popen(
                [sys.executable, script_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            job.process = process
            job.status = "running"

            logger.info(f"Spawned Claude Code agent {job_id} (PID: {process.pid})")

        except Exception as e:
            logger.error(f"Failed to spawn agent {job_info.get('job_id')}: {e}")
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = "failed"
                self.active_jobs[job_id].error = str(e)

    def _create_claude_agent_script(self, job_info: Dict[str, Any]) -> str:
        """Create a Python script that calls the real Claude Code CLI"""

        # Escape the task string properly
        task_escaped = repr(job_info["task"])

        return f'''#!/usr/bin/env python3
"""
Claude Code Agent Script - Calls real Claude CLI
Job ID: {job_info['job_id']}
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# Configuration
JOB_ID = "{job_info['job_id']}"
OUTPUT_DIR = "{job_info['output_dir']}"
RESULT_FILE = "{job_info['result_file']}"
TASK = {task_escaped}
TIMEOUT = {job_info.get('timeout', 600)}

def execute_claude_code():
    """Execute task using real Claude Code CLI"""
    
    result = {{
        "job_id": JOB_ID,
        "task": TASK,
        "status": "running",
        "started_at": datetime.now().isoformat()
    }}
    
    try:
        # Build Claude command
        cmd = [
            "claude",
            "--dangerously-skip-permissions",  # For automation
            "--output-format", "json"
        ]
        
        # Write task to stdin
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=TIMEOUT
        )
        
        # Send task and get result
        stdout, stderr = process.communicate(input=TASK)
        
        if process.returncode == 0:
            # Parse Claude's JSON output
            try:
                claude_result = json.loads(stdout)
                result["status"] = "completed"
                result["output"] = claude_result
                result["claude_session_id"] = claude_result.get("session_id")
                result["claude_cost"] = claude_result.get("total_cost_usd", 0)
            except json.JSONDecodeError:
                # Fallback for non-JSON output
                result["status"] = "completed"
                result["output"] = stdout
        else:
            result["status"] = "failed"
            result["error"] = stderr or f"Process exited with code {{process.returncode}}"
            
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = f"Task timed out after {{TIMEOUT}} seconds"
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
    
    finally:
        result["completed_at"] = datetime.now().isoformat()
        
        # Write result to file
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(RESULT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
        # Also print for debugging
        print(f"Task completed: {{result['status']}}")
        print(f"Result saved to: {{RESULT_FILE}}")
    
    return result

if __name__ == "__main__":
    result = execute_claude_code()
    sys.exit(0 if result["status"] == "completed" else 1)
'''

    async def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a specific job"""
        if job_id not in self.active_jobs:
            return {"status": "not_found"}

        job = self.active_jobs[job_id]

        # Check if process is still running
        if job.process:
            poll = job.process.poll()
            if poll is None:
                job.status = "running"
            elif poll == 0:
                job.status = "completed"
            else:
                job.status = "failed"

        return {
            "job_id": job.job_id,
            "status": job.status,
            "spawned_at": job.spawned_at,
            "task": job.task[:100] + "..." if len(job.task) > 100 else job.task,
        }

    async def kill_job(self, job_id: str) -> bool:
        """Kill a running job"""
        if job_id not in self.active_jobs:
            return False

        job = self.active_jobs[job_id]
        if job.process:
            try:
                os.killpg(os.getpgid(job.process.pid), signal.SIGTERM)
                job.status = "terminated"
                return True
            except:
                pass

        return False

    async def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active jobs"""
        active = []
        for job_id, job in self.active_jobs.items():
            status = await self.check_job_status(job_id)
            if status["status"] in ["running", "spawning"]:
                active.append(status)
        return active
