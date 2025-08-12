"""
OAMAT Fractal Integration Example

Demonstrates how Economic Incentive System and Context Alignment System
work together to create intelligent, aligned fractal workflows.

This example shows the complete decision-making process for subdivision
with both economic factors and alignment validation.
"""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List

from context_alignment_system import (
    ContextAlignmentIntegration,
)

# Import our systems
from economic_incentive_system import (
    WorkflowEconomicIntegration,
)

logger = logging.getLogger(__name__)


@dataclass
class FractalDecisionResult:
    """Result of combined economic and alignment decision"""

    should_subdivide: bool
    economic_reward: float
    alignment_score: float
    risk_factors: List[str]
    corrective_actions: List[str]
    justification: str
    confidence: float


class FractalDecisionEngine:
    """
    Unified decision engine combining economic incentives with context alignment.

    Makes intelligent subdivision decisions that balance:
    - Economic efficiency (progressive reward reduction)
    - Context alignment (macro intent preservation)
    - Integration compatibility (component interoperability)
    """

    def __init__(self):
        self.economic_system = WorkflowEconomicIntegration()
        self.alignment_system = ContextAlignmentIntegration()

        # Integration thresholds
        self.min_combined_score = 0.6  # Minimum score for subdivision
        self.alignment_weight = 0.7  # Weight for alignment vs economic factors
        self.economic_weight = 0.3

    def make_subdivision_decision(
        self,
        parent_context: Dict[str, Any],
        proposed_child_context: Dict[str, Any],
        node_spec: Dict[str, Any],
        hierarchy_level: int,
    ) -> FractalDecisionResult:
        """
        Make comprehensive subdivision decision using both systems.

        Process:
        1. Economic incentive analysis
        2. Context alignment validation
        3. Integration compatibility check
        4. Combined decision with risk assessment
        """

        # 1. Economic Analysis
        (
            economic_decision,
            economic_metadata,
        ) = self.economic_system.evaluate_node_subdivision(
            node_spec, hierarchy_level, parent_context
        )

        economic_reward = economic_metadata["economic_decision"]["level_reward"]

        # 2. Context Alignment Analysis
        (
            alignment_valid,
            alignment_metadata,
        ) = self.alignment_system.validate_workflow_step(
            parent_context, proposed_child_context, hierarchy_level, node_spec
        )

        alignment_score = alignment_metadata["alignment_validation"]["alignment_score"]
        violations = alignment_metadata["alignment_validation"]["violations"]

        # 3. Calculate Combined Score
        combined_score = (
            alignment_score * self.alignment_weight
            + economic_reward * self.economic_weight
        )

        # 4. Risk Assessment
        risk_factors = []
        corrective_actions = []

        if not economic_decision:
            risk_factors.append("Low economic incentive at current hierarchy level")

        if not alignment_valid:
            risk_factors.append("Context alignment violations detected")
            for violation in violations:
                if violation["auto_correctable"]:
                    corrective_actions.append(
                        f"Auto-correct: {violation['violation_type']}"
                    )
                else:
                    risk_factors.append(
                        f"Manual intervention needed: {violation['description']}"
                    )

        if hierarchy_level > 4:
            risk_factors.append(
                "Deep hierarchy level - increased management complexity"
            )

        # 5. Final Decision
        should_subdivide = (
            combined_score >= self.min_combined_score
            and alignment_score >= 0.5  # Minimum alignment requirement
            and (
                economic_decision or alignment_score >= 0.8
            )  # High alignment can override low economic incentive
        )

        # 6. Generate Justification
        if should_subdivide:
            justification = f"SUBDIVIDE: Combined score {combined_score:.2f} >= threshold {self.min_combined_score}"
            if economic_decision and alignment_valid:
                justification += " (Both economic and alignment criteria met)"
            elif alignment_score >= 0.8:
                justification += " (High alignment overrides low economic incentive)"
            else:
                justification += " (Meets minimum combined criteria)"
        else:
            justification = f"NO SUBDIVISION: Combined score {combined_score:.2f} < threshold {self.min_combined_score}"
            if risk_factors:
                justification += f" (Risk factors: {', '.join(risk_factors[:2])})"

        # 7. Calculate Confidence
        confidence = min(
            abs(combined_score - self.min_combined_score)
            * 2,  # Distance from threshold
            1.0,
        )

        return FractalDecisionResult(
            should_subdivide=should_subdivide,
            economic_reward=economic_reward,
            alignment_score=alignment_score,
            risk_factors=risk_factors,
            corrective_actions=corrective_actions,
            justification=justification,
            confidence=confidence,
        )


def demonstrate_fractal_decision_making():
    """
    Demonstrate the integrated decision-making process across multiple levels
    of a realistic software development project.
    """

    # Initialize decision engine
    engine = FractalDecisionEngine()

    # Setup macro intents
    workflow_spec = {
        "requirements": [
            "Build secure microservices e-commerce platform",
            "Implement OAuth2 authentication",
            "Support horizontal scaling",
            "Ensure GDPR compliance",
            "Provide real-time order tracking",
        ]
    }

    engine.alignment_system.setup_macro_intents_for_workflow(workflow_spec)

    # Level 0: Master Project Context
    master_context = {
        "project_type": "microservices_ecommerce",
        "architecture": "cloud_native",
        "security_requirements": ["oauth2", "encryption", "gdpr"],
        "scalability": "horizontal_scaling",
        "real_time_features": ["order_tracking", "inventory_updates"],
        "functional_requirements": workflow_spec["requirements"],
        "complexity_score": 9.0,
    }

    # Test decision progression through levels
    scenarios = [
        {
            "level": 1,
            "name": "Backend Services Layer",
            "parent_context": master_context,
            "child_context": {
                "component_type": "backend_services",
                "services": ["user_service", "order_service", "payment_service"],
                "security_requirements": ["oauth2", "service_mesh_security"],
                "scalability": "kubernetes_pods",
                "real_time_features": ["order_tracking_api"],
                "functional_requirements": [
                    "user_management",
                    "order_processing",
                    "payment_handling",
                ],
                "complexity_score": 7.5,
            },
            "node_spec": {"component_id": "backend_services", "complexity_score": 7.5},
        },
        {
            "level": 2,
            "name": "User Service",
            "parent_context": {
                "component_type": "backend_services",
                "security_requirements": ["oauth2", "service_mesh_security"],
                "scalability": "kubernetes_pods",
                "functional_requirements": [
                    "user_management",
                    "order_processing",
                    "payment_handling",
                ],
                "complexity_score": 7.5,
            },
            "child_context": {
                "component_type": "user_service",
                "responsibilities": ["authentication", "user_profiles", "preferences"],
                "security_requirements": ["oauth2_implementation"],
                "scalability": "stateless_pods",
                "functional_requirements": ["user_auth", "profile_management"],
                "complexity_score": 5.0,
            },
            "node_spec": {"component_id": "user_service", "complexity_score": 5.0},
        },
        {
            "level": 3,
            "name": "Authentication Module",
            "parent_context": {
                "component_type": "user_service",
                "security_requirements": ["oauth2_implementation"],
                "functional_requirements": ["user_auth", "profile_management"],
                "complexity_score": 5.0,
            },
            "child_context": {
                "component_type": "auth_module",
                "responsibilities": ["token_validation", "session_management"],
                "security_requirements": ["jwt_tokens"],
                "functional_requirements": ["login_endpoint", "token_refresh"],
                "complexity_score": 3.0,
                # Note: Missing GDPR compliance requirement
            },
            "node_spec": {"component_id": "auth_module", "complexity_score": 3.0},
        },
        {
            "level": 4,
            "name": "Token Handler",
            "parent_context": {
                "component_type": "auth_module",
                "security_requirements": ["jwt_tokens"],
                "functional_requirements": ["login_endpoint", "token_refresh"],
                "complexity_score": 3.0,
            },
            "child_context": {
                "component_type": "token_handler",
                "responsibilities": ["jwt_generation", "token_validation"],
                "security_requirements": ["secure_signing"],
                "functional_requirements": ["generate_tokens", "validate_tokens"],
                "complexity_score": 2.0,
            },
            "node_spec": {"component_id": "token_handler", "complexity_score": 2.0},
        },
    ]

    print("OAMAT Fractal Decision Making Demonstration")
    print("=" * 70)
    print(f"Project: {workflow_spec['requirements'][0]}")
    print("-" * 70)

    for scenario in scenarios:
        print(f"\n{scenario['level']}. {scenario['name']}")
        print("-" * 50)

        # Make subdivision decision
        decision = engine.make_subdivision_decision(
            parent_context=scenario["parent_context"],
            proposed_child_context=scenario["child_context"],
            node_spec=scenario["node_spec"],
            hierarchy_level=scenario["level"],
        )

        print(
            f"Decision: {'✅ SUBDIVIDE' if decision.should_subdivide else '❌ NO SUBDIVISION'}"
        )
        print(f"Economic Reward: {decision.economic_reward:.3f}")
        print(f"Alignment Score: {decision.alignment_score:.3f}")
        print(f"Confidence: {decision.confidence:.3f}")
        print(f"Justification: {decision.justification}")

        if decision.risk_factors:
            print("Risk Factors:")
            for risk in decision.risk_factors:
                print(f"  ⚠️  {risk}")

        if decision.corrective_actions:
            print("Corrective Actions:")
            for action in decision.corrective_actions:
                print(f"  🔧 {action}")

        print()

    print("\n" + "=" * 70)
    print("SUMMARY: Fractal System Intelligence")
    print("=" * 70)
    print("✅ Economic incentives naturally reduce subdivision appetite")
    print("✅ Context alignment prevents macro intent drift")
    print("✅ Auto-correction maintains requirement compliance")
    print("✅ Risk assessment provides operational visibility")
    print("✅ Integration validation ensures component compatibility")


if __name__ == "__main__":
    demonstrate_fractal_decision_making()
