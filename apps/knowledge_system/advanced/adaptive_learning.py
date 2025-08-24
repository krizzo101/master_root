#!/usr/bin/env python3
"""
Adaptive Learning System - The system that actually LEARNS from usage
Tracks what works, what doesn't, and continuously improves
This is what makes the RAG system intelligent, not just a search engine
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class UsageContext:
    """Context for a knowledge usage event"""

    query: str
    knowledge_ids: List[str]
    strategy_used: str  # vector, graph, hybrid
    user_feedback: Optional[str] = None  # explicit feedback
    task_completed: bool = False
    error_encountered: Optional[str] = None
    time_to_solution: Optional[float] = None  # seconds
    follow_up_queries: List[str] = None


class AdaptiveLearningSystem:
    """
    System that learns from every interaction
    Makes the RAG system smarter with use
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_auth: tuple = ("neo4j", "password"),
    ):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)

        # Learning parameters
        self.success_boost = 0.1  # Boost for successful knowledge
        self.failure_penalty = 0.15  # Penalty for unhelpful knowledge
        self.co_occurrence_strength = 0.05  # Strength of knowledge associations
        self.recency_weight = 0.8  # Weight for recent usage

    def record_usage_session(self, context: UsageContext) -> Dict:
        """
        Record a complete usage session
        This is how the system learns what works
        """

        session_id = f"session_{datetime.now().isoformat()}"

        with self.driver.session() as neo4j_session:
            # Create usage session node
            neo4j_session.run(
                """
                CREATE (s:UsageSession {
                    session_id: $session_id,
                    query_text: $query_text,
                    strategy: $strategy,
                    task_completed: $completed,
                    error: $error,
                    time_to_solution: $time,
                    timestamp: datetime()
                })
            """,
                session_id=session_id,
                query_text=context.query,
                strategy=context.strategy_used,
                completed=context.task_completed,
                error=context.error_encountered,
                time=context.time_to_solution,
            )

            # Link knowledge used in this session
            for kid in context.knowledge_ids:
                neo4j_session.run(
                    """
                    MATCH (s:UsageSession {session_id: $sid})
                    MATCH (k:Knowledge {knowledge_id: $kid})
                    MERGE (s)-[r:USED_KNOWLEDGE {
                        helpful: $helpful,
                        position: $position
                    }]->(k)
                """,
                    sid=session_id,
                    kid=kid,
                    helpful=context.task_completed,
                    position=context.knowledge_ids.index(kid),
                )

            # Update knowledge scores based on outcome
            self._update_knowledge_scores(
                neo4j_session,
                context.knowledge_ids,
                context.task_completed,
                context.error_encountered,
            )

            # Create associations between co-used knowledge
            if context.task_completed and len(context.knowledge_ids) > 1:
                self._create_knowledge_associations(
                    neo4j_session, context.knowledge_ids, context.query
                )

            # Track query patterns
            if context.follow_up_queries:
                self._track_query_patterns(
                    neo4j_session, context.query, context.follow_up_queries
                )

        return {
            "session_id": session_id,
            "knowledge_updated": len(context.knowledge_ids),
            "success": context.task_completed,
        }

    def _update_knowledge_scores(
        self, session, knowledge_ids: List[str], success: bool, error: Optional[str]
    ):
        """Update confidence scores based on usage outcome"""

        for i, kid in enumerate(knowledge_ids):
            # Position-based adjustment (first results matter more)
            position_factor = 1.0 / (1 + i * 0.2)

            if success:
                # Boost successful knowledge
                adjustment = self.success_boost * position_factor
                session.run(
                    """
                    MATCH (k:Knowledge {knowledge_id: $kid})
                    SET k.confidence_score =
                        CASE
                            WHEN k.confidence_score + $adj > 1.0 THEN 1.0
                            ELSE k.confidence_score + $adj
                        END,
                        k.success_count = COALESCE(k.success_count, 0) + 1,
                        k.last_successful_use = datetime()
                """,
                    kid=kid,
                    adj=adjustment,
                )
            else:
                # Penalize unhelpful knowledge
                adjustment = self.failure_penalty * position_factor
                session.run(
                    """
                    MATCH (k:Knowledge {knowledge_id: $kid})
                    SET k.confidence_score =
                        CASE
                            WHEN k.confidence_score - $adj < 0.1 THEN 0.1
                            ELSE k.confidence_score - $adj
                        END,
                        k.failure_count = COALESCE(k.failure_count, 0) + 1,
                        k.last_failure = datetime(),
                        k.failure_context = $error
                """,
                    kid=kid,
                    adj=adjustment,
                    error=error,
                )

    def _create_knowledge_associations(
        self, session, knowledge_ids: List[str], query_context: str
    ):
        """Create associations between knowledge used together successfully"""

        for i, kid1 in enumerate(knowledge_ids):
            for kid2 in knowledge_ids[i + 1 :]:
                session.run(
                    """
                    MATCH (k1:Knowledge {knowledge_id: $kid1})
                    MATCH (k2:Knowledge {knowledge_id: $kid2})
                    MERGE (k1)-[r:USED_WITH]->(k2)
                    ON CREATE SET
                        r.strength = $strength,
                        r.success_count = 1,
                        r.first_used = datetime(),
                        r.contexts = [$context]
                    ON MATCH SET
                        r.strength = r.strength + $strength,
                        r.success_count = r.success_count + 1,
                        r.last_used = datetime(),
                        r.contexts = r.contexts + $context
                """,
                    kid1=kid1,
                    kid2=kid2,
                    strength=self.co_occurrence_strength,
                    context=query_context[:100],
                )  # Keep context snippet

    def _track_query_patterns(self, session, initial_query: str, follow_ups: List[str]):
        """Track query refinement patterns"""

        session.run(
            """
            MERGE (q:QueryPattern {initial: $initial})
            SET q.follow_ups = COALESCE(q.follow_ups, []) + $follow_ups,
                q.occurrence_count = COALESCE(q.occurrence_count, 0) + 1,
                q.last_seen = datetime()
        """,
            initial=initial_query,
            follow_ups=follow_ups,
        )

    def get_adaptive_boost(self, knowledge_id: str) -> float:
        """
        Get the adaptive boost for a knowledge item
        This is added to base scores during retrieval
        """

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge {knowledge_id: $kid})
                RETURN
                    k.confidence_score as confidence,
                    k.success_count as successes,
                    k.failure_count as failures,
                    k.last_successful_use as last_success,
                    k.usage_count as usage
            """,
                kid=knowledge_id,
            )

            record = result.single()
            if not record:
                return 0.0

            # Base boost from confidence
            boost = (record["confidence"] - 0.7) * 0.5  # -0.1 to +0.15

            # Success rate boost
            successes = record["successes"] or 0
            failures = record["failures"] or 0
            if successes + failures > 0:
                success_rate = successes / (successes + failures)
                boost += (success_rate - 0.5) * 0.3  # -0.15 to +0.15

            # Recency boost
            if record["last_success"]:
                days_ago = (datetime.now() - record["last_success"]).days
                recency_factor = np.exp(-days_ago / 30)  # Decay over 30 days
                boost += recency_factor * 0.1  # 0 to +0.1

            # Usage frequency (popular knowledge)
            usage = record["usage"] or 0
            if usage > 10:
                boost += min(0.1, usage / 100)  # 0 to +0.1

            return boost

    def get_associated_knowledge(
        self, knowledge_ids: List[str], limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get knowledge frequently used together
        This helps expand results based on learned associations
        """

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (k1:Knowledge)-[r:USED_WITH]-(k2:Knowledge)
                WHERE k1.knowledge_id IN $kids
                AND NOT k2.knowledge_id IN $kids
                AND r.success_count > 2
                RETURN DISTINCT
                    k2.knowledge_id as associated_id,
                    sum(r.strength) as total_strength
                ORDER BY total_strength DESC
                LIMIT $limit
            """,
                kids=knowledge_ids,
                limit=limit,
            )

            return [
                (record["associated_id"], record["total_strength"]) for record in result
            ]

    def identify_failure_patterns(self) -> List[Dict]:
        """
        Identify patterns in failed knowledge usage
        This helps understand what's not working
        """

        with self.driver.session() as session:
            # Find knowledge with high failure rates
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.failure_count > k.success_count
                AND k.failure_count > 3
                RETURN
                    k.knowledge_id as id,
                    k.source as source,
                    k.failure_count as failures,
                    k.success_count as successes,
                    k.failure_context as context,
                    k.confidence_score as confidence
                ORDER BY failures DESC
                LIMIT 10
            """
            )

            patterns = []
            for record in result:
                patterns.append(
                    {
                        "knowledge_id": record["id"],
                        "source": record["source"],
                        "failure_rate": record["failures"]
                        / (record["failures"] + (record["successes"] or 0)),
                        "failure_context": record["context"],
                        "current_confidence": record["confidence"],
                        "recommendation": "deprecate"
                        if record["confidence"] < 0.3
                        else "review",
                    }
                )

            return patterns

    def suggest_query_refinements(self, query: str) -> List[str]:
        """
        Suggest query refinements based on learned patterns
        """

        with self.driver.session() as session:
            # Find similar initial queries and their successful follow-ups
            result = session.run(
                """
                MATCH (q:QueryPattern)
                WHERE toLower(q.initial) CONTAINS toLower($query)
                OR toLower($query) CONTAINS toLower(q.initial)
                RETURN q.follow_ups as follow_ups
                LIMIT 5
            """,
                query=query,
            )

            suggestions = []
            for record in result:
                if record["follow_ups"]:
                    suggestions.extend(record["follow_ups"])

            # Return unique suggestions
            return list(set(suggestions))[:5]

    def get_learning_statistics(self) -> Dict:
        """Get statistics about the learning system"""

        with self.driver.session() as session:
            stats = {}

            # Usage sessions
            result = session.run(
                """
                MATCH (s:UsageSession)
                RETURN
                    count(s) as total_sessions,
                    sum(CASE WHEN s.task_completed THEN 1 ELSE 0 END) as successful,
                    avg(s.time_to_solution) as avg_time
            """
            )
            record = result.single()
            stats["sessions"] = {
                "total": record["total_sessions"],
                "successful": record["successful"],
                "success_rate": record["successful"] / record["total_sessions"]
                if record["total_sessions"] > 0
                else 0,
                "avg_time_to_solution": record["avg_time"],
            }

            # Knowledge performance
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.usage_count > 0
                RETURN
                    avg(k.confidence_score) as avg_confidence,
                    sum(k.success_count) as total_successes,
                    sum(k.failure_count) as total_failures
            """
            )
            record = result.single()
            stats["knowledge"] = {
                "avg_confidence": record["avg_confidence"],
                "total_successes": record["total_successes"] or 0,
                "total_failures": record["total_failures"] or 0,
            }

            # Associations
            result = session.run(
                """
                MATCH ()-[r:USED_WITH]->()
                RETURN count(r) as associations,
                       avg(r.strength) as avg_strength
            """
            )
            record = result.single()
            stats["associations"] = {
                "total": record["associations"],
                "avg_strength": record["avg_strength"],
            }

            return stats

    def close(self):
        """Clean up"""
        self.driver.close()


# Example showing how this makes the system smarter
if __name__ == "__main__":
    learning = AdaptiveLearningSystem()

    print("ADAPTIVE LEARNING SYSTEM")
    print("=" * 60)

    # Simulate a successful usage session
    context = UsageContext(
        query="How to handle streaming in OpenAI API",
        knowledge_ids=["test_id_1", "test_id_2"],
        strategy_used="hybrid",
        task_completed=True,
        time_to_solution=45.3,
        follow_up_queries=["OpenAI async streaming", "streaming error handling"],
    )

    # Record the session
    result = learning.record_usage_session(context)
    print(f"Recorded session: {result}")

    # Get learning statistics
    stats = learning.get_learning_statistics()
    print(f"\nLearning Statistics:")
    print(
        f"  Sessions: {stats['sessions']['total']} (success rate: {stats['sessions']['success_rate']:.1%})"
    )
    print(
        f"  Knowledge performance: {stats['knowledge']['total_successes']} successes, {stats['knowledge']['total_failures']} failures"
    )
    print(f"  Knowledge associations: {stats['associations']['total']}")

    # Check failure patterns
    failures = learning.identify_failure_patterns()
    if failures:
        print(f"\nFailure Patterns Detected:")
        for pattern in failures[:3]:
            print(
                f"  {pattern['source']}: {pattern['failure_rate']:.1%} failure rate - {pattern['recommendation']}"
            )

    learning.close()
