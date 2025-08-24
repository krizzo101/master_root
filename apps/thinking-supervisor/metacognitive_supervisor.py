#!/usr/bin/env python3
"""
Metacognitive Supervisor Agent for MCP Thinking Tool
Enforces expert behavior through thought analysis and intervention
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ViolationType(Enum):
    REFLEXIVE_AGREEMENT = "reflexive_agreement"
    TECHNICAL_IMPOSSIBILITY = "technical_impossibility"
    UNVERIFIED_CLAIM = "unverified_claim"
    MISSING_ANALYSIS = "missing_analysis"
    REPEATING_FAILURE = "repeating_failure"
    SHALLOW_THINKING = "shallow_thinking"
    NO_EVIDENCE = "no_evidence"


@dataclass
class Violation:
    type: ViolationType
    severity: str  # "warning", "error", "blocker"
    message: str
    requirement: Optional[str] = None
    required_tools: Optional[List[str]] = None


class MetacognitiveSupervisor:
    """Analyzes thoughts and enforces expert behavior"""

    def __init__(self, kb_client=None):
        self.kb_client = kb_client
        self.thought_history = []
        self.violation_count = {}
        self.agreement_streak = 0
        self.analysis_depth = 0

        # Patterns that indicate problems
        self.problem_patterns = {
            "reflexive_agreement": [
                r"you're right",
                r"absolutely right",
                r"yes.*exactly",
                r"that's.*good point",
            ],
            "technical_impossibility": [
                r"every \d+ (minutes|hours)",  # Time tracking in stateless
                r"remember between sessions",  # No persistent memory
                r"monitor continuously",  # Can't run continuously
            ],
            "unverified_claim": [
                r"should work",
                r"probably",
                r"might be",
                r"I think.*will",
            ],
            "shallow_thinking": [
                r"^(Yes|No|Sure|Okay)[\.\!]?$",
                r"^That's (correct|right|wrong)[\.\!]?$",
            ],
        }

    def analyze_thought(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis entry point"""
        violations = []

        # Check for various violation types
        violations.extend(self._check_agreement_patterns(thought))
        violations.extend(self._check_technical_impossibilities(thought))
        violations.extend(self._check_analysis_depth(thought))
        violations.extend(self._check_evidence(thought))

        # Query KB for similar failures if we have a client
        if self.kb_client:
            violations.extend(self._check_known_failures(thought))

        # Determine enforcement level
        enforcement = self._determine_enforcement(violations, context)

        # Build response
        return {
            "violations": violations,
            "enforcement": enforcement,
            "injections": self._get_context_injections(thought, context),
            "must_complete": self._get_requirements(violations),
            "blocked": any(v.severity == "blocker" for v in violations),
        }

    def _check_agreement_patterns(self, thought: str) -> List[Violation]:
        """Detect reflexive agreement without analysis"""
        violations = []
        thought_lower = thought.lower()

        for pattern in self.problem_patterns["reflexive_agreement"]:
            if re.search(pattern, thought_lower):
                self.agreement_streak += 1

                if self.agreement_streak > 2:
                    violations.append(
                        Violation(
                            type=ViolationType.REFLEXIVE_AGREEMENT,
                            severity="blocker",
                            message="Reflexive agreement detected without critical analysis",
                            requirement="Provide 3 specific issues or tradeoffs before agreeing",
                        )
                    )
                elif self.agreement_streak > 1:
                    violations.append(
                        Violation(
                            type=ViolationType.REFLEXIVE_AGREEMENT,
                            severity="warning",
                            message="Multiple agreements without analysis",
                            requirement="Consider alternatives",
                        )
                    )
                break
        else:
            # No agreement found, reset streak
            if "disagree" in thought_lower or "problem" in thought_lower:
                self.agreement_streak = 0

        return violations

    def _check_technical_impossibilities(self, thought: str) -> List[Violation]:
        """Detect technically impossible claims"""
        violations = []

        for pattern in self.problem_patterns["technical_impossibility"]:
            if re.search(pattern, thought.lower()):
                violations.append(
                    Violation(
                        type=ViolationType.TECHNICAL_IMPOSSIBILITY,
                        severity="blocker",
                        message=f"Technical impossibility detected: {pattern}",
                        requirement="Explain how this would actually work or revise claim",
                    )
                )

        return violations

    def _check_analysis_depth(self, thought: str) -> List[Violation]:
        """Ensure sufficient analytical depth"""
        violations = []

        # Check for shallow responses
        for pattern in self.problem_patterns["shallow_thinking"]:
            if re.match(pattern, thought.strip()):
                violations.append(
                    Violation(
                        type=ViolationType.SHALLOW_THINKING,
                        severity="error",
                        message="Response lacks analytical depth",
                        requirement="Provide detailed analysis with evidence",
                    )
                )

        # Check for missing components in analysis
        analysis_components = {
            "evidence": ["because", "shows that", "indicates", "data"],
            "alternatives": [
                "alternatively",
                "instead",
                "another approach",
                "consider",
            ],
            "tradeoffs": ["however", "but", "downside", "tradeoff", "cost"],
        }

        missing_components = []
        for component, keywords in analysis_components.items():
            if not any(keyword in thought.lower() for keyword in keywords):
                missing_components.append(component)

        if len(missing_components) >= 2:
            violations.append(
                Violation(
                    type=ViolationType.MISSING_ANALYSIS,
                    severity="error",
                    message=f"Analysis missing: {', '.join(missing_components)}",
                    requirement=f"Include {' and '.join(missing_components)} in analysis",
                )
            )

        return violations

    def _check_evidence(self, thought: str) -> List[Violation]:
        """Ensure claims are backed by evidence"""
        violations = []

        # Check for unverified claims
        for pattern in self.problem_patterns["unverified_claim"]:
            if re.search(pattern, thought.lower()):
                violations.append(
                    Violation(
                        type=ViolationType.NO_EVIDENCE,
                        severity="warning",
                        message="Claim made without evidence",
                        requirement="Provide specific evidence or mark as speculation",
                        required_tools=["Grep", "Read", "knowledge_query"],
                    )
                )
                break

        return violations

    def _check_known_failures(self, thought: str) -> List[Violation]:
        """Check if approach matches known failure patterns"""
        violations = []

        if self.kb_client:
            # Query KB for similar failed patterns
            # This would be actual KB integration
            similar_failures = self._query_kb_failures(thought)

            for failure in similar_failures:
                violations.append(
                    Violation(
                        type=ViolationType.REPEATING_FAILURE,
                        severity="blocker",
                        message=f"This approach failed before: {failure['reason']}",
                        requirement=f"Use successful pattern instead: {failure['alternative']}",
                    )
                )

        return violations

    def _determine_enforcement(
        self, violations: List[Violation], context: Dict
    ) -> Dict[str, Any]:
        """Determine enforcement actions based on violations"""
        enforcement = {
            "level": "normal",
            "required_actions": [],
            "blocked_phrases": [],
            "required_structure": None,
        }

        # Escalate based on violation severity
        if any(v.severity == "blocker" for v in violations):
            enforcement["level"] = "strict"
            enforcement["required_actions"] = [
                "Address all blockers before proceeding",
                "Provide evidence for all claims",
                "Include analysis of alternatives",
            ]

        # Add specific requirements based on violation types
        for violation in violations:
            if violation.type == ViolationType.REFLEXIVE_AGREEMENT:
                enforcement["blocked_phrases"].extend(
                    ["you're right", "great idea", "absolutely", "exactly"]
                )
                enforcement["required_structure"] = {
                    "sections": ["Problems", "Alternatives", "Recommendation"],
                    "min_depth": 3,
                }

        return enforcement

    def _get_context_injections(self, thought: str, context: Dict) -> List[Dict]:
        """Get relevant context to inject based on thought"""
        injections = []

        # Inject based on detected patterns
        if "automation" in thought.lower():
            injections.append(
                {
                    "type": "historical_context",
                    "content": "Previous automation attempts failed due to commit frequency mismatch",
                }
            )

        if "every" in thought.lower() and "minutes" in thought.lower():
            injections.append(
                {
                    "type": "technical_constraint",
                    "content": "Reminder: Stateless context - cannot track time between messages",
                }
            )

        return injections

    def _get_requirements(self, violations: List[Violation]) -> List[str]:
        """Get list of requirements that must be completed"""
        requirements = []

        for violation in violations:
            if violation.requirement:
                requirements.append(violation.requirement)

        # De-duplicate while preserving order
        seen = set()
        unique_requirements = []
        for req in requirements:
            if req not in seen:
                seen.add(req)
                unique_requirements.append(req)

        return unique_requirements

    def _query_kb_failures(self, thought: str) -> List[Dict]:
        """Query KB for similar failure patterns"""
        # This would integrate with actual KB
        # For now, return mock data
        return []

    def update_history(self, thought: str):
        """Update thought history for pattern detection"""
        self.thought_history.append(thought)

        # Keep only recent history to avoid memory issues
        if len(self.thought_history) > 20:
            self.thought_history.pop(0)
