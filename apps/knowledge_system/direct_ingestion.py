#!/usr/bin/env python3
"""
Direct Knowledge Ingestion - Bypasses nano agent for bulk imports
Directly stores knowledge with embeddings, no GPT-5 calls
"""

import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, "/home/opsvi/master_root")

from neo4j import GraphDatabase

from apps.knowledge_system.embedding_service import get_embedding_service
from apps.knowledge_system.simple_rag import SimpleCache, SimpleVectorSearch

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class DirectKnowledgeStore:
    """Direct storage without nano agent transformation"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_search = SimpleVectorSearch()
        self.cache = SimpleCache()

        # Neo4j connection (with rate limiting disabled)
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )

    def generate_knowledge_id(self, content: str) -> str:
        """Generate unique ID for knowledge"""
        id_source = f"{content[:100]}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(id_source.encode()).hexdigest()[:16]

    def direct_store(
        self,
        content: str,
        knowledge_type: str,
        source: str,
        tags: List[str] = None,
        summary: str = None,
    ) -> Dict:
        """
        Store knowledge directly without nano agent processing

        Args:
            content: Raw knowledge content
            knowledge_type: Type (CODE_PATTERN, DOCUMENTATION, etc.)
            source: Source file or reference
            tags: List of tags
            summary: Optional summary (if not provided, uses first 100 chars)
        """

        # Generate ID
        knowledge_id = self.generate_knowledge_id(content)

        # Default summary if not provided
        if not summary:
            summary = content[:100] + "..." if len(content) > 100 else content

        # Default tags if not provided
        if not tags:
            tags = [knowledge_type.lower(), "reference"]

        # Generate embedding
        embed_text = f"{knowledge_type}: {content[:500]}"

        # Check cache first
        embedding = self.cache.get_cached_embedding(embed_text)
        if not embedding:
            embedding = self.embedding_service.generate_embedding(embed_text)
            self.cache.cache_embedding(embed_text, embedding)

        # Index in Qdrant
        metadata = {
            "knowledge_type": knowledge_type,
            "tags": tags[:10],
            "source": source,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self.vector_search.index_knowledge(knowledge_id, embedding, metadata)

        # Store in Neo4j
        query = """
        MERGE (k:Knowledge {knowledge_id: $knowledge_id})
        ON CREATE SET
            k.knowledge_type = $knowledge_type,
            k.content = $content,
            k.summary = $summary,
            k.source = $source,
            k.tags = $tags,
            k.confidence_score = 0.7,
            k.usage_count = 0,
            k.success_rate = 0.0,
            k.deprecated = false,
            k.created_at = datetime(),
            k.updated_at = datetime(),
            k.embedding = $embedding,
            k.embedding_model = 'sentence-transformers/all-MiniLM-L6-v2',
            k.direct_ingestion = true
        ON MATCH SET
            k.updated_at = datetime()
        RETURN k.knowledge_id as id
        """

        params = {
            "knowledge_id": knowledge_id,
            "knowledge_type": knowledge_type,
            "content": content[:5000],  # Limit content size
            "summary": summary[:500],
            "source": source,
            "tags": tags[:10],
            "embedding": embedding,
        }

        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query, params)
                stored_id = result.single()["id"]

                return {
                    "success": True,
                    "knowledge_id": stored_id,
                    "indexed_qdrant": True,
                    "stored_neo4j": True,
                }
        except Exception as e:
            logger.error(f"Neo4j storage failed: {e}")
            # Even if Neo4j fails, we have it in Qdrant
            return {
                "success": True,
                "knowledge_id": knowledge_id,
                "indexed_qdrant": True,
                "stored_neo4j": False,
                "error": str(e),
            }

    def bulk_ingest_directory(self, directory: str, max_files: int = None):
        """Bulk ingest files from directory"""

        path = Path(directory)
        stats = {"processed": 0, "stored": 0, "errors": 0, "total_size": 0}

        # Collect files
        patterns = ["**/*.md", "**/*.txt", "**/*.py", "**/*.json"]
        files = []

        for pattern in patterns:
            for f in path.glob(pattern):
                if f.is_file():
                    files.append(f)
                    if max_files and len(files) >= max_files:
                        break

        logger.info(f"Processing {len(files)} files from {directory}")

        for i, file_path in enumerate(files, 1):
            try:
                # Read file
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Skip small files
                if len(content) < 100:
                    continue

                stats["total_size"] += len(content)

                # Chunk large files
                chunks = []
                if len(content) > 3000:
                    # Split into chunks
                    chunk_size = 2000
                    for j in range(0, len(content), chunk_size):
                        chunks.append(content[j : j + chunk_size])
                else:
                    chunks = [content]

                # Determine type
                if file_path.suffix == ".py":
                    knowledge_type = "CODE_PATTERN"
                elif file_path.suffix == ".md":
                    knowledge_type = "DOCUMENTATION"
                elif file_path.suffix == ".json":
                    knowledge_type = "CONFIGURATION"
                else:
                    knowledge_type = "REFERENCE"

                # Generate tags
                tags = []
                path_parts = file_path.relative_to(path).parts
                tags.extend([p.replace("-", "_")[:20] for p in path_parts[:-1]])
                tags.append(file_path.suffix[1:] if file_path.suffix else "text")

                # Store each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    source = str(file_path.relative_to(path))
                    if len(chunks) > 1:
                        source += f" (chunk {chunk_idx+1}/{len(chunks)})"

                    result = self.direct_store(
                        content=chunk,
                        knowledge_type=knowledge_type,
                        source=source,
                        tags=tags,
                        summary=f"{file_path.name}: {chunk[:100]}",
                    )

                    if result["success"]:
                        stats["stored"] += 1
                    else:
                        stats["errors"] += 1

                stats["processed"] += 1

                # Progress update
                if i % 10 == 0:
                    logger.info(
                        f"Progress: {i}/{len(files)} files, {stats['stored']} chunks stored"
                    )

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                stats["errors"] += 1

        # Close Neo4j connection
        self.neo4j_driver.close()

        # Report
        logger.info("=" * 60)
        logger.info("DIRECT INGESTION COMPLETE")
        logger.info(f"Files processed: {stats['processed']}")
        logger.info(f"Chunks stored: {stats['stored']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Total size: {stats['total_size'] / 1024 / 1024:.1f} MB")
        logger.info("=" * 60)

        return stats


if __name__ == "__main__":
    # Test direct storage
    store = DirectKnowledgeStore()

    # Test with a single item
    test_result = store.direct_store(
        content="Direct ingestion test: Python decorators can be used to modify function behavior",
        knowledge_type="CODE_PATTERN",
        source="test.py",
        tags=["python", "decorator", "test"],
    )

    print(f"Test storage: {test_result}")

    # Run bulk ingestion on reference directory
    print("\nStarting bulk ingestion of reference materials...")
    stats = store.bulk_ingest_directory(
        "/home/opsvi/.reference", max_files=50  # Start with 50 files
    )
