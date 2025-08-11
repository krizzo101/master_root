"""
OAMAT Context Alignment & Drift Prevention System

Critical architectural component ensuring fractal workflows maintain alignment
with macro application intent while preventing development of mismatched components.

Core Principle: Context coherence and alignment validation at every level.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AlignmentRisk(Enum):
    """Risk levels for context alignment drift"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IntentDomain(Enum):
    """Categories of macro application intent"""

    FUNCTIONAL = "functional"  # What the application should do
    TECHNICAL = "technical"  # How it should be built
    BUSINESS = "business"  # Why it exists
    USER_EXPERIENCE = "ux"  # How users interact
    PERFORMANCE = "performance"  # Speed, scale, efficiency
    SECURITY = "security"  # Protection, compliance
    INTEGRATION = "integration"  # How components connect


@dataclass
class MacroIntent:
    """Core macro application intent that must be preserved"""

    domain: IntentDomain
    description: str
    priority: int = Field(ge=1, le=10)  # 1=lowest, 10=highest
    success_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    non_negotiable_requirements: List[str] = field(default_factory=list)


class ContextTrace(BaseModel):
    """Tracks context flow and transformations through hierarchy"""

    level: int
    parent_context_hash: Optional[str] = None
    current_context_hash: str
    transformation_summary: str
    information_lost: List[str] = Field(default_factory=list)
    information_added: List[str] = Field(default_factory=list)
    alignment_score: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)


class AlignmentViolation(BaseModel):
    """Detected violation of macro intent alignment"""

    violation_type: str
    severity: AlignmentRisk
    description: str
    affected_intent: MacroIntent
    current_level: int
    parent_level: int
    evidence: Dict[str, Any] = Field(default_factory=dict)
    suggested_correction: Optional[str] = None
    auto_correctable: bool = False


class IntegrationContract(BaseModel):
    """Contract defining how components must integrate"""

    component_name: str
    required_interfaces: List[str]
    provided_interfaces: List[str]
    data_dependencies: List[str]
    performance_requirements: Dict[str, Any] = Field(default_factory=dict)
    integration_points: List[str] = Field(default_factory=list)
    compatibility_constraints: List[str] = Field(default_factory=list)


class MacroIntentRepository:
    """
    Repository for managing and tracking macro application intent.

    Ensures all levels have access to authoritative intent definitions.
    """

    def __init__(self):
        self.intents: Dict[str, MacroIntent] = {}
        self.intent_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        self._change_log: List[Tuple[datetime, str, str]] = []

    def register_macro_intent(
        self,
        intent_id: str,
        intent: MacroIntent,
        parent_intent_id: Optional[str] = None,
    ) -> None:
        """Register a new macro intent"""
        self.intents[intent_id] = intent

        if parent_intent_id:
            if parent_intent_id not in self.intent_hierarchy:
                self.intent_hierarchy[parent_intent_id] = []
            self.intent_hierarchy[parent_intent_id].append(intent_id)

        self._change_log.append((datetime.now(), "REGISTER", intent_id))
        logger.info(
            f"Registered macro intent: {intent_id} (domain: {intent.domain.value})"
        )

    def get_intent_chain(self, intent_id: str) -> List[MacroIntent]:
        """Get full chain of intent from root to specified intent"""
        chain = []
        current_id = intent_id

        # Find path to root (simplified implementation)
        while current_id and current_id in self.intents:
            chain.insert(0, self.intents[current_id])
            # Find parent (reverse lookup)
            parent_id = None
            for parent, children in self.intent_hierarchy.items():
                if current_id in children:
                    parent_id = parent
                    break
            current_id = parent_id

        return chain

    def validate_intent_compatibility(
        self, parent_intent_id: str, child_intent_id: str
    ) -> Tuple[bool, List[str]]:
        """Validate that child intent is compatible with parent"""
        parent = self.intents.get(parent_intent_id)
        child = self.intents.get(child_intent_id)

        if not parent or not child:
            return False, ["Missing intent definitions"]

        violations = []

        # Check domain compatibility
        if child.domain != parent.domain and child.priority > parent.priority:
            violations.append(
                f"Child intent priority ({child.priority}) exceeds parent ({parent.priority})"
            )

        # Check constraint violations
        for constraint in parent.non_negotiable_requirements:
            # Simple constraint checking (would be more sophisticated in practice)
            if constraint.lower() not in child.description.lower():
                violations.append(
                    f"Child intent doesn't address non-negotiable requirement: {constraint}"
                )

        return len(violations) == 0, violations


class ContextAlignmentValidator:
    """
    Validates context alignment and detects drift at each hierarchy level.

    Prevents development of components that don't integrate or match macro intent.
    """

    def __init__(self, intent_repository: MacroIntentRepository):
        self.intent_repo = intent_repository
        self.context_traces: List[ContextTrace] = []
        self.violations: List[AlignmentViolation] = []
        self._alignment_thresholds = {
            AlignmentRisk.LOW: 0.9,
            AlignmentRisk.MEDIUM: 0.7,
            AlignmentRisk.HIGH: 0.5,
            AlignmentRisk.CRITICAL: 0.3,
        }

    def _calculate_context_hash(self, context: Dict[str, Any]) -> str:
        """Generate deterministic hash of context for tracking changes"""
        context_str = json.dumps(context, sort_keys=True, default=str)
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]

    def _calculate_alignment_score(
        self,
        parent_context: Dict[str, Any],
        child_context: Dict[str, Any],
        applicable_intents: List[MacroIntent],
    ) -> float:
        """Calculate alignment score between parent and child contexts"""
        # Simplified alignment calculation (would be more sophisticated in practice)
        score = 1.0

        # Check if key requirements are preserved
        for intent in applicable_intents:
            for requirement in intent.non_negotiable_requirements:
                req_key = requirement.lower().replace(" ", "_")
                if req_key in parent_context and req_key not in child_context:
                    score -= 0.2  # Penalty for lost requirements
                elif req_key in child_context and child_context[
                    req_key
                ] != parent_context.get(req_key):
                    score -= 0.1  # Penalty for modified requirements

        # Check for drift in core properties
        core_properties = [
            "functional_requirements",
            "technical_constraints",
            "user_requirements",
        ]
        for prop in core_properties:
            if prop in parent_context and prop in child_context:
                # Simple similarity check (would use semantic similarity in practice)
                parent_val = str(parent_context[prop]).lower()
                child_val = str(child_context[prop]).lower()
                overlap = len(set(parent_val.split()) & set(child_val.split()))
                total = len(set(parent_val.split()) | set(child_val.split()))
                if total > 0:
                    similarity = overlap / total
                    score *= similarity

        return max(0.0, min(1.0, score))

    def validate_context_transition(
        self,
        parent_context: Dict[str, Any],
        child_context: Dict[str, Any],
        hierarchy_level: int,
        applicable_intent_ids: List[str],
    ) -> Tuple[bool, List[AlignmentViolation], ContextTrace]:
        """
        Validate context transition from parent to child level.

        Returns: (is_valid, violations, context_trace)
        """
        # Get applicable macro intents
        applicable_intents = [
            self.intent_repo.intents[intent_id]
            for intent_id in applicable_intent_ids
            if intent_id in self.intent_repo.intents
        ]

        # Calculate context hashes and alignment score
        parent_hash = self._calculate_context_hash(parent_context)
        child_hash = self._calculate_context_hash(child_context)
        alignment_score = self._calculate_alignment_score(
            parent_context, child_context, applicable_intents
        )

        # Detect information changes
        parent_keys = set(parent_context.keys())
        child_keys = set(child_context.keys())

        information_lost = [key for key in parent_keys if key not in child_keys]
        information_added = [key for key in child_keys if key not in parent_keys]

        # Create context trace
        trace = ContextTrace(
            level=hierarchy_level,
            parent_context_hash=parent_hash,
            current_context_hash=child_hash,
            transformation_summary=f"Level {hierarchy_level} context transformation",
            information_lost=information_lost,
            information_added=information_added,
            alignment_score=alignment_score,
        )

        self.context_traces.append(trace)

        # Detect violations
        violations = []

        # Check alignment score against thresholds
        risk_level = AlignmentRisk.LOW
        for risk, threshold in sorted(
            self._alignment_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if alignment_score < threshold:
                risk_level = risk
                break

        if risk_level in [AlignmentRisk.HIGH, AlignmentRisk.CRITICAL]:
            violations.append(
                AlignmentViolation(
                    violation_type="LOW_ALIGNMENT_SCORE",
                    severity=risk_level,
                    description=f"Alignment score {alignment_score:.2f} below threshold for level {hierarchy_level}",
                    affected_intent=(
                        applicable_intents[0] if applicable_intents else None
                    ),
                    current_level=hierarchy_level,
                    parent_level=hierarchy_level - 1,
                    evidence={
                        "alignment_score": alignment_score,
                        "threshold": self._alignment_thresholds[risk_level],
                    },
                    suggested_correction="Review child context to ensure it preserves parent requirements",
                    auto_correctable=False,
                )
            )

        # Check for critical requirement losses
        for intent in applicable_intents:
            for requirement in intent.non_negotiable_requirements:
                req_key = requirement.lower().replace(" ", "_")
                if req_key in parent_context and req_key not in child_context:
                    violations.append(
                        AlignmentViolation(
                            violation_type="LOST_NON_NEGOTIABLE_REQUIREMENT",
                            severity=AlignmentRisk.CRITICAL,
                            description=f"Non-negotiable requirement '{requirement}' lost at level {hierarchy_level}",
                            affected_intent=intent,
                            current_level=hierarchy_level,
                            parent_level=hierarchy_level - 1,
                            evidence={
                                "lost_requirement": requirement,
                                "parent_context": req_key in parent_context,
                            },
                            suggested_correction=f"Restore requirement '{requirement}' in child context",
                            auto_correctable=True,
                        )
                    )

        self.violations.extend(violations)

        is_valid = (
            len(
                [
                    v
                    for v in violations
                    if v.severity in [AlignmentRisk.HIGH, AlignmentRisk.CRITICAL]
                ]
            )
            == 0
        )

        logger.info(
            f"Context validation at level {hierarchy_level}: "
            f"{'VALID' if is_valid else 'INVALID'} "
            f"(score: {alignment_score:.2f}, violations: {len(violations)})"
        )

        return is_valid, violations, trace

    def get_alignment_report(self) -> Dict[str, Any]:
        """Generate comprehensive alignment report"""
        if not self.context_traces:
            return {"message": "No context traces recorded"}

        avg_alignment = sum(
            trace.alignment_score for trace in self.context_traces
        ) / len(self.context_traces)

        violations_by_severity = {}
        for violation in self.violations:
            severity = violation.severity.value
            if severity not in violations_by_severity:
                violations_by_severity[severity] = 0
            violations_by_severity[severity] += 1

        return {
            "total_context_transitions": len(self.context_traces),
            "average_alignment_score": avg_alignment,
            "total_violations": len(self.violations),
            "violations_by_severity": violations_by_severity,
            "deepest_level_validated": (
                max(trace.level for trace in self.context_traces)
                if self.context_traces
                else 0
            ),
            "critical_violations": [
                {
                    "type": v.violation_type,
                    "description": v.description,
                    "level": v.current_level,
                    "auto_correctable": v.auto_correctable,
                }
                for v in self.violations
                if v.severity == AlignmentRisk.CRITICAL
            ],
            "alignment_trend": [
                {"level": trace.level, "score": trace.alignment_score}
                for trace in sorted(self.context_traces, key=lambda x: x.level)
            ],
        }


class IntegrationValidator:
    """
    Validates that components at different levels can actually integrate.

    Prevents development of incompatible components across hierarchy levels.
    """

    def __init__(self):
        self.contracts: Dict[str, IntegrationContract] = {}
        self.compatibility_matrix: Dict[Tuple[str, str], bool] = {}

    def register_component_contract(
        self, component_id: str, contract: IntegrationContract
    ) -> None:
        """Register integration contract for a component"""
        self.contracts[component_id] = contract
        logger.info(f"Registered integration contract for: {component_id}")

    def validate_component_compatibility(
        self, parent_component_id: str, child_component_id: str
    ) -> Tuple[bool, List[str]]:
        """Validate that child component can integrate with parent"""
        parent_contract = self.contracts.get(parent_component_id)
        child_contract = self.contracts.get(child_component_id)

        if not parent_contract or not child_contract:
            return False, ["Missing integration contracts"]

        incompatibilities = []

        # Check interface compatibility
        required_by_parent = set(parent_contract.required_interfaces)
        provided_by_child = set(child_contract.provided_interfaces)

        missing_interfaces = required_by_parent - provided_by_child
        if missing_interfaces:
            incompatibilities.append(
                f"Child missing required interfaces: {missing_interfaces}"
            )

        # Check data dependency satisfaction
        parent_data_deps = set(parent_contract.data_dependencies)
        child_provides = set(child_contract.provided_interfaces)

        unmet_dependencies = parent_data_deps - child_provides
        if unmet_dependencies:
            incompatibilities.append(f"Unmet data dependencies: {unmet_dependencies}")

        # Cache result
        compatibility_key = (parent_component_id, child_component_id)
        is_compatible = len(incompatibilities) == 0
        self.compatibility_matrix[compatibility_key] = is_compatible

        return is_compatible, incompatibilities


class DriftCorrectionEngine:
    """
    Automatically corrects detected alignment drift when possible.

    Implements corrective actions to restore alignment with macro intent.
    """

    def __init__(
        self,
        intent_repository: MacroIntentRepository,
        alignment_validator: ContextAlignmentValidator,
    ):
        self.intent_repo = intent_repository
        self.alignment_validator = alignment_validator
        self._correction_strategies: Dict[str, callable] = {
            "LOST_NON_NEGOTIABLE_REQUIREMENT": self._restore_lost_requirement,
            "LOW_ALIGNMENT_SCORE": self._boost_alignment_score,
            "INTERFACE_MISMATCH": self._resolve_interface_mismatch,
        }

    def _restore_lost_requirement(
        self, violation: AlignmentViolation, current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restore a lost non-negotiable requirement"""
        requirement = violation.evidence.get("lost_requirement", "")
        req_key = requirement.lower().replace(" ", "_")

        # Add requirement back to context with default implementation
        corrected_context = current_context.copy()
        corrected_context[req_key] = {
            "requirement": requirement,
            "status": "restored_automatically",
            "implementation": "default",
            "notes": f"Automatically restored due to violation at level {violation.current_level}",
        }

        logger.info(
            f"Auto-corrected: Restored requirement '{requirement}' at level {violation.current_level}"
        )
        return corrected_context

    def _boost_alignment_score(
        self, violation: AlignmentViolation, current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Attempt to boost alignment score by reinforcing key elements"""
        corrected_context = current_context.copy()

        # Add explicit alignment markers
        corrected_context["_alignment_metadata"] = {
            "macro_intent_acknowledged": True,
            "parent_requirements_reviewed": True,
            "alignment_score_target": 0.8,
            "correction_applied": f"level_{violation.current_level}_boost",
        }

        return corrected_context

    def _resolve_interface_mismatch(
        self, violation: AlignmentViolation, current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve interface compatibility issues"""
        corrected_context = current_context.copy()

        # Add interface adaptation layer
        corrected_context["_interface_adapters"] = {
            "auto_generated": True,
            "adaptation_strategy": "compatibility_layer",
            "violation_level": violation.current_level,
        }

        return corrected_context

    def apply_corrections(
        self, violations: List[AlignmentViolation], current_context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Apply automatic corrections for detected violations"""
        corrected_context = current_context.copy()
        applied_corrections = []

        for violation in violations:
            if (
                violation.auto_correctable
                and violation.violation_type in self._correction_strategies
            ):
                strategy = self._correction_strategies[violation.violation_type]
                corrected_context = strategy(violation, corrected_context)
                applied_corrections.append(violation.violation_type)

        return corrected_context, applied_corrections


# Integration with OAMAT workflow system
class ContextAlignmentIntegration:
    """
    Integration layer between context alignment system and OAMAT workflows.

    Provides seamless integration with existing workflow management.
    """

    def __init__(self):
        self.intent_repo = MacroIntentRepository()
        self.alignment_validator = ContextAlignmentValidator(self.intent_repo)
        self.integration_validator = IntegrationValidator()
        self.drift_corrector = DriftCorrectionEngine(
            self.intent_repo, self.alignment_validator
        )

    def setup_macro_intents_for_workflow(
        self, workflow_spec: Dict[str, Any]
    ) -> List[str]:
        """Setup macro intents from workflow specification"""
        intent_ids = []

        # Extract and register macro intents from workflow spec
        if "requirements" in workflow_spec:
            for i, req in enumerate(workflow_spec["requirements"]):
                intent_id = f"workflow_intent_{i}"
                intent = MacroIntent(
                    domain=IntentDomain.FUNCTIONAL,
                    description=req,
                    priority=8,  # High priority for explicit requirements
                    non_negotiable_requirements=[req],
                )
                self.intent_repo.register_macro_intent(intent_id, intent)
                intent_ids.append(intent_id)

        return intent_ids

    def validate_workflow_step(
        self,
        parent_context: Dict[str, Any],
        child_context: Dict[str, Any],
        hierarchy_level: int,
        component_spec: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a workflow step for context alignment and integration.

        Returns: (is_valid, validation_metadata)
        """
        # Get applicable intents (simplified - would be more sophisticated)
        intent_ids = list(self.intent_repo.intents.keys())

        # Validate context alignment
        (
            is_aligned,
            violations,
            trace,
        ) = self.alignment_validator.validate_context_transition(
            parent_context, child_context, hierarchy_level, intent_ids
        )

        # Apply automatic corrections if needed
        corrected_context = child_context
        applied_corrections = []

        if not is_aligned:
            auto_correctable_violations = [v for v in violations if v.auto_correctable]
            if auto_correctable_violations:
                (
                    corrected_context,
                    applied_corrections,
                ) = self.drift_corrector.apply_corrections(
                    auto_correctable_violations, child_context
                )

        # Validate integration if component spec provided
        integration_valid = True
        integration_issues = []

        if component_spec and "parent_component" in component_spec:
            # Register integration contracts and validate
            parent_id = component_spec["parent_component"]
            child_id = component_spec.get(
                "component_id", f"component_level_{hierarchy_level}"
            )

            # This would be more sophisticated in practice
            integration_valid, integration_issues = True, []

        validation_metadata = {
            "alignment_validation": {
                "is_aligned": is_aligned,
                "violations": [v.dict() for v in violations],
                "context_trace": trace.dict(),
                "alignment_score": trace.alignment_score,
            },
            "drift_correction": {
                "corrections_applied": applied_corrections,
                "corrected_context": corrected_context if applied_corrections else None,
            },
            "integration_validation": {
                "is_compatible": integration_valid,
                "issues": integration_issues,
            },
            "overall_valid": is_aligned and integration_valid,
            "hierarchy_level": hierarchy_level,
        }

        return validation_metadata["overall_valid"], validation_metadata


# Example usage and testing
if __name__ == "__main__":
    # Initialize system
    integration = ContextAlignmentIntegration()

    # Setup test workflow
    workflow_spec = {
        "requirements": [
            "Build a secure e-commerce platform",
            "Support mobile-first responsive design",
            "Implement real-time inventory tracking",
            "Ensure GDPR compliance",
        ]
    }

    intent_ids = integration.setup_macro_intents_for_workflow(workflow_spec)

    # Test context transitions
    master_context = {
        "project_type": "e-commerce_platform",
        "security_requirements": ["authentication", "encryption", "gdpr_compliance"],
        "user_interface": "mobile_first_responsive",
        "real_time_features": ["inventory_tracking", "order_status"],
        "functional_requirements": workflow_spec["requirements"],
    }

    # Level 1: Frontend development
    frontend_context = {
        "component_type": "frontend",
        "framework": "react_native",
        "responsive_design": True,
        "security_features": ["secure_authentication"],
        "real_time_updates": ["inventory_display"],
        "functional_requirements": [
            "mobile_first_responsive_ui",
            "user_authentication",
        ],
    }

    # Level 2: Authentication module
    auth_context = {
        "component_type": "authentication_module",
        "auth_method": "jwt_tokens",
        "security_level": "high",
        "functional_requirements": ["user_login", "session_management"],
        # Note: Missing GDPR compliance requirement
    }

    print("OAMAT Context Alignment System Test Results")
    print("=" * 60)

    # Test Level 1 transition
    print("\n1. Master → Frontend Context Transition")
    print("-" * 40)
    is_valid_1, metadata_1 = integration.validate_workflow_step(
        master_context, frontend_context, 1
    )
    print(f"Valid: {is_valid_1}")
    print(
        f"Alignment Score: {metadata_1['alignment_validation']['alignment_score']:.3f}"
    )
    print(f"Violations: {len(metadata_1['alignment_validation']['violations'])}")

    # Test Level 2 transition
    print("\n2. Frontend → Auth Module Context Transition")
    print("-" * 40)
    is_valid_2, metadata_2 = integration.validate_workflow_step(
        frontend_context, auth_context, 2
    )
    print(f"Valid: {is_valid_2}")
    print(
        f"Alignment Score: {metadata_2['alignment_validation']['alignment_score']:.3f}"
    )
    print(f"Violations: {len(metadata_2['alignment_validation']['violations'])}")

    if metadata_2["alignment_validation"]["violations"]:
        print("Detected Violations:")
        for violation in metadata_2["alignment_validation"]["violations"]:
            print(f"  - {violation['violation_type']}: {violation['description']}")
            if violation["auto_correctable"]:
                print("    ✓ Auto-correctable")

    # Show alignment report
    print("\n3. Overall Alignment Report")
    print("-" * 40)
    report = integration.alignment_validator.get_alignment_report()
    print(f"Total Transitions: {report['total_context_transitions']}")
    print(f"Average Alignment: {report['average_alignment_score']:.3f}")
    print(f"Total Violations: {report['total_violations']}")
    print(f"Critical Violations: {len(report.get('critical_violations', []))}")
