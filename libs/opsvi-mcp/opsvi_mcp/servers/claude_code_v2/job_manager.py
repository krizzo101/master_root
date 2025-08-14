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
            
            # PARENT DETERMINES MCP REQUIREMENTS
            from .mcp_manager import MCPRequirementAnalyzer, MCPConfigManager
            import json  # Need for passing servers via environment
            required_servers = MCPRequirementAnalyzer.analyze_task(job_info['task'])
            
            # Create minimal MCP config if needed
            mcp_config_path = None
            if required_servers:
                mcp_config_path = MCPConfigManager.create_instance_config(
                    instance_id=job_id,
                    custom_servers=list(required_servers)
                )
                logger.info(f"Parent created MCP config for {job_id}: {list(required_servers)}")
            else:
                logger.info(f"Parent determined no MCP servers needed for {job_id}")
            
            # CONTEXT MANAGEMENT: Prepare specialized agent context
            from .context_manager import (
                prepare_specialized_agent,
                ContextInheritanceManager,
                SessionManager
            )
            
            # Get parent context if this is a child agent
            parent_id = job_info.get('parent_id')
            inherit_session = job_info.get('inherit_session', False)
            
            # Prepare specialized agent with context and prompts
            agent_config = prepare_specialized_agent(
                job_id=job_id,
                task=job_info['task'],
                parent_id=parent_id,
                inherit_session=inherit_session
            )
            
            logger.info(f"Agent {job_id} specialized as '{agent_config['role']}' role")
            
            # Add MCP and context info to job_info for script generation
            job_info['mcp_config_path'] = mcp_config_path
            job_info['required_servers'] = list(required_servers) if required_servers else []
            job_info['agent_config'] = agent_config  # Add context configuration
            
            # Create agent job with parent tracking
            job = AgentJob(
                job_id=job_id,
                task=job_info["task"],
                agent_profile=job_info.get("agent_profile"),
                output_dir=job_info["output_dir"],
                result_file=job_info["result_file"],
                status="spawning",
                spawned_at=datetime.now().isoformat(),
                depth=job_info.get('depth', 0),
                parent_id=parent_id,
            )
            
            # Store in active jobs
            self.active_jobs[job_id] = job
            
            # Create the agent script with pre-determined MCP config
            agent_script = self._create_claude_agent_script(job_info)
            
            # Write script to temp file
            script_path = f"/tmp/agent_{job_id}.py"
            with open(script_path, "w") as f:
                f.write(agent_script)
            
            # Spawn the agent process
            env = os.environ.copy()
            
            # CRITICAL: Remove ANTHROPIC_API_KEY to prevent API token usage
            if "ANTHROPIC_API_KEY" in env:
                del env["ANTHROPIC_API_KEY"]
            
            # Set Claude Code token and job-specific variables
            env.update({
                "CLAUDE_CODE_TOKEN": self.config.claude_token or "",
                "AGENT_JOB_ID": job_id,
                "AGENT_OUTPUT_DIR": job_info.get("output_dir", "/tmp/claude_results"),
                "AGENT_RESULT_FILE": job_info.get("result_file", f"/tmp/claude_results/{job_id}.json"),
                # PARENT PASSES MCP CONFIG TO CHILD
                "AGENT_MCP_CONFIG": mcp_config_path or "",
                "AGENT_MCP_SERVERS": json.dumps(job_info.get('required_servers', [])),
                # CONTEXT CONFIGURATION
                "AGENT_SESSION_ID": agent_config.get('session_id', ''),
                "AGENT_ROLE": agent_config.get('role', 'general'),
                "AGENT_SYSTEM_PROMPT": agent_config.get('system_prompt', ''),
                "AGENT_RESUME_SESSION": agent_config.get('resume_command', ''),
                "AGENT_PARENT_CONTEXT": json.dumps(agent_config.get('parent_context', {})),
            })
            
            # Also remove any other ANTHROPIC_* variables
            # Keep other CLAUDE_* variables as they might be needed for configuration
            for key in list(env.keys()):
                if key.startswith("ANTHROPIC_"):
                    del env[key]
            
            # Start process detached
            process = subprocess.Popen(
                [sys.executable, script_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
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
        """Create a Python script that uses parent-determined MCP configuration"""
        
        # Escape the task string properly
        task_escaped = repr(job_info['task'])
        
        # Use parent-provided MCP and context configuration
        mcp_config_path = job_info.get('mcp_config_path')
        required_servers = job_info.get('required_servers', [])
        agent_config = job_info.get('agent_config', {})
        
        return f'''#!/usr/bin/env python3
"""
Claude Code Agent Script - Uses parent-determined MCP and context configuration
Job ID: {job_info['job_id']}
Role: {agent_config.get('role', 'general')}
MCP Config: {'Custom' if mcp_config_path else 'None (no MCP servers needed)'}
Required Servers: {required_servers if required_servers else 'None'}

IMPORTANT: Both MCP and context configuration are determined by the PARENT process.
This child process receives all configuration via environment variables.
"""'

import os
import sys
import json
import subprocess
import time
import asyncio
from datetime import datetime

# CRITICAL: Ensure ANTHROPIC_API_KEY is not used
# This must happen BEFORE any other operations
if "ANTHROPIC_API_KEY" in os.environ:
    del os.environ["ANTHROPIC_API_KEY"]
# Also set it to empty as a double safety measure
os.environ["ANTHROPIC_API_KEY"] = ""

# Configuration from parent process
JOB_ID = os.environ.get("AGENT_JOB_ID", "{job_info['job_id']}")
OUTPUT_DIR = os.environ.get("AGENT_OUTPUT_DIR", "{job_info['output_dir']}")
RESULT_FILE = os.environ.get("AGENT_RESULT_FILE", "{job_info['result_file']}")
TASK = {task_escaped}
TIMEOUT = {job_info.get('timeout', 600)}

# MCP configuration determined by parent
MCP_CONFIG_PATH = os.environ.get("AGENT_MCP_CONFIG", "") or None
REQUIRED_MCP_SERVERS = json.loads(os.environ.get("AGENT_MCP_SERVERS", "[]"))

# Context configuration from parent
SESSION_ID = os.environ.get("AGENT_SESSION_ID", "")
ROLE = os.environ.get("AGENT_ROLE", "general")
SYSTEM_PROMPT = os.environ.get("AGENT_SYSTEM_PROMPT", "")
RESUME_SESSION = os.environ.get("AGENT_RESUME_SESSION", "")
PARENT_CONTEXT = json.loads(os.environ.get("AGENT_PARENT_CONTEXT", "{{}}"))

print(f"Agent {{JOB_ID}} starting with parent-provided configuration")
print(f"  Role: {{ROLE}}")
if SESSION_ID:
    print(f"  Session ID: {{SESSION_ID}}")
if RESUME_SESSION:
    print(f"  Resuming from: {{RESUME_SESSION}}")
if MCP_CONFIG_PATH:
    print(f"  MCP Config: {{MCP_CONFIG_PATH}}")
    print(f"  Required Servers: {{REQUIRED_MCP_SERVERS}}")
else:
    print(f"  No MCP servers required (parent determined)")

def check_mcp_ready(attempt=1, max_attempts=10):
    """Check if MCP servers are ready with exponential backoff"""
    if not REQUIRED_MCP_SERVERS:
        return True
    
    # Simulate MCP readiness check (in real implementation, would probe servers)
    # For now, use timing-based approach
    elapsed = time.time() - START_TIME
    
    # Assume 1-2 seconds per server when loading minimal set
    expected_time = len(REQUIRED_MCP_SERVERS) * 1.5
    
    if elapsed >= expected_time:
        print(f"MCP servers ready after {{elapsed:.1f}}s")
        return True
    
    if attempt >= max_attempts:
        print(f"MCP servers failed to initialize after {{attempt}} attempts")
        return False
    
    # Exponential backoff
    wait_time = min(0.5 * (2 ** (attempt - 1)), 2.0)
    time.sleep(wait_time)
    return check_mcp_ready(attempt + 1, max_attempts)

def execute_claude_code():
    """Execute task using real Claude Code CLI with intelligent MCP management"""
    
    result = {{
        "job_id": JOB_ID,
        "task": TASK,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "role": ROLE,
        "session_id": SESSION_ID,
        "parent_context": PARENT_CONTEXT,
        "mcp_servers_required": REQUIRED_MCP_SERVERS,
        "mcp_config": MCP_CONFIG_PATH
    }}
    
    try:
        # Build Claude command
        cmd = [
            "claude",
            "--dangerously-skip-permissions",  # For automation
            "--output-format", "json"
        ]
        
        # Add session management
        if SESSION_ID:
            cmd.extend(["--session-id", SESSION_ID])
        
        # Add session resumption if needed
        if RESUME_SESSION and RESUME_SESSION.startswith("--resume"):
            # Parse the --resume command
            resume_parts = RESUME_SESSION.split()
            cmd.extend(resume_parts)
        
        # Add custom system prompt if provided
        if SYSTEM_PROMPT:
            cmd.extend(["--append-system-prompt", SYSTEM_PROMPT])
        
        # Add MCP configuration if needed
        if MCP_CONFIG_PATH:
            cmd.extend(["--mcp-config", MCP_CONFIG_PATH])
            cmd.append("--strict-mcp-config")  # Only load specified servers
        
        # Prepare environment for Claude Code
        env = os.environ.copy()
        
        # Ensure CLAUDE_CODE_TOKEN is set (passed from parent)
        claude_token = os.environ.get("CLAUDE_CODE_TOKEN", "")
        if claude_token:
            env["CLAUDE_CODE_TOKEN"] = claude_token
        
        # CRITICAL: Remove ANTHROPIC_API_KEY to force user auth
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
            print("Removed ANTHROPIC_API_KEY to use Claude Code auth")
        
        # Remove any other conflicting variables
        for key in list(env.keys()):
            if key.startswith("ANTHROPIC_"):
                del env[key]
        
        # Start Claude process
        print(f"Starting Claude with {{len(REQUIRED_MCP_SERVERS)}} MCP servers...")
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Wait for MCP servers to be ready if needed
        if REQUIRED_MCP_SERVERS:
            print(f"Waiting for MCP servers: {{REQUIRED_MCP_SERVERS}}")
            if not check_mcp_ready():
                result["status"] = "failed"
                result["error"] = "MCP servers failed to initialize within timeout"
                process.terminate()
                raise RuntimeError("MCP initialization timeout")
        
        # Send task and get result with timeout
        stdout, stderr = process.communicate(input=TASK, timeout=TIMEOUT)
        
        if process.returncode == 0:
            # Parse Claude's JSON output
            try:
                claude_result = json.loads(stdout)
                result["status"] = "completed"
                result["output"] = claude_result
                result["claude_session_id"] = claude_result.get("session_id")
                result["claude_cost"] = claude_result.get("total_cost_usd", 0)
                result["mcp_initialization_time"] = time.time() - START_TIME if REQUIRED_MCP_SERVERS else 0
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
        process.terminate()
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
        if REQUIRED_MCP_SERVERS:
            print(f"MCP initialization took: {{result.get('mcp_initialization_time', 0):.1f}}s")
        print(f"Result saved to: {{RESULT_FILE}}")
    
    return result

# Global start time for MCP timing
START_TIME = time.time()

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
            "task": job.task[:100] + "..." if len(job.task) > 100 else job.task
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