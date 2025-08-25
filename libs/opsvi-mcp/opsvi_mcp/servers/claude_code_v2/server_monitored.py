"""
Enhanced Claude Code V2 Server with Integrated Monitoring
Provides full visibility into fire-and-forget agent execution
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .config import ServerConfig
from .monitored_job_manager import MonitoredJobManager
from .result_collector import ResultCollector

logger = logging.getLogger(__name__)


class MonitoredClaudeCodeV2Server:
    """V2 Server with integrated monitoring and session capture"""

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.mcp = FastMCP("claude-code-v2-monitored")

        # Use monitored job manager
        self.job_manager = MonitoredJobManager(self.config, enable_monitoring=True)
        self.result_collector = ResultCollector(self.config)

        # Setup enhanced MCP tools
        self._setup_tools()

    def _setup_tools(self):
        """Register enhanced MCP tools with monitoring capabilities"""

        @self.mcp.tool()
        async def spawn_monitored_agent(
            task: str,
            agent_profile: Optional[str] = None,
            output_dir: Optional[str] = None,
            timeout: int = 600,
            enable_monitoring: bool = True,
            metadata: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """
            Spawn an agent with full monitoring and session capture.
            Returns immediately with job ID and monitoring endpoints.

            Args:
                task: Task for the agent to perform
                agent_profile: Optional agent profile to use
                output_dir: Optional directory for results
                timeout: Timeout in seconds (default: 600)
                enable_monitoring: Enable real-time monitoring (default: True)
                metadata: Optional additional metadata

            Returns:
                Job information including monitoring endpoints
            """
            try:
                # Generate unique job ID
                job_id = str(uuid.uuid4())

                # Determine output directory
                output_dir = output_dir or self.config.default_results_dir
                os.makedirs(output_dir, exist_ok=True)

                # Create job info
                job_info = {
                    "job_id": job_id,
                    "task": task,
                    "agent_profile": agent_profile,
                    "output_dir": output_dir,
                    "result_file": f"{output_dir}/{job_id}.json",
                    "monitoring_file": f"{output_dir}/{job_id}_monitoring.json",
                    "session_dir": f"{output_dir}/.agent-sessions/execution/{job_id}",
                    "status": "spawning",
                    "spawned_at": datetime.now().isoformat(),
                    "timeout": timeout,
                    "monitoring_enabled": enable_monitoring,
                    "metadata": metadata or {},
                }

                # Spawn agent with monitoring
                asyncio.create_task(self.job_manager.spawn_agent(job_info))

                # Return immediately with monitoring info
                return {
                    "success": True,
                    "job_id": job_id,
                    "result_location": job_info["result_file"],
                    "monitoring_location": job_info["monitoring_file"],
                    "session_location": job_info["session_dir"],
                    "message": "Agent spawned with monitoring. Check locations for output.",
                    "commands": {
                        "check_status": f"get_agent_status --job_id {job_id}",
                        "get_results": f"collect_results --job_ids {job_id}",
                        "view_session": f"analyze_session --job_id {job_id}",
                        "live_monitor": f"monitor_agent --job_id {job_id}",
                    },
                }

            except Exception as e:
                logger.error(f"Failed to spawn monitored agent: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def spawn_parallel_monitored_agents(
            tasks: List[str],
            output_dir: Optional[str] = None,
            timeout: int = 600,
            max_concurrent: int = 5,
            enable_monitoring: bool = True,
        ) -> Dict[str, Any]:
            """
            Spawn multiple agents in parallel with monitoring.
            Each agent gets independent monitoring and session capture.

            Args:
                tasks: List of tasks to execute in parallel
                output_dir: Optional directory for results
                timeout: Timeout per agent in seconds
                max_concurrent: Maximum concurrent agents
                enable_monitoring: Enable monitoring for all agents

            Returns:
                Summary with all job IDs and monitoring endpoints
            """
            output_dir = output_dir or self.config.default_results_dir
            os.makedirs(output_dir, exist_ok=True)

            jobs = []
            semaphore = asyncio.Semaphore(max_concurrent)

            async def spawn_with_limit(task: str, index: int):
                async with semaphore:
                    result = await spawn_monitored_agent(
                        task=task,
                        output_dir=output_dir,
                        timeout=timeout,
                        enable_monitoring=enable_monitoring,
                        metadata={"batch_index": index, "total_tasks": len(tasks)},
                    )
                    return result

            # Spawn all agents
            spawn_tasks = [spawn_with_limit(task, i) for i, task in enumerate(tasks)]

            results = await asyncio.gather(*spawn_tasks, return_exceptions=True)

            # Collect job IDs
            successful_jobs = []
            failed_spawns = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_spawns.append({"task_index": i, "error": str(result)})
                elif result.get("success"):
                    successful_jobs.append(
                        {
                            "job_id": result["job_id"],
                            "task": tasks[i][:100],
                            "locations": {
                                "result": result["result_location"],
                                "monitoring": result.get("monitoring_location"),
                                "session": result.get("session_location"),
                            },
                        }
                    )
                else:
                    failed_spawns.append(
                        {"task_index": i, "error": result.get("error")}
                    )

            # Create monitoring dashboard
            dashboard_file = f"{output_dir}/batch_dashboard.json"
            dashboard = {
                "batch_id": str(uuid.uuid4()),
                "created_at": datetime.now().isoformat(),
                "total_tasks": len(tasks),
                "successful_spawns": len(successful_jobs),
                "failed_spawns": len(failed_spawns),
                "jobs": successful_jobs,
                "failures": failed_spawns,
                "monitoring_enabled": enable_monitoring,
            }

            with open(dashboard_file, "w") as f:
                json.dump(dashboard, f, indent=2)

            return {
                "success": True,
                "batch_id": dashboard["batch_id"],
                "spawned": len(successful_jobs),
                "failed": len(failed_spawns),
                "dashboard_location": dashboard_file,
                "jobs": successful_jobs,
                "message": f"Spawned {len(successful_jobs)}/{len(tasks)} agents with monitoring",
            }

        @self.mcp.tool()
        async def get_agent_status(job_id: str) -> Dict[str, Any]:
            """
            Get current status and monitoring data for an agent.

            Args:
                job_id: The job ID to check

            Returns:
                Current status with monitoring metrics
            """
            return await self.job_manager.get_monitoring_status(job_id)

        @self.mcp.tool()
        async def monitor_agent(job_id: str) -> Dict[str, Any]:
            """
            Get live monitoring data for a running agent.
            Shows real-time progress, errors, and outputs.

            Args:
                job_id: The job ID to monitor

            Returns:
                Live monitoring data
            """
            status = await self.job_manager.get_monitoring_status(job_id)

            if not status.get("success"):
                return status

            job_data = status.get("job", {})
            session = job_data.get("session", {})

            return {
                "success": True,
                "job_id": job_id,
                "status": job_data.get("status"),
                "progress": session.get("progress", 0),
                "duration_seconds": (
                    datetime.now()
                    - datetime.fromisoformat(
                        job_data.get("started_at", datetime.now().isoformat())
                    )
                ).total_seconds()
                if job_data.get("started_at")
                else 0,
                "current_action": session.get("current_status", "processing"),
                "metrics": {
                    "lines_processed": session.get("total_lines", 0),
                    "errors_detected": len(session.get("errors", [])),
                    "files_created": len(session.get("files_created", [])),
                    "tools_used": len(session.get("tools_used", [])),
                },
                "recent_errors": session.get("errors", [])[-5:],
                "recent_files": session.get("files_created", [])[-5:],
            }

        @self.mcp.tool()
        async def analyze_session(job_id: str) -> Dict[str, Any]:
            """
            Get detailed analysis of an agent session.
            Includes health assessment, recommendations, and full metrics.

            Args:
                job_id: The job ID to analyze

            Returns:
                Comprehensive session analysis
            """
            return await self.job_manager.get_session_analysis(job_id)

        @self.mcp.tool()
        async def get_all_monitoring_status() -> Dict[str, Any]:
            """
            Get monitoring status for all active agents.

            Returns:
                Dashboard of all monitored agents
            """
            return await self.job_manager.get_monitoring_status()

        # Keep original tools for compatibility
        @self.mcp.tool()
        async def spawn_agent(
            task: str,
            agent_profile: Optional[str] = None,
            output_dir: Optional[str] = None,
            timeout: int = 600,
            metadata: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """
            Original spawn_agent tool (now with monitoring by default).
            """
            return await spawn_monitored_agent(
                task=task,
                agent_profile=agent_profile,
                output_dir=output_dir,
                timeout=timeout,
                enable_monitoring=True,
                metadata=metadata,
            )

        @self.mcp.tool()
        async def collect_results(
            job_ids: List[str], wait_for_completion: bool = False, max_wait: int = 60
        ) -> Dict[str, Any]:
            """
            Collect results from completed agents with monitoring data.
            """
            results = await self.result_collector.collect_results(
                job_ids, wait_for_completion, max_wait
            )

            # Enhance with monitoring data
            for job_id in job_ids:
                if job_id in results.get("results", {}):
                    analysis = await self.job_manager.get_session_analysis(job_id)
                    if not analysis.get("error"):
                        results["results"][job_id]["monitoring"] = analysis

            return results

    async def serve(self):
        """Start the MCP server"""
        await self.mcp.run()


def main():
    """Main entry point"""
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    config = ServerConfig()
    server = MonitoredClaudeCodeV2Server(config)

    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("\nServer stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
