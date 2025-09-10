#!/usr/bin/env python3
"""
Context-Isolated Agent Orchestrator
Fixes agent context isolation to prevent cross-agent config leakage.
Each agent runs in its own isolated .agent_exec/[agent_id]/ directory.
"""

import asyncio
import json
import logging
import os
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Generic agent task definition"""

    task_id: str
    task_type: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    quality_gates: List[str] = field(default_factory=list)
    mcp_needs: Optional[List[str]] = None  # MCP servers needed for this task

    def to_dict(self) -> Dict:
        return asdict(self)


class TokenPool:
    """Manages Claude API tokens for parallel execution"""

    def __init__(self, tokens: List[str] = None):
        if tokens is not None:
            self.tokens = [t for t in tokens if t and t.strip()]
        else:
            try:
                from token_loader import load_tokens
                self.tokens = load_tokens()
                if not self.tokens:
                    raise RuntimeError("TokenLoader returned empty token list")
            except ImportError:
                raise RuntimeError(
                    "CATASTROPHIC FAILURE: TokenLoader not available and no explicit tokens provided."
                )
            except Exception as e:
                raise RuntimeError(f"CATASTROPHIC FAILURE: TokenLoader failed: {str(e)}")

        if not self.tokens:
            raise RuntimeError("CATASTROPHIC FAILURE: No valid tokens available.")

        self.current_index = 0
        self.lock = asyncio.Lock()
        self.in_use = set()
        logger.info(f"Token pool initialized with {len(self.tokens)} tokens")

    async def acquire(self) -> Tuple[str, int]:
        """Get next available token (round-robin)"""
        async with self.lock:
            token = self.tokens[self.current_index]
            token_idx = self.current_index
            self.current_index = (self.current_index + 1) % len(self.tokens)
            self.in_use.add(token_idx)
            return token, token_idx

    def release(self, token_idx: int):
        """Release a token back to the pool"""
        if token_idx in self.in_use:
            self.in_use.discard(token_idx)
            logger.debug(f"Released token index {token_idx}")

    def size(self) -> int:
        return len(self.tokens)


class DependencyManager:
    """Manages task dependencies"""

    def __init__(self):
        self.completed: set = set()
        self.running: set = set()
        self.failed: set = set()
        self.lock = asyncio.Lock()

    async def can_run(self, task: AgentTask) -> bool:
        """Check if task dependencies are satisfied"""
        async with self.lock:
            if task.task_id in self.running or task.task_id in self.completed:
                return False
            for dep in task.dependencies:
                if dep not in self.completed:
                    return False
            return True

    async def mark_running(self, task_id: str):
        async with self.lock:
            self.running.add(task_id)

    async def mark_completed(self, task_id: str):
        async with self.lock:
            self.running.discard(task_id)
            self.completed.add(task_id)

    async def mark_failed(self, task_id: str):
        async with self.lock:
            self.running.discard(task_id)
            self.failed.add(task_id)


class ContextIsolatedOrchestrator:
    """
    Context-isolated orchestrator for parallel Claude agent execution.
    Each agent runs in its own isolated .agent_exec/[agent_id]/ directory.
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        master_mcp_registry_path: Optional[Path] = None,
        agent_execution_profile: str = "standard",
        agent_debug_mode: bool = False,
        enable_context_isolation: bool = True,  # New flag for isolation
        cleanup_on_completion: bool = True,     # Cleanup isolated contexts
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Context isolation settings
        self.enable_context_isolation = enable_context_isolation
        self.cleanup_on_completion = cleanup_on_completion
        self.isolated_contexts: Dict[str, Path] = {}  # Track created contexts
        
        # Create .agent_exec directory for isolated contexts
        if self.enable_context_isolation:
            self.agent_exec_dir = self.output_dir / ".agent_exec"
            self.agent_exec_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Context isolation enabled at: {self.agent_exec_dir}")
        
        # Store parameters
        self.use_optimizations = use_optimizations
        self.master_mcp_registry_path = master_mcp_registry_path
        self.agent_execution_profile = agent_execution_profile
        self.agent_debug_mode = agent_debug_mode
        
        # Ensure subdirectories exist
        (self.output_dir / "tasks").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        (self.output_dir / "shared_data").mkdir(exist_ok=True)
        
        # Setup logging
        self.log_file = (
            self.output_dir / "logs" / 
            f"orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.debug(f"Debug logging initialized: {self.log_file}")
        
        # Initialize components
        self.max_parallel = max(1, max_parallel if max_parallel is not None else 10)
        self.token_pool = TokenPool(tokens)
        self.dep_manager = DependencyManager()
        
        # Setup base Claude command
        self.claude_cmd = ["claude", "-p"]
        
        # Metrics
        self.metrics = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "total_duration": 0,
            "start_time": None,
            "end_time": None,
        }
        
        # Hooks for customization
        self.pre_execute_hook: Optional[Callable] = None
        self.post_execute_hook: Optional[Callable] = None
        self.task_builder_hook: Optional[Callable] = None

    def _create_isolated_context(self, task: AgentTask) -> Path:
        """Create an isolated execution context for an agent."""
        # Create unique context directory
        context_id = f"{task.task_id}_{uuid.uuid4().hex[:8]}"
        context_dir = self.agent_exec_dir / context_id
        context_dir.mkdir(parents=True, exist_ok=True)
        
        # Create standard subdirectories
        (context_dir / "workspace").mkdir(exist_ok=True)
        (context_dir / "logs").mkdir(exist_ok=True)
        (context_dir / "data").mkdir(exist_ok=True)
        
        # Track this context for cleanup
        self.isolated_contexts[task.task_id] = context_dir
        
        logger.info(f"Created isolated context for {task.task_id}: {context_dir}")
        return context_dir

    def _generate_isolated_mcp_config(self, task: AgentTask, context_dir: Path) -> Path:
        """Generate MCP configuration isolated to agent's context."""
        config_path = context_dir / "mcp_config.json"
        
        # Base MCP configuration
        mcp_config = {
            "mcpServers": {}
        }
        
        # Load from master registry if available
        if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
            try:
                with open(self.master_mcp_registry_path) as f:
                    master_config = json.load(f)
                    mcp_config["mcpServers"].update(master_config.get("mcpServers", {}))
            except Exception as e:
                logger.warning(f"Failed to load master MCP registry: {e}")
        
        # Apply profile filtering
        mcp_config = self._filter_mcp_by_profile(mcp_config, self.agent_execution_profile)
        
        # Add task-specific MCP servers if specified
        if hasattr(task, "mcp_needs") and task.mcp_needs:
            filtered_servers = {}
            for server_name in task.mcp_needs:
                if server_name in mcp_config.get("mcpServers", {}):
                    filtered_servers[server_name] = mcp_config["mcpServers"][server_name]
            mcp_config["mcpServers"] = filtered_servers
        
        # Add minimal research tools if needed
        if task.task_type == "research" and not mcp_config.get("mcpServers"):
            mcp_config["mcpServers"] = {
                "mcp_web_search": {
                    "command": "npx",
                    "args": ["-y", "brave-search-mcp"],
                    "env": {"BRAVE_API_KEY": "BSAqv6fii19i_ZRARk67Gs5udOHgxSN"},
                },
                "research_papers": {
                    "command": "/home/opsvi/miniconda/bin/python",
                    "args": ["-m", "arxiv_mcp_server"],
                },
            }
        
        # Update environment variables for isolation
        for server_name, server_config in mcp_config.get("mcpServers", {}).items():
            if "env" not in server_config:
                server_config["env"] = {}
            
            # Set isolated context environment
            server_config["env"]["AGENT_TASK_ID"] = task.task_id
            server_config["env"]["AGENT_CONTEXT_DIR"] = str(context_dir)
            server_config["env"]["AGENT_WORKSPACE"] = str(context_dir / "workspace")
            server_config["env"]["AGENT_TASK_TYPE"] = task.task_type
        
        # Write config to isolated context
        config_path.write_text(json.dumps(mcp_config, indent=2))
        logger.debug(f"Generated isolated MCP config for {task.task_id}: {config_path}")
        
        return config_path

    def _filter_mcp_by_profile(self, config: Dict, profile: str) -> Dict:
        """Filter MCP config based on execution profile."""
        profile_servers = {
            "minimal": ["shell_exec", "time"],
            "standard": [
                "shell_exec", "time", "mcp_web_search", 
                "firecrawl", "research_papers"
            ],
            "research": [
                "shell_exec", "time", "mcp_web_search", 
                "firecrawl", "research_papers", "tech_docs", "knowledge"
            ],
            "full": None,  # Include all
        }
        
        if profile == "full" or profile not in profile_servers:
            return config
        
        allowed = profile_servers[profile]
        filtered = {
            "mcpServers": {
                k: v for k, v in config.get("mcpServers", {}).items() 
                if k in allowed
            }
        }
        
        return filtered

    def _create_isolated_env_file(self, task: AgentTask, context_dir: Path) -> Path:
        """Create an isolated .env file for the agent."""
        env_file = context_dir / ".env"
        
        env_content = [
            f"# Isolated environment for agent {task.task_id}",
            f"AGENT_ID={task.task_id}",
            f"AGENT_TYPE={task.task_type}",
            f"AGENT_CONTEXT_DIR={context_dir}",
            f"WORKSPACE_ROOT={context_dir / 'workspace'}",
            f"DATA_DIR={context_dir / 'data'}",
            f"LOG_DIR={context_dir / 'logs'}",
            f"SHARED_DATA_DIR={self.output_dir / 'shared_data'}",
            f"OUTPUT_DIR={self.output_dir}",
            f"ISOLATION_ENABLED=true",
            f"CONTEXT_ID={context_dir.name}",
        ]
        
        # Add task context as environment variables
        if task.context:
            for key, value in task.context.items():
                if isinstance(value, (str, int, float, bool)):
                    env_content.append(f"TASK_{key.upper()}={value}")
        
        env_file.write_text("\n".join(env_content))
        logger.debug(f"Created isolated .env for {task.task_id}: {env_file}")
        
        return env_file

    def _cleanup_isolated_context(self, task_id: str):
        """Clean up an isolated context after agent completion."""
        if task_id in self.isolated_contexts:
            context_dir = self.isolated_contexts[task_id]
            
            try:
                # Save any important artifacts before cleanup
                artifacts_dir = self.output_dir / "artifacts" / task_id
                if (context_dir / "workspace").exists():
                    # Copy workspace contents to artifacts
                    artifacts_dir.mkdir(parents=True, exist_ok=True)
                    for item in (context_dir / "workspace").iterdir():
                        if item.is_file():
                            shutil.copy2(item, artifacts_dir)
                
                # Remove the isolated context
                shutil.rmtree(context_dir)
                del self.isolated_contexts[task_id]
                logger.info(f"Cleaned up isolated context for {task_id}")
                
            except Exception as e:
                logger.error(f"Failed to cleanup context for {task_id}: {e}")

    async def execute_agent(self, task: AgentTask) -> Dict:
        """Execute a single agent task in an isolated context."""
        session_id = str(uuid.uuid4())
        
        # Create isolated context if enabled
        if self.enable_context_isolation:
            context_dir = self._create_isolated_context(task)
            
            # Generate isolated configurations
            mcp_config_path = self._generate_isolated_mcp_config(task, context_dir)
            env_file_path = self._create_isolated_env_file(task, context_dir)
            
            # Create symlink to shared data
            shared_data = self.output_dir / "shared_data"
            if shared_data.exists():
                shared_link = context_dir / "shared"
                if not shared_link.exists():
                    shared_link.symlink_to(shared_data)
            
            work_dir = context_dir
        else:
            # Fallback to non-isolated execution
            context_dir = self.output_dir
            work_dir = self.output_dir
            mcp_config_path = None
        
        # Pre-execution hook
        if self.pre_execute_hook:
            await self.pre_execute_hook(task)
        
        # Build full prompt
        if self.task_builder_hook:
            prompt = await self.task_builder_hook(task)
        else:
            prompt = task.prompt
        
        # Prepare command
        cmd = self.claude_cmd.copy()
        
        # Add optimization flags
        if self.use_optimizations:
            cmd.extend([
                "--model", "opus",
                "--output-format", "json",
                "--dangerously-skip-permissions",
            ])
        
        # Add MCP config if using isolation
        if self.enable_context_isolation and mcp_config_path:
            cmd.extend(["--mcp-config", str(mcp_config_path)])
        
        # Add debug flag if enabled
        if getattr(task, "debug_mode", False) or self.agent_debug_mode:
            cmd.append("--debug")
        
        # Add system prompt based on task type
        system_prompts = {
            "analysis": "You are a specialized analysis agent. Focus on thorough, data-driven analysis.",
            "monitoring": "You are a system monitoring agent. Focus on performance metrics and system health.",
            "research": "You are a research specialist. Focus on comprehensive information gathering.",
        }
        
        if task.task_type in system_prompts:
            cmd.extend(["--append-system-prompt", system_prompts[task.task_type]])
        
        # Add session and workspace parameters
        cmd.extend([
            "--session-id", session_id,
            "--add-dir", str(work_dir),
            "--",  # Separator before prompt
            prompt,
        ])
        
        # Get token
        token, token_idx = await self.token_pool.acquire()
        
        try:
            # Prepare isolated environment
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token
            
            if self.enable_context_isolation:
                # Set isolated environment variables
                env["AGENT_WORKSPACE"] = str(context_dir)
                env["AGENT_MCP_CONFIG"] = str(mcp_config_path)
                env["AGENT_TASK_ID"] = task.task_id
                env["AGENT_TASK_TYPE"] = task.task_type
                env["ISOLATION_ENABLED"] = "true"
                
                # Load .env file
                if env_file_path and env_file_path.exists():
                    for line in env_file_path.read_text().splitlines():
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            env[key.strip()] = value.strip()
            
            # Execute agent
            task.start_time = datetime.now().timestamp()
            task.status = "running"
            await self.dep_manager.mark_running(task.task_id)
            
            logger.info(f"Executing {task.task_id} ({task.task_type}) in isolated context")
            
            # Set up logging
            log_file = None
            if self.enable_context_isolation:
                log_file = context_dir / "logs" / f"agent_{task.task_id}.log"
                log_file.parent.mkdir(parents=True, exist_ok=True)
                log_handle = open(log_file, "w")
                stderr_target = log_handle
            else:
                stderr_target = asyncio.subprocess.PIPE
                log_handle = None
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    cwd=str(work_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=stderr_target,
                )
                
                stdout, stderr = await process.communicate()
                
                # Close log file if used
                if log_handle:
                    log_handle.close()
                    # Read stderr from log file if process failed
                    if process.returncode != 0 and log_file:
                        with open(log_file) as f:
                            stderr = f.read().encode()
                
                task.end_time = datetime.now().timestamp()
                duration = task.end_time - task.start_time
                
                if process.returncode == 0:
                    try:
                        task.result = json.loads(stdout.decode())
                        task.status = "completed"
                        await self.dep_manager.mark_completed(task.task_id)
                        self.metrics["completed"] += 1
                        logger.info(f"✓ {task.task_id} completed in {duration:.2f}s")
                    except json.JSONDecodeError as e:
                        task.status = "failed"
                        task.error = f"JSON parsing failed: {e}"
                        await self.dep_manager.mark_failed(task.task_id)
                        self.metrics["failed"] += 1
                        logger.error(f"✗ {task.task_id} JSON parsing failed")
                else:
                    task.status = "failed"
                    task.error = stderr.decode() if stderr else "Process failed"
                    await self.dep_manager.mark_failed(task.task_id)
                    self.metrics["failed"] += 1
                    logger.error(f"✗ {task.task_id} failed: {task.error[:200]}")
                
                self.metrics["total_duration"] += duration
                
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                await self.dep_manager.mark_failed(task.task_id)
                self.metrics["failed"] += 1
                logger.error(f"✗ {task.task_id} exception: {e}")
            
        finally:
            # Release token
            self.token_pool.release(token_idx)
            
            # Cleanup isolated context if enabled
            if self.enable_context_isolation and self.cleanup_on_completion:
                self._cleanup_isolated_context(task.task_id)
        
        # Post-execution hook
        if self.post_execute_hook:
            await self.post_execute_hook(task)
        
        # Save task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))
        
        return task.to_dict()

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute a batch of tasks respecting dependencies and parallelism limits."""
        self.metrics["total"] = len(tasks)
        self.metrics["start_time"] = datetime.now().isoformat()
        
        results = []
        
        while len(results) < len(tasks):
            # Find tasks ready to run
            ready_tasks = []
            for task in tasks:
                if task.status == "pending" and await self.dep_manager.can_run(task):
                    ready_tasks.append(task)
                    if len(ready_tasks) >= self.max_parallel:
                        break
            
            if not ready_tasks:
                # Check if we're stuck
                pending = [t for t in tasks if t.status == "pending"]
                if pending:
                    logger.warning(f"Possible deadlock: {len(pending)} tasks pending")
                    for task in pending:
                        task.status = "failed"
                        task.error = "Dependencies not met"
                        results.append(task.to_dict())
                break
            
            # Execute ready tasks in parallel
            logger.info(f"Executing batch of {len(ready_tasks)} tasks")
            batch_results = await asyncio.gather(
                *[self.execute_agent(task) for task in ready_tasks],
                return_exceptions=True,
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch execution error: {result}")
                else:
                    results.append(result)
            
            # Brief pause between batches
            await asyncio.sleep(0.5)
        
        self.metrics["end_time"] = datetime.now().isoformat()
        
        # Final cleanup of any remaining contexts
        if self.enable_context_isolation and self.cleanup_on_completion:
            for task_id in list(self.isolated_contexts.keys()):
                self._cleanup_isolated_context(task_id)
        
        return results

    async def run(
        self,
        task_generator: Callable[[], List[AgentTask]],
        result_processor: Optional[Callable[[List[Dict]], None]] = None,
    ) -> Dict:
        """Main entry point - run orchestration with custom task generator."""
        logger.info("Starting orchestration with context isolation")
        
        # Generate tasks
        tasks = task_generator()
        logger.info(f"Generated {len(tasks)} tasks")
        
        # Execute tasks
        results = await self.execute_batch(tasks)
        
        # Process results
        if result_processor:
            result_processor(results)
        
        # Save metrics
        metrics_file = self.output_dir / "metrics.json"
        metrics_file.write_text(json.dumps(self.metrics, indent=2))
        
        # Generate summary
        summary = {
            "metrics": self.metrics,
            "results": results,
            "isolation_enabled": self.enable_context_isolation,
            "contexts_created": len(self.isolated_contexts),
            "contexts_cleaned": self.cleanup_on_completion,
        }
        
        summary_file = self.output_dir / "summary.json"
        summary_file.write_text(json.dumps(summary, indent=2))
        
        logger.info(
            f"Orchestration complete: {self.metrics['completed']}/{self.metrics['total']} tasks succeeded"
        )
        
        return summary


# Example usage
if __name__ == "__main__":
    async def main():
        # Example task generator
        def generate_tasks():
            return [
                AgentTask(
                    task_id="task_1",
                    task_type="research",
                    prompt="Research Python async programming",
                    mcp_needs=["mcp_web_search"],
                ),
                AgentTask(
                    task_id="task_2",
                    task_type="analysis",
                    prompt="Analyze system performance",
                    dependencies=["task_1"],
                ),
            ]
        
        # Run orchestrator with context isolation
        orchestrator = ContextIsolatedOrchestrator(
            output_dir=Path("test_isolation"),
            max_parallel=2,
            enable_context_isolation=True,
            cleanup_on_completion=True,
        )
        
        summary = await orchestrator.run(generate_tasks)
        print(json.dumps(summary, indent=2))
    
    asyncio.run(main())