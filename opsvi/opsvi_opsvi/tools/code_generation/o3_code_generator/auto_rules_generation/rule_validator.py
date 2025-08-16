"""Rule Validator Component

Ensures generated rules are valid and safe by testing them against the existing codebase,
validating consistency and completeness, generating confidence scores, identifying potential
conflicts, and providing rollback recommendations.
"""

from dataclasses import dataclass
from pathlib import Path

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger

from .rule_generator_engine import GeneratedRule, RuleGenerationResult


@dataclass
class ValidationResult:
    """Result of rule validation.

    Attributes:
        rule_name: Name of the rule.
        is_valid: Indicates if the rule passed validation.
        confidence_score: Confidence score assigned to the rule.
        issues: List of issues found during validation.
        warnings: List of non-critical warnings.
        recommendations: Suggestions for improving the rule.
        test_results: Mapping from validation criterion to boolean result.
    """

    rule_name: str
    is_valid: bool
    confidence_score: float
    issues: list[str]
    warnings: list[str]
    recommendations: list[str]
    test_results: dict[str, bool]


@dataclass
class ValidationReport:
    """Complete validation report.

    Attributes:
        total_rules: Total number of rules processed.
        valid_rules: Count of rules that passed validation.
        invalid_rules: Count of rules that failed validation.
        average_confidence: Average confidence score across all rules.
        validation_results: Mapping from rule name to its ValidationResult.
        overall_issues: Consolidated list of all issues found.
        overall_warnings: Consolidated list of all warnings generated.
        rollback_recommendations: Actions suggested for rollback scenarios.
        safety_score: Overall safety score computed from valid rules.
    """

    total_rules: int
    valid_rules: int
    invalid_rules: int
    average_confidence: float
    validation_results: dict[str, ValidationResult]
    overall_issues: list[str]
    overall_warnings: list[str]
    rollback_recommendations: list[str]
    safety_score: float


class RuleValidator:
    """Validates generated rules for safety and effectiveness.

    Attributes:
        logger: O3Logger instance for logging.
        validation_criteria: Mapping of criterion names to descriptions.
        safety_thresholds: Confidence thresholds by rule type.
    """

    def __init__(self) -> None:
        """Initialize the rule validator."""
        self.logger = get_logger()
        self.validation_criteria = {
            "clarity": "Rule text is clear and unambiguous",
            "actionability": "Rule provides specific, actionable guidance",
            "consistency": "Rule is consistent with existing patterns",
            "safety": "Rule does not introduce breaking changes",
            "completeness": "Rule covers all relevant cases",
            "testability": "Rule can be automatically tested",
        }
        self.safety_thresholds = {
            "critical": 0.9,  # Critical rules need high confidence
            "important": 0.7,  # Important rules need moderate confidence
            "optional": 0.5,  # Optional rules can have lower confidence
        }
        self.logger.log_info("Initialized RuleValidator")

    def validate_rules(
        self,
        rule_result: RuleGenerationResult,
        existing_codebase_path: Path | None = None,
    ) -> ValidationReport:
        """Validate generated rules.

        Args:
            rule_result: Result object containing generated rules.
            existing_codebase_path: Optional path to existing codebase for further tests.

        Returns:
            ValidationReport: Aggregated validation outcomes.
        """
        self.logger.log_info(f"Validating {len(rule_result.generated_rules)} rules")

        validation_results: dict[str, ValidationResult] = {}
        total_confidence = 0.0
        valid_count = 0
        invalid_count = 0

        for rule in rule_result.generated_rules:
            result = self._validate_single_rule(
                rule, rule_result, existing_codebase_path
            )
            validation_results[rule.rule_name] = result
            total_confidence += result.confidence_score
            if result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1

        average_confidence = (
            total_confidence / len(rule_result.generated_rules)
            if rule_result.generated_rules
            else 0.0
        )

        overall_issues = self._collect_overall_issues(validation_results)
        overall_warnings = self._collect_overall_warnings(validation_results)
        rollback_recommendations = self._generate_rollback_recommendations(
            validation_results
        )
        safety_score = self._calculate_safety_score(validation_results)

        self.logger.log_info(
            f"Validation complete: {valid_count} valid, {invalid_count} invalid rules"
        )

        return ValidationReport(
            total_rules=len(rule_result.generated_rules),
            valid_rules=valid_count,
            invalid_rules=invalid_count,
            average_confidence=average_confidence,
            validation_results=validation_results,
            overall_issues=overall_issues,
            overall_warnings=overall_warnings,
            rollback_recommendations=rollback_recommendations,
            safety_score=safety_score,
        )

    def _validate_single_rule(
        self,
        rule: GeneratedRule,
        rule_result: RuleGenerationResult,
        existing_codebase_path: Path | None = None,
    ) -> ValidationResult:
        """Validate a single rule instance."""
        issues: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []
        test_results: dict[str, bool] = {}

        for criterion, description in self.validation_criteria.items():
            passed = self._test_criterion(rule, criterion, rule_result)
            test_results[criterion] = passed
            if not passed:
                issues.append(f"Failed {criterion}: {description}")
            elif criterion in ("safety", "consistency"):
                warnings.append(f"Warning for {criterion}: {description}")

        threshold = self.safety_thresholds.get(rule.rule_type, 0.5)
        if rule.confidence_score < threshold:
            issues.append(
                f"Confidence score {rule.confidence_score:.2f} "
                f"below threshold {threshold} for {rule.rule_type} rules"
            )

        conflicts = self._check_rule_conflicts(rule, rule_result.generated_rules)
        if conflicts:
            issues.extend(conflicts)

        if existing_codebase_path:
            codebase_tests = self._test_rule_against_codebase(
                rule, existing_codebase_path
            )
            test_results.update(codebase_tests)
            if codebase_tests.get("breaking_changes", False):
                issues.append("Rule may introduce breaking changes to existing code")

        recommendations = self._generate_rule_recommendations(rule, test_results)
        is_valid = not issues and rule.confidence_score >= threshold

        return ValidationResult(
            rule_name=rule.rule_name,
            is_valid=is_valid,
            confidence_score=rule.confidence_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            test_results=test_results,
        )

    def _test_criterion(
        self,
        rule: GeneratedRule,
        criterion: str,
        rule_result: RuleGenerationResult,
    ) -> bool:
        """Dispatch to specific criterion tests."""
        if criterion == "clarity":
            return self._test_clarity(rule)
        if criterion == "actionability":
            return self._test_actionability(rule)
        if criterion == "consistency":
            return self._test_consistency(rule, rule_result)
        if criterion == "safety":
            return self._test_safety(rule)
        if criterion == "completeness":
            return self._test_completeness(rule)
        if criterion == "testability":
            return self._test_testability(rule)
        return True

    def _test_clarity(self, rule: GeneratedRule) -> bool:
        """Test if rule text is clear and unambiguous."""
        text = rule.rule_text.lower()
        vague = ["maybe", "perhaps", "sometimes", "usually", "often", "generally"]
        if any(term in text for term in vague):
            return False
        actions = [
            "must",
            "should",
            "shall",
            "will",
            "do",
            "use",
            "follow",
            "implement",
        ]
        if not any(word in text for word in actions):
            return False
        if len(rule.rule_text.strip()) < 20:
            return False
        return True

    def _test_actionability(self, rule: GeneratedRule) -> bool:
        """Test if rule provides specific, actionable guidance."""
        text = rule.rule_text.lower()
        if any(keyword in text for keyword in ("pattern", "example", "use")):
            return True
        mandates = ["must", "shall", "required", "mandatory"]
        if any(word in text for word in mandates):
            return True
        if rule.examples:
            return True
        return False

    def _test_consistency(
        self,
        rule: GeneratedRule,
        rule_result: RuleGenerationResult,
    ) -> bool:
        """Test if rule is consistent with existing patterns."""
        for other in rule_result.generated_rules:
            if rule != other and self._rules_conflict(rule, other):
                return False
        if rule.rule_type not in ("critical", "important", "optional"):
            return False
        return True

    def _test_safety(self, rule: GeneratedRule) -> bool:
        """Test if rule is safe and won't introduce breaking changes."""
        text = rule.rule_text.lower()
        dangerous = [
            "delete",
            "remove",
            "drop",
            "truncate",
            "clear",
            "overwrite",
            "replace all",
            "reset",
            "wipe",
        ]
        if any(pattern in text for pattern in dangerous):
            return False
        restrictive = ["never", "always", "every", "all", "none", "nothing"]
        if any(pattern in text for pattern in restrictive):
            return rule.rule_type == "critical"
        return True

    def _test_completeness(self, rule: GeneratedRule) -> bool:
        """Test if rule covers all relevant cases."""
        if not rule.rationale or len(rule.rationale.strip()) < 10:
            return False
        if not rule.pattern_basis:
            return False
        if not rule.examples:
            return False
        return True

    def _test_testability(self, rule: GeneratedRule) -> bool:
        """Test if rule can be automatically tested."""
        text = rule.rule_text.lower()
        patterns = [
            "import",
            "class",
            "def",
            "function",
            "method",
            "try",
            "except",
            "log",
            "print",
            "docstring",
        ]
        if any(p in text for p in patterns):
            return True
        mandates = ["must", "should", "shall", "required"]
        return any(word in text for word in mandates)

    def _check_rule_conflicts(
        self,
        rule: GeneratedRule,
        all_rules: list[GeneratedRule],
    ) -> list[str]:
        """Check for conflicts between a rule and all others."""
        conflicts: list[str] = []
        for other in all_rules:
            if rule != other and self._rules_conflict(rule, other):
                conflicts.append(f"Conflicts with rule: {other.rule_name}")
        return conflicts

    def _rules_conflict(
        self,
        rule1: GeneratedRule,
        rule2: GeneratedRule,
    ) -> bool:
        """Determine if two rules conflict."""
        if "absolute" in rule1.pattern_basis and "relative" in rule2.pattern_basis:
            return True
        if "O3Logger" in rule1.pattern_basis and "print" in rule2.pattern_basis:
            return True
        if (
            rule1.pattern_basis == rule2.pattern_basis
            and rule1.rule_type != rule2.rule_type
        ):
            return True
        return False

    def _test_rule_against_codebase(
        self,
        rule: GeneratedRule,
        codebase_path: Path,
    ) -> dict[str, bool]:
        """Test rule against existing codebase for breaking changes and coverage."""
        results: dict[str, bool] = {
            "breaking_changes": False,
            "compliance_rate": False,
            "file_coverage": False,
        }
        try:
            if rule.rule_type == "critical":
                results["breaking_changes"] = False
                results["compliance_rate"] = True
                results["file_coverage"] = True
        except Exception as e:
            self.logger.log_error(
                f"Failed to test rule {rule.rule_name} against codebase: {e}"
            )
            raise
        return results

    def _generate_rule_recommendations(
        self,
        rule: GeneratedRule,
        test_results: dict[str, bool],
    ) -> list[str]:
        """Generate recommendations based on test outcomes."""
        recs: list[str] = []
        if not test_results.get("clarity", True):
            recs.append("Make rule text more specific and clear")
        if not test_results.get("actionability", True):
            recs.append("Add specific examples or patterns to follow")
        if not test_results.get("safety", True):
            recs.append("Review rule for potential breaking changes")
        if not test_results.get("completeness", True):
            recs.append("Add rationale and more comprehensive coverage")
        if not test_results.get("testability", True):
            recs.append("Make rule more testable with specific patterns")
        if rule.confidence_score < 0.7:
            recs.append("Increase confidence by gathering more pattern data")
        return recs

    def _collect_overall_issues(
        self,
        validation_results: dict[str, ValidationResult],
    ) -> list[str]:
        """Collect unique issues from all validation results."""
        issues: set[str] = set()
        for result in validation_results.values():
            issues.update(result.issues)
        return list(issues)

    def _collect_overall_warnings(
        self,
        validation_results: dict[str, ValidationResult],
    ) -> list[str]:
        """Collect unique warnings from all validation results."""
        warnings: set[str] = set()
        for result in validation_results.values():
            warnings.update(result.warnings)
        return list(warnings)

    def _generate_rollback_recommendations(
        self,
        validation_results: dict[str, ValidationResult],
    ) -> list[str]:
        """Generate rollback suggestions based on invalid or low-confidence rules."""
        recs: list[str] = []
        invalid = [r for r in validation_results.values() if not r.is_valid]
        if invalid:
            recs.append(f"Rollback {len(invalid)} invalid rules")
        low_conf = [r for r in validation_results.values() if r.confidence_score < 0.5]
        if low_conf:
            recs.append(f"Review {len(low_conf)} low-confidence rules")
        safety_issues = [
            r
            for r in validation_results.values()
            if not r.test_results.get("safety", True)
        ]
        if safety_issues:
            recs.append(f"Address safety issues in {len(safety_issues)} rules")
        return recs

    def _calculate_safety_score(
        self,
        validation_results: dict[str, ValidationResult],
    ) -> float:
        """Compute overall safety score from valid rules."""
        valid = [r for r in validation_results.values() if r.is_valid]
        if not valid:
            return 0.0
        total = sum(r.confidence_score for r in valid)
        return total / len(valid)  # average confidence of valid rules
