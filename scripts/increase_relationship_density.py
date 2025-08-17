#!/usr/bin/env python3
"""
Increase Knowledge Base Relationship Density
Analyzes knowledge entries and creates missing relationships to achieve 2-3 edges/node
"""

import logging
import os
from typing import Dict, List, Tuple

import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RelationshipBuilder:
    """Build relationships between knowledge entries based on similarity."""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
    ):
        """Initialize with Neo4j connection."""
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Initialized relationship builder")

    def get_current_statistics(self) -> Dict:
        """Get current relationship statistics."""
        query = """
        MATCH (k:Knowledge)
        WITH count(k) as total_nodes
        MATCH ()-[r:RELATED_TO]->()
        WITH total_nodes, count(r) as total_relationships
        RETURN total_nodes, total_relationships,
               toFloat(total_relationships) / total_nodes as avg_relationships_per_node
        """

        with self.driver.session() as session:
            result = session.run(query)
            stats = result.single()
            if stats:
                return stats.data()
        return {}

    def get_knowledge_with_embeddings(self) -> List[Dict]:
        """Fetch all knowledge entries with embeddings."""
        query = """
        MATCH (k:Knowledge)
        WHERE k.embedding IS NOT NULL
        RETURN k.knowledge_id as id,
               k.knowledge_type as type,
               k.content as content,
               k.embedding as embedding
        """

        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_existing_relationships(self) -> List[Tuple[str, str]]:
        """Get all existing relationships."""
        query = """
        MATCH (k1:Knowledge)-[:RELATED_TO]-(k2:Knowledge)
        WHERE k1.knowledge_id < k2.knowledge_id
        RETURN k1.knowledge_id as id1, k2.knowledge_id as id2
        """

        with self.driver.session() as session:
            result = session.run(query)
            return [(r["id1"], r["id2"]) for r in result]

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        # Handle dimension mismatches by truncating to min size
        min_dim = min(len(embedding1), len(embedding2))
        vec1 = np.array(embedding1[:min_dim])
        vec2 = np.array(embedding2[:min_dim])

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))

    def find_potential_relationships(
        self,
        entries: List[Dict],
        existing: List[Tuple[str, str]],
        threshold: float = 0.6,
    ) -> List[Dict]:
        """Find potential relationships based on similarity."""
        potential = []
        existing_set = set(existing)

        for i, entry1 in enumerate(entries):
            for j, entry2 in enumerate(entries[i + 1 :], i + 1):
                id1, id2 = entry1["id"], entry2["id"]

                # Skip if relationship already exists
                if (id1, id2) in existing_set or (id2, id1) in existing_set:
                    continue

                # Calculate similarity
                similarity = self.calculate_similarity(
                    entry1["embedding"], entry2["embedding"]
                )

                # Consider as potential if above threshold
                if similarity >= threshold:
                    # Boost score for same type
                    if entry1["type"] == entry2["type"]:
                        similarity *= 1.2

                    potential.append(
                        {
                            "id1": id1,
                            "id2": id2,
                            "similarity": similarity,
                            "type_match": entry1["type"] == entry2["type"],
                            "types": (entry1["type"], entry2["type"]),
                        }
                    )

        # Sort by similarity
        potential.sort(key=lambda x: x["similarity"], reverse=True)
        return potential

    def create_relationships(self, relationships: List[Dict]) -> int:
        """Create relationships in Neo4j."""
        query = """
        MATCH (k1:Knowledge {knowledge_id: $id1})
        MATCH (k2:Knowledge {knowledge_id: $id2})
        CREATE (k1)-[r:RELATED_TO {
            similarity: $similarity,
            created_at: datetime(),
            created_by: 'relationship_builder'
        }]->(k2)
        RETURN r
        """

        created_count = 0
        with self.driver.session() as session:
            for rel in relationships:
                try:
                    result = session.run(
                        query,
                        id1=rel["id1"],
                        id2=rel["id2"],
                        similarity=rel["similarity"],
                    )
                    if result.single():
                        created_count += 1
                        logger.debug(
                            f"Created relationship: {rel['id1']} <-> {rel['id2']} "
                            f"(similarity: {rel['similarity']:.3f})"
                        )
                except Exception as e:
                    logger.error(f"Failed to create relationship: {e}")

        return created_count

    def run(self, target_density: float = 2.5, similarity_threshold: float = 0.6):
        """Run the relationship building process."""
        logger.info("Starting relationship density improvement...")

        # Get current statistics
        stats = self.get_current_statistics()
        logger.info("Current statistics:")
        logger.info(f"  Total nodes: {stats['total_nodes']}")
        logger.info(f"  Total relationships: {stats['total_relationships']}")
        logger.info(f"  Avg per node: {stats['avg_relationships_per_node']:.2f}")

        # Calculate target
        target_relationships = int(stats["total_nodes"] * target_density)
        needed = target_relationships - stats["total_relationships"]

        if needed <= 0:
            logger.info(f"Already at or above target density ({target_density})")
            return

        logger.info(f"Need to create {needed} relationships to reach target density")

        # Get knowledge entries with embeddings
        entries = self.get_knowledge_with_embeddings()
        logger.info(f"Found {len(entries)} entries with embeddings")

        # Get existing relationships
        existing = self.get_existing_relationships()
        logger.info(f"Found {len(existing)} existing relationships")

        # Find potential relationships
        potential = self.find_potential_relationships(
            entries, existing, similarity_threshold
        )
        logger.info(f"Found {len(potential)} potential relationships")

        # Select top relationships to create
        to_create = potential[:needed]
        logger.info(f"Creating {len(to_create)} new relationships...")

        # Create relationships
        created = self.create_relationships(to_create)
        logger.info(f"Successfully created {created} relationships")

        # Final statistics
        final_stats = self.get_current_statistics()
        logger.info("\nFinal statistics:")
        logger.info(f"  Total nodes: {final_stats['total_nodes']}")
        logger.info(f"  Total relationships: {final_stats['total_relationships']}")
        logger.info(f"  Avg per node: {final_stats['avg_relationships_per_node']:.2f}")

        # Show improvement
        improvement = (
            final_stats["avg_relationships_per_node"]
            - stats["avg_relationships_per_node"]
        )
        logger.info(f"\nImprovement: +{improvement:.2f} relationships per node")

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()


def main():
    """Main execution function."""
    # Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    TARGET_DENSITY = float(os.getenv("TARGET_DENSITY", "2.5"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))

    # Create builder
    builder = RelationshipBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Run relationship building
        builder.run(
            target_density=TARGET_DENSITY, similarity_threshold=SIMILARITY_THRESHOLD
        )
    finally:
        # Clean up
        builder.close()


if __name__ == "__main__":
    main()
