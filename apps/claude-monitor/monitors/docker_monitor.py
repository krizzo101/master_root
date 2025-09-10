#!/usr/bin/env python3
"""
Docker Monitor for Claude Processes

Monitors Docker containers for Claude activity, resource usage, and metrics.
"""

import json
import logging
import re
import threading
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import docker

logger = logging.getLogger(__name__)


class DockerClaudeMonitor:
    def __init__(self):
        self.client = None
        self.containers_with_claude = {}
        self.metrics = defaultdict(dict)
        self.log_streams = {}
        self.monitoring_active = False
        self.monitor_thread = None
        self._connect_to_docker()

    def _connect_to_docker(self) -> bool:
        """Connect to Docker daemon with error handling."""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
            return True
        except docker.errors.DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.client = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Docker: {e}")
            self.client = None
            return False

    def _is_docker_available(self) -> bool:
        """Check if Docker daemon is available."""
        if not self.client:
            return self._connect_to_docker()

        try:
            self.client.ping()
            return True
        except:
            logger.warning("Lost connection to Docker daemon, attempting reconnect...")
            return self._connect_to_docker()

    def _check_container_for_claude(self, container) -> Dict[str, Any]:
        """Check if container has Claude activity."""
        claude_indicators = {
            "env_vars": [],
            "processes": [],
            "labels": [],
            "logs_mention": False,
        }

        try:
            # Check environment variables for CLAUDE tokens
            if hasattr(container, "attrs") and container.attrs:
                env_vars = container.attrs.get("Config", {}).get("Env", [])
                for env_var in env_vars:
                    if "claude" in env_var.lower() or "anthropic" in env_var.lower():
                        # Don't log actual token values
                        env_name = env_var.split("=")[0]
                        claude_indicators["env_vars"].append(env_name)

            # Check container labels
            labels = container.labels or {}
            for key, value in labels.items():
                if "claude" in key.lower() or "claude" in str(value).lower():
                    claude_indicators["labels"].append({key: value})

            # Check running processes for 'claude' command
            if container.status == "running":
                try:
                    top_result = container.top()
                    if top_result and "Processes" in top_result:
                        for process in top_result["Processes"]:
                            process_cmd = " ".join(process).lower()
                            if "claude" in process_cmd:
                                claude_indicators["processes"].append(process)
                except docker.errors.APIError:
                    # Container might not support top command
                    pass

            # Check recent logs for Claude mentions
            try:
                logs = container.logs(
                    tail=100, since=int(time.time() - 300)
                )  # Last 5 minutes
                log_text = logs.decode("utf-8", errors="ignore").lower()
                if "claude" in log_text or "anthropic" in log_text:
                    claude_indicators["logs_mention"] = True
            except docker.errors.APIError:
                # Might not have permission to read logs
                pass

        except Exception as e:
            logger.warning(f"Error checking container {container.short_id}: {e}")

        return claude_indicators

    def discover_claude_containers(self) -> Dict[str, Dict]:
        """Discover all containers with Claude activity."""
        if not self._is_docker_available():
            return {}

        claude_containers = {}

        try:
            # Get all containers (running and stopped)
            containers = self.client.containers.list(all=True)

            for container in containers:
                claude_indicators = self._check_container_for_claude(container)

                # Consider container to have Claude activity if any indicator is positive
                has_claude_activity = (
                    len(claude_indicators["env_vars"]) > 0
                    or len(claude_indicators["processes"]) > 0
                    or len(claude_indicators["labels"]) > 0
                    or claude_indicators["logs_mention"]
                )

                if has_claude_activity:
                    claude_containers[container.id] = {
                        "container": container,
                        "name": container.name,
                        "short_id": container.short_id,
                        "status": container.status,
                        "image": container.image.tags[0]
                        if container.image.tags
                        else container.image.id,
                        "claude_indicators": claude_indicators,
                        "created": container.attrs.get("Created"),
                        "started": container.attrs.get("State", {}).get("StartedAt"),
                    }

            self.containers_with_claude = claude_containers
            logger.info(
                f"Found {len(claude_containers)} containers with Claude activity"
            )

        except Exception as e:
            logger.error(f"Error discovering Claude containers: {e}")

        return claude_containers

    def get_container_resources(self, container_id: str) -> Dict[str, Any]:
        """Get resource usage for a specific container."""
        if not self._is_docker_available():
            return {}

        try:
            container = self.client.containers.get(container_id)
            if container.status != "running":
                return {"status": "not_running"}

            # Get container stats
            stats = container.stats(stream=False)

            # Calculate CPU usage percentage
            cpu_usage = 0
            if "cpu_stats" in stats and "precpu_stats" in stats:
                cpu_delta = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_delta = (
                    stats["cpu_stats"]["system_cpu_usage"]
                    - stats["precpu_stats"]["system_cpu_usage"]
                )

                if system_delta > 0 and "online_cpus" in stats["cpu_stats"]:
                    cpu_usage = (
                        (cpu_delta / system_delta)
                        * stats["cpu_stats"]["online_cpus"]
                        * 100
                    )

            # Memory usage
            memory_usage = 0
            memory_limit = 0
            if "memory_stats" in stats:
                memory_usage = stats["memory_stats"].get("usage", 0)
                memory_limit = stats["memory_stats"].get("limit", 0)

            # Network I/O
            network_rx = 0
            network_tx = 0
            if "networks" in stats:
                for interface in stats["networks"].values():
                    network_rx += interface.get("rx_bytes", 0)
                    network_tx += interface.get("tx_bytes", 0)

            # Block I/O
            block_read = 0
            block_write = 0
            if (
                "blkio_stats" in stats
                and "io_service_bytes_recursive" in stats["blkio_stats"]
            ):
                for item in stats["blkio_stats"]["io_service_bytes_recursive"]:
                    if item["op"] == "Read":
                        block_read += item["value"]
                    elif item["op"] == "Write":
                        block_write += item["value"]

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": round(cpu_usage, 2),
                "memory_usage_bytes": memory_usage,
                "memory_limit_bytes": memory_limit,
                "memory_percent": round(
                    (memory_usage / memory_limit * 100) if memory_limit > 0 else 0, 2
                ),
                "network_rx_bytes": network_rx,
                "network_tx_bytes": network_tx,
                "block_read_bytes": block_read,
                "block_write_bytes": block_write,
                "status": "running",
            }

        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return {"status": "not_found"}
        except Exception as e:
            logger.error(f"Error getting resources for container {container_id}: {e}")
            return {"status": "error", "error": str(e)}

    def stream_container_logs(self, container_id: str, callback=None) -> bool:
        """Stream logs from a container and detect Claude mentions."""
        if not self._is_docker_available():
            return False

        try:
            container = self.client.containers.get(container_id)

            def log_streamer():
                try:
                    for log_line in container.logs(stream=True, follow=True, tail=0):
                        log_text = log_line.decode("utf-8", errors="ignore").strip()

                        # Check for Claude mentions
                        claude_mention = bool(
                            re.search(
                                r"\bclaude\b|\banthropics?\b", log_text, re.IGNORECASE
                            )
                        )

                        log_entry = {
                            "container_id": container_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": log_text,
                            "claude_mention": claude_mention,
                        }

                        if callback:
                            callback(log_entry)

                        # Store in metrics if Claude mention
                        if claude_mention:
                            if container_id not in self.metrics:
                                self.metrics[container_id] = defaultdict(list)
                            self.metrics[container_id]["claude_log_mentions"].append(
                                log_entry
                            )

                except Exception as e:
                    logger.error(f"Error streaming logs for {container_id}: {e}")

            # Start log streaming in background thread
            log_thread = threading.Thread(target=log_streamer, daemon=True)
            log_thread.start()
            self.log_streams[container_id] = log_thread

            return True

        except Exception as e:
            logger.error(f"Failed to start log streaming for {container_id}: {e}")
            return False

    def get_claude_processes(self, container_id: str) -> List[Dict]:
        """Get running Claude processes in a container."""
        if not self._is_docker_available():
            return []

        try:
            container = self.client.containers.get(container_id)
            if container.status != "running":
                return []

            claude_processes = []
            top_result = container.top(ps_args="aux")

            if top_result and "Processes" in top_result:
                headers = top_result.get("Titles", [])
                for process in top_result["Processes"]:
                    process_dict = dict(zip(headers, process))
                    command = process_dict.get("COMMAND", "")

                    if "claude" in command.lower():
                        claude_processes.append(
                            {
                                "pid": process_dict.get("PID"),
                                "user": process_dict.get("USER"),
                                "cpu": process_dict.get("%CPU"),
                                "memory": process_dict.get("%MEM"),
                                "command": command,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

            return claude_processes

        except Exception as e:
            logger.error(f"Error getting Claude processes for {container_id}: {e}")
            return []

    def calculate_token_consumption(self, container_id: str) -> Dict[str, Any]:
        """Estimate token consumption based on log analysis."""
        if container_id not in self.metrics:
            return {"estimated_tokens": 0, "method": "no_data"}

        # This is a simplified estimation - in reality, you'd need to parse
        # actual API calls or have instrumentation in the Claude client
        claude_mentions = len(self.metrics[container_id].get("claude_log_mentions", []))

        # Rough estimation: each mention might represent ~100 tokens on average
        estimated_tokens = claude_mentions * 100

        return {
            "estimated_tokens": estimated_tokens,
            "claude_mentions": claude_mentions,
            "method": "log_analysis",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def aggregate_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics across all Claude containers."""
        if not self.containers_with_claude:
            return {"total_containers": 0}

        aggregated = {
            "total_containers": len(self.containers_with_claude),
            "running_containers": 0,
            "total_cpu_percent": 0,
            "total_memory_bytes": 0,
            "total_network_rx_bytes": 0,
            "total_network_tx_bytes": 0,
            "total_estimated_tokens": 0,
            "containers": {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        for container_id, container_info in self.containers_with_claude.items():
            # Get current resources
            resources = self.get_container_resources(container_id)

            # Get Claude processes
            processes = self.get_claude_processes(container_id)

            # Get token consumption estimate
            tokens = self.calculate_token_consumption(container_id)

            container_metrics = {
                "name": container_info["name"],
                "status": container_info["status"],
                "resources": resources,
                "claude_processes": processes,
                "token_consumption": tokens,
                "claude_indicators": container_info["claude_indicators"],
            }

            aggregated["containers"][container_id] = container_metrics

            # Aggregate totals
            if resources.get("status") == "running":
                aggregated["running_containers"] += 1
                aggregated["total_cpu_percent"] += resources.get("cpu_percent", 0)
                aggregated["total_memory_bytes"] += resources.get(
                    "memory_usage_bytes", 0
                )
                aggregated["total_network_rx_bytes"] += resources.get(
                    "network_rx_bytes", 0
                )
                aggregated["total_network_tx_bytes"] += resources.get(
                    "network_tx_bytes", 0
                )

            aggregated["total_estimated_tokens"] += tokens.get("estimated_tokens", 0)

        return aggregated

    def start_monitoring(self, interval: int = 30) -> bool:
        """Start continuous monitoring of Claude containers."""
        if not self._is_docker_available():
            logger.error("Cannot start monitoring: Docker not available")
            return False

        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return True

        def monitor_loop():
            self.monitoring_active = True
            logger.info(f"Started Docker Claude monitoring (interval: {interval}s)")

            while self.monitoring_active:
                try:
                    # Rediscover containers periodically
                    self.discover_claude_containers()

                    # Update metrics for all containers
                    for container_id in self.containers_with_claude.keys():
                        resources = self.get_container_resources(container_id)
                        if container_id not in self.metrics:
                            self.metrics[container_id] = defaultdict(list)
                        self.metrics[container_id]["resource_history"].append(resources)

                        # Keep only last 100 resource measurements
                        if len(self.metrics[container_id]["resource_history"]) > 100:
                            self.metrics[container_id][
                                "resource_history"
                            ] = self.metrics[container_id]["resource_history"][-100:]

                    time.sleep(interval)

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

        return True

    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped Docker Claude monitoring")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Docker monitor."""
        return {
            "docker_connected": self.client is not None,
            "monitoring_active": self.monitoring_active,
            "containers_tracked": len(self.containers_with_claude),
            "log_streams_active": len(self.log_streams),
            "last_discovery": datetime.utcnow().isoformat(),
        }


def main():
    """Example usage of DockerClaudeMonitor."""
    logging.basicConfig(level=logging.INFO)

    monitor = DockerClaudeMonitor()

    # Discover Claude containers
    containers = monitor.discover_claude_containers()
    print(f"Found {len(containers)} containers with Claude activity:")

    for container_id, info in containers.items():
        print(f"  - {info['name']} ({info['short_id']}): {info['status']}")
        print(f"    Image: {info['image']}")
        print(f"    Claude indicators: {info['claude_indicators']}")

    if containers:
        print("\nGetting aggregated metrics...")
        metrics = monitor.aggregate_metrics()
        print(json.dumps(metrics, indent=2, default=str))

        # Start monitoring for demonstration
        print(f"\nStarting monitoring for 60 seconds...")
        monitor.start_monitoring(interval=10)
        time.sleep(60)
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
