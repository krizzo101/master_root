"""
Factor Analyzer Module

Analyzes individual complexity factors using pattern recognition and indicators.
Extracted from complexity_model.py for better modularity.
"""

import logging
from typing import Dict, List

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.complexity_models import ComplexityFactor


class FactorAnalyzer:
    """Analyzes individual complexity factors using pattern recognition"""

    def __init__(self, factor_weights: Dict[str, float]):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.factor_weights = factor_weights
        self.complexity_indicators = self._initialize_indicators()

    def _initialize_indicators(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize complexity indicators for automated detection."""
        return {
            "scope": {
                "high": [
                    "full stack",
                    "full-stack",
                    "end-to-end",
                    "complete system",
                    "entire platform",
                    "platform",
                    "comprehensive",
                ],
                "medium": [
                    "multi-component",
                    "several features",
                    "multiple pages",
                    "various modules",
                ],
                "low": ["single", "simple", "basic", "minimal", "one"],
            },
            "technical_depth": {
                "high": [
                    "machine learning",
                    "ai",
                    "blockchain",
                    "distributed",
                    "microservices",
                    "cloud native",
                ],
                "medium": [
                    "api",
                    "database",
                    "backend",
                    "frontend",
                    "integration",
                    "real-time",
                ],
                "low": ["script", "utility", "basic", "simple", "straightforward"],
            },
            "domain_knowledge": {
                "high": [
                    "finance",
                    "healthcare",
                    "legal",
                    "scientific",
                    "research",
                    "compliance",
                    "payment processing",
                ],
                "medium": [
                    "business",
                    "e-commerce",
                    "analytics",
                    "reporting",
                    "workflow",
                ],
                "low": ["general", "personal", "hobby", "learning", "demo"],
            },
            "dependencies": {
                "high": [
                    "third-party",
                    "external api",
                    "multiple services",
                    "legacy systems",
                    "complex integrations",
                    "payment processing",
                ],
                "medium": [
                    "database",
                    "authentication",
                    "payment",
                    "notification",
                    "file storage",
                ],
                "low": [
                    "standalone",
                    "self-contained",
                    "independent",
                    "no dependencies",
                ],
            },
            "timeline": {
                "urgent": ["asap", "urgent", "immediately", "rush", "emergency"],
                "normal": ["soon", "next week", "reasonable time", "standard"],
                "flexible": ["when possible", "no rush", "eventually", "flexible"],
            },
            "risk": {
                "high": [
                    "production",
                    "critical",
                    "mission critical",
                    "high availability",
                    "enterprise",
                    "payment processing",
                    "security",
                    "authentication",
                ],
                "medium": ["business", "important", "moderate risk", "staging"],
                "low": ["prototype", "poc", "demo", "learning", "test"],
            },
        }

    def _extract_request_text(self, request) -> str:
        """Extract text from request object in multiple formats"""
        if hasattr(request, "content"):
            return str(request.content).lower()
        elif hasattr(request, "description"):
            return str(request.description).lower()
        elif hasattr(request, "get"):
            # Dictionary-like request - extract content from keys
            if "content" in request and request["content"]:
                return str(request["content"]).lower()
            elif "description" in request and request["description"]:
                return str(request["description"]).lower()
            else:
                return str(request).lower()
        else:
            return str(request).lower()

    def analyze_scope_factor(self, request) -> ComplexityFactor:
        """Analyze scope complexity (1-10)."""
        request_text = self._extract_request_text(request)

        # Count scope indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["scope"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["scope"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["scope"]["low"]
            if indicator in request_text
        )

        # Analyze request structure
        features_count = len(request_text.split("feature")) + len(
            request_text.split("component")
        )
        pages_count = len(request_text.split("page")) + len(
            request_text.split("screen")
        )

        # Calculate score
        score = ConfigManager().analysis.scoring.base_score  # Base score

        if high_indicators > 0:
            score += ConfigManager().analysis.scoring.high_boost
        elif medium_indicators > 0:
            score += ConfigManager().analysis.scoring.medium_boost
        elif low_indicators > 0:
            score -= ConfigManager().analysis.scoring.small_penalty

        # Adjust based on feature count
        if features_count > 5:
            score += ConfigManager().analysis.scoring.medium_boost
        elif features_count > 2:
            score += ConfigManager().analysis.scoring.small_boost

        # Adjust based on page count
        if pages_count > 3:
            score += ConfigManager().analysis.scoring.small_boost

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Scope: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Features: {features_count}, Pages: {pages_count}"

        return ComplexityFactor(
            name="scope",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["scope"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"features:{features_count}",
                f"pages:{pages_count}",
            ],
        )

    def analyze_technical_depth_factor(self, request) -> ComplexityFactor:
        """Analyze technical depth complexity (1-10)."""
        request_text = self._extract_request_text(request)

        # Count technical indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["technical_depth"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["technical_depth"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["technical_depth"]["low"]
            if indicator in request_text
        )

        # Technical terms analysis
        tech_terms = [
            "algorithm",
            "optimization",
            "performance",
            "scalability",
            "architecture",
        ]
        tech_count = sum(1 for term in tech_terms if term in request_text)

        # Calculate score
        score = ConfigManager().analysis.scoring.base_score  # Base score

        if high_indicators > 0:
            score += ConfigManager().analysis.scoring.very_high_boost
        elif medium_indicators > 0:
            score += ConfigManager().analysis.scoring.medium_boost
        elif low_indicators > 0:
            score -= ConfigManager().analysis.scoring.small_penalty

        score += min(tech_count, 3)

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Technical: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Tech terms: {tech_count}"

        return ComplexityFactor(
            name="technical_depth",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["technical_depth"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"tech_terms:{tech_count}",
            ],
        )

    def analyze_domain_knowledge_factor(self, request) -> ComplexityFactor:
        """Analyze domain knowledge complexity (1-10)."""
        request_text = self._extract_request_text(request)

        # Count domain indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["domain_knowledge"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["domain_knowledge"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["domain_knowledge"]["low"]
            if indicator in request_text
        )

        # Domain-specific terms
        domain_terms = [
            "regulation",
            "compliance",
            "standard",
            "protocol",
            "specification",
        ]
        domain_count = sum(1 for term in domain_terms if term in request_text)

        # Calculate score
        score = ConfigManager().analysis.scoring.base_score  # Base score

        if high_indicators > 0:
            score += ConfigManager().analysis.scoring.high_boost
        elif medium_indicators > 0:
            score += ConfigManager().analysis.scoring.medium_boost
        elif low_indicators > 0:
            score -= ConfigManager().analysis.scoring.small_penalty

        score += min(domain_count, 2)

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Domain: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Domain terms: {domain_count}"

        return ComplexityFactor(
            name="domain_knowledge",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["domain_knowledge"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"domain_terms:{domain_count}",
            ],
        )

    def analyze_dependencies_factor(self, request) -> ComplexityFactor:
        """Analyze dependencies complexity (1-10)."""
        request_text = self._extract_request_text(request)

        # Count dependency indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["dependencies"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["dependencies"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["dependencies"]["low"]
            if indicator in request_text
        )

        # Integration terms
        integration_terms = ["integrate", "connect", "sync", "webhook", "event"]
        integration_count = sum(1 for term in integration_terms if term in request_text)

        # Calculate score
        score = ConfigManager().analysis.scoring.base_score  # Base score

        if high_indicators > 0:
            score += ConfigManager().analysis.scoring.high_boost
        elif medium_indicators > 0:
            score += ConfigManager().analysis.scoring.medium_boost
        elif low_indicators > 0:
            score -= ConfigManager().analysis.scoring.medium_penalty

        score += min(integration_count, 2)

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Dependencies: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Integration: {integration_count}"

        return ComplexityFactor(
            name="dependencies",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["dependencies"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"integration:{integration_count}",
            ],
        )

    def analyze_timeline_factor(self, request) -> ComplexityFactor:
        """Analyze timeline complexity (1-10)."""
        request_text = self._extract_request_text(request)

        # Count timeline indicators
        urgent_indicators = sum(
            1
            for indicator in self.complexity_indicators["timeline"]["urgent"]
            if indicator in request_text
        )
        normal_indicators = sum(
            1
            for indicator in self.complexity_indicators["timeline"]["normal"]
            if indicator in request_text
        )
        flexible_indicators = sum(
            1
            for indicator in self.complexity_indicators["timeline"]["flexible"]
            if indicator in request_text
        )

        # Calculate score (inverted - urgent = higher complexity)
        score = 5  # Base score

        if urgent_indicators > 0:
            score += ConfigManager().analysis.scoring.base_boost
        elif normal_indicators > 0:
            pass  # No score adjustment needed
        elif flexible_indicators > 0:
            score -= ConfigManager().analysis.scoring.medium_penalty

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Timeline: {urgent_indicators} urgent, {normal_indicators} normal, {flexible_indicators} flexible indicators"

        return ComplexityFactor(
            name="timeline",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["timeline"],
            indicators=[
                f"urgent:{urgent_indicators}",
                f"normal:{normal_indicators}",
                f"flexible:{flexible_indicators}",
            ],
        )

    def analyze_risk_factor(self, request) -> ComplexityFactor:
        """Analyze risk complexity (1-10)."""
        request_text = self._extract_request_text(request)

        # Count risk indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["risk"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["risk"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["risk"]["low"]
            if indicator in request_text
        )

        # Risk factors
        risk_terms = ["security", "data", "privacy", "backup", "recovery", "monitoring"]
        risk_count = sum(1 for term in risk_terms if term in request_text)

        # Calculate score
        score = ConfigManager().analysis.scoring.base_score  # Base score

        if high_indicators > 0:
            score += ConfigManager().analysis.scoring.very_high_boost
        elif medium_indicators > 0:
            score += ConfigManager().analysis.scoring.medium_boost
        elif low_indicators > 0:
            score -= ConfigManager().analysis.scoring.small_penalty

        score += min(risk_count, 2)

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Risk: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Risk terms: {risk_count}"

        return ComplexityFactor(
            name="risk",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["risk"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"risk_terms:{risk_count}",
            ],
        )
