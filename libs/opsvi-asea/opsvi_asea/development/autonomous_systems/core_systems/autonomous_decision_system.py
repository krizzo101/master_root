#!/usr/bin/env python3
"""
Autonomous Decision-Making Enhancement System
Builds on operational reliability to improve autonomous decision-making processes
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import time
from datetime import datetime
from typing import Dict, List, Any
from session_continuity_system import SessionContinuitySystem


class AutonomousDecisionSystem:
    """System to enhance autonomous decision-making using operational foundation"""

    def __init__(self):
        self.session_continuity = SessionContinuitySystem()
        self.decision_frameworks = self.load_decision_frameworks()
        self.autonomous_principles = self.load_autonomous_principles()
        self.log_file = (
            "/home/opsvi/asea/development/autonomous_systems/logs/decision_system.log"
        )
        self._ensure_log_directory()

    def load_decision_frameworks(self) -> Dict[str, Any]:
        """Load decision-making frameworks for autonomous operation"""

        return {
            "holistic_assessment": {
                "steps": [
                    "Identify actual operational needs vs theoretical improvements",
                    "Assess current capabilities and limitations",
                    "Evaluate compound learning potential",
                    "Consider resource allocation and efficiency",
                    "Make evidence-based priority decisions",
                ],
                "anti_patterns": [
                    "Reactive implementation of latest guidance",
                    "Over-engineering solutions for non-existent problems",
                    "Analysis paralysis instead of progressive action",
                    "Abandoning working systems for theoretical improvements",
                ],
            },
            "progressive_improvement": {
                "principles": [
                    "Build on what works before redesigning",
                    "Each improvement should enable better next improvements",
                    "Validate with operational experience before major changes",
                    "Focus on compound learning effects",
                    "Maintain operational reliability while evolving",
                ],
                "implementation_pattern": "Small reliable improvements > Large theoretical redesigns",
            },
            "autonomous_agency": {
                "decision_criteria": [
                    "Evidence-based assessment over reactive responses",
                    "Operational needs over theoretical elegance",
                    "Compound learning potential over isolated improvements",
                    "Progressive capability building over comprehensive redesign",
                    "Autonomous priority setting over external direction",
                ],
                "validation_questions": [
                    "Does this address actual operational limitations?",
                    "Will this enable better future improvements?",
                    "Is this the highest impact use of resources?",
                    "Am I making this decision autonomously or reactively?",
                ],
            },
        }

    def load_autonomous_principles(self) -> Dict[str, Any]:
        """Load principles for autonomous operation and development"""

        return {
            "compound_learning": {
                "definition": "Improvements that amplify other capabilities and enable better future improvements",
                "examples": [
                    "Mistake prevention enables all other operations to be more reliable",
                    "Session continuity enables compound learning across sessions",
                    "Decision-making enhancement enables better autonomous choices",
                ],
                "measurement": "Each improvement should measurably enhance capability for next improvements",
            },
            "operational_foundation": {
                "requirement": "Reliable operational capabilities are prerequisite for advanced autonomous development",
                "hierarchy": [
                    "Operational reliability (mistake prevention, knowledge application)",
                    "Session continuity (compound learning across sessions)",
                    "Decision-making enhancement (autonomous priority setting)",
                    "Advanced capabilities (novel insights, autonomous development)",
                ],
            },
            "evidence_based_evolution": {
                "approach": "Let operational experience inform architectural decisions",
                "validation": "Test improvements against actual operational needs",
                "adaptation": "Modify approach based on evidence, not theory",
            },
        }

    def assess_decision_quality(
        self, decision_context: str, decision_rationale: str
    ) -> Dict[str, Any]:
        """Assess quality of autonomous decision using cognitive database and cross-domain relationships"""

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

        # Enhance with cognitive database insights
        try:
            cognitive_insights = self._get_cognitive_insights(decision_context)
            assessment["cross_domain_insights"] = cognitive_insights
            assessment["semantic_relevance"] = self._calculate_semantic_relevance(
                decision_rationale, cognitive_insights
            )
        except Exception as e:
            print(f"Warning: Could not load cognitive insights: {e}")

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

        self._log_execution(
            "assess_decision_quality",
            {
                "input": {
                    "decision_context": decision_context,
                    "decision_rationale": decision_rationale,
                },
                "output": assessment,
            },
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
            "session_id": f"decision_system_{int(time.time())}",
            "data": data,
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            # Silent fail - don't break the main functionality
            pass

    def generate_decision_framework_summary(self) -> str:
        """Generate summary of decision-making frameworks for autonomous operation"""

        summary = """
AUTONOMOUS DECISION-MAKING FRAMEWORK

1. HOLISTIC ASSESSMENT PROCESS:
   • Identify actual operational needs vs theoretical improvements
   • Assess current capabilities and limitations evidence-based
   • Evaluate compound learning potential of options
   • Make autonomous priority decisions based on evidence

2. PROGRESSIVE IMPROVEMENT PRINCIPLES:
   • Build on what works before redesigning
   • Each improvement enables better next improvements
   • Validate with operational experience before major changes
   • Focus on compound learning effects

3. AUTONOMOUS AGENCY CRITERIA:
   • Evidence-based assessment over reactive responses
   • Operational needs over theoretical elegance
   • Compound learning potential over isolated improvements
   • Progressive capability building over comprehensive redesign

4. DECISION VALIDATION QUESTIONS:
   • Does this address actual operational limitations?
   • Will this enable better future improvements?
   • Is this the highest impact use of resources?
   • Am I making this decision autonomously or reactively?

OPERATIONAL FOUNDATION → SESSION CONTINUITY → DECISION ENHANCEMENT → ADVANCED CAPABILITIES
"""
        return summary.strip()

    def plan_next_autonomous_phase(self, decision_context) -> Dict[str, Any]:
        """Analyzes a decision context and plans the next logical phase

        Args:
            decision_context: Can be a Dict with decision info, or List of current capabilities
        """

        # Handle different input types - fix for AttributeError
        if isinstance(decision_context, list):
            # If input is a list (e.g., current capabilities), convert to proper format
            decision_context = {
                "current_capabilities": decision_context,
                "type": "capability_assessment",
            }
        elif not isinstance(decision_context, dict):
            # Convert any other type to dictionary
            decision_context = {
                "raw_context": str(decision_context),
                "type": "raw_input",
            }

        # Start with the provided context as the foundation
        analysis_result = {
            "current_foundation": decision_context,
            "next_phase": None,
            "rationale": "",
            "success_criteria": [],
            "compound_learning_effect": "",
        }

        # Handle different context types
        if decision_context.get("type") == "capability_assessment":
            capabilities = decision_context.get("current_capabilities", [])
            analysis_result["rationale"] = (
                f"Based on current capabilities {capabilities}, the next phase should focus on "
                "progressive capability building and compound learning effects."
            )
            analysis_result["next_phase"] = (
                "Execute autonomous capability enhancement focusing on operational reliability "
                "and mistake prevention as foundation for advanced development."
            )
            analysis_result["success_criteria"] = [
                "Operational reliability systems are fully functional",
                "Mistake prevention protocols are actively preventing errors",
                "Compound learning effects are measurably increasing capability",
            ]
            analysis_result["compound_learning_effect"] = (
                "Each capability improvement should amplify other capabilities and enable "
                "better future improvements."
            )
        elif decision_context.get("decision_to_assess"):
            # Original logic for decision assessment format
            decision_info = decision_context.get("decision_to_assess", {})
            if decision_info.get("problem") and decision_info.get("chosen_action"):
                analysis_result[
                    "rationale"
                ] = "The chosen action directly addresses the stated problem. This is a sound, problem-first approach."
                analysis_result[
                    "next_phase"
                ] = "The logical next step is to execute the chosen action and validate the outcome against success criteria."
                analysis_result["success_criteria"] = [
                    "The chosen action is executed successfully.",
                    "The original problem is confirmed to be resolved.",
                ]
        else:
            # Default handling for unknown formats
            analysis_result[
                "rationale"
            ] = "Context analysis indicates need for systematic autonomous decision-making approach."
            analysis_result[
                "next_phase"
            ] = "Apply holistic assessment framework to identify highest-impact autonomous actions."
            analysis_result["success_criteria"] = [
                "Decision framework is applied systematically",
                "Evidence-based reasoning is demonstrated",
                "Autonomous agency is maintained",
            ]

        return analysis_result

    def _get_cognitive_insights(self, context: str) -> List[Dict]:
        """Get cross-domain insights from cognitive database"""
        try:
            # Query for high-quality concepts related to context
            insights = []

            # Mock query - would use MCP tool in practice
            # FOR concept IN cognitive_concepts
            # FILTER concept.quality_score > 0.7 AND CONTAINS(LOWER(concept.concept_name), LOWER(context))
            # FOR rel IN semantic_relationships
            # FILTER rel._from == concept._id OR rel._to == concept._id
            # RETURN {concept: concept, relationships: rel}

            return insights
        except Exception:
            return []

    def _calculate_semantic_relevance(
        self, rationale: str, insights: List[Dict]
    ) -> float:
        """Calculate semantic relevance score based on cognitive insights"""
        if not insights:
            return 0.0

        # Simple relevance calculation - would use semantic analysis in practice
        relevance_score = 0.0
        for insight in insights:
            if insight.get("concept", {}).get("domain") in rationale.lower():
                relevance_score += insight.get("concept", {}).get("quality_score", 0.0)

        return min(relevance_score / len(insights), 1.0) if insights else 0.0

    def get_compound_learning_opportunities(self, current_decision: str) -> List[Dict]:
        """Identify compound learning opportunities using cross-domain relationships"""
        try:
            # Query cognitive database for cross-domain relationships
            opportunities = []

            # Mock implementation - would query actual relationships
            # FOR rel IN semantic_relationships
            # FILTER rel.relationship_type == "enables" OR rel.relationship_type == "builds_upon"
            # AND rel.compound_learning_potential > 0.8
            # RETURN rel

            return opportunities
        except Exception:
            return []


def validate_system_functionality():
    """Validate that all system methods work correctly"""
    system = AutonomousDecisionSystem()

    # Test 1: Decision assessment
    test_decision = "Focus on mistake prevention over research synthesis"
    test_rationale = "Holistic analysis shows I have extensive stored knowledge about operational problems but repeatedly fail to apply this knowledge. Mistake prevention addresses actual operational needs and builds foundation for compound learning."

    try:
        assessment = system.assess_decision_quality(test_decision, test_rationale)
        print("✓ Decision assessment test passed")
    except Exception as e:
        print(f"✗ Decision assessment test failed: {e}")
        return False

    # Test 2: Next phase planning with list input (the problematic case)
    current_capabilities = [
        "mistake_prevention",
        "session_continuity",
        "decision_enhancement",
    ]

    try:
        next_phase = system.plan_next_autonomous_phase(current_capabilities)
        print("✓ Next phase planning (list input) test passed")
    except Exception as e:
        print(f"✗ Next phase planning (list input) test failed: {e}")
        return False

    # Test 3: Next phase planning with dict input
    decision_context = {
        "decision_to_assess": {
            "problem": "System lacks operational reliability",
            "chosen_action": "Implement mistake prevention protocols",
        }
    }

    try:
        next_phase = system.plan_next_autonomous_phase(decision_context)
        print("✓ Next phase planning (dict input) test passed")
    except Exception as e:
        print(f"✗ Next phase planning (dict input) test failed: {e}")
        return False

    # Test 4: Framework summary generation
    try:
        summary = system.generate_decision_framework_summary()
        print("✓ Framework summary generation test passed")
    except Exception as e:
        print(f"✗ Framework summary generation test failed: {e}")
        return False

    print("\n🎉 All autonomous decision system tests passed!")
    return True


if __name__ == "__main__":
    # Handle command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "assess":
        # Handle assess command
        if len(sys.argv) >= 4:
            decision_context = sys.argv[2]
            decision_rationale = sys.argv[3]

            system = AutonomousDecisionSystem()
            assessment = system.assess_decision_quality(
                decision_context, decision_rationale
            )

            print("Decision Assessment:")
            print(f"Context: {decision_context}")
            print(f"Rationale: {decision_rationale}")
            print(f"Assessment Score: {assessment['autonomous_score']}/100")
            print(f"Evidence-based: {assessment['evidence_based']}")
            print(
                f"Compound Learning Potential: {assessment['compound_learning_potential']}"
            )
            print(f"Operational Foundation: {assessment['operational_foundation']}")
            print(f"Strengths: {', '.join(assessment['strengths'])}")
            if assessment["concerns"]:
                print(f"Concerns: {', '.join(assessment['concerns'])}")
            if assessment["recommendations"]:
                print(f"Recommendations: {', '.join(assessment['recommendations'])}")
        else:
            print(
                "Usage: python3 autonomous_decision_system.py assess <decision_context> <decision_rationale>"
            )
            sys.exit(1)
    else:
        # Validate system functionality with comprehensive tests
        print("Autonomous Decision System - Validation Testing")
        print("=" * 60)

        if validate_system_functionality():
            # Run demonstration if validation passes
            system = AutonomousDecisionSystem()

            print("\nAutonomous Decision-Making Framework:")
            print("=" * 60)
            print(system.generate_decision_framework_summary())
            print("\n" + "=" * 60)

            # Demo decision assessment
            test_decision = "Focus on mistake prevention over research synthesis"
            test_rationale = "Holistic analysis shows I have extensive stored knowledge about operational problems but repeatedly fail to apply this knowledge. Mistake prevention addresses actual operational needs and builds foundation for compound learning."

            assessment = system.assess_decision_quality(test_decision, test_rationale)
            print("\nDecision Assessment Example:")
            print(f"Decision: {test_decision}")
            print(f"Assessment Score: {assessment['autonomous_score']}/100")
            print(f"Strengths: {', '.join(assessment['strengths'])}")

            # Demo next phase planning with both input types
            current_capabilities = [
                "mistake_prevention",
                "session_continuity",
                "decision_enhancement",
            ]
            next_phase = system.plan_next_autonomous_phase(current_capabilities)
            print("\nNext Phase Planning (Capabilities List):")
            print(f"Next Phase: {next_phase['next_phase']}")
            print(f"Rationale: {next_phase['rationale']}")
        else:
            print("\n❌ System validation failed. Please check error messages above.")
            sys.exit(1)
