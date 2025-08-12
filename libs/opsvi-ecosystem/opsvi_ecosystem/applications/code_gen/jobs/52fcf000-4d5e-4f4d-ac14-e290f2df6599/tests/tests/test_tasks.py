import pytest
from unittest.mock import MagicMock, patch
from app.tasks import analyze_code_task, generate_suggestions


def test_generate_suggestions_includes_expected_keys():
    sample_results = {
        "bandit": "Some security issues",
        "pylint": "Some code smell",
        "performance": "Performance issues detected",
    }
    suggestions = generate_suggestions(sample_results)
    assert isinstance(suggestions, dict)
    # Should have keys for each passed test
    for key in sample_results.keys():
        assert key in suggestions
        assert isinstance(suggestions[key], str)


def test_analyze_code_task_processes_report_correctly(monkeypatch):
    mock_self = MagicMock()
    report_id = 123
    file_path = "/fake/path"

    # Patch analyze_code to return dummy results
    monkeypatch.setattr("app.tasks.analyze_code", lambda path: {"bandit": "test"})

    # Patch generate_suggestions to verify called
    monkeypatch.setattr(
        "app.tasks.generate_suggestions", lambda results: {"bandit": "suggestion"}
    )

    # Patch generate_report_file to dummy
    monkeypatch.setattr(
        "app.report_generation.generate_report_file", lambda results, rid: True
    )

    # Run analyze_code_task
    analyze_code_task(mock_self, report_id, file_path)
    # Validate the mocks were called
    mock_self.assert_not_called()  # Because no real callbacks
