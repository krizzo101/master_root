#!/usr/bin/env python3
"""
Context Analyzer Module

Analyzes user requests and determines optimal context for LLM processing.
Can suggest which files, documentation, or other context should be included.
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class ContextRecommendation:
    """A recommendation for context inclusion."""
    file_paths: List[str]
    context_type: str  # "files", "documentation", "config", "tests"
    priority: int  # 1-5, where 1 is highest priority
    reason: str
    confidence: float  # 0.0-1.0


@dataclass
class ContextAnalysis:
    """Result of context analysis."""
    user_files: List[str]
    recommended_files: List[str]
    recommended_context: List[ContextRecommendation]
    analysis_summary: str
    confidence_score: float


class ContextAnalyzer:
    """Analyzes user requests to determine optimal context."""

    def __init__(self):
        self.context_patterns = {
            "bug_fix": [
                r"bug", r"fix", r"error", r"issue", r"problem", r"broken",
                r"doesn't work", r"not working", r"failing", r"crash"
            ],
            "feature_development": [
                r"add", r"implement", r"create", r"new feature", r"enhancement",
                r"improve", r"extend", r"build", r"develop"
            ],
            "refactoring": [
                r"refactor", r"clean up", r"restructure", r"reorganize",
                r"improve code", r"optimize", r"simplify"
            ],
            "testing": [
                r"test", r"unit test", r"integration test", r"coverage",
                r"test case", r"assertion", r"mock"
            ],
            "documentation": [
                r"document", r"comment", r"readme", r"docs", r"explain",
                r"describe", r"clarify", r"help"
            ],
            "configuration": [
                r"config", r"setting", r"environment", r"deploy", r"setup",
                r"install", r"dependency", r"package"
            ],
            "performance": [
                r"performance", r"speed", r"slow", r"optimize", r"efficient",
                r"memory", r"cpu", r"bottleneck"
            ],
            "security": [
                r"security", r"vulnerability", r"secure", r"authentication",
                r"authorization", r"encrypt", r"password", r"token"
            ]
        }

    def analyze_request(self, user_request: str, user_files: List[str] = None) -> ContextAnalysis:
        """
        Analyze a user request to determine optimal context.

        Args:
            user_request: The user's request/prompt
            user_files: Files provided by the user (optional)

        Returns:
            ContextAnalysis with recommendations
        """
        user_files = user_files or []

        # Analyze the request type
        request_type = self._classify_request(user_request)

        # Generate context recommendations
        recommendations = self._generate_recommendations(user_request, user_files, request_type)

        # Extract recommended files
        recommended_files = []
        for rec in recommendations:
            recommended_files.extend(rec.file_paths)

        # Create analysis summary
        summary = self._create_analysis_summary(request_type, recommendations)

        # Calculate confidence score
        confidence = self._calculate_confidence(user_request, request_type, recommendations)

        return ContextAnalysis(
            user_files=user_files,
            recommended_files=recommended_files,
            recommended_context=recommendations,
            analysis_summary=summary,
            confidence_score=confidence
        )

    def _classify_request(self, user_request: str) -> Dict[str, float]:
        """Classify the type of request based on keywords."""
        request_lower = user_request.lower()
        scores = {}

        for category, patterns in self.context_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, request_lower))
                score += matches * 0.1  # Weight per match

            if score > 0:
                scores[category] = min(score, 1.0)  # Cap at 1.0

        return scores

    def _generate_recommendations(self, user_request: str, user_files: List[str], request_type: Dict[str, float]) -> List[ContextRecommendation]:
        """Generate context recommendations based on request type."""
        recommendations = []

        # Add recommendations based on request type
        for category, score in request_type.items():
            if score > 0.3:  # Only consider significant matches
                rec = self._create_recommendation_for_category(category, score, user_files)
                if rec:
                    recommendations.append(rec)

        # Add general recommendations
        general_rec = self._create_general_recommendations(user_request, user_files)
        recommendations.extend(general_rec)

        # Sort by priority
        recommendations.sort(key=lambda x: x.priority)

        return recommendations

    def _create_recommendation_for_category(self, category: str, score: float, user_files: List[str]) -> Optional[ContextRecommendation]:
        """Create a recommendation for a specific request category."""
        if category == "bug_fix":
            return ContextRecommendation(
                file_paths=user_files,  # Keep user files
                context_type="files",
                priority=1,
                reason="Bug fixes require understanding the problematic code",
                confidence=score
            )

        elif category == "feature_development":
            return ContextRecommendation(
                file_paths=user_files,
                context_type="files",
                priority=1,
                reason="Feature development needs related modules and interfaces",
                confidence=score
            )

        elif category == "refactoring":
            return ContextRecommendation(
                file_paths=user_files,
                context_type="files",
                priority=1,
                reason="Refactoring requires understanding dependencies and usage",
                confidence=score
            )

        elif category == "testing":
            return ContextRecommendation(
                file_paths=[],
                context_type="tests",
                priority=2,
                reason="Testing requests need test files and test configuration",
                confidence=score
            )

        elif category == "documentation":
            return ContextRecommendation(
                file_paths=[],
                context_type="documentation",
                priority=2,
                reason="Documentation requests need existing docs and examples",
                confidence=score
            )

        elif category == "configuration":
            return ContextRecommendation(
                file_paths=[],
                context_type="config",
                priority=2,
                reason="Configuration requests need config files and settings",
                confidence=score
            )

        elif category == "performance":
            return ContextRecommendation(
                file_paths=user_files,
                context_type="files",
                priority=1,
                reason="Performance analysis needs the code being optimized",
                confidence=score
            )

        elif category == "security":
            return ContextRecommendation(
                file_paths=user_files,
                context_type="files",
                priority=1,
                reason="Security analysis needs the code being reviewed",
                confidence=score
            )

        return None

    def _create_general_recommendations(self, user_request: str, user_files: List[str]) -> List[ContextRecommendation]:
        """Create general recommendations based on the request."""
        recommendations = []

        # Always recommend keeping user-provided files
        if user_files:
            recommendations.append(ContextRecommendation(
                file_paths=user_files,
                context_type="files",
                priority=1,
                reason="User explicitly provided these files",
                confidence=1.0
            ))

        # Recommend related files if user provided files
        if user_files:
            recommendations.append(ContextRecommendation(
                file_paths=[],
                context_type="files",
                priority=3,
                reason="Related files (imports, imports-by, same directory) should be included",
                confidence=0.8
            ))

        # Recommend configuration files for any code changes
        if any(word in user_request.lower() for word in ["code", "file", "module", "class", "function"]):
            recommendations.append(ContextRecommendation(
                file_paths=[],
                context_type="config",
                priority=4,
                reason="Configuration files may be relevant for code changes",
                confidence=0.6
            ))

        return recommendations

    def _create_analysis_summary(self, request_type: Dict[str, float], recommendations: List[ContextRecommendation]) -> str:
        """Create a summary of the analysis."""
        if not request_type:
            return "General request - recommend user files and related context"

        primary_type = max(request_type.items(), key=lambda x: x[1])

        summary_parts = [f"Request classified as: {primary_type[0]} (confidence: {primary_type[1]:.2f})"]

        for rec in recommendations[:3]:  # Top 3 recommendations
            summary_parts.append(f"- {rec.context_type}: {rec.reason}")

        return "; ".join(summary_parts)

    def _calculate_confidence(self, user_request: str, request_type: Dict[str, float], recommendations: List[ContextRecommendation]) -> float:
        """Calculate confidence in the analysis."""
        if not request_type:
            return 0.3  # Low confidence for unclassified requests

        # Base confidence on request type classification
        max_type_score = max(request_type.values()) if request_type else 0
        base_confidence = max_type_score * 0.7

        # Boost confidence if we have user files
        if any(rec.file_paths for rec in recommendations):
            base_confidence += 0.2

        # Boost confidence if we have multiple strong recommendations
        strong_recommendations = [rec for rec in recommendations if rec.confidence > 0.7]
        if len(strong_recommendations) > 1:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def filter_recommendations_by_confidence(self, recommendations: List[ContextRecommendation], min_confidence: float = 0.5) -> List[ContextRecommendation]:
        """Filter recommendations by confidence threshold."""
        return [rec for rec in recommendations if rec.confidence >= min_confidence]

    def get_priority_recommendations(self, recommendations: List[ContextRecommendation], max_priority: int = 3) -> List[ContextRecommendation]:
        """Get recommendations up to a certain priority level."""
        return [rec for rec in recommendations if rec.priority <= max_priority]
