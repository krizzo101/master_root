#!/usr/bin/env python3
"""
DPO Orchestrator Integration Layer

Connects the Development Process Orchestrator (DPO) system with the GenericOrchestrator
for seamless workflow submission, monitoring, and results harvesting.

This module provides:
- Workflow submission from DPO to orchestrator
- Real-time progress monitoring with WebSocket support
- Results harvesting and knowledge extraction
- Checkpoint/resume capability
- Dashboard integration

Author: Agent Orchestrator Team
Date: September 2025
"""

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .dpo_intelligence_integration import (
    DPOIntelligenceIntegration,
    DPORequest,
    EnhancedDPOWorkflow,
)

# Import core components
from .generic_orchestrator import AgentTask, GenericOrchestrator
from .sdlc_template_system import SDLCTemplateSystem
from .specialist_agent_templates import SpecialistAgentTemplates

# Try to import WebSocket support
try:
    import websockets
    from websockets.server import WebSocketServerProtocol

    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    WebSocketServerProtocol = None

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""

    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowSubmission:
    """Represents a workflow submission to the orchestrator"""

    workflow_id: str
    dpo_request: DPORequest
    enhanced_workflow: EnhancedDPOWorkflow
    orchestrator_tasks: List[AgentTask]
    submission_time: datetime
    status: WorkflowStatus
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["status"] = self.status.value
        data["submission_time"] = self.submission_time.isoformat()
        return data


@dataclass
class WorkflowProgress:
    """Real-time workflow execution progress"""

    workflow_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: List[str]
    current_phase: str
    progress_percentage: float
    estimated_completion: Optional[datetime]
    last_update: datetime

    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "running_tasks": self.running_tasks,
            "current_phase": self.current_phase,
            "progress_percentage": self.progress_percentage,
            "estimated_completion": self.estimated_completion.isoformat()
            if self.estimated_completion
            else None,
            "last_update": self.last_update.isoformat(),
        }


@dataclass
class WorkflowResults:
    """Workflow execution results and deliverables"""

    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    task_results: List[Dict]
    deliverables: List[str]
    extracted_knowledge: List[Dict]
    metrics: Dict[str, Any]
    errors: List[str]

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["status"] = self.status.value
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat()
        return data


class DPOOrchestrator:
    """
    Main integration layer between DPO and GenericOrchestrator

    Provides complete workflow lifecycle management from DPO request
    to orchestrator execution and results harvesting.
    """

    def __init__(
        self,
        output_base_dir: str = "output/dpo_workflows",
        max_parallel_agents: int = 10,
        enable_websocket: bool = True,
        websocket_port: int = 8765,
        dashboard_callback: Optional[Callable] = None,
    ):
        """
        Initialize DPO Orchestrator Integration

        Args:
            output_base_dir: Base directory for workflow outputs
            max_parallel_agents: Maximum parallel agent execution
            enable_websocket: Enable WebSocket for real-time updates
            websocket_port: Port for WebSocket server
            dashboard_callback: Callback for dashboard integration
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

        self.max_parallel_agents = max_parallel_agents
        self.enable_websocket = enable_websocket and WEBSOCKET_AVAILABLE
        self.websocket_port = websocket_port
        self.dashboard_callback = dashboard_callback

        # Initialize components
        self.dpo_intelligence = DPOIntelligenceIntegration(
            output_dir=str(self.output_base_dir / "intelligence")
        )
        self.template_system = SDLCTemplateSystem()
        self.specialist_templates = SpecialistAgentTemplates()

        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowSubmission] = {}
        self.workflow_progress: Dict[str, WorkflowProgress] = {}
        self.workflow_results: Dict[str, WorkflowResults] = {}

        # WebSocket connections for real-time updates
        self.websocket_clients: List[WebSocketServerProtocol] = []
        self.websocket_server = None

        # Start WebSocket server if enabled
        if self.enable_websocket:
            asyncio.create_task(self._start_websocket_server())

        logger.info(
            f"DPO Orchestrator initialized with output dir: {self.output_base_dir}"
        )

    async def submit_development_request(
        self,
        request: str,
        project_type: str = "web_app",
        complexity: str = "moderate",
        context: Optional[Dict] = None,
    ) -> str:
        """
        Submit a development request to the DPO system

        Args:
            request: Natural language development request
            project_type: Type of project (web_app, api, cli, library, integration)
            complexity: Complexity level (simple, moderate, complex)
            context: Additional project context

        Returns:
            Workflow ID for tracking
        """
        # Create DPO request
        dpo_request = DPORequest(
            request_id=str(uuid.uuid4()),
            user_request=request,
            project_type=project_type,
            complexity_level=complexity,
            project_context=context or {},
            constraints={"max_agents": self.max_parallel_agents, "timeline": "normal"},
            enhancement_preferences={
                "prioritize_quality": True,
                "prioritize_innovation": complexity == "complex",
            },
        )

        # Process through DPO Intelligence
        logger.info(f"Processing DPO request: {dpo_request.request_id}")
        enhanced_workflow = await self.dpo_intelligence.process_dpo_request(dpo_request)

        # Convert to orchestrator tasks
        orchestrator_tasks = await self._convert_to_orchestrator_tasks(
            enhanced_workflow
        )

        # Create workflow submission
        workflow_submission = WorkflowSubmission(
            workflow_id=enhanced_workflow.workflow_id,
            dpo_request=dpo_request,
            enhanced_workflow=enhanced_workflow,
            orchestrator_tasks=orchestrator_tasks,
            submission_time=datetime.now(),
            status=WorkflowStatus.PENDING,
            metadata={
                "total_phases": len(enhanced_workflow.workflow_phases),
                "total_tasks": len(orchestrator_tasks),
                "estimated_duration": enhanced_workflow.estimated_timeline[
                    "total_duration"
                ],
            },
        )

        # Track workflow
        self.active_workflows[workflow_submission.workflow_id] = workflow_submission

        # Initialize progress tracking
        self.workflow_progress[workflow_submission.workflow_id] = WorkflowProgress(
            workflow_id=workflow_submission.workflow_id,
            total_tasks=len(orchestrator_tasks),
            completed_tasks=0,
            failed_tasks=0,
            running_tasks=[],
            current_phase="initializing",
            progress_percentage=0.0,
            estimated_completion=None,
            last_update=datetime.now(),
        )

        # Submit to orchestrator
        asyncio.create_task(self._execute_workflow(workflow_submission))

        # Notify dashboard
        if self.dashboard_callback:
            self.dashboard_callback(
                {
                    "event": "workflow_submitted",
                    "workflow_id": workflow_submission.workflow_id,
                    "request": request,
                    "project_type": project_type,
                    "complexity": complexity,
                    "total_tasks": len(orchestrator_tasks),
                }
            )

        # Broadcast to WebSocket clients
        await self._broadcast_update(
            {
                "type": "workflow_submitted",
                "workflow_id": workflow_submission.workflow_id,
                "status": "pending",
                "metadata": workflow_submission.metadata,
            }
        )

        logger.info(f"Workflow submitted: {workflow_submission.workflow_id}")
        return workflow_submission.workflow_id

    async def _convert_to_orchestrator_tasks(
        self, enhanced_workflow: EnhancedDPOWorkflow
    ) -> List[AgentTask]:
        """Convert enhanced DPO workflow to orchestrator tasks"""
        tasks = []
        task_counter = 0

        for phase_idx, phase in enumerate(enhanced_workflow.workflow_phases):
            phase_id = phase["phase_id"]
            phase_agents = enhanced_workflow.agent_assignments.get(phase_id, [])

            # Determine dependencies
            dependencies = []
            if phase_idx > 0:
                # Depend on previous phase completion
                prev_phase = enhanced_workflow.workflow_phases[phase_idx - 1]
                prev_phase_id = prev_phase["phase_id"]
                prev_agents = enhanced_workflow.agent_assignments.get(prev_phase_id, [])
                dependencies = [
                    f"task_{i}"
                    for i in range(task_counter - len(prev_agents), task_counter)
                ]

            # Create tasks for this phase
            for agent_idx, agent_id in enumerate(phase_agents):
                task_counter += 1

                # Build comprehensive prompt
                prompt = self._build_agent_prompt(
                    phase=phase,
                    agent_id=agent_id,
                    original_request=enhanced_workflow.original_request.user_request,
                    enhancements=phase.get("enhancements", []),
                    context=enhanced_workflow.original_request.project_context,
                )

                # Determine project location
                project_name = f"dpo_{enhanced_workflow.original_request.project_type}_{enhanced_workflow.workflow_id[:8]}"
                project_location = f"/home/opsvi/master_root/apps/{project_name}/"

                # Create agent task
                task = AgentTask(
                    task_id=f"task_{task_counter}",
                    task_type=self._determine_task_type(agent_id),
                    prompt=prompt,
                    context={
                        "phase": phase["name"],
                        "phase_id": phase_id,
                        "agent_id": agent_id,
                        "workflow_id": enhanced_workflow.workflow_id,
                        "enhancements": phase.get("enhancements", []),
                        "deliverables": phase.get("deliverables", []),
                        "success_criteria": phase.get("success_criteria", []),
                    },
                    dependencies=dependencies.copy()
                    if agent_idx == 0
                    else [f"task_{task_counter - 1}"],
                    quality_gates=phase.get("success_criteria", []),
                    project_location=project_location,
                    deliverable_structure={
                        "phase_output": f"{project_location}{phase['type']}/",
                        "documentation": f"{project_location}docs/",
                        "tests": f"{project_location}tests/",
                    },
                    directory_permissions=[
                        project_location,
                        "/home/opsvi/master_root/apps/",
                    ],
                )

                tasks.append(task)

        return tasks

    def _build_agent_prompt(
        self,
        phase: Dict,
        agent_id: str,
        original_request: str,
        enhancements: List,
        context: Dict,
    ) -> str:
        """Build comprehensive prompt for agent"""
        prompt_parts = []

        # Base request
        prompt_parts.append(f"## Development Request\n{original_request}\n")

        # Phase context
        prompt_parts.append(f"## Current Phase: {phase['name']}\n")
        prompt_parts.append(f"Your role: {agent_id}\n")

        # Deliverables
        if phase.get("deliverables"):
            prompt_parts.append("## Expected Deliverables:")
            for deliverable in phase["deliverables"]:
                prompt_parts.append(f"- {deliverable}")
            prompt_parts.append("")

        # Enhancements to implement
        if enhancements:
            prompt_parts.append("## Enhancements to Implement:")
            for enhancement in enhancements[:3]:
                if isinstance(enhancement, dict):
                    prompt_parts.append(
                        f"- {enhancement.get('title', 'Enhancement')}: {enhancement.get('description', '')}"
                    )
            prompt_parts.append("")

        # Success criteria
        if phase.get("success_criteria"):
            prompt_parts.append("## Success Criteria:")
            for criterion in phase["success_criteria"]:
                prompt_parts.append(f"- {criterion}")
            prompt_parts.append("")

        # Project context
        if context:
            prompt_parts.append("## Project Context:")
            prompt_parts.append(json.dumps(context, indent=2))
            prompt_parts.append("")

        # Quality requirements
        prompt_parts.append("## Quality Requirements:")
        prompt_parts.append("- Follow best practices for the technology stack")
        prompt_parts.append("- Ensure code is well-documented and tested")
        prompt_parts.append("- Optimize for performance and scalability")
        prompt_parts.append("- Maintain clean, readable code structure")

        return "\n".join(prompt_parts)

    def _determine_task_type(self, agent_id: str) -> str:
        """Determine task type from agent ID"""
        if "research" in agent_id or "genius" in agent_id:
            return "research"
        elif "architect" in agent_id or "design" in agent_id:
            return "architecture"
        elif (
            "implement" in agent_id
            or "develop" in agent_id
            or "accelerator" in agent_id
        ):
            return "implementation"
        elif "test" in agent_id or "qa" in agent_id:
            return "testing"
        elif "deploy" in agent_id:
            return "deployment"
        elif "document" in agent_id:
            return "documentation"
        elif "integrate" in agent_id or "specialist" in agent_id:
            return "integration"
        elif "optimize" in agent_id or "performance" in agent_id:
            return "optimization"
        elif "innovate" in agent_id or "analyst" in agent_id:
            return "innovation"
        else:
            return "general"

    async def _execute_workflow(self, submission: WorkflowSubmission):
        """Execute workflow through orchestrator"""
        try:
            # Update status
            submission.status = WorkflowStatus.INITIALIZING
            await self._update_workflow_status(
                submission.workflow_id, WorkflowStatus.INITIALIZING
            )

            # Create workflow output directory
            workflow_dir = self.output_base_dir / submission.workflow_id
            workflow_dir.mkdir(parents=True, exist_ok=True)

            # Initialize orchestrator with dashboard callback
            orchestrator = GenericOrchestrator(
                output_dir=workflow_dir,
                max_parallel=self.max_parallel_agents,
                workflow_name=submission.workflow_id,
                enable_dashboard_reporting=True,
                dashboard_state_callback=self._handle_orchestrator_update,
            )

            # Update status to running
            submission.status = WorkflowStatus.RUNNING
            await self._update_workflow_status(
                submission.workflow_id, WorkflowStatus.RUNNING
            )

            # Execute tasks
            start_time = datetime.now()
            results = await orchestrator.execute_batch(submission.orchestrator_tasks)
            end_time = datetime.now()

            # Process results
            workflow_results = await self._process_workflow_results(
                submission=submission,
                results=results,
                start_time=start_time,
                end_time=end_time,
                orchestrator=orchestrator,
            )

            # Store results
            self.workflow_results[submission.workflow_id] = workflow_results

            # Update status
            final_status = (
                WorkflowStatus.COMPLETED
                if workflow_results.status == WorkflowStatus.COMPLETED
                else WorkflowStatus.FAILED
            )
            submission.status = final_status
            await self._update_workflow_status(submission.workflow_id, final_status)

            # Clean up active workflow
            del self.active_workflows[submission.workflow_id]

            logger.info(
                f"Workflow {submission.workflow_id} completed with status: {final_status.value}"
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            submission.status = WorkflowStatus.FAILED
            await self._update_workflow_status(
                submission.workflow_id, WorkflowStatus.FAILED, error=str(e)
            )

    async def _process_workflow_results(
        self,
        submission: WorkflowSubmission,
        results: List[Dict],
        start_time: datetime,
        end_time: datetime,
        orchestrator: GenericOrchestrator,
    ) -> WorkflowResults:
        """Process and harvest workflow results"""
        # Count task outcomes
        completed_tasks = [r for r in results if r.get("status") == "completed"]
        failed_tasks = [r for r in results if r.get("status") == "failed"]

        # Extract deliverables
        deliverables = []
        workflow_dir = self.output_base_dir / submission.workflow_id

        # Scan for deliverables
        for root, dirs, files in os.walk(workflow_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in [
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".md",
                    ".json",
                    ".yaml",
                ]:
                    deliverables.append(str(file_path))

        # Extract knowledge from successful tasks
        extracted_knowledge = []
        for task_result in completed_tasks:
            if task_result.get("result"):
                knowledge = self._extract_knowledge_from_result(task_result)
                if knowledge:
                    extracted_knowledge.append(knowledge)

        # Collect errors
        errors = []
        for task_result in failed_tasks:
            if task_result.get("error"):
                errors.append(f"{task_result['task_id']}: {task_result['error']}")

        # Calculate metrics
        duration = (end_time - start_time).total_seconds()
        success_rate = len(completed_tasks) / len(results) if results else 0

        metrics = {
            "total_tasks": len(results),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": success_rate,
            "duration_seconds": duration,
            "avg_task_duration": duration / len(results) if results else 0,
            "deliverables_count": len(deliverables),
            "knowledge_extracted": len(extracted_knowledge),
        }

        # Determine overall status
        if len(failed_tasks) == 0:
            status = WorkflowStatus.COMPLETED
        elif len(completed_tasks) > 0:
            status = WorkflowStatus.COMPLETED  # Partial success
        else:
            status = WorkflowStatus.FAILED

        return WorkflowResults(
            workflow_id=submission.workflow_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            task_results=results,
            deliverables=deliverables,
            extracted_knowledge=extracted_knowledge,
            metrics=metrics,
            errors=errors,
        )

    def _extract_knowledge_from_result(self, task_result: Dict) -> Optional[Dict]:
        """Extract reusable knowledge from task result"""
        result_data = task_result.get("result", {})

        # Skip if no meaningful result
        if not result_data or isinstance(result_data, str):
            return None

        knowledge = {
            "task_id": task_result["task_id"],
            "task_type": task_result.get("task_type", "unknown"),
            "patterns": [],
            "best_practices": [],
            "integrations": [],
            "performance_insights": [],
        }

        # Extract patterns
        if "patterns" in result_data:
            knowledge["patterns"] = result_data["patterns"]

        # Extract best practices
        if "best_practices" in result_data:
            knowledge["best_practices"] = result_data["best_practices"]

        # Extract integration points
        if "integrations" in result_data or "apis" in result_data:
            knowledge["integrations"] = result_data.get(
                "integrations", []
            ) + result_data.get("apis", [])

        # Extract performance insights
        if "performance" in result_data or "optimizations" in result_data:
            knowledge["performance_insights"] = result_data.get(
                "performance", []
            ) + result_data.get("optimizations", [])

        # Only return if we extracted something meaningful
        if any(
            [
                knowledge["patterns"],
                knowledge["best_practices"],
                knowledge["integrations"],
                knowledge["performance_insights"],
            ]
        ):
            return knowledge

        return None

    async def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get current workflow status and progress"""
        if workflow_id in self.active_workflows:
            submission = self.active_workflows[workflow_id]
            progress = self.workflow_progress.get(workflow_id)

            return {
                "workflow_id": workflow_id,
                "status": submission.status.value,
                "progress": progress.to_dict() if progress else None,
                "metadata": submission.metadata,
            }
        elif workflow_id in self.workflow_results:
            results = self.workflow_results[workflow_id]
            return {
                "workflow_id": workflow_id,
                "status": results.status.value,
                "completed": True,
                "metrics": results.metrics,
                "deliverables_count": len(results.deliverables),
                "errors_count": len(results.errors),
            }
        else:
            return {
                "workflow_id": workflow_id,
                "status": "not_found",
                "error": "Workflow not found",
            }

    async def get_workflow_results(self, workflow_id: str) -> Optional[WorkflowResults]:
        """Get completed workflow results"""
        return self.workflow_results.get(workflow_id)

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id in self.active_workflows:
            submission = self.active_workflows[workflow_id]
            submission.status = WorkflowStatus.CANCELLED
            await self._update_workflow_status(workflow_id, WorkflowStatus.CANCELLED)

            # TODO: Implement actual cancellation in orchestrator
            # This would require adding cancellation support to GenericOrchestrator

            del self.active_workflows[workflow_id]

            logger.info(f"Workflow {workflow_id} cancelled")
            return True

        return False

    async def resume_workflow(self, workflow_id: str, checkpoint_path: str) -> bool:
        """Resume a workflow from checkpoint"""
        try:
            # Load checkpoint
            checkpoint_file = Path(checkpoint_path)
            if not checkpoint_file.exists():
                logger.error(f"Checkpoint file not found: {checkpoint_path}")
                return False

            with open(checkpoint_file, "r") as f:
                checkpoint_data = json.load(f)

            # TODO: Implement actual resume logic
            # This would require:
            # 1. Reconstructing the workflow submission from checkpoint
            # 2. Loading completed/failed task states
            # 3. Resuming orchestrator execution from checkpoint

            logger.info(f"Workflow {workflow_id} resumed from checkpoint")
            return True

        except Exception as e:
            logger.error(f"Failed to resume workflow: {str(e)}")
            return False

    def _handle_orchestrator_update(self, state_data: Dict):
        """Handle updates from orchestrator for dashboard integration"""
        event = state_data.get("event")
        workflow_id = state_data.get("workflow_id")

        if not workflow_id or workflow_id not in self.workflow_progress:
            return

        progress = self.workflow_progress[workflow_id]

        if event == "workflow_progress":
            progress.completed_tasks = state_data.get("completed_tasks", 0)
            progress.progress_percentage = state_data.get("progress_percent", 0)
            progress.last_update = datetime.now()

            # Estimate completion
            if state_data.get("eta_seconds"):
                from datetime import timedelta

                progress.estimated_completion = datetime.now() + timedelta(
                    seconds=state_data["eta_seconds"]
                )

        elif event == "task_activity":
            activity = state_data.get("activity")
            task_id = state_data.get("task_id")

            if activity == "started":
                progress.running_tasks.append(task_id)
            elif activity == "completed":
                if task_id in progress.running_tasks:
                    progress.running_tasks.remove(task_id)
                progress.completed_tasks += 1
            elif activity == "failed":
                if task_id in progress.running_tasks:
                    progress.running_tasks.remove(task_id)
                progress.failed_tasks += 1

            progress.last_update = datetime.now()

        # Forward to dashboard callback
        if self.dashboard_callback:
            self.dashboard_callback(state_data)

        # Broadcast WebSocket update
        asyncio.create_task(
            self._broadcast_update(
                {
                    "type": "progress_update",
                    "workflow_id": workflow_id,
                    "progress": progress.to_dict(),
                }
            )
        )

    async def _update_workflow_status(
        self, workflow_id: str, status: WorkflowStatus, error: Optional[str] = None
    ):
        """Update workflow status and notify clients"""
        if workflow_id in self.workflow_progress:
            progress = self.workflow_progress[workflow_id]
            progress.last_update = datetime.now()

        # Notify dashboard
        if self.dashboard_callback:
            self.dashboard_callback(
                {
                    "event": "workflow_status_changed",
                    "workflow_id": workflow_id,
                    "status": status.value,
                    "error": error,
                }
            )

        # Broadcast to WebSocket clients
        await self._broadcast_update(
            {
                "type": "status_update",
                "workflow_id": workflow_id,
                "status": status.value,
                "error": error,
            }
        )

    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        if not WEBSOCKET_AVAILABLE:
            logger.warning(
                "WebSocket support not available - install 'websockets' package"
            )
            return

        async def handle_client(websocket: WebSocketServerProtocol, path: str):
            """Handle WebSocket client connections"""
            self.websocket_clients.append(websocket)
            logger.info(f"WebSocket client connected from {websocket.remote_address}")

            try:
                # Send initial state
                for workflow_id in self.active_workflows:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "workflow_state",
                                "workflow_id": workflow_id,
                                "status": self.active_workflows[
                                    workflow_id
                                ].status.value,
                                "progress": self.workflow_progress[
                                    workflow_id
                                ].to_dict(),
                            }
                        )
                    )

                # Keep connection alive
                await websocket.wait_closed()

            finally:
                self.websocket_clients.remove(websocket)
                logger.info(f"WebSocket client disconnected")

        try:
            self.websocket_server = await websockets.serve(
                handle_client, "localhost", self.websocket_port
            )
            logger.info(f"WebSocket server started on port {self.websocket_port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {str(e)}")

    async def _broadcast_update(self, update: Dict):
        """Broadcast update to all WebSocket clients"""
        if not self.websocket_clients:
            return

        message = json.dumps(update)

        # Send to all connected clients
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            self.websocket_clients.remove(client)

    async def shutdown(self):
        """Shutdown the DPO orchestrator"""
        # Cancel active workflows
        for workflow_id in list(self.active_workflows.keys()):
            await self.cancel_workflow(workflow_id)

        # Close WebSocket server
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()

        logger.info("DPO Orchestrator shutdown complete")


# REST API Endpoints (using FastAPI)
try:
    from fastapi import BackgroundTasks, FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    class DevelopmentRequest(BaseModel):
        request: str
        project_type: str = "web_app"
        complexity: str = "moderate"
        context: Optional[Dict] = None

    class WorkflowStatusResponse(BaseModel):
        workflow_id: str
        status: str
        progress: Optional[Dict] = None
        metadata: Optional[Dict] = None

    # Create FastAPI app
    api = FastAPI(title="DPO Orchestrator API", version="1.0.0")

    # Global orchestrator instance
    orchestrator: Optional[DPOOrchestrator] = None

    @api.on_event("startup")
    async def startup_event():
        global orchestrator
        orchestrator = DPOOrchestrator()

    @api.on_event("shutdown")
    async def shutdown_event():
        if orchestrator:
            await orchestrator.shutdown()

    @api.post("/api/v1/workflows/submit")
    async def submit_workflow(
        request: DevelopmentRequest, background_tasks: BackgroundTasks
    ):
        """Submit a new development workflow"""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        workflow_id = await orchestrator.submit_development_request(
            request=request.request,
            project_type=request.project_type,
            complexity=request.complexity,
            context=request.context,
        )

        return JSONResponse(
            content={
                "workflow_id": workflow_id,
                "status": "submitted",
                "message": "Workflow submitted successfully",
            }
        )

    @api.get("/api/v1/workflows/{workflow_id}/status")
    async def get_workflow_status(workflow_id: str):
        """Get workflow status and progress"""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        status = await orchestrator.get_workflow_status(workflow_id)

        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Workflow not found")

        return JSONResponse(content=status)

    @api.get("/api/v1/workflows/{workflow_id}/results")
    async def get_workflow_results(workflow_id: str):
        """Get workflow execution results"""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        results = await orchestrator.get_workflow_results(workflow_id)

        if not results:
            raise HTTPException(status_code=404, detail="Workflow results not found")

        return JSONResponse(content=results.to_dict())

    @api.post("/api/v1/workflows/{workflow_id}/cancel")
    async def cancel_workflow(workflow_id: str):
        """Cancel a running workflow"""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        success = await orchestrator.cancel_workflow(workflow_id)

        if not success:
            raise HTTPException(
                status_code=404, detail="Workflow not found or not cancellable"
            )

        return JSONResponse(
            content={
                "workflow_id": workflow_id,
                "status": "cancelled",
                "message": "Workflow cancelled successfully",
            }
        )

    @api.post("/api/v1/workflows/{workflow_id}/resume")
    async def resume_workflow(workflow_id: str, checkpoint_path: str):
        """Resume a workflow from checkpoint"""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        success = await orchestrator.resume_workflow(workflow_id, checkpoint_path)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to resume workflow")

        return JSONResponse(
            content={
                "workflow_id": workflow_id,
                "status": "resumed",
                "message": "Workflow resumed successfully",
            }
        )

except ImportError:
    logger.warning("FastAPI not available - REST API endpoints disabled")
    api = None


async def main():
    """Example usage and testing"""
    # Initialize orchestrator
    dpo_orchestrator = DPOOrchestrator(
        output_base_dir="output/dpo_test", max_parallel_agents=5, enable_websocket=True
    )

    # Submit a test workflow
    workflow_id = await dpo_orchestrator.submit_development_request(
        request="Build a task management API with user authentication, task CRUD operations, and real-time notifications",
        project_type="api",
        complexity="moderate",
        context={
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "authentication": "JWT",
            "features": ["user_management", "task_crud", "notifications", "api_docs"],
        },
    )

    print(f"Workflow submitted: {workflow_id}")

    # Monitor progress
    for _ in range(60):  # Monitor for up to 60 seconds
        await asyncio.sleep(2)
        status = await dpo_orchestrator.get_workflow_status(workflow_id)
        print(f"Status: {status['status']}")

        if status.get("progress"):
            progress = status["progress"]
            print(
                f"Progress: {progress['completed_tasks']}/{progress['total_tasks']} tasks ({progress['progress_percentage']:.1f}%)"
            )

        if status["status"] in ["completed", "failed", "cancelled"]:
            break

    # Get results
    results = await dpo_orchestrator.get_workflow_results(workflow_id)
    if results:
        print(f"\nWorkflow completed!")
        print(f"Duration: {results.duration_seconds:.2f} seconds")
        print(f"Success rate: {results.metrics['success_rate']:.1%}")
        print(f"Deliverables: {results.metrics['deliverables_count']}")
        print(f"Knowledge extracted: {results.metrics['knowledge_extracted']}")

    # Shutdown
    await dpo_orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
