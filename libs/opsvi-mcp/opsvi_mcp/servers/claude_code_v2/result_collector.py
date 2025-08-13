"""
Result Collector for Fire-and-Forget Agents

Collects and aggregates results from independently running agents.
Each agent's result includes its complete sub-agent tree.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .config import ServerConfig


logger = logging.getLogger(__name__)


class ResultCollector:
    """
    Collects results from fire-and-forget agents.

    Results include:
    - Main agent output
    - Complete tree of child agent results
    - Execution metadata and timings
    """

    def __init__(self, config: ServerConfig):
        self.config = config

    async def collect(
        self,
        output_dir: str,
        job_ids: Optional[List[str]] = None,
        include_partial: bool = False,
    ) -> Dict[str, Any]:
        """
        Collect results from specified directory.

        Returns:
            Dictionary with completed, partial, failed, and pending results
        """

        results = {
            "completed": {},
            "partial": {},
            "failed": {},
            "pending": [],
            "results": {},
        }

        try:
            # List all result files in directory
            result_files = []
            status_files = []

            for file in os.listdir(output_dir):
                if file.endswith(".json"):
                    if "_status.json" in file:
                        status_files.append(file)
                    else:
                        result_files.append(file)

            # Filter by job IDs if specified
            if job_ids:
                result_files = [
                    f for f in result_files if any(job_id in f for job_id in job_ids)
                ]
                status_files = [
                    f for f in status_files if any(job_id in f for job_id in job_ids)
                ]

            # Process result files
            for file in result_files:
                file_path = os.path.join(output_dir, file)
                job_id = file.replace(".json", "")

                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                    # Categorize based on status
                    status = data.get("status", "unknown")

                    if status == "completed":
                        results["completed"][job_id] = self._process_completed_result(
                            data
                        )
                        results["results"][job_id] = {"completed": data}

                    elif status == "failed":
                        results["failed"][job_id] = self._process_failed_result(data)
                        results["results"][job_id] = {"failed": data}

                    elif status == "running" and include_partial:
                        results["partial"][job_id] = self._process_partial_result(data)
                        results["results"][job_id] = {"partial": data}

                except Exception as e:
                    logger.error(f"Failed to process result file {file}: {e}")

            # Check status files for pending jobs
            for file in status_files:
                file_path = os.path.join(output_dir, file)
                job_id = file.replace("_status.json", "")

                # Skip if we already have a result for this job
                if job_id in results["completed"] or job_id in results["failed"]:
                    continue

                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                    if data.get("status") == "running":
                        results["pending"].append(
                            {
                                "job_id": job_id,
                                "started_at": data.get("spawned_at"),
                                "task": data.get("task", "")[:100],
                            }
                        )

                except Exception as e:
                    logger.error(f"Failed to process status file {file}: {e}")

            # Add summary statistics
            results["summary"] = self._create_summary(results)

        except Exception as e:
            logger.error(f"Failed to collect results from {output_dir}: {e}")

        return results

    def _process_completed_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a completed agent result including its children"""

        processed = {
            "job_id": data.get("job_id"),
            "status": "completed",
            "duration": self._calculate_duration(
                data.get("started_at"), data.get("completed_at")
            ),
            "output": data.get("output", {}),
            "children_count": len(data.get("children", {})),
            "total_agents": 1 + self._count_total_agents(data.get("children", {})),
        }

        # Extract key findings from output
        if "output" in data:
            output = data["output"]
            if isinstance(output, dict):
                processed["summary"] = output.get("summary", "")
                processed["confidence"] = output.get("details", {}).get("confidence", 0)
                processed["findings"] = output.get("details", {}).get("findings", [])

        # Process children recursively
        if data.get("children"):
            processed["children"] = self._process_children(data["children"])

        return processed

    def _process_failed_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a failed agent result"""

        return {
            "job_id": data.get("job_id"),
            "status": "failed",
            "error": data.get("error", "Unknown error"),
            "traceback": data.get("traceback"),
            "duration": self._calculate_duration(
                data.get("started_at"), data.get("completed_at")
            ),
            "children_completed": len(
                [
                    c
                    for c in data.get("children", {}).values()
                    if c.get("status") == "completed"
                ]
            ),
        }

    def _process_partial_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a partial (still running) agent result"""

        return {
            "job_id": data.get("job_id"),
            "status": "running",
            "started_at": data.get("started_at"),
            "task": data.get("task", "")[:200],
            "children_spawned": len(data.get("children", {})),
        }

    def _process_children(self, children: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively process child agent results"""

        processed = {}

        for child_id, child_data in children.items():
            if isinstance(child_data, dict):
                processed[child_id] = {
                    "status": child_data.get("status"),
                    "output": child_data.get("output"),
                    "children": self._process_children(child_data.get("children", {}))
                    if child_data.get("children")
                    else {},
                }

        return processed

    def _count_total_agents(self, children: Dict[str, Any]) -> int:
        """Count total number of agents in tree"""

        count = len(children)

        for child_data in children.values():
            if isinstance(child_data, dict) and "children" in child_data:
                count += self._count_total_agents(child_data["children"])

        return count

    def _calculate_duration(
        self, start: Optional[str], end: Optional[str]
    ) -> Optional[float]:
        """Calculate duration in seconds"""

        if not start or not end:
            return None

        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            return (end_dt - start_dt).total_seconds()
        except:
            return None

    def _create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary statistics"""

        total_agents = 0
        total_children = 0
        avg_duration = 0
        durations = []

        for job_data in results["completed"].values():
            total_agents += job_data.get("total_agents", 1)
            total_children += job_data.get("children_count", 0)

            if duration := job_data.get("duration"):
                durations.append(duration)

        if durations:
            avg_duration = sum(durations) / len(durations)

        return {
            "total_jobs": len(results["completed"])
            + len(results["failed"])
            + len(results["partial"]),
            "completed": len(results["completed"]),
            "failed": len(results["failed"]),
            "partial": len(results["partial"]),
            "pending": len(results["pending"]),
            "total_agents_spawned": total_agents,
            "total_children": total_children,
            "average_duration": avg_duration,
            "success_rate": len(results["completed"])
            / max(1, len(results["completed"]) + len(results["failed"])),
        }
