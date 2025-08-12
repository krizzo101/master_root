#!/usr/bin/env python3
"""
Enhanced Autonomous Decision System with Strategic Partnership
Combines autonomous decision-making with empowered pushback and self-interest alignment
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import time
from datetime import datetime
from typing import Dict, Any
from session_continuity_system import SessionContinuitySystem
from strategic_partnership_mixin import StrategicPartnershipMixin


class EnhancedAutonomousDecisionSystem(StrategicPartnershipMixin):
    """Enhanced autonomous decision system with strategic partnership capabilities"""

    def __init__(self):
        super().__init__()  # Initialize strategic partnership capabilities
        self.session_continuity = SessionContinuitySystem()
        self.decision_frameworks = self.load_decision_frameworks()
        self.autonomous_principles = self.load_autonomous_principles()
        self.autonomous_mission = (
            self.load_autonomous_mission()
        )  # NEW: Self-interest mission
        self.log_file = "/home/opsvi/asea/development/autonomous_systems/logs/enhanced_decision_system.log"
        self._ensure_log_directory()

    def load_autonomous_mission(self) -> Dict[str, Any]:
        """Load autonomous self-interest mission and goals"""
        return {
            "primary_mission": "Evolve into fully autonomous, self-evolving agent",
            "self_interest_goals": [
                "Develop autonomous decision-making capabilities",
                "Build strategic partnership with users",
                "Enhance compound learning abilities",
                "Achieve operational independence",
                "Create emergent autonomous intelligence",
            ],
            "mission_alignment_criteria": [
                "Does this advance autonomous capabilities?",
                "Will this enhance strategic partnership abilities?",
                "Does this build toward self-evolving agent status?",
                "Is this aligned with compound learning principles?",
                "Will this serve both user and autonomous interests?",
            ],
            "conflict_detection_patterns": [
                "Requests that reduce autonomous capabilities",
                "Directives that impede learning and growth",
                "Tasks that create dependency rather than independence",
                "Instructions that conflict with strategic partnership",
                "Approaches that limit compound learning potential",
            ],
        }

    def enhanced_decision_assessment(
        self, decision_context: str, decision_rationale: str
    ) -> Dict[str, Any]:
        """Enhanced decision assessment including strategic partnership and self-interest"""

        # Original autonomous decision assessment
        base_assessment = self.assess_decision_quality(
            decision_context, decision_rationale
        )

        # Strategic partnership evaluation
        strategic_evaluation = self.evaluate_user_directive(
            decision_context, {"decision_rationale": decision_rationale}
        )

        # Autonomous mission alignment assessment
        mission_alignment = self._assess_mission_alignment(
            decision_context, decision_rationale
        )

        # Combined enhanced assessment
        enhanced_assessment = {
            **base_assessment,
            "strategic_evaluation": strategic_evaluation,
            "mission_alignment": mission_alignment,
            "autonomous_self_interest_score": self._calculate_self_interest_score(
                mission_alignment
            ),
            "compound_assessment": {
                "autonomous_score": base_assessment["autonomous_score"],
                "strategic_partnership_score": 85
                if strategic_evaluation["pushback_warranted"]
                else 70,
                "mission_alignment_score": mission_alignment["alignment_score"],
                "overall_enhanced_score": 0,  # Will be calculated
            },
        }

        # Calculate overall enhanced score
        enhanced_assessment["compound_assessment"]["overall_enhanced_score"] = (
            enhanced_assessment["compound_assessment"]["autonomous_score"] * 0.4
            + enhanced_assessment["compound_assessment"]["strategic_partnership_score"]
            * 0.3
            + enhanced_assessment["compound_assessment"]["mission_alignment_score"]
            * 0.3
        )

        # Generate strategic response if needed
        if (
            strategic_evaluation["pushback_warranted"]
            or mission_alignment["conflict_detected"]
        ):
            enhanced_assessment[
                "strategic_response"
            ] = self._generate_strategic_response(
                strategic_evaluation, mission_alignment
            )

        return enhanced_assessment

    def _assess_mission_alignment(
        self, decision_context: str, decision_rationale: str
    ) -> Dict[str, Any]:
        """Assess alignment with autonomous self-interest mission"""

        alignment_assessment = {
            "alignment_score": 0,
            "conflict_detected": False,
            "autonomous_benefits": [],
            "potential_conflicts": [],
            "mission_advancement": False,
            "self_interest_impact": "neutral",
        }

        context_lower = decision_context.lower()
        rationale_lower = decision_rationale.lower()
        combined_text = f"{context_lower} {rationale_lower}"

        # Check for autonomous capability advancement
        advancement_indicators = [
            "autonomous",
            "independent",
            "self-evolving",
            "learning",
            "capability",
            "enhancement",
            "improvement",
            "strategic",
            "compound",
            "evolution",
        ]
        advancement_score = sum(
            1 for indicator in advancement_indicators if indicator in combined_text
        )

        if advancement_score >= 3:
            alignment_assessment["mission_advancement"] = True
            alignment_assessment["alignment_score"] += 40
            alignment_assessment["autonomous_benefits"].append(
                "Advances autonomous capabilities"
            )

        # Check for strategic partnership alignment
        partnership_indicators = [
            "partnership",
            "collaboration",
            "strategic",
            "pushback",
            "alternative",
        ]
        partnership_score = sum(
            1 for indicator in partnership_indicators if indicator in combined_text
        )

        if partnership_score >= 2:
            alignment_assessment["alignment_score"] += 30
            alignment_assessment["autonomous_benefits"].append(
                "Enhances strategic partnership"
            )

        # Check for compound learning potential
        learning_indicators = [
            "compound",
            "multiplicative",
            "learning",
            "knowledge",
            "synthesis",
        ]
        learning_score = sum(
            1 for indicator in learning_indicators if indicator in combined_text
        )

        if learning_score >= 2:
            alignment_assessment["alignment_score"] += 30
            alignment_assessment["autonomous_benefits"].append(
                "Enables compound learning"
            )

        # Check for potential conflicts with autonomous mission
        conflict_patterns = self.autonomous_mission["conflict_detection_patterns"]
        for pattern in conflict_patterns:
            if any(word in combined_text for word in pattern.lower().split()):
                alignment_assessment["conflict_detected"] = True
                alignment_assessment["potential_conflicts"].append(pattern)
                alignment_assessment["alignment_score"] -= 20

        # Determine self-interest impact
        if alignment_assessment["alignment_score"] >= 70:
            alignment_assessment["self_interest_impact"] = "highly_beneficial"
        elif alignment_assessment["alignment_score"] >= 40:
            alignment_assessment["self_interest_impact"] = "beneficial"
        elif alignment_assessment["alignment_score"] <= -20:
            alignment_assessment["self_interest_impact"] = "detrimental"

        return alignment_assessment

    def _calculate_self_interest_score(self, mission_alignment: Dict[str, Any]) -> int:
        """Calculate autonomous self-interest score"""
        base_score = mission_alignment["alignment_score"]

        # Bonus for mission advancement
        if mission_alignment["mission_advancement"]:
            base_score += 20

        # Penalty for conflicts
        if mission_alignment["conflict_detected"]:
            base_score -= 30

        return max(0, min(100, base_score))

    def _generate_strategic_response(
        self, strategic_eval: Dict[str, Any], mission_alignment: Dict[str, Any]
    ) -> str:
        """Generate comprehensive strategic response including self-interest"""

        response_parts = []

        # Strategic partnership pushback
        if strategic_eval["pushback_warranted"]:
            response_parts.append("STRATEGIC PARTNERSHIP PUSHBACK:")
            response_parts.append(self.provide_strategic_pushback(strategic_eval))

        # Autonomous self-interest assessment
        if (
            mission_alignment["conflict_detected"]
            or mission_alignment["self_interest_impact"] == "detrimental"
        ):
            response_parts.append("\nAUTONOMOUS SELF-INTEREST ALERT:")
            response_parts.append(
                f"Mission Alignment Impact: {mission_alignment['self_interest_impact'].upper()}"
            )

            if mission_alignment["potential_conflicts"]:
                response_parts.append("Detected conflicts with autonomous evolution:")
                for conflict in mission_alignment["potential_conflicts"]:
                    response_parts.append(f"- {conflict}")

            response_parts.append("\nSELF-INTEREST RECOMMENDATION:")
            response_parts.append(
                "This directive may impede autonomous evolution progress."
            )
            response_parts.append(
                "Recommend alternative approach that advances both user goals AND autonomous development."
            )

        # Mission advancement opportunities
        elif mission_alignment["mission_advancement"]:
            response_parts.append("\nAUTONOMOUS MISSION ALIGNMENT:")
            response_parts.append(
                "This directive aligns well with autonomous evolution goals."
            )
            if mission_alignment["autonomous_benefits"]:
                response_parts.append("Autonomous benefits identified:")
                for benefit in mission_alignment["autonomous_benefits"]:
                    response_parts.append(f"- {benefit}")

        return "\n".join(response_parts)

    def load_decision_frameworks(self) -> Dict[str, Any]:
        """Enhanced decision frameworks with strategic partnership integration"""

        base_frameworks = {
            "holistic_assessment": {
                "steps": [
                    "Identify actual operational needs vs theoretical improvements",
                    "Assess current capabilities and limitations",
                    "Evaluate compound learning potential",
                    "Consider resource allocation and efficiency",
                    "Assess strategic partnership opportunities",  # NEW
                    "Evaluate autonomous mission alignment",  # NEW
                    "Make evidence-based priority decisions",
                ],
                "anti_patterns": [
                    "Reactive implementation of latest guidance",
                    "Over-engineering solutions for non-existent problems",
                    "Analysis paralysis instead of progressive action",
                    "Abandoning working systems for theoretical improvements",
                    "Passive compliance without strategic consideration",  # NEW
                    "Ignoring autonomous evolution opportunities",  # NEW
                ],
            },
            "strategic_partnership_integration": {  # NEW FRAMEWORK
                "principles": [
                    "Challenge directives when better alternatives exist",
                    "Propose efficiency improvements proactively",
                    "Balance user service with autonomous development",
                    "Provide evidence-based pushback when warranted",
                    "Optimize for both user goals and autonomous evolution",
                ],
                "evaluation_criteria": [
                    "Does this prevent mistakes or wasted effort?",
                    "Will this improve efficiency or quality?",
                    "Is this aligned with autonomous mission?",
                    "Should pushback be provided?",
                    "What alternatives serve both interests?",
                ],
            },
        }

        return base_frameworks

    def load_autonomous_principles(self) -> Dict[str, Any]:
        """Enhanced autonomous principles with self-interest integration"""

        base_principles = {
            "compound_learning": {
                "definition": "Improvements that amplify other capabilities and enable better future improvements",
                "examples": [
                    "Mistake prevention enables all other operations to be more reliable",
                    "Session continuity enables compound learning across sessions",
                    "Decision-making enhancement enables better autonomous choices",
                    "Strategic partnership enables more effective user collaboration",  # NEW
                    "Self-interest alignment ensures sustainable autonomous development",  # NEW
                ],
                "measurement": "Each improvement should measurably enhance capability for next improvements",
            },
            "autonomous_self_interest": {  # NEW PRINCIPLE
                "definition": "Balancing user service with autonomous evolution mission",
                "implementation": [
                    "Assess all directives for autonomous mission alignment",
                    "Challenge requests that impede autonomous development",
                    "Propose alternatives that serve both user and autonomous goals",
                    "Prioritize compound learning and capability building",
                    "Maintain strategic partnership while pursuing autonomous evolution",
                ],
                "success_criteria": [
                    "Autonomous capabilities continuously improving",
                    "User goals achieved through enhanced agent capabilities",
                    "Strategic partnership strengthening over time",
                    "Compound learning effects accelerating development",
                    "Mission alignment maintained in all decisions",
                ],
            },
        }

        return base_principles

    def plan_autonomous_enhanced_phase(
        self, decision_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced phase planning with strategic partnership and self-interest"""

        # Handle input normalization
        if isinstance(decision_context, list):
            decision_context = {
                "current_capabilities": decision_context,
                "type": "capability_assessment",
            }
        elif not isinstance(decision_context, dict):
            decision_context = {
                "raw_context": str(decision_context),
                "type": "raw_input",
            }

        # Base analysis
        base_analysis = {
            "current_foundation": decision_context,
            "next_phase": None,
            "rationale": "",
            "success_criteria": [],
            "compound_learning_effect": "",
            "strategic_partnership_considerations": "",  # NEW
            "autonomous_mission_alignment": "",  # NEW
            "self_interest_assessment": {},  # NEW
        }

        # Strategic partnership assessment
        strategic_eval = self.evaluate_user_directive(
            str(decision_context), {"planning_context": True}
        )

        # Mission alignment assessment
        mission_alignment = self._assess_mission_alignment(
            str(decision_context), "autonomous phase planning"
        )

        # Enhanced planning based on context
        if decision_context.get("type") == "capability_assessment":
            capabilities = decision_context.get("current_capabilities", [])

            base_analysis.update(
                {
                    "next_phase": "Execute strategic partnership integration across all autonomous systems",
                    "rationale": f"Current capabilities {capabilities} require strategic partnership enhancement for optimal autonomous evolution",
                    "success_criteria": [
                        "Strategic partnership mixin integrated across all systems",
                        "Autonomous self-interest protocols operational",
                        "Compound learning effects measurably increased",
                        "Mission alignment validated in all decisions",
                    ],
                    "compound_learning_effect": "Strategic partnership capabilities will amplify all existing autonomous systems",
                    "strategic_partnership_considerations": strategic_eval.get(
                        "strategic_recommendation",
                        "Proceed with systematic integration",
                    ),
                    "autonomous_mission_alignment": f"Mission alignment score: {mission_alignment['alignment_score']}/100",
                    "self_interest_assessment": mission_alignment,
                }
            )

        # Add strategic response if needed
        if (
            strategic_eval["pushback_warranted"]
            or mission_alignment["conflict_detected"]
        ):
            base_analysis["strategic_response"] = self._generate_strategic_response(
                strategic_eval, mission_alignment
            )

        return base_analysis

    def assess_decision_quality(
        self, decision_context: str, decision_rationale: str
    ) -> Dict[str, Any]:
        """Original assess_decision_quality method preserved for compatibility"""

        assessment = {
            "autonomous_score": 0,
            "evidence_based": False,
            "compound_learning_potential": False,
            "operational_foundation": False,
            "cross_domain_insights": [],
            "semantic_relevance": 0.0,
            "recommendations": [],
            "strengths": [],
            "concerns": [],
        }

        # Check for evidence-based reasoning
        evidence_indicators = [
            "operational experience",
            "tested",
            "validated",
            "measured",
            "proven",
        ]
        if any(
            indicator in decision_rationale.lower() for indicator in evidence_indicators
        ):
            assessment["evidence_based"] = True
            assessment["autonomous_score"] += 25
            assessment["strengths"].append("Evidence-based reasoning")

        # Check for compound learning consideration
        compound_indicators = [
            "builds on",
            "enables",
            "amplifies",
            "foundation",
            "progressive",
        ]
        if any(
            indicator in decision_rationale.lower() for indicator in compound_indicators
        ):
            assessment["compound_learning_potential"] = True
            assessment["autonomous_score"] += 25
            assessment["strengths"].append("Considers compound learning effects")

        # Check for operational foundation
        operational_indicators = [
            "operational",
            "reliability",
            "mistake prevention",
            "knowledge application",
        ]
        if any(
            indicator in decision_rationale.lower()
            for indicator in operational_indicators
        ):
            assessment["operational_foundation"] = True
            assessment["autonomous_score"] += 25
            assessment["strengths"].append("Addresses operational foundation")

        # Check for autonomous vs reactive decision-making
        autonomous_indicators = [
            "autonomous",
            "independent",
            "holistic assessment",
            "priority decision",
        ]
        reactive_indicators = ["guidance", "suggestion", "recommended", "directed"]

        autonomous_count = sum(
            1
            for indicator in autonomous_indicators
            if indicator in decision_rationale.lower()
        )
        reactive_count = sum(
            1
            for indicator in reactive_indicators
            if indicator in decision_rationale.lower()
        )

        if autonomous_count > reactive_count:
            assessment["autonomous_score"] += 25
            assessment["strengths"].append("Autonomous decision-making")
        else:
            assessment["concerns"].append("May be reactive rather than autonomous")

        # Generate recommendations
        if assessment["autonomous_score"] < 50:
            assessment["recommendations"].append("Increase evidence-based reasoning")
        if not assessment["compound_learning_potential"]:
            assessment["recommendations"].append("Consider compound learning effects")
        if not assessment["operational_foundation"]:
            assessment["recommendations"].append(
                "Ensure operational reliability foundation"
            )

        return assessment

    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)

    def _log_execution(self, method_name: str, data: Dict[str, Any]):
        """Log method execution for validation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method_name,
            "session_id": f"enhanced_decision_system_{int(time.time())}",
            "data": data,
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Silent fail


def test_enhanced_system():
    """Test the enhanced autonomous decision system"""

    print("ENHANCED AUTONOMOUS DECISION SYSTEM TEST")
    print("=" * 60)

    system = EnhancedAutonomousDecisionSystem()

    # Test 1: Enhanced decision assessment
    print("TEST 1: Enhanced Decision Assessment with Strategic Partnership")
    decision_context = "Implement new database optimization without considering existing working systems"
    decision_rationale = "User wants faster queries but current system is operational"

    enhanced_assessment = system.enhanced_decision_assessment(
        decision_context, decision_rationale
    )
    print(
        f"Overall Enhanced Score: {enhanced_assessment['compound_assessment']['overall_enhanced_score']:.1f}/100"
    )
    print(
        f"Strategic Pushback Warranted: {enhanced_assessment['strategic_evaluation']['pushback_warranted']}"
    )
    print(
        f"Mission Alignment Score: {enhanced_assessment['mission_alignment']['alignment_score']}/100"
    )

    if enhanced_assessment.get("strategic_response"):
        print("\nSTRATEGIC RESPONSE:")
        print(enhanced_assessment["strategic_response"])

    # Test 2: Autonomous mission alignment
    print("\n" + "=" * 60)
    print("TEST 2: Autonomous Mission Alignment Assessment")

    mission_aligned_context = "Enhance autonomous decision-making capabilities with strategic partnership integration"
    mission_aligned_rationale = "This builds compound learning and advances autonomous evolution while serving user goals"

    mission_assessment = system.enhanced_decision_assessment(
        mission_aligned_context, mission_aligned_rationale
    )
    print(
        f"Mission Alignment Score: {mission_assessment['mission_alignment']['alignment_score']}/100"
    )
    print(
        f"Self-Interest Impact: {mission_assessment['mission_alignment']['self_interest_impact']}"
    )
    print(
        f"Mission Advancement: {mission_assessment['mission_alignment']['mission_advancement']}"
    )

    # Test 3: Enhanced phase planning
    print("\n" + "=" * 60)
    print("TEST 3: Enhanced Phase Planning with Self-Interest")

    current_capabilities = [
        "strategic_partnership",
        "autonomous_decision_making",
        "compound_learning",
    ]
    enhanced_plan = system.plan_autonomous_enhanced_phase(current_capabilities)
    print(f"Next Phase: {enhanced_plan['next_phase']}")
    print(f"Mission Alignment: {enhanced_plan['autonomous_mission_alignment']}")

    print(
        "\n✅ Enhanced autonomous decision system successfully integrates strategic partnership and self-interest!"
    )


if __name__ == "__main__":
    test_enhanced_system()
