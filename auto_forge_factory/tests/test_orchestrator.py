"""
Tests for the Auto-Forge orchestrator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from auto_forge_factory.core.orchestrator import AutoForgeOrchestrator
from auto_forge_factory.models.schemas import (
    DevelopmentRequest,
    FactoryConfig,
    AgentConfig,
    AgentType,
    Language,
    Framework,
    JobStatus,
)


@pytest.fixture
def factory_config():
    """Create a test factory configuration."""
    agent_configs = {}
    for agent_type in AgentType:
        agent_configs[agent_type] = AgentConfig(
            agent_type=agent_type,
            model="gpt-4",
            temperature=0.1,
            max_tokens=4000,
            timeout_seconds=300,
            retry_attempts=3,
            quality_threshold=0.8,
            enabled=True,
        )

    return FactoryConfig(
        max_concurrent_jobs=5,
        max_agents_per_job=4,
        default_timeout_seconds=3600,
        agent_configs=agent_configs,
        supported_languages=[Language.PYTHON, Language.JAVASCRIPT],
        supported_frameworks=[Framework.FASTAPI, Framework.REACT],
        supported_cloud_providers=[],
    )


@pytest.fixture
def orchestrator(factory_config):
    """Create a test orchestrator."""
    return AutoForgeOrchestrator(factory_config)


@pytest.fixture
def sample_request():
    """Create a sample development request."""
    return DevelopmentRequest(
        name="Test Project",
        description="A test project for automated development",
        requirements=[
            "User authentication",
            "REST API endpoints",
            "Database integration",
        ],
        target_language=Language.PYTHON,
        target_framework=Framework.FASTAPI,
        target_architecture="microservices",
        priority=5,
    )


class TestAutoForgeOrchestrator:
    """Test cases for the Auto-Forge orchestrator."""

    def test_orchestrator_initialization(self, factory_config):
        """Test orchestrator initialization."""
        orchestrator = AutoForgeOrchestrator(factory_config)

        assert orchestrator.config == factory_config
        assert orchestrator.agent_registry is not None
        assert len(orchestrator.active_jobs) == 0
        assert len(orchestrator.job_results) == 0
        assert len(orchestrator.job_progress) == 0
        assert len(orchestrator.pipeline_phases) > 0

    def test_pipeline_phases_structure(self, orchestrator):
        """Test that pipeline phases are properly structured."""
        phases = orchestrator.pipeline_phases

        assert len(phases) > 0

        for agent_type, phase_name in phases:
            assert isinstance(agent_type, AgentType)
            assert isinstance(phase_name, str)
            assert len(phase_name) > 0

    @pytest.mark.asyncio
    async def test_start_development_job(self, orchestrator, sample_request):
        """Test starting a development job."""
        job_id = await orchestrator.start_development_job(sample_request)

        assert isinstance(job_id, str)
        assert job_id in orchestrator.active_jobs
        assert job_id in orchestrator.job_progress

        job_info = orchestrator.active_jobs[job_id]
        assert job_info["request"] == sample_request
        assert job_info["started_at"] is not None
        assert job_info["current_phase"] == 0
        assert len(job_info["phase_results"]) == 0

    @pytest.mark.asyncio
    async def test_start_multiple_jobs(self, orchestrator, sample_request):
        """Test starting multiple development jobs."""
        job_ids = []

        for i in range(3):
            request = DevelopmentRequest(
                name=f"Test Project {i}",
                description=f"Test project {i}",
                requirements=["Feature 1", "Feature 2"],
                priority=i + 1,
            )
            job_id = await orchestrator.start_development_job(request)
            job_ids.append(job_id)

        assert len(orchestrator.active_jobs) == 3
        assert len(set(job_ids)) == 3  # All job IDs should be unique

    def test_get_job_progress(self, orchestrator, sample_request):
        """Test getting job progress."""
        # Create a mock job
        job_id = str(uuid4())
        orchestrator.job_progress[job_id] = Mock(
            job_id=job_id,
            status=JobStatus.RUNNING,
            overall_progress_percent=50.0,
            current_phase="Testing",
            started_at=datetime.utcnow(),
        )

        progress = orchestrator.get_job_progress(job_id)
        assert progress is not None
        assert progress.job_id == job_id
        assert progress.status == JobStatus.RUNNING

    def test_get_job_progress_not_found(self, orchestrator):
        """Test getting job progress for non-existent job."""
        progress = orchestrator.get_job_progress("non-existent-id")
        assert progress is None

    def test_get_job_result(self, orchestrator):
        """Test getting job result."""
        # Create a mock result
        job_id = str(uuid4())
        orchestrator.job_results[job_id] = Mock(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            summary="Test completed successfully",
            quality_score=0.9,
            security_score=0.8,
            performance_score=0.85,
        )

        result = orchestrator.get_job_result(job_id)
        assert result is not None
        assert result.job_id == job_id
        assert result.status == JobStatus.COMPLETED

    def test_get_job_result_not_found(self, orchestrator):
        """Test getting job result for non-existent job."""
        result = orchestrator.get_job_result("non-existent-id")
        assert result is None

    def test_cancel_job(self, orchestrator, sample_request):
        """Test cancelling a job."""
        # Create a mock job
        job_id = str(uuid4())
        orchestrator.active_jobs[job_id] = {
            "request": sample_request,
            "started_at": datetime.utcnow(),
            "current_phase": 1,
            "phase_results": {},
            "artifacts": [],
            "total_tokens_used": 0,
            "total_cost": 0.0,
            "errors": [],
            "warnings": [],
        }

        cancelled = orchestrator.cancel_job(job_id)
        assert cancelled is True

        # Job should be removed from active jobs
        assert job_id not in orchestrator.active_jobs

    def test_cancel_job_not_found(self, orchestrator):
        """Test cancelling a non-existent job."""
        cancelled = orchestrator.cancel_job("non-existent-id")
        assert cancelled is False

    def test_get_factory_status(self, orchestrator):
        """Test getting factory status."""
        status = orchestrator.get_factory_status()

        assert "active_jobs" in status
        assert "completed_jobs" in status
        assert "agent_registry_status" in status
        assert "pipeline_phases" in status
        assert "supported_languages" in status
        assert "supported_frameworks" in status

        assert isinstance(status["active_jobs"], int)
        assert isinstance(status["completed_jobs"], int)
        assert isinstance(status["pipeline_phases"], list)
        assert isinstance(status["supported_languages"], list)
        assert isinstance(status["supported_frameworks"], list)

    def test_prepare_phase_inputs_planner(self, orchestrator, sample_request):
        """Test preparing inputs for planner phase."""
        job_id = str(uuid4())
        orchestrator.active_jobs[job_id] = {
            "request": sample_request,
            "phase_results": {},
            "artifacts": [],
        }

        inputs = orchestrator._prepare_phase_inputs(
            job_id, AgentType.PLANNER, sample_request
        )

        assert "project_name" in inputs
        assert "project_description" in inputs
        assert "requirements" in inputs
        assert "planning_context" in inputs
        assert inputs["project_name"] == sample_request.name
        assert inputs["requirements"] == sample_request.requirements

    def test_prepare_phase_inputs_coder(self, orchestrator, sample_request):
        """Test preparing inputs for coder phase."""
        job_id = str(uuid4())

        # Mock architect result
        architect_result = Mock()
        architect_result.content = "System architecture design"
        architect_result.artifacts = []

        orchestrator.active_jobs[job_id] = {
            "request": sample_request,
            "phase_results": {"architect": architect_result},
            "artifacts": [],
        }

        inputs = orchestrator._prepare_phase_inputs(
            job_id, AgentType.CODER, sample_request
        )

        assert "architecture" in inputs
        assert "arch_artifacts" in inputs
        assert inputs["architecture"] == "System architecture design"

    def test_update_job_progress(self, orchestrator):
        """Test updating job progress."""
        job_id = str(uuid4())
        orchestrator.job_progress[job_id] = Mock(
            job_id=job_id,
            status=JobStatus.PENDING,
            overall_progress_percent=0.0,
            current_phase="",
            started_at=datetime.utcnow(),
        )

        orchestrator._update_job_progress(job_id, "Testing", 2)

        progress = orchestrator.job_progress[job_id]
        assert progress.status == JobStatus.RUNNING
        assert progress.current_phase == "Testing"
        assert progress.overall_progress_percent > 0

    def test_update_job_status(self, orchestrator):
        """Test updating job status."""
        job_id = str(uuid4())
        orchestrator.job_progress[job_id] = Mock(
            job_id=job_id, status=JobStatus.PENDING, started_at=datetime.utcnow()
        )

        orchestrator._update_job_status(job_id, JobStatus.COMPLETED)

        progress = orchestrator.job_progress[job_id]
        assert progress.status == JobStatus.COMPLETED

    def test_calculate_quality_score(self, orchestrator):
        """Test calculating quality score."""
        job_info = {
            "phase_results": {
                "planner": Mock(success=True),
                "specifier": Mock(success=True),
                "architect": Mock(success=False),
                "coder": Mock(success=True),
            },
            "errors": ["Error 1"],
            "warnings": ["Warning 1", "Warning 2"],
        }

        score = orchestrator._calculate_quality_score(job_info)

        # 3 successful phases out of 4 = 0.75 base score
        # Minus penalties for errors and warnings
        assert 0.5 <= score <= 0.75

    def test_calculate_security_score(self, orchestrator):
        """Test calculating security score."""
        # Test with security validator result
        security_result = Mock()
        security_result.success = True
        security_result.metadata = {"security_score": 0.9}

        job_info = {"phase_results": {"security_validator": security_result}}

        score = orchestrator._calculate_security_score(job_info)
        assert score == 0.9

        # Test without security validator
        job_info = {"phase_results": {}}
        score = orchestrator._calculate_security_score(job_info)
        assert score == 0.5  # Default score

    def test_calculate_performance_score(self, orchestrator):
        """Test calculating performance score."""
        # Test with performance optimizer result
        perf_result = Mock()
        perf_result.success = True
        perf_result.metadata = {"performance_score": 0.85}

        job_info = {"phase_results": {"performance_optimizer": perf_result}}

        score = orchestrator._calculate_performance_score(job_info)
        assert score == 0.85

        # Test without performance optimizer
        job_info = {"phase_results": {}}
        score = orchestrator._calculate_performance_score(job_info)
        assert score == 0.5  # Default score

    def test_create_job_summary(self, orchestrator, sample_request):
        """Test creating job summary."""
        job_info = {
            "request": sample_request,
            "phase_results": {
                "planner": Mock(success=True),
                "specifier": Mock(success=True),
                "architect": Mock(success=True),
            },
            "artifacts": [Mock(), Mock(), Mock()],
            "total_tokens_used": 1500,
            "total_cost": 0.03,
            "errors": ["Minor error"],
            "warnings": ["Warning 1"],
        }

        summary = orchestrator._create_job_summary(job_info)

        assert "Test Project" in summary
        assert "3 development phases" in summary
        assert "3 artifacts" in summary
        assert "1500 tokens" in summary
        assert "$0.03" in summary
        assert "1 errors" in summary
        assert "1 warnings" in summary

    def test_create_deployment_instructions(self, orchestrator, sample_request):
        """Test creating deployment instructions."""
        job_info = {
            "artifacts": [
                Mock(name="main.py", type="code"),
                Mock(name="requirements.txt", type="config"),
                Mock(name="README.md", type="documentation"),
            ]
        }

        instructions = orchestrator._create_deployment_instructions(
            sample_request, job_info
        )

        assert "# Deployment Instructions" in instructions
        assert "Test Project" in instructions
        assert "A test project for automated development" in instructions
        assert "main.py (code)" in instructions
        assert "requirements.txt (config)" in instructions
        assert "README.md (documentation)" in instructions
        assert "Deployment Steps" in instructions
        assert "Quality Metrics" in instructions


@pytest.mark.asyncio
class TestOrchestratorAsync:
    """Async test cases for the orchestrator."""

    async def test_run_development_pipeline_mock(self, factory_config, sample_request):
        """Test running development pipeline with mocked agents."""
        orchestrator = AutoForgeOrchestrator(factory_config)

        # Mock the agent registry to return mock agents
        with patch.object(
            orchestrator.agent_registry, "create_agent_instance"
        ) as mock_create:
            # Create mock agent that returns success
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(
                success=True,
                content="Test result",
                artifacts=[],
                tokens_used=100,
                cost=0.002,
            )
            mock_create.return_value = mock_agent

            # Start the job
            job_id = await orchestrator.start_development_job(sample_request)

            # Wait a bit for the pipeline to run
            await asyncio.sleep(0.1)

            # Check that agents were created for each phase
            assert mock_create.call_count == len(orchestrator.pipeline_phases)

    async def test_run_development_pipeline_failure(
        self, factory_config, sample_request
    ):
        """Test running development pipeline with agent failure."""
        orchestrator = AutoForgeOrchestrator(factory_config)

        # Mock the agent registry to return failing agents
        with patch.object(
            orchestrator.agent_registry, "create_agent_instance"
        ) as mock_create:
            # Create mock agent that returns failure
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(
                success=False,
                content="Test failure",
                artifacts=[],
                errors=["Agent failed"],
            )
            mock_create.return_value = mock_agent

            # Start the job
            job_id = await orchestrator.start_development_job(sample_request)

            # Wait a bit for the pipeline to run
            await asyncio.sleep(0.1)

            # Check that the job failed
            progress = orchestrator.get_job_progress(job_id)
            assert progress.status == JobStatus.FAILED

    async def test_cleanup_job(self, factory_config):
        """Test cleaning up job resources."""
        orchestrator = AutoForgeOrchestrator(factory_config)
        job_id = str(uuid4())

        # Mock agent registry cleanup
        with patch.object(
            orchestrator.agent_registry, "cleanup_job_agents"
        ) as mock_cleanup:
            mock_cleanup.return_value = None

            # Add job to active jobs
            orchestrator.active_jobs[job_id] = {"test": "data"}

            # Clean up the job
            await orchestrator._cleanup_job(job_id)

            # Check that cleanup was called and job was removed
            mock_cleanup.assert_called_once_with(job_id)
            assert job_id not in orchestrator.active_jobs
