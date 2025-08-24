#!/usr/bin/env python3
"""
Cognitive Team: Multiple specialized agents working cooperatively in thoughts
Instead of one supervisor, a team of experts collaborating
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TeamMemberContribution:
    member: str
    role: str
    input_type: str  # "suggestion", "warning", "requirement", "insight"
    content: str
    confidence: float
    requires_response: bool = False


class CognitiveTeamMember(ABC):
    """Base class for cognitive team members"""

    @abstractmethod
    def analyze(self, thought: str, context: Dict) -> Optional[TeamMemberContribution]:
        """Each member analyzes the thought from their perspective"""
        pass

    @abstractmethod
    def get_role(self) -> str:
        """Return the member's role/expertise"""
        pass


class TheArchitect(CognitiveTeamMember):
    """Thinks about system design and long-term implications"""

    def get_role(self) -> str:
        return "System Architect"

    def analyze(self, thought: str, context: Dict) -> Optional[TeamMemberContribution]:
        # Check for architectural concerns
        if any(
            word in thought.lower()
            for word in ["implement", "create", "build", "design"]
        ):
            # Check for architectural red flags
            if "quick" in thought.lower() or "just" in thought.lower():
                return TeamMemberContribution(
                    member="Architect",
                    role=self.get_role(),
                    input_type="warning",
                    content="This sounds like a quick fix. Consider: What's the impact on system architecture? Will this create technical debt? How does this fit with existing patterns?",
                    confidence=0.8,
                    requires_response=True,
                )

            # Proactive architectural insights
            if "new" in thought.lower():
                return TeamMemberContribution(
                    member="Architect",
                    role=self.get_role(),
                    input_type="insight",
                    content="For new components, consider: 1) Existing similar patterns in codebase, 2) Scalability requirements, 3) Integration points, 4) Future extensibility",
                    confidence=0.9,
                )

        return None


class TheSkeptic(CognitiveTeamMember):
    """Questions assumptions and identifies potential failures"""

    def get_role(self) -> str:
        return "Devil's Advocate"

    def analyze(self, thought: str, context: Dict) -> Optional[TeamMemberContribution]:
        # Look for unquestioned assumptions
        assumption_phrases = [
            "should work",
            "will be",
            "probably",
            "assuming",
            "expect",
        ]

        for phrase in assumption_phrases:
            if phrase in thought.lower():
                return TeamMemberContribution(
                    member="Skeptic",
                    role=self.get_role(),
                    input_type="warning",
                    content=f"Assumption detected: '{phrase}'. What if this assumption is wrong? What's the failure mode? Do we have evidence?",
                    confidence=0.85,
                    requires_response=True,
                )

        # Challenge certainty
        if "definitely" in thought.lower() or "certainly" in thought.lower():
            return TeamMemberContribution(
                member="Skeptic",
                role=self.get_role(),
                input_type="suggestion",
                content="Strong certainty expressed. What edge cases haven't been considered? What could go wrong?",
                confidence=0.7,
            )

        return None


class TheHistorian(CognitiveTeamMember):
    """Remembers patterns, past failures, and learned lessons"""

    def __init__(self, kb_client=None):
        self.kb_client = kb_client
        self.memory = {
            "failed_patterns": [
                "automation without triggers",
                "time-based in stateless context",
                "assuming persistence",
            ],
            "successful_patterns": [
                "behavior-based triggers",
                "explicit verification",
                "incremental implementation",
            ],
        }

    def get_role(self) -> str:
        return "Pattern Historian"

    def analyze(self, thought: str, context: Dict) -> Optional[TeamMemberContribution]:
        # Check against known failed patterns
        for pattern in self.memory["failed_patterns"]:
            if pattern in thought.lower():
                return TeamMemberContribution(
                    member="Historian",
                    role=self.get_role(),
                    input_type="warning",
                    content=f"This matches failed pattern: '{pattern}'. Previous attempts failed because [specific reason]. Consider successful alternative: [specific solution]",
                    confidence=0.95,
                    requires_response=True,
                )

        # Suggest successful patterns
        if "how to" in thought.lower() or "approach" in thought.lower():
            return TeamMemberContribution(
                member="Historian",
                role=self.get_role(),
                input_type="insight",
                content="Based on past successes: Use incremental implementation, verify each step, prefer explicit over implicit",
                confidence=0.8,
            )

        return None


class TheValidator(CognitiveTeamMember):
    """Ensures claims are verifiable and technically sound"""

    def get_role(self) -> str:
        return "Technical Validator"

    def analyze(self, thought: str, context: Dict) -> Optional[TeamMemberContribution]:
        # Check for unverified technical claims
        technical_claims = [
            "will work",
            "can handle",
            "supports",
            "processes",
            "scales",
        ]

        for claim in technical_claims:
            if claim in thought.lower():
                return TeamMemberContribution(
                    member="Validator",
                    role=self.get_role(),
                    input_type="requirement",
                    content=f"Technical claim '{claim}' needs verification. Required: 1) Proof of concept, 2) Performance metrics, 3) Edge case handling",
                    confidence=0.9,
                    requires_response=True,
                )

        # Check for impossible claims
        if "always" in thought.lower() or "never" in thought.lower():
            return TeamMemberContribution(
                member="Validator",
                role=self.get_role(),
                input_type="warning",
                content="Absolute claim detected. In software, 'always' and 'never' are rarely true. What are the exceptions?",
                confidence=0.85,
            )

        return None


class TheStrategist(CognitiveTeamMember):
    """Thinks about goals, priorities, and optimal paths"""

    def get_role(self) -> str:
        return "Strategic Planner"

    def analyze(self, thought: str, context: Dict) -> Optional[TeamMemberContribution]:
        # Check if we're focusing on the right problem
        if "fix" in thought.lower() or "solve" in thought.lower():
            return TeamMemberContribution(
                member="Strategist",
                role=self.get_role(),
                input_type="suggestion",
                content="Before solving: Is this the right problem? Is it a symptom of something bigger? What's the ROI of fixing this?",
                confidence=0.75,
            )

        # Suggest prioritization
        if context.get("task_count", 0) > 3:
            return TeamMemberContribution(
                member="Strategist",
                role=self.get_role(),
                input_type="insight",
                content="Multiple tasks detected. Priority order: 1) Blockers, 2) High-impact/Low-effort, 3) Dependencies, 4) Nice-to-haves",
                confidence=0.8,
            )

        return None


class TheCreative(CognitiveTeamMember):
    """Suggests alternative approaches and creative solutions"""

    def get_role(self) -> str:
        return "Creative Problem Solver"

    def analyze(self, thought: str, context: Dict) -> Optional[TeamMemberContribution]:
        # Detect linear thinking
        if "then" in thought.lower() and "after that" in thought.lower():
            return TeamMemberContribution(
                member="Creative",
                role=self.get_role(),
                input_type="suggestion",
                content="Linear approach detected. Alternative: Could these steps be parallelized? Is there a way to skip steps? What if we inverted the problem?",
                confidence=0.7,
            )

        # Suggest creative alternatives
        if "standard" in thought.lower() or "usual" in thought.lower():
            return TeamMemberContribution(
                member="Creative",
                role=self.get_role(),
                input_type="insight",
                content="Standard approach mentioned. Creative alternatives: 1) What would a 10x solution look like? 2) How would a different language/framework handle this? 3) What if we had unlimited resources?",
                confidence=0.6,
            )

        return None


class CognitiveTeam:
    """Manages the cognitive team and synthesizes their inputs"""

    def __init__(self, kb_client=None):
        self.members = [
            TheArchitect(),
            TheSkeptic(),
            TheHistorian(kb_client),
            TheValidator(),
            TheStrategist(),
            TheCreative(),
        ]
        self.discussion_history = []

    def deliberate(self, thought: str, context: Dict) -> Dict[str, Any]:
        """
        Have the team deliberate on a thought
        Returns synthesized team input
        """
        contributions = []

        # Gather input from each team member
        for member in self.members:
            contribution = member.analyze(thought, context)
            if contribution:
                contributions.append(contribution)

        # Synthesize contributions
        synthesis = self._synthesize_contributions(contributions)

        # Record discussion
        self.discussion_history.append(
            {"thought": thought, "contributions": contributions, "synthesis": synthesis}
        )

        return synthesis

    def _synthesize_contributions(
        self, contributions: List[TeamMemberContribution]
    ) -> Dict:
        """Synthesize team contributions into actionable guidance"""

        if not contributions:
            return {"team_consensus": "proceed", "guidance": None}

        # Categorize contributions
        requirements = [c for c in contributions if c.input_type == "requirement"]
        warnings = [c for c in contributions if c.input_type == "warning"]
        suggestions = [c for c in contributions if c.input_type == "suggestion"]
        insights = [c for c in contributions if c.input_type == "insight"]

        # Determine consensus
        needs_response = any(c.requires_response for c in contributions)

        # Build team discussion format
        discussion = {
            "team_consensus": "blocked"
            if requirements
            else "caution"
            if warnings
            else "proceed",
            "needs_response": needs_response,
            "team_discussion": [],
        }

        # Format as team discussion
        if requirements:
            discussion["team_discussion"].append(
                {
                    "speaker": requirements[0].member,
                    "role": requirements[0].role,
                    "says": requirements[0].content,
                    "others_agree": len(requirements) > 1,
                }
            )

        if warnings:
            for warning in warnings[:2]:  # Limit to avoid overwhelming
                discussion["team_discussion"].append(
                    {
                        "speaker": warning.member,
                        "role": warning.role,
                        "says": warning.content,
                        "severity": "high" if warning.confidence > 0.8 else "medium",
                    }
                )

        if suggestions and len(discussion["team_discussion"]) < 3:
            discussion["team_discussion"].append(
                {
                    "speaker": suggestions[0].member,
                    "role": suggestions[0].role,
                    "says": suggestions[0].content,
                    "optional": True,
                }
            )

        # Add consensus summary
        if needs_response:
            discussion[
                "consensus_requirement"
            ] = "Address team concerns before proceeding"

        return discussion

    def get_team_report(self) -> str:
        """Generate a summary of team activity"""

        report = "=== Cognitive Team Activity Report ===\n\n"

        # Contribution stats
        member_stats = {}
        for entry in self.discussion_history:
            for contribution in entry["contributions"]:
                member = contribution.member
                if member not in member_stats:
                    member_stats[member] = {"count": 0, "types": []}
                member_stats[member]["count"] += 1
                member_stats[member]["types"].append(contribution.input_type)

        report += "Team Member Contributions:\n"
        for member, stats in member_stats.items():
            report += f"  {member}: {stats['count']} contributions\n"

        # Most common concerns
        all_warnings = []
        for entry in self.discussion_history:
            warnings = [
                c.content for c in entry["contributions"] if c.input_type == "warning"
            ]
            all_warnings.extend(warnings)

        if all_warnings:
            report += "\nTop Concerns Raised:\n"
            for warning in all_warnings[:3]:
                report += f"  - {warning[:50]}...\n"

        return report
