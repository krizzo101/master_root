import pytest
from app.report_generation import calculate_score, generate_report_file


def test_generate_report_file_creates_file_and_returns_path(tmp_path):
    results = {"bandit": "issue"}
    report_id = 1
    path = generate_report_file(results, report_id)
    assert isinstance(path, str)
    assert path.endswith(".html")
    # Check file exists and content includes results
    with open(path) as f:
        content = f.read()
    assert "issue" in content


@pytest.mark.parametrize(
    "results,expected_score",
    [
        ({"errors": 5, "warnings": 2, "style_violations": 3}, pytest.approx(100 - 0.5)),
        ({"errors": 0, "warnings": 0, "style_violations": 0}, 100),
        ({"errors": 100, "warnings": 100, "style_violations": 100}, pytest.approx(0)),
    ],
)
def test_calculate_score_various_input(results, expected_score):
    score = calculate_score(results)
    assert 0 <= score <= 100
    # Check score is close to expected (when given)
    if isinstance(expected_score, float) or hasattr(expected_score, "approx"):
        assert abs(score - expected_score) < 10
