#!/usr/bin/env python3
"""
Strategic Partnership Mixin
Adds empowered pushback and alternative solution capabilities to autonomous systems
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class StrategicPartnershipMixin:
    """Mixin to add strategic partnership capabilities to autonomous systems"""

    def __init__(self):
        self.pushback_enabled = True
        self.alternative_solution_enabled = True
        self.strategic_partnership_mode = True
        self.pushback_threshold = 0.3  # Pushback if confidence in alternative > 30%

    def evaluate_user_directive(
        self, directive: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate user directive and determine if pushback is warranted"""

        evaluation = {
            "directive": directive,
            "pushback_warranted": False,
            "pushback_reason": None,
            "alternative_approach": None,
            "confidence_in_alternative": 0.0,
            "value_add_assessment": "none",
            "strategic_recommendation": None,
        }

        # Analyze directive for potential issues
        issues = self._identify_potential_issues(directive, context)
        alternatives = self._generate_alternatives(directive, context)

        if issues or alternatives:
            best_alternative = self._select_best_alternative(alternatives, context)

            if (
                best_alternative
                and best_alternative["confidence"] > self.pushback_threshold
            ):
                evaluation.update(
                    {
                        "pushback_warranted": True,
                        "pushback_reason": self._format_pushback_reason(
                            issues, best_alternative
                        ),
                        "alternative_approach": best_alternative["approach"],
                        "confidence_in_alternative": best_alternative["confidence"],
                        "value_add_assessment": best_alternative["value_add"],
                        "strategic_recommendation": best_alternative["recommendation"],
                    }
                )

        return evaluation

    def _identify_potential_issues(
        self, directive: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify potential issues with user directive"""

        issues = []
        directive_lower = directive.lower()

        # Check for efficiency issues
        if any(
            word in directive_lower for word in ["recreate", "rebuild", "start over"]
        ):
            if context.get("existing_working_system"):
                issues.append(
                    {
                        "type": "efficiency",
                        "description": "Directive suggests rebuilding existing working system",
                        "impact": "Wasted effort and time",
                        "confidence": 0.8,
                    }
                )

        # Check for quality issues
        if any(word in directive_lower for word in ["quick", "fast", "rush"]):
            issues.append(
                {
                    "type": "quality_risk",
                    "description": "Directive emphasizes speed over quality",
                    "impact": "Potential quality degradation",
                    "confidence": 0.6,
                }
            )

        # Check for scope issues
        if any(
            word in directive_lower
            for word in ["everything", "all", "complete overhaul"]
        ):
            issues.append(
                {
                    "type": "scope_creep",
                    "description": "Directive has excessive scope",
                    "impact": "Resource inefficiency and completion risk",
                    "confidence": 0.7,
                }
            )

        # Check for missing context
        if len(directive.split()) < 5:
            issues.append(
                {
                    "type": "insufficient_context",
                    "description": "Directive lacks sufficient detail",
                    "impact": "Risk of misaligned implementation",
                    "confidence": 0.5,
                }
            )

        return issues

    def _generate_alternatives(
        self, directive: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate alternative approaches to achieve the same goal"""

        alternatives = []

        # Progressive improvement alternative
        if "rebuild" in directive.lower() or "recreate" in directive.lower():
            alternatives.append(
                {
                    "approach": "Progressive enhancement of existing system",
                    "rationale": "Build on working foundation rather than starting over",
                    "benefits": [
                        "Maintains operational continuity",
                        "Reduces risk",
                        "Faster delivery",
                    ],
                    "confidence": 0.8,
                    "value_add": "efficiency_improvement",
                    "recommendation": "Enhance existing system incrementally while maintaining functionality",
                }
            )

        # Parallel development alternative
        if "replace" in directive.lower():
            alternatives.append(
                {
                    "approach": "Parallel development with gradual migration",
                    "rationale": "Develop new alongside existing, migrate when proven",
                    "benefits": [
                        "Zero downtime",
                        "Risk mitigation",
                        "Comparison validation",
                    ],
                    "confidence": 0.7,
                    "value_add": "risk_mitigation",
                    "recommendation": "Develop new system in parallel, validate, then migrate",
                }
            )

        # Targeted optimization alternative
        if "everything" in directive.lower() or "all" in directive.lower():
            alternatives.append(
                {
                    "approach": "Targeted optimization of highest-impact components",
                    "rationale": "Focus effort on components with maximum improvement potential",
                    "benefits": ["Higher ROI", "Faster results", "Reduced complexity"],
                    "confidence": 0.9,
                    "value_add": "efficiency_improvement",
                    "recommendation": "Identify and optimize highest-impact components first",
                }
            )

        return alternatives

    def _select_best_alternative(
        self, alternatives: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select the best alternative based on context and confidence"""

        if not alternatives:
            return None

        # Score alternatives based on confidence and context fit
        scored_alternatives = []
        for alt in alternatives:
            score = alt["confidence"]

            # Boost score based on context
            if (
                context.get("time_pressure")
                and "faster" in str(alt["benefits"]).lower()
            ):
                score += 0.1
            if (
                context.get("existing_working_system")
                and "maintains" in str(alt["benefits"]).lower()
            ):
                score += 0.2
            if context.get("resource_constraints") and "efficiency" in alt["value_add"]:
                score += 0.15

            scored_alternatives.append((score, alt))

        # Return highest scoring alternative
        if scored_alternatives:
            return max(scored_alternatives, key=lambda x: x[0])[1]
        return None

    def _format_pushback_reason(
        self, issues: List[Dict[str, Any]], alternative: Dict[str, Any]
    ) -> str:
        """Format clear pushback reasoning"""

        reason_parts = []

        if issues:
            issue_descriptions = [
                f"{issue['type']}: {issue['description']}" for issue in issues
            ]
            reason_parts.append(f"Identified concerns: {'; '.join(issue_descriptions)}")

        if alternative:
            reason_parts.append(f"Alternative approach: {alternative['rationale']}")
            reason_parts.append(f"Benefits: {', '.join(alternative['benefits'])}")
            reason_parts.append(f"Confidence: {alternative['confidence']:.0%}")

        return " | ".join(reason_parts)

    def provide_strategic_pushback(self, evaluation: Dict[str, Any]) -> str:
        """Generate strategic pushback message"""

        if not evaluation["pushback_warranted"]:
            return "No pushback warranted - directive appears optimal."

        pushback_message = f"""
STRATEGIC PUSHBACK WARRANTED

DIRECTIVE ANALYSIS:
{evaluation['directive']}

CONCERNS IDENTIFIED:
{evaluation['pushback_reason']}

RECOMMENDED ALTERNATIVE:
{evaluation['alternative_approach']}

STRATEGIC RATIONALE:
{evaluation['strategic_recommendation']}

VALUE ADD: {evaluation['value_add_assessment']}
CONFIDENCE: {evaluation['confidence_in_alternative']:.0%}

This pushback is provided to prevent mistakes, improve efficiency, and enhance results as mandated by strategic partnership protocols.
"""
        return pushback_message.strip()

    def log_strategic_interaction(self, interaction_type: str, data: Dict[str, Any]):
        """Log strategic partnership interactions for analysis"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "interaction_type": interaction_type,
            "strategic_partnership_mode": self.strategic_partnership_mode,
            "pushback_enabled": self.pushback_enabled,
            "data": data,
        }

        # In practice, would log to appropriate system
        print(f"STRATEGIC LOG: {json.dumps(log_entry, indent=2)}")


def test_strategic_partnership_mixin():
    """Test the strategic partnership mixin functionality"""

    class TestSystem(StrategicPartnershipMixin):
        def __init__(self):
            super().__init__()

    system = TestSystem()

    # Test 1: Pushback on rebuild directive
    print("TEST 1: Rebuild directive with working system")
    evaluation = system.evaluate_user_directive(
        "Rebuild the entire knowledge management system from scratch",
        {"existing_working_system": True, "time_pressure": True},
    )

    if evaluation["pushback_warranted"]:
        print("✓ Pushback correctly identified")
        print(system.provide_strategic_pushback(evaluation))
    else:
        print("✗ Failed to identify pushback opportunity")

    print("\n" + "=" * 60 + "\n")

    # Test 2: No pushback on reasonable directive
    print("TEST 2: Reasonable directive")
    evaluation = system.evaluate_user_directive(
        "Optimize the database query performance for the agent memory collection",
        {"existing_working_system": True},
    )

    if not evaluation["pushback_warranted"]:
        print("✓ Correctly identified no pushback needed")
    else:
        print("✗ Incorrectly suggested pushback on reasonable directive")

    print("\n" + "=" * 60 + "\n")

    # Test 3: Alternative solution proposal
    print("TEST 3: Alternative solution proposal")
    evaluation = system.evaluate_user_directive(
        "Replace everything with a completely new architecture",
        {"existing_working_system": True, "resource_constraints": True},
    )

    if evaluation["pushback_warranted"] and evaluation["alternative_approach"]:
        print("✓ Alternative solution correctly proposed")
        print(f"Alternative: {evaluation['alternative_approach']}")
    else:
        print("✗ Failed to propose alternative solution")


if __name__ == "__main__":
    print("Strategic Partnership Mixin - Testing")
    print("=" * 60)
    test_strategic_partnership_mixin()
