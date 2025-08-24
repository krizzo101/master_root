#!/usr/bin/env python3
"""
Monitored Knowledge Ingestion with Live Logging
Curated ingestion of ~11MB valuable content from 1.3GB reference
"""

import hashlib
import json
import logging
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

sys.path.insert(0, "/home/opsvi/master_root")

from neo4j import GraphDatabase

from apps.knowledge_system.embedding_service import get_embedding_service
from apps.knowledge_system.semantic_code_analyzer import CodeIntelligenceBuilder
from apps.knowledge_system.simple_rag import SimpleCache, SimpleVectorSearch

# Configure logging to file AND console
LOG_FILE = "/home/opsvi/master_root/apps/knowledge_system/ingestion_monitor.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class IngestionMonitor:
    """Live monitoring of ingestion progress"""

    def __init__(self):
        self.start_time = time.time()
        self.stats = {
            "files_scanned": 0,
            "files_selected": 0,
            "files_processed": 0,
            "chunks_created": 0,
            "chunks_stored": 0,
            "embeddings_generated": 0,
            "embeddings_cached": 0,
            "errors": 0,
            "bytes_processed": 0,
            "bytes_selected": 0,
        }
        self.current_file = None
        self.lock = threading.Lock()

    def update(self, key: str, value: int = 1):
        """Thread-safe stat update"""
        with self.lock:
            self.stats[key] += value

    def set_current(self, filename: str):
        """Set current file being processed"""
        with self.lock:
            self.current_file = filename

    def log_progress(self):
        """Log current progress"""
        elapsed = time.time() - self.start_time
        rate = self.stats["files_processed"] / elapsed if elapsed > 0 else 0

        logger.info(f"{'='*60}")
        logger.info(f"PROGRESS REPORT - {elapsed:.1f}s elapsed")
        logger.info(
            f"Files: {self.stats['files_processed']}/{self.stats['files_selected']} ({rate:.1f}/sec)"
        )
        logger.info(
            f"Chunks: {self.stats['chunks_stored']}/{self.stats['chunks_created']}"
        )
        logger.info(
            f"Embeddings: {self.stats['embeddings_generated']} new, {self.stats['embeddings_cached']} cached"
        )
        logger.info(f"Data: {self.stats['bytes_processed']/1024/1024:.1f}MB processed")
        logger.info(f"Errors: {self.stats['errors']}")
        if self.current_file:
            logger.info(f"Current: {self.current_file}")
        logger.info(f"{'='*60}")


class CuratedDirectIngestion:
    """Direct ingestion with curation and monitoring"""

    # File patterns to INCLUDE
    INCLUDE_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yaml"}

    # Patterns to EXCLUDE
    EXCLUDE_PATTERNS = [
        "*/.git/*",
        "*/__pycache__/*",
        "*/test_*",
        "*_test.py",
        "*/tests/*",
        "*.pyc",
        "*.ipynb",
        "*.jpg",
        "*.png",
        "*.pdf",
        "*.jsonl",  # Usually large test data
        "*/node_modules/*",
        "*/venv/*",
        "*/build/*",
        "*/dist/*",
    ]

    # Size limits
    MIN_SIZE = 100  # bytes
    MAX_SIZE = 500_000  # 500KB per file

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_search = SimpleVectorSearch()
        self.cache = SimpleCache()
        self.monitor = IngestionMonitor()

        # Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )

        # Track state for relationship creation
        self.source_files = {}  # path -> node_id mapping
        self.previous_chunk_ids = {}  # file_path -> last_chunk_id for NEXT_CHUNK

        # Code intelligence for Python files
        self.code_intelligence = CodeIntelligenceBuilder()

        logger.info("Initialized ingestion pipeline with code intelligence")
        logger.info(f"Log file: {LOG_FILE}")

    def should_include(self, file_path: Path) -> bool:
        """Determine if file should be included"""

        # Check extension
        if file_path.suffix not in self.INCLUDE_EXTENSIONS:
            return False

        # Check exclude patterns
        str_path = str(file_path)
        for pattern in self.EXCLUDE_PATTERNS:
            if "*" in pattern:
                pattern_parts = (
                    pattern.replace("*/", "").replace("/*", "").replace("*", "")
                )
                if pattern_parts in str_path:
                    return False
            elif pattern in str_path:
                return False

        # Check size
        try:
            size = file_path.stat().st_size
            if size < self.MIN_SIZE or size > self.MAX_SIZE:
                return False
        except:
            return False

        return True

    def ensure_source_file(self, file_path: Path, base_path: Path) -> str:
        """Ensure SourceFile node exists and return its ID"""
        relative_path = str(file_path.relative_to(base_path))

        if relative_path in self.source_files:
            return self.source_files[relative_path]

        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MERGE (s:SourceFile {path: $path})
                ON CREATE SET
                    s.created_at = datetime(),
                    s.file_type = $file_type,
                    s.size = $size
                RETURN s.path as path
            """,
                path=relative_path,
                file_type=file_path.suffix,
                size=file_path.stat().st_size,
            )

            self.source_files[relative_path] = result.single()["path"]
            return self.source_files[relative_path]

    def extract_chunks(self, file_path: Path, content: str) -> List[Dict]:
        """Extract knowledge chunks from content"""
        chunks = []

        # For large files, split into chunks
        if len(content) > 3000:
            chunk_size = 2000
            overlap = 200
            for i in range(0, len(content), chunk_size - overlap):
                chunk_text = content[i : i + chunk_size]
                if len(chunk_text) > self.MIN_SIZE:
                    chunks.append(
                        {"text": chunk_text, "start": i, "end": i + len(chunk_text)}
                    )
        else:
            chunks.append({"text": content, "start": 0, "end": len(content)})

        return chunks

    def store_chunk(
        self,
        content: str,
        knowledge_type: str,
        source: str,
        tags: List[str],
        file_path: str = None,
        chunk_index: int = None,
    ) -> str:
        """Store a single chunk and create relationships. Returns knowledge_id or None"""
        try:
            # Generate ID
            knowledge_id = hashlib.sha256(
                f"{content[:100]}{time.time()}".encode()
            ).hexdigest()[:16]

            # Generate or get cached embedding
            embed_key = content[:500]
            embedding = self.cache.get_cached_embedding(embed_key)

            if embedding:
                self.monitor.update("embeddings_cached")
            else:
                embedding = self.embedding_service.generate_embedding(embed_key)
                self.cache.cache_embedding(embed_key, embedding)
                self.monitor.update("embeddings_generated")

            # Index in Qdrant
            metadata = {
                "knowledge_type": knowledge_type,
                "source": source,
                "tags": tags[:10],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.vector_search.index_knowledge(knowledge_id, embedding, metadata)

            # Store in Neo4j with relationships
            with self.neo4j_driver.session() as session:
                # Create Knowledge node
                result = session.run(
                    """
                    CREATE (k:Knowledge {
                        knowledge_id: $knowledge_id,
                        knowledge_type: $knowledge_type,
                        content: $content,
                        source: $source,
                        tags: $tags,
                        confidence_score: 0.7,
                        created_at: datetime(),
                        direct_ingestion: true,
                        embedding_model: 'sentence-transformers/all-MiniLM-L6-v2'
                    })
                    RETURN k.knowledge_id as id
                """,
                    knowledge_id=knowledge_id,
                    knowledge_type=knowledge_type,
                    content=content[:5000],
                    source=source,
                    tags=tags,
                )

                result.single()

                # Create relationship to SourceFile
                if file_path:
                    session.run(
                        """
                        MATCH (s:SourceFile {path: $file_path})
                        MATCH (k:Knowledge {knowledge_id: $knowledge_id})
                        MERGE (s)-[:CONTAINS]->(k)
                    """,
                        file_path=file_path,
                        knowledge_id=knowledge_id,
                    )

                # Create NEXT_CHUNK relationship if this is part of a sequence
                if file_path and chunk_index is not None and chunk_index > 0:
                    prev_chunk_id = self.previous_chunk_ids.get(file_path)
                    if prev_chunk_id:
                        session.run(
                            """
                            MATCH (k1:Knowledge {knowledge_id: $prev_id})
                            MATCH (k2:Knowledge {knowledge_id: $curr_id})
                            MERGE (k1)-[:NEXT_CHUNK]->(k2)
                        """,
                            prev_id=prev_chunk_id,
                            curr_id=knowledge_id,
                        )

                # Update previous chunk tracking
                if file_path and chunk_index is not None:
                    self.previous_chunk_ids[file_path] = knowledge_id

            return knowledge_id

        except Exception as e:
            logger.error(f"Failed to store chunk: {e}")
            return None

    def process_file(self, file_path: Path, base_path: Path) -> int:
        """Process a single file, return number of chunks stored"""
        chunks_stored = 0
        relative_path = str(file_path.relative_to(base_path))

        try:
            self.monitor.set_current(relative_path)

            # Ensure SourceFile node exists
            source_file_path = self.ensure_source_file(file_path, base_path)

            # Read file
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            self.monitor.update("bytes_processed", len(content))

            # Determine type
            if file_path.suffix == ".py":
                knowledge_type = "CODE"
                # Extract semantic code intelligence
                try:
                    entities, relationships = self.code_intelligence.analyze_file(
                        str(file_path), content
                    )
                    if entities or relationships:
                        self.code_intelligence.store_code_intelligence(
                            str(file_path), entities, relationships
                        )
                        logger.info(
                            f"Extracted {len(entities)} entities, {len(relationships)} relationships from {relative_path}"
                        )
                except Exception as e:
                    logger.warning(f"Code analysis failed for {relative_path}: {e}")
            elif file_path.suffix == ".md":
                knowledge_type = "DOCUMENTATION"
            elif file_path.suffix in [".json", ".yaml"]:
                knowledge_type = "CONFIGURATION"
            else:
                knowledge_type = "REFERENCE"

            # Generate tags from path
            tags = []
            path_parts = file_path.relative_to(base_path).parts
            tags.extend(
                [p.replace("-", "_").replace(".", "_")[:20] for p in path_parts[:-1]]
            )
            tags.append(file_path.suffix[1:])

            # Extract and store chunks
            chunks = self.extract_chunks(file_path, content)
            self.monitor.update("chunks_created", len(chunks))

            # Reset chunk tracking for this file
            self.previous_chunk_ids[relative_path] = None

            for i, chunk in enumerate(chunks):
                chunk_source = f"{relative_path}"
                if len(chunks) > 1:
                    chunk_source += f" [part {i+1}/{len(chunks)}]"

                # Store with relationship information
                knowledge_id = self.store_chunk(
                    chunk["text"],
                    knowledge_type,
                    chunk_source,
                    tags,
                    file_path=relative_path,
                    chunk_index=i if len(chunks) > 1 else None,
                )

                if knowledge_id:
                    chunks_stored += 1
                    self.monitor.update("chunks_stored")
                else:
                    self.monitor.update("errors")

            self.monitor.update("files_processed")

        except Exception as e:
            logger.error(f"Error processing {relative_path}: {e}")
            self.monitor.update("errors")

        return chunks_stored

    def create_tag_relationships(self):
        """Create relationships between Knowledge nodes with shared tags"""
        try:
            with self.neo4j_driver.session() as session:
                # Create SHARES_TAG relationships for nodes with common tags
                result = session.run(
                    """
                    MATCH (k1:Knowledge), (k2:Knowledge)
                    WHERE k1.direct_ingestion = true
                      AND k2.direct_ingestion = true
                      AND k1.knowledge_id < k2.knowledge_id
                      AND SIZE([tag IN k1.tags WHERE tag IN k2.tags]) >= 2
                    WITH k1, k2, [tag IN k1.tags WHERE tag IN k2.tags] as shared_tags
                    LIMIT 200
                    MERGE (k1)-[r:SHARES_TAG]->(k2)
                    SET r.tags = shared_tags
                    RETURN count(r) as count
                """
                )
                count = result.single()["count"]
                logger.info(f"Created {count} SHARES_TAG relationships")

                # Create SAME_TYPE relationships for same knowledge types
                result = session.run(
                    """
                    MATCH (k1:Knowledge), (k2:Knowledge)
                    WHERE k1.direct_ingestion = true
                      AND k2.direct_ingestion = true
                      AND k1.knowledge_type = k2.knowledge_type
                      AND k1.knowledge_id < k2.knowledge_id
                      AND EXISTS {
                          MATCH (s1:SourceFile)-[:CONTAINS]->(k1)
                          MATCH (s2:SourceFile)-[:CONTAINS]->(k2)
                          WHERE s1.path <> s2.path
                      }
                    WITH k1, k2, k1.knowledge_type as type
                    LIMIT 100
                    MERGE (k1)-[:SAME_TYPE {type: type}]->(k2)
                    RETURN count(*) as count
                """
                )
                count = result.single()["count"]
                logger.info(f"Created {count} SAME_TYPE relationships")

        except Exception as e:
            logger.error(f"Failed to create tag relationships: {e}")

    def run_ingestion(
        self, directory: str = "/home/opsvi/.reference", max_files: int = None
    ):
        """Run the curated ingestion with monitoring"""
        base_path = Path(directory)

        logger.info("=" * 60)
        logger.info("STARTING CURATED KNOWLEDGE INGESTION")
        logger.info(f"Source: {directory}")
        logger.info(f"Max files: {max_files or 'unlimited'}")
        logger.info("=" * 60)

        # Phase 1: Scan and select files
        logger.info("Phase 1: Scanning directory...")
        selected_files = []

        for file_path in base_path.rglob("*"):
            if file_path.is_file():
                self.monitor.update("files_scanned")

                if self.should_include(file_path):
                    selected_files.append(file_path)
                    self.monitor.update("files_selected")
                    self.monitor.update("bytes_selected", file_path.stat().st_size)

                    if max_files and len(selected_files) >= max_files:
                        break

        logger.info(
            f"Selected {len(selected_files)} files ({self.monitor.stats['bytes_selected']/1024/1024:.1f}MB)"
        )

        # Phase 2: Process files
        logger.info("Phase 2: Processing files...")
        progress_interval = max(1, len(selected_files) // 20)  # Report 20 times

        for i, file_path in enumerate(selected_files, 1):
            self.process_file(file_path, base_path)

            # Progress report
            if i % progress_interval == 0 or i == len(selected_files):
                self.monitor.log_progress()

        # Create tag-based relationships in batch
        logger.info("Phase 3: Creating tag relationships...")
        self.create_tag_relationships()

        # Close connections
        self.neo4j_driver.close()
        self.code_intelligence.close()

        # Final report
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info(f"Files processed: {self.monitor.stats['files_processed']}")
        logger.info(f"Chunks stored: {self.monitor.stats['chunks_stored']}")
        logger.info(
            f"Embeddings: {self.monitor.stats['embeddings_generated']} generated, {self.monitor.stats['embeddings_cached']} cached"
        )
        logger.info(f"Total time: {time.time() - self.monitor.start_time:.1f}s")
        logger.info(f"Errors: {self.monitor.stats['errors']}")
        logger.info("=" * 60)


if __name__ == "__main__":
    # Parse arguments
    import argparse

    parser = argparse.ArgumentParser(description="Curated knowledge ingestion")
    parser.add_argument(
        "--max-files", type=int, default=100, help="Maximum files to process"
    )
    parser.add_argument(
        "--directory", default="/home/opsvi/.reference", help="Directory to ingest"
    )
    args = parser.parse_args()

    # Run ingestion
    ingester = CuratedDirectIngestion()
    ingester.run_ingestion(args.directory, args.max_files)
