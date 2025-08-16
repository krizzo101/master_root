import pytest
from app.code_analysis import (
    AnalysisError,
    analyze_code,
    run_subprocess,
)


def test_run_subprocess_executes_command_and_returns_output():
    output = run_subprocess(["echo", "hello"], cwd=None, timeout=5)
    assert "hello" in output


def test_run_subprocess_raises_on_timeout():
    with pytest.raises(AnalysisError):
        # Run a command guaranteed to timeout
        run_subprocess(["sleep", "2"], cwd=None, timeout=0.1)


@pytest.mark.parametrize(
    "func,expected_substr",
    [
        ("run_bandit", "bandit"),
        ("run_pylint", "pylint"),
        ("run_radon_cc", "radon cc"),
        ("run_radon_mi", "radon mi"),
        ("run_flake8", "flake8"),
        ("run_performance_heuristic", "performance"),
    ],
)
def test_analysis_functions_call_run_subprocess(monkeypatch, func, expected_substr):
    """Test each analysis runner calls run_subprocess with the expected command."""
    import app.code_analysis as ca

    called = {}

    def mock_run_subprocess(cmd, cwd=None, timeout=None):
        called["cmd"] = cmd
        return "output"

    monkeypatch.setattr(ca, "run_subprocess", mock_run_subprocess)

    f = getattr(ca, func)
    output = f("/fake/path")
    assert output == "output"
    # Ensure the command includes expected_substr
    cmd_str = " ".join(called["cmd"]).lower()
    assert expected_substr in cmd_str


def test_analyze_code_combines_all_results(monkeypatch):
    import app.code_analysis as ca

    monkeypatch.setattr(ca, "run_bandit", lambda path: "bandit_results")
    monkeypatch.setattr(ca, "run_pylint", lambda path: "pylint_results")
    monkeypatch.setattr(ca, "run_radon_cc", lambda path: "radon_cc_results")
    monkeypatch.setattr(ca, "run_radon_mi", lambda path: "radon_mi_results")
    monkeypatch.setattr(ca, "run_flake8", lambda path: "flake8_results")
    monkeypatch.setattr(
        ca, "run_performance_heuristic", lambda path: "performance_results"
    )

    results = analyze_code("/fake/path")
    # The results should contain the keys and correct results
    for key in ["bandit", "pylint", "radon_cc", "radon_mi", "flake8", "performance"]:
        assert key in results
        assert results[key].endswith("_results")
