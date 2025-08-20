"""Main research workflow with advanced features and fault tolerance."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from ..errors import OrchestrationError
from ..models import ResearchSummary
from ..workflow_tool import ResearchWorkflowTool

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Represents a step in the research workflow."""

    name: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: float | None = None
    end_time: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MainResearchWorkflow:
    """Main research workflow with advanced features, fault tolerance, and progress tracking."""

    def __init__(self, config=None):
        self.workflow_tool = ResearchWorkflowTool(config)
        self.steps: list[WorkflowStep] = []

    async def execute(
        self,
        query: str,
        k: int = 10,
        enable_synthesis: bool = True,
        persist: bool = True,
        retry_failed: bool = True,
        max_retries: int = 2,
    ) -> ResearchSummary:
        """Execute main research workflow with comprehensive features."""
        workflow_start = time.time()

        try:
            # Initialize workflow steps
            self._initialize_steps()

            # Step 1: Query validation and preprocessing
            await self._execute_step("query_validation", self._validate_query, query)

            # Step 2: Configuration validation
            await self._execute_step("config_validation", self._validate_config)

            # Step 3: Execute research with retries
            summary = await self._execute_research_with_retries(
                query,
                k,
                enable_synthesis,
                persist,
                retry_failed,
                max_retries,
            )

            # Step 4: Post-processing and analysis
            await self._execute_step(
                "post_processing", self._post_process_results, summary
            )

            # Step 5: Persistence (if enabled)
            if persist:
                await self._execute_step(
                    "persistence", self._persist_workflow_results, summary
                )

            # Step 6: Generate workflow report
            await self._execute_step(
                "report_generation", self._generate_workflow_report, summary
            )

            workflow_duration = time.time() - workflow_start
            logger.info(f"Main research workflow completed in {workflow_duration:.2f}s")

            return summary

        except Exception as e:
            logger.error(f"Main research workflow failed: {e}")
            await self._mark_workflow_failed(str(e))
            raise OrchestrationError(f"Main research workflow failed: {e}")

    def _initialize_steps(self):
        """Initialize workflow steps."""
        self.steps = [
            WorkflowStep("query_validation"),
            WorkflowStep("config_validation"),
            WorkflowStep("research_execution"),
            WorkflowStep("post_processing"),
            WorkflowStep("persistence"),
            WorkflowStep("report_generation"),
        ]

    async def _execute_step(self, step_name: str, step_func, *args, **kwargs):
        """Execute a workflow step with error handling."""
        step = self._get_step(step_name)
        if not step:
            logger.warning(f"Unknown step: {step_name}")
            return None

        step.status = "running"
        step.start_time = time.time()

        try:
            result = await step_func(*args, **kwargs)
            step.status = "completed"
            step.end_time = time.time()
            step.metadata["duration"] = step.end_time - step.start_time
            logger.info(f"Step '{step_name}' completed successfully")
            return result

        except Exception as e:
            step.status = "failed"
            step.end_time = time.time()
            step.error = str(e)
            step.metadata["duration"] = step.end_time - step.start_time
            logger.error(f"Step '{step_name}' failed: {e}")
            raise

    def _get_step(self, step_name: str) -> WorkflowStep | None:
        """Get a workflow step by name."""
        for step in self.steps:
            if step.name == step_name:
                return step
        return None

    async def _validate_query(self, query: str) -> bool:
        """Validate the research query."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if len(query.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")

        if len(query) > 1000:
            raise ValueError("Query too long (max 1000 characters)")

        return True

    async def _validate_config(self) -> bool:
        """Validate the research configuration."""
        config = self.workflow_tool.config

        # Check that at least one client is enabled
        enabled_clients = [c for c in config.clients.values() if c.enabled]
        if not enabled_clients:
            raise ValueError("No research clients are enabled")

        # Validate client configurations
        for client_name, client_config in config.clients.items():
            if client_config.enabled:
                if client_config.timeout <= 0:
                    raise ValueError(f"Invalid timeout for client {client_name}")
                if client_config.max_results <= 0:
                    raise ValueError(f"Invalid max_results for client {client_name}")

        return True

    async def _execute_research_with_retries(
        self,
        query: str,
        k: int,
        enable_synthesis: bool,
        persist: bool,
        retry_failed: bool,
        max_retries: int,
    ) -> ResearchSummary:
        """Execute research with retry logic."""
        step = self._get_step("research_execution")
        step.status = "running"
        step.start_time = time.time()

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                summary = await self.workflow_tool.execute(
                    query=query,
                    k=k,
                    persist=persist,
                    enable_synthesis=enable_synthesis,
                )

                step.status = "completed"
                step.end_time = time.time()
                step.metadata["attempts"] = attempt + 1
                step.metadata["duration"] = step.end_time - step.start_time

                return summary

            except Exception as e:
                last_error = e
                step.metadata["attempts"] = attempt + 1
                step.metadata[f"error_attempt_{attempt}"] = str(e)

                if attempt < max_retries and retry_failed:
                    logger.warning(
                        f"Research attempt {attempt + 1} failed, retrying..."
                    )
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    break

        # All attempts failed
        step.status = "failed"
        step.end_time = time.time()
        step.error = str(last_error)
        step.metadata["duration"] = step.end_time - step.start_time
        raise last_error

    async def _post_process_results(self, summary: ResearchSummary) -> ResearchSummary:
        """Post-process research results."""
        # Add workflow metadata
        summary.metadata["workflow_type"] = "main_research"
        summary.metadata["workflow_steps"] = [
            {
                "name": step.name,
                "status": step.status,
                "duration": step.metadata.get("duration", 0),
                "error": step.error,
            }
            for step in self.steps
        ]

        # Calculate additional metrics
        if summary.top_results:
            avg_relevance = sum(float(r.relevance) for r in summary.top_results) / len(
                summary.top_results
            )
            summary.metadata["avg_relevance"] = avg_relevance
            summary.metadata["relevance_range"] = {
                "min": float(min(r.relevance for r in summary.top_results)),
                "max": float(max(r.relevance for r in summary.top_results)),
            }

        return summary

    async def _persist_workflow_results(self, summary: ResearchSummary) -> None:
        """Persist workflow results with additional metadata."""
        # Add workflow-specific persistence
        workflow_metadata = {
            "workflow_steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "start_time": step.start_time,
                    "end_time": step.end_time,
                    "duration": step.metadata.get("duration", 0),
                    "error": step.error,
                }
                for step in self.steps
            ],
        }

        summary.metadata["workflow_metadata"] = workflow_metadata

        # Use the workflow tool's persistence
        await self.workflow_tool._persist_results(summary)

    async def _generate_workflow_report(
        self, summary: ResearchSummary
    ) -> dict[str, Any]:
        """Generate a comprehensive workflow report."""
        report = {
            "workflow_summary": {
                "total_steps": len(self.steps),
                "completed_steps": len(
                    [s for s in self.steps if s.status == "completed"]
                ),
                "failed_steps": len([s for s in self.steps if s.status == "failed"]),
                "total_duration": sum(
                    s.metadata.get("duration", 0) for s in self.steps
                ),
            },
            "research_summary": {
                "query": summary.query,
                "total_results": len(summary.top_results),
                "successful_sources": summary.successful_sources,
                "failed_sources": summary.failed_sources,
                "execution_time": summary.execution_time,
                "synthesis_length": len(summary.synthesis),
            },
            "step_details": [
                {
                    "name": step.name,
                    "status": step.status,
                    "duration": step.metadata.get("duration", 0),
                    "error": step.error,
                    "metadata": step.metadata,
                }
                for step in self.steps
            ],
        }

        logger.info(f"Workflow report generated: {report['workflow_summary']}")
        return report

    async def _mark_workflow_failed(self, error: str):
        """Mark the entire workflow as failed."""
        for step in self.steps:
            if step.status == "running":
                step.status = "failed"
                step.error = f"Workflow failed: {error}"
                step.end_time = time.time()
                step.metadata["duration"] = step.end_time - step.start_time

    def get_workflow_status(self) -> dict[str, Any]:
        """Get the current status of the workflow."""
        return {
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "duration": step.metadata.get("duration", 0),
                    "error": step.error,
                }
                for step in self.steps
            ],
            "overall_status": "completed"
            if all(s.status == "completed" for s in self.steps)
            else "failed"
            if any(s.status == "failed" for s in self.steps)
            else "running",
        }
