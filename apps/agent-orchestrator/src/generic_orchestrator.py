#!/usr/bin/env python3
"""
Generic Agent Orchestrator Framework
A simplified, reusable orchestrator for parallel Claude agent execution
Extracted and simplified from Hecaton patterns
"""

import asyncio
import json
import logging
import os
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Generic agent task definition with enhanced error tracking"""

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
    quality_gates: List[str] = field(
        default_factory=list
    )  # Quality gates for enhanced orchestrator
    raw_output: Optional[str] = None  # Store raw stdout for debugging
    error_details: Optional[Dict] = None  # Detailed error information

    def to_dict(self) -> Dict:
        """Convert to dictionary with error details"""
        result = asdict(self)
        # Include error details only if present
        if self.raw_output and len(self.raw_output) > 1000:
            # Truncate very long raw output for serialization
            result["raw_output"] = (
                self.raw_output[:500] + "..." + self.raw_output[-500:]
            )
        return result


class TokenPool:
    """
    Manages Claude API tokens for parallel execution

    CRITICAL SAFETY REQUIREMENT:
    NO FALLBACK to single environment token allowed.
    Must use TokenTool or fail catastrophically.
    """

    def __init__(self, tokens: List[str] = None):
        # Handle explicit tokens or call TokenTool
        if tokens is not None:
            self.tokens = [t for t in tokens if t and t.strip()]
        else:
            # Call TokenLoader to get token pool - NO ENV FALLBACK ALLOWED
            try:
                from .token_loader import load_tokens

                self.tokens = load_tokens()
                if not self.tokens:
                    raise RuntimeError("TokenLoader returned empty token list")
            except ImportError:
                # TokenLoader not available - CATASTROPHIC FAILURE
                raise RuntimeError(
                    "CATASTROPHIC FAILURE: TokenLoader not available and no explicit tokens provided. "
                    "NO FALLBACK to environment variables allowed. "
                    "TokenLoader must work or system must fail."
                )
            except Exception as e:
                # TokenLoader failed - CATASTROPHIC FAILURE
                raise RuntimeError(
                    f"CATASTROPHIC FAILURE: TokenLoader failed: {str(e)}. "
                    "NO FALLBACK to environment variables allowed."
                )

        # Ensure we have valid tokens
        if not self.tokens:
            raise RuntimeError(
                "CATASTROPHIC FAILURE: No valid tokens available. "
                "TokenTool must provide tokens or system must fail - NO ENV FALLBACK."
            )

        self.current_index = 0
        self.lock = asyncio.Lock()
        self.in_use = set()  # Track tokens in use

        logger.info(
            f"Token pool initialized with {len(self.tokens)} tokens - NO FALLBACKS ENABLED"
        )

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

    @property
    def available(self) -> int:
        """Get number of available tokens (not in use)"""
        return len(self.tokens) - len(self.in_use)


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
            # Can't run if already running or completed
            if task.task_id in self.running or task.task_id in self.completed:
                return False

            # Check all dependencies are completed
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


class MessageBus:
    """Simple file-based message passing between agents"""

    def __init__(self, message_dir: Path):
        self.message_dir = message_dir
        self.message_dir.mkdir(parents=True, exist_ok=True)

    async def send(self, from_id: str, to_id: str, message: Dict):
        """Send message from one agent to another"""
        msg_file = self.message_dir / f"{to_id}_{datetime.now().timestamp()}.json"
        msg_data = {
            "from": from_id,
            "to": to_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        msg_file.write_text(json.dumps(msg_data, indent=2))

    async def receive(self, agent_id: str) -> List[Dict]:
        """Get all messages for an agent"""
        messages = []
        for msg_file in self.message_dir.glob(f"{agent_id}_*.json"):
            messages.append(json.loads(msg_file.read_text()))
            msg_file.unlink()  # Delete after reading
        return sorted(messages, key=lambda x: x["timestamp"])


class GenericOrchestrator:
    """
    Generic orchestrator for parallel Claude agent execution.
    Can be customized for any use case by providing task generator and result processor.
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        # New parameters for dynamic architecture
        master_mcp_registry_path: Optional[Path] = None,
        agent_execution_profile: str = "standard",  # standard, minimal, research, full
        agent_debug_mode: bool = False,
        agent_base_work_dir: Optional[Path] = None,
        enable_dynamic_configs: bool = False,
        log_to_work_dir: bool = False,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Store all parameters including existing ones
        self.use_optimizations = use_optimizations

        # Store new parameters
        self.master_mcp_registry_path = master_mcp_registry_path
        self.agent_execution_profile = agent_execution_profile
        self.agent_debug_mode = agent_debug_mode
        self.agent_base_work_dir = (
            agent_base_work_dir or output_dir / "agent_workspaces"
        )
        self.enable_dynamic_configs = enable_dynamic_configs
        self.log_to_work_dir = log_to_work_dir

        # Create agent work directory if needed
        if self.enable_dynamic_configs:
            self.agent_base_work_dir.mkdir(parents=True, exist_ok=True)

        # Ensure subdirectories exist
        (self.output_dir / "tasks").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)

        # Setup debug file logging
        self.log_file = (
            self.output_dir
            / "logs"
            / f"orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.debug(f"Debug logging initialized: {self.log_file}")

        # Handle None and invalid values
        self.max_parallel = max(1, max_parallel if max_parallel is not None else 10)

        # Initialize TokenPool - will use TokenTool automatically if no explicit tokens
        # NO FALLBACK to single environment token allowed per safety requirements
        self.token_pool = TokenPool(tokens)
        self.dep_manager = DependencyManager()
        self.message_bus = MessageBus(output_dir / "messages")

        # Setup Claude command
        self.claude_cmd = ["claude", "-p"]

        if use_optimizations:
            # NEW: Check for master registry first
            if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
                # Load from master registry
                with open(self.master_mcp_registry_path) as f:
                    mcp_config = json.load(f)

                # Filter based on execution profile
                if self.agent_execution_profile != "full":
                    mcp_config = self._filter_mcp_by_profile(
                        mcp_config, self.agent_execution_profile
                    )

                # Write filtered config
                research_config = Path(self.output_dir) / "research_mcp.json"
                research_config.write_text(json.dumps(mcp_config, indent=2))
            else:
                # Existing minimal research config
                research_config = Path(self.output_dir) / "research_mcp.json"

                # Only include essential research tools (not all 15+ MCP servers)
                minimal_research_config = {
                    "mcpServers": {
                        "mcp_web_search": {
                            "command": "npx",
                            "args": ["-y", "brave-search-mcp"],
                            "env": {"BRAVE_API_KEY": "BSAqv6fii19i_ZRARk67Gs5udOHgxSN"},
                        },
                        "research_papers": {
                            "command": "/home/opsvi/miniconda/bin/python",
                            "args": ["-m", "arxiv_mcp_server"],
                        },
                        "firecrawl": {
                            "command": "npx",
                            "args": ["-y", "firecrawl-mcp"],
                            "env": {
                                "FIRECRAWL_API_KEY": "fc-a9cc6620c7b24c9c90bd010c73deb51f"
                            },
                        },
                    }
                }

                research_config.write_text(
                    json.dumps(minimal_research_config, indent=2)
                )

            self.claude_cmd.extend(
                [
                    "--model",
                    "opus",  # Better for research quality
                    "--mcp-config",
                    str(research_config),
                    "--dangerously-skip-permissions",
                    "--allowedTools",
                    "mcp__mcp_web_search__brave_web_search,mcp__research_papers__search_papers,mcp__firecrawl__firecrawl_search,WebSearch,Read,Write,Bash",
                    "--output-format",
                    "json",
                ]
            )

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

    def _filter_mcp_by_profile(self, config: Dict, profile: str) -> Dict:
        """Filter MCP config based on execution profile."""

        profile_servers = {
            "minimal": ["shell_exec", "time"],
            "standard": [
                "shell_exec",
                "time",
                "mcp_web_search",
                "firecrawl",
                "research_papers",
            ],
            "research": [
                "shell_exec",
                "time",
                "mcp_web_search",
                "firecrawl",
                "research_papers",
                "tech_docs",
                "knowledge",
            ],
            "full": None,  # Include all
        }

        if profile == "full" or profile not in profile_servers:
            return config

        allowed = profile_servers[profile]
        filtered = {
            "mcpServers": {
                k: v for k, v in config.get("mcpServers", {}).items() if k in allowed
            }
        }

        return filtered

    def _generate_agent_mcp_config(self, task: AgentTask, config_path: Path):
        """Generate agent-specific MCP configuration based on task requirements."""

        # Start with base config
        if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
            with open(self.master_mcp_registry_path) as f:
                mcp_config = json.load(f)
        else:
            # Use minimal config
            mcp_config = {
                "mcpServers": {
                    "mcp_web_search": {
                        "command": "npx",
                        "args": ["-y", "brave-search-mcp"],
                        "env": {"BRAVE_API_KEY": "BSAqv6fii19i_ZRARk67Gs5udOHgxSN"},
                    },
                    "research_papers": {
                        "command": "/home/opsvi/miniconda/bin/python",
                        "args": ["-m", "arxiv_mcp_server"],
                    },
                    "firecrawl": {
                        "command": "npx",
                        "args": ["-y", "firecrawl-mcp"],
                        "env": {
                            "FIRECRAWL_API_KEY": "fc-a9cc6620c7b24c9c90bd010c73deb51f"
                        },
                    },
                }
            }

        # Check for task-specific MCP needs (if task has mcp_needs attribute)
        if hasattr(task, "mcp_needs") and task.mcp_needs:
            # Only include specifically requested MCP servers
            filtered_servers = {}
            for server_name in task.mcp_needs:
                if server_name in mcp_config.get("mcpServers", {}):
                    filtered_servers[server_name] = mcp_config["mcpServers"][
                        server_name
                    ]
            mcp_config["mcpServers"] = filtered_servers
        elif self.agent_execution_profile != "full":
            # Apply profile filtering if no specific needs
            mcp_config = self._filter_mcp_by_profile(
                mcp_config, self.agent_execution_profile
            )

        # Task-specific customizations based on task type
        if task.task_type == "research":
            # Ensure research tools are included
            if "mcp_web_search" not in mcp_config.get("mcpServers", {}):
                mcp_config.setdefault("mcpServers", {})["mcp_web_search"] = {
                    "command": "npx",
                    "args": ["-y", "brave-search-mcp"],
                    "env": {"BRAVE_API_KEY": "BSAqv6fii19i_ZRARk67Gs5udOHgxSN"},
                }
        elif task.task_type == "monitoring":
            # Could add monitoring-specific tools here if needed
            pass

        # Update working directories and environment in config
        work_dir = config_path.parent
        for server_name, server_config in mcp_config.get("mcpServers", {}).items():
            # Update environment variables
            if "env" not in server_config:
                server_config["env"] = {}

            server_config["env"]["AGENT_TASK_ID"] = task.task_id
            server_config["env"]["AGENT_WORK_DIR"] = str(work_dir)
            server_config["env"]["AGENT_TASK_TYPE"] = task.task_type

        # Write to config file
        config_path.write_text(json.dumps(mcp_config, indent=2))

        logger.debug(f"Generated MCP config for {task.task_id}: {config_path}")

    async def execute_agent(self, task: AgentTask) -> Dict:
        """Execute a single agent task with dynamic architecture support"""

        session_id = str(uuid.uuid4())

        # Set up dynamic working directory if enabled
        agent_work_dir = self.output_dir
        if self.enable_dynamic_configs:
            # Use work_dir_name if task has it, otherwise use task_id
            dir_name = getattr(task, "work_dir_name", None) or task.task_id
            agent_work_dir = self.agent_base_work_dir / dir_name
            agent_work_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (agent_work_dir / "workspace").mkdir(exist_ok=True)
            (agent_work_dir / "logs").mkdir(exist_ok=True)
            (agent_work_dir / "data").mkdir(exist_ok=True)

            # Generate agent-specific MCP config
            agent_mcp_config = agent_work_dir / "mcp_config.json"
            self._generate_agent_mcp_config(task, agent_mcp_config)

            # Create symlinks to shared resources if needed
            shared_data = self.output_dir / "shared_data"
            if shared_data.exists():
                target = agent_work_dir / "shared"
                if not target.exists():
                    target.symlink_to(shared_data)

            # Create agent-specific .env file
            env_file = agent_work_dir / ".env"
            env_content = [
                f"AGENT_ID={task.task_id}",
                f"AGENT_TYPE={task.task_type}",
                f"WORKSPACE_ROOT={agent_work_dir}",
                f"OUTPUT_DIR={self.output_dir}",
            ]
            env_file.write_text("\n".join(env_content))

            logger.debug(f"Setup workspace for {task.task_id}: {agent_work_dir}")
        else:
            agent_work_dir = self.output_dir

        # Pre-execution hook
        if self.pre_execute_hook:
            await self.pre_execute_hook(task)

        # Build full prompt
        if self.task_builder_hook:
            prompt = await self.task_builder_hook(task)
        else:
            prompt = task.prompt

        # Prepare command with role-specific system prompt
        cmd = self.claude_cmd.copy()

        # Add debug flag if enabled (task-specific or global)
        if getattr(task, "debug_mode", False) or self.agent_debug_mode:
            cmd.append("--debug")

        # Use agent-specific MCP config if dynamic configs enabled
        if self.enable_dynamic_configs:
            agent_mcp_config = agent_work_dir / "mcp_config.json"
            if "--mcp-config" in cmd:
                idx = cmd.index("--mcp-config")
                cmd[idx + 1] = str(agent_mcp_config)
            else:
                cmd.extend(["--mcp-config", str(agent_mcp_config)])

        # Add system prompt based on task type for better specialization
        system_prompts = {
            "analysis": "You are a specialized analysis agent. Focus on thorough, data-driven analysis. Provide clear, structured summaries with key metrics.",
            "monitoring": "You are a system monitoring agent. Focus on performance metrics, resource usage, and system health indicators. Be concise and actionable.",
            "research": "You are a research specialist. Focus on comprehensive information gathering, accurate citations, and structured findings.",
            "strategic_research_lead": "You are a strategic research commander. Plan and coordinate research operations. Focus on leadership, strategy, and optimal orchestration patterns.",
        }

        if task.task_type in system_prompts:
            cmd.extend(["--append-system-prompt", system_prompts[task.task_type]])

        # Add session and workspace parameters
        cmd.extend(
            [
                "--session-id",
                session_id,
                "--add-dir",
                str(agent_work_dir if self.enable_dynamic_configs else self.output_dir),
                "--",  # Important: separator before prompt
                prompt,
            ]
        )

        # Get token
        token, token_idx = await self.token_pool.acquire()

        try:
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token

            # Add dynamic architecture environment variables
            if self.enable_dynamic_configs:
                env["AGENT_WORKSPACE"] = str(agent_work_dir)
                env["AGENT_MCP_CONFIG"] = str(agent_work_dir / "mcp_config.json")
                env["AGENT_TASK_ID"] = task.task_id
                env["AGENT_TASK_TYPE"] = task.task_type

                # Load .env file if exists
                env_file = agent_work_dir / ".env"
                if env_file.exists():
                    for line in env_file.read_text().splitlines():
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            env[key.strip()] = value.strip()

            # Execute
            task.start_time = datetime.now().timestamp()
            task.status = "running"
            await self.dep_manager.mark_running(task.task_id)

            try:
                logger.info(f"Executing {task.task_id} ({task.task_type})")

                # Set up log file if log_to_work_dir is enabled
                log_file_handle = None
                if self.log_to_work_dir and self.enable_dynamic_configs:
                    log_file = agent_work_dir / "logs" / f"agent_{task.task_id}.log"
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file_handle = open(log_file, "w")
                    stderr_target = log_file_handle
                else:
                    stderr_target = asyncio.subprocess.PIPE

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    cwd=str(agent_work_dir),  # Always provide working directory
                    stdout=asyncio.subprocess.PIPE,
                    stderr=stderr_target,
                )

                stdout, stderr = await process.communicate()

                # Close log file if used
                if log_file_handle:
                    log_file_handle.close()
                    # Read stderr from log file if process failed
                    if process.returncode != 0:
                        try:
                            with open(
                                agent_work_dir / "logs" / f"agent_{task.task_id}.log"
                            ) as f:
                                stderr_content = f.read()
                                stderr = (
                                    stderr_content.encode() if stderr_content else None
                                )
                        except Exception as e:
                            logger.warning(f"Failed to read stderr from log file: {e}")
                            stderr = None

                task.end_time = datetime.now().timestamp()
                duration = task.end_time - task.start_time

                if process.returncode == 0:
                    # Parse output with comprehensive error handling
                    if stdout:
                        try:
                            # Attempt JSON parsing
                            task.result = json.loads(stdout.decode())
                            task.status = "completed"
                            await self.dep_manager.mark_completed(task.task_id)
                            self.metrics["completed"] += 1
                            logger.info(
                                f"✓ {task.task_id} completed in {duration:.2f}s"
                            )
                        except json.JSONDecodeError as e:
                            # Capture JSON parsing error with context
                            stdout_str = stdout.decode()
                            error_msg = f"JSON decode error at line {e.lineno}, col {e.colno}: {e.msg}"
                            if len(stdout_str) > 500:
                                preview = stdout_str[:250] + "..." + stdout_str[-250:]
                            else:
                                preview = stdout_str

                            # Build comprehensive error message
                            error_parts = [
                                error_msg,
                                (
                                    f"Output preview: {preview[:200]}"
                                    if preview
                                    else "No output to preview"
                                ),
                                f"Task: {task.task_id}",
                            ]
                            task.error = " | ".join(error_parts)
                            task.status = "failed"
                            task.raw_output = stdout_str  # Preserve raw output
                            task.error_details = {
                                "type": "JSONDecodeError",
                                "message": error_msg,
                                "output_preview": preview,
                                "task_id": task.task_id,
                            }
                            await self.dep_manager.mark_failed(task.task_id)
                            self.metrics["failed"] += 1
                            logger.error(
                                f"✗ {task.task_id} JSON parsing failed: {error_msg}"
                            )
                    else:
                        # No stdout despite successful return code
                        task.status = "failed"
                        task.error = "Process returned success but produced no output"
                        await self.dep_manager.mark_failed(task.task_id)
                        self.metrics["failed"] += 1
                        logger.error(f"✗ {task.task_id} no output despite success code")
                else:
                    task.status = "failed"
                    # Build comprehensive error from available information
                    error_parts = []

                    # Process stderr
                    if stderr:
                        try:
                            stderr_str = stderr.decode().strip()
                            if stderr_str:
                                # Look for specific error patterns
                                if "Error:" in stderr_str:
                                    # Extract the main error message
                                    error_lines = [
                                        line
                                        for line in stderr_str.split("\n")
                                        if "Error:" in line
                                    ]
                                    if error_lines:
                                        error_parts.append(error_lines[0].strip())
                                    else:
                                        error_parts.append(
                                            f"Stderr: {stderr_str[:500]}"
                                        )
                                else:
                                    error_parts.append(f"Stderr: {stderr_str[:500]}")
                            else:
                                error_parts.append("Empty stderr output")
                        except Exception as e:
                            error_parts.append(f"Failed to decode stderr: {str(e)}")
                    else:
                        error_parts.append("No stderr captured")

                    # Process stdout for additional context
                    if stdout:
                        try:
                            stdout_str = stdout.decode().strip()
                            if stdout_str:
                                preview = (
                                    stdout_str[:200]
                                    if len(stdout_str) > 200
                                    else stdout_str
                                )
                                error_parts.append(f"Stdout preview: {preview}")
                            else:
                                error_parts.append("Empty stdout")
                        except Exception as e:
                            error_parts.append(f"Failed to decode stdout: {str(e)}")
                    else:
                        error_parts.append("No stdout captured")

                    # Always include exit code and task info
                    error_parts.append(f"Exit code: {process.returncode}")
                    error_parts.append(f"Task: {task.task_id} (type: {task.task_type})")

                    # Add command info for debugging
                    if hasattr(task, "prompt") and task.prompt:
                        prompt_preview = (
                            task.prompt[:100] if len(task.prompt) > 100 else task.prompt
                        )
                        error_parts.append(f"Prompt: {prompt_preview}")

                    # Ensure we always have an error message
                    if not error_parts or all(not part for part in error_parts):
                        error_parts = [
                            f"Process failed with exit code {process.returncode} but no diagnostic information was captured"
                        ]

                    task.error = " | ".join(
                        filter(None, error_parts)
                    )  # Filter out empty parts
                    task.raw_output = (
                        stdout.decode() if stdout else None
                    )  # Preserve for debugging

                    # Store detailed error information
                    task.error_details = {
                        "exit_code": process.returncode,
                        "stderr": stderr.decode() if stderr else None,
                        "stdout_preview": stdout.decode()[:500] if stdout else None,
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "timestamp": datetime.now().isoformat(),
                    }

                    await self.dep_manager.mark_failed(task.task_id)
                    self.metrics["failed"] += 1

                    logger.error(f"✗ {task.task_id} failed: {task.error}")

                self.metrics["total_duration"] += duration

            except Exception as e:
                task.status = "failed"

                # Build comprehensive error message
                error_parts = []

                # Get exception type and message
                error_type = type(e).__name__
                error_msg = str(e).strip()

                if error_msg:
                    error_parts.append(f"{error_type}: {error_msg}")
                else:
                    # Fallback for empty error messages - include repr for more info
                    error_repr = repr(e)
                    if error_repr and error_repr != "":
                        error_parts.append(f"{error_type}: {error_repr}")
                    else:
                        error_parts.append(
                            f"{error_type} occurred (no message available)"
                        )

                # Add traceback for debugging
                tb_lines = traceback.format_tb(e.__traceback__)
                if tb_lines:
                    # Get the most relevant traceback lines
                    relevant_tb = []
                    for line in tb_lines[-3:]:  # Last 3 traceback lines
                        line = line.strip()
                        if line and "File" in line:
                            relevant_tb.append(line)
                    if relevant_tb:
                        error_parts.append(
                            f"Traceback: {' -> '.join(relevant_tb[-2:])}"
                        )

                # Add context about the task
                error_parts.append(f"Task: {task.task_id} (type: {task.task_type})")

                # Add prompt info if available
                if hasattr(task, "prompt") and task.prompt:
                    prompt_preview = (
                        task.prompt[:100] if len(task.prompt) > 100 else task.prompt
                    )
                    error_parts.append(f"Prompt: {prompt_preview}")

                # Ensure we have a meaningful error
                if not error_parts:
                    error_parts.append("Unknown error occurred during task execution")

                # Combine error information
                task.error = " | ".join(filter(None, error_parts))

                # Store additional debugging info
                task.error_details = {
                    "type": error_type,
                    "message": error_msg or repr(e) or "No message",
                    "traceback": tb_lines,
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "prompt": (
                        task.prompt[:200]
                        if hasattr(task, "prompt") and task.prompt
                        else None
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

                await self.dep_manager.mark_failed(task.task_id)
                self.metrics["failed"] += 1

                logger.error(f"✗ {task.task_id} exception: {task.error}")

        finally:
            # Always release the token
            if hasattr(self.token_pool, "release"):
                self.token_pool.release(token_idx)

        # Post-execution hook
        if self.post_execute_hook:
            await self.post_execute_hook(task)

        # Save task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

        return task.to_dict()

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute a batch of tasks respecting dependencies and parallelism limits"""

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
                    # Mark them as failed
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

            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Task failed with exception - create failure result
                    failed_task = ready_tasks[i]

                    # Build comprehensive error information
                    error_type = type(result).__name__
                    error_msg = str(result).strip()

                    if error_msg:
                        error_text = f"{error_type}: {error_msg}"
                    else:
                        error_text = f"{error_type} occurred during task execution"

                    # Mark task as failed
                    failed_task.status = "failed"
                    failed_task.error = error_text
                    failed_task.error_details = {
                        "type": error_type,
                        "message": error_msg or "No message",
                        "task_id": failed_task.task_id,
                        "task_type": failed_task.task_type,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Mark in dependency manager
                    await self.dep_manager.mark_failed(failed_task.task_id)
                    self.metrics["failed"] += 1

                    # Save task state to file
                    task_file = (
                        self.output_dir / "tasks" / f"{failed_task.task_id}.json"
                    )
                    task_file.parent.mkdir(exist_ok=True)
                    task_file.write_text(json.dumps(failed_task.to_dict(), indent=2))

                    # Add failed task result to results
                    results.append(failed_task.to_dict())

                    logger.error(
                        f"Batch execution error for {failed_task.task_id}: {error_text}"
                    )
                else:
                    results.append(result)

            # Brief pause between batches
            await asyncio.sleep(0.5)

        self.metrics["end_time"] = datetime.now().isoformat()

        return results

    async def run(
        self,
        task_generator: Callable[[], List[AgentTask]],
        result_processor: Optional[Callable[[List[Dict]], None]] = None,
    ) -> Dict:
        """
        Main entry point - run orchestration with custom task generator.

        Args:
            task_generator: Function that returns list of AgentTask objects
            result_processor: Optional function to process results

        Returns:
            Execution metrics and results
        """

        logger.info("=" * 60)
        logger.info("Generic Agent Orchestrator")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Max parallel: {self.max_parallel}")
        logger.info(f"Token pool size: {self.token_pool.size()}")
        logger.info("=" * 60)

        # Generate tasks
        tasks = task_generator()
        logger.info(f"Generated {len(tasks)} tasks")

        # Execute tasks
        results = await self.execute_batch(tasks)

        # Process results if processor provided
        if result_processor:
            await result_processor(results)

        # Print summary
        logger.info("=" * 60)
        logger.info("EXECUTION COMPLETE")
        logger.info(f"Total: {self.metrics['total']}")
        logger.info(f"Completed: {self.metrics['completed']}")
        logger.info(f"Failed: {self.metrics['failed']}")

        if self.metrics["completed"] > 0:
            avg_time = self.metrics["total_duration"] / self.metrics["completed"]
            logger.info(f"Avg time: {avg_time:.2f}s")

        logger.info("=" * 60)

        return {"metrics": self.metrics, "results": results}


# Example usage for testing
async def example_usage():
    """Example showing how to use the generic orchestrator"""

    def generate_test_tasks() -> List[AgentTask]:
        """Generate some test tasks"""
        tasks = []

        # Create some tasks with dependencies
        tasks.append(
            AgentTask(
                task_id="research_1",
                task_type="research",
                prompt="Research Python async patterns",
                dependencies=[],
            )
        )

        tasks.append(
            AgentTask(
                task_id="design_1",
                task_type="design",
                prompt="Design a simple async system",
                dependencies=["research_1"],  # Depends on research
            )
        )

        tasks.append(
            AgentTask(
                task_id="implement_1",
                task_type="implement",
                prompt="Implement a hello world async function",
                dependencies=["design_1"],  # Depends on design
            )
        )

        return tasks

    async def process_results(results: List[Dict]):
        """Process the results"""
        print("\nResults Summary:")
        for r in results:
            print(f"  {r['task_id']}: {r['status']}")

    # Create and run orchestrator
    import tempfile

    orchestrator = GenericOrchestrator(
        output_dir=Path(tempfile.mkdtemp(prefix="orchestrator_test_")), max_parallel=3
    )

    await orchestrator.run(
        task_generator=generate_test_tasks, result_processor=process_results
    )


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
