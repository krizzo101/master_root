"""
Enhanced Job Manager with Integrated Monitoring
Adds real-time visibility to the fire-and-forget pattern
"""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..claude_code_v3.agent_monitor import (
    AgentHealthMonitor,
    PhaseValidator,
    SessionCaptureAgent,
)
from .job_manager import FireAndForgetJobManager


class MonitoredJobManager(FireAndForgetJobManager):
    """Job manager with integrated monitoring and session capture"""

    def __init__(self, config, enable_monitoring: bool = True):
        super().__init__(config)
        self.enable_monitoring = enable_monitoring

        # Initialize monitoring components
        self.session_dir = Path(config.default_results_dir) / ".agent-sessions"
        self.session_dir.mkdir(exist_ok=True)

        if enable_monitoring:
            self.capture_agent = SessionCaptureAgent(self.session_dir)
            self.health_monitor = AgentHealthMonitor()
            self.validator = PhaseValidator()

        # Track active jobs with monitoring data
        self.monitored_jobs: Dict[str, Dict] = {}

    async def spawn_agent(self, job_info: Dict[str, Any]) -> None:
        """Spawn agent with monitoring"""

        job_id = job_info["job_id"]

        if self.enable_monitoring:
            # Add monitoring wrapper
            await self._spawn_with_monitoring(job_info)
        else:
            # Fall back to original implementation
            await super().spawn_agent(job_info)

    async def _spawn_with_monitoring(self, job_info: Dict[str, Any]) -> None:
        """Spawn agent with full monitoring and session capture"""

        job_id = job_info["job_id"]
        task = job_info["task"]
        output_dir = job_info["output_dir"]
        timeout = job_info.get("timeout", 600)

        # Create monitoring entry
        self.monitored_jobs[job_id] = {
            "job_info": job_info,
            "started_at": datetime.now(),
            "status": "initializing",
            "session": None,
            "health": None,
        }

        try:
            # Update status
            job_info["status"] = "spawning"
            self._update_monitoring_status(job_id, "spawning")

            # Build agent command (from parent's perspective)
            cmd = self._build_agent_command(job_info)

            # Log the command for debugging
            self.logger.info(f"[{job_id}] Spawning with monitoring: {' '.join(cmd)}")

            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=output_dir,
            )

            # Update status
            job_info["status"] = "running"
            job_info["pid"] = process.pid
            self._update_monitoring_status(job_id, "running", {"pid": process.pid})

            # Capture session with monitoring
            session = await self.capture_agent.capture_session_stream(
                process=process,
                job_id=job_id,
                phase="execution",  # V2 doesn't have phases like V3
                timeout=timeout,
            )

            # Store session data
            self.monitored_jobs[job_id]["session"] = session

            # Perform health check
            health = await self.health_monitor.check_health(session)
            self.monitored_jobs[job_id]["health"] = health

            # Determine final status
            if session.get("status") == "timeout":
                job_info["status"] = "timeout"
                job_info["error"] = f"Agent timed out after {timeout}s"
            elif session.get("status") == "error":
                job_info["status"] = "failed"
                job_info["error"] = session.get("error", "Unknown error")
            elif process.returncode == 0:
                job_info["status"] = "completed"
            else:
                job_info["status"] = "failed"
                job_info["error"] = f"Process exited with code {process.returncode}"

            # Add monitoring data to result
            job_info["monitoring"] = {
                "session_id": session.get("job_id"),
                "duration_seconds": session.get("duration_seconds"),
                "lines_captured": session.get("total_lines"),
                "errors_detected": len(session.get("errors", [])),
                "files_created": session.get("files_created", []),
                "health_status": health.get("status"),
                "recommendations": health.get("recommendations", []),
            }

            # Save enhanced result
            job_info["completed_at"] = datetime.now().isoformat()
            result_file = Path(job_info["result_file"])

            with open(result_file, "w") as f:
                json.dump(job_info, f, indent=2)

            self.logger.info(
                f"[{job_id}] Completed with monitoring. Status: {job_info['status']}"
            )

            # Save monitoring report
            monitoring_report = self._generate_monitoring_report(job_id)
            report_file = result_file.parent / f"{job_id}_monitoring.json"
            with open(report_file, "w") as f:
                json.dump(monitoring_report, f, indent=2)

        except Exception as e:
            self.logger.error(f"[{job_id}] Monitoring failed: {e}")
            job_info["status"] = "error"
            job_info["error"] = str(e)

            # Still try to save result
            try:
                with open(job_info["result_file"], "w") as f:
                    json.dump(job_info, f, indent=2)
            except:
                pass

        finally:
            # Clean up monitoring entry after some time
            await asyncio.sleep(300)  # Keep for 5 minutes
            if job_id in self.monitored_jobs:
                del self.monitored_jobs[job_id]

    def _update_monitoring_status(
        self, job_id: str, status: str, data: Optional[Dict] = None
    ):
        """Update monitoring status for a job"""
        if job_id in self.monitored_jobs:
            self.monitored_jobs[job_id]["status"] = status
            self.monitored_jobs[job_id]["last_updated"] = datetime.now().isoformat()
            if data:
                self.monitored_jobs[job_id].update(data)

    def _generate_monitoring_report(self, job_id: str) -> Dict[str, Any]:
        """Generate comprehensive monitoring report for a job"""

        if job_id not in self.monitored_jobs:
            return {"error": "Job not found in monitoring"}

        job_data = self.monitored_jobs[job_id]
        session = job_data.get("session", {})
        health = job_data.get("health", {})

        report = {
            "job_id": job_id,
            "generated_at": datetime.now().isoformat(),
            "execution_summary": {
                "task": job_data["job_info"].get("task"),
                "duration_seconds": session.get("duration_seconds", 0),
                "status": session.get("status"),
                "lines_processed": session.get("total_lines", 0),
            },
            "outputs": {
                "files_created": session.get("files_created", []),
                "files_read": session.get("files_read", []),
                "tools_used": session.get("tools_used", []),
                "mcp_servers": session.get("mcp_servers", []),
            },
            "issues": {
                "errors": session.get("errors", []),
                "warnings": session.get("warnings", []),
                "error_rate": len(session.get("errors", []))
                / max(session.get("total_lines", 1), 1),
            },
            "health_assessment": {
                "status": health.get("status"),
                "metrics": health.get("metrics", {}),
                "issues": health.get("issues", []),
                "recommendations": health.get("recommendations", []),
            },
            "session_location": str(self.session_dir / "execution" / job_id),
        }

        return report

    async def get_monitoring_status(
        self, job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get current monitoring status for jobs"""

        if job_id:
            if job_id in self.monitored_jobs:
                return {"success": True, "job": self.monitored_jobs[job_id]}
            else:
                return {"success": False, "error": "Job not found in active monitoring"}
        else:
            # Return all monitored jobs
            return {
                "success": True,
                "active_jobs": len(self.monitored_jobs),
                "jobs": {
                    jid: {
                        "status": job["status"],
                        "task": job["job_info"].get("task", "")[:100],
                        "duration": (datetime.now() - job["started_at"]).total_seconds()
                        if job.get("started_at")
                        else 0,
                    }
                    for jid, job in self.monitored_jobs.items()
                },
            }

    async def get_session_analysis(self, job_id: str) -> Dict[str, Any]:
        """Get detailed session analysis for a completed job"""

        # Try to load from monitoring data first
        if job_id in self.monitored_jobs:
            return self._generate_monitoring_report(job_id)

        # Try to load from saved report
        report_file = (
            Path(self.config.default_results_dir) / f"{job_id}_monitoring.json"
        )
        if report_file.exists():
            with open(report_file) as f:
                return json.load(f)

        # Try to reconstruct from session files
        session_dir = self.session_dir / "execution" / job_id
        if session_dir.exists():
            summary_file = session_dir / "session_summary.json"
            if summary_file.exists():
                with open(summary_file) as f:
                    session = json.load(f)

                # Run health check
                health = await self.health_monitor.check_health(session)

                return {
                    "job_id": job_id,
                    "session": session,
                    "health": health,
                    "reconstructed": True,
                }

        return {"error": "No monitoring data found for job", "job_id": job_id}
