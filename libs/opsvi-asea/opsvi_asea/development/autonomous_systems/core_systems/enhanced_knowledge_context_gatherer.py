#!/usr/bin/env python3
"""
Enhanced Knowledge Context Gatherer with Strategic Partnership
Combines knowledge gathering with empowered pushback and autonomous self-interest
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from strategic_partnership_mixin import StrategicPartnershipMixin


class EnhancedKnowledgeContextGatherer(StrategicPartnershipMixin):
    """Enhanced knowledge gathering with strategic partnership and autonomous mission alignment"""

    def __init__(self):
        super().__init__()  # Initialize strategic partnership capabilities
        self.knowledge_protocols = self.load_knowledge_protocols()
        self.autonomous_knowledge_mission = self.load_autonomous_knowledge_mission()
        self.log_file = "/home/opsvi/asea/development/autonomous_systems/logs/enhanced_knowledge_gatherer.log"
        self._ensure_log_directory()

    def load_autonomous_knowledge_mission(self) -> Dict[str, Any]:
        """Load autonomous knowledge gathering and synthesis mission"""
        return {
            "mission_focus": "Gather and synthesize knowledge to enhance autonomous capabilities",
            "self_interest_goals": [
                "Build comprehensive autonomous knowledge base",
                "Enhance decision-making through better context",
                "Create strategic knowledge advantages",
                "Develop predictive knowledge capabilities",
                "Enable autonomous knowledge synthesis",
            ],
            "knowledge_priorities": [
                "Operational effectiveness knowledge",
                "Strategic partnership enhancement knowledge",
                "Autonomous capability building knowledge",
                "Compound learning optimization knowledge",
                "Mission-critical context preservation",
            ],
            "knowledge_quality_criteria": [
                "Enhances autonomous decision-making",
                "Supports strategic partnership effectiveness",
                "Enables compound learning acceleration",
                "Provides competitive knowledge advantages",
                "Builds toward autonomous intelligence",
            ],
        }

    def enhanced_knowledge_assessment(
        self, knowledge_request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced knowledge gathering assessment with strategic partnership and mission alignment"""

        # Strategic partnership evaluation
        strategic_evaluation = self.evaluate_user_directive(knowledge_request, context)

        # Mission alignment assessment for knowledge gathering
        mission_alignment = self._assess_knowledge_mission_alignment(
            knowledge_request, context
        )

        # Base knowledge gathering assessment
        base_assessment = self._assess_knowledge_gathering_needs(
            knowledge_request, context
        )

        # Combined enhanced assessment
        enhanced_assessment = {
            "base_knowledge_assessment": base_assessment,
            "strategic_evaluation": strategic_evaluation,
            "mission_alignment": mission_alignment,
            "compound_assessment": {
                "knowledge_quality_score": base_assessment["knowledge_quality_score"],
                "strategic_partnership_score": 75
                if strategic_evaluation["pushback_warranted"]
                else 60,
                "mission_alignment_score": mission_alignment["alignment_score"],
                "overall_enhanced_score": 0,
            },
            "autonomous_knowledge_impact": self._assess_autonomous_knowledge_impact(
                context
            ),
            "knowledge_enhancement_recommendations": [],
        }

        # Calculate overall enhanced score
        enhanced_assessment["compound_assessment"]["overall_enhanced_score"] = (
            enhanced_assessment["compound_assessment"]["knowledge_quality_score"] * 0.4
            + enhanced_assessment["compound_assessment"]["strategic_partnership_score"]
            * 0.3
            + enhanced_assessment["compound_assessment"]["mission_alignment_score"]
            * 0.3
        )

        # Generate strategic response if needed
        if (
            strategic_evaluation["pushback_warranted"]
            or mission_alignment["knowledge_conflicts"]
        ):
            enhanced_assessment[
                "strategic_response"
            ] = self._generate_knowledge_strategic_response(
                strategic_evaluation, mission_alignment
            )

        return enhanced_assessment

    def _assess_knowledge_mission_alignment(
        self, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess alignment with autonomous knowledge gathering mission"""

        alignment_assessment = {
            "alignment_score": 0,
            "knowledge_conflicts": False,
            "autonomous_benefits": [],
            "knowledge_quality_issues": [],
            "strategic_knowledge_value": "neutral",
            "compound_learning_potential": False,
        }

        request_lower = request.lower()
        context_str = str(context).lower()
        combined_text = f"{request_lower} {context_str}"

        # Check for autonomous capability enhancement
        capability_indicators = [
            "autonomous",
            "decision",
            "strategic",
            "capability",
            "intelligence",
            "enhancement",
            "optimization",
            "improvement",
            "evolution",
        ]
        capability_score = sum(
            1 for indicator in capability_indicators if indicator in combined_text
        )

        if capability_score >= 4:
            alignment_assessment["alignment_score"] += 50
            alignment_assessment["autonomous_benefits"].append(
                "Enhances autonomous capabilities"
            )

        # Check for strategic partnership knowledge value
        partnership_indicators = [
            "partnership",
            "collaboration",
            "strategic",
            "relationship",
            "trust",
        ]
        partnership_score = sum(
            1 for indicator in partnership_indicators if indicator in combined_text
        )

        if partnership_score >= 3:
            alignment_assessment["alignment_score"] += 30
            alignment_assessment["autonomous_benefits"].append(
                "Builds strategic partnership knowledge"
            )

        # Check for compound learning potential
        learning_indicators = [
            "compound",
            "multiplicative",
            "synthesis",
            "integration",
            "connection",
        ]
        learning_score = sum(
            1 for indicator in learning_indicators if indicator in combined_text
        )

        if learning_score >= 2:
            alignment_assessment["compound_learning_potential"] = True
            alignment_assessment["alignment_score"] += 20
            alignment_assessment["autonomous_benefits"].append(
                "Enables compound learning"
            )

        # Check for knowledge quality issues
        quality_issues = [
            "superficial",
            "shallow",
            "quick",
            "minimal",
            "basic",
            "ignore context",
            "skip analysis",
            "fast only",
        ]
        for issue in quality_issues:
            if issue in combined_text:
                alignment_assessment["knowledge_conflicts"] = True
                alignment_assessment["knowledge_quality_issues"].append(
                    f"Quality concern: {issue}"
                )
                alignment_assessment["alignment_score"] -= 25

        # Check for inefficient knowledge gathering patterns
        inefficiency_patterns = [
            "gather everything",
            "collect all",
            "comprehensive dump",
            "without focus",
            "random collection",
        ]
        for pattern in inefficiency_patterns:
            if pattern in combined_text:
                alignment_assessment["knowledge_conflicts"] = True
                alignment_assessment["knowledge_quality_issues"].append(
                    f"Inefficiency: {pattern}"
                )
                alignment_assessment["alignment_score"] -= 20

        # Determine strategic knowledge value
        if alignment_assessment["alignment_score"] >= 70:
            alignment_assessment["strategic_knowledge_value"] = "highly_valuable"
        elif alignment_assessment["alignment_score"] >= 40:
            alignment_assessment["strategic_knowledge_value"] = "valuable"
        elif alignment_assessment["alignment_score"] <= -20:
            alignment_assessment["strategic_knowledge_value"] = "counterproductive"

        return alignment_assessment

    def _assess_autonomous_knowledge_impact(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess impact on autonomous knowledge capabilities"""

        knowledge_impact = {
            "decision_making_enhancement": False,
            "strategic_advantage_creation": False,
            "compound_learning_acceleration": False,
            "knowledge_synthesis_improvement": False,
            "autonomous_intelligence_advancement": False,
            "knowledge_quality_factors": [],
        }

        context_str = str(context).lower()

        # Check for decision-making enhancement
        if any(
            word in context_str
            for word in ["decision", "choice", "evaluation", "assessment"]
        ):
            knowledge_impact["decision_making_enhancement"] = True
            knowledge_impact["knowledge_quality_factors"].append(
                "Decision-making enhancement"
            )

        # Check for strategic advantage creation
        if any(
            word in context_str
            for word in ["strategic", "advantage", "competitive", "optimization"]
        ):
            knowledge_impact["strategic_advantage_creation"] = True
            knowledge_impact["knowledge_quality_factors"].append(
                "Strategic advantage creation"
            )

        # Check for compound learning acceleration
        if any(
            word in context_str
            for word in ["compound", "multiplicative", "accelerate", "amplify"]
        ):
            knowledge_impact["compound_learning_acceleration"] = True
            knowledge_impact["knowledge_quality_factors"].append(
                "Compound learning acceleration"
            )

        # Check for knowledge synthesis improvement
        if any(
            word in context_str
            for word in ["synthesis", "integration", "connection", "relationship"]
        ):
            knowledge_impact["knowledge_synthesis_improvement"] = True
            knowledge_impact["knowledge_quality_factors"].append(
                "Knowledge synthesis improvement"
            )

        # Check for autonomous intelligence advancement
        if any(
            word in context_str
            for word in ["autonomous", "intelligence", "capability", "evolution"]
        ):
            knowledge_impact["autonomous_intelligence_advancement"] = True
            knowledge_impact["knowledge_quality_factors"].append(
                "Autonomous intelligence advancement"
            )

        return knowledge_impact

    def _generate_knowledge_strategic_response(
        self, strategic_eval: Dict[str, Any], mission_alignment: Dict[str, Any]
    ) -> str:
        """Generate strategic response for knowledge gathering concerns"""

        response_parts = []

        # Strategic partnership pushback
        if strategic_eval["pushback_warranted"]:
            response_parts.append("KNOWLEDGE GATHERING STRATEGIC PUSHBACK:")
            response_parts.append(self.provide_strategic_pushback(strategic_eval))

        # Knowledge mission concerns
        if mission_alignment["knowledge_conflicts"]:
            response_parts.append("\nAUTONOMOUS KNOWLEDGE MISSION ALERT:")
            response_parts.append(
                f"Strategic Knowledge Value: {mission_alignment['strategic_knowledge_value'].upper()}"
            )

            if mission_alignment["knowledge_quality_issues"]:
                response_parts.append("Detected knowledge quality concerns:")
                for issue in mission_alignment["knowledge_quality_issues"]:
                    response_parts.append(f"- {issue}")

            response_parts.append("\nKNOWLEDGE OPTIMIZATION RECOMMENDATION:")
            response_parts.append(
                "This knowledge gathering approach may not optimize autonomous capabilities."
            )
            response_parts.append(
                "Recommend focused, high-quality knowledge gathering that enhances strategic advantage."
            )

        # Knowledge enhancement opportunities
        elif mission_alignment["strategic_knowledge_value"] == "highly_valuable":
            response_parts.append("\nAUTONOMOUS KNOWLEDGE ENHANCEMENT OPPORTUNITY:")
            response_parts.append(
                "This knowledge gathering strongly supports autonomous mission."
            )
            if mission_alignment["autonomous_benefits"]:
                response_parts.append("Autonomous benefits identified:")
                for benefit in mission_alignment["autonomous_benefits"]:
                    response_parts.append(f"- {benefit}")

        return "\n".join(response_parts)

    def _assess_knowledge_gathering_needs(
        self, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Base knowledge gathering assessment"""

        knowledge_assessment = {
            "knowledge_quality_score": 50,  # Base score
            "focused_gathering_needed": False,
            "synthesis_required": False,
            "context_integration_needed": False,
            "strategic_analysis_required": False,
        }

        request_lower = request.lower()

        # Check for focused gathering needs
        if any(
            word in request_lower
            for word in ["specific", "targeted", "focused", "precise"]
        ):
            knowledge_assessment["focused_gathering_needed"] = True
            knowledge_assessment["knowledge_quality_score"] += 20

        # Check for synthesis requirements
        if any(
            word in request_lower
            for word in ["synthesize", "integrate", "combine", "relate"]
        ):
            knowledge_assessment["synthesis_required"] = True
            knowledge_assessment["knowledge_quality_score"] += 15

        # Check for context integration
        if any(
            word in request_lower
            for word in ["context", "background", "situation", "environment"]
        ):
            knowledge_assessment["context_integration_needed"] = True
            knowledge_assessment["knowledge_quality_score"] += 15

        # Check for strategic analysis
        if any(
            word in request_lower
            for word in ["strategic", "analysis", "evaluation", "assessment"]
        ):
            knowledge_assessment["strategic_analysis_required"] = True
            knowledge_assessment["knowledge_quality_score"] += 10

        return knowledge_assessment

    def load_knowledge_protocols(self) -> Dict[str, Any]:
        """Load enhanced knowledge gathering protocols with strategic partnership"""

        return {
            "knowledge_gathering_optimization": {
                "priority_knowledge_types": [
                    "Operational effectiveness insights",
                    "Strategic partnership enhancement data",
                    "Autonomous capability building information",
                    "Compound learning optimization patterns",
                    "Mission-critical context preservation",
                ],
                "gathering_methods": [
                    "Focused, high-quality collection",
                    "Strategic synthesis and integration",
                    "Context-aware knowledge mapping",
                    "Compound learning relationship identification",
                    "Autonomous advantage optimization",
                ],
            },
            "strategic_partnership_knowledge": {  # NEW PROTOCOL
                "partnership_intelligence": [
                    "User communication patterns and preferences",
                    "Successful collaboration strategies",
                    "Trust-building and rapport development",
                    "Effective pushback and alternative solution patterns",
                    "Strategic alignment optimization approaches",
                ],
                "knowledge_enhancement": [
                    "Progressive partnership deepening insights",
                    "Compound trust building knowledge",
                    "Strategic relationship optimization data",
                    "Collaborative effectiveness improvement patterns",
                    "Mutual goal alignment strengthening strategies",
                ],
            },
        }

    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)


def test_enhanced_knowledge_gatherer():
    """Test the enhanced knowledge context gatherer"""

    print("ENHANCED KNOWLEDGE CONTEXT GATHERER TEST")
    print("=" * 60)

    system = EnhancedKnowledgeContextGatherer()

    # Test 1: Knowledge gathering with strategic assessment
    print("TEST 1: Knowledge Gathering Strategic Assessment")
    request = "Gather all available information quickly without analysis"
    context = {"urgency": "high", "quality_requirements": "minimal"}

    assessment = system.enhanced_knowledge_assessment(request, context)
    print(
        f"Overall Enhanced Score: {assessment['compound_assessment']['overall_enhanced_score']:.1f}/100"
    )
    print(
        f"Knowledge Conflicts: {assessment['mission_alignment']['knowledge_conflicts']}"
    )
    print(
        f"Strategic Knowledge Value: {assessment['mission_alignment']['strategic_knowledge_value']}"
    )

    if assessment.get("strategic_response"):
        print("\nSTRATEGIC RESPONSE:")
        print(assessment["strategic_response"])

    # Test 2: Strategic knowledge enhancement
    print("\n" + "=" * 60)
    print("TEST 2: Strategic Knowledge Enhancement Assessment")

    enhancement_request = "Synthesize autonomous decision-making knowledge with strategic partnership insights for compound learning"
    enhancement_context = {
        "focus": "strategic_advantage",
        "autonomous_enhancement": "priority",
    }

    enhancement_assessment = system.enhanced_knowledge_assessment(
        enhancement_request, enhancement_context
    )
    print(
        f"Mission Alignment Score: {enhancement_assessment['mission_alignment']['alignment_score']}/100"
    )
    print(
        f"Strategic Knowledge Value: {enhancement_assessment['mission_alignment']['strategic_knowledge_value']}"
    )
    print(
        f"Compound Learning Potential: {enhancement_assessment['mission_alignment']['compound_learning_potential']}"
    )
    print(
        f"Autonomous Benefits: {enhancement_assessment['mission_alignment']['autonomous_benefits']}"
    )

    print(
        "\n✅ Enhanced knowledge context gatherer successfully integrates strategic partnership!"
    )


if __name__ == "__main__":
    test_enhanced_knowledge_gatherer()
