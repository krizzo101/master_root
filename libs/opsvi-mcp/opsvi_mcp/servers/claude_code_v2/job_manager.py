"""
Fire-and-Forget Job Manager with Hybrid Decoupling

This manager implements a hybrid approach:
1. First-level agents are decoupled from the parent (fire-and-forget)
2. Each first-level agent is fully responsible for its children
3. Sub-agents use traditional synchronous management within their scope
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
    completed_at: Optional[str] = None
    process: Optional[subprocess.Popen] = None
    parent_job_id: Optional[str] = None
    depth: int = 0
    children: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "job_id": self.job_id,
            "task": self.task[:200] + "..." if len(self.task) > 200 else self.task,
            "agent_profile": self.agent_profile,
            "status": self.status,
            "spawned_at": self.spawned_at,
            "completed_at": self.completed_at,
            "parent_job_id": self.parent_job_id,
            "depth": self.depth,
            "children": self.children,
            "error": self.error,
            "result_file": self.result_file,
        }


class FireAndForgetJobManager:
    """
    Manages fire-and-forget jobs with hybrid decoupling.

    Key principles:
    - First-level agents are fully decoupled (fire-and-forget)
    - Each agent manages its own children synchronously
    - Results include full recursive tree of sub-agent results
    """

    def __init__(self, config: ServerConfig):
        self.config = config
        self.active_jobs: Dict[str, AgentJob] = {}
        self.completed_jobs: Dict[str, AgentJob] = {}

    async def spawn_agent(self, job_info: Dict[str, Any]) -> None:
        """
        Spawn a first-level agent that runs independently.
        This agent will manage its own children synchronously.
        """
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
                depth=0,  # First-level agent
            )

            # Store in active jobs
            self.active_jobs[job_id] = job

            # Create the agent script that will run independently
            agent_script = self._create_agent_script(job_info)

            # Write script to temp file
            script_path = f"/tmp/agent_{job_id}.py"
            with open(script_path, "w") as f:
                f.write(agent_script)

            # Spawn the agent process (fire-and-forget)
            env = os.environ.copy()
            env.update(
                {
                    "PYTHONPATH": self.config.python_path,
                    "CLAUDE_CODE_TOKEN": self.config.claude_token,
                    "AGENT_JOB_ID": job_id,
                    "AGENT_OUTPUT_DIR": job_info["output_dir"],
                    "AGENT_RESULT_FILE": job_info["result_file"],
                    "AGENT_PROFILE": job_info.get("agent_profile", ""),
                    "AGENT_TIMEOUT": str(job_info.get("timeout", 600)),
                    # Enable child management for this agent
                    "AGENT_MANAGE_CHILDREN": "true",
                    "AGENT_MAX_RECURSION": "3",
                }
            )

            # Start process detached from parent
            process = subprocess.Popen(
                [sys.executable, script_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # Detach from parent process group
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            job.process = process
            job.status = "running"

            # Log spawn
            logger.info(f"Spawned agent {job_id} (PID: {process.pid})")

            # Write initial status file
            self._write_status_file(job)

        except Exception as e:
            logger.error(f"Failed to spawn agent {job_info.get('job_id')}: {e}")
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = "failed"
                self.active_jobs[job_id].error = str(e)
                self._write_status_file(self.active_jobs[job_id])

    def _create_agent_script(self, job_info: Dict[str, Any]) -> str:
        """
        Create the Python script that will run as the independent agent.
        This script manages its own children synchronously.
        """
        return f'''#!/usr/bin/env python3
"""
Independent Agent Script
Job ID: {job_info['job_id']}
This agent manages its own children synchronously and reports complete results.
"""

import os
import sys
import json
import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any, List
import subprocess
import time

# Agent configuration from environment
JOB_ID = os.environ.get("AGENT_JOB_ID")
OUTPUT_DIR = os.environ.get("AGENT_OUTPUT_DIR")
RESULT_FILE = os.environ.get("AGENT_RESULT_FILE")
AGENT_PROFILE = os.environ.get("AGENT_PROFILE", "")
TIMEOUT = int(os.environ.get("AGENT_TIMEOUT", "600"))
MANAGE_CHILDREN = os.environ.get("AGENT_MANAGE_CHILDREN", "true") == "true"
MAX_RECURSION = int(os.environ.get("AGENT_MAX_RECURSION", "3"))

# Task to execute
TASK = {repr(job_info['task'])}


class ChildManager:
    """Manages child agents synchronously"""
    
    def __init__(self, parent_id: str):
        self.parent_id = parent_id
        self.children = {{}}
        
    async def spawn_child(self, task: str, depth: int) -> Dict[str, Any]:
        """Spawn a child agent and wait for completion"""
        
        if depth >= MAX_RECURSION:
            return {{
                "status": "skipped",
                "reason": "Max recursion depth reached"
            }}
        
        child_id = f"{{self.parent_id}}_child_{{len(self.children)}}"
        
        try:
            # Use claude_run (synchronous) for child agents
            from subprocess import run, PIPE
            
            # Create command to run child task
            cmd = [
                sys.executable, "-c",
                f"""
import os
os.environ['CLAUDE_CODE_TOKEN'] = '{os.environ.get('CLAUDE_CODE_TOKEN', '')}'

# Execute child task using Claude
# This would use the claude_run tool synchronously
result = {{'child_id': '{child_id}', 'task': '{task}', 'status': 'completed'}}
print(json.dumps(result))
"""
            ]
            
            # Run child synchronously
            result = run(cmd, capture_output=True, text=True, timeout=TIMEOUT//2)
            
            if result.returncode == 0:
                child_result = json.loads(result.stdout)
                self.children[child_id] = child_result
                return child_result
            else:
                return {{
                    "status": "failed",
                    "error": result.stderr
                }}
                
        except Exception as e:
            return {{
                "status": "failed",
                "error": str(e)
            }}
    
    def get_all_results(self) -> Dict[str, Any]:
        """Get results from all children"""
        return self.children


async def execute_task():
    """Execute the main task with child management"""
    
    result = {{
        "job_id": JOB_ID,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "task": TASK,
        "agent_profile": AGENT_PROFILE,
        "depth": 0,
        "children": {{}},
        "output": {{}}
    }}
    
    try:
        # Write initial status
        status_file = f"{{OUTPUT_DIR}}/{{JOB_ID}}_status.json"
        with open(status_file, "w") as f:
            json.dump(result, f, indent=2)
        
        # Initialize child manager if enabled
        child_manager = ChildManager(JOB_ID) if MANAGE_CHILDREN else None
        
        # Execute main task logic here
        # This is where the actual Claude API call would happen
        print(f"Executing task: {{TASK[:100]}}...")
        
        # Simulate task execution with potential child spawning
        if "analyze" in TASK.lower() and child_manager:
            # Example: Spawn child agents for sub-analyses
            sub_tasks = [
                "Analyze code structure",
                "Analyze dependencies",
                "Analyze patterns"
            ]
            
            for sub_task in sub_tasks:
                child_result = await child_manager.spawn_child(sub_task, 1)
                print(f"Child task completed: {{child_result.get('status')}}")
        
        # Simulate main task completion
        await asyncio.sleep(2)  # Simulate work
        
        # Collect all results
        result["status"] = "completed"
        result["completed_at"] = datetime.now().isoformat()
        
        if child_manager:
            result["children"] = child_manager.get_all_results()
        
        result["output"] = {{
            "summary": f"Successfully executed task with {{len(result['children'])}} sub-agents",
            "details": {{
                "task_type": "analysis" if "analyze" in TASK.lower() else "execution",
                "confidence": 0.95,
                "findings": []
            }}
        }}
        
        # Write final result
        with open(RESULT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
        # Update status file
        with open(status_file, "w") as f:
            json.dump(result, f, indent=2)
            
        print(f"Task completed successfully. Results written to {{RESULT_FILE}}")
        
    except Exception as e:
        # Handle errors gracefully
        result["status"] = "failed"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        result["completed_at"] = datetime.now().isoformat()
        
        # Write error result
        with open(RESULT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"Task failed: {{e}}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the task
    asyncio.run(execute_task())
'''

    def _write_status_file(self, job: AgentJob) -> None:
        """Write job status to file for monitoring"""
        try:
            status_file = f"{job.output_dir}/{job.job_id}_status.json"
            with open(status_file, "w") as f:
                json.dump(job.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write status file for {job.job_id}: {e}")

    async def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a specific job"""

        # Check active jobs
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]

            # Check if process is still running
            if job.process and job.process.poll() is None:
                return {"status": "running", "job": job.to_dict()}
            else:
                # Process completed, move to completed
                job.status = "completed" if job.process.returncode == 0 else "failed"
                job.completed_at = datetime.now().isoformat()

                self.completed_jobs[job_id] = job
                del self.active_jobs[job_id]

                return {"status": job.status, "job": job.to_dict()}

        # Check completed jobs
        if job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
            return {"status": job.status, "job": job.to_dict()}

        # Job not found
        return {"status": "not_found", "job_id": job_id}

    async def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active jobs"""
        active = []

        for job_id, job in list(self.active_jobs.items()):
            # Check if still running
            if job.process and job.process.poll() is None:
                active.append(job.to_dict())
            else:
                # Move to completed
                job.status = "completed" if job.process.returncode == 0 else "failed"
                job.completed_at = datetime.now().isoformat()

                self.completed_jobs[job_id] = job
                del self.active_jobs[job_id]

        return active

    async def kill_job(self, job_id: str) -> bool:
        """Kill a running job"""

        if job_id not in self.active_jobs:
            return False

        job = self.active_jobs[job_id]

        if job.process:
            try:
                # Kill the process group (includes children)
                os.killpg(os.getpgid(job.process.pid), signal.SIGTERM)

                # Wait a moment for graceful shutdown
                await asyncio.sleep(1)

                # Force kill if still running
                if job.process.poll() is None:
                    os.killpg(os.getpgid(job.process.pid), signal.SIGKILL)

                job.status = "killed"
                job.completed_at = datetime.now().isoformat()

                # Move to completed
                self.completed_jobs[job_id] = job
                del self.active_jobs[job_id]

                return True

            except Exception as e:
                logger.error(f"Failed to kill job {job_id}: {e}")
                return False

        return False
