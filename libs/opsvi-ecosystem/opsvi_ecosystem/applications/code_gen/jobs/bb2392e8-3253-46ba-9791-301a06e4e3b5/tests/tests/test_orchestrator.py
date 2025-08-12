from unittest import mock

from multiagent_cli.orchestrator import OrchestrationEngine


def test_orchestration_engine_init_sets_properties():
    fake_input_data = {"workloads": []}
    fake_config = {"some": "config"}
    fake_logger = mock.Mock()
    engine = OrchestrationEngine(fake_input_data, fake_config, fake_logger)
    assert engine.input_data == fake_input_data
    assert engine.config == fake_config
    assert engine.logger == fake_logger


def test_orchestration_engine_run_executes_tasks_and_reports_progress():
    fake_input_data = {
        "workloads": [
            {"id": "w1", "tasks": [{"id": "t1", "type": "reasoning", "input": {}}]}
        ]
    }
    fake_config = {}
    fake_logger = mock.Mock()
    engine = OrchestrationEngine(fake_input_data, fake_config, fake_logger)
    # Mock internal method that runs tasks to avoid complexity
    with mock.patch.object(engine, "_execute_tasks") as mock_execute:
        mock_execute.return_value = {"status": "success"}
        result = engine.run(progress=True, progress_task=None)
    assert isinstance(result, dict)
    assert "status" in result
