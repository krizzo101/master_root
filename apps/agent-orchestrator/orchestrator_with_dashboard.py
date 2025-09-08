#!/usr/bin/env python3
"""
Orchestrator with Integrated Dashboard
Combines workflow execution with real-time dashboard monitoring
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator
from monitoring.dashboard_server import DashboardServer
from monitoring.metrics_collector import get_global_collector


class IntegratedOrchestratorDashboard:
    """Combined orchestrator and dashboard system"""

    def __init__(
        self,
        dashboard_port: int = 8765,
        dashboard_host: str = "localhost",
        enable_dashboard: bool = True,
    ):
        self.dashboard_port = dashboard_port
        self.dashboard_host = dashboard_host
        self.enable_dashboard = enable_dashboard
        self.dashboard_server: Optional[DashboardServer] = None
        self.orchestrator: Optional[GenericOrchestrator] = None
        self.logger = logging.getLogger(__name__)

    async def start_dashboard(self):
        """Start the dashboard server"""
        if not self.enable_dashboard:
            return

        try:
            self.dashboard_server = DashboardServer(
                host=self.dashboard_host, port=self.dashboard_port
            )
            await self.dashboard_server.start_server()
            self.logger.info(
                f"🚀 Dashboard started on http://{self.dashboard_host}:{self.dashboard_port}"
            )
        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {e}")
            self.dashboard_server = None

    def create_dashboard_callback(self, workflow_name: str):
        """Create dashboard callback for workflow reporting"""
        if not self.dashboard_server:
            return None

        async def dashboard_callback(state_data: Dict[str, Any]):
            """Handle workflow state changes and update dashboard"""
            try:
                event = state_data.get("event")
                collector = get_global_collector()

                if event == "workflow_started":
                    self.logger.info(f"📊 Workflow started: {workflow_name}")
                    if collector:
                        collector.record_workflow_start(
                            workflow_id=state_data.get("workflow_id"),
                            workflow_name=workflow_name,
                        )

                elif event == "workflow_progress":
                    progress = state_data.get("progress_percent", 0)
                    eta = state_data.get("eta_seconds", 0)
                    self.logger.info(f"📈 Progress: {progress}% (ETA: {eta}s)")

                    # Broadcast to WebSocket clients
                    await self.dashboard_server.broadcast_to_websockets(
                        {
                            "type": "workflow_progress",
                            "workflow_name": workflow_name,
                            "progress": progress,
                            "eta": eta,
                            "data": state_data,
                        }
                    )

                elif event == "task_activity":
                    task_id = state_data.get("task_id")
                    activity = state_data.get("activity")
                    duration = state_data.get("duration", 0)

                    if collector:
                        if activity == "started":
                            collector.record_task_start(task_id)
                        elif activity == "completed":
                            collector.record_task_completion(task_id, duration)
                        elif activity == "failed":
                            collector.record_task_failure(
                                task_id, state_data.get("error", "Unknown error")
                            )

                    # Broadcast task activity
                    await self.dashboard_server.broadcast_to_websockets(
                        {
                            "type": "task_activity",
                            "workflow_name": workflow_name,
                            "task_id": task_id,
                            "activity": activity,
                            "duration": duration,
                        }
                    )

                elif event == "workflow_completed":
                    metrics = state_data.get("metrics", {})
                    self.logger.info(f"✅ Workflow completed: {workflow_name}")
                    self.logger.info(f"📊 Metrics: {metrics}")

                    # Broadcast completion
                    await self.dashboard_server.broadcast_to_websockets(
                        {
                            "type": "workflow_completed",
                            "workflow_name": workflow_name,
                            "metrics": metrics,
                        }
                    )

            except Exception as e:
                self.logger.error(f"Dashboard callback error: {e}")

        return dashboard_callback

    async def run_workflow(
        self,
        tasks_file: str,
        output_dir: str,
        workflow_name: Optional[str] = None,
        max_parallel: int = 5,
    ):
        """Run orchestrator workflow with dashboard integration"""

        # Load tasks
        tasks = self.load_tasks_from_file(tasks_file)
        if not tasks:
            self.logger.error("No tasks loaded from file")
            return False

        # Derive workflow name if not provided
        if not workflow_name:
            workflow_name = (
                Path(tasks_file).stem.replace("_tasks", "").replace("_", "-")
            )

        # Create orchestrator with dashboard callback
        dashboard_callback = self.create_dashboard_callback(workflow_name)

        self.orchestrator = GenericOrchestrator(
            output_dir=Path(output_dir),
            max_parallel=max_parallel,
            workflow_name=workflow_name,
            task_file_path=tasks_file,
            enable_dashboard_reporting=True,
            dashboard_state_callback=dashboard_callback,
        )

        self.logger.info(f"🎯 Starting workflow: {workflow_name}")
        self.logger.info(f"📁 Output directory: {output_dir}")
        self.logger.info(f"🔢 Tasks: {len(tasks)} | Max parallel: {max_parallel}")

        try:
            # Execute workflow
            results = await self.orchestrator.run_workflow(tasks)

            # Report final status
            success_count = sum(1 for r in results if r.status == "completed")
            total_count = len(results)

            self.logger.info(
                f"🏁 Workflow completed: {success_count}/{total_count} tasks successful"
            )

            return success_count == total_count

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return False

    def load_tasks_from_file(self, file_path: str) -> list:
        """Load task definitions from a JSON file"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            tasks = []
            for task_data in data.get("tasks", []):
                tasks.append(AgentTask(**task_data))

            return tasks
        except Exception as e:
            self.logger.error(f"Failed to load tasks from {file_path}: {e}")
            return []

    async def run(
        self,
        tasks_file: str,
        output_dir: str = "outputs",
        workflow_name: Optional[str] = None,
        max_parallel: int = 5,
        keep_dashboard_running: bool = False,
    ):
        """Main execution method"""

        try:
            # Start dashboard first
            await self.start_dashboard()

            # Run workflow
            success = await self.run_workflow(
                tasks_file=tasks_file,
                output_dir=output_dir,
                workflow_name=workflow_name,
                max_parallel=max_parallel,
            )

            if keep_dashboard_running:
                self.logger.info("🌐 Dashboard will continue running...")
                self.logger.info(
                    f"🔗 Access at: http://{self.dashboard_host}:{self.dashboard_port}"
                )

                # Keep dashboard running
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("👋 Shutting down...")

            return success

        except KeyboardInterrupt:
            self.logger.info("👋 Interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Orchestrator with Integrated Dashboard"
    )

    parser.add_argument(
        "--tasks-file", required=True, help="JSON file containing task definitions"
    )
    parser.add_argument(
        "--output-dir", default="outputs", help="Output directory for results"
    )
    parser.add_argument("--workflow-name", help="Custom workflow name")
    parser.add_argument(
        "--max-parallel", type=int, default=5, help="Maximum parallel agents"
    )
    parser.add_argument(
        "--dashboard-port", type=int, default=8765, help="Dashboard port"
    )
    parser.add_argument("--dashboard-host", default="localhost", help="Dashboard host")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable dashboard")
    parser.add_argument(
        "--keep-dashboard",
        action="store_true",
        help="Keep dashboard running after workflow completes",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run integrated system
    system = IntegratedOrchestratorDashboard(
        dashboard_port=args.dashboard_port,
        dashboard_host=args.dashboard_host,
        enable_dashboard=not args.no_dashboard,
    )

    success = await system.run(
        tasks_file=args.tasks_file,
        output_dir=args.output_dir,
        workflow_name=args.workflow_name,
        max_parallel=args.max_parallel,
        keep_dashboard_running=args.keep_dashboard,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
