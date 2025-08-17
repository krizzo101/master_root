#!/usr/bin/env python3
"""
Fix entries without knowledge_id and generate their embeddings
"""

import os
import sys

sys.path.insert(0, "/home/opsvi/master_root/apps/knowledge_system")

import hashlib
from datetime import datetime

from embedding_service import get_embedding_service
from neo4j import GraphDatabase


def generate_knowledge_id(content, index):
    """Generate a unique knowledge ID."""
    # Use content hash + timestamp for uniqueness
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"kb_{content_hash}_{index}"


def main():
    print("=" * 60)
    print("Fixing and Embedding Remaining Knowledge Entries")
    print("=" * 60)

    # Connect to Neo4j
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    # Get embedding service
    service = get_embedding_service()

    with driver.session() as session:
        # Find entries without embeddings (using Neo4j internal ID)
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.embedding IS NULL
            RETURN id(k) as neo4j_id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.description as description,
                   k.tags as tags,
                   k.context as context
        """
        )

        entries = list(result)
        print(f"\n📊 Found {len(entries)} entries to process\n")

        for i, entry in enumerate(entries, 1):
            print(f"[{i}/{len(entries)}] Processing Neo4j ID: {entry['neo4j_id']}")

            # Generate knowledge_id if missing
            knowledge_id = generate_knowledge_id(entry["content"] or "", i)
            print(f"   Generated ID: {knowledge_id}")

            # Prepare text for embedding
            knowledge_data = {
                "knowledge_type": entry["type"],
                "content": entry["content"] or entry["description"] or "",
                "tags": entry["tags"],
                "context": entry["context"],
            }

            text = service.prepare_knowledge_text(knowledge_data)
            print(f"   Text preview: {text[:80]}...")

            # Generate embedding
            embedding = service.generate_embedding(text)
            print(f"   Generated {len(embedding)}-dimensional embedding")

            # Update entry with both knowledge_id and embedding
            update_result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE id(k) = $neo4j_id
                SET k.knowledge_id = $knowledge_id,
                    k.embedding = $embedding,
                    k.embedding_model = $model,
                    k.embedding_generated_at = datetime(),
                    k.updated_at = datetime()
                RETURN k.knowledge_id as id
            """,
                neo4j_id=entry["neo4j_id"],
                knowledge_id=knowledge_id,
                embedding=embedding,
                model="sentence-transformers/all-MiniLM-L6-v2",
            )

            updated = update_result.single()
            if updated:
                print(f"   ✅ Updated with ID: {updated['id']}")
            else:
                print(f"   ❌ Failed to update")

        # Final statistics
        print("\n" + "=" * 60)
        result = session.run(
            """
            MATCH (k:Knowledge)
            RETURN count(k) as total,
                   count(k.embedding) as with_embeddings,
                   count(k.knowledge_id) as with_ids
        """
        )

        stats = result.single()
        print(f"📊 Final Statistics:")
        print(f"   Total entries: {stats['total']}")
        print(f"   With IDs: {stats['with_ids']}")
        print(f"   With embeddings: {stats['with_embeddings']}")
        print(f"   Coverage: {stats['with_embeddings']/stats['total']*100:.1f}%")

        if stats["with_embeddings"] == stats["total"]:
            print("\n🎉 SUCCESS! All knowledge entries now have embeddings!")

            # Create vector index
            print("\n🔍 Creating vector index for semantic search...")
            try:
                session.run(
                    """
                    CREATE VECTOR INDEX knowledge_embeddings IF NOT EXISTS
                    FOR (k:Knowledge)
                    ON k.embedding
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 384,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                """
                )
                print("   ✅ Vector index created/verified")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("   ✅ Vector index already exists")
                else:
                    print(f"   ℹ️ Index status: {e}")

    driver.close()
    print("\n✅ Processing complete!")


if __name__ == "__main__":
    main()
