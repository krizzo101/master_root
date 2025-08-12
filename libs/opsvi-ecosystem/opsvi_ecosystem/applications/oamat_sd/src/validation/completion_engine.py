"""
Completion Engine Module

Fills information gaps through research and intelligent defaults.
Extracted from request_validation.py for better modularity.
"""

import logging
from typing import Any

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.validation_models import (
    CompletionResult,
    GapAnalysisResult,
    GapPriority,
    InformationGap,
)
from src.applications.oamat_sd.src.validation.schema_registry import (
    RequestSchemaRegistry,
)


class CompletionEngine:
    """Fills information gaps through research and intelligent defaults"""

    def __init__(self, schema_registry: RequestSchemaRegistry):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.schema_registry = schema_registry

        # Research database for common technology choices
        self.research_db = {
            "framework": {"web_application": "React", "default": "React"},
            "database": {
                "web_application": "PostgreSQL",
                "microservices": "PostgreSQL",
                "data_analysis": "PostgreSQL",
                "default": "PostgreSQL",
            },
            "styling": {"web_application": "Tailwind CSS", "default": "Tailwind CSS"},
            "language": {
                "simple_script": "Python",
                "data_analysis": "Python",
                "automation": "Python",
                "default": "Python",
            },
            "authentication": {
                "web_application": "JWT",
                "microservices": "OAuth2",
                "default": "JWT",
            },
            "communication": {"microservices": "REST API", "default": "REST API"},
            "tools": {"data_analysis": "pandas, matplotlib", "default": "pandas"},
            "orchestration": {"microservices": "Docker Compose", "default": "Docker"},
        }

    async def research_gap(
        self, gap: InformationGap, request_type: str = "default"
    ) -> Any | None:
        """Research information for a specific gap."""
        if not gap.researchable:
            return None

        # Get field-specific research data - NO FALLBACKS
        if gap.field_name not in self.research_db:
            return None

        field_research = self.research_db[gap.field_name]

        # Try request-type specific first, then explicit default check
        if request_type in field_research:
            result = field_research[request_type]
        elif "default" in field_research:
            result = field_research["default"]
        else:
            result = None

        if result:
            self.logger.debug(
                f"Researched {gap.field_name} = '{result}' for {request_type}"
            )

        return result

    def apply_defaults(self, gaps: list[InformationGap]) -> dict[str, Any]:
        """Apply reasonable defaults for gaps that have them."""
        defaults = {}

        for gap in gaps:
            if gap.suggested_defaults:
                defaults[gap.field_name] = gap.suggested_defaults[0]
                self.logger.debug(
                    f"Applied default {gap.field_name} = '{defaults[gap.field_name]}'"
                )

        return defaults

    def document_assumptions(
        self, filled_fields: dict[str, Any], applied_defaults: dict[str, Any]
    ) -> list[str]:
        """Document assumptions made during completion."""
        assumptions = []

        for field, value in applied_defaults.items():
            assumptions.append(f"Assumed {field} = '{value}' based on common defaults")

        for field, value in filled_fields.items():
            if field not in applied_defaults:
                assumptions.append(
                    f"Researched {field} = '{value}' based on best practices"
                )

        return assumptions

    def identify_escalation_needs(
        self, critical_gaps_remaining: list[str], gap_analysis: GapAnalysisResult
    ) -> bool:
        """Determine if escalation to user is required."""
        # Escalate if there are unresolved critical gaps that can't be researched
        critical_unresearchable = [
            gap
            for gap in gap_analysis.unresearchable_gaps
            if gap.priority == GapPriority.CRITICAL
            and gap.field_name in critical_gaps_remaining
        ]

        return len(critical_unresearchable) > 0

    async def complete_information(
        self, gap_analysis: GapAnalysisResult, request_type: str = "default"
    ) -> CompletionResult:
        """Complete missing information through research and defaults."""
        self.logger.info(f"Completing information for {len(gap_analysis.gaps)} gaps")

        filled_fields = {}
        research_results = {}

        # Research researchable gaps (excluding critical ones for safety)
        for gap in gap_analysis.researchable_gaps:
            if (
                gap.priority != GapPriority.CRITICAL
            ):  # Don't auto-research critical fields
                result = await self.research_gap(gap, request_type)
                if result:
                    filled_fields[gap.field_name] = result
                    research_results[gap.field_name] = result

        # Apply defaults for remaining gaps
        remaining_gaps = [
            g for g in gap_analysis.gaps if g.field_name not in filled_fields
        ]
        applied_defaults = self.apply_defaults(remaining_gaps)

        # Combine filled and default fields
        all_filled = {**filled_fields, **applied_defaults}

        # Document assumptions
        assumptions = self.document_assumptions(filled_fields, applied_defaults)

        # Identify remaining critical gaps
        critical_gaps_remaining = [
            gap.field_name
            for gap in gap_analysis.gaps
            if gap.priority == GapPriority.CRITICAL and gap.field_name not in all_filled
        ]

        # Determine if escalation is needed
        escalation_required = self.identify_escalation_needs(
            critical_gaps_remaining, gap_analysis
        )

        result = CompletionResult(
            filled_fields=filled_fields,
            applied_defaults=applied_defaults,
            research_results=research_results,
            assumptions=assumptions,
            escalation_required=escalation_required,
            critical_gaps_remaining=critical_gaps_remaining,
        )

        self.logger.info(
            f"Completion result: {len(filled_fields)} researched, "
            f"{len(applied_defaults)} defaulted, "
            f"{len(critical_gaps_remaining)} critical remaining, "
            f"escalation: {escalation_required}"
        )

        return result

    def get_completion_summary(self, completion_result: CompletionResult) -> str:
        """Get a human-readable summary of the completion results."""
        parts = []

        if completion_result.filled_fields:
            parts.append(f"Researched {len(completion_result.filled_fields)} fields")

        if completion_result.applied_defaults:
            parts.append(f"Applied {len(completion_result.applied_defaults)} defaults")

        if completion_result.critical_gaps_remaining:
            parts.append(
                f"{len(completion_result.critical_gaps_remaining)} critical gaps remain"
            )

        if completion_result.escalation_required:
            parts.append("User input required")

        return "; ".join(parts) if parts else "No gaps to complete"

    def get_research_confidence(
        self, field_name: str, request_type: str = "default"
    ) -> float:
        """Get confidence level for research results of a specific field - NO FALLBACKS"""
        if field_name not in self.research_db:
            return 0.0  # No research available

        field_research = self.research_db[field_name]

        if request_type in field_research and field_research[request_type]:
            return (
                ConfigManager().analysis.confidence.very_high_confidence
            )  # for type-specific research
        elif "default" in field_research and field_research["default"]:
            return (
                ConfigManager().analysis.confidence.default_confidence
            )  # for default research
        else:
            return 0.0  # No research available
