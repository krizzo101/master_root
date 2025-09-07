#!/usr/bin/env python3
"""
Debug-Enhanced Generic Agent Orchestrator Framework
Complete implementation with comprehensive debug logging
"""

import asyncio
import inspect
import json
import logging
import os
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DebugLevel(Enum):
    """Debug verbosity levels"""

    OFF = 0  # No debug output
    BASIC = 1  # Basic flow and errors
    VERBOSE = 2  # Detailed variable values
    TRACE = 3  # Full execution trace including tokens


class OrchestratorDebugger:
    """Centralized debug logging for orchestrator"""

    def __init__(self, level: int = 1, log_file: Optional[Path] = None):
        self.level = level
        self.logger = logging.getLogger("orchestrator.debug")

        # Setup file handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s"
                )
            )
            self.logger.addHandler(handler)

        self.logger.setLevel(logging.DEBUG if level > 0 else logging.INFO)

    def log_entry(self, func_name: str, **kwargs):
        """Log function entry with parameters"""
        if self.level >= 2:
            params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self.logger.debug(f"ENTRY: {func_name}({params})")

    def log_exit(self, func_name: str, result=None):
        """Log function exit with result"""
        if self.level >= 2:
            self.logger.debug(f"EXIT: {func_name} -> {result}")

    def log_variable(self, name: str, value: Any, sensitive: bool = False):
        """Log variable value"""
        if self.level >= 2:
            if sensitive and self.level < 3:
                value = "***REDACTED***"
            self.logger.debug(f"VAR: {name} = {value}")

    def log_subprocess(self, cmd: List[str], env: Dict, cwd: str = None):
        """Log subprocess execution details"""
        if self.level >= 1:
            self.logger.debug(f"EXEC: {' '.join(cmd)}")
            if self.level >= 2:
                self.logger.debug(f"  CWD: {cwd or 'default'}")
            if self.level >= 3:
                # Log environment (mask sensitive values)
                safe_env = self._mask_sensitive_env(env)
                self.logger.debug(f"  ENV: {safe_env}")

    def log_token_flow(self, action: str, token_idx: int, task_id: str):
        """Log token acquisition/release"""
        if self.level >= 2:
            self.logger.debug(f"TOKEN: {action} token[{token_idx}] for {task_id}")

    def log_error(self, error: Exception, context: str = ""):
        """Log detailed error information"""
        self.logger.error(f"ERROR in {context}: {type(error).__name__}: {error}")
        if self.level >= 2:
            self.logger.error(f"TRACE:\n{traceback.format_exc()}")

    def log_dependency_resolution(self, task_id: str, deps: List[str], satisfied: bool):
        """Log dependency resolution details"""
        if self.level >= 2:
            self.logger.debug(
                f"DEPS: Task {task_id} deps={deps}, satisfied={satisfied}"
            )

    def log_mcp_config(self, config_path: str, profile: str):
        """Log MCP configuration details"""
        if self.level >= 2:
            self.logger.debug(f"MCP: Config={config_path}, Profile={profile}")

    def _mask_sensitive_env(self, env: Dict) -> Dict:
        """Mask sensitive environment variables"""
        sensitive_keys = ["TOKEN", "KEY", "PASSWORD", "SECRET", "API"]
        safe_env = {}
        for key, value in env.items():
            if any(s in key.upper() for s in sensitive_keys):
                safe_env[key] = "***REDACTED***"
            else:
                safe_env[key] = value
        return safe_env


def debug_trace(debugger: OrchestratorDebugger):
    """Decorator to add debug tracing to methods"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get function signature for logging
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Log entry (skip 'self' parameter)
            params = {k: v for k, v in bound.arguments.items() if k != "self"}
            debugger.log_entry(func.__name__, **params)

            try:
                result = await func(*args, **kwargs)
                debugger.log_exit(func.__name__, result)
                return result
            except Exception as e:
                debugger.log_error(e, func.__name__)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Log entry (skip 'self' parameter)
            params = {k: v for k, v in bound.arguments.items() if k != "self"}
            debugger.log_entry(func.__name__, **params)

            try:
                result = func(*args, **kwargs)
                debugger.log_exit(func.__name__, result)
                return result
            except Exception as e:
                debugger.log_error(e, func.__name__)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


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

    def to_dict(self) -> Dict:
        return asdict(self)


class TokenPool:
    """
    Manages Claude API tokens for parallel execution with debug logging
    """

    def __init__(
        self, tokens: List[str] = None, debugger: Optional[OrchestratorDebugger] = None
    ):
        self.debugger = debugger

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
                raise RuntimeError(
                    "CATASTROPHIC FAILURE: TokenLoader not available and no explicit tokens provided."
                )
            except Exception as e:
                raise RuntimeError(
                    f"CATASTROPHIC FAILURE: TokenLoader failed: {str(e)}."
                )

        # Ensure we have valid tokens
        if not self.tokens:
            raise RuntimeError("CATASTROPHIC FAILURE: No valid tokens available.")

        self.current_index = 0
        self.lock = asyncio.Lock()
        self.in_use = set()  # Track tokens in use

        logger.info(f"Token pool initialized with {len(self.tokens)} tokens")

    async def acquire(self) -> Tuple[str, int]:
        """Get next available token (round-robin)"""
        async with self.lock:
            token = self.tokens[self.current_index]
            token_idx = self.current_index
            self.current_index = (self.current_index + 1) % len(self.tokens)
            self.in_use.add(token_idx)

            if self.debugger:
                self.debugger.log_token_flow("ACQUIRED", token_idx, "unknown")

            logger.debug(
                f"Token acquired: index={token_idx}, in_use={len(self.in_use)}"
            )
            return token, token_idx

    def release(self, token_idx: int):
        """Release a token back to the pool"""
        if token_idx in self.in_use:
            self.in_use.discard(token_idx)

            if self.debugger:
                self.debugger.log_token_flow("RELEASED", token_idx, "unknown")

            logger.debug(
                f"Token released: index={token_idx}, in_use={len(self.in_use)}"
            )

    def size(self) -> int:
        return len(self.tokens)


class DependencyManager:
    """Manages task dependencies with debug logging"""

    def __init__(self, debugger: Optional[OrchestratorDebugger] = None):
        self.completed: set = set()
        self.running: set = set()
        self.failed: set = set()
        self.lock = asyncio.Lock()
        self.debugger = debugger

    async def can_run(self, task: AgentTask) -> bool:
        """Check if task dependencies are satisfied"""
        async with self.lock:
            # Can't run if already running or completed
            if task.task_id in self.running or task.task_id in self.completed:
                logger.debug(
                    f"Task {task.task_id} cannot run: already running or completed"
                )
                return False

            # Check all dependencies are completed
            for dep in task.dependencies:
                if dep not in self.completed:
                    logger.debug(f"Task {task.task_id} waiting for dependency: {dep}")
                    if self.debugger:
                        self.debugger.log_dependency_resolution(
                            task.task_id, task.dependencies, False
                        )
                    return False

            logger.debug(
                f"Task {task.task_id} ready to run: all dependencies satisfied"
            )
            if self.debugger:
                self.debugger.log_dependency_resolution(
                    task.task_id, task.dependencies, True
                )
            return True

    async def mark_running(self, task_id: str):
        async with self.lock:
            self.running.add(task_id)
            if self.debugger:
                self.debugger.log_variable(f"task_{task_id}_status", "running")

    async def mark_completed(self, task_id: str):
        async with self.lock:
            self.running.discard(task_id)
            self.completed.add(task_id)
            if self.debugger:
                self.debugger.log_variable(f"task_{task_id}_status", "completed")

    async def mark_failed(self, task_id: str):
        async with self.lock:
            self.running.discard(task_id)
            self.failed.add(task_id)
            if self.debugger:
                self.debugger.log_variable(f"task_{task_id}_status", "failed")


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
    Generic orchestrator for parallel Claude agent execution with comprehensive debug logging.
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
        # Debug parameters
        debug_level: int = 0,  # 0=off, 1=basic, 2=verbose, 3=trace
        debug_log_file: Optional[Path] = None,
    ):
        # Check for debug environment variables
        if "ORCHESTRATOR_DEBUG" in os.environ:
            debug_level = int(os.environ["ORCHESTRATOR_DEBUG"])
        if "ORCHESTRATOR_DEBUG_FILE" in os.environ:
            debug_log_file = Path(os.environ["ORCHESTRATOR_DEBUG_FILE"])
        if "AGENT_DEBUG" in os.environ:
            agent_debug_mode = os.environ["AGENT_DEBUG"].lower() in ("true", "1", "yes")

        # Setup debug logging first
        self.debug_level = debug_level
        self.agent_debug_mode = agent_debug_mode

        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Ensure subdirectories exist
        (self.output_dir / "tasks").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)

        # Initialize debugger
        debug_file = debug_log_file or (
            self.output_dir
            / "logs"
            / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        self.debugger = OrchestratorDebugger(debug_level, debug_file)

        # Initialize debug statistics
        self._init_debug_stats()

        # Log initialization
        self.debugger.log_entry(
            "__init__",
            output_dir=str(output_dir),
            max_parallel=max_parallel,
            use_optimizations=use_optimizations,
            debug_level=debug_level,
            agent_debug_mode=agent_debug_mode,
        )

        # Store new parameters
        self.master_mcp_registry_path = master_mcp_registry_path
        self.agent_execution_profile = agent_execution_profile
        self.agent_base_work_dir = (
            agent_base_work_dir or output_dir / "agent_workspaces"
        )
        self.enable_dynamic_configs = enable_dynamic_configs
        self.log_to_work_dir = log_to_work_dir

        # Create agent work directory if needed
        if self.enable_dynamic_configs:
            self.agent_base_work_dir.mkdir(parents=True, exist_ok=True)

        # Setup standard file logging (in addition to debug logging)
        if debug_level == 0:
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
            logger.debug(f"Standard logging initialized: {self.log_file}")
        else:
            self.debugger.logger.debug(f"Debug logging initialized: {debug_file}")

        # Handle None and invalid values
        self.max_parallel = max(1, max_parallel if max_parallel is not None else 10)
        self.debugger.log_variable("max_parallel", self.max_parallel)

        # Initialize TokenPool - will use TokenTool automatically if no explicit tokens
        self.debugger.log_variable("initializing_token_pool", True)
        self.token_pool = TokenPool(tokens, self.debugger)
        self.debugger.log_variable("token_pool_size", self.token_pool.size())

        self.dep_manager = DependencyManager(self.debugger)
        self.message_bus = MessageBus(output_dir / "messages")

        # Setup Claude command
        self.claude_cmd = ["claude", "-p"]
        self.debugger.log_variable("base_claude_cmd", self.claude_cmd)

        if use_optimizations:
            # Check for master registry first
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
                self.debugger.log_mcp_config(
                    str(research_config), self.agent_execution_profile
                )
            else:
                # Existing minimal research config
                research_config = Path(self.output_dir) / "research_mcp.json"

                # Only include essential research tools
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
                self.debugger.log_variable("mcp_config_created", str(research_config))

            self.claude_cmd.extend(
                [
                    "--model",
                    "opus",
                    "--mcp-config",
                    str(research_config),
                    "--dangerously-skip-permissions",
                    "--allowedTools",
                    "mcp__mcp_web_search__brave_web_search,mcp__research_papers__search_papers,mcp__firecrawl__firecrawl_search,WebSearch,Read,Write,Bash",
                    "--output-format",
                    "json",
                ]
            )
            self.debugger.log_variable("final_claude_cmd", self.claude_cmd)

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

    def _init_debug_stats(self):
        """Initialize debug statistics collection"""
        self.debug_stats = {
            "token_acquisitions": 0,
            "token_releases": 0,
            "subprocess_calls": 0,
            "errors": [],
            "task_durations": [],
            "memory_usage": [],
        }

    def _update_debug_stats(self, stat_type: str, value: Any = None):
        """Update debug statistics"""
        if self.debug_level == 0:
            return

        if stat_type == "token_acquire":
            self.debug_stats["token_acquisitions"] += 1
        elif stat_type == "token_release":
            self.debug_stats["token_releases"] += 1
        elif stat_type == "subprocess":
            self.debug_stats["subprocess_calls"] += 1
        elif stat_type == "error":
            self.debug_stats["errors"].append(
                {"timestamp": datetime.now().isoformat(), "error": str(value)}
            )
        elif stat_type == "duration":
            self.debug_stats["task_durations"].append(value)

    def get_debug_report(self) -> Dict:
        """Generate debug statistics report"""
        if self.debug_level == 0:
            return {"debug": "disabled"}

        return {
            "debug_level": self.debug_level,
            "statistics": self.debug_stats,
            "token_balance": self.debug_stats["token_acquisitions"]
            - self.debug_stats["token_releases"],
            "avg_duration": sum(self.debug_stats["task_durations"])
            / len(self.debug_stats["task_durations"])
            if self.debug_stats["task_durations"]
            else 0,
            "error_count": len(self.debug_stats["errors"]),
        }

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
        """Generate agent-specific MCP configuration."""
        self.debugger.log_entry(
            "_generate_agent_mcp_config",
            task_id=task.task_id,
            config_path=str(config_path),
        )

        if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
            with open(self.master_mcp_registry_path) as f:
                mcp_config = json.load(f)

            # Filter based on execution profile
            if self.agent_execution_profile != "full":
                mcp_config = self._filter_mcp_by_profile(
                    mcp_config, self.agent_execution_profile
                )
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

        config_path.write_text(json.dumps(mcp_config, indent=2))
        self.debugger.log_mcp_config(str(config_path), self.agent_execution_profile)

    async def execute_agent(self, task: AgentTask) -> Dict:
        """Execute a single agent task with comprehensive debug logging."""

        session_id = str(uuid.uuid4())

        # Debug: Log task execution start
        self.debugger.log_entry(
            "execute_agent",
            task_id=task.task_id,
            task_type=task.task_type,
            session_id=session_id,
        )

        # Debug: Log task details
        self.debugger.log_variable(
            "task.prompt",
            task.prompt[:100] + "..." if len(task.prompt) > 100 else task.prompt,
        )
        self.debugger.log_variable("task.dependencies", task.dependencies)
        self.debugger.log_variable("task.context", task.context)

        # Set up dynamic working directory if enabled
        if self.enable_dynamic_configs:
            agent_work_dir = self.agent_base_work_dir / task.task_id
            agent_work_dir.mkdir(parents=True, exist_ok=True)
            self.debugger.log_variable("agent_work_dir", str(agent_work_dir))

            # Generate agent-specific MCP config
            agent_mcp_config = agent_work_dir / "mcp_config.json"
            self._generate_agent_mcp_config(task, agent_mcp_config)
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

        # Build command with debug logging
        cmd = self.claude_cmd.copy()

        # Add debug flag if enabled for individual agents
        if self.agent_debug_mode:
            cmd.append("--debug")
            self.debugger.log_variable("agent_debug_mode", True)

            # Add verbose output if debug level is high
            if self.debug_level >= 2:
                cmd.append("--verbose")

            # Add trace mode for maximum verbosity
            if self.debug_level >= 3:
                cmd.append("--trace")
                cmd.extend(["--log-level", "TRACE"])

        # Debug: Log command construction
        self.debugger.log_variable("base_command", cmd)

        # Add system prompt based on task type
        system_prompts = {
            "analysis": "You are a specialized analysis agent.",
            "monitoring": "You are a system monitoring agent.",
            "research": "You are a research specialist.",
            "strategic_research_lead": "You are a strategic research commander.",
        }

        if task.task_type in system_prompts:
            cmd.extend(["--append-system-prompt", system_prompts[task.task_type]])

        # Add session and workspace parameters
        cmd.extend(
            [
                "--session-id",
                session_id,
                "--add-dir",
                str(self.output_dir),
                "--",  # Important: separator before prompt
                prompt,
            ]
        )

        self.debugger.log_variable("final_command", cmd)

        # Get token with debug logging
        token, token_idx = await self.token_pool.acquire()
        self.debugger.log_token_flow("ACQUIRED", token_idx, task.task_id)
        self._update_debug_stats("token_acquire")

        try:
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token

            # Debug: Log subprocess execution
            self.debugger.log_subprocess(
                cmd,
                env,
                cwd=str(agent_work_dir) if self.enable_dynamic_configs else None,
            )
            self._update_debug_stats("subprocess")

            # Execute
            task.start_time = datetime.now().timestamp()
            task.status = "running"
            await self.dep_manager.mark_running(task.task_id)

            self.debugger.log_variable("task.status", "running")

            try:
                logger.info(f"Executing {task.task_id} ({task.task_type})")

                # Set up log file if log_to_work_dir is enabled
                log_file_handle = None
                if self.log_to_work_dir and self.enable_dynamic_configs:
                    log_file = agent_work_dir / "agent.log"
                    log_file_handle = open(log_file, "w")
                    stderr_target = log_file_handle
                else:
                    stderr_target = asyncio.subprocess.PIPE

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    cwd=str(agent_work_dir) if self.enable_dynamic_configs else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=stderr_target,
                )

                # Debug: Log process ID
                self.debugger.log_variable("process.pid", process.pid)

                stdout, stderr = await process.communicate()

                # Close log file if used
                if log_file_handle:
                    log_file_handle.close()
                    # Read stderr from log file
                    if process.returncode != 0:
                        with open(agent_work_dir / "agent.log") as f:
                            stderr = f.read().encode()

                task.end_time = datetime.now().timestamp()
                duration = task.end_time - task.start_time

                # Debug: Log execution results
                self.debugger.log_variable("returncode", process.returncode)
                self.debugger.log_variable("duration", f"{duration:.2f}s")
                self._update_debug_stats("duration", duration)

                if process.returncode == 0:
                    task.status = "completed"
                    task.result = json.loads(stdout.decode())
                    await self.dep_manager.mark_completed(task.task_id)
                    self.metrics["completed"] += 1

                    # Debug: Log success
                    self.debugger.log_variable("task.status", "completed")
                    if self.debug_level >= 3:
                        self.debugger.log_variable("stdout_length", len(stdout))
                        self.debugger.log_variable(
                            "result_keys",
                            list(task.result.keys())
                            if isinstance(task.result, dict)
                            else "non-dict",
                        )

                    logger.info(f"✓ {task.task_id} completed in {duration:.2f}s")
                else:
                    task.status = "failed"
                    task.error = (
                        stderr.decode()
                        if stderr
                        else "Process failed with no stderr output"
                    )
                    await self.dep_manager.mark_failed(task.task_id)
                    self.metrics["failed"] += 1

                    # Debug: Log failure details
                    self.debugger.log_variable("task.status", "failed")
                    self.debugger.log_variable(
                        "stderr",
                        task.error[:500] if len(task.error) > 500 else task.error,
                    )
                    self._update_debug_stats("error", task.error)

                    logger.error(f"✗ {task.task_id} failed: {task.error}")

                self.metrics["total_duration"] += duration

            except Exception as e:
                # Debug: Log exception
                self.debugger.log_error(e, f"execute_agent({task.task_id})")
                self._update_debug_stats("error", str(e))

                task.status = "failed"
                task.error = str(e)
                await self.dep_manager.mark_failed(task.task_id)
                self.metrics["failed"] += 1

                logger.error(f"✗ {task.task_id} exception: {e}")

        finally:
            # Always release token with debug logging
            if hasattr(self.token_pool, "release"):
                self.token_pool.release(token_idx)
                self.debugger.log_token_flow("RELEASED", token_idx, task.task_id)
                self._update_debug_stats("token_release")

        # Post-execution hook
        if self.post_execute_hook:
            await self.post_execute_hook(task)

        # Save task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

        # Debug: Log task completion
        self.debugger.log_exit(
            "execute_agent",
            {
                "status": task.status,
                "duration": duration if "duration" in locals() else None,
            },
        )

        return task.to_dict()

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute a batch of tasks respecting dependencies and parallelism limits"""

        self.debugger.log_entry("execute_batch", task_count=len(tasks))

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

            self.debugger.log_variable("ready_tasks", [t.task_id for t in ready_tasks])

            if not ready_tasks:
                # Check if we're stuck
                pending = [t for t in tasks if t.status == "pending"]
                if pending:
                    logger.warning(f"Possible deadlock: {len(pending)} tasks pending")
                    self.debugger.log_variable(
                        "deadlock_tasks", [t.task_id for t in pending]
                    )
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

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch execution error: {result}")
                    self.debugger.log_error(result, "batch_execution")
                else:
                    results.append(result)

            # Brief pause between batches
            await asyncio.sleep(0.5)

        self.metrics["end_time"] = datetime.now().isoformat()

        self.debugger.log_exit("execute_batch", {"result_count": len(results)})

        return results

    async def run(
        self,
        task_generator: Callable[[], List[AgentTask]],
        result_processor: Optional[Callable[[List[Dict]], None]] = None,
    ) -> Dict:
        """
        Main entry point - run orchestration with custom task generator.
        """

        self.debugger.log_entry("run")

        logger.info("=" * 60)
        logger.info("Generic Agent Orchestrator")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Max parallel: {self.max_parallel}")
        logger.info(f"Token pool size: {self.token_pool.size()}")
        logger.info(f"Debug level: {self.debug_level}")
        logger.info("=" * 60)

        # Generate tasks
        tasks = task_generator()
        logger.info(f"Generated {len(tasks)} tasks")
        self.debugger.log_variable("generated_tasks", [t.task_id for t in tasks])

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

        # Add debug report to results
        debug_report = self.get_debug_report()
        logger.info(f"Debug Report: {json.dumps(debug_report, indent=2)}")

        logger.info("=" * 60)

        self.debugger.log_exit("run", {"metrics": self.metrics})

        return {"metrics": self.metrics, "results": results, "debug": debug_report}


# Example usage for testing debug features
async def example_debug_usage():
    """Example showing how to use the debug-enhanced orchestrator"""

    import tempfile

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

    # Create and run orchestrator with debug logging
    orchestrator = GenericOrchestrator(
        output_dir=Path(tempfile.mkdtemp(prefix="orchestrator_debug_test_")),
        max_parallel=3,
        debug_level=2,  # Verbose debug logging
        agent_debug_mode=True,  # Enable agent debug flags
    )

    result = await orchestrator.run(
        task_generator=generate_test_tasks, result_processor=process_results
    )

    # Print debug report
    print("\n=== DEBUG REPORT ===")
    print(json.dumps(result["debug"], indent=2))


if __name__ == "__main__":
    # Run example with debug logging
    asyncio.run(example_debug_usage())
