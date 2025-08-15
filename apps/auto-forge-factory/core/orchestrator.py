"""
Main orchestrator for the Auto-Forge factory.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .agent_registry import AgentRegistry
from .agents.base_agent import AgentResult
from ..models.schemas import (
    AgentType,
    JobStatus,
    DevelopmentRequest,
    JobProgress,
    JobResult,
    Artifact,
    FactoryConfig,
)


class AutoForgeOrchestrator:
    """Main orchestrator for the Auto-Forge factory."""

    def __init__(self, config: FactoryConfig):
        """Initialize the orchestrator.

        Args:
            config: Factory configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.agent_registry = AgentRegistry(config)

        # Job tracking
        self.active_jobs: Dict[UUID, Dict[str, Any]] = {}
        self.job_results: Dict[UUID, JobResult] = {}
        self.job_progress: Dict[UUID, JobProgress] = {}

        # Pipeline phases
        self.pipeline_phases = [
            (AgentType.PLANNER, "Planning"),
            (AgentType.SPECIFIER, "Specifying"),
            (AgentType.ARCHITECT, "Architecting"),
            (AgentType.CODER, "Coding"),
            (AgentType.TESTER, "Testing"),
            (AgentType.PERFORMANCE_OPTIMIZER, "Optimizing"),
            (AgentType.SECURITY_VALIDATOR, "Validating"),
            (AgentType.CRITIC, "Reviewing"),
        ]

    async def start_development_job(self, request: DevelopmentRequest) -> UUID:
        """Start a new development job.

        Args:
            request: Development request

        Returns:
            Job ID
        """
        job_id = UUID.uuid4()

        # Initialize job tracking
        self.active_jobs[job_id] = {
            "request": request,
            "started_at": datetime.utcnow(),
            "current_phase": 0,
            "phase_results": {},
            "artifacts": [],
            "total_tokens_used": 0,
            "total_cost": 0.0,
            "errors": [],
            "warnings": [],
        }

        # Initialize progress tracking
        self.job_progress[job_id] = JobProgress(
            job_id=job_id,
            status=JobStatus.PENDING,
            overall_progress_percent=0.0,
            current_phase="Initializing",
            started_at=datetime.utcnow(),
        )

        self.logger.info(
            f"Started development job {job_id} for project: {request.name}"
        )

        # Start the pipeline asynchronously
        asyncio.create_task(self._run_development_pipeline(job_id))

        return job_id

    async def _run_development_pipeline(self, job_id: UUID):
        """Run the complete development pipeline for a job.

        Args:
            job_id: Job ID
        """
        try:
            job_info = self.active_jobs[job_id]
            request = job_info["request"]

            self.logger.info(f"Starting development pipeline for job {job_id}")

            # Run each phase of the pipeline
            for phase_idx, (agent_type, phase_name) in enumerate(self.pipeline_phases):
                try:
                    # Update job status
                    job_info["current_phase"] = phase_idx
                    self._update_job_progress(job_id, phase_name, phase_idx)

                    self.logger.info(f"Starting phase {phase_name} for job {job_id}")

                    # Create and run the agent
                    agent = self.agent_registry.create_agent_instance(
                        agent_type=agent_type,
                        job_id=job_id,
                        config=self.agent_registry.get_agent_config(agent_type),
                    )

                    # Prepare inputs for this phase
                    inputs = self._prepare_phase_inputs(job_id, agent_type, request)

                    # Run the agent
                    result = await agent.run(inputs)

                    # Store phase result
                    job_info["phase_results"][agent_type.value] = result

                    # Update job metrics
                    job_info["total_tokens_used"] += result.tokens_used or 0
                    job_info["total_cost"] += result.cost or 0.0
                    job_info["artifacts"].extend(result.artifacts)

                    # Add errors and warnings
                    job_info["errors"].extend(result.errors)
                    job_info["warnings"].extend(result.warnings)

                    # Check if we should continue
                    if not result.success:
                        self.logger.error(f"Phase {phase_name} failed for job {job_id}")
                        self._update_job_status(job_id, JobStatus.FAILED)
                        return

                    self.logger.info(f"Completed phase {phase_name} for job {job_id}")

                except Exception as e:
                    self.logger.error(
                        f"Error in phase {phase_name} for job {job_id}: {e}"
                    )
                    job_info["errors"].append(f"Phase {phase_name} failed: {e}")
                    self._update_job_status(job_id, JobStatus.FAILED)
                    return

            # Pipeline completed successfully
            self.logger.info(
                f"Development pipeline completed successfully for job {job_id}"
            )
            self._update_job_status(job_id, JobStatus.COMPLETED)

            # Create final result
            await self._create_job_result(job_id)

        except Exception as e:
            self.logger.error(f"Development pipeline failed for job {job_id}: {e}")
            job_info = self.active_jobs.get(job_id, {})
            job_info["errors"] = job_info.get("errors", []) + [f"Pipeline failed: {e}"]
            self._update_job_status(job_id, JobStatus.FAILED)

        finally:
            # Clean up
            await self._cleanup_job(job_id)

    def _prepare_phase_inputs(
        self, job_id: UUID, agent_type: AgentType, request: DevelopmentRequest
    ) -> Dict[str, Any]:
        """Prepare inputs for a specific phase.

        Args:
            job_id: Job ID
            agent_type: Agent type
            request: Original development request

        Returns:
            Inputs for the agent
        """
        job_info = self.active_jobs[job_id]
        phase_results = job_info["phase_results"]

        inputs = {
            "project_name": request.name,
            "project_description": request.description,
            "requirements": request.requirements,
            "target_language": request.target_language,
            "target_framework": request.target_framework,
            "target_architecture": request.target_architecture,
            "cloud_provider": request.cloud_provider,
            "budget_tokens": request.budget_tokens,
            "budget_cost": request.budget_cost,
            "deadline": request.deadline,
            "priority": request.priority,
            "metadata": request.metadata,
            "previous_phase_results": phase_results,
            "artifacts": job_info["artifacts"],
        }

        # Add phase-specific inputs
        if agent_type == AgentType.PLANNER:
            inputs["planning_context"] = {
                "requirements": request.requirements,
                "constraints": {
                    "language": request.target_language,
                    "framework": request.target_framework,
                    "architecture": request.target_architecture,
                    "budget": request.budget_cost,
                    "deadline": request.deadline,
                },
            }

        elif agent_type == AgentType.SPECIFIER:
            planner_result = phase_results.get("planner")
            if planner_result:
                inputs["plan"] = planner_result.content
                inputs["plan_artifacts"] = planner_result.artifacts

        elif agent_type == AgentType.ARCHITECT:
            specifier_result = phase_results.get("specifier")
            if specifier_result:
                inputs["specification"] = specifier_result.content
                inputs["spec_artifacts"] = specifier_result.artifacts

        elif agent_type == AgentType.CODER:
            architect_result = phase_results.get("architect")
            if architect_result:
                inputs["architecture"] = architect_result.content
                inputs["arch_artifacts"] = architect_result.artifacts

        elif agent_type == AgentType.TESTER:
            coder_result = phase_results.get("coder")
            if coder_result:
                inputs["code"] = coder_result.content
                inputs["code_artifacts"] = coder_result.artifacts

        elif agent_type == AgentType.PERFORMANCE_OPTIMIZER:
            tester_result = phase_results.get("tester")
            if tester_result:
                inputs["test_results"] = tester_result.content
                inputs["test_artifacts"] = tester_result.artifacts

        elif agent_type == AgentType.SECURITY_VALIDATOR:
            optimizer_result = phase_results.get("performance_optimizer")
            if optimizer_result:
                inputs["optimized_code"] = optimizer_result.content
                inputs["optimized_artifacts"] = optimizer_result.artifacts

        elif agent_type == AgentType.CRITIC:
            # Include all previous results for comprehensive review
            inputs["all_phase_results"] = phase_results
            inputs["all_artifacts"] = job_info["artifacts"]

        return inputs

    def _update_job_progress(self, job_id: UUID, phase_name: str, phase_idx: int):
        """Update job progress.

        Args:
            job_id: Job ID
            phase_name: Current phase name
            phase_idx: Current phase index
        """
        if job_id in self.job_progress:
            progress = self.job_progress[job_id]
            progress.status = JobStatus.RUNNING
            progress.current_phase = phase_name
            progress.overall_progress_percent = (
                phase_idx / len(self.pipeline_phases)
            ) * 100
            progress.updated_at = datetime.utcnow()

    def _update_job_status(self, job_id: UUID, status: JobStatus):
        """Update job status.

        Args:
            job_id: Job ID
            status: New status
        """
        if job_id in self.job_progress:
            self.job_progress[job_id].status = status
            self.job_progress[job_id].updated_at = datetime.utcnow()

    async def _create_job_result(self, job_id: UUID):
        """Create final job result.

        Args:
            job_id: Job ID
        """
        job_info = self.active_jobs[job_id]
        request = job_info["request"]

        # Calculate quality scores
        quality_score = self._calculate_quality_score(job_info)
        security_score = self._calculate_security_score(job_info)
        performance_score = self._calculate_performance_score(job_info)

        # Create summary
        summary = self._create_job_summary(job_info)

        # Create deployment instructions
        deployment_instructions = self._create_deployment_instructions(
            request, job_info
        )

        # Create final result
        result = JobResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            artifacts=job_info["artifacts"],
            summary=summary,
            metrics={
                "total_phases": len(self.pipeline_phases),
                "successful_phases": len(
                    [r for r in job_info["phase_results"].values() if r.success]
                ),
                "total_artifacts": len(job_info["artifacts"]),
                "total_tokens_used": job_info["total_tokens_used"],
                "total_cost": job_info["total_cost"],
            },
            quality_score=quality_score,
            security_score=security_score,
            performance_score=performance_score,
            total_tokens_used=job_info["total_tokens_used"],
            total_cost=job_info["total_cost"],
            execution_time_seconds=(
                datetime.utcnow() - job_info["started_at"]
            ).total_seconds(),
            errors=job_info["errors"],
            warnings=job_info["warnings"],
            deployment_instructions=deployment_instructions,
            created_at=job_info["started_at"],
            completed_at=datetime.utcnow(),
        )

        self.job_results[job_id] = result
        self.logger.info(f"Created final result for job {job_id}")

    def _calculate_quality_score(self, job_info: Dict[str, Any]) -> float:
        """Calculate overall quality score.

        Args:
            job_info: Job information

        Returns:
            Quality score (0-1)
        """
        phase_results = job_info["phase_results"]
        if not phase_results:
            return 0.0

        # Calculate based on successful phases and artifact quality
        successful_phases = len([r for r in phase_results.values() if r.success])
        total_phases = len(phase_results)

        base_score = successful_phases / total_phases if total_phases > 0 else 0.0

        # Adjust based on errors and warnings
        error_penalty = min(0.2, len(job_info["errors"]) * 0.05)
        warning_penalty = min(0.1, len(job_info["warnings"]) * 0.02)

        return max(0.0, min(1.0, base_score - error_penalty - warning_penalty))

    def _calculate_security_score(self, job_info: Dict[str, Any]) -> float:
        """Calculate security score.

        Args:
            job_info: Job information

        Returns:
            Security score (0-1)
        """
        security_result = job_info["phase_results"].get("security_validator")
        if security_result and security_result.success:
            # Extract security score from security validator result
            return security_result.metadata.get("security_score", 0.8)
        return 0.5  # Default score if no security validation

    def _calculate_performance_score(self, job_info: Dict[str, Any]) -> float:
        """Calculate performance score.

        Args:
            job_info: Job information

        Returns:
            Performance score (0-1)
        """
        perf_result = job_info["phase_results"].get("performance_optimizer")
        if perf_result and perf_result.success:
            # Extract performance score from optimizer result
            return perf_result.metadata.get("performance_score", 0.8)
        return 0.5  # Default score if no performance optimization

    def _create_job_summary(self, job_info: Dict[str, Any]) -> str:
        """Create a summary of the job.

        Args:
            job_info: Job information

        Returns:
            Job summary
        """
        request = job_info["request"]
        phase_results = job_info["phase_results"]

        summary_parts = [
            f"Successfully developed '{request.name}' - {request.description}",
            f"Completed {len(phase_results)} development phases",
            f"Generated {len(job_info['artifacts'])} artifacts",
            f"Used {job_info['total_tokens_used']} tokens (${job_info['total_cost']:.2f})",
        ]

        if job_info["errors"]:
            summary_parts.append(f"Encountered {len(job_info['errors'])} errors")

        if job_info["warnings"]:
            summary_parts.append(f"Generated {len(job_info['warnings'])} warnings")

        return ". ".join(summary_parts) + "."

    def _create_deployment_instructions(
        self, request: DevelopmentRequest, job_info: Dict[str, Any]
    ) -> str:
        """Create deployment instructions.

        Args:
            request: Development request
            job_info: Job information

        Returns:
            Deployment instructions
        """
        instructions = [
            f"# Deployment Instructions for {request.name}",
            "",
            f"## Project Overview",
            f"- Name: {request.name}",
            f"- Description: {request.description}",
            f"- Language: {request.target_language or 'Auto-detected'}",
            f"- Framework: {request.target_framework or 'Auto-detected'}",
            f"- Architecture: {request.target_architecture or 'Auto-detected'}",
            "",
            "## Generated Artifacts",
        ]

        for artifact in job_info["artifacts"]:
            instructions.append(f"- {artifact.name} ({artifact.type})")

        instructions.extend(
            [
                "",
                "## Deployment Steps",
                "1. Review all generated artifacts",
                "2. Install required dependencies",
                "3. Configure environment variables",
                "4. Run tests to verify functionality",
                "5. Deploy to your target environment",
                "",
                "## Quality Metrics",
                f"- Quality Score: {self._calculate_quality_score(job_info):.2f}/1.0",
                f"- Security Score: {self._calculate_security_score(job_info):.2f}/1.0",
                f"- Performance Score: {self._calculate_performance_score(job_info):.2f}/1.0",
            ]
        )

        return "\n".join(instructions)

    async def _cleanup_job(self, job_id: UUID):
        """Clean up job resources.

        Args:
            job_id: Job ID
        """
        # Clean up agent instances
        await self.agent_registry.cleanup_job_agents(job_id)

        # Remove from active jobs
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]

        self.logger.info(f"Cleaned up job {job_id}")

    def get_job_progress(self, job_id: UUID) -> Optional[JobProgress]:
        """Get job progress.

        Args:
            job_id: Job ID

        Returns:
            Job progress if exists, None otherwise
        """
        return self.job_progress.get(job_id)

    def get_job_result(self, job_id: UUID) -> Optional[JobResult]:
        """Get job result.

        Args:
            job_id: Job ID

        Returns:
            Job result if exists, None otherwise
        """
        return self.job_results.get(job_id)

    def cancel_job(self, job_id: UUID) -> bool:
        """Cancel a job.

        Args:
            job_id: Job ID

        Returns:
            True if job was cancelled, False if not found
        """
        if job_id in self.active_jobs:
            self._update_job_status(job_id, JobStatus.CANCELLED)
            asyncio.create_task(self._cleanup_job(job_id))
            return True
        return False

    def get_factory_status(self) -> Dict[str, Any]:
        """Get overall factory status.

        Returns:
            Factory status information
        """
        return {
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.job_results),
            "agent_registry_status": self.agent_registry.get_factory_status(),
            "pipeline_phases": [phase[1] for phase in self.pipeline_phases],
            "supported_languages": [
                lang.value for lang in self.config.supported_languages
            ],
            "supported_frameworks": [
                fw.value for fw in self.config.supported_frameworks
            ],
        }
