#!/usr/bin/env python3
"""
Fast Reference Ingestion - Qdrant-only version
Bypasses Neo4j authentication issues and focuses on vector indexing
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, "/home/opsvi/master_root")

from apps.knowledge_system.embedding_service import get_embedding_service
from apps.knowledge_system.knowledge_nano_agent import get_nano_agent
from apps.knowledge_system.simple_rag import SimpleCache, SimpleVectorSearch

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class FastIngestion:
    """Fast ingestion directly to Qdrant"""

    def __init__(self):
        self.vector_search = SimpleVectorSearch()
        self.cache = SimpleCache()
        self.embedding_service = get_embedding_service()
        self.nano_agent = get_nano_agent()
        self.stats = {"processed": 0, "indexed": 0, "cached": 0, "errors": 0}

    async def process_file(self, file_path: Path) -> int:
        """Process a single file and return number of chunks indexed"""
        chunks_indexed = 0

        try:
            # Read file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Skip small files
            if len(content) < 100:
                return 0

            # Extract meaningful chunks based on file type
            chunks = []

            if file_path.suffix == ".md":
                # Extract markdown sections
                import re

                sections = re.split(r"^#{1,3}\s+", content, flags=re.MULTILINE)
                for section in sections[1:5]:  # First 5 sections
                    if len(section) > 200:
                        chunks.append(section[:1500])

            elif file_path.suffix == ".py":
                # Extract docstrings and class definitions
                import re

                # Find classes with docstrings
                classes = re.findall(
                    r'class\s+(\w+).*?:\s*"""(.*?)"""', content, re.DOTALL
                )
                for name, doc in classes[:3]:
                    chunks.append(f"Class {name}: {doc[:500]}")

                # Find important functions
                functions = re.findall(
                    r'def\s+(\w+)\(.*?\).*?:\s*"""(.*?)"""', content, re.DOTALL
                )
                for name, doc in functions[:3]:
                    if len(doc) > 50:
                        chunks.append(f"Function {name}: {doc[:500]}")

            elif file_path.suffix == ".txt":
                # Take first meaningful paragraph
                paragraphs = content.split("\n\n")
                for para in paragraphs[:3]:
                    if len(para) > 200:
                        chunks.append(para[:1500])

            # Process chunks
            for chunk_text in chunks:
                try:
                    # Transform with nano agent
                    structured = await self.nano_agent.transform_knowledge(
                        raw_input=chunk_text,
                        hint_type="DOCUMENTATION",
                        hint_tags=[file_path.stem, file_path.suffix[1:]],
                    )

                    # Generate embedding
                    embed_text = (
                        f"{structured.knowledge_type}: {structured.content[:500]}"
                    )

                    # Check cache first
                    embedding = self.cache.get_cached_embedding(embed_text)
                    if not embedding:
                        embedding = self.embedding_service.generate_embedding(
                            embed_text
                        )
                        self.cache.cache_embedding(embed_text, embedding)
                        self.stats["cached"] += 1

                    # Index in Qdrant
                    knowledge_id = f"{file_path.stem}_{chunks_indexed}"
                    metadata = {
                        "source": str(file_path.relative_to("/home/opsvi/.reference")),
                        "type": structured.knowledge_type,
                        "tags": structured.tags[:5],
                    }

                    self.vector_search.index_knowledge(
                        knowledge_id, embedding, metadata
                    )
                    chunks_indexed += 1
                    self.stats["indexed"] += 1

                except Exception as e:
                    logger.warning(f"Chunk processing error: {e}")
                    self.stats["errors"] += 1

        except Exception as e:
            logger.error(f"File processing error for {file_path}: {e}")
            self.stats["errors"] += 1

        return chunks_indexed

    async def ingest_directory(
        self, directory: str = "/home/opsvi/.reference", max_files: int = 20
    ):
        """Ingest files from directory"""
        logger.info(f"Starting fast ingestion from {directory}")

        path = Path(directory)
        files = []

        # Collect important files first
        priority_patterns = [
            "**/README.md",
            "**/api.md",
            "**/*example*.py",
            "**/*cookbook*.md",
            "gpt-5*.txt",
            "responses*.txt",
        ]

        for pattern in priority_patterns:
            for f in path.glob(pattern):
                if f.is_file() and f not in files:
                    files.append(f)
                    if len(files) >= max_files:
                        break

        # Process files
        logger.info(f"Processing {len(files)} files...")

        for i, file_path in enumerate(files, 1):
            chunks = await self.process_file(file_path)
            self.stats["processed"] += 1

            if chunks > 0:
                logger.info(
                    f"[{i}/{len(files)}] Indexed {chunks} chunks from {file_path.name}"
                )

            # Progress update
            if i % 5 == 0:
                logger.info(f"Stats: {self.stats}")

        # Final report
        logger.info("=" * 60)
        logger.info("FAST INGESTION COMPLETE")
        logger.info(f"Files processed: {self.stats['processed']}")
        logger.info(f"Chunks indexed: {self.stats['indexed']}")
        logger.info(f"Embeddings cached: {self.stats['cached']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)


async def main():
    ingester = FastIngestion()
    await ingester.ingest_directory(max_files=20)  # Start with 20 files


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
