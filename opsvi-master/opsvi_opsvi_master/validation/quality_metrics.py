"""
Quality Metrics Calculator

Aggregates code quality, security, and coverage metrics into a single report.
"""

from typing import Dict
import math


def calculate_quality_metrics(code: Dict, security: Dict, coverage: Dict) -> Dict:
    """Calculate comprehensive quality metrics from validation results.

    Args:
        code: Results from code quality validation (flake8)
        security: Results from security scanning (bandit)
        coverage: Results from test coverage analysis

    Returns:
        Dict containing aggregated metrics and quality score
    """
    # Extract metrics with safe defaults
    flake8_errors = code.get("flake8_errors", -1)
    bandit_issues = security.get("bandit_issues", -1)
    coverage_pct = coverage.get("coverage", -1.0)

    # Calculate component scores (0-100 scale)
    code_score = _calculate_code_score(flake8_errors)
    security_score = _calculate_security_score(security)
    coverage_score = _calculate_coverage_score(coverage_pct)

    # Calculate weighted overall quality score
    quality_score = _calculate_overall_score(code_score, security_score, coverage_score)

    # Determine quality grade
    quality_grade = _get_quality_grade(quality_score)

    return {
        "flake8_errors": flake8_errors,
        "bandit_issues": bandit_issues,
        "coverage": coverage_pct,
        "code_score": code_score,
        "security_score": security_score,
        "coverage_score": coverage_score,
        "quality_score": quality_score,
        "quality_grade": quality_grade,
        "recommendations": _generate_recommendations(code, security, coverage),
    }


def _calculate_code_score(flake8_errors: int) -> float:
    """Calculate code quality score based on flake8 errors."""
    if flake8_errors < 0:
        return -1.0  # Invalid/failed
    elif flake8_errors == 0:
        return 100.0
    else:
        # Exponential decay: score decreases rapidly with more errors
        return max(0.0, 100.0 * math.exp(-0.1 * flake8_errors))


def _calculate_security_score(security: Dict) -> float:
    """Calculate security score based on bandit issues with severity weighting."""
    bandit_issues = security.get("bandit_issues", -1)
    if bandit_issues < 0:
        return -1.0  # Invalid/failed
    elif bandit_issues == 0:
        return 100.0

    # Try to get severity breakdown from output if available
    output = security.get("output", "")
    high_severity = output.count('"SEVERITY.HIGH"') if output else 0
    medium_severity = output.count('"SEVERITY.MEDIUM"') if output else 0
    low_severity = output.count('"SEVERITY.LOW"') if output else 0

    # Weight severity: HIGH=10, MEDIUM=3, LOW=1
    weighted_issues = (high_severity * 10) + (medium_severity * 3) + low_severity

    if weighted_issues == 0:
        return 100.0
    else:
        return max(0.0, 100.0 * math.exp(-0.05 * weighted_issues))


def _calculate_coverage_score(coverage_pct: float) -> float:
    """Calculate coverage score with realistic thresholds."""
    if coverage_pct < 0:
        return -1.0  # Invalid/failed
    elif coverage_pct >= 95:
        return 100.0
    elif coverage_pct >= 80:
        # 80-100 scale
        return 80.0 + (coverage_pct - 80) * (20.0 / 15.0)
    elif coverage_pct >= 60:
        # 60-80 scale
        return 60.0 + (coverage_pct - 60) * (20.0 / 20.0)
    else:
        return coverage_pct  # Direct mapping for <60%


def _calculate_overall_score(
    code_score: float, security_score: float, coverage_score: float
) -> float:
    """Calculate weighted overall quality score."""
    # Handle failed validations
    valid_scores = [s for s in [code_score, security_score, coverage_score] if s >= 0]
    if not valid_scores:
        return -1.0

    # Weights: Code 30%, Security 40%, Coverage 30%
    weights = [0.3, 0.4, 0.3]
    scores = [code_score, security_score, coverage_score]

    # Adjust weights for missing scores
    adjusted_weights = []
    adjusted_scores = []
    for score, weight in zip(scores, weights):
        if score >= 0:
            adjusted_weights.append(weight)
            adjusted_scores.append(score)

    # Normalize weights
    total_weight = sum(adjusted_weights)
    if total_weight == 0:
        return -1.0

    normalized_weights = [w / total_weight for w in adjusted_weights]

    # Calculate weighted average
    return round(sum(s * w for s, w in zip(adjusted_scores, normalized_weights)), 1)


def _get_quality_grade(score: float) -> str:
    """Convert quality score to letter grade."""
    if score < 0:
        return "FAILED"
    elif score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _generate_recommendations(code: Dict, security: Dict, coverage: Dict) -> list:
    """Generate actionable recommendations based on validation results."""
    recommendations = []

    flake8_errors = code.get("flake8_errors", 0)
    if flake8_errors > 0:
        recommendations.append(
            f"Fix {flake8_errors} code style issues (run: flake8 src/)"
        )

    bandit_issues = security.get("bandit_issues", 0)
    if bandit_issues > 0:
        recommendations.append(
            f"Address {bandit_issues} security issues (run: bandit -r src/)"
        )

    coverage_pct = coverage.get("coverage", 0)
    if 0 <= coverage_pct < 80:
        recommendations.append(
            f"Increase test coverage from {coverage_pct}% to 80%+ (add more tests)"
        )

    if coverage.get("returncode", 0) != 0:
        recommendations.append("Fix test failures preventing coverage analysis")

    if not recommendations:
        recommendations.append("All validation checks passing - excellent work!")

    return recommendations
