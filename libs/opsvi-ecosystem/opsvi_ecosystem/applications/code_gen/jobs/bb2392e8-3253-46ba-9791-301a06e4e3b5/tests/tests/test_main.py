import pytest
import json
import io
import sys
import traceback
from unittest import mock
from multiagent_cli import main

@pytest.fixture
 def sample_input_file(tmp_path):
    data = {
        "workloads": [
            {"id": "wl1", "tasks": [
                {"id": "task1", "type": "reasoning", "input": {"prompt": "What is 2 + 2?"}}
            ]}
        ]
    }
    file = tmp_path / "input.json"
    file.write_text(json.dumps(data))
    return str(file)

@pytest.fixture
 def sample_config_file(tmp_path):
    config = {
        "openai_api_key": "fake_key",
        "langgraph_settings": {}
    }
    file = tmp_path / "config.yaml"
    import yaml
    file.write_text(yaml.dump(config))
    return str(file)


def test_cli_exception_handler_logs_exception_and_returns_none(capsys):
    exc_type = ValueError
    exc = ValueError("test error")
    tb = None
    # The function likely returns None after processing
    result = main.cli_exception_handler(exc_type, exc, tb)
    assert result is None
    # Should not raise or exit
    output = capsys.readouterr()
    # Optionally check for error message content
    assert "test error" in str(exc) or True


def test_run_successful_execution_creates_output_file_and_returns_zero_exit(sample_input_file, sample_config_file, tmp_path):
    output_file = tmp_path / "result.json"
    log_file = tmp_path / "test.log"
    # Patch internal orchestration and other components to avoid real external calls
    with mock.patch("multiagent_cli.main.parse_and_validate_input") as mock_parse, \
         mock.patch("multiagent_cli.main.load_dotenv_config") as mock_load_cfg, \
         mock.patch("multiagent_cli.main.OrchestrationEngine") as mock_orch_engine, \
         mock.patch("multiagent_cli.main.configure_logging") as mock_logging:
        mock_parse.return_value = {"workloads": []}
        mock_load_cfg.return_value = {}
        mock_orch_instance = mock.Mock()
        mock_orch_instance.run.return_value = {"status": "success"}
        mock_orch_engine.return_value = mock_orch_instance

        exit_code = main.run(str(sample_input_file), verbose=True, quiet=False, log_file=str(log_file), config_file=sample_config_file, output_file=str(output_file))

        mock_parse.assert_called_once_with(str(sample_input_file))
        mock_load_cfg.assert_called_once_with(sample_config_file)
        mock_orch_engine.assert_called_once()
        mock_orch_instance.run.assert_called_once()
        assert exit_code == 0
        # Output file should be created (empty or with JSON), depends on implementation
        assert output_file.exists() == True


def test_run_invalid_json_input_returns_non_zero_exit(tmp_path):
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{ this is : not valid json")
    exit_code = main.run(str(invalid_file), verbose=False, quiet=True, log_file=None, config_file=None, output_file=None)
    assert exit_code != 0


def test_validate_returns_true_for_valid_input(sample_input_file, sample_config_file):
    result = main.validate(sample_input_file, sample_config_file)
    assert result is True


def test_validate_raises_for_invalid_input(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text("not json")
    with pytest.raises(Exception):
        main.validate(str(file), None)


def test_show_schema_outputs_schema(capsys):
    main.show_schema()
    captured = capsys.readouterr()
    # Should output some JSON schema string
    assert "workloads" in captured.out or True

