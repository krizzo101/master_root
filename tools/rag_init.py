#!/usr/bin/env python3
"""OPSVI RAG Initialization Tool."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ruff: noqa: E402
from opsvi_core import get_logger, setup_logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logger = get_logger(__name__)


async def init_rag_system(collection_name: str = "global__demo") -> None:
    """Initialize RAG system with Qdrant and demo collection."""

    # Setup logging
    setup_logging(level="INFO")

    logger.info("Initializing RAG system", collection_name=collection_name)

    try:
        # Connect to Qdrant
        client = QdrantClient("localhost", port=6333)

        # Ping Qdrant
        logger.info("Pinging Qdrant...")
        health = client.get_health()
        logger.info("Qdrant health check passed", status=health.status)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if collection_name in collection_names:
            logger.info("Collection already exists", collection_name=collection_name)
            return

        # Create demo collection
        logger.info("Creating demo collection", collection_name=collection_name)

        # Define vector parameters (using a common embedding dimension)
        vector_size = 384  # Common for sentence-transformers models

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

        logger.info(
            "Demo collection created successfully",
            collection_name=collection_name,
            vector_size=vector_size,
        )

        # Add some sample data
        sample_texts = [
            "OPSVI is an AI/ML operations platform",
            "This is a demo collection for testing",
            "Vector search enables semantic similarity",
            "RAG systems combine retrieval and generation",
        ]

        # Create sample embeddings (dummy vectors for demo)
        import numpy as np

        sample_vectors = [np.random.rand(vector_size).tolist() for _ in sample_texts]

        # Add points to collection
        client.upsert(
            collection_name=collection_name,
            points=[
                {"id": i, "vector": vector, "payload": {"text": text}}
                for i, (text, vector) in enumerate(
                    zip(sample_texts, sample_vectors, strict=False)
                )
            ],
        )

        logger.info(
            "Sample data added to collection",
            collection_name=collection_name,
            sample_count=len(sample_texts),
        )

        # Test search
        logger.info("Testing search functionality...")
        search_result = client.search(
            collection_name=collection_name, query_vector=sample_vectors[0], limit=3
        )

        logger.info("Search test completed", results_count=len(search_result))

        print("✅ RAG system initialized successfully!")
        print(f"📊 Collection: {collection_name}")
        print(f"🔍 Sample data: {len(sample_texts)} documents")
        print("🌐 Qdrant UI: http://localhost:8080")

    except Exception as e:
        logger.error("Failed to initialize RAG system", error=str(e))
        print(f"❌ Failed to initialize RAG system: {e}")
        print("💡 Make sure Qdrant is running: docker-compose up -d")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize OPSVI RAG system")
    parser.add_argument(
        "--collection",
        default="global__demo",
        help="Collection name (default: global__demo)",
    )

    args = parser.parse_args()

    asyncio.run(init_rag_system(args.collection))


if __name__ == "__main__":
    main()
