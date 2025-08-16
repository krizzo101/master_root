"""
Enhanced Claude Code MCP Server with Fire-and-Forget Pattern

This server implements a decoupled execution model where:
1. Child agents are spawned in independent processes
2. Results are written to a shared directory
3. Parent agent can poll for results without blocking
4. Failures are isolated and don't impact the parent
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from fastmcp import FastMCP

from .job_manager import FireAndForgetJobManager
from .result_collector import ResultCollector
from .config import ServerConfig


logger = logging.getLogger(__name__)


class ClaudeCodeV2Server:
    """Enhanced Claude Code MCP Server with fire-and-forget pattern"""

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.mcp = FastMCP("claude-code-v2")
        self.job_manager = FireAndForgetJobManager(self.config)
        self.result_collector = ResultCollector(self.config)

        # Setup MCP tools
        self._setup_tools()

    def _setup_tools(self):
        """Register MCP tools"""

        @self.mcp.tool()
        async def spawn_agent(
            task: str,
            agent_profile: Optional[str] = None,
            output_dir: Optional[str] = None,
            timeout: int = 600,
            metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Spawn a new agent that runs independently.
            Returns immediately with job ID and result location.
            
            Args:
                task: Task for the agent to perform
                agent_profile: Optional agent profile to use
                output_dir: Optional directory for results
                timeout: Timeout in seconds (default: 600)
                metadata: Optional additional metadata
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
                    "status": "spawning",
                    "spawned_at": datetime.now().isoformat(),
                    "timeout": timeout,
                    "metadata": metadata or {},
                }

                # Spawn agent in background (fire and forget)
                asyncio.create_task(self.job_manager.spawn_agent(job_info))

                # Return immediately
                return {
                    "success": True,
                    "job_id": job_id,
                    "result_location": job_info["result_file"],
                    "message": "Agent spawned successfully. Check result_location for output.",
                    "poll_command": f"collect_results --job_ids {job_id}",
                }

            except Exception as e:
                logger.error(f"Failed to spawn agent: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def spawn_parallel_agents(
            tasks: List[str],
            agent_profile: Optional[str] = None,
            output_dir: Optional[str] = None,
            timeout: int = 600,
        ) -> Dict[str, Any]:
            """
            Spawn multiple agents in parallel.
            All run independently and deposit results in shared directory.
            """
            try:
                output_dir = output_dir or self.config.default_results_dir
                os.makedirs(output_dir, exist_ok=True)

                jobs = []
                for task in tasks:
                    job_id = str(uuid.uuid4())
                    job_info = {
                        "job_id": job_id,
                        "task": task,
                        "agent_profile": agent_profile,
                        "output_dir": output_dir,
                        "result_file": f"{output_dir}/{job_id}.json",
                        "status": "spawning",
                        "spawned_at": datetime.now().isoformat(),
                        "timeout": timeout,
                    }

                    # Spawn each agent
                    asyncio.create_task(self.job_manager.spawn_agent(job_info))

                    jobs.append(
                        {
                            "job_id": job_id,
                            "task": task[:100] + "..." if len(task) > 100 else task,
                            "result_location": job_info["result_file"],
                        }
                    )

                return {
                    "success": True,
                    "total_spawned": len(jobs),
                    "jobs": jobs,
                    "output_directory": output_dir,
                    "message": f"Spawned {len(jobs)} agents. Results will appear in {output_dir}",
                }

            except Exception as e:
                logger.error(f"Failed to spawn parallel agents: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def collect_results(
            job_ids: Optional[List[str]] = None,
            output_dir: Optional[str] = None,
            include_partial: bool = False,
            cleanup: bool = False
        ) -> Dict[str, Any]:
            """
            Collect results from spawned agents.
            Non-blocking - returns whatever is available.
            
            Args:
                job_ids: Optional list of specific job IDs to check
                output_dir: Optional directory to check for results
                include_partial: Include partial results (default: False)
                cleanup: Remove collected results from disk (default: False)
            """
            try:
                output_dir = output_dir or self.config.default_results_dir

                # Collect available results
                results = await self.result_collector.collect(
                    output_dir=output_dir,
                    job_ids=job_ids,
                    include_partial=include_partial,
                )

                # Optionally cleanup
                if cleanup and results["completed"]:
                    for job_id in results["completed"]:
                        result_file = f"{output_dir}/{job_id}.json"
                        if os.path.exists(result_file):
                            os.remove(result_file)

                return {
                    "success": True,
                    "total_found": len(results["completed"])
                    + len(results["partial"])
                    + len(results["failed"]),
                    "completed": len(results["completed"]),
                    "partial": len(results["partial"]),
                    "failed": len(results["failed"]),
                    "pending": len(results["pending"]),
                    "results": results,
                }

            except Exception as e:
                logger.error(f"Failed to collect results: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def check_agent_health(job_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Check health status of spawned agents.
            Can check specific job or all active jobs.
            """
            try:
                if job_id:
                    status = await self.job_manager.check_job_status(job_id)
                    return {"success": True, "job_id": job_id, "status": status}
                else:
                    # Check all active jobs
                    active_jobs = await self.job_manager.get_active_jobs()
                    return {
                        "success": True,
                        "total_active": len(active_jobs),
                        "jobs": active_jobs,
                    }

            except Exception as e:
                logger.error(f"Failed to check agent health: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def kill_agent(job_id: str, cleanup: bool = True) -> Dict[str, Any]:
            """
            Forcefully terminate a spawned agent.
            Optionally cleanup partial results.
            """
            try:
                success = await self.job_manager.kill_job(job_id)

                if success and cleanup:
                    # Remove partial results
                    output_dir = self.config.default_results_dir
                    result_file = f"{output_dir}/{job_id}.json"
                    if os.path.exists(result_file):
                        os.remove(result_file)

                return {
                    "success": success,
                    "job_id": job_id,
                    "message": "Agent terminated"
                    if success
                    else "Agent not found or already terminated",
                }

            except Exception as e:
                logger.error(f"Failed to kill agent: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def aggregate_results(
            output_dir: Optional[str] = None, aggregation_type: str = "summary"
        ) -> Dict[str, Any]:
            """
            Aggregate results from multiple completed agents.
            Useful for synthesizing findings from parallel analyses.
            """
            try:
                output_dir = output_dir or self.config.default_results_dir

                # Collect all completed results
                results = await self.result_collector.collect(
                    output_dir=output_dir, include_partial=False
                )

                if not results["completed"]:
                    return {
                        "success": True,
                        "message": "No completed results to aggregate",
                    }

                # Perform aggregation based on type
                if aggregation_type == "summary":
                    aggregated = self._aggregate_summary(results["results"])
                elif aggregation_type == "merge":
                    aggregated = self._aggregate_merge(results["results"])
                elif aggregation_type == "consensus":
                    aggregated = self._aggregate_consensus(results["results"])
                else:
                    aggregated = results["results"]

                return {
                    "success": True,
                    "total_aggregated": len(results["completed"]),
                    "aggregation_type": aggregation_type,
                    "aggregated_data": aggregated,
                }

            except Exception as e:
                logger.error(f"Failed to aggregate results: {e}")
                return {"success": False, "error": str(e)}

    def _aggregate_summary(self, results: Dict) -> Dict:
        """Create summary aggregation of results"""
        summary = {
            "total_agents": len(results),
            "key_findings": [],
            "common_patterns": [],
            "unique_insights": [],
            "statistics": {},
        }

        for job_id, data in results.items():
            if "completed" in data and data["completed"]:
                result = data["completed"]

                # Extract key findings
                if "summary" in result:
                    summary["key_findings"].append(
                        {"job_id": job_id, "finding": result["summary"]}
                    )

                # Collect metrics
                if "metrics" in result:
                    for key, value in result["metrics"].items():
                        if key not in summary["statistics"]:
                            summary["statistics"][key] = []
                        summary["statistics"][key].append(value)

        return summary

    def _aggregate_merge(self, results: Dict) -> Dict:
        """Merge all results into single structure"""
        merged = {
            "merged_at": datetime.now().isoformat(),
            "sources": [],
            "combined_data": {},
        }

        for job_id, data in results.items():
            if "completed" in data and data["completed"]:
                merged["sources"].append(job_id)
                merged["combined_data"][job_id] = data["completed"]

        return merged

    def _aggregate_consensus(self, results: Dict) -> Dict:
        """Find consensus among agent results"""
        consensus = {
            "agreement_level": 0.0,
            "consensus_items": [],
            "disagreements": [],
            "confidence_scores": {},
        }

        # Simple consensus logic - can be enhanced
        all_findings = []
        for job_id, data in results.items():
            if "completed" in data and data["completed"]:
                if "findings" in data["completed"]:
                    all_findings.extend(data["completed"]["findings"])

        # Count occurrences
        finding_counts = {}
        for finding in all_findings:
            finding_str = json.dumps(finding, sort_keys=True)
            finding_counts[finding_str] = finding_counts.get(finding_str, 0) + 1

        # Determine consensus
        total_agents = len(results)
        for finding_str, count in finding_counts.items():
            agreement_ratio = count / total_agents
            if agreement_ratio > 0.5:
                consensus["consensus_items"].append(
                    {"finding": json.loads(finding_str), "agreement": agreement_ratio}
                )

        return consensus

    async def run(self):
        """Run the MCP server"""
        await self.mcp.run()
