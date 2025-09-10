#!/usr/bin/env python3
"""
Predictive Pre-fetching System - Anticipating knowledge needs before they arise
This system predicts what I'll need based on patterns and pre-loads it
It's how I become faster by knowing what's coming
"""

import hashlib
import json
import pickle
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from neo4j import GraphDatabase

sys.path.insert(0, "/home/opsvi/master_root")
from apps.knowledge_system.embedding_service import get_embedding_service
from apps.knowledge_system.unified_intelligent_search import UnifiedIntelligentSearch


class QueryPattern:
    """A pattern in query sequences"""

    def __init__(self, sequence: List[str]):
        self.sequence = sequence
        self.frequency = 1
        self.last_seen = datetime.now()
        self.predictions = []  # What typically follows this pattern
        self.confidence = 0.5

    def add_occurrence(self, next_query: Optional[str] = None):
        """Record another occurrence of this pattern"""
        self.frequency += 1
        self.last_seen = datetime.now()
        if next_query:
            self.predictions.append(next_query)
        self.confidence = min(1.0, 0.5 + (self.frequency * 0.05))

    def get_likely_next(self) -> List[Tuple[str, float]]:
        """Get likely next queries with probabilities"""
        if not self.predictions:
            return []

        # Count frequencies
        pred_counts = defaultdict(int)
        for pred in self.predictions:
            pred_counts[pred] += 1

        # Calculate probabilities
        total = sum(pred_counts.values())
        predictions = [
            (query, count / total * self.confidence)
            for query, count in pred_counts.items()
        ]

        return sorted(predictions, key=lambda x: x[1], reverse=True)[:5]


class PredictivePrefetcher:
    """
    System that predicts and pre-fetches knowledge I'll likely need
    Makes me faster by having answers ready before questions
    """

    def __init__(self, cache_size: int = 100):
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.search_system = UnifiedIntelligentSearch()
        self.embedding_service = get_embedding_service()

        # Prediction state
        self.query_history = deque(maxlen=100)  # Recent queries
        self.query_patterns = {}  # Detected patterns
        self.prefetch_cache = {}  # Pre-fetched results
        self.cache_size = cache_size
        self.prediction_stats = {
            "predictions_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "accuracy": 0.0,
        }

        # Pattern detection parameters
        self.min_pattern_length = 2
        self.max_pattern_length = 5
        self.pattern_threshold = 2  # Min occurrences to consider pattern

    def record_query(self, query: str) -> None:
        """Record a query for pattern analysis"""

        self.query_history.append(
            {
                "query": query,
                "timestamp": datetime.now(),
                "embedding": None,  # Will compute if needed
            }
        )

        # Detect patterns in recent history
        self._detect_patterns()

        # Make predictions based on patterns
        predictions = self._predict_next_queries(query)

        # Pre-fetch predicted queries
        if predictions:
            self._prefetch_queries(predictions)

    def _detect_patterns(self) -> None:
        """Detect patterns in query history"""

        if len(self.query_history) < self.min_pattern_length:
            return

        # Extract just the query texts
        recent_queries = [q["query"] for q in self.query_history]

        # Look for patterns of different lengths
        for pattern_len in range(
            self.min_pattern_length,
            min(self.max_pattern_length + 1, len(recent_queries)),
        ):
            # Check recent sequences
            for i in range(len(recent_queries) - pattern_len + 1):
                sequence = recent_queries[i : i + pattern_len]
                pattern_key = "→".join(sequence)

                # Check if this pattern exists in history
                if pattern_key in self.query_patterns:
                    # Update existing pattern
                    next_query = (
                        recent_queries[i + pattern_len]
                        if i + pattern_len < len(recent_queries)
                        else None
                    )
                    self.query_patterns[pattern_key].add_occurrence(next_query)
                else:
                    # Check if pattern appears elsewhere in history
                    pattern_count = self._count_pattern_occurrences(
                        sequence, recent_queries
                    )
                    if pattern_count >= self.pattern_threshold:
                        # New recurring pattern found
                        self.query_patterns[pattern_key] = QueryPattern(sequence)
                        print(f"New pattern detected: {pattern_key[:50]}...")

    def _count_pattern_occurrences(self, pattern: List[str], history: List[str]) -> int:
        """Count how many times a pattern appears in history"""

        count = 0
        pattern_len = len(pattern)

        for i in range(len(history) - pattern_len + 1):
            if history[i : i + pattern_len] == pattern:
                count += 1

        return count

    def _predict_next_queries(self, current_query: str) -> List[Tuple[str, float]]:
        """Predict likely next queries based on patterns"""

        predictions = []

        # Check if current query is part of any pattern
        for pattern_key, pattern in self.query_patterns.items():
            if current_query in pattern.sequence:
                # This query is part of a known pattern
                likely_next = pattern.get_likely_next()
                predictions.extend(likely_next)

        # Also predict based on semantic similarity
        semantic_predictions = self._predict_semantic_continuations(current_query)
        predictions.extend(semantic_predictions)

        # Combine and deduplicate predictions
        combined = {}
        for query, prob in predictions:
            if query in combined:
                combined[query] = max(combined[query], prob)
            else:
                combined[query] = prob

        # Sort by probability
        sorted_predictions = sorted(combined.items(), key=lambda x: x[1], reverse=True)

        self.prediction_stats["predictions_made"] += len(sorted_predictions)

        return sorted_predictions[:10]  # Top 10 predictions

    def _predict_semantic_continuations(self, query: str) -> List[Tuple[str, float]]:
        """Predict semantically related follow-up queries"""

        predictions = []

        # Analyze query for concepts
        query_lower = query.lower()

        # Common follow-up patterns
        if "error" in query_lower:
            predictions.extend(
                [
                    ("how to fix this error", 0.7),
                    ("error handling best practices", 0.6),
                    ("common causes of this error", 0.5),
                ]
            )

        if "implement" in query_lower:
            predictions.extend(
                [
                    ("implementation example", 0.6),
                    ("best practices for implementation", 0.5),
                    ("testing the implementation", 0.4),
                ]
            )

        if "async" in query_lower:
            predictions.extend(
                [
                    ("async error handling", 0.6),
                    ("async await patterns", 0.5),
                    ("asyncio examples", 0.4),
                ]
            )

        if "test" in query_lower:
            predictions.extend(
                [
                    ("unit test examples", 0.5),
                    ("test coverage", 0.4),
                    ("mocking in tests", 0.4),
                ]
            )

        # Query refinements
        if len(query.split()) < 5:  # Short query might be refined
            predictions.append((f"{query} example", 0.4))
            predictions.append((f"{query} best practices", 0.3))
            predictions.append((f"how to {query}", 0.3))

        return predictions

    def _prefetch_queries(self, predictions: List[Tuple[str, float]]) -> None:
        """Pre-fetch results for predicted queries"""

        # Only prefetch high-confidence predictions
        to_prefetch = [q for q, prob in predictions if prob > 0.4][:5]

        for query in to_prefetch:
            if query not in self.prefetch_cache:
                # Perform search and cache results
                try:
                    results = self.search_system.search(
                        query, limit=5, track_usage=False
                    )

                    self.prefetch_cache[query] = {
                        "results": results,
                        "cached_at": datetime.now(),
                        "hit_count": 0,
                    }

                    # Manage cache size
                    if len(self.prefetch_cache) > self.cache_size:
                        self._evict_cache()

                except Exception as e:
                    print(f"Prefetch failed for '{query}': {e}")

    def _evict_cache(self) -> None:
        """Evict least useful cache entries"""

        # Calculate usefulness score for each entry
        scores = []
        for query, data in self.prefetch_cache.items():
            age = (datetime.now() - data["cached_at"]).total_seconds() / 3600  # Hours
            usefulness = data["hit_count"] / (1 + age)  # Hits per hour
            scores.append((query, usefulness))

        # Sort by usefulness
        scores.sort(key=lambda x: x[1])

        # Evict least useful 20%
        evict_count = len(scores) // 5
        for query, _ in scores[:evict_count]:
            del self.prefetch_cache[query]

    def get_cached_results(self, query: str) -> Optional[List]:
        """Get pre-fetched results if available"""

        if query in self.prefetch_cache:
            # Cache hit!
            self.prefetch_cache[query]["hit_count"] += 1
            self.prediction_stats["cache_hits"] += 1

            # Check if cache is stale
            age = (
                datetime.now() - self.prefetch_cache[query]["cached_at"]
            ).total_seconds()
            if age > 3600:  # 1 hour
                # Refresh cache
                del self.prefetch_cache[query]
                self.prediction_stats["cache_misses"] += 1
                return None

            return self.prefetch_cache[query]["results"]
        else:
            self.prediction_stats["cache_misses"] += 1
            return None

    def analyze_query_trajectory(self, recent_n: int = 10) -> Dict:
        """Analyze the trajectory of recent queries to predict direction"""

        if len(self.query_history) < 2:
            return {"trajectory": "insufficient_data"}

        recent = list(self.query_history)[-recent_n:]

        # Analyze semantic drift
        embeddings = []
        for q in recent:
            if q["embedding"] is None:
                q["embedding"] = self.embedding_service.generate_embedding(q["query"])
            embeddings.append(q["embedding"])

        # Calculate semantic distances between consecutive queries
        distances = []
        for i in range(1, len(embeddings)):
            # Cosine distance
            dist = 1 - np.dot(embeddings[i - 1], embeddings[i])
            distances.append(dist)

        # Analyze trajectory
        avg_distance = np.mean(distances) if distances else 0
        distance_trend = (
            np.polyfit(range(len(distances)), distances, 1)[0]
            if len(distances) > 1
            else 0
        )

        # Interpret trajectory
        if avg_distance < 0.2:
            trajectory = "focused"  # Staying on same topic
        elif avg_distance < 0.5:
            trajectory = "exploring"  # Related but expanding
        else:
            trajectory = "shifting"  # Changing topics

        if distance_trend > 0.1:
            direction = "diverging"  # Moving away from original topic
        elif distance_trend < -0.1:
            direction = "converging"  # Focusing in
        else:
            direction = "stable"

        return {
            "trajectory": trajectory,
            "direction": direction,
            "avg_semantic_distance": avg_distance,
            "distance_trend": distance_trend,
            "recent_queries": [q["query"] for q in recent[-5:]],
            "likely_intent": self._infer_intent(trajectory, direction, recent),
        }

    def _infer_intent(
        self, trajectory: str, direction: str, recent_queries: List
    ) -> str:
        """Infer the likely intent from query trajectory"""

        if trajectory == "focused" and direction == "converging":
            return "debugging_specific_issue"
        elif trajectory == "exploring" and direction == "diverging":
            return "learning_new_concept"
        elif trajectory == "shifting":
            return "comparing_alternatives"
        elif trajectory == "focused" and direction == "stable":
            return "implementing_solution"
        else:
            return "general_exploration"

    def generate_predictive_report(self) -> str:
        """Generate a report on prediction effectiveness"""

        # Calculate accuracy
        if (
            self.prediction_stats["cache_hits"] + self.prediction_stats["cache_misses"]
            > 0
        ):
            self.prediction_stats["accuracy"] = self.prediction_stats["cache_hits"] / (
                self.prediction_stats["cache_hits"]
                + self.prediction_stats["cache_misses"]
            )

        # Analyze patterns
        active_patterns = len(
            [
                p
                for p in self.query_patterns.values()
                if (datetime.now() - p.last_seen).days < 7
            ]
        )

        # Get trajectory
        trajectory = self.analyze_query_trajectory()

        report = f"""
PREDICTIVE PRE-FETCHING REPORT
Generated: {datetime.now().isoformat()}
{'=' * 60}

PREDICTION STATISTICS:
- Predictions Made: {self.prediction_stats['predictions_made']}
- Cache Hits: {self.prediction_stats['cache_hits']}
- Cache Misses: {self.prediction_stats['cache_misses']}
- Hit Rate: {self.prediction_stats['accuracy']:.1%}
- Cache Size: {len(self.prefetch_cache)}/{self.cache_size}

PATTERN ANALYSIS:
- Total Patterns Detected: {len(self.query_patterns)}
- Active Patterns (last 7d): {active_patterns}
- Query History Size: {len(self.query_history)}

TOP PATTERNS:
"""

        # List top patterns
        sorted_patterns = sorted(
            self.query_patterns.items(),
            key=lambda x: x[1].frequency * x[1].confidence,
            reverse=True,
        )[:5]

        for pattern_key, pattern in sorted_patterns:
            report += f"- {pattern_key[:50]}... (freq: {pattern.frequency}, conf: {pattern.confidence:.2f})\n"
            likely = pattern.get_likely_next()
            if likely:
                report += f"  Predicts: {likely[0][0][:40]}... ({likely[0][1]:.2f})\n"

        report += f"""

QUERY TRAJECTORY:
- Current Trajectory: {trajectory['trajectory']}
- Direction: {trajectory['direction']}
- Likely Intent: {trajectory['likely_intent']}
- Avg Semantic Distance: {trajectory.get('avg_semantic_distance', 0):.3f}

CACHE CONTENTS:
"""

        # Show most hit cache entries
        cache_by_hits = sorted(
            self.prefetch_cache.items(), key=lambda x: x[1]["hit_count"], reverse=True
        )[:5]

        for query, data in cache_by_hits:
            age = (datetime.now() - data["cached_at"]).total_seconds() / 60
            report += (
                f"- {query[:50]}... (hits: {data['hit_count']}, age: {age:.0f}m)\n"
            )

        report += """

RECOMMENDATIONS:
"""

        if self.prediction_stats["accuracy"] < 0.3:
            report += "- Low hit rate: Pattern detection needs more training data\n"
        if len(self.query_patterns) < 5:
            report += "- Few patterns detected: System needs more usage to learn\n"
        if trajectory["trajectory"] == "shifting":
            report += "- Trajectory shifting: Consider broader prefetch strategy\n"
        if len(self.prefetch_cache) >= self.cache_size * 0.9:
            report += "- Cache near capacity: Consider increasing cache size\n"

        return report

    def save_state(
        self,
        filepath: str = "/home/opsvi/master_root/apps/knowledge_system/prefetch_state.pkl",
    ):
        """Save predictor state for persistence"""

        state = {
            "query_history": list(self.query_history),
            "query_patterns": self.query_patterns,
            "prefetch_cache": self.prefetch_cache,
            "prediction_stats": self.prediction_stats,
        }

        with open(filepath, "wb") as f:
            pickle.dump(state, f)

        print(f"Saved prefetch state to {filepath}")

    def load_state(
        self,
        filepath: str = "/home/opsvi/master_root/apps/knowledge_system/prefetch_state.pkl",
    ):
        """Load previous predictor state"""

        try:
            with open(filepath, "rb") as f:
                state = pickle.load(f)

            self.query_history = deque(state["query_history"], maxlen=100)
            self.query_patterns = state["query_patterns"]
            self.prefetch_cache = state["prefetch_cache"]
            self.prediction_stats = state["prediction_stats"]

            print(f"Loaded prefetch state from {filepath}")
            return True
        except FileNotFoundError:
            print("No previous state found")
            return False

    def close(self):
        """Clean up resources"""
        self.save_state()  # Save before closing
        self.neo4j_driver.close()
        self.search_system.close()


# Self-testing system
if __name__ == "__main__":
    print("PREDICTIVE PRE-FETCHING SYSTEM")
    print("=" * 60)

    prefetcher = PredictivePrefetcher()

    # Load previous state if exists
    prefetcher.load_state()

    # Simulate query sequence to test prediction
    test_queries = [
        "How to handle async errors",
        "async error handling patterns",
        "asyncio exception handling",
        "How to handle async errors",  # Repeat to create pattern
        "async error handling patterns",
        "Best practices for error handling",
        "Python error handling",
        "exception handling in async code",
    ]

    print("\nSimulating query sequence...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: {query}")

        # Check cache first
        cached = prefetcher.get_cached_results(query)
        if cached:
            print(f"   ✓ CACHE HIT! Retrieved {len(cached)} pre-fetched results")
        else:
            print(f"   ✗ Cache miss - would need to search")

        # Record for pattern learning
        prefetcher.record_query(query)

        # Show predictions
        predictions = prefetcher._predict_next_queries(query)
        if predictions:
            print(f"   Predictions for next query:")
            for pred_query, prob in predictions[:3]:
                print(f"     - {pred_query[:50]}... ({prob:.2f})")

    # Generate report
    print("\n" + "=" * 60)
    print(prefetcher.generate_predictive_report())

    # Save state
    prefetcher.save_state()
    prefetcher.close()
