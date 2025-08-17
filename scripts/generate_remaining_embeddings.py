#!/usr/bin/env python3
"""
Generate embeddings for the 10 remaining knowledge entries
"""

import os
import sys

sys.path.insert(0, "/home/opsvi/master_root/apps/knowledge_system")

import json

from embedding_service import get_embedding_service
from neo4j import GraphDatabase


def main():
    print("=" * 60)
    print("Generating Embeddings for Remaining Knowledge Entries")
    print("=" * 60)

    # Connect to Neo4j
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    # Get embedding service
    service = get_embedding_service()

    with driver.session() as session:
        # Find entries without embeddings
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.embedding IS NULL
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.context as context,
                   k.tags as tags
            LIMIT 20
        """
        )

        entries = list(result)
        print(f"\n📊 Found {len(entries)} entries without embeddings\n")

        if not entries:
            print("✅ All entries already have embeddings!")
            return

        # Generate embeddings
        for i, entry in enumerate(entries, 1):
            print(f"[{i}/{len(entries)}] Processing: {entry['id']}")

            # Prepare text for embedding
            knowledge_data = {
                "knowledge_type": entry["type"],
                "content": entry["content"],
                "tags": entry["tags"],
                "context": entry["context"],
            }

            text = service.prepare_knowledge_text(knowledge_data)
            print(f"   Text preview: {text[:100]}...")

            # Generate embedding
            embedding = service.generate_embedding(text)
            print(f"   Generated {len(embedding)}-dimensional embedding")

            # Store in Neo4j
            update_result = session.run(
                """
                MATCH (k:Knowledge {knowledge_id: $id})
                SET k.embedding = $embedding,
                    k.embedding_model = $model,
                    k.embedding_generated_at = datetime()
                RETURN k.knowledge_id as id
            """,
                id=entry["id"],
                embedding=embedding,
                model="sentence-transformers/all-MiniLM-L6-v2",
            )

            updated = update_result.single()
            if updated:
                print(f"   ✅ Embedding stored for {updated['id']}")
            else:
                print(f"   ❌ Failed to store embedding")

        # Final statistics
        print("\n" + "=" * 60)
        result = session.run(
            """
            MATCH (k:Knowledge)
            RETURN count(k) as total,
                   count(k.embedding) as with_embeddings
        """
        )

        stats = result.single()
        print(f"📊 Final Statistics:")
        print(f"   Total entries: {stats['total']}")
        print(f"   With embeddings: {stats['with_embeddings']}")
        print(f"   Coverage: {stats['with_embeddings']/stats['total']*100:.1f}%")

        if stats["with_embeddings"] == stats["total"]:
            print("\n🎉 SUCCESS! All knowledge entries now have embeddings!")

            # Create vector index if it doesn't exist
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
                print(f"   ℹ️ Index status: {e}")

    driver.close()
    print("\n✅ Embedding generation complete!")


if __name__ == "__main__":
    main()
