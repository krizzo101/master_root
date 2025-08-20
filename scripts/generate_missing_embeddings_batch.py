#!/usr/bin/env python3
"""
Batch Embedding Generation for Knowledge Base
Generates embeddings for all knowledge entries that are missing them.
"""

import logging
import os
from typing import Dict, List

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for knowledge entries missing them."""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
    ):
        """Initialize with Neo4j connection and embedding model."""
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Initialized with model: all-MiniLM-L6-v2 (384 dimensions)")

    def get_entries_without_embeddings(self) -> List[Dict]:
        """Fetch all knowledge entries that don't have embeddings."""
        query = """
        MATCH (k:Knowledge)
        WHERE k.embedding IS NULL
        RETURN k.knowledge_id as id,
               k.knowledge_type as type,
               k.content as content,
               k.description as description,
               k.context as context
        """

        with self.driver.session() as session:
            result = session.run(query)
            entries = [record.data() for record in result]
            logger.info(f"Found {len(entries)} entries without embeddings")
            return entries

    def generate_embedding_text(self, entry: Dict) -> str:
        """Create text to embed from knowledge entry."""
        parts = []

        # Add content
        if entry.get("content"):
            parts.append(entry["content"])

        # Add description
        if entry.get("description"):
            parts.append(entry["description"])

        # Add context if it's not too large
        if entry.get("context") and len(str(entry["context"])) < 1000:
            parts.append(str(entry["context"]))

        # Add type as context
        if entry.get("type"):
            parts.append(f"Type: {entry['type']}")

        return " ".join(parts)

    def generate_embeddings(self, entries: List[Dict]) -> Dict[str, List[float]]:
        """Generate embeddings for multiple entries."""
        embeddings = {}

        # Prepare texts
        texts = []
        ids = []

        for entry in entries:
            text = self.generate_embedding_text(entry)
            texts.append(text)
            ids.append(entry["id"])

        # Generate embeddings in batch
        if texts:
            logger.info(f"Generating embeddings for {len(texts)} entries...")
            embedding_vectors = self.model.encode(texts, show_progress_bar=True)

            for id, embedding in zip(ids, embedding_vectors):
                embeddings[id] = embedding.tolist()

        return embeddings

    def store_embeddings(self, embeddings: Dict[str, List[float]]) -> int:
        """Store embeddings in Neo4j."""
        query = """
        MATCH (k:Knowledge {knowledge_id: $id})
        SET k.embedding = $embedding,
            k.embedding_model = $model,
            k.embedding_generated_at = datetime()
        RETURN k.knowledge_id
        """

        stored_count = 0
        with self.driver.session() as session:
            for id, embedding in embeddings.items():
                try:
                    result = session.run(
                        query, id=id, embedding=embedding, model="all-MiniLM-L6-v2"
                    )
                    if result.single():
                        stored_count += 1
                        logger.debug(f"Stored embedding for {id}")
                except Exception as e:
                    logger.error(f"Failed to store embedding for {id}: {e}")

        logger.info(f"Successfully stored {stored_count}/{len(embeddings)} embeddings")
        return stored_count

    def update_statistics(self):
        """Update and display knowledge base statistics."""
        query = """
        MATCH (k:Knowledge)
        WITH count(k) as total,
             count(CASE WHEN k.embedding IS NOT NULL THEN 1 END) as with_embeddings
        RETURN total, with_embeddings,
               toFloat(with_embeddings) / total as coverage
        """

        with self.driver.session() as session:
            result = session.run(query)
            stats = result.single()

            if stats:
                logger.info("=" * 60)
                logger.info("Knowledge Base Statistics:")
                logger.info(f"Total entries: {stats['total']}")
                logger.info(f"With embeddings: {stats['with_embeddings']}")
                logger.info(f"Coverage: {stats['coverage']:.1%}")
                logger.info("=" * 60)
                return stats.data()

        return None

    def run(self, batch_size: int = 10):
        """Run the embedding generation process."""
        logger.info("Starting embedding generation process...")

        # Get initial statistics
        logger.info("Initial statistics:")
        self.update_statistics()

        # Get entries without embeddings
        entries = self.get_entries_without_embeddings()

        if not entries:
            logger.info("All entries already have embeddings!")
            return

        # Process in batches
        total_stored = 0
        for i in range(0, len(entries), batch_size):
            batch = entries[i : i + batch_size]
            logger.info(
                f"Processing batch {i//batch_size + 1}/{(len(entries)-1)//batch_size + 1}"
            )

            # Generate embeddings
            embeddings = self.generate_embeddings(batch)

            # Store embeddings
            stored = self.store_embeddings(embeddings)
            total_stored += stored

        # Final statistics
        logger.info(f"\nTotal embeddings generated and stored: {total_stored}")
        logger.info("\nFinal statistics:")
        self.update_statistics()

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()


def main():
    """Main execution function."""
    # Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

    # Create generator
    generator = EmbeddingGenerator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Run generation
        generator.run(batch_size=BATCH_SIZE)
    finally:
        # Clean up
        generator.close()


if __name__ == "__main__":
    main()
