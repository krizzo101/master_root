"""
Gap Analyzer Module

Analyzes information gaps and prioritizes them for completion.
Extracted from request_validation.py for better modularity.
"""

import logging
from typing import List, Tuple

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.validation_models import (
    GapAnalysisResult,
    GapPriority,
    InformationGap,
    RequestType,
    ValidationResult,
)
from src.applications.oamat_sd.src.validation.schema_registry import (
    RequestSchemaRegistry,
)


class GapAnalyzer:
    """Analyzes information gaps and prioritizes them for completion"""

    def __init__(self, schema_registry: RequestSchemaRegistry):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.schema_registry = schema_registry

    def prioritize_gaps(
        self, missing_fields: List[str], request_type: RequestType
    ) -> List[InformationGap]:
        """Prioritize missing information gaps."""
        schema = self.schema_registry.get_schema(request_type)
        if not schema:
            return []

        gaps = []
        field_map = {field.name: field for field in schema.fields}

        for field_name in missing_fields:
            field = field_map.get(field_name)
            if not field:
                continue

            # Determine priority
            if field.required:
                priority = GapPriority.CRITICAL
            elif field_name in ["framework", "database", "authentication"]:
                priority = GapPriority.IMPORTANT
            else:
                priority = GapPriority.OPTIONAL

            # Determine if researchable
            researchable = field_name in [
                "framework",
                "database",
                "styling",
                "language",
                "tools",
                "communication",
                "orchestration",
            ]

            # Create gap
            gap = InformationGap(
                field_name=field_name,
                priority=priority,
                description=field.description,
                researchable=researchable,
                suggested_defaults=[field.default] if field.default else [],
                research_keywords=(
                    [field_name, request_type.value] if researchable else []
                ),
            )
            gaps.append(gap)

        return gaps

    def calculate_confidence(self, gaps: List[InformationGap]) -> float:
        """Calculate confidence based on gaps."""
        if not gaps:
            return 1.0

        critical_gaps = len([g for g in gaps if g.priority == GapPriority.CRITICAL])
        important_gaps = len([g for g in gaps if g.priority == GapPriority.IMPORTANT])
        optional_gaps = len([g for g in gaps if g.priority == GapPriority.OPTIONAL])

        # Weight gaps by priority
        penalty = (critical_gaps * 0.4) + (important_gaps * 0.2) + (optional_gaps * 0.1)
        confidence = max(0.0, 1.0 - penalty)

        return confidence

    def categorize_gaps(
        self, gaps: List[InformationGap]
    ) -> Tuple[List[InformationGap], List[InformationGap]]:
        """Categorize gaps into researchable and unresearchable."""
        researchable = [gap for gap in gaps if gap.researchable]
        unresearchable = [gap for gap in gaps if not gap.researchable]
        return researchable, unresearchable

    def analyze_gaps(self, validation_result: ValidationResult) -> GapAnalysisResult:
        """Perform comprehensive gap analysis."""
        self.logger.info(f"Analyzing gaps for {validation_result.request_type}")

        # Prioritize gaps
        gaps = self.prioritize_gaps(
            validation_result.missing_fields, validation_result.request_type
        )

        # Calculate metrics - NO HARDCODED VALUES

        confidence = self.calculate_confidence(gaps)
        completeness_score = (
            1.0 - len(gaps) / ConfigManager().validation.gap_scoring_divisor
        )
        critical_gaps_count = len(
            [g for g in gaps if g.priority == GapPriority.CRITICAL]
        )

        # Categorize gaps
        researchable_gaps, unresearchable_gaps = self.categorize_gaps(gaps)

        self.logger.info(
            f"Gap analysis complete: {len(gaps)} total gaps, "
            f"{critical_gaps_count} critical, confidence: {confidence:.2f}"
        )

        return GapAnalysisResult(
            gaps=gaps,
            confidence=confidence,
            completeness_score=max(0.0, completeness_score),
            critical_gaps_count=critical_gaps_count,
            researchable_gaps=researchable_gaps,
            unresearchable_gaps=unresearchable_gaps,
        )

    def get_critical_gaps(self, gaps: List[InformationGap]) -> List[InformationGap]:
        """Get only critical gaps from a list."""
        return [gap for gap in gaps if gap.priority == GapPriority.CRITICAL]

    def get_researchable_gaps(self, gaps: List[InformationGap]) -> List[InformationGap]:
        """Get only researchable gaps from a list."""
        return [gap for gap in gaps if gap.researchable]

    def estimate_completion_difficulty(self, gap_analysis: GapAnalysisResult) -> str:
        """Estimate the difficulty of completing the gaps."""
        critical_count = gap_analysis.critical_gaps_count
        researchable_count = len(gap_analysis.researchable_gaps)
        total_gaps = len(gap_analysis.gaps)

        if critical_count > 3:
            return "High - Multiple critical gaps requiring user input"
        elif critical_count > 0 and researchable_count < critical_count:
            return "Medium-High - Critical gaps with limited research options"
        elif total_gaps > 5:
            return "Medium - Many gaps but mostly optional"
        elif researchable_count >= total_gaps * 0.7:
            return "Low - Most gaps can be researched automatically"
        else:
            return "Low-Medium - Few gaps with reasonable defaults"
