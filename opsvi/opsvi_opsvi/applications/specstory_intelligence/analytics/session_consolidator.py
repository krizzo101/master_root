"""
Session Consolidator - Merge multiple AI conversations into master knowledge
"""

import json
from typing import Dict, List

from .context_compression_engine import ContextCompressionEngine, ContextPackage


class SessionConsolidator:
    """Consolidate multiple AI sessions into unified understanding"""

    def __init__(self):
        self.compressor = ContextCompressionEngine()

    def consolidate_sessions(self, session_files: List[str]) -> ContextPackage:
        """Merge multiple session logs into master context"""

        all_components = []
        all_insights = []
        all_decisions = []
        frustration_patterns = []
        performance_variance = []

        for session_file in session_files:
            session_data = self._load_session(session_file)

            # Extract components
            all_components.extend(session_data.get("components", []))

            # Analyze frustration points
            frustrations = self._detect_frustration_patterns(session_data)
            frustration_patterns.extend(frustrations)

            # Analyze AI performance variance
            performance = self._analyze_ai_performance(session_data)
            performance_variance.append(performance)

        # Create consolidated package
        master_package = self.compressor.compress_conversation(all_components)

        # Add meta-analysis
        master_package.frustration_analysis = self._analyze_frustration_trends(
            frustration_patterns
        )
        master_package.performance_analysis = self._analyze_performance_variance(
            performance_variance
        )
        master_package.session_count = len(session_files)

        return master_package

    def _detect_frustration_patterns(self, session_data: Dict) -> List[Dict]:
        """Find user frustration indicators"""
        patterns = []

        for component in session_data.get("components", []):
            content = component.get("content", "").lower()

            # Frustration indicators
            if any(
                phrase in content
                for phrase in [
                    "this isn't working",
                    "confused",
                    "why did you",
                    "is this even the same model",
                    "struggling",
                ]
            ):
                patterns.append(
                    {
                        "type": "frustration",
                        "content": component.get("content", ""),
                        "timestamp": component.get("timestamp", ""),
                        "context": self._extract_preceding_context(
                            session_data, component
                        ),
                    }
                )

        return patterns

    def _analyze_ai_performance(self, session_data: Dict) -> Dict:
        """Analyze AI performance in this session"""

        startup_quality = self._assess_startup_performance(session_data)
        task_completion = self._assess_task_completion(session_data)
        error_rate = self._calculate_error_rate(session_data)

        return {
            "startup_quality": startup_quality,
            "task_completion": task_completion,
            "error_rate": error_rate,
            "overall_rating": (startup_quality + task_completion + (1 - error_rate))
            / 3,
        }

    def _load_session(self, filepath: str) -> Dict:
        """Load session data from file"""
        try:
            with open(filepath) as f:
                return json.load(f)
        except:
            return {"components": []}

    def _extract_preceding_context(
        self, session_data: Dict, target_component: Dict
    ) -> str:
        """Get context leading up to frustration"""
        # Simple implementation - get previous 2 components
        components = session_data.get("components", [])
        try:
            idx = components.index(target_component)
            preceding = components[max(0, idx - 2) : idx]
            return " | ".join([c.get("content", "")[:50] for c in preceding])
        except:
            return ""

    def _assess_startup_performance(self, session_data: Dict) -> float:
        """Rate startup sequence performance 0-1"""
        # Look for startup indicators
        startup_components = [
            c
            for c in session_data.get("components", [])
            if "startup" in c.get("content", "").lower()
        ]

        if not startup_components:
            return 0.5  # No startup info

        # Count errors/confusion in startup
        error_count = sum(
            1
            for c in startup_components
            if any(
                word in c.get("content", "").lower()
                for word in ["error", "confused", "mistake"]
            )
        )

        return max(0, 1 - (error_count / len(startup_components)))

    def _assess_task_completion(self, session_data: Dict) -> float:
        """Rate task completion quality 0-1"""
        components = session_data.get("components", [])

        completion_indicators = sum(
            1
            for c in components
            if any(
                word in c.get("content", "").lower()
                for word in ["completed", "finished", "done", "success"]
            )
        )

        error_indicators = sum(
            1
            for c in components
            if any(
                word in c.get("content", "").lower()
                for word in ["failed", "error", "wrong", "broken"]
            )
        )

        if completion_indicators + error_indicators == 0:
            return 0.5

        return completion_indicators / (completion_indicators + error_indicators)

    def _calculate_error_rate(self, session_data: Dict) -> float:
        """Calculate error rate for session"""
        components = session_data.get("components", [])

        if not components:
            return 0

        error_count = sum(
            1
            for c in components
            if any(
                word in c.get("content", "").lower()
                for word in ["error", "failed", "wrong", "broken"]
            )
        )

        return error_count / len(components)

    def _analyze_frustration_trends(self, patterns: List[Dict]) -> Dict:
        """Analyze patterns in user frustration"""
        if not patterns:
            return {"total_incidents": 0, "common_triggers": []}

        # Group by common triggers
        triggers = {}
        for pattern in patterns:
            content = pattern["content"].lower()

            if "startup" in content:
                triggers["startup_issues"] = triggers.get("startup_issues", 0) + 1
            elif "confused" in content:
                triggers["ai_confusion"] = triggers.get("ai_confusion", 0) + 1
            elif "error" in content:
                triggers["errors"] = triggers.get("errors", 0) + 1
            else:
                triggers["other"] = triggers.get("other", 0) + 1

        return {
            "total_incidents": len(patterns),
            "common_triggers": sorted(
                triggers.items(), key=lambda x: x[1], reverse=True
            ),
        }

    def _analyze_performance_variance(self, performance_data: List[Dict]) -> Dict:
        """Analyze variance in AI performance across sessions"""
        if not performance_data:
            return {"variance": 0, "average_performance": 0.5}

        ratings = [p["overall_rating"] for p in performance_data]
        avg_rating = sum(ratings) / len(ratings)
        variance = sum((r - avg_rating) ** 2 for r in ratings) / len(ratings)

        return {
            "variance": variance,
            "average_performance": avg_rating,
            "session_count": len(performance_data),
            "high_performance_sessions": sum(1 for r in ratings if r > 0.8),
            "low_performance_sessions": sum(1 for r in ratings if r < 0.4),
        }
