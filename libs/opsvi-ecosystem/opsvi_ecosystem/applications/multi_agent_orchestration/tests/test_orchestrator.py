"""
Tests for WorkflowOrchestrator

Comprehensive test suite for the workflow orchestrator including
unit tests, integration tests, and workflow execution tests.
"""

import asyncio
import logging

import pytest

from ..agents.base_agent import BaseAgent
from ..common.types import TaskResult, WorkflowStatus
from ..communication.message_broker import MessageBroker
from ..orchestrator.workflow_orchestrator import (
    ExecutionPattern,
    Workflow,
    WorkflowOrchestrator,
    WorkflowStep,
)


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, agent_id: str, should_fail: bool = False):
        super().__init__(agent_id, f"Mock Agent {agent_id}")
        self.should_fail = should_fail
        self.executed_tasks = []

    async def _execute_task_logic(self, task):
        """Mock task execution."""
        self.executed_tasks.append(task)

        if self.should_fail:
            return TaskResult(success=False, error="Mock task failure")

        return TaskResult(
            success=True, result=f"Mock result for {task.get('task_type', 'unknown')}"
        )


@pytest.fixture
async def message_broker():
    """Create message broker for testing."""
    broker = MessageBroker()
    yield broker
    await broker.shutdown()


@pytest.fixture
async def orchestrator(message_broker):
    """Create orchestrator for testing."""
    logger = logging.getLogger("test_orchestrator")
    orch = WorkflowOrchestrator(message_broker, logger)
    yield orch
    await orch.shutdown()


@pytest.fixture
async def mock_agents():
    """Create mock agents for testing."""
    agents = [
        MockAgent("agent_1"),
        MockAgent("agent_2"),
        MockAgent("agent_3", should_fail=True),  # This agent will fail
    ]
    return agents


class TestWorkflowStep:
    """Test WorkflowStep class."""

    def test_step_creation(self):
        """Test step creation."""
        step = WorkflowStep(
            step_id="test_step",
            agent_id="test_agent",
            task_type="test_task",
            task_data={"key": "value"},
            dependencies=["dep1", "dep2"],
            timeout=30.0,
        )

        assert step.step_id == "test_step"
        assert step.agent_id == "test_agent"
        assert step.task_type == "test_task"
        assert step.task_data == {"key": "value"}
        assert step.dependencies == ["dep1", "dep2"]
        assert step.timeout == 30.0
        assert step.status == WorkflowStatus.PENDING
        assert step.result is None
        assert step.error is None

    def test_step_to_dict(self):
        """Test step serialization."""
        step = WorkflowStep(
            step_id="test_step",
            agent_id="test_agent",
            task_type="test_task",
            task_data={"key": "value"},
        )
        step.status = WorkflowStatus.COMPLETED
        step.result = "test_result"

        step_dict = step.to_dict()

        assert step_dict["step_id"] == "test_step"
        assert step_dict["agent_id"] == "test_agent"
        assert step_dict["task_type"] == "test_task"
        assert step_dict["task_data"] == {"key": "value"}
        assert step_dict["status"] == "completed"
        assert step_dict["result"] == "test_result"


class TestWorkflow:
    """Test Workflow class."""

    def test_workflow_creation(self):
        """Test workflow creation."""
        steps = [
            WorkflowStep("step1", "agent1", "task1", {}),
            WorkflowStep("step2", "agent2", "task2", {}, dependencies=["step1"]),
        ]

        workflow = Workflow(
            workflow_id="test_workflow",
            name="Test Workflow",
            steps=steps,
            execution_pattern=ExecutionPattern.SEQUENTIAL,
        )

        assert workflow.workflow_id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 2
        assert workflow.execution_pattern == ExecutionPattern.SEQUENTIAL
        assert workflow.status == WorkflowStatus.PENDING

    def test_get_ready_steps(self):
        """Test getting ready steps."""
        steps = [
            WorkflowStep("step1", "agent1", "task1", {}),
            WorkflowStep("step2", "agent2", "task2", {}, dependencies=["step1"]),
            WorkflowStep("step3", "agent3", "task3", {}),
        ]

        workflow = Workflow("test_workflow", "Test", steps)

        # Initially, steps without dependencies should be ready
        ready_steps = workflow.get_ready_steps()
        ready_ids = [step.step_id for step in ready_steps]
        assert "step1" in ready_ids
        assert "step3" in ready_ids
        assert "step2" not in ready_ids

        # After step1 completes, step2 should be ready
        workflow.steps["step1"].status = WorkflowStatus.COMPLETED
        ready_steps = workflow.get_ready_steps()
        ready_ids = [step.step_id for step in ready_steps]
        assert "step2" in ready_ids

    def test_is_complete(self):
        """Test workflow completion check."""
        steps = [
            WorkflowStep("step1", "agent1", "task1", {}),
            WorkflowStep("step2", "agent2", "task2", {}),
        ]

        workflow = Workflow("test_workflow", "Test", steps)

        # Initially not complete
        assert not workflow.is_complete()

        # Complete one step
        workflow.steps["step1"].status = WorkflowStatus.COMPLETED
        assert not workflow.is_complete()

        # Complete all steps
        workflow.steps["step2"].status = WorkflowStatus.COMPLETED
        assert workflow.is_complete()

    def test_has_failed_steps(self):
        """Test failed steps check."""
        steps = [
            WorkflowStep("step1", "agent1", "task1", {}),
            WorkflowStep("step2", "agent2", "task2", {}),
        ]

        workflow = Workflow("test_workflow", "Test", steps)

        # Initially no failed steps
        assert not workflow.has_failed_steps()

        # Fail one step
        workflow.steps["step1"].status = WorkflowStatus.FAILED
        assert workflow.has_failed_steps()


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator class."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.message_broker is not None
        assert orchestrator.logger is not None
        assert len(orchestrator.agents) == 0
        assert len(orchestrator.workflows) == 0
        assert len(orchestrator.active_workflows) == 0

    @pytest.mark.asyncio
    async def test_agent_registration(self, orchestrator, mock_agents):
        """Test agent registration."""
        agent = mock_agents[0]

        await orchestrator.register_agent(agent)

        assert agent.agent_id in orchestrator.agents
        assert orchestrator.agents[agent.agent_id] == agent

    @pytest.mark.asyncio
    async def test_agent_unregistration(self, orchestrator, mock_agents):
        """Test agent unregistration."""
        agent = mock_agents[0]

        await orchestrator.register_agent(agent)
        assert agent.agent_id in orchestrator.agents

        await orchestrator.unregister_agent(agent.agent_id)
        assert agent.agent_id not in orchestrator.agents

    @pytest.mark.asyncio
    async def test_workflow_creation(self, orchestrator):
        """Test workflow creation."""
        steps = [
            {
                "step_id": "step1",
                "agent_id": "agent1",
                "task_type": "test_task",
                "task_data": {"key": "value"},
            }
        ]

        workflow_id = orchestrator.create_workflow(
            name="Test Workflow",
            steps=steps,
            execution_pattern=ExecutionPattern.SEQUENTIAL,
        )

        assert workflow_id in orchestrator.workflows
        workflow = orchestrator.workflows[workflow_id]
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1
        assert workflow.execution_pattern == ExecutionPattern.SEQUENTIAL

    @pytest.mark.asyncio
    async def test_sequential_workflow_execution(self, orchestrator, mock_agents):
        """Test sequential workflow execution."""
        # Register agents
        for agent in mock_agents[:2]:  # Use non-failing agents
            await orchestrator.register_agent(agent)

        # Create workflow
        steps = [
            {
                "step_id": "step1",
                "agent_id": "agent_1",
                "task_type": "task1",
                "task_data": {"data": "test1"},
            },
            {
                "step_id": "step2",
                "agent_id": "agent_2",
                "task_type": "task2",
                "task_data": {"data": "test2"},
                "dependencies": ["step1"],
            },
        ]

        workflow_id = orchestrator.create_workflow(
            name="Sequential Test",
            steps=steps,
            execution_pattern=ExecutionPattern.SEQUENTIAL,
        )

        # Execute workflow
        results = await orchestrator.execute_workflow(workflow_id)

        assert results["status"] == "completed"
        assert len(results["steps"]) == 2
        assert results["steps"]["step1"]["status"] == "completed"
        assert results["steps"]["step2"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_parallel_workflow_execution(self, orchestrator, mock_agents):
        """Test parallel workflow execution."""
        # Register agents
        for agent in mock_agents[:2]:
            await orchestrator.register_agent(agent)

        # Create workflow with parallel steps
        steps = [
            {
                "step_id": "step1",
                "agent_id": "agent_1",
                "task_type": "task1",
                "task_data": {"data": "test1"},
            },
            {
                "step_id": "step2",
                "agent_id": "agent_2",
                "task_type": "task2",
                "task_data": {"data": "test2"},
            },
        ]

        workflow_id = orchestrator.create_workflow(
            name="Parallel Test",
            steps=steps,
            execution_pattern=ExecutionPattern.PARALLEL,
        )

        # Execute workflow
        results = await orchestrator.execute_workflow(workflow_id)

        assert results["status"] == "completed"
        assert len(results["steps"]) == 2
        assert results["steps"]["step1"]["status"] == "completed"
        assert results["steps"]["step2"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_workflow_with_failure(self, orchestrator, mock_agents):
        """Test workflow execution with step failure."""
        # Register agents including failing agent
        for agent in mock_agents:
            await orchestrator.register_agent(agent)

        # Create workflow with failing step
        steps = [
            {
                "step_id": "step1",
                "agent_id": "agent_1",
                "task_type": "task1",
                "task_data": {"data": "test1"},
            },
            {
                "step_id": "step2",
                "agent_id": "agent_3",  # This agent fails
                "task_type": "task2",
                "task_data": {"data": "test2"},
                "dependencies": ["step1"],
            },
        ]

        workflow_id = orchestrator.create_workflow(
            name="Failure Test",
            steps=steps,
            execution_pattern=ExecutionPattern.SEQUENTIAL,
        )

        # Execute workflow
        results = await orchestrator.execute_workflow(workflow_id)

        assert results["status"] == "failed"
        assert results["steps"]["step1"]["status"] == "completed"
        assert results["steps"]["step2"]["status"] == "failed"
        assert "Mock task failure" in results["steps"]["step2"]["error"]

    @pytest.mark.asyncio
    async def test_workflow_timeout(self, orchestrator, mock_agents):
        """Test workflow step timeout."""

        # Create a mock agent that takes too long
        class SlowAgent(BaseAgent):
            def __init__(self, agent_id: str):
                super().__init__(agent_id, f"Slow Agent {agent_id}")

            async def _execute_task_logic(self, task):
                await asyncio.sleep(2)  # Take longer than timeout
                return TaskResult(success=True, result="slow result")

        slow_agent = SlowAgent("slow_agent")
        await orchestrator.register_agent(slow_agent)

        # Create workflow with short timeout
        steps = [
            {
                "step_id": "slow_step",
                "agent_id": "slow_agent",
                "task_type": "slow_task",
                "task_data": {"data": "test"},
                "timeout": 0.5,  # Short timeout
            }
        ]

        workflow_id = orchestrator.create_workflow(name="Timeout Test", steps=steps)

        # Execute workflow
        results = await orchestrator.execute_workflow(workflow_id)

        assert results["status"] == "failed"
        assert results["steps"]["slow_step"]["status"] == "failed"
        assert "timeout" in results["steps"]["slow_step"]["error"].lower()

    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, orchestrator, mock_agents):
        """Test workflow cancellation."""
        # Register agent
        await orchestrator.register_agent(mock_agents[0])

        # Create workflow
        steps = [
            {
                "step_id": "step1",
                "agent_id": "agent_1",
                "task_type": "task1",
                "task_data": {"data": "test"},
            }
        ]

        workflow_id = orchestrator.create_workflow(name="Cancel Test", steps=steps)

        # Start workflow execution in background
        execution_task = asyncio.create_task(orchestrator.execute_workflow(workflow_id))

        # Brief delay to let execution start
        await asyncio.sleep(0.1)

        # Cancel workflow
        cancelled = await orchestrator.cancel_workflow(workflow_id)
        assert cancelled

        # Wait for execution to complete
        results = await execution_task

        assert results["status"] == "cancelled"

    def test_get_workflow_status(self, orchestrator):
        """Test getting workflow status."""
        # Non-existent workflow
        status = orchestrator.get_workflow_status("non_existent")
        assert status is None

        # Create workflow
        steps = [
            {
                "step_id": "step1",
                "agent_id": "agent1",
                "task_type": "task1",
                "task_data": {},
            }
        ]

        workflow_id = orchestrator.create_workflow("Test", steps)
        status = orchestrator.get_workflow_status(workflow_id)

        assert status is not None
        assert status["workflow_id"] == workflow_id
        assert status["status"] == "pending"

    def test_get_metrics(self, orchestrator):
        """Test getting orchestrator metrics."""
        metrics = orchestrator.get_metrics()

        assert "workflows_executed" in metrics
        assert "workflows_successful" in metrics
        assert "workflows_failed" in metrics
        assert "total_execution_time" in metrics
        assert "average_execution_time" in metrics

        # Initially all should be 0
        assert metrics["workflows_executed"] == 0
        assert metrics["workflows_successful"] == 0
        assert metrics["workflows_failed"] == 0

    def test_get_active_workflows(self, orchestrator):
        """Test getting active workflows."""
        active = orchestrator.get_active_workflows()
        assert isinstance(active, list)
        assert len(active) == 0  # Initially no active workflows

    def test_get_execution_history(self, orchestrator):
        """Test getting execution history."""
        history = orchestrator.get_execution_history()
        assert isinstance(history, list)
        assert len(history) == 0  # Initially no history

        # Test with limit
        limited_history = orchestrator.get_execution_history(limit=5)
        assert isinstance(limited_history, list)


class TestConditionalExecution:
    """Test conditional workflow execution."""

    @pytest.mark.asyncio
    async def test_condition_evaluation(self, orchestrator):
        """Test condition evaluation logic."""
        # Create a simple workflow for testing
        steps = [
            WorkflowStep("step1", "agent1", "task1", {}),
            WorkflowStep("step2", "agent2", "task2", {}),
        ]

        workflow = Workflow("test", "Test", steps)
        workflow.steps["step1"].status = WorkflowStatus.COMPLETED
        workflow.steps["step1"].result = "test_result"

        # Test step result condition
        conditions = {"step_result": ["step1", "test_result"]}

        result = await orchestrator._evaluate_conditions(conditions, workflow)
        assert result is True

        # Test step result condition (false case)
        conditions = {"step_result": ["step1", "different_result"]}

        result = await orchestrator._evaluate_conditions(conditions, workflow)
        assert result is False

        # Test step status condition
        conditions = {"step_status": ["step1", "completed"]}

        result = await orchestrator._evaluate_conditions(conditions, workflow)
        assert result is True


@pytest.mark.asyncio
async def test_orchestrator_shutdown(message_broker):
    """Test orchestrator shutdown."""
    logger = logging.getLogger("test_shutdown")
    orchestrator = WorkflowOrchestrator(message_broker, logger)

    # Register a mock agent
    mock_agent = MockAgent("test_agent")
    await orchestrator.register_agent(mock_agent)

    # Create and start a workflow
    steps = [
        {
            "step_id": "step1",
            "agent_id": "test_agent",
            "task_type": "task1",
            "task_data": {},
        }
    ]

    workflow_id = orchestrator.create_workflow("Test", steps)

    # Shutdown orchestrator
    await orchestrator.shutdown()

    # Verify cleanup
    assert len(orchestrator.agents) == 0
    assert len(orchestrator.active_workflows) == 0


if __name__ == "__main__":
    pytest.main([__file__])
