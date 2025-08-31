"""
SDLC Quality Gates for phase validation and quality enforcement.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SDLCPhase(Enum):
    """Software Development Lifecycle phases"""

    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    REVIEW = "review"


class ValidationStatus(Enum):
    """Status of validation checks"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    PENDING = "pending"


@dataclass
class ValidationResult:
    """Result of a validation check"""

    check_name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: str = "medium"  # low, medium, high, critical

    @property
    def is_blocking(self) -> bool:
        """Check if this result blocks progression"""
        return self.status == ValidationStatus.FAILED and self.severity in [
            "high",
            "critical",
        ]


@dataclass
class QualityGate:
    """Definition of a quality gate"""

    name: str
    phase: SDLCPhase
    description: str
    validators: List[Callable] = field(default_factory=list)
    required_artifacts: List[str] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    blocking: bool = True
    enabled: bool = True


class SDLCQualityGates:
    """Manages quality gates throughout the SDLC"""

    def __init__(self):
        self.gates: Dict[SDLCPhase, List[QualityGate]] = {}
        self.validation_history: List[Dict[str, Any]] = []
        self.phase_transitions: List[Tuple[SDLCPhase, SDLCPhase]] = []
        self.custom_validators: Dict[str, Callable] = {}
        self._initialize_default_gates()

    def _initialize_default_gates(self):
        """Initialize default quality gates for each phase"""

        # Planning phase gates
        self.register_gate(
            QualityGate(
                name="requirements_completeness",
                phase=SDLCPhase.PLANNING,
                description="Verify requirements are complete and clear",
                required_artifacts=["requirements_doc", "user_stories"],
                success_criteria={"min_requirements": 1, "clarity_score": 0.7},
            )
        )

        # Design phase gates
        self.register_gate(
            QualityGate(
                name="design_review",
                phase=SDLCPhase.DESIGN,
                description="Validate design documents and architecture",
                required_artifacts=["design_doc", "architecture_diagram"],
                success_criteria={"review_approved": True, "patterns_documented": True},
            )
        )

        # Development phase gates
        self.register_gate(
            QualityGate(
                name="code_quality",
                phase=SDLCPhase.DEVELOPMENT,
                description="Ensure code meets quality standards",
                required_artifacts=["source_code"],
                success_criteria={
                    "coverage": 0.8,
                    "lint_pass": True,
                    "no_critical_issues": True,
                },
            )
        )

        # Testing phase gates
        self.register_gate(
            QualityGate(
                name="test_coverage",
                phase=SDLCPhase.TESTING,
                description="Verify adequate test coverage",
                required_artifacts=["test_suite", "test_results"],
                success_criteria={"min_coverage": 0.8, "all_tests_pass": True},
            )
        )

        # Deployment phase gates
        self.register_gate(
            QualityGate(
                name="deployment_readiness",
                phase=SDLCPhase.DEPLOYMENT,
                description="Verify deployment readiness",
                required_artifacts=["deployment_plan", "rollback_plan"],
                success_criteria={"staging_tested": True, "approval_received": True},
            )
        )

    def register_gate(self, gate: QualityGate):
        """Register a quality gate"""
        if gate.phase not in self.gates:
            self.gates[gate.phase] = []

        self.gates[gate.phase].append(gate)
        logger.info(
            f"Registered quality gate '{gate.name}' for phase {gate.phase.value}"
        )

    def register_validator(self, name: str, validator: Callable):
        """Register a custom validator function"""
        self.custom_validators[name] = validator
        logger.debug(f"Registered custom validator: {name}")

    async def validate_phase(
        self, phase: SDLCPhase, context: Dict[str, Any]
    ) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate all quality gates for a phase

        Returns:
            Tuple of (all_passed, results)
        """

        if phase not in self.gates:
            logger.warning(f"No quality gates defined for phase {phase.value}")
            return True, []

        results = []
        all_passed = True

        for gate in self.gates[phase]:
            if not gate.enabled:
                results.append(
                    ValidationResult(
                        check_name=gate.name,
                        status=ValidationStatus.SKIPPED,
                        message=f"Gate '{gate.name}' is disabled",
                    )
                )
                continue

            # Check required artifacts
            artifact_result = self._check_artifacts(gate, context)
            results.append(artifact_result)

            if artifact_result.is_blocking:
                all_passed = False
                continue

            # Run validators
            for validator in gate.validators:
                try:
                    result = await validator(context)
                    if isinstance(result, ValidationResult):
                        results.append(result)
                        if result.is_blocking:
                            all_passed = False
                    else:
                        # Handle boolean returns
                        status = (
                            ValidationStatus.PASSED
                            if result
                            else ValidationStatus.FAILED
                        )
                        results.append(
                            ValidationResult(
                                check_name=validator.__name__,
                                status=status,
                                message=f"Validator {validator.__name__} returned {result}",
                            )
                        )
                        if not result and gate.blocking:
                            all_passed = False

                except Exception as e:
                    logger.error(f"Validator {validator.__name__} failed: {e}")
                    results.append(
                        ValidationResult(
                            check_name=validator.__name__,
                            status=ValidationStatus.FAILED,
                            message=f"Validator error: {str(e)}",
                            severity="high",
                        )
                    )
                    if gate.blocking:
                        all_passed = False

            # Check success criteria
            criteria_result = self._check_criteria(gate, context)
            results.append(criteria_result)
            if criteria_result.is_blocking:
                all_passed = False

        # Record validation
        self._record_validation(phase, results, all_passed)

        return all_passed, results

    def _check_artifacts(
        self, gate: QualityGate, context: Dict[str, Any]
    ) -> ValidationResult:
        """Check if required artifacts are present"""

        artifacts = context.get("artifacts", {})
        missing = []

        for required in gate.required_artifacts:
            if required not in artifacts or not artifacts[required]:
                missing.append(required)

        if missing:
            return ValidationResult(
                check_name=f"{gate.name}_artifacts",
                status=ValidationStatus.FAILED,
                message=f"Missing required artifacts: {', '.join(missing)}",
                details={"missing": missing, "required": gate.required_artifacts},
                severity="high" if gate.blocking else "medium",
            )

        return ValidationResult(
            check_name=f"{gate.name}_artifacts",
            status=ValidationStatus.PASSED,
            message="All required artifacts present",
            details={"artifacts": list(artifacts.keys())},
        )

    def _check_criteria(
        self, gate: QualityGate, context: Dict[str, Any]
    ) -> ValidationResult:
        """Check if success criteria are met"""

        if not gate.success_criteria:
            return ValidationResult(
                check_name=f"{gate.name}_criteria",
                status=ValidationStatus.PASSED,
                message="No specific criteria defined",
            )

        metrics = context.get("metrics", {})
        failed_criteria = []

        for criterion, expected in gate.success_criteria.items():
            actual = metrics.get(criterion)

            if actual is None:
                failed_criteria.append(f"{criterion}: missing")
            elif isinstance(expected, bool):
                if actual != expected:
                    failed_criteria.append(
                        f"{criterion}: expected {expected}, got {actual}"
                    )
            elif isinstance(expected, (int, float)):
                if actual < expected:
                    failed_criteria.append(f"{criterion}: {actual} < {expected}")

        if failed_criteria:
            return ValidationResult(
                check_name=f"{gate.name}_criteria",
                status=ValidationStatus.FAILED,
                message=f"Criteria not met: {'; '.join(failed_criteria)}",
                details={"failed": failed_criteria, "metrics": metrics},
                severity="high" if gate.blocking else "medium",
            )

        return ValidationResult(
            check_name=f"{gate.name}_criteria",
            status=ValidationStatus.PASSED,
            message="All success criteria met",
            details={"criteria": gate.success_criteria, "metrics": metrics},
        )

    def _record_validation(
        self, phase: SDLCPhase, results: List[ValidationResult], passed: bool
    ):
        """Record validation results in history"""

        record = {
            "timestamp": datetime.utcnow(),
            "phase": phase.value,
            "passed": passed,
            "total_checks": len(results),
            "passed_checks": sum(
                1 for r in results if r.status == ValidationStatus.PASSED
            ),
            "failed_checks": sum(
                1 for r in results if r.status == ValidationStatus.FAILED
            ),
            "warnings": sum(1 for r in results if r.status == ValidationStatus.WARNING),
            "results": [
                {
                    "check": r.check_name,
                    "status": r.status.value,
                    "message": r.message,
                    "severity": r.severity,
                }
                for r in results
            ],
        }

        self.validation_history.append(record)

        # Keep only last 100 records
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]

    async def can_transition(
        self, from_phase: SDLCPhase, to_phase: SDLCPhase, context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Check if transition between phases is allowed

        Returns:
            Tuple of (allowed, reason)
        """

        # Validate current phase gates
        passed, results = await self.validate_phase(from_phase, context)

        if not passed:
            blocking_issues = [r for r in results if r.is_blocking]
            return (
                False,
                f"Cannot transition: {len(blocking_issues)} blocking issues in {from_phase.value}",
            )

        # Record transition
        self.phase_transitions.append((from_phase, to_phase))

        return True, f"Transition from {from_phase.value} to {to_phase.value} approved"

    def get_phase_status(self, phase: SDLCPhase) -> Dict[str, Any]:
        """Get status of quality gates for a phase"""

        if phase not in self.gates:
            return {"phase": phase.value, "gates": [], "message": "No gates defined"}

        gates_info = []
        for gate in self.gates[phase]:
            gates_info.append(
                {
                    "name": gate.name,
                    "description": gate.description,
                    "enabled": gate.enabled,
                    "blocking": gate.blocking,
                    "required_artifacts": gate.required_artifacts,
                    "success_criteria": gate.success_criteria,
                }
            )

        # Get recent validations for this phase
        recent_validations = [
            v for v in self.validation_history[-10:] if v["phase"] == phase.value
        ]

        return {
            "phase": phase.value,
            "gates": gates_info,
            "total_gates": len(gates_info),
            "enabled_gates": sum(1 for g in gates_info if g["enabled"]),
            "recent_validations": recent_validations,
        }

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validations"""

        if not self.validation_history:
            return {"total_validations": 0}

        total = len(self.validation_history)
        passed = sum(1 for v in self.validation_history if v["passed"])

        by_phase = {}
        for record in self.validation_history:
            phase = record["phase"]
            if phase not in by_phase:
                by_phase[phase] = {"total": 0, "passed": 0}
            by_phase[phase]["total"] += 1
            if record["passed"]:
                by_phase[phase]["passed"] += 1

        return {
            "total_validations": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": passed / total if total > 0 else 0,
            "by_phase": by_phase,
            "transitions": len(self.phase_transitions),
        }

    def disable_gate(self, phase: SDLCPhase, gate_name: str):
        """Disable a specific quality gate"""

        if phase in self.gates:
            for gate in self.gates[phase]:
                if gate.name == gate_name:
                    gate.enabled = False
                    logger.info(f"Disabled gate '{gate_name}' in phase {phase.value}")
                    return

    def enable_gate(self, phase: SDLCPhase, gate_name: str):
        """Enable a specific quality gate"""

        if phase in self.gates:
            for gate in self.gates[phase]:
                if gate.name == gate_name:
                    gate.enabled = True
                    logger.info(f"Enabled gate '{gate_name}' in phase {phase.value}")
                    return
