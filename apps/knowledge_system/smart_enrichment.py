#!/usr/bin/env python3
"""
Smart Enrichment Module - Automatic enrichment for new KB entries
Integrates into the storage pipeline to provide immediate enrichment
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SmartEnrichment:
    """Provides automatic enrichment for new knowledge entries"""

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver

    def calculate_quality_score(self, entry: Dict) -> float:
        """Calculate quality score based on entry characteristics"""
        score = 0.5  # Base score

        # Content length contributes to quality
        content = entry.get("content", "")
        if len(content) > 500:
            score += 0.1
        if len(content) > 1000:
            score += 0.1

        # Summary quality
        summary = entry.get("summary", "")
        if summary and len(summary) > 20:
            score += 0.1

        # Tags contribute to discoverability
        tags = entry.get("tags", [])
        if len(tags) >= 3:
            score += 0.1
        if len(tags) >= 5:
            score += 0.1

        # Knowledge type specificity
        ktype = entry.get("knowledge_type", "")
        if ktype in ["ERROR_SOLUTION", "WORKFLOW", "CODE_PATTERN"]:
            score += 0.1

        # Has embedding
        if entry.get("embedding"):
            score += 0.1

        return min(score, 1.0)

    def calculate_confidence(self, entry: Dict) -> float:
        """Calculate initial confidence based on content patterns"""
        confidence = 0.5  # Default
        content = entry.get("content", "").upper()

        # High confidence indicators
        if "CRITICAL:" in content or "SYSTEM TRUTH:" in content:
            confidence = 0.9
        elif "VERIFIED:" in content or "CONFIRMED:" in content:
            confidence = 0.85
        elif "ERROR_SOLUTION" == entry.get("knowledge_type"):
            confidence = 0.8
        elif "WORKFLOW" == entry.get("knowledge_type"):
            confidence = 0.75
        elif "TEST" in content or "EXPERIMENTAL" in content:
            confidence = 0.4
        elif "DEPRECATED:" in content:
            confidence = 0.2

        # Adjust based on supersedes
        if entry.get("supersedes"):
            confidence += 0.1  # Newer version, slightly more confident

        return min(confidence, 1.0)

    def detect_relationships_for_new_entry(
        self, new_entry: Dict, max_comparisons: int = 100, session=None
    ) -> List[Tuple[str, str, float]]:
        """
        Detect relationships between new entry and existing entries
        Returns: List of (target_id, relationship_type, strength)
        """
        relationships = []

        if not new_entry.get("embedding"):
            return relationships

        new_embedding = np.array(new_entry["embedding"])

        # Use provided session or create new one
        should_close = False
        if not session:
            session = self.driver.session()
            should_close = True

        try:
            # Get similar entries by type first (more relevant)
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.knowledge_type = $ktype
                  AND k.knowledge_id <> $kid
                  AND k.embedding IS NOT NULL
                RETURN k.knowledge_id as id,
                       k.embedding as embedding,
                       k.summary as summary
                ORDER BY k.created_at DESC
                LIMIT $limit
            """,
                {
                    "ktype": new_entry.get("knowledge_type"),
                    "kid": new_entry.get("knowledge_id"),
                    "limit": max_comparisons // 2,
                },
            )

            for record in result:
                if record["embedding"]:
                    other_embedding = np.array(record["embedding"])
                    similarity = cosine_similarity([new_embedding], [other_embedding])[
                        0
                    ][0]

                    # Add relationships based on similarity
                    if 0.3 < similarity < 0.95:
                        relationships.append(
                            (record["id"], "RELATED_TO", float(similarity))
                        )
                    elif similarity >= 0.95:
                        # Very similar - might be duplicate
                        relationships.append(
                            (record["id"], "SIMILAR_TO", float(similarity))
                        )

            # Also check recent entries regardless of type
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.knowledge_id <> $kid
                  AND k.embedding IS NOT NULL
                RETURN k.knowledge_id AS id, k.embedding AS embedding
                ORDER BY k.created_at DESC
                LIMIT $limit
            """,
                {"kid": new_entry.get("knowledge_id"), "limit": max_comparisons // 2},
            )

            for record in result:
                if record["embedding"]:
                    other_embedding = np.array(record["embedding"])
                    similarity = cosine_similarity([new_embedding], [other_embedding])[
                        0
                    ][0]

                    if similarity > 0.4:  # Lower threshold for cross-type
                        # Check if relationship already exists
                        exists = any(r[0] == record["id"] for r in relationships)
                        if not exists:
                            relationships.append(
                                (record["id"], "RELATED_TO", float(similarity))
                            )
        finally:
            if should_close:
                session.close()

        return relationships

    def enrich_on_storage(self, entry: Dict, session=None) -> Dict:
        """
        Enrich a knowledge entry immediately upon storage
        Returns enrichment updates to apply
        """
        enrichments = {
            "enriched_at": datetime.now(timezone.utc),
            "quality_score": self.calculate_quality_score(entry),
            "confidence": self.calculate_confidence(entry),
        }

        # Detect if it's critical
        content = entry.get("content", "").upper()
        if "CRITICAL:" in content or "MANDATORY:" in content:
            enrichments["is_critical"] = True

        # Detect if deprecated
        if "DEPRECATED:" in content or "OBSOLETE:" in content:
            enrichments["deprecated"] = True

        # Detect relationships (async but quick with limits)
        relationships = self.detect_relationships_for_new_entry(entry, session=session)
        enrichments["relationships"] = relationships

        # Add enrichment tags
        enhanced_tags = list(entry.get("tags", []))

        # Add quality tags
        if enrichments["quality_score"] > 0.8:
            enhanced_tags.append("high-quality")
        if enrichments["confidence"] > 0.8:
            enhanced_tags.append("high-confidence")
        if enrichments.get("is_critical"):
            enhanced_tags.append("critical")
        if len(relationships) > 5:
            enhanced_tags.append("well-connected")

        # Add recency tag
        enhanced_tags.append("recent")

        enrichments["tags"] = list(set(enhanced_tags))

        return enrichments


def apply_enrichments_to_storage(
    neo4j_driver, knowledge_id: str, enrichments: Dict, session=None
) -> bool:
    """Apply enrichments to a newly stored entry"""
    # Use provided session or create new one
    should_close = False
    if not session:
        session = neo4j_driver.session()
        should_close = True

    try:
        # Log what we're about to apply
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Applying enrichments to {knowledge_id}: quality={enrichments.get('quality_score')}, confidence={enrichments.get('confidence')}"
        )

        # Update the entry with enrichments
        session.run(
            """
            MATCH (k:Knowledge {knowledge_id: $kid})
            SET k.enriched_at = $enriched_at,
                k.quality_score = $quality_score,
                k.confidence = $confidence,
                k.tags = $tags
        """,
            {
                "kid": knowledge_id,
                "enriched_at": enrichments["enriched_at"],
                "quality_score": enrichments["quality_score"],
                "confidence": enrichments["confidence"],
                "tags": enrichments["tags"],
            },
        )
        logger.info(f"Successfully updated basic enrichments for {knowledge_id}")

        # Add critical/deprecated flags if present
        if enrichments.get("is_critical"):
            session.run(
                """
                MATCH (k:Knowledge {knowledge_id: $kid})
                SET k.is_critical = true
            """,
                {"kid": knowledge_id},
            )

        if enrichments.get("deprecated"):
            session.run(
                """
                MATCH (k:Knowledge {knowledge_id: $kid})
                SET k.deprecated = true
            """,
                {"kid": knowledge_id},
            )

        # Create relationships
        for target_id, rel_type, strength in enrichments.get("relationships", []):
            session.run(
                f"""
                MATCH (k1:Knowledge {{knowledge_id: $source}})
                MATCH (k2:Knowledge {{knowledge_id: $target}})
                MERGE (k1)-[r:{rel_type}]->(k2)
                SET r.strength = $strength,
                    r.detected_at = datetime()
            """,
                {"source": knowledge_id, "target": target_id, "strength": strength},
            )

        return True
    except Exception as e:
        print(f"Failed to apply enrichments: {e}")
        return False
    finally:
        if should_close:
            session.close()
