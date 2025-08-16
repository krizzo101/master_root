"""
Conversation Analyzer - Deep analysis of atomic conversation components

Analyzes parsed conversation components to find patterns, insights, and trends
across individual conversations and entire conversation histories.
"""

from collections import Counter, defaultdict
import statistics
from typing import Any, Dict, List


class ConversationAnalyzer:
    """Analyze atomic conversation components for insights"""

    def __init__(self, storage_client=None):
        self.storage = storage_client

    def analyze_conversation_flow(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze flow patterns within a single conversation"""

        flow_analysis = {
            "total_components": len(components),
            "speaker_distribution": self._analyze_speaker_distribution(components),
            "component_types": self._analyze_component_types(components),
            "conversation_arc": self._analyze_conversation_arc(components),
            "response_patterns": self._analyze_response_patterns(components),
            "complexity_progression": self._analyze_complexity_progression(components),
            "tool_usage_patterns": self._analyze_tool_usage(components),
        }

        return flow_analysis

    def analyze_cross_conversation_patterns(
        self, all_components: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze patterns across multiple conversations"""

        # Group by session
        sessions = defaultdict(list)
        for comp in all_components:
            session_id = comp.get("id", "").split("_comp_")[0]
            sessions[session_id].append(comp)

        cross_analysis = {
            "session_count": len(sessions),
            "total_interactions": len(all_components),
            "recurring_patterns": self._find_recurring_patterns(all_components),
            "frustration_triggers": self._analyze_frustration_triggers(all_components),
            "learning_progression": self._analyze_learning_progression(sessions),
            "topic_evolution": self._analyze_topic_evolution(all_components),
            "efficiency_trends": self._analyze_efficiency_trends(sessions),
        }

        return cross_analysis

    def find_breakthrough_moments(self, components: List[Dict]) -> List[Dict]:
        """Identify breakthrough insights and key realizations"""

        breakthroughs = []

        for comp in components:
            content = comp.get("content", "").lower()

            # Breakthrough indicators
            breakthrough_signals = [
                "breakthrough",
                "key insight",
                "realized",
                "fundamental",
                "this changes everything",
                "aha moment",
                "discovery",
                "important realization",
                "critical insight",
            ]

            if any(signal in content for signal in breakthrough_signals):
                breakthrough = {
                    "component_id": comp.get("id"),
                    "content": comp.get("content"),
                    "timestamp": comp.get("timestamp"),
                    "context_window": comp.get("context_window"),
                    "breakthrough_type": self._classify_breakthrough(content),
                    "impact_score": self._score_breakthrough_impact(comp, components),
                }
                breakthroughs.append(breakthrough)

        return sorted(breakthroughs, key=lambda x: x["impact_score"], reverse=True)

    def analyze_ai_performance_patterns(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze AI performance patterns across conversations"""

        ai_components = [c for c in components if c.get("speaker") == "ai"]

        performance_analysis = {
            "response_quality": self._analyze_response_quality(ai_components),
            "error_patterns": self._analyze_error_patterns(ai_components),
            "improvement_trends": self._analyze_improvement_trends(ai_components),
            "consistency_metrics": self._analyze_consistency(ai_components),
            "capability_growth": self._analyze_capability_growth(ai_components),
        }

        return performance_analysis

    def _analyze_speaker_distribution(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze distribution of speakers in conversation"""
        speakers = [c.get("speaker", "unknown") for c in components]
        counter = Counter(speakers)

        return {
            "counts": dict(counter),
            "percentages": {k: v / len(speakers) for k, v in counter.items()},
            "turn_taking_ratio": counter.get("ai", 0) / max(1, counter.get("user", 1)),
        }

    def _analyze_component_types(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze types of conversation components"""
        types = [c.get("type", "unknown") for c in components]
        counter = Counter(types)

        return {
            "type_distribution": dict(counter),
            "most_common": counter.most_common(5),
            "complexity_indicators": {
                "has_insights": counter.get("insight", 0),
                "has_decisions": counter.get("decision", 0),
                "has_frustrations": counter.get("frustration", 0),
                "has_breakthroughs": counter.get("breakthrough", 0),
            },
        }

    def _analyze_conversation_arc(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze the arc/progression of conversation"""

        # Divide conversation into phases
        total = len(components)
        phase_size = max(1, total // 3)

        phases = {
            "opening": components[:phase_size],
            "middle": components[phase_size : 2 * phase_size],
            "closing": components[2 * phase_size :],
        }

        arc_analysis = {}
        for phase_name, phase_components in phases.items():
            types = [c.get("type") for c in phase_components]
            arc_analysis[phase_name] = {
                "dominant_types": Counter(types).most_common(3),
                "sentiment_trend": self._analyze_phase_sentiment(phase_components),
                "complexity_level": self._analyze_phase_complexity(phase_components),
            }

        return arc_analysis

    def _analyze_response_patterns(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in responses between speakers"""

        patterns = []
        for i in range(len(components) - 1):
            current = components[i]
            next_comp = components[i + 1]

            pattern = {
                "from_type": current.get("type"),
                "to_type": next_comp.get("type"),
                "from_speaker": current.get("speaker"),
                "to_speaker": next_comp.get("speaker"),
            }
            patterns.append(pattern)

        # Count transition patterns
        transitions = Counter(f"{p['from_type']} -> {p['to_type']}" for p in patterns)

        return {
            "common_transitions": transitions.most_common(10),
            "response_chains": self._find_response_chains(patterns),
        }

    def _analyze_complexity_progression(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze how complexity changes throughout conversation"""

        complexity_scores = []
        for comp in components:
            metadata = comp.get("metadata", {})
            word_count = metadata.get("word_count", 0)
            has_code = metadata.get("has_code", False)
            tools_count = len(metadata.get("tools_mentioned", []))

            # Simple complexity score
            score = word_count * 0.1 + (20 if has_code else 0) + tools_count * 5
            complexity_scores.append(score)

        if complexity_scores:
            return {
                "average_complexity": statistics.mean(complexity_scores),
                "complexity_trend": (
                    "increasing"
                    if complexity_scores[-1] > complexity_scores[0]
                    else "decreasing"
                ),
                "peak_complexity": max(complexity_scores),
                "complexity_variance": (
                    statistics.variance(complexity_scores)
                    if len(complexity_scores) > 1
                    else 0
                ),
            }

        return {"average_complexity": 0, "complexity_trend": "stable"}

    def _analyze_tool_usage(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze tool usage patterns"""

        all_tools = []
        for comp in components:
            metadata = comp.get("metadata", {})
            tools = metadata.get("tools_mentioned", [])
            all_tools.extend(tools)

        tool_counter = Counter(all_tools)

        return {
            "total_tool_uses": len(all_tools),
            "unique_tools": len(tool_counter),
            "most_used_tools": tool_counter.most_common(10),
            "tool_diversity": len(tool_counter) / max(1, len(all_tools)),
        }

    def _find_recurring_patterns(self, components: List[Dict]) -> List[Dict]:
        """Find patterns that recur across conversations"""

        # Look for similar content patterns
        content_patterns = defaultdict(list)

        for comp in components:
            content = comp.get("content", "").lower()

            # Extract key phrases (simple approach)
            words = content.split()
            if len(words) >= 3:
                for i in range(len(words) - 2):
                    phrase = " ".join(words[i : i + 3])
                    content_patterns[phrase].append(comp.get("id"))

        # Find patterns that appear multiple times
        recurring = []
        for phrase, occurrences in content_patterns.items():
            if len(occurrences) >= 3:  # Appears 3+ times
                recurring.append(
                    {
                        "pattern": phrase,
                        "frequency": len(occurrences),
                        "component_ids": occurrences,
                    }
                )

        return sorted(recurring, key=lambda x: x["frequency"], reverse=True)

    def _analyze_frustration_triggers(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze what triggers user frustration"""

        frustration_components = [
            c for c in components if c.get("type") == "frustration"
        ]

        triggers = {
            "total_frustrations": len(frustration_components),
            "common_triggers": [],
            "preceding_patterns": [],
        }

        for frustration in frustration_components:
            # Look at what happened before frustration
            window = frustration.get("context_window", 0)
            if window > 0:
                # Find preceding components
                preceding = [
                    c
                    for c in components
                    if c.get("context_window", 0) in range(window - 2, window)
                ]

                for prec in preceding:
                    triggers["preceding_patterns"].append(
                        {
                            "before_frustration": prec.get("type"),
                            "frustration_content": frustration.get("content", "")[:100],
                        }
                    )

        return triggers

    def _analyze_learning_progression(
        self, sessions: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """Analyze learning progression across sessions"""

        session_metrics = []
        for session_id, components in sessions.items():
            session_analysis = self.analyze_conversation_flow(components)

            metrics = {
                "session_id": session_id,
                "complexity": session_analysis.get("complexity_progression", {}).get(
                    "average_complexity", 0
                ),
                "tool_diversity": session_analysis.get("tool_usage_patterns", {}).get(
                    "tool_diversity", 0
                ),
                "insight_count": len(
                    [c for c in components if c.get("type") == "insight"]
                ),
                "error_count": len([c for c in components if c.get("type") == "error"]),
            }
            session_metrics.append(metrics)

        # Sort by session order (assuming chronological IDs)
        session_metrics.sort(key=lambda x: x["session_id"])

        if len(session_metrics) > 1:
            return {
                "sessions_analyzed": len(session_metrics),
                "complexity_trend": self._calculate_trend(
                    [s["complexity"] for s in session_metrics]
                ),
                "tool_mastery_trend": self._calculate_trend(
                    [s["tool_diversity"] for s in session_metrics]
                ),
                "insight_generation_trend": self._calculate_trend(
                    [s["insight_count"] for s in session_metrics]
                ),
                "error_reduction_trend": self._calculate_trend(
                    [s["error_count"] for s in session_metrics], reverse=True
                ),
            }

        return {"sessions_analyzed": len(session_metrics)}

    def _calculate_trend(self, values: List[float], reverse: bool = False) -> str:
        """Calculate if trend is improving, declining, or stable"""
        if len(values) < 2:
            return "insufficient_data"

        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if reverse:
            # For metrics where lower is better (like errors)
            if second_avg < first_avg:
                return "improving"
            elif second_avg > first_avg:
                return "declining"
        else:
            if second_avg > first_avg:
                return "improving"
            elif second_avg < first_avg:
                return "declining"

        return "stable"

    def _classify_breakthrough(self, content: str) -> str:
        """Classify type of breakthrough"""
        if "technical" in content or "implementation" in content:
            return "technical"
        elif "concept" in content or "understanding" in content:
            return "conceptual"
        elif "approach" in content or "method" in content:
            return "methodological"
        else:
            return "general"

    def _score_breakthrough_impact(
        self, breakthrough_comp: Dict, all_components: List[Dict]
    ) -> float:
        """Score the impact of a breakthrough based on subsequent conversation"""

        window = breakthrough_comp.get("context_window", 0)

        # Look at next few components for impact indicators
        subsequent = [
            c
            for c in all_components
            if c.get("context_window", 0) > window
            and c.get("context_window", 0) <= window + 5
        ]

        impact_score = 1.0  # Base score

        for comp in subsequent:
            content = comp.get("content", "").lower()
            comp_type = comp.get("type", "")

            # Positive impact indicators
            if any(
                word in content for word in ["build", "implement", "create", "develop"]
            ):
                impact_score += 0.5

            if comp_type in ["task_start", "code_creation", "decision"]:
                impact_score += 0.3

            # Negative impact indicators
            if comp_type in ["confusion", "error", "frustration"]:
                impact_score -= 0.2

        return max(0.1, impact_score)  # Minimum score of 0.1

    # Additional helper methods for other analysis functions would be implemented here
    def _analyze_phase_sentiment(self, components: List[Dict]) -> str:
        """Analyze sentiment of conversation phase"""
        sentiment_scores = []
        for comp in components:
            metadata = comp.get("metadata", {})
            sentiment = metadata.get("sentiment", "neutral")

            if sentiment == "positive":
                sentiment_scores.append(1)
            elif sentiment == "negative":
                sentiment_scores.append(-1)
            else:
                sentiment_scores.append(0)

        if sentiment_scores:
            avg_sentiment = statistics.mean(sentiment_scores)
            if avg_sentiment > 0.3:
                return "positive"
            elif avg_sentiment < -0.3:
                return "negative"

        return "neutral"

    def _analyze_phase_complexity(self, components: List[Dict]) -> str:
        """Analyze complexity level of conversation phase"""
        complexities = []
        for comp in components:
            metadata = comp.get("metadata", {})
            complexity = metadata.get("complexity", "simple")
            complexities.append(complexity)

        complexity_counter = Counter(complexities)
        most_common = complexity_counter.most_common(1)

        return most_common[0][0] if most_common else "simple"

    def _find_response_chains(self, patterns: List[Dict]) -> List[str]:
        """Find common response chain patterns"""
        # This would implement chain detection logic
        # For now, return placeholder
        return ["user_message -> ai_response -> user_follow_up"]

    def _analyze_topic_evolution(self, components: List[Dict]) -> Dict[str, Any]:
        """Analyze how topics evolve across conversations"""
        # Placeholder implementation
        return {"topic_shifts": 0, "main_topics": []}

    def _analyze_efficiency_trends(
        self, sessions: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """Analyze efficiency trends across sessions"""
        # Placeholder implementation
        return {"average_session_length": 0, "efficiency_trend": "stable"}

    def _analyze_response_quality(self, ai_components: List[Dict]) -> Dict[str, Any]:
        """Analyze quality of AI responses"""
        # Placeholder implementation
        return {"average_quality": 0.5, "quality_trend": "stable"}

    def _analyze_error_patterns(self, ai_components: List[Dict]) -> Dict[str, Any]:
        """Analyze AI error patterns"""
        # Placeholder implementation
        return {"error_rate": 0.1, "common_errors": []}

    def _analyze_improvement_trends(self, ai_components: List[Dict]) -> Dict[str, Any]:
        """Analyze AI improvement trends"""
        # Placeholder implementation
        return {"improvement_rate": 0.05, "trend": "improving"}

    def _analyze_consistency(self, ai_components: List[Dict]) -> Dict[str, Any]:
        """Analyze AI consistency metrics"""
        # Placeholder implementation
        return {"consistency_score": 0.7, "variance": 0.2}

    def _analyze_capability_growth(self, ai_components: List[Dict]) -> Dict[str, Any]:
        """Analyze AI capability growth"""
        # Placeholder implementation
        return {"capabilities_gained": [], "growth_rate": 0.1}
