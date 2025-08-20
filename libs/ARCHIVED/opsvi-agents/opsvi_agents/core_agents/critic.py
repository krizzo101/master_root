"""CriticAgent - Review and critique work."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class CritiqueLevel(Enum):
    """Levels of critique severity."""

    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class QualityDimension(Enum):
    """Dimensions of quality to evaluate."""

    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    EFFICIENCY = "efficiency"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    CONSISTENCY = "consistency"
    DOCUMENTATION = "documentation"


@dataclass
class Issue:
    """Individual issue found during critique."""

    level: CritiqueLevel
    dimension: QualityDimension
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None
    impact: Optional[str] = None
    priority: int = 3  # 1-5, 1 being highest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "dimension": self.dimension.value,
            "description": self.description,
            "location": self.location,
            "suggestion": self.suggestion,
            "impact": self.impact,
            "priority": self.priority,
        }


@dataclass
class Critique:
    """Complete critique of work."""

    work_id: str
    overall_score: float  # 0-100
    issues: List[Issue] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    dimension_scores: Dict[QualityDimension, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: Issue):
        """Add an issue to the critique."""
        self.issues.append(issue)
        # Recalculate score
        self._update_score()

    def _update_score(self):
        """Update overall score based on issues."""
        if not self.issues:
            self.overall_score = 100.0
            return

        # Deduct points based on issue severity
        deductions = {
            CritiqueLevel.INFO: 0,
            CritiqueLevel.SUGGESTION: 2,
            CritiqueLevel.WARNING: 5,
            CritiqueLevel.ERROR: 10,
            CritiqueLevel.CRITICAL: 20,
        }

        total_deduction = sum(
            deductions.get(issue.level, 0) / issue.priority for issue in self.issues
        )

        self.overall_score = max(0, 100 - total_deduction)

    def get_summary(self) -> Dict[str, Any]:
        """Get critique summary."""
        issue_counts = {}
        for level in CritiqueLevel:
            issue_counts[level.value] = sum(1 for i in self.issues if i.level == level)

        return {
            "work_id": self.work_id,
            "overall_score": self.overall_score,
            "total_issues": len(self.issues),
            "issue_breakdown": issue_counts,
            "strengths_count": len(self.strengths),
            "improvements_count": len(self.improvements),
            "dimensions_evaluated": len(self.dimension_scores),
        }

    def get_critical_issues(self) -> List[Issue]:
        """Get critical and error level issues."""
        return [
            issue
            for issue in self.issues
            if issue.level in [CritiqueLevel.CRITICAL, CritiqueLevel.ERROR]
        ]

    def get_actionable_items(self) -> List[Dict[str, Any]]:
        """Get actionable improvement items."""
        items = []

        for issue in self.issues:
            if issue.suggestion:
                items.append(
                    {
                        "type": "fix",
                        "priority": issue.priority,
                        "dimension": issue.dimension.value,
                        "issue": issue.description,
                        "action": issue.suggestion,
                        "location": issue.location,
                    }
                )

        for improvement in self.improvements:
            items.append({"type": "improvement", "priority": 3, "action": improvement})

        return sorted(items, key=lambda x: x["priority"])


class CriticAgent(BaseAgent):
    """Reviews and critiques work to ensure quality."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize critic agent."""
        super().__init__(
            config
            or AgentConfig(
                name="CriticAgent",
                description="Review and critique work",
                capabilities=[
                    "review",
                    "critique",
                    "suggest_improvements",
                    "quality_assurance",
                ],
                max_retries=2,
                timeout=60,
            )
        )
        self.critiques = {}
        self.standards = self._load_default_standards()
        self._critique_counter = 0

    def initialize(self) -> bool:
        """Initialize the critic agent."""
        logger.info("critic_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute critique task."""
        action = task.get("action", "critique")

        if action == "critique":
            return self._perform_critique(task)
        elif action == "compare":
            return self._compare_works(task)
        elif action == "suggest":
            return self._suggest_improvements(task)
        elif action == "validate":
            return self._validate_standards(task)
        elif action == "report":
            return self._generate_report(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def critique(
        self,
        work: Any,
        dimensions: Optional[List[QualityDimension]] = None,
        standards: Optional[Dict[str, Any]] = None,
    ) -> Critique:
        """Perform critique on work."""
        result = self.execute(
            {
                "action": "critique",
                "work": work,
                "dimensions": dimensions,
                "standards": standards,
            }
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["critique"]

    def _perform_critique(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed critique."""
        work = task.get("work")
        dimensions = task.get("dimensions")
        standards = task.get("standards", self.standards)

        if work is None:
            return {"error": "Work to critique is required"}

        # Generate critique ID
        self._critique_counter += 1
        critique_id = f"critique_{self._critique_counter}"

        # Create critique object
        critique = Critique(work_id=critique_id)

        # Determine dimensions to evaluate
        if not dimensions:
            dimensions = self._infer_dimensions(work)
        else:
            dimensions = [
                QualityDimension[d.upper()] if isinstance(d, str) else d
                for d in dimensions
            ]

        # Evaluate each dimension
        for dimension in dimensions:
            score, issues = self._evaluate_dimension(work, dimension, standards)
            critique.dimension_scores[dimension] = score
            critique.issues.extend(issues)

        # Identify strengths
        critique.strengths = self._identify_strengths(work, critique.dimension_scores)

        # Generate improvement suggestions
        critique.improvements = self._generate_improvements(critique.issues)

        # Calculate overall score
        if critique.dimension_scores:
            critique.overall_score = sum(critique.dimension_scores.values()) / len(
                critique.dimension_scores
            )
        else:
            critique.overall_score = 50.0  # Default if no dimensions evaluated

        # Store critique
        self.critiques[critique_id] = critique

        logger.info(
            "critique_completed",
            critique_id=critique_id,
            overall_score=critique.overall_score,
            issues_count=len(critique.issues),
            dimensions_evaluated=len(dimensions),
        )

        return {
            "critique": critique,
            "critique_id": critique_id,
            "summary": critique.get_summary(),
        }

    def _infer_dimensions(self, work: Any) -> List[QualityDimension]:
        """Infer relevant quality dimensions based on work type."""
        dimensions = [QualityDimension.CORRECTNESS, QualityDimension.COMPLETENESS]

        # Analyze work type
        if isinstance(work, str):
            # Text-based work
            dimensions.extend([QualityDimension.CLARITY, QualityDimension.CONSISTENCY])

            # Check for code-like content
            if any(
                indicator in work.lower()
                for indicator in ["def ", "class ", "function", "import"]
            ):
                dimensions.extend(
                    [
                        QualityDimension.EFFICIENCY,
                        QualityDimension.MAINTAINABILITY,
                        QualityDimension.SECURITY,
                    ]
                )
        elif isinstance(work, dict):
            # Structured data
            dimensions.append(QualityDimension.CONSISTENCY)

            if "performance" in work or "metrics" in work:
                dimensions.append(QualityDimension.PERFORMANCE)

            if "user" in work or "interface" in work:
                dimensions.append(QualityDimension.USABILITY)

        return list(set(dimensions))  # Remove duplicates

    def _evaluate_dimension(
        self, work: Any, dimension: QualityDimension, standards: Dict[str, Any]
    ) -> Tuple[float, List[Issue]]:
        """Evaluate a specific quality dimension."""
        issues = []
        score = 100.0

        if dimension == QualityDimension.CORRECTNESS:
            # Check for obvious errors
            if isinstance(work, str):
                # Check for common mistakes
                if "TODO" in work:
                    issues.append(
                        Issue(
                            level=CritiqueLevel.WARNING,
                            dimension=dimension,
                            description="Incomplete work: TODO items found",
                            suggestion="Complete all TODO items before submission",
                        )
                    )
                    score -= 10

                if "FIXME" in work:
                    issues.append(
                        Issue(
                            level=CritiqueLevel.ERROR,
                            dimension=dimension,
                            description="Known issues: FIXME items found",
                            suggestion="Address all FIXME items",
                        )
                    )
                    score -= 20

        elif dimension == QualityDimension.COMPLETENESS:
            # Check for completeness
            if isinstance(work, str) and len(work) < 50:
                issues.append(
                    Issue(
                        level=CritiqueLevel.WARNING,
                        dimension=dimension,
                        description="Work appears incomplete or too brief",
                        suggestion="Provide more comprehensive content",
                    )
                )
                score -= 15

        elif dimension == QualityDimension.CLARITY:
            # Check for clarity indicators
            if isinstance(work, str):
                # Check for overly complex sentences
                sentences = work.split(".")
                long_sentences = [s for s in sentences if len(s.split()) > 30]
                if long_sentences:
                    issues.append(
                        Issue(
                            level=CritiqueLevel.SUGGESTION,
                            dimension=dimension,
                            description=f"Found {len(long_sentences)} overly complex sentences",
                            suggestion="Break down complex sentences for better readability",
                        )
                    )
                    score -= 5

        elif dimension == QualityDimension.EFFICIENCY:
            # Check for efficiency issues
            if isinstance(work, str):
                # Look for nested loops (simplified check)
                if work.count("for ") > 2:
                    issues.append(
                        Issue(
                            level=CritiqueLevel.WARNING,
                            dimension=dimension,
                            description="Multiple loops detected, potential efficiency concern",
                            suggestion="Consider optimizing loop structures",
                        )
                    )
                    score -= 10

        elif dimension == QualityDimension.SECURITY:
            # Check for security issues
            if isinstance(work, str):
                security_keywords = ["password", "token", "secret", "key", "credential"]
                for keyword in security_keywords:
                    if keyword in work.lower() and "=" in work:
                        issues.append(
                            Issue(
                                level=CritiqueLevel.CRITICAL,
                                dimension=dimension,
                                description=f"Potential hardcoded {keyword} detected",
                                suggestion="Use environment variables or secure vaults for sensitive data",
                                impact="High security risk",
                            )
                        )
                        score -= 30
                        break

        elif dimension == QualityDimension.DOCUMENTATION:
            # Check for documentation
            if isinstance(work, str):
                # Check for comments or docstrings
                if "def " in work and '"""' not in work and "'''" not in work:
                    issues.append(
                        Issue(
                            level=CritiqueLevel.WARNING,
                            dimension=dimension,
                            description="Functions lack docstrings",
                            suggestion="Add docstrings to all functions",
                        )
                    )
                    score -= 15

        return max(0, score), issues

    def _identify_strengths(
        self, work: Any, dimension_scores: Dict[QualityDimension, float]
    ) -> List[str]:
        """Identify strengths in the work."""
        strengths = []

        # High-scoring dimensions
        for dimension, score in dimension_scores.items():
            if score >= 90:
                strengths.append(f"Excellent {dimension.value}")
            elif score >= 80:
                strengths.append(f"Good {dimension.value}")

        # Work-specific strengths
        if isinstance(work, str):
            if len(work) > 500:
                strengths.append("Comprehensive and detailed")

            if work.count("\n") > 10:
                strengths.append("Well-structured with clear formatting")

        return strengths

    def _generate_improvements(self, issues: List[Issue]) -> List[str]:
        """Generate improvement suggestions based on issues."""
        improvements = []

        # Group issues by dimension
        dimension_issues = {}
        for issue in issues:
            if issue.dimension not in dimension_issues:
                dimension_issues[issue.dimension] = []
            dimension_issues[issue.dimension].append(issue)

        # Generate improvements per dimension
        for dimension, dim_issues in dimension_issues.items():
            if len(dim_issues) > 2:
                improvements.append(
                    f"Focus on improving {dimension.value} across the work"
                )

            # Add specific suggestions
            for issue in dim_issues[:2]:  # Limit to top 2 per dimension
                if issue.suggestion and issue.suggestion not in improvements:
                    improvements.append(issue.suggestion)

        return improvements

    def _compare_works(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple works."""
        works = task.get("works", [])
        dimensions = task.get("dimensions")

        if len(works) < 2:
            return {"error": "At least 2 works required for comparison"}

        critiques = []
        for work in works:
            result = self._perform_critique({"work": work, "dimensions": dimensions})
            critiques.append(result["critique"])

        # Compare scores
        comparison = {
            "work_count": len(works),
            "best_overall": max(critiques, key=lambda c: c.overall_score),
            "dimension_winners": {},
            "rankings": sorted(critiques, key=lambda c: c.overall_score, reverse=True),
        }

        # Find best per dimension
        all_dimensions = set()
        for critique in critiques:
            all_dimensions.update(critique.dimension_scores.keys())

        for dimension in all_dimensions:
            scores = [
                (i, c.dimension_scores.get(dimension, 0))
                for i, c in enumerate(critiques)
            ]
            best_idx = max(scores, key=lambda x: x[1])[0]
            comparison["dimension_winners"][dimension.value] = f"Work {best_idx + 1}"

        return {"comparison": comparison}

    def _suggest_improvements(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed improvement suggestions."""
        critique_id = task.get("critique_id")

        if not critique_id or critique_id not in self.critiques:
            return {"error": f"Critique {critique_id} not found"}

        critique = self.critiques[critique_id]

        # Get actionable items
        actionable = critique.get_actionable_items()

        # Prioritize improvements
        high_priority = [item for item in actionable if item["priority"] <= 2]
        medium_priority = [item for item in actionable if item["priority"] == 3]
        low_priority = [item for item in actionable if item["priority"] > 3]

        suggestions = {
            "critique_id": critique_id,
            "immediate_actions": high_priority,
            "recommended_actions": medium_priority,
            "optional_improvements": low_priority,
            "estimated_score_improvement": min(
                100, critique.overall_score + len(actionable) * 5
            ),
        }

        return {"suggestions": suggestions}

    def _validate_standards(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate work against specific standards."""
        work = task.get("work")
        standards = task.get("standards", self.standards)
        strict = task.get("strict", False)

        if work is None:
            return {"error": "Work to validate is required"}

        violations = []
        warnings = []

        # Check each standard
        for standard_name, standard_rules in standards.items():
            if isinstance(standard_rules, dict):
                for rule_name, rule_value in standard_rules.items():
                    passed, message = self._check_rule(work, rule_name, rule_value)

                    if not passed:
                        if strict:
                            violations.append(f"{standard_name}.{rule_name}: {message}")
                        else:
                            warnings.append(f"{standard_name}.{rule_name}: {message}")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "standards_checked": len(standards),
        }

    def _check_rule(
        self, work: Any, rule_name: str, rule_value: Any
    ) -> Tuple[bool, str]:
        """Check a specific rule."""
        # Simplified rule checking
        if rule_name == "min_length" and isinstance(work, str):
            if len(work) < rule_value:
                return False, f"Work length {len(work)} is below minimum {rule_value}"

        elif rule_name == "max_length" and isinstance(work, str):
            if len(work) > rule_value:
                return False, f"Work length {len(work)} exceeds maximum {rule_value}"

        elif rule_name == "required_sections" and isinstance(work, str):
            for section in rule_value:
                if section not in work:
                    return False, f"Required section '{section}' not found"

        elif rule_name == "forbidden_content" and isinstance(work, str):
            for forbidden in rule_value:
                if forbidden in work:
                    return False, f"Forbidden content '{forbidden}' found"

        return True, "Passed"

    def _generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate critique report."""
        critique_id = task.get("critique_id")
        format_type = task.get("format", "summary")

        if not critique_id or critique_id not in self.critiques:
            return {"error": f"Critique {critique_id} not found"}

        critique = self.critiques[critique_id]

        if format_type == "summary":
            return {"report": critique.get_summary()}

        elif format_type == "detailed":
            return {
                "report": {
                    "summary": critique.get_summary(),
                    "issues": [issue.to_dict() for issue in critique.issues],
                    "strengths": critique.strengths,
                    "improvements": critique.improvements,
                    "dimension_scores": {
                        dim.value: score
                        for dim, score in critique.dimension_scores.items()
                    },
                }
            }

        elif format_type == "actionable":
            return {
                "report": {
                    "critical_issues": [
                        issue.to_dict() for issue in critique.get_critical_issues()
                    ],
                    "action_items": critique.get_actionable_items(),
                }
            }

        else:
            return {"error": f"Unknown report format: {format_type}"}

    def _load_default_standards(self) -> Dict[str, Any]:
        """Load default quality standards."""
        return {
            "code": {
                "min_length": 10,
                "max_length": 10000,
                "required_sections": [],
                "forbidden_content": ["eval(", "exec("],
            },
            "documentation": {
                "min_length": 100,
                "required_sections": ["Overview", "Usage"],
                "forbidden_content": [],
            },
            "general": {"min_length": 1, "max_length": 100000, "forbidden_content": []},
        }

    def shutdown(self) -> bool:
        """Shutdown the critic agent."""
        logger.info("critic_agent_shutdown", critiques_count=len(self.critiques))
        self.critiques.clear()
        return True
