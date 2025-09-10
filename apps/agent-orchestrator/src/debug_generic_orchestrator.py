#!/usr/bin/env python3
"""
Debug-Enhanced GenericOrchestrator

This is the GenericOrchestrator with comprehensive debug logging enabled.
It provides detailed visibility into every aspect of orchestrator behavior
including task execution, dependency resolution, token management, and performance metrics.
"""

import asyncio
import json
import os
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Import our enhanced components
try:
    from .debug_logger import DebugLogger, TimedOperation
    from .enhanced_token_pool import EnhancedTokenPool
    from .enhanced_dependency_manager import EnhancedDependencyManager
except ImportError:
    # Fallback for direct execution
    from debug_logger import DebugLogger, TimedOperation
    from enhanced_token_pool import EnhancedTokenPool
    from enhanced_dependency_manager import EnhancedDependencyManager


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
    quality_gates: List[str] = field(default_factory=list)
    raw_output: Optional[str] = None
    error_details: Optional[Dict] = None

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


class MessageBus:
    """Simple file-based message passing between agents with logging"""

    def __init__(self, message_dir: Path, debug_logger: DebugLogger = None):
        self.message_dir = message_dir
        self.message_dir.mkdir(parents=True, exist_ok=True)
        self.debug_logger = debug_logger
        
        if self.debug_logger:
            self.debug_logger.log_values("MessageBus.__init__",
                                        message_dir=str(message_dir))

    async def send(self, from_id: str, to_id: str, message: Dict):
        """Send message from one agent to another"""
        msg_file = self.message_dir / f"{to_id}_{datetime.now().timestamp()}.json"
        msg_data = {
            "from": from_id,
            "to": to_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        
        if self.debug_logger:
            self.debug_logger.log_values("MessageBus.send",
                                        from_id=from_id,
                                        to_id=to_id,
                                        message_size=len(str(message)),
                                        msg_file=str(msg_file))
        
        msg_file.write_text(json.dumps(msg_data, indent=2))

    async def receive(self, agent_id: str) -> List[Dict]:
        """Get all messages for an agent"""
        messages = []
        msg_files = list(self.message_dir.glob(f"{agent_id}_*.json"))
        
        if self.debug_logger:
            self.debug_logger.log_values("MessageBus.receive",
                                        agent_id=agent_id,
                                        message_files_found=len(msg_files))
        
        for msg_file in msg_files:
            try:
                messages.append(json.loads(msg_file.read_text()))
                msg_file.unlink()  # Delete after reading
            except Exception as e:
                if self.debug_logger:
                    self.debug_logger.error("Failed to read message file",
                                           msg_file=str(msg_file),
                                           error=str(e))
        
        sorted_messages = sorted(messages, key=lambda x: x["timestamp"])
        
        if self.debug_logger:
            self.debug_logger.log_values("MessageBus.receive.result",
                                        agent_id=agent_id,
                                        messages_received=len(sorted_messages))
        
        return sorted_messages


class DebugGenericOrchestrator:
    """
    GenericOrchestrator with comprehensive debug logging enabled.
    
    Provides detailed visibility into every aspect of orchestrator behavior:
    - Task lifecycle and state transitions
    - Token acquisition and release patterns  
    - Dependency resolution logic
    - Command construction and execution
    - Performance metrics and bottlenecks
    - Error analysis and debugging information
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        # New parameters for dynamic architecture
        master_mcp_registry_path: Optional[Path] = None,
        agent_execution_profile: str = "standard",
        agent_debug_mode: bool = False,
        agent_base_work_dir: Optional[Path] = None,
        enable_dynamic_configs: bool = False,
        log_to_work_dir: bool = False,
        # Debug logging parameters
        enable_debug_logging: bool = True,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup enhanced debug logging
        if enable_debug_logging:
            self.debug_logger = DebugLogger("GenericOrchestrator", output_dir)
        else:
            self.debug_logger = None

        # Log initialization parameters
        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator.__init__.params",
                output_dir=str(output_dir),
                max_parallel=max_parallel,
                tokens_provided=tokens is not None,
                token_count=len(tokens) if tokens else 0,
                use_optimizations=use_optimizations,
                master_mcp_registry_path=str(master_mcp_registry_path) if master_mcp_registry_path else None,
                agent_execution_profile=agent_execution_profile,
                agent_debug_mode=agent_debug_mode,
                agent_base_work_dir=str(agent_base_work_dir) if agent_base_work_dir else None,
                enable_dynamic_configs=enable_dynamic_configs,
                log_to_work_dir=log_to_work_dir,
                enable_debug_logging=enable_debug_logging
            )

        # Store all parameters
        self.use_optimizations = use_optimizations
        self.master_mcp_registry_path = master_mcp_registry_path
        self.agent_execution_profile = agent_execution_profile
        self.agent_debug_mode = agent_debug_mode
        self.agent_base_work_dir = agent_base_work_dir or output_dir / "agent_workspaces"
        self.enable_dynamic_configs = enable_dynamic_configs
        self.log_to_work_dir = log_to_work_dir

        # Create agent work directory if needed
        if self.enable_dynamic_configs:
            self.agent_base_work_dir.mkdir(parents=True, exist_ok=True)
            if self.debug_logger:
                self.debug_logger.debug("Created agent work directory",
                                       path=str(self.agent_base_work_dir))

        # Ensure subdirectories exist
        (self.output_dir / "tasks").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)

        # Handle None and invalid values
        self.max_parallel = max(1, max_parallel if max_parallel is not None else 10)

        # Initialize enhanced components with debug logging
        self.token_pool = EnhancedTokenPool(tokens, output_dir if enable_debug_logging else None)
        self.dep_manager = EnhancedDependencyManager(output_dir if enable_debug_logging else None)
        self.message_bus = MessageBus(output_dir / "messages", self.debug_logger)

        # Setup Claude command
        self.claude_cmd = ["claude", "-p"]

        # Configure MCP setup with logging
        if use_optimizations:
            self._setup_mcp_configuration()

        # Metrics with enhanced tracking
        self.metrics = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "total_duration": 0,
            "start_time": None,
            "end_time": None,
            "batch_rounds": 0,
            "total_token_acquisitions": 0,
            "total_dependency_checks": 0,
            "average_task_duration": 0,
            "peak_parallel_tasks": 0
        }

        # Hooks for customization
        self.pre_execute_hook: Optional[Callable] = None
        self.post_execute_hook: Optional[Callable] = None
        self.task_builder_hook: Optional[Callable] = None

        # Log final initialization state
        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator.__init__.complete",
                max_parallel=self.max_parallel,
                token_pool_size=self.token_pool.size(),
                available_tokens=self.token_pool.available,
                claude_cmd=self.claude_cmd,
                output_dir_structure=[str(p.relative_to(output_dir)) for p in output_dir.rglob("*") if p.is_file()][:10]
            )
            
            self.debug_logger.info("DebugGenericOrchestrator initialized successfully",
                                  token_pool_size=self.token_pool.size(),
                                  max_parallel=self.max_parallel)

    def _setup_mcp_configuration(self):
        """Setup MCP configuration with logging"""
        if self.debug_logger:
            with TimedOperation(self.debug_logger, "mcp_configuration_setup"):
                self._do_mcp_setup()
        else:
            self._do_mcp_setup()

    def _do_mcp_setup(self):
        """Actual MCP setup logic"""
        # NEW: Check for master registry first
        if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
            if self.debug_logger:
                self.debug_logger.debug("Loading MCP config from master registry",
                                       path=str(self.master_mcp_registry_path))
            
            # Load from master registry
            with open(self.master_mcp_registry_path) as f:
                mcp_config = json.load(f)

            # Filter based on execution profile
            if self.agent_execution_profile != "full":
                original_count = len(mcp_config.get("mcpServers", {}))
                mcp_config = self._filter_mcp_by_profile(mcp_config, self.agent_execution_profile)
                filtered_count = len(mcp_config.get("mcpServers", {}))
                
                if self.debug_logger:
                    self.debug_logger.debug("Filtered MCP config by profile",
                                           profile=self.agent_execution_profile,
                                           original_count=original_count,
                                           filtered_count=filtered_count)

            # Write filtered config
            research_config = Path(self.output_dir) / "research_mcp.json"
            research_config.write_text(json.dumps(mcp_config, indent=2))
            
            if self.debug_logger:
                self.debug_logger.debug("Wrote filtered MCP config",
                                       config_path=str(research_config),
                                       server_count=len(mcp_config.get("mcpServers", {})))
        else:
            # Use minimal research config
            if self.debug_logger:
                self.debug_logger.debug("Using minimal MCP research config")
            
            research_config = Path(self.output_dir) / "research_mcp.json"
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
                        "env": {"FIRECRAWL_API_KEY": "fc-a9cc6620c7b24c9c90bd010c73deb51f"},
                    },
                }
            }
            research_config.write_text(json.dumps(minimal_research_config, indent=2))

        self.claude_cmd.extend([
            "--model", "opus",
            "--mcp-config", str(research_config),
            "--dangerously-skip-permissions",
            "--allowedTools", "mcp__mcp_web_search__brave_web_search,mcp__research_papers__search_papers,mcp__firecrawl__firecrawl_search,WebSearch,Read,Write,Bash",
            "--output-format", "json",
        ])

    def _filter_mcp_by_profile(self, config: Dict, profile: str) -> Dict:
        """Filter MCP config based on execution profile with logging"""
        
        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator._filter_mcp_by_profile",
                profile=profile,
                original_server_count=len(config.get("mcpServers", {}))
            )

        profile_servers = {
            "minimal": ["shell_exec", "time"],
            "standard": ["shell_exec", "time", "mcp_web_search", "firecrawl", "research_papers"],
            "research": ["shell_exec", "time", "mcp_web_search", "firecrawl", "research_papers", "tech_docs", "knowledge"],
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
        
        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator._filter_mcp_by_profile.result",
                profile=profile,
                allowed_servers=allowed,
                filtered_server_count=len(filtered["mcpServers"])
            )

        return filtered

    def _generate_agent_mcp_config(self, task: AgentTask, config_path: Path):
        """Generate agent-specific MCP configuration with logging"""
        
        if self.debug_logger:
            with TimedOperation(self.debug_logger, f"generate_agent_mcp_config_{task.task_id}",
                               task_id=task.task_id, task_type=task.task_type):
                self._do_generate_agent_mcp_config(task, config_path)
        else:
            self._do_generate_agent_mcp_config(task, config_path)

    def _do_generate_agent_mcp_config(self, task: AgentTask, config_path: Path):
        """Actual MCP config generation logic"""
        
        # Start with base config
        if self.master_mcp_registry_path and self.master_mcp_registry_path.exists():
            with open(self.master_mcp_registry_path) as f:
                mcp_config = json.load(f)
            
            if self.debug_logger:
                self.debug_logger.debug("Loaded base MCP config from master registry",
                                       server_count=len(mcp_config.get("mcpServers", {})))
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
                        "env": {"FIRECRAWL_API_KEY": "fc-a9cc6620c7b24c9c90bd010c73deb51f"},
                    },
                }
            }
            
            if self.debug_logger:
                self.debug_logger.debug("Using minimal MCP config as base")

        # Check for task-specific MCP needs
        if hasattr(task, "mcp_needs") and task.mcp_needs:
            original_count = len(mcp_config.get("mcpServers", {}))
            filtered_servers = {}
            for server_name in task.mcp_needs:
                if server_name in mcp_config.get("mcpServers", {}):
                    filtered_servers[server_name] = mcp_config["mcpServers"][server_name]
            mcp_config["mcpServers"] = filtered_servers
            
            if self.debug_logger:
                self.debug_logger.debug("Applied task-specific MCP filtering",
                                       task_id=task.task_id,
                                       mcp_needs=task.mcp_needs,
                                       original_count=original_count,
                                       filtered_count=len(filtered_servers))
        elif self.agent_execution_profile != "full":
            # Apply profile filtering if no specific needs
            original_count = len(mcp_config.get("mcpServers", {}))
            mcp_config = self._filter_mcp_by_profile(mcp_config, self.agent_execution_profile)
            
            if self.debug_logger:
                self.debug_logger.debug("Applied profile-based MCP filtering",
                                       task_id=task.task_id,
                                       profile=self.agent_execution_profile,
                                       original_count=original_count,
                                       filtered_count=len(mcp_config.get("mcpServers", {})))

        # Task-specific customizations based on task type
        if task.task_type == "research":
            if "mcp_web_search" not in mcp_config.get("mcpServers", {}):
                mcp_config.setdefault("mcpServers", {})["mcp_web_search"] = {
                    "command": "npx",
                    "args": ["-y", "brave-search-mcp"],
                    "env": {"BRAVE_API_KEY": "BSAqv6fii19i_ZRARk67Gs5udOHgxSN"},
                }
                
                if self.debug_logger:
                    self.debug_logger.debug("Added research tools for research task",
                                           task_id=task.task_id)

        # Update working directories and environment in config
        work_dir = config_path.parent
        for server_name, server_config in mcp_config.get("mcpServers", {}).items():
            if "env" not in server_config:
                server_config["env"] = {}

            server_config["env"]["AGENT_TASK_ID"] = task.task_id
            server_config["env"]["AGENT_WORK_DIR"] = str(work_dir)
            server_config["env"]["AGENT_TASK_TYPE"] = task.task_type

        # Write to config file
        config_path.write_text(json.dumps(mcp_config, indent=2))

        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator._generate_agent_mcp_config.complete",
                task_id=task.task_id,
                config_path=str(config_path),
                final_server_count=len(mcp_config.get("mcpServers", {})),
                server_names=list(mcp_config.get("mcpServers", {}).keys())
            )

    async def execute_agent(self, task: AgentTask) -> Dict:
        """Execute a single agent task with comprehensive debug logging"""
        execution_start_time = time.time()
        session_id = str(uuid.uuid4())

        if self.debug_logger:
            # Log task execution start with full context
            self.debug_logger.log_values("GenericOrchestrator.execute_agent.start",
                task_id=task.task_id,
                task_type=task.task_type,
                session_id=session_id,
                dependencies=task.dependencies,
                context=task.context,
                prompt_length=len(task.prompt),
                prompt_preview=task.prompt[:200] + "..." if len(task.prompt) > 200 else task.prompt,
                quality_gates=task.quality_gates
            )

        # Set up dynamic working directory if enabled
        agent_work_dir = self.output_dir
        if self.enable_dynamic_configs:
            dir_name = getattr(task, "work_dir_name", None) or task.task_id
            agent_work_dir = self.agent_base_work_dir / dir_name
            agent_work_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (agent_work_dir / "workspace").mkdir(exist_ok=True)
            (agent_work_dir / "logs").mkdir(exist_ok=True)
            (agent_work_dir / "data").mkdir(exist_ok=True)

            if self.debug_logger:
                self.debug_logger.debug("Setup dynamic workspace",
                                       task_id=task.task_id,
                                       workspace_path=str(agent_work_dir))

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
            env_file.write_text("\\n".join(env_content))

        # Pre-execution hook
        if self.pre_execute_hook:
            if self.debug_logger:
                with TimedOperation(self.debug_logger, f"pre_execute_hook_{task.task_id}"):
                    await self.pre_execute_hook(task)
            else:
                await self.pre_execute_hook(task)

        # Build full prompt
        if self.task_builder_hook:
            if self.debug_logger:
                with TimedOperation(self.debug_logger, f"task_builder_hook_{task.task_id}"):
                    prompt = await self.task_builder_hook(task)
            else:
                prompt = await self.task_builder_hook(task)
        else:
            prompt = task.prompt

        # Prepare command with logging
        cmd = self.claude_cmd.copy()

        # Add debug flag if enabled
        if getattr(task, "debug_mode", False) or self.agent_debug_mode:
            cmd.append("--debug")
            if self.debug_logger:
                self.debug_logger.debug("Added debug flag to command", task_id=task.task_id)

        # Use agent-specific MCP config if dynamic configs enabled
        if self.enable_dynamic_configs:
            agent_mcp_config = agent_work_dir / "mcp_config.json"
            if "--mcp-config" in cmd:
                idx = cmd.index("--mcp-config")
                cmd[idx + 1] = str(agent_mcp_config)
            else:
                cmd.extend(["--mcp-config", str(agent_mcp_config)])

        # Add system prompt based on task type
        system_prompts = {
            "analysis": "You are a specialized analysis agent. Focus on thorough, data-driven analysis. Provide clear, structured summaries with key metrics.",
            "monitoring": "You are a system monitoring agent. Focus on performance metrics, resource usage, and system health indicators. Be concise and actionable.",
            "research": "You are a research specialist. Focus on comprehensive information gathering, accurate citations, and structured findings.",
            "strategic_research_lead": "You are a strategic research commander. Plan and coordinate research operations. Focus on leadership, strategy, and optimal orchestration patterns.",
        }

        if task.task_type in system_prompts:
            cmd.extend(["--append-system-prompt", system_prompts[task.task_type]])
            if self.debug_logger:
                self.debug_logger.debug("Added specialized system prompt",
                                       task_id=task.task_id,
                                       task_type=task.task_type)

        # Add session and workspace parameters
        cmd.extend([
            "--session-id", session_id,
            "--add-dir", str(agent_work_dir if self.enable_dynamic_configs else self.output_dir),
            "--", prompt,
        ])

        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator.execute_agent.command_built",
                task_id=task.task_id,
                full_command=cmd,
                command_length=len(cmd),
                working_directory=str(agent_work_dir),
                session_id=session_id
            )

        # Get token with logging
        if self.debug_logger:
            token_acquire_start = time.time()
            
        token, token_idx = await self.token_pool.acquire()
        self.metrics["total_token_acquisitions"] += 1
        
        if self.debug_logger:
            token_acquire_duration = time.time() - token_acquire_start
            self.debug_logger.log_values("GenericOrchestrator.execute_agent.token_acquired",
                task_id=task.task_id,
                token_idx=token_idx,
                token_preview=token[:8] + "..." if len(token) > 8 else token,
                acquisition_duration=token_acquire_duration,
                available_tokens_after=self.token_pool.available,
                total_acquisitions=self.metrics["total_token_acquisitions"]
            )

        try:
            # Setup environment
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token

            # Add dynamic architecture environment variables
            if self.enable_dynamic_configs:
                env.update({
                    "AGENT_WORKSPACE": str(agent_work_dir),
                    "AGENT_MCP_CONFIG": str(agent_work_dir / "mcp_config.json"),
                    "AGENT_TASK_ID": task.task_id,
                    "AGENT_TASK_TYPE": task.task_type,
                })

                # Load .env file if exists
                env_file = agent_work_dir / ".env"
                if env_file.exists():
                    for line in env_file.read_text().splitlines():
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            env[key.strip()] = value.strip()

            if self.debug_logger:
                self.debug_logger.log_values("GenericOrchestrator.execute_agent.environment_setup",
                    task_id=task.task_id,
                    environment_vars=list(env.keys()),
                    agent_specific_vars=[k for k in env.keys() if k.startswith("AGENT_")],
                    working_directory=str(agent_work_dir)
                )

            # Execute task
            task.start_time = datetime.now().timestamp()
            task.status = "running"
            await self.dep_manager.mark_running(task.task_id)

            if self.debug_logger:
                self.debug_logger.info(f"Starting task execution: {task.task_id}",
                                      task_type=task.task_type,
                                      session_id=session_id)

            try:
                # Set up log file if log_to_work_dir is enabled
                log_file_handle = None
                if self.log_to_work_dir and self.enable_dynamic_configs:
                    log_file = agent_work_dir / "logs" / f"agent_{task.task_id}.log"
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file_handle = open(log_file, "w")
                    stderr_target = log_file_handle
                    
                    if self.debug_logger:
                        self.debug_logger.debug("Redirecting stderr to work dir log file",
                                               task_id=task.task_id,
                                               log_file=str(log_file))
                else:
                    stderr_target = asyncio.subprocess.PIPE

                # Start process with logging
                if self.debug_logger:
                    process_start_time = time.time()
                    
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    cwd=str(agent_work_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=stderr_target,
                )

                if self.debug_logger:
                    process_start_duration = time.time() - process_start_time
                    self.debug_logger.log_values("GenericOrchestrator.execute_agent.process_started",
                        task_id=task.task_id,
                        process_pid=process.pid,
                        start_duration=process_start_duration
                    )

                # Wait for process completion with logging
                if self.debug_logger:
                    communicate_start_time = time.time()
                    
                stdout, stderr = await process.communicate()
                
                if self.debug_logger:
                    communicate_duration = time.time() - communicate_start_time
                    self.debug_logger.log_values("GenericOrchestrator.execute_agent.process_completed",
                        task_id=task.task_id,
                        return_code=process.returncode,
                        stdout_length=len(stdout) if stdout else 0,
                        stderr_length=len(stderr) if stderr else 0,
                        communicate_duration=communicate_duration,
                        stdout_preview=(stdout.decode()[:500] + "..." if len(stdout) > 500 else stdout.decode()) if stdout else None,
                        stderr_preview=(stderr.decode()[:500] + "..." if len(stderr) > 500 else stderr.decode()) if stderr else None
                    )

                # Close log file if used
                if log_file_handle:
                    log_file_handle.close()
                    if process.returncode != 0:
                        try:
                            with open(agent_work_dir / "logs" / f"agent_{task.task_id}.log") as f:
                                stderr_content = f.read()
                                stderr = stderr_content.encode() if stderr_content else None
                        except Exception as e:
                            if self.debug_logger:
                                self.debug_logger.warning("Failed to read stderr from log file",
                                                         task_id=task.task_id,
                                                         error=str(e))

                task.end_time = datetime.now().timestamp()
                duration = task.end_time - task.start_time

                if process.returncode == 0:
                    # Process successful output
                    if stdout:
                        try:
                            task.result = json.loads(stdout.decode())
                            task.status = "completed"
                            await self.dep_manager.mark_completed(task.task_id)
                            self.metrics["completed"] += 1
                            
                            if self.debug_logger:
                                self.debug_logger.log_values("GenericOrchestrator.execute_agent.success",
                                    task_id=task.task_id,
                                    duration=duration,
                                    result_type=type(task.result).__name__,
                                    result_keys=list(task.result.keys()) if isinstance(task.result, dict) else None,
                                    result_size=len(str(task.result))
                                )
                                
                                self.debug_logger.info(f"Task completed successfully: {task.task_id}",
                                                      duration=f"{duration:.2f}s",
                                                      result_size=len(str(task.result)))
                                
                        except json.JSONDecodeError as e:
                            # Handle JSON parsing error with detailed logging
                            stdout_str = stdout.decode()
                            error_msg = f"JSON decode error at line {e.lineno}, col {e.colno}: {e.msg}"
                            
                            task.error = error_msg
                            task.status = "failed"
                            task.raw_output = stdout_str
                            task.error_details = {
                                "type": "JSONDecodeError",
                                "message": error_msg,
                                "output_preview": stdout_str[:1000],
                                "task_id": task.task_id,
                            }
                            
                            await self.dep_manager.mark_failed(task.task_id, error_msg)
                            self.metrics["failed"] += 1
                            
                            if self.debug_logger:
                                self.debug_logger.log_values("GenericOrchestrator.execute_agent.json_parse_error",
                                    task_id=task.task_id,
                                    error_type="JSONDecodeError",
                                    error_message=error_msg,
                                    error_line=e.lineno,
                                    error_column=e.colno,
                                    stdout_length=len(stdout_str),
                                    stdout_preview=stdout_str[:1000]
                                )
                                
                                self.debug_logger.error(f"Task failed with JSON parse error: {task.task_id}",
                                                       error=error_msg,
                                                       duration=f"{duration:.2f}s")
                    else:
                        # No output despite success
                        error_msg = "Process returned success but produced no output"
                        task.status = "failed"
                        task.error = error_msg
                        await self.dep_manager.mark_failed(task.task_id, error_msg)
                        self.metrics["failed"] += 1
                        
                        if self.debug_logger:
                            self.debug_logger.log_values("GenericOrchestrator.execute_agent.no_output_error",
                                task_id=task.task_id,
                                return_code=process.returncode,
                                error_message=error_msg
                            )
                            
                            self.debug_logger.error(f"Task failed - no output: {task.task_id}",
                                                   duration=f"{duration:.2f}s")
                else:
                    # Process failed - comprehensive error logging
                    error_parts = self._build_comprehensive_error(process, stdout, stderr, task)
                    
                    task.status = "failed"
                    task.error = " | ".join(filter(None, error_parts))
                    task.raw_output = stdout.decode() if stdout else None
                    task.error_details = {
                        "exit_code": process.returncode,
                        "stderr": stderr.decode() if stderr else None,
                        "stdout_preview": stdout.decode()[:500] if stdout else None,
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    await self.dep_manager.mark_failed(task.task_id, task.error)
                    self.metrics["failed"] += 1
                    
                    if self.debug_logger:
                        self.debug_logger.log_values("GenericOrchestrator.execute_agent.process_failure",
                            task_id=task.task_id,
                            exit_code=process.returncode,
                            error_message=task.error,
                            stderr_length=len(stderr) if stderr else 0,
                            stdout_length=len(stdout) if stdout else 0,
                            duration=duration
                        )
                        
                        self.debug_logger.error(f"Task failed with exit code {process.returncode}: {task.task_id}",
                                               error=task.error[:200],
                                               duration=f"{duration:.2f}s")

                self.metrics["total_duration"] += duration
                
                # Update average task duration
                completed_tasks = self.metrics["completed"] + self.metrics["failed"]
                if completed_tasks > 0:
                    self.metrics["average_task_duration"] = self.metrics["total_duration"] / completed_tasks

            except Exception as e:
                # Handle execution exceptions with comprehensive logging
                task.status = "failed"
                error_info = self._build_exception_error(e, task)
                
                task.error = error_info["message"]
                task.error_details = error_info["details"]
                
                await self.dep_manager.mark_failed(task.task_id, task.error)
                self.metrics["failed"] += 1
                
                if self.debug_logger:
                    self.debug_logger.log_values("GenericOrchestrator.execute_agent.execution_exception",
                        task_id=task.task_id,
                        exception_type=type(e).__name__,
                        exception_message=str(e),
                        **error_info["details"]
                    )
                    
                    self.debug_logger.error(f"Task failed with exception: {task.task_id}",
                                           exception=f"{type(e).__name__}: {str(e)}")

        finally:
            # Always release the token with logging
            if self.debug_logger:
                token_release_start = time.time()
                
            self.token_pool.release(token_idx)
            
            if self.debug_logger:
                token_release_duration = time.time() - token_release_start
                self.debug_logger.log_values("GenericOrchestrator.execute_agent.token_released",
                    task_id=task.task_id,
                    token_idx=token_idx,
                    release_duration=token_release_duration,
                    available_tokens_after=self.token_pool.available
                )

        # Post-execution hook
        if self.post_execute_hook:
            if self.debug_logger:
                with TimedOperation(self.debug_logger, f"post_execute_hook_{task.task_id}"):
                    await self.post_execute_hook(task)
            else:
                await self.post_execute_hook(task)

        # Save task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

        # Log final execution summary
        total_execution_time = time.time() - execution_start_time
        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator.execute_agent.complete",
                task_id=task.task_id,
                final_status=task.status,
                total_execution_time=total_execution_time,
                task_duration=task.end_time - task.start_time if task.start_time and task.end_time else None,
                error=task.error,
                result_size=len(str(task.result)) if task.result else 0,
                token_idx=token_idx
            )
            
            self.debug_logger.log_performance("GenericOrchestrator.execute_agent", total_execution_time,
                task_id=task.task_id,
                task_type=task.task_type,
                status=task.status,
                token_idx=token_idx,
                result_size=len(str(task.result)) if task.result else 0
            )

        return task.to_dict()

    def _build_comprehensive_error(self, process, stdout, stderr, task) -> List[str]:
        """Build comprehensive error message from process failure"""
        error_parts = []

        # Process stderr
        if stderr:
            try:
                stderr_str = stderr.decode().strip()
                if stderr_str:
                    if "Error:" in stderr_str:
                        error_lines = [line for line in stderr_str.split("\\n") if "Error:" in line]
                        if error_lines:
                            error_parts.append(error_lines[0].strip())
                        else:
                            error_parts.append(f"Stderr: {stderr_str[:500]}")
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
                    preview = stdout_str[:200] if len(stdout_str) > 200 else stdout_str
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

        return error_parts

    def _build_exception_error(self, exception: Exception, task: AgentTask) -> Dict:
        """Build comprehensive error information from exception"""
        error_type = type(exception).__name__
        error_msg = str(exception).strip()

        error_parts = []
        if error_msg:
            error_parts.append(f"{error_type}: {error_msg}")
        else:
            error_parts.append(f"{error_type} occurred (no message available)")

        # Add traceback for debugging
        tb_lines = traceback.format_tb(exception.__traceback__)
        if tb_lines:
            relevant_tb = []
            for line in tb_lines[-3:]:  # Last 3 traceback lines
                line = line.strip()
                if line and "File" in line:
                    relevant_tb.append(line)
            if relevant_tb:
                error_parts.append(f"Traceback: {' -> '.join(relevant_tb[-2:])}")

        error_parts.append(f"Task: {task.task_id} (type: {task.task_type})")

        return {
            "message": " | ".join(filter(None, error_parts)),
            "details": {
                "type": error_type,
                "message": error_msg or repr(exception) or "No message",
                "traceback": tb_lines,
                "task_id": task.task_id,
                "task_type": task.task_type,
                "timestamp": datetime.now().isoformat(),
            }
        }

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute a batch of tasks with comprehensive logging"""
        batch_start_time = time.time()
        
        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator.execute_batch.start",
                total_tasks=len(tasks),
                max_parallel=self.max_parallel,
                task_ids=[t.task_id for t in tasks],
                task_types=[t.task_type for t in tasks],
                dependency_graph={t.task_id: t.dependencies for t in tasks}
            )
            
            self.debug_logger.info("Starting batch execution",
                                  total_tasks=len(tasks),
                                  max_parallel=self.max_parallel)

        self.metrics["total"] = len(tasks)
        self.metrics["start_time"] = datetime.now().isoformat()
        results = []

        batch_round = 0
        while len(results) < len(tasks):
            batch_round += 1
            round_start_time = time.time()
            self.metrics["batch_rounds"] = batch_round

            # Find tasks ready to run
            ready_tasks = []
            for task in tasks:
                if task.status == "pending":
                    self.metrics["total_dependency_checks"] += 1
                    if await self.dep_manager.can_run(task):
                        ready_tasks.append(task)
                        if len(ready_tasks) >= self.max_parallel:
                            break

            if self.debug_logger:
                self.debug_logger.log_values("GenericOrchestrator.execute_batch.round",
                    batch_round=batch_round,
                    ready_tasks=[t.task_id for t in ready_tasks],
                    ready_count=len(ready_tasks),
                    pending_tasks=[t.task_id for t in tasks if t.status == "pending"],
                    completed_tasks=[t.task_id for t in tasks if t.status == "completed"],
                    failed_tasks=[t.task_id for t in tasks if t.status == "failed"],
                    dependency_checks_this_round=len([t for t in tasks if t.status == "pending"])
                )

            if not ready_tasks:
                # Check for deadlock
                pending = [t for t in tasks if t.status == "pending"]
                if pending:
                    if self.debug_logger:
                        deadlock_analysis = self.dep_manager.detect_deadlocks()
                        self.debug_logger.log_values("GenericOrchestrator.execute_batch.deadlock",
                            pending_tasks=[t.task_id for t in pending],
                            pending_count=len(pending),
                            deadlock_analysis=deadlock_analysis
                        )
                        
                        self.debug_logger.warning("Potential deadlock detected - marking pending tasks as failed",
                                                 pending_count=len(pending))

                    # Mark them as failed
                    for task in pending:
                        task.status = "failed"
                        task.error = "Dependencies not met - potential deadlock"
                        await self.dep_manager.mark_failed(task.task_id, task.error)
                        results.append(task.to_dict())
                        self.metrics["failed"] += 1
                break

            # Track peak parallel usage
            current_parallel = len(ready_tasks)
            if current_parallel > self.metrics["peak_parallel_tasks"]:
                self.metrics["peak_parallel_tasks"] = current_parallel

            # Execute ready tasks in parallel
            if self.debug_logger:
                self.debug_logger.info(f"Executing batch round {batch_round}",
                                      tasks_count=len(ready_tasks),
                                      task_ids=[t.task_id for t in ready_tasks])

            batch_results = await asyncio.gather(
                *[self.execute_agent(task) for task in ready_tasks],
                return_exceptions=True,
            )

            # Process batch results with logging
            round_duration = time.time() - round_start_time
            successful = sum(1 for r in batch_results if not isinstance(r, Exception))
            failed = len(batch_results) - successful

            if self.debug_logger:
                self.debug_logger.log_values("GenericOrchestrator.execute_batch.round_complete",
                    batch_round=batch_round,
                    round_duration=round_duration,
                    successful_count=successful,
                    failed_count=failed,
                    results_summary=[{
                        "task_id": ready_tasks[i].task_id,
                        "success": not isinstance(r, Exception),
                        "status": r.get('status') if not isinstance(r, Exception) else "exception",
                        "error": str(r) if isinstance(r, Exception) else r.get('error')
                    } for i, r in enumerate(batch_results)]
                )

            # Process individual results
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Handle batch execution exception
                    failed_task = ready_tasks[i]
                    error_type = type(result).__name__
                    error_msg = str(result).strip()

                    failed_task.status = "failed"
                    failed_task.error = f"{error_type}: {error_msg}" if error_msg else f"{error_type} occurred"
                    failed_task.error_details = {
                        "type": error_type,
                        "message": error_msg or "No message",
                        "task_id": failed_task.task_id,
                        "task_type": failed_task.task_type,
                        "timestamp": datetime.now().isoformat(),
                    }

                    await self.dep_manager.mark_failed(failed_task.task_id, failed_task.error)
                    self.metrics["failed"] += 1

                    # Save failed task state
                    task_file = self.output_dir / "tasks" / f"{failed_task.task_id}.json"
                    task_file.parent.mkdir(exist_ok=True)
                    task_file.write_text(json.dumps(failed_task.to_dict(), indent=2))

                    results.append(failed_task.to_dict())

                    if self.debug_logger:
                        self.debug_logger.log_values("GenericOrchestrator.execute_batch.exception_handling",
                            task_id=failed_task.task_id,
                            exception_type=error_type,
                            exception_message=error_msg,
                            batch_round=batch_round
                        )
                        
                        self.debug_logger.error(f"Batch execution exception: {failed_task.task_id}",
                                               exception=f"{error_type}: {error_msg}")
                else:
                    results.append(result)

            # Brief pause between batches
            await asyncio.sleep(0.5)

        # Log final batch execution results
        total_batch_duration = time.time() - batch_start_time
        self.metrics["end_time"] = datetime.now().isoformat()
        
        final_metrics = {
            "total": len(tasks),
            "completed": self.metrics["completed"],
            "failed": self.metrics["failed"],
            "batch_duration": total_batch_duration,
            "batch_rounds": batch_round,
            "peak_parallel_tasks": self.metrics["peak_parallel_tasks"],
            "total_token_acquisitions": self.metrics["total_token_acquisitions"],
            "total_dependency_checks": self.metrics["total_dependency_checks"],
            "average_task_duration": self.metrics["average_task_duration"]
        }

        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator.execute_batch.complete",
                **final_metrics,
                task_status_summary={
                    t.task_id: {
                        "status": t.status,
                        "duration": (t.end_time - t.start_time) if t.start_time and t.end_time else None,
                        "error": t.error
                    } for t in tasks
                }
            )
            
            self.debug_logger.log_performance("GenericOrchestrator.execute_batch", total_batch_duration,
                total_tasks=len(tasks),
                completed_tasks=self.metrics["completed"],
                failed_tasks=self.metrics["failed"],
                batch_rounds=batch_round,
                peak_parallel=self.metrics["peak_parallel_tasks"]
            )
            
            self.debug_logger.info("Batch execution completed",
                                  **{k: v for k, v in final_metrics.items() if k != "task_status_summary"})

        return results

    async def run(
        self,
        task_generator: Callable[[], List[AgentTask]],
        result_processor: Optional[Callable[[List[Dict]], None]] = None,
    ) -> Dict:
        """Main entry point with comprehensive logging"""
        
        if self.debug_logger:
            with TimedOperation(self.debug_logger, "orchestrator_run"):
                return await self._do_run(task_generator, result_processor)
        else:
            return await self._do_run(task_generator, result_processor)

    async def _do_run(self, task_generator, result_processor) -> Dict:
        """Actual run implementation"""
        
        if self.debug_logger:
            self.debug_logger.info("Starting orchestrator run",
                                  output_dir=str(self.output_dir),
                                  max_parallel=self.max_parallel,
                                  token_pool_size=self.token_pool.size())

        # Generate tasks
        with TimedOperation(self.debug_logger, "task_generation") if self.debug_logger else None:
            tasks = task_generator()
            
        if self.debug_logger:
            self.debug_logger.log_values("GenericOrchestrator.run.tasks_generated",
                task_count=len(tasks),
                task_types=[t.task_type for t in tasks],
                task_ids=[t.task_id for t in tasks],
                dependency_count=sum(len(t.dependencies) for t in tasks)
            )
            
            self.debug_logger.info(f"Generated {len(tasks)} tasks for execution")

        # Execute tasks
        results = await self.execute_batch(tasks)

        # Process results if processor provided
        if result_processor:
            if self.debug_logger:
                with TimedOperation(self.debug_logger, "result_processing"):
                    await result_processor(results)
            else:
                await result_processor(results)

        # Generate comprehensive summary
        if self.debug_logger:
            self._log_final_summary()

        return {"metrics": self.metrics, "results": results}

    def _log_final_summary(self):
        """Log comprehensive final summary with all statistics"""
        
        if not self.debug_logger:
            return

        # Get component statistics
        token_stats = self.token_pool.get_stats()
        dependency_stats = self.dep_manager.get_stats()
        
        # Log comprehensive summary
        self.debug_logger.info("=== ORCHESTRATOR EXECUTION SUMMARY ===",
                              total_tasks=self.metrics["total"],
                              completed=self.metrics["completed"],
                              failed=self.metrics["failed"],
                              batch_rounds=self.metrics["batch_rounds"],
                              peak_parallel=self.metrics["peak_parallel_tasks"])

        self.debug_logger.log_values("GenericOrchestrator.final_summary",
            execution_metrics=self.metrics,
            token_pool_stats=token_stats,
            dependency_manager_stats=dependency_stats
        )

        # Log individual component summaries
        self.token_pool.log_summary()
        self.dep_manager.log_summary()

        if self.metrics["completed"] > 0:
            avg_time = self.metrics["total_duration"] / self.metrics["completed"]
            self.debug_logger.info("Performance summary",
                                  average_task_time=f"{avg_time:.2f}s",
                                  total_duration=f"{self.metrics['total_duration']:.2f}s",
                                  token_utilization=f"{token_stats.get('utilization_percentage', 0):.1f}%")


# Factory function for easy creation
def create_debug_orchestrator(output_dir: Path, **kwargs) -> DebugGenericOrchestrator:
    """Create a DebugGenericOrchestrator with sensible defaults"""
    # Set debug logging to True by default, but allow override
    defaults = {"enable_debug_logging": True}
    defaults.update(kwargs)
    return DebugGenericOrchestrator(
        output_dir=output_dir,
        **defaults
    )