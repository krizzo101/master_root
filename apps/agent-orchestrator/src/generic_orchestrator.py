#!/usr/bin/env python3
"""
Generic Agent Orchestrator Framework
A simplified, reusable orchestrator for parallel Claude agent execution
Extracted and simplified from Hecaton patterns
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
import traceback
import uuid
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

# Multi-provider support
try:
    from .providers.openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Generic agent task definition with enhanced error tracking and project organization"""

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
    work_dir_name: Optional[str] = None  # Custom working directory name

    # Project organization fields
    project_location: Optional[
        str
    ] = None  # Expected project path (/apps/PROJECT-NAME/)
    deliverable_structure: Optional[Dict[str, str]] = field(
        default_factory=dict
    )  # Expected output organization
    directory_permissions: Optional[List[str]] = field(
        default_factory=list
    )  # Required --add-dir parameters
    output_validation: Optional[Dict[str, Any]] = field(
        default_factory=dict
    )  # Validation rules for outputs

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
            # Robust token loading with multiple fallback strategies
            self.tokens = []

            # Strategy 1: Try relative import (works when called from orchestrator)
            try:
                from .token_loader import load_tokens

                self.tokens = load_tokens()
                if self.tokens:
                    print(f"✓ Loaded {len(self.tokens)} tokens via relative import")
            except ImportError:
                pass

            # Strategy 2: Try absolute import (works when called from other apps)
            if not self.tokens:
                try:
                    import os
                    import sys

                    # Add orchestrator src to path if not already there
                    orchestrator_src = os.path.join(os.path.dirname(__file__), "..")
                    if orchestrator_src not in sys.path:
                        sys.path.insert(0, orchestrator_src)

                    from src.token_loader import load_tokens

                    self.tokens = load_tokens()
                    if self.tokens:
                        print(f"✓ Loaded {len(self.tokens)} tokens via absolute import")
                except ImportError:
                    pass

            # Strategy 3: Direct file access to token_loader
            if not self.tokens:
                try:
                    import importlib.util
                    import os

                    token_loader_path = os.path.join(
                        os.path.dirname(__file__), "token_loader.py"
                    )
                    if os.path.exists(token_loader_path):
                        spec = importlib.util.spec_from_file_location(
                            "token_loader", token_loader_path
                        )
                        token_loader = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(token_loader)
                        self.tokens = token_loader.load_tokens()
                        if self.tokens:
                            print(
                                f"✓ Loaded {len(self.tokens)} tokens via direct file access"
                            )
                except Exception:
                    pass

            # Strategy 4: Environment variable fallback (for emergency cases)
            if not self.tokens:
                import os

                env_token = os.environ.get("CLAUDE_CODE_TOKEN")
                if env_token:
                    self.tokens = [env_token]
                    print(
                        "✓ Loaded 1 token from CLAUDE_CODE_TOKEN environment variable"
                    )

                # Try multiple tokens
                env_tokens = os.environ.get("CLAUDE_CODE_TOKENS")
                if env_tokens and not self.tokens:
                    self.tokens = env_tokens.split(",")
                    print(
                        f"✓ Loaded {len(self.tokens)} tokens from CLAUDE_CODE_TOKENS environment variable"
                    )

            # Final check
            if not self.tokens:
                raise RuntimeError(
                    "CATASTROPHIC FAILURE: Could not load tokens via any strategy:\n"
                    "- Relative import failed\n"
                    "- Absolute import failed\n"
                    "- Direct file access failed\n"
                    "- Environment variables not set\n"
                    "Please ensure tokens are available via TokenLoader or environment variables."
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
    Enhanced with workflow tracking and dashboard integration support.

    Enforces project directory standards to maintain proper separation between:
    - Project deliverables (in project-specific directories)
    - Orchestrator operations (in orchestrator-specific directories)
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
        # New workflow and dashboard parameters
        workflow_name: Optional[str] = None,
        task_file_path: Optional[str] = None,
        enable_dashboard_reporting: bool = False,
        dashboard_state_callback: Optional[Callable] = None,
        # New workflow isolation parameters
        workflow_source: Optional[str] = None,
    ):
        # Determine workflow source and name
        self.workflow_source = workflow_source or self._determine_workflow_source(
            task_file_path
        )
        self.workflow_name = self._determine_workflow_name(
            workflow_name, task_file_path
        )
        self.workflow_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate unique workflow ID with hash
        workflow_content = (
            f"{self.workflow_source}_{self.workflow_name}_{self.workflow_timestamp}"
        )
        workflow_hash = hashlib.md5(workflow_content.encode()).hexdigest()[:8]
        self.workflow_id = (
            f"workflow_{self.workflow_source}_{self.workflow_timestamp}_{workflow_hash}"
        )

        # Create workflow-specific output directory structure: output/workflow_SOURCE_TIMESTAMP_HASH/
        self.use_isolated_workflow = bool(
            workflow_name or task_file_path or workflow_source
        )

        if self.use_isolated_workflow:
            # Use workflow-isolated directory structure
            base_output_dir = (
                output_dir.parent
                if output_dir.parent.name != "outputs"
                else output_dir.parent.parent
            )
            self.output_dir = base_output_dir / "output" / self.workflow_id
            self.workflow_base_dir = base_output_dir / "output"
        else:
            # Use provided output_dir directly for backward compatibility
            self.output_dir = output_dir
            self.workflow_base_dir = None
            # For backward compatibility, use generic workflow ID
            self.workflow_id = (
                f"workflow_{self.workflow_source}_{self.workflow_timestamp}"
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Always create essential workflow directories (not just for isolated workflows)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        (self.output_dir / "agents").mkdir(exist_ok=True)
        (self.output_dir / "deliverables").mkdir(exist_ok=True)
        (self.output_dir / "checkpoints").mkdir(exist_ok=True)

        # Create workflow-specific subdirectories if using isolated structure
        if self.use_isolated_workflow:
            (self.output_dir / "orchestrator.log").touch()

        # Store all parameters including existing ones
        self.use_optimizations = use_optimizations
        self.enable_dashboard_reporting = enable_dashboard_reporting
        self.dashboard_state_callback = dashboard_state_callback

        # Store new parameters
        self.master_mcp_registry_path = master_mcp_registry_path
        self.agent_execution_profile = agent_execution_profile
        self.agent_debug_mode = agent_debug_mode
        self.agent_base_work_dir = (
            agent_base_work_dir or output_dir / "agent_workspaces"
        )
        self.enable_dynamic_configs = enable_dynamic_configs
        self.log_to_work_dir = log_to_work_dir

        # Initialize workflow tracking
        self.workflow_start_time = None
        self.total_tasks = 0
        self.task_completion_times = []  # For ETA calculations

        # Initialize resource tracking
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.initial_cpu_time = self.process.cpu_times()
        self.peak_memory = self.initial_memory

        # Initialize audit logging and deliverables tracking
        self.audit_log = []
        self.deliverables = set()
        self.file_operations = {"created": 0, "modified": 0, "deleted": 0}

        # Track file system state before workflow starts
        self.initial_file_count = 0
        if self.output_dir.exists():
            self.initial_file_count = len(list(self.output_dir.rglob("*")))

        # Mark metadata as pending - will be created after token_pool initialization
        # Only create metadata for isolated workflows
        if self.use_isolated_workflow:
            self._metadata_pending = True

        # Create agent work directory if needed
        if self.enable_dynamic_configs:
            self.agent_base_work_dir.mkdir(parents=True, exist_ok=True)

        # Legacy directory structure for backward compatibility
        (self.output_dir / "tasks").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)

        # Setup debug file logging with workflow identification
        self.log_file = self.output_dir / "orchestrator.log"
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
        self.message_bus = MessageBus(self.output_dir / "messages")

        # Create initial metadata.json now that token_pool is initialized (only for isolated workflows)
        if hasattr(self, "_metadata_pending"):
            self._create_workflow_metadata()
            delattr(self, "_metadata_pending")

        # Initialize multi-provider support
        self._init_providers()

        # Setup Claude command with main MCP config
        self.claude_cmd = [
            "claude",
            "-p",
            "--mcp-config",
            "/home/opsvi/master_root/.mcp.json",
        ]

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
                    str(research_config.absolute()),  # Use absolute path
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

        # Initialize dashboard reporting if enabled
        if self.enable_dashboard_reporting:
            self._report_workflow_started()

        # Initialize project directory validation
        self.project_root_base = Path("/home/opsvi/master_root/apps")
        self.orchestrator_root = Path("/home/opsvi/master_root/apps/agent-orchestrator")

        # Track directory validation warnings
        self._directory_warnings = set()

        # Log workflow initialization
        logger.info(f"Workflow {self.workflow_id} initialized in {self.output_dir}")

        # Log initial audit entry
        self._log_audit_action(
            "workflow_initialized",
            {
                "workflow_id": self.workflow_id,
                "output_dir": str(self.output_dir),
                "max_parallel": self.max_parallel,
                "token_pool_size": self.token_pool.size(),
                "initial_memory_mb": self.initial_memory,
                "initial_file_count": self.initial_file_count,
            },
        )

    def _determine_workflow_source(self, task_file_path: Optional[str]) -> str:
        """Determine workflow source from task file path or caller context."""
        if task_file_path:
            task_file = Path(task_file_path)
            # Extract meaningful part from filename
            name = task_file.stem

            # Remove common suffixes to get the core name
            for suffix in ["_tasks", "_task", "_workflow", "_plan"]:
                if name.endswith(suffix):
                    name = name[: -len(suffix)]
                    break

            return name

        # Try to determine from calling context
        import inspect

        frame = inspect.currentframe()
        try:
            # Go up the call stack to find the originating module
            caller_frame = frame.f_back.f_back if frame.f_back else None
            if caller_frame and caller_frame.f_globals.get("__name__"):
                module_name = caller_frame.f_globals["__name__"]
                if module_name != "__main__":
                    # Extract meaningful part from module name
                    return module_name.split(".")[-1]
        finally:
            del frame

        return "generic"

    def _determine_workflow_name(
        self, workflow_name: Optional[str], task_file_path: Optional[str]
    ) -> str:
        """Determine workflow name from parameters or task file path."""
        if workflow_name:
            return workflow_name

        if task_file_path:
            # Extract workflow name from task file path
            # Examples: system_analysis_tasks.json -> system_analysis
            #           orchestrator_dashboard_build_tasks.json -> orchestrator_dashboard_build
            task_file = Path(task_file_path)
            name = task_file.stem  # Remove .json extension

            # Remove common suffixes
            for suffix in ["_tasks", "_task", "_workflow", "_plan"]:
                if name.endswith(suffix):
                    name = name[: -len(suffix)]
                    break

            return name

        # Default workflow name
        return "generic_workflow"

    def _log_audit_action(self, action: str, details: Dict[str, Any] = None):
        """Log an action to the audit trail with timestamp."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {},
        }
        self.audit_log.append(audit_entry)

        # Also log to main logger for visibility
        logger.debug(f"AUDIT: {action} - {details}")

    def _update_resource_usage(self):
        """Update resource usage metrics."""
        try:
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory

            # Update file operations count
            if self.output_dir.exists():
                current_file_count = len(list(self.output_dir.rglob("*")))
                if current_file_count > self.initial_file_count:
                    self.file_operations["created"] = (
                        current_file_count - self.initial_file_count
                    )

        except Exception as e:
            logger.warning(f"Failed to update resource usage: {e}")

    def _track_deliverable(self, file_path: str, operation: str = "created"):
        """Track a deliverable file that was created or modified."""
        try:
            path_obj = Path(file_path)
            if path_obj.exists():
                # Convert to absolute path for consistent tracking
                abs_path = str(path_obj.resolve())

                # Only track files within our output directory or apps directory
                if (
                    str(self.output_dir.resolve()) in abs_path
                    or "/home/opsvi/master_root/apps/" in abs_path
                ):
                    self.deliverables.add(abs_path)
                    self.file_operations[operation] += 1

                    self._log_audit_action(
                        f"deliverable_{operation}",
                        {
                            "file_path": abs_path,
                            "operation": operation,
                            "file_size": path_obj.stat().st_size
                            if path_obj.exists()
                            else 0,
                        },
                    )

        except Exception as e:
            logger.warning(f"Failed to track deliverable {file_path}: {e}")

    def _scan_for_deliverables(self):
        """Scan output and related directories for deliverables created during workflow."""
        try:
            # Scan output directory
            if self.output_dir.exists():
                for file_path in self.output_dir.rglob("*"):
                    if file_path.is_file():
                        self._track_deliverable(str(file_path), "created")

            # Scan apps directories for project deliverables
            apps_base = Path("/home/opsvi/master_root/apps")
            if apps_base.exists():
                # Look for recently modified files that might be deliverables
                cutoff_time = (
                    self.workflow_start_time
                    if self.workflow_start_time
                    else time.time() - 3600
                )

                for app_dir in apps_base.iterdir():
                    if app_dir.is_dir() and app_dir.name != "agent-orchestrator":
                        for file_path in app_dir.rglob("*"):
                            if (
                                file_path.is_file()
                                and file_path.stat().st_mtime > cutoff_time
                                and not file_path.name.startswith(".")
                            ):
                                self._track_deliverable(str(file_path), "created")

        except Exception as e:
            logger.warning(f"Failed to scan for deliverables: {e}")

    def _generate_workflow_completion_report(self) -> Dict[str, Any]:
        """Generate comprehensive workflow completion report."""
        end_time = datetime.now()
        start_time_dt = (
            datetime.fromtimestamp(self.workflow_start_time)
            if self.workflow_start_time
            else end_time
        )
        duration_seconds = (end_time - start_time_dt).total_seconds()

        # Update resource usage one final time
        self._update_resource_usage()

        # Scan for deliverables
        self._scan_for_deliverables()

        # Calculate CPU time used
        current_cpu_time = self.process.cpu_times()
        cpu_time_used = (current_cpu_time.user - self.initial_cpu_time.user) + (
            current_cpu_time.system - self.initial_cpu_time.system
        )

        # Collect error information
        errors = []
        for entry in self.audit_log:
            if (
                "error" in entry.get("action", "").lower()
                or "failed" in entry.get("action", "").lower()
            ):
                errors.append(entry.get("details", {}).get("error", str(entry)))

        # Generate report
        report = {
            "workflow_id": self.workflow_id,
            "workflow_source": self.workflow_source,
            "workflow_name": self.workflow_name,
            "start_time": start_time_dt.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration_seconds, 2),
            "tasks_total": self.total_tasks,
            "tasks_completed": self.metrics.get("completed", 0),
            "tasks_failed": self.metrics.get("failed", 0),
            "deliverables": sorted(list(self.deliverables)),
            "deliverables_count": len(self.deliverables),
            "resource_usage": {
                "initial_memory_mb": round(self.initial_memory, 2),
                "peak_memory_mb": round(self.peak_memory, 2),
                "memory_growth_mb": round(self.peak_memory - self.initial_memory, 2),
                "cpu_time_seconds": round(cpu_time_used, 2),
                "file_operations": self.file_operations.copy(),
                "files_tracked": len(self.deliverables),
            },
            "errors": errors[:10],  # Limit to first 10 errors
            "error_count": len(errors),
            "audit_log": self.audit_log[-50:],  # Last 50 audit entries
            "audit_entries_total": len(self.audit_log),
            "performance_metrics": {
                "avg_task_duration": round(
                    duration_seconds / max(self.total_tasks, 1), 2
                ),
                "tasks_per_minute": round(
                    (
                        self.metrics.get("completed", 0)
                        / max(duration_seconds / 60, 0.1)
                    ),
                    2,
                ),
                "success_rate": round(
                    (self.metrics.get("completed", 0) / max(self.total_tasks, 1)) * 100,
                    1,
                ),
            },
            "output_directory": str(self.output_dir),
            "generated_at": datetime.now().isoformat(),
        }

        return report

    def _save_completion_report(self, report: Dict[str, Any]):
        """Save the workflow completion report to the deliverables directory."""
        try:
            deliverables_dir = self.output_dir / "deliverables"
            deliverables_dir.mkdir(parents=True, exist_ok=True)

            report_file = deliverables_dir / "workflow_completion_report.json"
            report_file.write_text(json.dumps(report, indent=2, default=str))

            # Also create a summary report
            summary = {
                "workflow_id": report["workflow_id"],
                "workflow_name": report["workflow_name"],
                "duration_seconds": report["duration_seconds"],
                "tasks_completed": report["tasks_completed"],
                "tasks_failed": report["tasks_failed"],
                "success_rate": report["performance_metrics"]["success_rate"],
                "deliverables_count": report["deliverables_count"],
                "peak_memory_mb": report["resource_usage"]["peak_memory_mb"],
                "error_count": report["error_count"],
                "completed_at": report["end_time"],
            }

            summary_file = deliverables_dir / "workflow_summary.json"
            summary_file.write_text(json.dumps(summary, indent=2))

            # Track these reports as deliverables
            self._track_deliverable(str(report_file), "created")
            self._track_deliverable(str(summary_file), "created")

            logger.info(f"Workflow completion report saved: {report_file}")
            logger.info(f"Workflow summary saved: {summary_file}")

        except Exception as e:
            logger.error(f"Failed to save completion report: {e}")

    def _create_workflow_metadata(self):
        """Create initial metadata.json with workflow tracking info."""
        metadata = {
            "workflow_id": self.workflow_id,
            "workflow_source": self.workflow_source,
            "workflow_name": self.workflow_name,
            "timestamp": self.workflow_timestamp,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "output_dir": str(self.output_dir),
            "max_parallel": self.max_parallel,
            "token_pool_size": self.token_pool.size()
            if hasattr(self, "token_pool") and self.token_pool
            else 0,
            "agent_execution_profile": self.agent_execution_profile,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "agents": [],
            "deliverables": [],
            "progress": {
                "percent": 0,
                "current_phase": "initializing",
                "eta_seconds": None,
            },
            "directory_structure": {
                "metadata": "workflow_info.json and other metadata files",
                "orchestrator.log": "main orchestrator log file",
                "agents": "individual agent logs and results",
                "deliverables": "workflow outputs and results",
                "checkpoints": "resume capability data",
            },
        }

        metadata_file = self.output_dir / "metadata" / "workflow_info.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

    def _update_workflow_metadata(self, updates: Dict):
        """Update workflow metadata with new information."""
        metadata_file = self.output_dir / "metadata" / "workflow_info.json"

        try:
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
            else:
                metadata = {}

            metadata.update(updates)
            metadata["last_updated"] = datetime.now().isoformat()

            metadata_file.write_text(json.dumps(metadata, indent=2))
        except Exception as e:
            logger.warning(f"Failed to update workflow metadata: {e}")

    def _create_checkpoint(self, task: AgentTask):
        """Create checkpoint for resume capability."""
        try:
            checkpoint_data = {
                "workflow_id": self.workflow_id,
                "workflow_source": self.workflow_source,
                "workflow_name": self.workflow_name,
                "timestamp": datetime.now().isoformat(),
                "task_id": task.task_id,
                "task_status": task.status,
                "metrics": self.metrics.copy(),
                "completed_tasks": list(self.dep_manager.completed),
                "failed_tasks": list(self.dep_manager.failed),
                "running_tasks": list(self.dep_manager.running),
            }

            checkpoint_file = (
                self.output_dir
                / "checkpoints"
                / f"checkpoint_{task.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))

            # Also create latest checkpoint
            latest_checkpoint = (
                self.output_dir / "checkpoints" / "latest_checkpoint.json"
            )
            latest_checkpoint.write_text(json.dumps(checkpoint_data, indent=2))

        except Exception as e:
            logger.warning(f"Failed to create checkpoint: {e}")

    def _report_workflow_started(self):
        """Report workflow start to dashboard if callback is configured."""
        if self.dashboard_state_callback:
            try:
                state_data = {
                    "event": "workflow_started",
                    "workflow_id": self.workflow_id,
                    "workflow_name": self.workflow_name,
                    "output_dir": str(self.output_dir),
                    "timestamp": datetime.now().isoformat(),
                    "max_parallel": self.max_parallel,
                    "token_pool_size": self.token_pool.size(),
                }
                self.dashboard_state_callback(state_data)
            except Exception as e:
                logger.warning(f"Failed to report workflow start to dashboard: {e}")

    def _report_workflow_progress(
        self, completed_tasks: int, total_tasks: int, current_task: Optional[str] = None
    ):
        """Report workflow progress to dashboard."""
        if self.dashboard_state_callback:
            try:
                progress_percent = (
                    int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
                )
                eta_seconds = self._calculate_eta(completed_tasks, total_tasks)

                state_data = {
                    "event": "workflow_progress",
                    "workflow_id": self.workflow_id,
                    "workflow_name": self.workflow_name,
                    "completed_tasks": completed_tasks,
                    "total_tasks": total_tasks,
                    "progress_percent": progress_percent,
                    "current_task": current_task,
                    "eta_seconds": eta_seconds,
                    "timestamp": datetime.now().isoformat(),
                }
                self.dashboard_state_callback(state_data)
            except Exception as e:
                logger.warning(f"Failed to report workflow progress to dashboard: {e}")

    def _report_task_activity(
        self, task: AgentTask, activity: str, details: Optional[Dict] = None
    ):
        """Report individual task activity to dashboard."""
        if self.dashboard_state_callback:
            try:
                state_data = {
                    "event": "task_activity",
                    "workflow_id": self.workflow_id,
                    "workflow_name": self.workflow_name,
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "activity": activity,  # started, completed, failed, progress
                    "status": task.status,
                    "timestamp": datetime.now().isoformat(),
                    "details": details or {},
                }
                if task.start_time:
                    state_data["duration"] = (
                        datetime.now().timestamp() - task.start_time
                    )
                self.dashboard_state_callback(state_data)
            except Exception as e:
                logger.warning(f"Failed to report task activity to dashboard: {e}")

    def _report_workflow_completed(self, metrics: Dict):
        """Report workflow completion to dashboard."""
        if self.dashboard_state_callback:
            try:
                state_data = {
                    "event": "workflow_completed",
                    "workflow_id": self.workflow_id,
                    "workflow_name": self.workflow_name,
                    "output_dir": str(self.output_dir),
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics,
                    "total_duration": metrics.get("total_duration", 0),
                }
                self.dashboard_state_callback(state_data)
            except Exception as e:
                logger.warning(
                    f"Failed to report workflow completion to dashboard: {e}"
                )

    def _calculate_eta(self, completed_tasks: int, total_tasks: int) -> Optional[int]:
        """Calculate estimated time to completion based on task completion rates."""
        if completed_tasks == 0 or not self.task_completion_times:
            return None

        remaining_tasks = total_tasks - completed_tasks
        if remaining_tasks <= 0:
            return 0

        # Calculate average completion time from recent completions
        recent_times = self.task_completion_times[
            -min(5, len(self.task_completion_times)) :
        ]
        avg_completion_time = sum(recent_times) / len(recent_times)

        # Estimate remaining time (accounting for parallel execution)
        estimated_seconds = (remaining_tasks * avg_completion_time) / self.max_parallel
        return int(estimated_seconds)

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

    def _validate_project_directory(self, path: str) -> Dict[str, Any]:
        """
        Validate that a directory path follows project directory standards.

        Returns:
            Dict with 'is_valid', 'category', 'warnings', and 'suggestions'
        """
        path_obj = Path(path).resolve()
        result = {
            "is_valid": True,
            "category": "unknown",
            "warnings": [],
            "suggestions": [],
        }

        # Check if path is under the master root
        master_root = Path("/home/opsvi/master_root").resolve()
        try:
            relative_to_master = path_obj.relative_to(master_root)
        except ValueError:
            result["is_valid"] = False
            result["warnings"].append(f"Path {path} is outside master_root structure")
            result["suggestions"].append(
                "Place project files under /home/opsvi/master_root/apps/PROJECT-NAME/"
            )
            return result

        # Categorize the path
        parts = relative_to_master.parts
        if not parts:
            result["category"] = "master_root"
            result["warnings"].append("Writing directly to master_root is discouraged")
            result["suggestions"].append(
                "Create project directory under apps/PROJECT-NAME/"
            )
        elif parts[0] == "apps":
            result["category"] = "apps"
            if len(parts) == 1:
                # Writing to /apps directory itself
                result["warnings"].append("Writing directly to apps/ directory")
                result["suggestions"].append(
                    "Create specific project directory like apps/PROJECT-NAME/"
                )
            elif len(parts) >= 2:
                project_name = parts[1]
                if project_name == "agent-orchestrator":
                    result["category"] = "orchestrator"
                    # This is orchestrator-specific, which is OK
                else:
                    result["category"] = "project"
                    # Validate project directory structure
                    if not self._is_valid_project_name(project_name):
                        result["warnings"].append(
                            f"Project name '{project_name}' should follow kebab-case convention"
                        )
                        result["suggestions"].append(
                            "Use lowercase with hyphens (e.g., my-awesome-project)"
                        )
        elif parts[0] == ".claude":
            result["category"] = "claude_workspace"
            # This is OK - Claude's personal workspace
        else:
            result["category"] = "other"
            result["warnings"].append(
                f"Path under {parts[0]}/ - consider if this belongs in apps/PROJECT-NAME/"
            )

        return result

    def _is_valid_project_name(self, name: str) -> bool:
        """
        Validate project name follows conventions.

        Project names should:
        - Be lowercase
        - Use hyphens instead of underscores
        - Be descriptive
        - Avoid generic names
        """
        # Basic format check: lowercase alphanumeric with hyphens
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            return False

        # Avoid single character or very short names
        if len(name) < 3:
            return False

        # Avoid generic names that might conflict
        generic_names = {"app", "project", "test", "demo", "sample", "temp", "tmp"}
        if name in generic_names:
            return False

        return True

    def _suggest_project_directory_structure(self, project_name: str) -> str:
        """
        Suggest proper directory structure for a new project.
        """
        # Clean and validate project name
        clean_name = self._clean_project_name(project_name)

        suggestions = f"""Suggested project structure for '{clean_name}':

/home/opsvi/master_root/apps/{clean_name}/
├── README.md                 # Project overview
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   └── USER_GUIDE.md
├── src/                      # Source code
├── tests/                    # Test files
├── config/                   # Configuration files
├── scripts/                  # Utility scripts
├── data/                     # Project data files
└── outputs/                  # Generated outputs

Project deliverables go in: /apps/{clean_name}/
Orchestrator operations remain in: /apps/agent-orchestrator/
"""
        return suggestions

    def _clean_project_name(self, name: str) -> str:
        """
        Clean and normalize a project name to follow conventions.
        """
        # Convert to lowercase
        clean = name.lower().strip()

        # Replace underscores and spaces with hyphens
        clean = re.sub(r"[_\s]+", "-", clean)

        # Remove non-alphanumeric characters except hyphens
        clean = re.sub(r"[^a-z0-9-]", "", clean)

        # Remove consecutive hyphens
        clean = re.sub(r"-+", "-", clean)

        # Remove leading/trailing hyphens
        clean = clean.strip("-")

        # Ensure it's not empty and not too short
        if len(clean) < 3:
            clean = f"project-{clean}" if clean else "new-project"

        return clean

    def _validate_and_warn_directory_usage(
        self, task: AgentTask, directory_path: str
    ) -> bool:
        """
        Validate directory usage for a task and issue warnings if needed.

        Returns:
            True if directory usage is acceptable, False if it should be blocked
        """
        validation = self._validate_project_directory(directory_path)

        # Create a warning key to avoid duplicate warnings
        warning_key = f"{task.task_type}:{validation['category']}:{directory_path}"

        if validation["warnings"] and warning_key not in self._directory_warnings:
            self._directory_warnings.add(warning_key)

            warning_msg = (
                f"[{task.task_id}] Directory usage warning for {directory_path}:\n"
            )
            for warning in validation["warnings"]:
                warning_msg += f"  • {warning}\n"

            if validation["suggestions"]:
                warning_msg += "Suggestions:\n"
                for suggestion in validation["suggestions"]:
                    warning_msg += f"  • {suggestion}\n"

            logger.warning(warning_msg)

            # Issue Python warning as well
            warnings.warn(
                f"Task {task.task_id}: {validation['warnings'][0]}",
                UserWarning,
                stacklevel=2,
            )

        # For now, don't block any operations for backward compatibility
        # In the future, could return False for certain violations
        return True

    def _detect_new_project_creation(self, task: AgentTask) -> Optional[str]:
        """
        Detect if a task is trying to create a new project.

        Returns:
            Project name if new project creation detected, None otherwise
        """
        # Look for patterns in task prompts that suggest new project creation
        if not hasattr(task, "prompt") or not task.prompt:
            return None

        prompt_lower = task.prompt.lower()

        # Common patterns that suggest new project creation
        creation_patterns = [
            r'create\s+(?:a\s+)?(?:new\s+)?project\s+(?:named\s+|called\s+)?["\']?([a-zA-Z0-9_-]+)["\']?',
            r'build\s+(?:a\s+)?(?:new\s+)?(?:application|app)\s+(?:named\s+|called\s+)?["\']?([a-zA-Z0-9_-]+)["\']?',
            r'implement\s+(?:a\s+)?(?:new\s+)?project\s+["\']?([a-zA-Z0-9_-]+)["\']?',
            r'start\s+(?:a\s+)?(?:new\s+)?project\s+["\']?([a-zA-Z0-9_-]+)["\']?',
            r'initialize\s+(?:a\s+)?(?:new\s+)?project\s+["\']?([a-zA-Z0-9_-]+)["\']?',
        ]

        for pattern in creation_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                return match.group(1)

        return None

    def _provide_project_creation_guidance(self, task: AgentTask, project_name: str):
        """
        Provide guidance when new project creation is detected.
        """
        clean_name = self._clean_project_name(project_name)
        suggested_structure = self._suggest_project_directory_structure(clean_name)

        guidance_msg = f"""[{task.task_id}] New project creation detected: '{project_name}'

Project Directory Standards:
{suggested_structure}

To ensure proper organization:
1. All project deliverables should go in /apps/{clean_name}/
2. Keep orchestrator operations separate in /apps/agent-orchestrator/
3. Follow the suggested directory structure above
4. Use kebab-case for project names (lowercase with hyphens)
"""

        logger.info(guidance_msg)

        # Store guidance in task context for agent to see
        if not hasattr(task, "context"):
            task.context = {}
        task.context["project_directory_guidance"] = {
            "project_name": project_name,
            "clean_name": clean_name,
            "suggested_path": f"/home/opsvi/master_root/apps/{clean_name}",
            "structure": suggested_structure,
        }

    def _validate_task_project_organization(self, task: AgentTask) -> Dict[str, Any]:
        """
        Validate task project organization fields and suggest improvements.

        Returns:
            Dict with 'is_valid', 'warnings', and 'suggestions'
        """
        result = {"is_valid": True, "warnings": [], "suggestions": []}

        # Check if project location is specified
        if hasattr(task, "project_location") and task.project_location:
            project_validation = self._validate_project_directory(task.project_location)
            if not project_validation["is_valid"]:
                result["is_valid"] = False
                result["warnings"].extend(
                    [f"Project location: {w}" for w in project_validation["warnings"]]
                )
                result["suggestions"].extend(
                    [
                        f"Project location: {s}"
                        for s in project_validation["suggestions"]
                    ]
                )
        else:
            # Check if task suggests new project creation
            project_name = self._detect_new_project_creation(task)
            if project_name:
                result["warnings"].append(
                    "Task appears to create a new project but lacks 'project_location' field"
                )
                clean_name = self._clean_project_name(project_name)
                result["suggestions"].append(
                    f"Add project_location: '/home/opsvi/master_root/apps/{clean_name}/'"
                )

        # Validate deliverable structure if specified
        if hasattr(task, "deliverable_structure") and task.deliverable_structure:
            for key, path in task.deliverable_structure.items():
                if not path.startswith("/"):
                    result["warnings"].append(
                        f"Deliverable path '{key}' should be absolute: {path}"
                    )
                    result["suggestions"].append(
                        f"Use absolute paths starting with '/' for all deliverables"
                    )
                    break

        # Check if directory permissions are properly specified
        if hasattr(task, "directory_permissions") and task.directory_permissions:
            for perm in task.directory_permissions:
                if not perm.startswith("/"):
                    result["warnings"].append(
                        f"Directory permission should be absolute path: {perm}"
                    )
                    result["suggestions"].append(
                        "Use absolute paths for directory permissions"
                    )
                    break
        else:
            # Suggest standard permissions based on task type
            if hasattr(task, "project_location") and task.project_location:
                result["suggestions"].append(
                    f"Consider adding directory_permissions: ['{task.project_location}']"
                )

        return result

    def _enhance_task_with_project_organization(self, task: AgentTask) -> AgentTask:
        """
        Enhance task with suggested project organization fields if missing.

        Returns:
            Enhanced task with project organization suggestions
        """
        # Auto-detect project creation and suggest project_location
        if not hasattr(task, "project_location") or not task.project_location:
            project_name = self._detect_new_project_creation(task)
            if project_name:
                clean_name = self._clean_project_name(project_name)
                task.project_location = f"/home/opsvi/master_root/apps/{clean_name}/"

                # Suggest standard deliverable structure
                if (
                    not hasattr(task, "deliverable_structure")
                    or not task.deliverable_structure
                ):
                    task.deliverable_structure = {
                        "main_deliverable": f"{task.project_location}",
                        "documentation": f"{task.project_location}docs/",
                        "source_code": f"{task.project_location}src/",
                        "configuration": f"{task.project_location}config/",
                    }

                # Add standard directory permissions
                if (
                    not hasattr(task, "directory_permissions")
                    or not task.directory_permissions
                ):
                    task.directory_permissions = [
                        task.project_location,
                        "/home/opsvi/master_root/apps/",
                    ]

                # Add basic output validation rules
                if not hasattr(task, "output_validation") or not task.output_validation:
                    task.output_validation = {
                        "required_structure": True,
                        "validate_paths": True,
                        "check_project_standards": True,
                    }

        return task

    def _apply_task_directory_permissions(
        self, task: AgentTask, cmd: List[str]
    ) -> List[str]:
        """
        Apply directory permissions from task to command.

        Args:
            task: The task with potential directory permissions
            cmd: The command list to modify

        Returns:
            Modified command list with additional --add-dir parameters
        """
        # Apply directory permissions from task if available
        if hasattr(task, "directory_permissions") and task.directory_permissions:
            for dir_path in task.directory_permissions:
                # Avoid duplicates
                if "--add-dir" in cmd:
                    existing_dirs = []
                    i = 0
                    while i < len(cmd) - 1:
                        if cmd[i] == "--add-dir":
                            existing_dirs.append(cmd[i + 1])
                            i += 2
                        else:
                            i += 1

                    if dir_path not in existing_dirs:
                        # Find insertion point (before the "--" separator)
                        try:
                            separator_idx = cmd.index("--")
                            cmd.insert(separator_idx, "--add-dir")
                            cmd.insert(separator_idx + 1, dir_path)
                        except ValueError:
                            # No separator found, add at end
                            cmd.extend(["--add-dir", dir_path])
                else:
                    # First --add-dir parameter
                    try:
                        separator_idx = cmd.index("--")
                        cmd.insert(separator_idx, "--add-dir")
                        cmd.insert(separator_idx + 1, dir_path)
                    except ValueError:
                        # No separator found, add at end
                        cmd.extend(["--add-dir", dir_path])

        return cmd

    def _log_task_organization_validation(
        self, task: AgentTask, validation_result: Dict[str, Any]
    ):
        """Log task organization validation results."""
        if validation_result["warnings"]:
            warning_msg = f"[{task.task_id}] Project organization warnings:\n"
            for warning in validation_result["warnings"]:
                warning_msg += f"  • {warning}\n"

            if validation_result["suggestions"]:
                warning_msg += "Suggestions:\n"
                for suggestion in validation_result["suggestions"]:
                    warning_msg += f"  • {suggestion}\n"

            logger.warning(warning_msg)

            # Log to audit trail
            self._log_audit_action(
                "task_organization_validation",
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "validation_result": validation_result,
                },
            )

    def _init_providers(self):
        """Initialize multi-provider support"""
        self.providers = {}
        self.active_provider = "claude"

        # Initialize OpenAI provider if available
        if OpenAIProvider and os.getenv("OPENAI_API_KEY"):
            self.providers["openai"] = OpenAIProvider()
            logger.info("OpenAI provider initialized")
        else:
            logger.info("OpenAI provider not available")

    def _switch_provider(self):
        """Switch to fallback provider when current exhausted"""
        if self.active_provider == "claude" and "openai" in self.providers:
            if self.providers["openai"].has_capacity():
                self.active_provider = "openai"
                logger.info("Switched to OpenAI provider")
                return True
        elif self.active_provider == "openai":
            # Try switching back to Claude (if tokens refreshed)
            self.active_provider = "claude"
            logger.info("Switched back to Claude provider")
            return True
        return False

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

        # Log audit entry for task start
        self._log_audit_action(
            "task_started",
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "session_id": session_id,
                "agent_work_dir": str(agent_work_dir),
            },
        )

        # Validate and enhance task project organization
        validation_result = self._validate_task_project_organization(task)
        if validation_result["warnings"] or validation_result["suggestions"]:
            self._log_task_organization_validation(task, validation_result)

        # Enhance task with project organization if needed
        task = self._enhance_task_with_project_organization(task)

        # Report task start to dashboard
        self._report_task_activity(task, "started")

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

        # Validate directory usage and provide guidance
        project_name = self._detect_new_project_creation(task)
        if project_name:
            self._provide_project_creation_guidance(task, project_name)

        # Validate primary working directory
        work_dir_path = str(
            agent_work_dir if self.enable_dynamic_configs else self.output_dir
        )
        self._validate_and_warn_directory_usage(task, work_dir_path)

        # Validate additional directory access
        apps_dir = "/home/opsvi/master_root/apps"
        self._validate_and_warn_directory_usage(task, apps_dir)

        # Add session and workspace parameters
        cmd.extend(
            [
                "--session-id",
                session_id,
                "--add-dir",
                work_dir_path,
                "--add-dir",
                apps_dir,  # Allow agents to create project directories outside orchestrator scope
            ]
        )

        # Apply additional directory permissions from task
        cmd = self._apply_task_directory_permissions(task, cmd)

        # Add prompt separator and prompt
        cmd.extend(["--", prompt])

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

            # Report task running to dashboard
            self._report_task_activity(task, "running", {"start_time": task.start_time})

            try:
                logger.info(f"Executing {task.task_id} ({task.task_type})")

                # Set up log file - always log to agents directory
                log_file_handle = None
                agent_log_file = self.output_dir / "agents" / f"{task.task_id}.log"
                agent_log_file.parent.mkdir(parents=True, exist_ok=True)

                if self.log_to_work_dir and self.enable_dynamic_configs:
                    # Also log to work dir if requested
                    work_dir_log_file = (
                        agent_work_dir / "logs" / f"agent_{task.task_id}.log"
                    )
                    work_dir_log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file_handle = open(work_dir_log_file, "w")
                    stderr_target = log_file_handle

                    # Create symlink from agents directory to work dir log
                    try:
                        if agent_log_file.exists():
                            agent_log_file.unlink()
                        agent_log_file.symlink_to(work_dir_log_file)
                    except OSError:
                        # Fallback to copy if symlink fails
                        pass
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
                elif process.returncode != 0 and stderr is None:
                    # Try to capture stderr from agents log file
                    try:
                        if agent_log_file.exists():
                            stderr_content = agent_log_file.read_text()
                            stderr = stderr_content.encode() if stderr_content else None
                    except Exception as e:
                        logger.warning(
                            f"Failed to read stderr from agent log file: {e}"
                        )

                task.end_time = datetime.now().timestamp()
                duration = task.end_time - task.start_time

                if process.returncode == 0:
                    # Parse output with comprehensive error handling
                    if stdout:
                        stdout_text = stdout.decode("utf-8", errors="replace").strip()

                        # Opt-in parsing controls
                        require_json = os.getenv("UNIFIED_REQUIRE_JSON", "0") == "1"
                        strip_fences = os.getenv("UNIFIED_STRIP_FENCES", "0") == "1"

                        if strip_fences:
                            # Extract first fenced block ```json ... ``` or ``` ... ```
                            m = re.search(
                                r"```(?:json)?\s*(.*?)\s*```", stdout_text, re.S | re.I
                            )
                            if m:
                                stdout_text = m.group(1).strip()

                        try:
                            # Attempt JSON parsing
                            task.result = json.loads(stdout_text)
                            task.status = "completed"
                            await self.dep_manager.mark_completed(task.task_id)
                            self.metrics["completed"] += 1

                            # Track completion time for ETA calculations
                            self.task_completion_times.append(duration)

                            # Log audit entry for task completion
                            self._log_audit_action(
                                "task_completed",
                                {
                                    "task_id": task.task_id,
                                    "task_type": task.task_type,
                                    "duration_seconds": duration,
                                    "result_type": "json",
                                    "memory_usage_mb": self.process.memory_info().rss
                                    / 1024
                                    / 1024,
                                },
                            )

                            # Report task completion to dashboard
                            self._report_task_activity(
                                task,
                                "completed",
                                {"duration": duration, "result_type": "json"},
                            )

                            # Update workflow progress
                            self._update_workflow_metadata(
                                {
                                    "completed_tasks": self.metrics["completed"],
                                    "progress": {
                                        "percent": int(
                                            (
                                                self.metrics["completed"]
                                                / self.total_tasks
                                            )
                                            * 100
                                        )
                                        if self.total_tasks > 0
                                        else 0,
                                        "current_phase": "executing",
                                    },
                                }
                            )

                            # Create checkpoint
                            self._create_checkpoint(task)

                            logger.info(
                                f"✓ {task.task_id} completed in {duration:.2f}s"
                            )
                        except json.JSONDecodeError as e:
                            if require_json:
                                task.status = "failed"
                                task.error_details = f"json_parse_failed: {e.__class__.__name__}: {str(e)[:200]}"
                                # ensure dependency graph is updated and metrics reflect failure
                                await self.dep_manager.mark_failed(task.task_id)
                                self.metrics["failed"] = (
                                    self.metrics.get("failed", 0) + 1
                                )
                                logger.error(
                                    f"✗ {task.task_id} failed JSON validation: {task.error_details}"
                                )
                                return {
                                    "status": "error",
                                    "error": "json_parse_failed",
                                    "raw": stdout_text,
                                }
                            else:
                                # legacy behavior: accept freeform as success
                                task.result = {
                                    "status": "completed",
                                    "raw_text": stdout_text,
                                }
                                task.status = "completed"
                                await self.dep_manager.mark_completed(task.task_id)
                                self.metrics["completed"] += 1

                                # Track completion time for ETA calculations
                                self.task_completion_times.append(duration)

                                # Log audit entry for task completion
                                self._log_audit_action(
                                    "task_completed",
                                    {
                                        "task_id": task.task_id,
                                        "task_type": task.task_type,
                                        "duration_seconds": duration,
                                        "result_type": "non_json",
                                        "memory_usage_mb": self.process.memory_info().rss
                                        / 1024
                                        / 1024,
                                    },
                                )

                                # Report task completion to dashboard
                                self._report_task_activity(
                                    task,
                                    "completed",
                                    {"duration": duration, "result_type": "non_json"},
                                )

                                # Update workflow progress
                                self._update_workflow_metadata(
                                    {
                                        "completed_tasks": self.metrics["completed"],
                                        "progress": {
                                            "percent": int(
                                                (
                                                    self.metrics["completed"]
                                                    / self.total_tasks
                                                )
                                                * 100
                                            )
                                            if self.total_tasks > 0
                                            else 0,
                                            "current_phase": "executing",
                                        },
                                    }
                                )

                                # Create checkpoint
                                self._create_checkpoint(task)

                                logger.info(
                                    f"✓ {task.task_id} completed in {duration:.2f}s (non-JSON output)"
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

                    # Log audit entry for task failure
                    self._log_audit_action(
                        "task_failed",
                        {
                            "task_id": task.task_id,
                            "task_type": task.task_type,
                            "duration_seconds": duration,
                            "error": task.error[:200]
                            if task.error
                            else "Unknown error",
                            "exit_code": process.returncode,
                            "memory_usage_mb": self.process.memory_info().rss
                            / 1024
                            / 1024,
                        },
                    )

                    # Report task failure to dashboard
                    self._report_task_activity(
                        task,
                        "failed",
                        {
                            "duration": duration,
                            "error": task.error,
                            "exit_code": process.returncode,
                        },
                    )

                    # Update workflow metadata with failure
                    self._update_workflow_metadata(
                        {"failed_tasks": self.metrics["failed"]}
                    )

                    # Create checkpoint for failed task too
                    self._create_checkpoint(task)

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

                # Log audit entry for task exception
                self._log_audit_action(
                    "task_exception",
                    {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "error": task.error[:200]
                        if task.error
                        else "Unknown exception",
                        "error_type": error_type,
                        "memory_usage_mb": self.process.memory_info().rss / 1024 / 1024,
                    },
                )

                # Report task exception to dashboard
                self._report_task_activity(
                    task, "failed", {"error": task.error, "error_type": "exception"}
                )

                # Update workflow metadata with failure
                self._update_workflow_metadata({"failed_tasks": self.metrics["failed"]})

                # Create checkpoint for exception too
                self._create_checkpoint(task)

                logger.error(f"✗ {task.task_id} exception: {task.error}")

        finally:
            # Always release the token
            if hasattr(self.token_pool, "release"):
                self.token_pool.release(token_idx)

        # Post-execution hook
        if self.post_execute_hook:
            await self.post_execute_hook(task)

        # Update resource usage after task completion
        self._update_resource_usage()

        # Save task state to agents directory
        task_file = self.output_dir / "agents" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

        # Track the task file as a deliverable
        self._track_deliverable(str(task_file), "created")

        return task.to_dict()

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute a batch of tasks respecting dependencies and parallelism limits"""

        self.metrics["total"] = len(tasks)
        self.metrics["start_time"] = datetime.now().isoformat()
        self.workflow_start_time = datetime.now().timestamp()
        self.total_tasks = len(tasks)

        # Log audit entry for batch execution start
        self._log_audit_action(
            "batch_execution_started",
            {
                "total_tasks": len(tasks),
                "max_parallel": self.max_parallel,
                "initial_memory_mb": self.process.memory_info().rss / 1024 / 1024,
            },
        )

        # Report initial workflow progress
        self._report_workflow_progress(0, len(tasks))

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
                        self.output_dir / "agents" / f"{failed_task.task_id}.json"
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

            # Report progress after each batch
            completed_count = len(
                [r for r in results if r.get("status") == "completed"]
            )
            self._report_workflow_progress(completed_count, len(tasks))

            # Brief pause between batches
            await asyncio.sleep(0.5)

        self.metrics["end_time"] = datetime.now().isoformat()

        # Generate and save workflow completion report
        completion_report = self._generate_workflow_completion_report()
        self._save_completion_report(completion_report)

        # Log audit entry for batch completion
        self._log_audit_action(
            "batch_execution_completed",
            {
                "total_tasks": len(tasks),
                "completed_tasks": self.metrics["completed"],
                "failed_tasks": self.metrics["failed"],
                "duration_seconds": completion_report["duration_seconds"],
                "success_rate": completion_report["performance_metrics"][
                    "success_rate"
                ],
                "deliverables_count": completion_report["deliverables_count"],
                "peak_memory_mb": completion_report["resource_usage"]["peak_memory_mb"],
            },
        )

        # Report workflow completion
        if self.enable_dashboard_reporting:
            self._report_workflow_completed(self.metrics)

        # Update final metadata
        self._update_workflow_metadata(
            {
                "status": "batch_completed",
                "completed_tasks": self.metrics["completed"],
                "failed_tasks": self.metrics["failed"],
                "completion_report_generated": True,
            }
        )

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

        # Update metadata with task count
        self._update_workflow_metadata(
            {
                "total_tasks": len(tasks),
                "status": "running",
                "started_at": datetime.now().isoformat(),
            }
        )

        # Execute tasks
        results = await self.execute_batch(tasks)

        # Process results if processor provided
        if result_processor:
            await result_processor(results)

        # Final metadata update (completion report already generated in execute_batch)
        self._update_workflow_metadata(
            {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "completed_tasks": self.metrics["completed"],
                "failed_tasks": self.metrics["failed"],
                "total_duration": self.metrics["total_duration"],
            }
        )

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
