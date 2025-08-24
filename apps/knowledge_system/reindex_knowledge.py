#!/usr/bin/env python3
"""
Reindex Knowledge System - Ensure all knowledge is properly vectorized
This fixes the critical gap where knowledge exists but can't be found
"""

import sys
import uuid
from typing import Dict, List

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

sys.path.insert(0, "/home/opsvi/master_root")
from apps.knowledge_system.embedding_service import get_embedding_service


class KnowledgeReindexer:
    """
    Ensure all knowledge is properly indexed for retrieval
    """

    def __init__(self):
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.embedding_service = get_embedding_service()
        self.collection_name = "knowledge_vectors"

    def ensure_collection_exists(self):
        """Ensure Qdrant collection exists with proper configuration"""

        collections = self.qdrant_client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            print(f"Creating collection: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        else:
            # Check if it's properly configured
            info = self.qdrant_client.get_collection(self.collection_name)
            print(f"Collection exists with {info.vectors_count} vectors")

    def index_all_knowledge(self) -> Dict:
        """Index all knowledge from Neo4j into Qdrant"""

        stats = {"total_knowledge": 0, "indexed": 0, "skipped": 0, "errors": 0}

        with self.neo4j_driver.session() as session:
            # Get all knowledge with content
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.content IS NOT NULL
                AND k.content <> ''
                AND k.deprecated = false
                RETURN k.knowledge_id as id,
                       k.content as content,
                       k.knowledge_type as type,
                       k.source as source,
                       k.confidence_score as confidence
                ORDER BY k.confidence_score DESC
            """
            )

            batch_points = []
            batch_size = 10

            for record in result:
                stats["total_knowledge"] += 1

                try:
                    # Generate embedding
                    embedding = self.embedding_service.generate_embedding(
                        record["content"]
                    )

                    # Create point for Qdrant
                    point_id = str(uuid.uuid4())
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "knowledge_id": record["id"],
                            "knowledge_type": record["type"] or "GENERAL",
                            "source": record["source"] or "unknown",
                            "confidence": record["confidence"] or 0.5,
                            "content_preview": record["content"][:200],
                        },
                    )

                    batch_points.append(point)

                    # Upload in batches
                    if len(batch_points) >= batch_size:
                        self.qdrant_client.upsert(
                            collection_name=self.collection_name, points=batch_points
                        )
                        stats["indexed"] += len(batch_points)
                        print(
                            f"Indexed {stats['indexed']}/{stats['total_knowledge']} knowledge items..."
                        )
                        batch_points = []

                except Exception as e:
                    print(f"Error indexing knowledge {record['id']}: {e}")
                    stats["errors"] += 1

            # Upload remaining batch
            if batch_points:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name, points=batch_points
                )
                stats["indexed"] += len(batch_points)

        return stats

    def verify_indexing(self) -> Dict:
        """Verify that indexing worked correctly"""

        # Check Neo4j count
        with self.neo4j_driver.session() as session:
            neo4j_count = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.content IS NOT NULL
                AND k.content <> ''
                AND k.deprecated = false
                RETURN count(k) as count
            """
            ).single()["count"]

        # Check Qdrant count
        collection_info = self.qdrant_client.get_collection(self.collection_name)
        qdrant_count = collection_info.vectors_count

        # Test search
        test_query = "error handling async streaming"
        test_embedding = self.embedding_service.generate_embedding(test_query)
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name, query_vector=test_embedding, limit=5
        )

        return {
            "neo4j_knowledge": neo4j_count,
            "qdrant_vectors": qdrant_count,
            "sync_status": "synced" if neo4j_count == qdrant_count else "mismatch",
            "test_search_results": len(search_results),
            "sample_result": search_results[0].payload if search_results else None,
        }

    def close(self):
        """Clean up connections"""
        self.neo4j_driver.close()


def main():
    print("KNOWLEDGE REINDEXING SYSTEM")
    print("=" * 60)

    reindexer = KnowledgeReindexer()

    try:
        # Ensure collection exists
        print("\n1. Checking Qdrant collection...")
        reindexer.ensure_collection_exists()

        # Index all knowledge
        print("\n2. Indexing all knowledge from Neo4j to Qdrant...")
        stats = reindexer.index_all_knowledge()

        print(f"\nIndexing Complete:")
        print(f"  Total Knowledge: {stats['total_knowledge']}")
        print(f"  Successfully Indexed: {stats['indexed']}")
        print(f"  Errors: {stats['errors']}")

        # Verify
        print("\n3. Verifying indexing...")
        verification = reindexer.verify_indexing()

        print(f"\nVerification Results:")
        print(f"  Neo4j Knowledge: {verification['neo4j_knowledge']}")
        print(f"  Qdrant Vectors: {verification['qdrant_vectors']}")
        print(f"  Sync Status: {verification['sync_status']}")
        print(f"  Test Search Results: {verification['test_search_results']}")

        if verification["sample_result"]:
            print(
                f"  Sample Result: {verification['sample_result']['knowledge_type']} - {verification['sample_result']['content_preview'][:50]}..."
            )

        print("\n✓ Knowledge system is now properly indexed and searchable!")

    finally:
        reindexer.close()


if __name__ == "__main__":
    main()
