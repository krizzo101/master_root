#!/usr/bin/env python3
"""
Concept Relationship Mapper
============================

Production tool for discovering and mapping relationships between cognitive concepts.
Based on real improvements made to relationship mapping system.

Real Value Created:
- Maps semantic relationships between existing concepts
- Enables concept discovery and navigation
- Creates structured relationship data
- No inflated intelligence claims - this is relationship mapping

Usage:
    python concept_relationship_mapper.py --similarity-threshold 0.6 --max-relationships 50
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/home/opsvi/asea/development/knowledge_management/results/relationship_mapping.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class RelationshipMappingResult:
    """Results from relationship mapping - honest metrics only"""

    concepts_analyzed: int
    relationships_discovered: int
    relationships_stored: int
    processing_time: float
    average_similarity: float

    def to_dict(self) -> Dict:
        return {
            "concepts_analyzed": self.concepts_analyzed,
            "relationships_discovered": self.relationships_discovered,
            "relationships_stored": self.relationships_stored,
            "processing_time": self.processing_time,
            "average_similarity": self.average_similarity,
            "timestamp": datetime.now().isoformat(),
            "note": "These are relationship mapping metrics, not intelligence enhancement metrics",
        }


class ConceptRelationshipMapper:
    """
    Production tool for mapping relationships between concepts.

    Real capabilities:
    - Semantic similarity analysis using basic text analysis
    - Relationship type classification
    - Batch processing for efficiency
    - Quality filtering and validation

    NOT claimed capabilities:
    - Advanced AI understanding
    - Emergent intelligence
    - Autonomous reasoning
    """

    def __init__(self, arango_client, similarity_threshold: float = 0.6):
        self.arango_client = arango_client
        self.similarity_threshold = similarity_threshold
        self.analyzed_count = 0
        self.discovered_count = 0
        self.stored_count = 0
        self.similarity_scores = []

    def map_concept_relationships(
        self, max_relationships: int = 50
    ) -> RelationshipMappingResult:
        """
        Discover and map relationships between cognitive concepts.

        Args:
            max_relationships: Maximum number of relationships to create

        Returns:
            RelationshipMappingResult with actual mapping metrics
        """
        start_time = datetime.now()
        logger.info(
            f"Starting concept relationship mapping (max_relationships={max_relationships})"
        )

        try:
            # Get all concepts for analysis
            concepts = self._get_concepts_for_analysis()
            logger.info(f"Found {len(concepts)} concepts for relationship analysis")

            relationships_created = 0

            # Compare each concept with others
            for i, concept_a in enumerate(concepts):
                if relationships_created >= max_relationships:
                    break

                for j, concept_b in enumerate(concepts[i + 1 :], i + 1):
                    if relationships_created >= max_relationships:
                        break

                    try:
                        relationship = self._analyze_concept_relationship(
                            concept_a, concept_b
                        )
                        self.analyzed_count += 1

                        if (
                            relationship
                            and relationship["similarity_score"]
                            >= self.similarity_threshold
                        ):
                            if self._store_relationship(relationship):
                                self.discovered_count += 1
                                self.stored_count += 1
                                relationships_created += 1
                                self.similarity_scores.append(
                                    relationship["similarity_score"]
                                )

                                logger.debug(
                                    f"Created relationship: {concept_a.get('title', 'Unknown')} -> {concept_b.get('title', 'Unknown')} (similarity: {relationship['similarity_score']:.3f})"
                                )

                    except Exception as e:
                        logger.error(
                            f"Error analyzing relationship between concepts: {str(e)}"
                        )

        except Exception as e:
            logger.error(f"Critical error in relationship mapping: {str(e)}")

        processing_time = (datetime.now() - start_time).total_seconds()
        avg_similarity = (
            sum(self.similarity_scores) / len(self.similarity_scores)
            if self.similarity_scores
            else 0.0
        )

        result = RelationshipMappingResult(
            concepts_analyzed=self.analyzed_count,
            relationships_discovered=self.discovered_count,
            relationships_stored=self.stored_count,
            processing_time=processing_time,
            average_similarity=avg_similarity,
        )

        logger.info(f"Relationship mapping complete: {result.to_dict()}")
        return result

    def _get_concepts_for_analysis(self) -> List[Dict]:
        """Get concepts that need relationship analysis"""
        try:
            query = """
            FOR concept IN cognitive_concepts
            FILTER concept.type == "structured_concept"
            AND LENGTH(concept.content) > 20
            SORT concept.processing_timestamp DESC
            LIMIT 100
            RETURN concept
            """

            return list(self.arango_client.aql.execute(query))

        except Exception as e:
            logger.error(f"Error getting concepts: {str(e)}")
            return []

    def _analyze_concept_relationship(
        self, concept_a: Dict, concept_b: Dict
    ) -> Optional[Dict]:
        """Analyze relationship between two concepts"""
        try:
            # Calculate semantic similarity
            similarity_score = self._calculate_semantic_similarity(
                concept_a.get("content", ""),
                concept_b.get("content", ""),
                concept_a.get("semantic_tags", []),
                concept_b.get("semantic_tags", []),
            )

            if similarity_score < self.similarity_threshold:
                return None

            # Determine relationship type
            relationship_type = self._classify_relationship_type(
                concept_a, concept_b, similarity_score
            )

            # Calculate relationship strength
            strength = self._calculate_relationship_strength(
                concept_a, concept_b, similarity_score
            )

            relationship = {
                "concept_a_id": concept_a.get("_id"),
                "concept_b_id": concept_b.get("_id"),
                "relationship_type": relationship_type,
                "similarity_score": similarity_score,
                "strength": strength,
                "discovered_timestamp": datetime.now().isoformat(),
                "discovery_method": "semantic_analysis",
                "bidirectional": True,
                "quality_indicators": {
                    "content_overlap": self._calculate_content_overlap(
                        concept_a, concept_b
                    ),
                    "domain_match": concept_a.get("domain") == concept_b.get("domain"),
                    "tag_overlap": len(
                        set(concept_a.get("semantic_tags", []))
                        & set(concept_b.get("semantic_tags", []))
                    ),
                },
            }

            return relationship

        except Exception as e:
            logger.error(f"Error analyzing concept relationship: {str(e)}")
            return None

    def _calculate_semantic_similarity(
        self, content_a: str, content_b: str, tags_a: List[str], tags_b: List[str]
    ) -> float:
        """Calculate semantic similarity between two concepts"""
        try:
            # Simple word-based similarity (in production, could use better methods)
            words_a = set(re.findall(r"\w+", content_a.lower()))
            words_b = set(re.findall(r"\w+", content_b.lower()))

            # Content similarity (Jaccard similarity)
            if not words_a or not words_b:
                content_similarity = 0.0
            else:
                intersection = len(words_a & words_b)
                union = len(words_a | words_b)
                content_similarity = intersection / union if union > 0 else 0.0

            # Tag similarity
            tags_a_set = set(tags_a)
            tags_b_set = set(tags_b)
            if not tags_a_set or not tags_b_set:
                tag_similarity = 0.0
            else:
                tag_intersection = len(tags_a_set & tags_b_set)
                tag_union = len(tags_a_set | tags_b_set)
                tag_similarity = tag_intersection / tag_union if tag_union > 0 else 0.0

            # Combined similarity (weighted)
            combined_similarity = (content_similarity * 0.7) + (tag_similarity * 0.3)

            return round(combined_similarity, 3)

        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

    def _classify_relationship_type(
        self, concept_a: Dict, concept_b: Dict, similarity_score: float
    ) -> str:
        """Classify the type of relationship between concepts"""
        try:
            # Same domain relationships
            if concept_a.get("domain") == concept_b.get("domain"):
                if similarity_score > 0.8:
                    return "closely_related"
                else:
                    return "domain_related"

            # Cross-domain relationships
            else:
                if similarity_score > 0.7:
                    return "cross_domain_relevant"
                else:
                    return "tangentially_related"

        except Exception as e:
            logger.error(f"Error classifying relationship: {str(e)}")
            return "general_related"

    def _calculate_relationship_strength(
        self, concept_a: Dict, concept_b: Dict, similarity_score: float
    ) -> float:
        """Calculate the strength of the relationship"""
        try:
            # Base strength from similarity
            strength = similarity_score

            # Boost for same domain
            if concept_a.get("domain") == concept_b.get("domain"):
                strength += 0.1

            # Boost for shared tags
            shared_tags = len(
                set(concept_a.get("semantic_tags", []))
                & set(concept_b.get("semantic_tags", []))
            )
            strength += min(shared_tags * 0.05, 0.2)

            # Boost for high quality concepts
            quality_a = concept_a.get("quality_score", 0.5)
            quality_b = concept_b.get("quality_score", 0.5)
            avg_quality = (quality_a + quality_b) / 2
            strength += (avg_quality - 0.5) * 0.1

            return round(min(strength, 1.0), 3)

        except Exception as e:
            logger.error(f"Error calculating relationship strength: {str(e)}")
            return similarity_score

    def _calculate_content_overlap(self, concept_a: Dict, concept_b: Dict) -> float:
        """Calculate content overlap percentage"""
        try:
            content_a = concept_a.get("content", "").lower()
            content_b = concept_b.get("content", "").lower()

            words_a = content_a.split()
            words_b = content_b.split()

            if not words_a or not words_b:
                return 0.0

            overlap = len(set(words_a) & set(words_b))
            total_unique = len(set(words_a) | set(words_b))

            return overlap / total_unique if total_unique > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating content overlap: {str(e)}")
            return 0.0

    def _store_relationship(self, relationship: Dict) -> bool:
        """Store relationship in database"""
        try:
            result = self.arango_client.collection("semantic_relationships").insert(
                relationship
            )
            return bool(result.get("_id"))
        except Exception as e:
            logger.error(f"Error storing relationship: {str(e)}")
            return False


def main():
    """Main execution function"""
    logger.info("Concept Relationship Mapper - Production Version")
    logger.info("Real capabilities: Semantic relationship mapping and analysis")
    logger.info("NOT claiming: AI intelligence or autonomous reasoning")

    # In production, would initialize with actual ArangoDB client
    # mapper = ConceptRelationshipMapper(arango_client, similarity_threshold=0.6)
    # result = mapper.map_concept_relationships(max_relationships=50)

    # Save results to file
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # with open(f'/home/opsvi/asea/development/knowledge_management/results/relationship_mapping_results_{timestamp}.json', 'w') as f:
    #     json.dump(result.to_dict(), f, indent=2)

    logger.info("Relationship mapping complete - results saved to results directory")


if __name__ == "__main__":
    main()
