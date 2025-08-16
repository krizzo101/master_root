#!/usr/bin/env python3
"""
Generate Missing Embeddings for Knowledge Base

This script:
1. Queries all knowledge entries without embeddings
2. Generates embeddings using sentence-transformers
3. Updates Neo4j with the generated embeddings
4. Reports on progress and any errors
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "libs" / "opsvi-mcp"))

# Import Neo4j connection
from opsvi_mcp.servers.knowledge.knowledge_tools_fixed import (  # noqa: E402
    get_connection,
)

# Import embedding service
from apps.knowledge_system.embedding_service import get_embedding_service  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for knowledge entries missing them."""

    def __init__(self):
        """Initialize services."""
        self.embedding_service = get_embedding_service()
        self.neo4j = get_connection()
        self.stats = {
            "total_entries": 0,
            "missing_embeddings": 0,
            "successfully_updated": 0,
            "failed_updates": 0,
            "errors": [],
        }

    def get_entries_without_embeddings(self) -> list:
        """Query all knowledge entries without embeddings."""
        query = """
        MATCH (k:Knowledge)
        WHERE k.embedding IS NULL
           OR k.embedding_generated_at IS NULL
           OR size(k.embedding) = 0
        RETURN
            k.id as id,
            k.knowledge_id as knowledge_id,
            k.content as content,
            k.knowledge_type as type,
            k.type as legacy_type,
            k.description as description,
            k.context as context,
            k.created_at as created_at
        ORDER BY k.created_at DESC
        """

        try:
            results = self.neo4j.execute_read(query, {})
            logger.info(f"Found {len(results)} entries without embeddings")
            return results
        except Exception as e:
            logger.error(f"Failed to query entries: {e}")
            return []

    def generate_knowledge_text(self, entry: dict) -> str:
        """Create comprehensive text representation for embedding."""
        parts = []

        # Add content
        if entry.get("content"):
            parts.append(entry["content"])

        # Add description if different from content
        if entry.get("description") and entry["description"] != entry.get("content"):
            parts.append(entry["description"])

        # Add type information
        knowledge_type = entry.get("type") or entry.get("legacy_type") or "UNKNOWN"
        parts.append(f"Type: {knowledge_type}")

        # Add context if it's a string (JSON)
        if entry.get("context"):
            try:
                if isinstance(entry["context"], str):
                    context_data = json.loads(entry["context"])
                    # Extract key information from context
                    if isinstance(context_data, dict):
                        for key, value in context_data.items():
                            if isinstance(value, (str, int, float, bool)):
                                parts.append(f"{key}: {value}")
            except Exception:
                # If JSON parsing fails, just include raw context
                parts.append(str(entry["context"]))

        return " | ".join(parts)

    def update_entry_embedding(self, entry: dict, embedding: list) -> bool:
        """Update a knowledge entry with its embedding."""
        # Determine which ID to use
        entry_id = entry.get("knowledge_id") or entry.get("id")
        if not entry_id:
            logger.error(f"Entry has no ID: {entry}")
            return False

        # Determine ID field name
        id_field = "knowledge_id" if entry.get("knowledge_id") else "id"

        query = f"""
        MATCH (k:Knowledge {{{id_field}: $entry_id}})
        SET k.embedding = $embedding,
            k.embedding_generated_at = datetime(),
            k.embedding_model = $model
        RETURN k.{id_field} as updated_id
        """

        params = {
            "entry_id": entry_id,
            "embedding": embedding,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
        }

        try:
            result = self.neo4j.execute_write(query, params)
            if result.get("success", False):
                logger.info(f"✓ Updated embedding for {id_field}: {entry_id}")
                return True
            else:
                logger.error(f"✗ Failed to update {id_field}: {entry_id}")
                return False
        except Exception as e:
            logger.error(f"✗ Error updating {id_field} {entry_id}: {e}")
            self.stats["errors"].append(f"{entry_id}: {str(e)}")
            return False

    def process_batch(self, entries: list, batch_size: int = 10):
        """Process entries in batches for efficiency."""
        for i in range(0, len(entries), batch_size):
            batch = entries[i : i + batch_size]
            texts = []

            # Prepare texts for batch embedding
            for entry in batch:
                text = self.generate_knowledge_text(entry)
                texts.append(text)

            # Generate embeddings
            try:
                embeddings = self.embedding_service.generate_embeddings_batch(texts)

                # Update each entry
                for entry, embedding in zip(batch, embeddings):
                    if self.update_entry_embedding(entry, embedding):
                        self.stats["successfully_updated"] += 1
                    else:
                        self.stats["failed_updates"] += 1

                batch_num = i // batch_size + 1
                total_batches = (len(entries) + batch_size - 1) // batch_size
                logger.info(f"Processed batch {batch_num}/{total_batches}")

            except Exception as e:
                logger.error(f"Failed to process batch: {e}")
                self.stats["failed_updates"] += len(batch)
                self.stats["errors"].append(f"Batch {i//batch_size + 1}: {str(e)}")

    def run(self):
        """Main execution flow."""
        logger.info("=" * 60)
        logger.info("Starting Missing Embeddings Generation")
        logger.info("=" * 60)

        # Get total count
        count_query = "MATCH (k:Knowledge) RETURN count(k) as total"
        total_result = self.neo4j.execute_read(count_query, {})
        self.stats["total_entries"] = total_result[0]["total"] if total_result else 0

        # Get entries without embeddings
        entries = self.get_entries_without_embeddings()
        self.stats["missing_embeddings"] = len(entries)

        if not entries:
            logger.info("✅ All knowledge entries already have embeddings!")
            return

        logger.info(f"Processing {len(entries)} entries...")

        # Process in batches
        self.process_batch(entries)

        # Report results
        self.report_results()

    def report_results(self):
        """Generate final report."""
        logger.info("=" * 60)
        logger.info("EMBEDDING GENERATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total knowledge entries: {self.stats['total_entries']}")
        logger.info(f"Entries missing embeddings: {self.stats['missing_embeddings']}")
        logger.info(f"Successfully updated: {self.stats['successfully_updated']}")
        logger.info(f"Failed updates: {self.stats['failed_updates']}")

        success_rate = (
            self.stats["successfully_updated"] / self.stats["missing_embeddings"] * 100
            if self.stats["missing_embeddings"] > 0
            else 100
        )
        logger.info(f"Success rate: {success_rate:.1f}%")

        if self.stats["errors"]:
            logger.error("Errors encountered:")
            for error in self.stats["errors"][:10]:  # Show first 10 errors
                logger.error(f"  - {error}")
            if len(self.stats["errors"]) > 10:
                logger.error(f"  ... and {len(self.stats['errors']) - 10} more errors")

        # Verify embeddings were created
        verify_query = """
        MATCH (k:Knowledge)
        WHERE k.embedding IS NOT NULL
        RETURN count(k) as with_embeddings
        """
        verify_result = self.neo4j.execute_read(verify_query, {})
        embeddings_count = verify_result[0]["with_embeddings"] if verify_result else 0

        logger.info(
            f"\n✅ Final state: {embeddings_count}/{self.stats['total_entries']} "
            "entries have embeddings"
        )

        if embeddings_count == self.stats["total_entries"]:
            logger.info("🎉 All knowledge entries now have embeddings!")
        else:
            remaining = self.stats["total_entries"] - embeddings_count
            logger.warning(f"⚠️  {remaining} entries still missing embeddings")


def main():
    """Main entry point."""
    try:
        generator = EmbeddingGenerator()
        generator.run()
    except KeyboardInterrupt:
        logger.info("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
