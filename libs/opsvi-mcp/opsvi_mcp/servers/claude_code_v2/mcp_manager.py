"""
MCP Server Manager for V2 - Intelligent MCP server availability and monitoring
"""

import os
import sys
import time
import json
import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MCPServerStatus(Enum):
    """MCP server status states"""

    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    NOT_NEEDED = "not_needed"


@dataclass
class MCPServerMetrics:
    """Metrics for MCP server initialization and performance"""

    server_name: str
    start_time: Optional[float] = None
    ready_time: Optional[float] = None
    initialization_duration_ms: Optional[int] = None
    status: MCPServerStatus = MCPServerStatus.UNKNOWN
    error_message: Optional[str] = None
    check_attempts: int = 0
    last_check_time: Optional[float] = None


@dataclass
class MCPInstanceConfig:
    """Configuration for a Claude instance with specific MCP servers"""

    instance_id: str
    config_path: str
    required_servers: Set[str] = field(default_factory=set)
    optional_servers: Set[str] = field(default_factory=set)
    max_wait_seconds: int = 7
    check_interval_ms: int = 500
    exponential_backoff: bool = True
    metrics: Dict[str, MCPServerMetrics] = field(default_factory=dict)


class MCPRequirementAnalyzer:
    """Analyzes tasks to determine which MCP servers are needed"""

    # MCP server patterns - which keywords/patterns indicate need for each server
    MCP_PATTERNS = {
        "git": [
            r"\bgit\b",
            r"\bcommit\b",
            r"\bbranch\b",
            r"\bmerge\b",
            r"\brebase\b",
            r"\bcheckout\b",
            r"\bclone\b",
            r"\bpull\b",
            r"\bpush\b",
        ],
        "firecrawl": [
            r"\bscrape\b",
            r"\bcrawl\b",
            r"\bweb\s+page\b",
            r"\bwebsite\b",
            r"\bextract\s+from\s+url\b",
            r"\bfetch\s+url\b",
        ],
        "time": [
            r"\bcurrent\s+time\b",
            r"\btimestamp\b",
            r"\bdate\b",
            r"\btimezone\b",
            r"\bconvert\s+time\b",
        ],
        "shell_exec": [
            r"\brun\s+command\b",
            r"\bexecute\b",
            r"\bshell\b",
            r"\bbash\b",
            r"\bterminal\b",
            r"\bcommand\s+line\b",
        ],
        "research_papers": [
            r"\barxiv\b",
            r"\bpaper\b",
            r"\bresearch\b",
            r"\bacademic\b",
            r"\bjournal\b",
            r"\bpublication\b",
        ],
        "db": [
            r"\bdatabase\b",
            r"\bneo4j\b",
            r"\bcypher\b",
            r"\bquery\b",
            r"\bSQL\b",
            r"\btable\b",
            r"\bschema\b",
        ],
        "tech_docs": [
            r"\bdocumentation\b",
            r"\blibrary\b",
            r"\bAPI\s+docs\b",
            r"\bframework\b",
            r"\bpackage\s+docs\b",
        ],
        "mcp_web_search": [
            r"\bsearch\s+web\b",
            r"\bgoogle\b",
            r"\bbrave\s+search\b",
            r"\binternet\b",
            r"\bonline\b",
        ],
        "calc": [
            r"\bcalculate\b",
            r"\bmath\b",
            r"\barithmetic\b",
            r"\bcompute\b",
            r"\bsum\b",
            r"\baverage\b",
            r"\bequation\b",
        ],
        "claude-code-wrapper": [
            r"\bdebug\b",
            r"\bfix\s+error\b",
            r"\binvestigate\b",
            r"\banalyze\s+code\b",
            r"\bwhy\b",
        ],
        "claude-code-v2": [
            r"\bparallel\b",
            r"\ball\s+files\b",
            r"\bevery\b",
            r"\bmultiple\b",
            r"\bbatch\b",
            r"\bconcurrent\b",
        ],
        "claude-code-v3": [
            r"\bproduction\b",
            r"\benterprise\b",
            r"\brobust\b",
            r"\bcomprehensive\b",
            r"\bquality\b",
        ],
    }

    @classmethod
    def analyze_task(cls, task: str) -> Set[str]:
        """Analyze a task to determine which MCP servers are needed"""
        required_servers = set()
        task_lower = task.lower()

        for server_name, patterns in cls.MCP_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, task_lower, re.IGNORECASE):
                    required_servers.add(server_name)
                    break

        logger.debug(f"Task analysis found required MCP servers: {required_servers}")
        return required_servers

    @classmethod
    def task_needs_mcp(cls, task: str) -> bool:
        """Check if a task needs any MCP servers at all"""
        return len(cls.analyze_task(task)) > 0


class MCPAvailabilityChecker:
    """Checks MCP server availability with exponential backoff"""

    def __init__(self, config: MCPInstanceConfig):
        self.config = config
        self.start_time = time.time()

    async def wait_for_mcp_servers(
        self, required_servers: Optional[Set[str]] = None, task: Optional[str] = None
    ) -> Tuple[bool, Dict[str, MCPServerMetrics]]:
        """
        Wait for required MCP servers to be available

        Returns:
            Tuple of (success, metrics_dict)
        """
        # Determine which servers we need
        if required_servers is None and task:
            required_servers = MCPRequirementAnalyzer.analyze_task(task)

        if not required_servers:
            logger.info("No MCP servers required for this task")
            return True, {}

        logger.info(f"Waiting for MCP servers: {required_servers}")

        # Initialize metrics
        for server in required_servers:
            if server not in self.config.metrics:
                self.config.metrics[server] = MCPServerMetrics(
                    server_name=server, start_time=self.start_time
                )

        # Check loop with exponential backoff
        attempt = 0
        backoff_ms = self.config.check_interval_ms

        while (time.time() - self.start_time) < self.config.max_wait_seconds:
            attempt += 1
            all_ready = True

            for server in required_servers:
                metric = self.config.metrics[server]
                metric.check_attempts = attempt
                metric.last_check_time = time.time()

                # Check if server is ready
                is_ready = await self._check_server_ready(server)

                if is_ready and metric.status != MCPServerStatus.READY:
                    # Server just became ready
                    metric.ready_time = time.time()
                    metric.initialization_duration_ms = int(
                        (metric.ready_time - self.start_time) * 1000
                    )
                    metric.status = MCPServerStatus.READY
                    logger.info(
                        f"MCP server '{server}' ready after {metric.initialization_duration_ms}ms "
                        f"({attempt} attempts)"
                    )
                elif not is_ready:
                    metric.status = MCPServerStatus.INITIALIZING
                    all_ready = False

            if all_ready:
                logger.info(f"All required MCP servers ready after {attempt} attempts")
                return True, self.config.metrics

            # Wait with backoff
            await asyncio.sleep(backoff_ms / 1000.0)

            if self.config.exponential_backoff:
                backoff_ms = min(backoff_ms * 2, 2000)  # Cap at 2 seconds

        # Timeout - mark failed servers
        for server in required_servers:
            metric = self.config.metrics[server]
            if metric.status != MCPServerStatus.READY:
                metric.status = MCPServerStatus.FAILED
                metric.error_message = f"Timeout after {self.config.max_wait_seconds}s"
                logger.error(f"MCP server '{server}' failed to initialize in time")

        return False, self.config.metrics

    async def _check_server_ready(self, server_name: str) -> bool:
        """
        Check if a specific MCP server is ready

        This would need to be implemented based on how we can probe MCP servers
        """
        # TODO: Implement actual MCP server readiness check
        # For now, simulate based on time
        elapsed = time.time() - self.start_time

        # Simulate different load times for different servers
        simulated_load_times = {
            "git": 1.5,
            "firecrawl": 2.0,
            "time": 0.5,
            "shell_exec": 1.0,
            "claude-code-wrapper": 3.0,
            "claude-code-v2": 3.5,
            "claude-code-v3": 4.0,
        }

        required_time = simulated_load_times.get(server_name, 2.0)
        return elapsed >= required_time


class MCPConfigManager:
    """Manages different MCP configurations for different instance types"""

    # Pre-defined configurations for different use cases
    CONFIGURATIONS = {
        "minimal": {
            "description": "Minimal MCP servers for basic operations",
            "servers": ["time", "calc"],
        },
        "git_only": {"description": "Only Git operations", "servers": ["git"]},
        "web_focused": {
            "description": "Web scraping and search",
            "servers": ["firecrawl", "mcp_web_search", "tech_docs"],
        },
        "development": {
            "description": "Standard development tools",
            "servers": ["git", "shell_exec", "tech_docs"],
        },
        "data_science": {
            "description": "Data science and research",
            "servers": ["research_papers", "db", "calc"],
        },
        "claude_orchestration": {
            "description": "Claude orchestration servers only",
            "servers": ["claude-code-wrapper", "claude-code-v2", "claude-code-v3"],
        },
        "full": {
            "description": "All available MCP servers",
            "servers": None,  # Load from main .mcp.json
        },
    }

    @classmethod
    def create_instance_config(
        cls,
        instance_id: str,
        config_type: str = "minimal",
        custom_servers: Optional[List[str]] = None,
    ) -> str:
        """
        Create a custom .mcp.json configuration for an instance

        Returns:
            Path to the created configuration file
        """
        # Create instance-specific config directory
        config_dir = Path(f"/tmp/claude_instances/{instance_id}")
        config_dir.mkdir(parents=True, exist_ok=True)

        config_path = config_dir / ".mcp.json"

        # Determine which servers to include
        if custom_servers:
            servers_to_include = custom_servers
        elif config_type in cls.CONFIGURATIONS:
            servers_to_include = cls.CONFIGURATIONS[config_type]["servers"]
        else:
            servers_to_include = cls.CONFIGURATIONS["minimal"]["servers"]

        # Load base configuration
        base_config_path = Path("/home/opsvi/master_root/.mcp.json")
        if base_config_path.exists():
            with open(base_config_path, "r") as f:
                base_config = json.load(f)
        else:
            base_config = {"mcpServers": {}}

        # Filter to only requested servers
        if servers_to_include:
            filtered_config = {
                "mcpServers": {
                    server: config
                    for server, config in base_config.get("mcpServers", {}).items()
                    if server in servers_to_include
                }
            }
        else:
            filtered_config = base_config

        # Write configuration
        with open(config_path, "w") as f:
            json.dump(filtered_config, f, indent=2)

        logger.info(
            f"Created MCP config for instance '{instance_id}' "
            f"with servers: {list(filtered_config['mcpServers'].keys())}"
        )

        return str(config_path)


class MCPEventMonitor:
    """Monitors Claude logs for MCP initialization events"""

    MCP_INIT_PATTERNS = [
        r"MCP server '([^']+)' initialized",
        r"Starting MCP server: ([^\s]+)",
        r"Connected to ([^\s]+) MCP server",
        r"MCP\s+([^\s]+)\s+ready",
        r"\[([^\]]+)\]\s+server started",
    ]

    MCP_COMPLETE_PATTERNS = [
        r"All MCP servers initialized",
        r"MCP initialization complete",
        r"Ready to accept commands",
        r"Claude Code ready",
    ]

    @classmethod
    async def monitor_initialization(
        cls, log_file: str, timeout_seconds: int = 10
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Monitor log file for MCP initialization events

        Returns:
            Tuple of (all_initialized, server_timestamps)
        """
        server_timestamps = {}
        start_time = time.time()

        # Open log file for monitoring
        try:
            with open(log_file, "r") as f:
                # Move to end of file
                f.seek(0, 2)

                while (time.time() - start_time) < timeout_seconds:
                    line = f.readline()

                    if not line:
                        await asyncio.sleep(0.1)
                        continue

                    # Check for individual server initialization
                    for pattern in cls.MCP_INIT_PATTERNS:
                        match = re.search(pattern, line)
                        if match:
                            server_name = match.group(1)
                            if server_name not in server_timestamps:
                                server_timestamps[server_name] = time.time()
                                logger.debug(
                                    f"Detected MCP server '{server_name}' initialized"
                                )

                    # Check for completion signal
                    for pattern in cls.MCP_COMPLETE_PATTERNS:
                        if re.search(pattern, line):
                            logger.info("Detected MCP initialization complete signal")
                            return True, server_timestamps

        except FileNotFoundError:
            logger.warning(f"Log file not found: {log_file}")
        except Exception as e:
            logger.error(f"Error monitoring log file: {e}")

        return False, server_timestamps


class IntelligentMCPManager:
    """Main manager combining all MCP management capabilities"""

    def __init__(self):
        self.instances: Dict[str, MCPInstanceConfig] = {}
        self.metrics_history: List[Dict] = []

    async def prepare_instance(
        self, instance_id: str, task: str, force_config_type: Optional[str] = None
    ) -> MCPInstanceConfig:
        """
        Prepare a Claude instance with appropriate MCP configuration
        """
        # Analyze task requirements
        required_servers = MCPRequirementAnalyzer.analyze_task(task)

        if not required_servers:
            logger.info(f"Task doesn't require MCP servers: {task[:100]}")
            config_type = "minimal"
        elif force_config_type:
            config_type = force_config_type
        else:
            # Determine best config type based on requirements
            config_type = self._select_config_type(required_servers)

        # Create instance configuration
        config_path = MCPConfigManager.create_instance_config(
            instance_id,
            config_type,
            custom_servers=list(required_servers) if required_servers else None,
        )

        # Create instance config object
        instance_config = MCPInstanceConfig(
            instance_id=instance_id,
            config_path=config_path,
            required_servers=required_servers,
            max_wait_seconds=7,
            exponential_backoff=True,
        )

        self.instances[instance_id] = instance_config
        return instance_config

    async def wait_for_instance_ready(
        self, instance_id: str, task: Optional[str] = None
    ) -> bool:
        """
        Wait for an instance's MCP servers to be ready
        """
        if instance_id not in self.instances:
            logger.error(f"Unknown instance: {instance_id}")
            return False

        config = self.instances[instance_id]
        checker = MCPAvailabilityChecker(config)

        success, metrics = await checker.wait_for_mcp_servers(task=task)

        # Store metrics for analysis
        self._record_metrics(instance_id, metrics)

        return success

    def _select_config_type(self, required_servers: Set[str]) -> str:
        """Select the best configuration type based on required servers"""

        # Check each predefined config
        for config_name, config_info in MCPConfigManager.CONFIGURATIONS.items():
            if (
                config_info["servers"]
                and set(config_info["servers"]) >= required_servers
            ):
                return config_name

        # Default to full if no match
        return "full"

    def _record_metrics(self, instance_id: str, metrics: Dict[str, MCPServerMetrics]):
        """Record metrics for analysis"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "instance_id": instance_id,
            "metrics": {},
        }

        for server_name, metric in metrics.items():
            record["metrics"][server_name] = {
                "status": metric.status.value,
                "initialization_ms": metric.initialization_duration_ms,
                "attempts": metric.check_attempts,
                "error": metric.error_message,
            }

        self.metrics_history.append(record)

        # Log summary
        successful = sum(
            1 for m in metrics.values() if m.status == MCPServerStatus.READY
        )
        failed = sum(1 for m in metrics.values() if m.status == MCPServerStatus.FAILED)
        avg_init_time = sum(
            m.initialization_duration_ms
            for m in metrics.values()
            if m.initialization_duration_ms
        ) / max(successful, 1)

        logger.info(
            f"MCP initialization complete for '{instance_id}': "
            f"{successful} ready, {failed} failed, avg time: {avg_init_time:.0f}ms"
        )

    def get_performance_summary(self) -> Dict:
        """Get summary of MCP initialization performance"""
        if not self.metrics_history:
            return {"message": "No metrics collected yet"}

        all_init_times = []
        server_stats = {}

        for record in self.metrics_history:
            for server_name, data in record["metrics"].items():
                if server_name not in server_stats:
                    server_stats[server_name] = {
                        "total_attempts": 0,
                        "successful": 0,
                        "failed": 0,
                        "init_times": [],
                    }

                stats = server_stats[server_name]
                stats["total_attempts"] += 1

                if data["status"] == "ready":
                    stats["successful"] += 1
                    if data["initialization_ms"]:
                        stats["init_times"].append(data["initialization_ms"])
                        all_init_times.append(data["initialization_ms"])
                elif data["status"] == "failed":
                    stats["failed"] += 1

        # Calculate aggregates
        summary = {
            "total_instances": len(self.instances),
            "total_measurements": len(self.metrics_history),
            "overall_avg_init_ms": sum(all_init_times) / len(all_init_times)
            if all_init_times
            else 0,
            "overall_max_init_ms": max(all_init_times) if all_init_times else 0,
            "overall_min_init_ms": min(all_init_times) if all_init_times else 0,
            "per_server_stats": {},
        }

        for server_name, stats in server_stats.items():
            if stats["init_times"]:
                summary["per_server_stats"][server_name] = {
                    "success_rate": stats["successful"] / stats["total_attempts"],
                    "avg_init_ms": sum(stats["init_times"]) / len(stats["init_times"]),
                    "max_init_ms": max(stats["init_times"]),
                    "min_init_ms": min(stats["init_times"]),
                    "samples": len(stats["init_times"]),
                }

        return summary


# Example usage
async def example_usage():
    """Example of how to use the intelligent MCP manager"""

    manager = IntelligentMCPManager()

    # Task that needs Git and shell
    task1 = "Create a git commit for all changes and run the tests"
    instance1 = await manager.prepare_instance("instance-1", task1)

    # Start Claude with custom config
    claude_process = await start_claude_with_config(
        instance1.config_path, instance1.instance_id
    )

    # Wait for MCP servers to be ready
    ready = await manager.wait_for_instance_ready("instance-1", task1)

    if ready:
        # Execute task
        result = await execute_task_on_instance(claude_process, task1)
    else:
        logger.error("MCP servers failed to initialize")

    # Get performance metrics
    summary = manager.get_performance_summary()
    print(json.dumps(summary, indent=2))


async def start_claude_with_config(config_path: str, instance_id: str):
    """Start Claude with a specific MCP configuration"""
    # This would need to be implemented based on how Claude can be started
    # with a custom config path
    pass


async def execute_task_on_instance(process, task: str):
    """Execute a task on a Claude instance"""
    # Implementation would depend on Claude's interface
    pass


if __name__ == "__main__":
    # Test the components
    asyncio.run(example_usage())
