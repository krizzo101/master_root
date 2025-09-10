#!/usr/bin/env python3
"""
Mock Orchestrator Server for Testing

Provides a mock implementation of the orchestrator API for testing
DPO functionality without requiring the full orchestrator system.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)


@dataclass
class MockWorkflowExecution:
    """Mock workflow execution state"""

    workflow_id: str
    status: str = "submitted"
    progress: float = 0.0
    start_time: float = field(default_factory=time.time)
    phases: List[Dict] = field(default_factory=list)
    agents: Dict = field(default_factory=dict)
    outputs: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class MockOrchestratorServer:
    """Mock orchestrator server for testing"""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.workflows: Dict[str, MockWorkflowExecution] = {}
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""
        self.app.router.add_post("/api/v1/workflows", self.submit_workflow)
        self.app.router.add_get(
            "/api/v1/workflows/{workflow_id}/status", self.get_workflow_status
        )
        self.app.router.add_get(
            "/api/v1/workflows/{workflow_id}/results", self.get_workflow_results
        )
        self.app.router.add_delete(
            "/api/v1/workflows/{workflow_id}", self.cancel_workflow
        )
        self.app.router.add_get("/api/v1/workflows", self.list_workflows)
        self.app.router.add_get("/health", self.health_check)

    async def start(self):
        """Start the mock server"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        logger.info(f"Mock orchestrator server started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the mock server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

        logger.info("Mock orchestrator server stopped")

    async def submit_workflow(self, request: web.Request) -> web.Response:
        """Submit a new workflow"""
        try:
            data = await request.json()

            # Generate workflow ID if not provided
            workflow_id = data.get("workflow_id", f"mock_{uuid.uuid4().hex[:8]}")

            # Create mock execution
            execution = MockWorkflowExecution(
                workflow_id=workflow_id,
                status="submitted",
                phases=data.get("phases", []),
                agents=self._count_agents(data.get("phases", [])),
            )

            self.workflows[workflow_id] = execution

            # Start mock execution
            asyncio.create_task(self._simulate_execution(workflow_id))

            response = {
                "workflow_id": workflow_id,
                "status": "submitted",
                "output_dir": f"/mock/output/{workflow_id}",
                "submission_time": time.time(),
            }

            return web.json_response(response, status=201)

        except Exception as e:
            logger.error(f"Error submitting workflow: {e}")
            return web.json_response(
                {"error": f"Failed to submit workflow: {str(e)}"}, status=400
            )

    async def get_workflow_status(self, request: web.Request) -> web.Response:
        """Get workflow status"""
        workflow_id = request.match_info["workflow_id"]

        if workflow_id not in self.workflows:
            return web.json_response({"error": "Workflow not found"}, status=404)

        execution = self.workflows[workflow_id]

        response = {
            "workflow_id": workflow_id,
            "status": execution.status,
            "progress": execution.progress,
            "start_time": execution.start_time,
            "current_phase": self._get_current_phase(execution),
            "agents": {
                "total": execution.agents.get("total", 0),
                "completed": execution.agents.get("completed", 0),
                "running": execution.agents.get("running", 0),
                "pending": execution.agents.get("pending", 0),
            },
            "errors": execution.errors,
        }

        return web.json_response(response)

    async def get_workflow_results(self, request: web.Request) -> web.Response:
        """Get workflow results"""
        workflow_id = request.match_info["workflow_id"]

        if workflow_id not in self.workflows:
            return web.json_response({"error": "Workflow not found"}, status=404)

        execution = self.workflows[workflow_id]

        if execution.status not in ["completed", "failed", "cancelled"]:
            return web.json_response({"error": "Workflow not finished"}, status=400)

        response = {
            "workflow_id": workflow_id,
            "status": execution.status,
            "outputs": execution.outputs,
            "artifacts": self._generate_mock_artifacts(execution),
            "metrics": {
                "duration": time.time() - execution.start_time,
                "agents_used": execution.agents.get("total", 0),
                "phases_completed": len(
                    [p for p in execution.phases if p.get("status") == "completed"]
                ),
            },
        }

        return web.json_response(response)

    async def cancel_workflow(self, request: web.Request) -> web.Response:
        """Cancel a workflow"""
        workflow_id = request.match_info["workflow_id"]

        if workflow_id not in self.workflows:
            return web.json_response({"error": "Workflow not found"}, status=404)

        execution = self.workflows[workflow_id]

        if execution.status in ["completed", "failed", "cancelled"]:
            return web.json_response({"error": "Workflow already finished"}, status=400)

        execution.status = "cancelled"

        response = {
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Workflow cancelled successfully",
        }

        return web.json_response(response)

    async def list_workflows(self, request: web.Request) -> web.Response:
        """List all workflows"""
        workflows = []

        for workflow_id, execution in self.workflows.items():
            workflows.append(
                {
                    "workflow_id": workflow_id,
                    "status": execution.status,
                    "progress": execution.progress,
                    "start_time": execution.start_time,
                    "agents": execution.agents.get("total", 0),
                }
            )

        response = {"workflows": workflows, "total": len(workflows)}

        return web.json_response(response)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response(
            {"status": "healthy", "timestamp": time.time(), "version": "mock-1.0.0"}
        )

    async def _simulate_execution(self, workflow_id: str):
        """Simulate workflow execution"""
        execution = self.workflows[workflow_id]

        try:
            # Simulate phases
            phases = execution.phases
            total_phases = len(phases)

            if total_phases == 0:
                # Default phases for testing
                phases = [
                    {"phase_id": "discovery", "phase_name": "Discovery"},
                    {"phase_id": "implementation", "phase_name": "Implementation"},
                    {"phase_id": "testing", "phase_name": "Testing"},
                ]
                execution.phases = phases
                total_phases = len(phases)

            execution.status = "running"
            execution.agents = {
                "total": self._count_agents(phases).get("total", 3),
                "completed": 0,
                "running": 1,
                "pending": self._count_agents(phases).get("total", 3) - 1,
            }

            # Simulate phase execution
            for i, phase in enumerate(phases):
                if execution.status == "cancelled":
                    return

                phase["status"] = "running"
                phase["start_time"] = time.time()

                # Simulate phase duration
                phase_duration = 2.0 + (i * 1.0)  # Varying duration
                await asyncio.sleep(phase_duration)

                if execution.status == "cancelled":
                    phase["status"] = "cancelled"
                    return

                phase["status"] = "completed"
                phase["end_time"] = time.time()

                # Update progress
                execution.progress = (i + 1) / total_phases

                # Update agent counts
                agents_this_phase = len(phase.get("agents", [{"role": "default"}]))
                execution.agents["completed"] += agents_this_phase
                if i < total_phases - 1:
                    execution.agents["running"] = len(
                        phases[i + 1].get("agents", [{"role": "default"}])
                    )
                else:
                    execution.agents["running"] = 0
                execution.agents["pending"] = max(
                    0,
                    execution.agents["total"]
                    - execution.agents["completed"]
                    - execution.agents["running"],
                )

            # Complete execution
            execution.status = "completed"
            execution.progress = 1.0
            execution.outputs = self._generate_mock_outputs(execution)

            logger.info(f"Mock workflow {workflow_id} completed successfully")

        except Exception as e:
            execution.status = "failed"
            execution.errors.append(f"Execution failed: {str(e)}")
            logger.error(f"Mock workflow {workflow_id} failed: {e}")

    def _count_agents(self, phases: List[Dict]) -> Dict[str, int]:
        """Count total agents in workflow"""
        total = 0
        for phase in phases:
            total += len(phase.get("agents", [{"role": "default"}]))

        return {"total": total, "completed": 0, "running": 0, "pending": total}

    def _get_current_phase(self, execution: MockWorkflowExecution) -> Optional[str]:
        """Get current phase name"""
        for phase in execution.phases:
            if phase.get("status") == "running":
                return phase.get("phase_name", phase.get("phase_id", "unknown"))

        # If no running phase, return last completed or first pending
        completed_phases = [
            p for p in execution.phases if p.get("status") == "completed"
        ]
        if completed_phases:
            return f"After {completed_phases[-1].get('phase_name', 'unknown')}"

        pending_phases = [p for p in execution.phases if p.get("status") != "completed"]
        if pending_phases:
            return f"Starting {pending_phases[0].get('phase_name', 'unknown')}"

        return None

    def _generate_mock_outputs(self, execution: MockWorkflowExecution) -> Dict:
        """Generate mock outputs for completed workflow"""
        return {
            "deliverables": [
                f"Mock deliverable {i+1}" for i in range(len(execution.phases))
            ],
            "documentation": [
                "API specification",
                "Architecture documentation",
                "User guide",
            ],
            "artifacts": self._generate_mock_artifacts(execution),
        }

    def _generate_mock_artifacts(self, execution: MockWorkflowExecution) -> List[Dict]:
        """Generate mock artifacts"""
        artifacts = []

        for i, phase in enumerate(execution.phases):
            artifacts.extend(
                [
                    {
                        "type": "documentation",
                        "name": f"{phase.get('phase_name', 'Phase')} Documentation",
                        "path": f"/mock/output/{execution.workflow_id}/phase_{i+1}_docs.md",
                        "size": 1024 * (i + 1),
                    },
                    {
                        "type": "code"
                        if "implementation" in phase.get("phase_name", "").lower()
                        else "document",
                        "name": f"{phase.get('phase_name', 'Phase')} Output",
                        "path": f"/mock/output/{execution.workflow_id}/phase_{i+1}_output",
                        "size": 2048 * (i + 1),
                    },
                ]
            )

        return artifacts


class MockOrchestratorClient:
    """Mock orchestrator client for unit testing"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.workflows: Dict[str, MockWorkflowExecution] = {}

    async def submit_workflow(self, workflow: Dict) -> Dict:
        """Submit workflow (mock implementation)"""
        workflow_id = workflow.get("workflow_id", f"client_mock_{uuid.uuid4().hex[:8]}")

        execution = MockWorkflowExecution(
            workflow_id=workflow_id,
            status="submitted",
            phases=workflow.get("phases", []),
        )

        self.workflows[workflow_id] = execution

        return {
            "workflow_id": workflow_id,
            "status": "submitted",
            "output_dir": f"/mock/client/{workflow_id}",
        }

    async def get_status(self, workflow_id: str) -> Dict:
        """Get workflow status (mock implementation)"""
        if workflow_id not in self.workflows:
            raise Exception(f"Workflow {workflow_id} not found")

        execution = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "status": execution.status,
            "progress": execution.progress,
            "agents": asdict(execution.agents)
            if hasattr(execution.agents, "__dict__")
            else execution.agents,
        }

    async def get_results(self, workflow_id: str) -> Dict:
        """Get workflow results (mock implementation)"""
        if workflow_id not in self.workflows:
            raise Exception(f"Workflow {workflow_id} not found")

        execution = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "status": execution.status,
            "outputs": execution.outputs,
            "artifacts": [],
        }

    async def cancel_workflow(self, workflow_id: str) -> Dict:
        """Cancel workflow (mock implementation)"""
        if workflow_id not in self.workflows:
            raise Exception(f"Workflow {workflow_id} not found")

        execution = self.workflows[workflow_id]
        execution.status = "cancelled"

        return {"workflow_id": workflow_id, "status": "cancelled"}
