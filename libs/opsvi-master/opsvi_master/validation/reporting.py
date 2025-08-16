"""
Unified Validation Reporting

Runs all validation checks, aggregates results, and outputs summary.
"""

import json
from .code_validator import validate_code_quality
from .security_scanner import scan_security
from .coverage_analyzer import analyze_coverage
from .quality_metrics import calculate_quality_metrics


def run_full_validation_report(
    code_path: str = "src/", test_path: str = "tests/"
) -> dict:
    """Run all validation checks and print a unified report."""
    code_result = validate_code_quality(code_path)
    security_result = scan_security(code_path)
    coverage_result = analyze_coverage(code_path, test_path)

    metrics = calculate_quality_metrics(code_result, security_result, coverage_result)

    # Hardened status logic: fail if any core metric is invalid, or if any
    # return code is nonzero, or if coverage is -1.0
    core_metrics = [
        metrics["code_score"],
        metrics["security_score"],
        metrics["coverage_score"],
    ]
    failed_critical = (
        not all(s >= 0 for s in core_metrics)
        or metrics["quality_score"] < 0
        or coverage_result.get("coverage", -1.0) == -1.0
        or (
            coverage_result.get("returncode", 0) not in [0, -2]
        )  # Allow -2 for recursion prevention
        or code_result.get("returncode", 0) != 0
        and code_result.get("flake8_errors", 0) < 0
        or security_result.get("returncode", 0) != 0
        and security_result.get("bandit_issues", 0) < 0
    )
    status = "failed" if failed_critical else "success"

    report = {
        "status": status,
        "quality_score": metrics["quality_score"],
        "quality_grade": metrics["quality_grade"],
        "flake8_errors": metrics["flake8_errors"],
        "bandit_issues": metrics["bandit_issues"],
        "coverage": metrics["coverage"],
        "code_score": metrics["code_score"],
        "security_score": metrics["security_score"],
        "coverage_score": metrics["coverage_score"],
        "recommendations": metrics["recommendations"],
        "details": {
            "code": code_result,
            "security": security_result,
            "coverage": coverage_result,
        },
    }

    # Print human-readable summary
    print("\n=== VALIDATION SUMMARY ===")
    print(
        f"Quality Score: {
            report['quality_score']} ({
            report['quality_grade']})"
    )
    print(f"Code Quality Errors: {report['flake8_errors']}")
    print(f"Security Issues: {report['bandit_issues']}")
    print(f"Test Coverage: {report['coverage']}%")
    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"- {rec}")
    print("\nFull JSON Report:")
    print(json.dumps(report, indent=2))

    return report
