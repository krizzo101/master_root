#!/usr/bin/env python3
"""
Knowledge Usage Tracking and Decay System
Tracks how knowledge is used and adjusts confidence over time
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class KnowledgeUsageTracker:
    """Track and update knowledge usage patterns"""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_auth: tuple = ("neo4j", "password"),
    ):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)

        # Decay parameters
        self.decay_rate = 0.01  # Daily decay rate
        self.min_confidence = 0.1  # Minimum confidence before deprecation
        self.boost_success = 0.05  # Confidence boost for successful use
        self.penalty_failure = 0.1  # Confidence penalty for failed use

    def track_usage(
        self, knowledge_id: str, success: bool, context: Optional[Dict] = None
    ) -> Dict:
        """Track a usage event for a knowledge item"""

        with self.driver.session() as session:
            # Update usage count and success rate
            cypher = """
                MATCH (k:Knowledge {knowledge_id: $kid})
                SET k.usage_count = COALESCE(k.usage_count, 0) + 1,
                    k.last_used = datetime(),
                    k.success_count = COALESCE(k.success_count, 0) + $success_inc,
                    k.failure_count = COALESCE(k.failure_count, 0) + $failure_inc
                WITH k,
                     COALESCE(k.success_count, 0) + $success_inc as successes,
                     COALESCE(k.failure_count, 0) + $failure_inc as failures
                SET k.success_rate = CASE
                    WHEN successes + failures > 0
                    THEN toFloat(successes) / (successes + failures)
                    ELSE 0.5
                END
                RETURN k.knowledge_id as id,
                       k.usage_count as usage_count,
                       k.success_rate as success_rate,
                       k.confidence_score as confidence
            """

            params = {
                "kid": knowledge_id,
                "success_inc": 1 if success else 0,
                "failure_inc": 0 if success else 1,
            }

            result = session.run(cypher, params)
            record = result.single()

            if record:
                # Adjust confidence based on usage
                new_confidence = self._adjust_confidence(
                    current_confidence=record["confidence"],
                    success=success,
                    success_rate=record["success_rate"],
                )

                # Update confidence
                session.run(
                    """
                    MATCH (k:Knowledge {knowledge_id: $kid})
                    SET k.confidence_score = $new_confidence
                """,
                    kid=knowledge_id,
                    new_confidence=new_confidence,
                )

                # Create usage event node if context provided
                if context:
                    session.run(
                        """
                        MATCH (k:Knowledge {knowledge_id: $kid})
                        CREATE (u:UsageEvent {
                            timestamp: datetime(),
                            success: $success,
                            query: $query_text,
                            strategy: $strategy
                        })
                        CREATE (k)-[:USED_IN]->(u)
                    """,
                        kid=knowledge_id,
                        success=success,
                        query_text=context.get("query", ""),
                        strategy=context.get("strategy", "unknown"),
                    )

                return {
                    "success": True,
                    "knowledge_id": knowledge_id,
                    "usage_count": record["usage_count"],
                    "success_rate": record["success_rate"],
                    "new_confidence": new_confidence,
                }

            return {"success": False, "error": "Knowledge not found"}

    def _adjust_confidence(
        self, current_confidence: float, success: bool, success_rate: float
    ) -> float:
        """Adjust confidence score based on usage"""

        if success:
            # Boost confidence for successful use
            adjustment = self.boost_success * success_rate
            new_confidence = min(1.0, current_confidence + adjustment)
        else:
            # Penalize confidence for failed use
            adjustment = self.penalty_failure * (1 - success_rate)
            new_confidence = max(0.0, current_confidence - adjustment)

        return new_confidence

    def apply_decay(self, days_inactive: int = 30) -> Dict:
        """Apply time-based decay to unused knowledge"""

        cutoff_date = datetime.now() - timedelta(days=days_inactive)

        with self.driver.session() as session:
            # Find inactive knowledge
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                AND (k.last_used IS NULL OR k.last_used < $cutoff)
                AND k.deprecated = false
                RETURN count(k) as count
            """,
                cutoff=cutoff_date,
            )

            inactive_count = result.single()["count"]

            # Apply decay
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                AND (k.last_used IS NULL OR k.last_used < $cutoff)
                AND k.deprecated = false
                WITH k, k.confidence_score * $decay_factor as new_confidence
                SET k.confidence_score = new_confidence
                WITH k
                WHERE new_confidence < $min_confidence
                SET k.deprecated = true,
                    k.deprecated_reason = 'Low confidence due to inactivity'
                RETURN count(k) as deprecated_count
            """,
                cutoff=cutoff_date,
                decay_factor=(1 - self.decay_rate) ** days_inactive,
                min_confidence=self.min_confidence,
            )

            deprecated_count = result.single()["deprecated_count"]

            return {
                "inactive_count": inactive_count,
                "deprecated_count": deprecated_count,
                "decay_rate": self.decay_rate,
                "days_inactive": days_inactive,
            }

    def get_usage_statistics(self) -> Dict:
        """Get overall usage statistics"""

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                RETURN
                    count(k) as total,
                    avg(k.usage_count) as avg_usage,
                    avg(k.confidence_score) as avg_confidence,
                    avg(k.success_rate) as avg_success_rate,
                    sum(CASE WHEN k.deprecated = true THEN 1 ELSE 0 END) as deprecated,
                    sum(CASE WHEN k.usage_count > 0 THEN 1 ELSE 0 END) as used,
                    sum(CASE WHEN k.usage_count = 0 OR k.usage_count IS NULL THEN 1 ELSE 0 END) as unused
            """
            )

            record = result.single()

            # Get most/least used
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true AND k.usage_count > 0
                RETURN k.source as source, k.usage_count as count
                ORDER BY count DESC
                LIMIT 5
            """
            )
            most_used = [(r["source"], r["count"]) for r in result]

            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                AND (k.usage_count = 0 OR k.usage_count IS NULL)
                AND k.deprecated = false
                RETURN k.source as source
                LIMIT 5
            """
            )
            never_used = [r["source"] for r in result]

            return {
                "total_knowledge": record["total"],
                "avg_usage_count": record["avg_usage"] or 0,
                "avg_confidence": record["avg_confidence"] or 0,
                "avg_success_rate": record["avg_success_rate"] or 0,
                "deprecated_count": record["deprecated"],
                "used_count": record["used"],
                "unused_count": record["unused"],
                "most_used": most_used,
                "never_used": never_used,
            }

    def recommend_cleanup(self) -> List[Dict]:
        """Recommend knowledge items for cleanup"""

        recommendations = []

        with self.driver.session() as session:
            # Low confidence items
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                AND k.confidence_score < 0.3
                AND k.deprecated = false
                RETURN k.knowledge_id as id,
                       k.source as source,
                       k.confidence_score as confidence,
                       k.usage_count as usage,
                       'low_confidence' as reason
                LIMIT 10
            """
            )

            for record in result:
                recommendations.append(dict(record))

            # Never used old items
            cutoff = datetime.now() - timedelta(days=60)
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                AND (k.usage_count = 0 OR k.usage_count IS NULL)
                AND k.created_at < $cutoff
                AND k.deprecated = false
                RETURN k.knowledge_id as id,
                       k.source as source,
                       k.confidence_score as confidence,
                       0 as usage,
                       'never_used_old' as reason
                LIMIT 10
            """,
                cutoff=cutoff,
            )

            for record in result:
                recommendations.append(dict(record))

            # Failed frequently
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.direct_ingestion = true
                AND k.success_rate < 0.2
                AND k.usage_count > 5
                AND k.deprecated = false
                RETURN k.knowledge_id as id,
                       k.source as source,
                       k.success_rate as success_rate,
                       k.usage_count as usage,
                       'high_failure_rate' as reason
                LIMIT 10
            """
            )

            for record in result:
                recommendations.append(dict(record))

        return recommendations

    def close(self):
        """Clean up"""
        self.driver.close()


# Example usage
if __name__ == "__main__":
    tracker = KnowledgeUsageTracker()

    print("Knowledge Usage Statistics")
    print("=" * 60)

    # Get current statistics
    stats = tracker.get_usage_statistics()
    print(f"Total knowledge items: {stats['total_knowledge']}")
    print(f"Used: {stats['used_count']}, Unused: {stats['unused_count']}")
    print(f"Deprecated: {stats['deprecated_count']}")
    print(f"Average confidence: {stats['avg_confidence']:.2f}")
    print(f"Average success rate: {stats['avg_success_rate']:.2%}")

    print("\nMost used knowledge:")
    for source, count in stats["most_used"]:
        print(f"  {source[:50]}... ({count} uses)")

    print("\nNever used:")
    for source in stats["never_used"]:
        print(f"  {source[:50]}...")

    # Get cleanup recommendations
    print("\nCleanup Recommendations:")
    recommendations = tracker.recommend_cleanup()
    for rec in recommendations[:5]:
        print(f"  {rec['source'][:40]}... (reason: {rec['reason']})")

    # Apply decay (disabled for demo)
    # decay_result = tracker.apply_decay(days_inactive=30)
    # print(f"\nDecay applied: {decay_result['deprecated_count']} items deprecated")

    tracker.close()
