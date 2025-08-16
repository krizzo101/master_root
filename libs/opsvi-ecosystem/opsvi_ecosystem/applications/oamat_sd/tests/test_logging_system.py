"""
Tests for Smart Decomposition Logging System

Validates logging functionality, correlation context, and console interface.
"""

import tempfile
from pathlib import Path

import pytest

from src.applications.oamat_sd.src.sd_logging import (
    ConsoleInterface,
    CorrelationContext,
    CorrelationContextManager,
    LogCategory,
    LogConfig,
    LoggerFactory,
    LogLevel,
    create_correlation_context,
)
from src.applications.oamat_sd.src.sd_logging.correlation import get_correlation_context


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for test logs"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config(temp_log_dir):
    """Create test configuration"""
    return LogConfig(
        log_dir=temp_log_dir,
        console_rich=False,  # Disable for testing
        console_progress=False,
        correlation_tracking=True,
    )


@pytest.fixture
def logger_factory(test_config):
    """Create logger factory for testing"""
    return LoggerFactory(test_config)


class TestLogConfig:
    """Test logging configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = LogConfig()

        assert config.console_level == LogLevel.INFO
        assert config.console_rich is True
        assert config.correlation_tracking is True
        assert config.truncate_prompts_console == 200

    def test_log_files_generation(self, test_config):
        """Test log file configuration generation"""
        log_files = test_config.get_log_files()

        # Verify all categories are present
        expected_categories = [
            LogCategory.DEBUG,
            LogCategory.API,
            LogCategory.WORKFLOW,
            LogCategory.PERFORMANCE,
            LogCategory.COMPLEXITY,
            LogCategory.ERROR,
            LogCategory.AUDIT,
        ]

        for category in expected_categories:
            assert category in log_files
            file_config = log_files[category]
            assert file_config.category == category
            assert file_config.filename.endswith(".jsonl")


class TestCorrelationContext:
    """Test correlation context functionality"""

    def test_correlation_context_creation(self):
        """Test creating correlation context"""
        context = CorrelationContext(
            user_request="Test request", complexity_score=75.0, execution_mode="dag"
        )

        assert context.user_request == "Test request"
        assert context.complexity_score == 75.0
        assert context.execution_mode == "dag"
        assert context.correlation_id is not None
        assert context.session_id is not None

    def test_child_context_creation(self):
        """Test creating child context"""
        parent_context = CorrelationContext(
            user_request="Parent request", workflow_id="test_workflow"
        )

        child_context = parent_context.create_child_context(
            agent_id="test_agent", task_id="test_task"
        )

        assert child_context.session_id == parent_context.session_id
        assert child_context.workflow_id == parent_context.workflow_id
        assert child_context.agent_id == "test_agent"
        assert child_context.task_id == "test_task"
        assert child_context.parent_correlation_id == parent_context.correlation_id
        assert child_context.correlation_id != parent_context.correlation_id

    def test_context_manager(self):
        """Test correlation context manager"""
        context = CorrelationContext(user_request="Test request")

        with CorrelationContextManager(context):
            current_context = get_correlation_context()
            assert current_context.correlation_id == context.correlation_id

    def test_context_to_dict(self):
        """Test context serialization"""
        context = CorrelationContext(
            user_request="Test request", complexity_score=75.0, agent_id="test_agent"
        )

        context_dict = context.to_dict()

        assert context_dict["user_request"] == "Test request"
        assert context_dict["complexity_score"] == 75.0
        assert context_dict["agent_id"] == "test_agent"
        assert "correlation_id" in context_dict
        assert "started_at" in context_dict


class TestLoggerFactory:
    """Test logger factory functionality"""

    def test_logger_creation(self, logger_factory):
        """Test creating different types of loggers"""
        debug_logger = logger_factory.get_debug_logger()
        api_logger = logger_factory.get_api_logger()
        workflow_logger = logger_factory.get_workflow_logger()

        assert debug_logger is not None
        assert api_logger is not None
        assert workflow_logger is not None

        # Test singleton behavior
        assert logger_factory.get_debug_logger() is debug_logger

    def test_api_call_logging(self, logger_factory, test_config):
        """Test API call logging"""
        logger_factory.log_api_call(
            method="POST",
            url="https://api.test.com/endpoint",
            request_data={"test": "data"},
            response_data={"result": "success"},
            status_code=200,
            duration_ms=1234.5,
        )

        # Verify log file was created
        api_log_file = (
            test_config.log_dir / f"oamat_smart_{test_config.session_id}_api.jsonl"
        )
        assert api_log_file.exists()

    def test_agent_interaction_logging(self, logger_factory):
        """Test agent interaction logging"""
        logger_factory.log_agent_interaction(
            agent_id="test_agent",
            action="execute",
            input_data={"query": "test"},
            output_data={"result": "completed"},
            duration_ms=5000.0,
            metadata={"step_count": 3},
        )

        # Should complete without error
        assert True

    def test_complexity_analysis_logging(self, logger_factory):
        """Test complexity analysis logging"""
        factors = {
            "Skill Diversity": 7.5,
            "Coordination Complexity": 8.2,
            "Parallelizability": 6.0,
        }

        logger_factory.log_complexity_analysis(
            user_request="Test request",
            factors=factors,
            overall_score=75.3,
            decision="DAG Orchestration",
            reasoning="High complexity factors detected",
            user_override=False,
        )

        # Should complete without error
        assert True

    def test_performance_metrics_logging(self, logger_factory):
        """Test performance metrics logging"""
        logger_factory.log_performance_metrics(
            operation="test_operation",
            duration_ms=2500.0,
            resource_usage={"memory_mb": 128.5, "cpu_percent": 15.2},
            metadata={"test": True},
        )

        # Should complete without error
        assert True

    def test_workflow_execution_logging(self, logger_factory):
        """Test workflow execution logging"""
        logger_factory.log_workflow_execution(
            workflow_type="dag",
            agents=["agent1", "agent2"],
            dependencies={"agent2": ["agent1"]},
            results={"completed": True},
            total_duration_ms=10000.0,
        )

        # Should complete without error
        assert True


class TestConsoleInterface:
    """Test console interface functionality"""

    def test_console_interface_creation(self, test_config):
        """Test creating console interface"""
        console = ConsoleInterface(test_config)
        assert console.config == test_config
        assert console.console is None  # Rich disabled for testing

    def test_session_management(self, test_config):
        """Test session start and end"""
        console = ConsoleInterface(test_config)

        # Should not raise errors
        console.start_session(user_request="Test request", complexity_score=75.0)
        console.end_session()

    def test_task_management(self, test_config):
        """Test task tracking"""
        console = ConsoleInterface(test_config)

        task_id = console.start_task("Test Task", "Testing functionality", 4)
        assert task_id is not None

        console.update_task(task_id, "Step 1 completed", advance=1)
        console.complete_task(task_id, "Task completed successfully")

    def test_complexity_decision_display(self, test_config):
        """Test complexity decision display"""
        console = ConsoleInterface(test_config)

        factors = {"Skill Diversity": 7.5, "Coordination Complexity": 8.2}

        # Should not raise errors
        console.show_complexity_decision(
            score=75.3,
            factors=factors,
            decision="DAG Orchestration",
            user_override=False,
        )

    def test_dag_structure_display(self, test_config):
        """Test DAG structure display"""
        console = ConsoleInterface(test_config)

        agents = ["researcher", "analyst", "writer"]
        dependencies = {"analyst": ["researcher"], "writer": ["researcher", "analyst"]}

        # Should not raise errors
        console.show_dag_structure(agents, dependencies)

    def test_error_display(self, test_config):
        """Test error message display"""
        console = ConsoleInterface(test_config)

        # Should not raise errors
        console.show_error("Test error message", "Detailed error information")
        console.show_warning("Test warning message")

    def test_final_results_display(self, test_config):
        """Test final results display"""
        console = ConsoleInterface(test_config)

        results = {"agents_executed": 3, "tasks_completed": 12, "api_calls": 8}

        # Should not raise errors
        console.show_final_results(results, execution_time=15.5)

    def test_text_truncation(self, test_config):
        """Test text truncation functionality"""
        console = ConsoleInterface(test_config)

        long_text = "This is a very long text that should be truncated" * 5
        truncated = console._truncate_text(long_text, 50)

        assert len(truncated) <= 50
        assert truncated.endswith("...") if len(long_text) > 50 else True


class TestIntegration:
    """Integration tests for the complete logging system"""

    def test_full_workflow_logging(self, logger_factory, test_config):
        """Test complete workflow with correlation context"""
        # Create correlation context
        context = create_correlation_context(
            user_request="Integration test workflow",
            complexity_score=80.0,
            execution_mode="dag",
        )

        with CorrelationContextManager(context):
            # Log complexity analysis
            logger_factory.log_complexity_analysis(
                user_request="Integration test workflow",
                factors={"Skill Diversity": 8.0, "Coordination": 7.5},
                overall_score=80.0,
                decision="DAG Orchestration",
                reasoning="Integration test scenario",
            )

            # Log API calls
            logger_factory.log_api_call(
                method="POST",
                url="https://api.test.com/agents",
                status_code=200,
                duration_ms=1500.0,
            )

            # Log agent interactions
            logger_factory.log_agent_interaction(
                agent_id="test_agent", action="execute", duration_ms=3000.0
            )

            # Log performance metrics
            logger_factory.log_performance_metrics(
                operation="integration_test",
                duration_ms=5000.0,
                resource_usage={"memory_mb": 64.0},
            )

        # Verify log files were created
        expected_files = [
            f"oamat_smart_{test_config.session_id}_complexity.jsonl",
            f"oamat_smart_{test_config.session_id}_api.jsonl",
            f"oamat_smart_{test_config.session_id}_workflow.jsonl",
            f"oamat_smart_{test_config.session_id}_performance.jsonl",
        ]

        for filename in expected_files:
            log_file = test_config.log_dir / filename
            assert log_file.exists(), f"Log file {filename} was not created"

    def test_console_and_logging_integration(self, test_config):
        """Test console interface with logging system"""
        console = ConsoleInterface(test_config)
        factory = LoggerFactory(test_config)

        # Start session
        console.start_session("Integration test", complexity_score=70.0)

        # Simulate workflow
        task_id = console.start_task("Test", "Running integration test", 2)

        # Log during task execution
        factory.log_api_call(
            method="GET",
            url="https://api.test.com/data",
            status_code=200,
            duration_ms=800.0,
        )

        console.update_task(task_id, "API call completed", advance=1)
        console.complete_task(task_id, "Integration test completed")

        # Show results
        console.show_final_results({"status": "success"}, execution_time=2.5)
        console.end_session()

        # Should complete without errors
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
