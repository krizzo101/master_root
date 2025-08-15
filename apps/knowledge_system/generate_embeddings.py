#!/usr/bin/env python3
"""
Generate embeddings for all existing knowledge entries in Neo4j.
This script should be run periodically to ensure all knowledge has embeddings.
"""

import sys
import json
from neo4j import GraphDatabase
from embedding_service import get_embedding_service

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


def get_knowledge_without_embeddings(driver):
    """Fetch all knowledge entries that don't have embeddings yet."""
    with driver.session() as session:
        result = session.run("""
            MATCH (k:Knowledge)
            WHERE k.embedding IS NULL
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.context as context,
                   k.tags as tags
            LIMIT 100
        """)
        return list(result)


def get_all_knowledge(driver):
    """Fetch all knowledge entries (for re-generating embeddings)."""
    with driver.session() as session:
        result = session.run("""
            MATCH (k:Knowledge)
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.context as context,
                   k.tags as tags
        """)
        return list(result)


def update_knowledge_embedding(driver, knowledge_id, embedding):
    """Update a knowledge entry with its embedding."""
    with driver.session() as session:
        result = session.run("""
            MATCH (k:Knowledge {knowledge_id: $knowledge_id})
            SET k.embedding = $embedding,
                k.embedding_generated_at = datetime(),
                k.embedding_model = $model
            RETURN k.knowledge_id as id
        """, 
        knowledge_id=knowledge_id,
        embedding=embedding,
        model="sentence-transformers/all-MiniLM-L6-v2")
        
        updated = list(result)
        return len(updated) > 0


def main(regenerate_all=False):
    """
    Generate embeddings for knowledge entries.
    
    Args:
        regenerate_all: If True, regenerate embeddings for all entries
    """
    # Initialize services
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    embedding_service = get_embedding_service()
    
    try:
        # Fetch knowledge entries
        if regenerate_all:
            print("Fetching ALL knowledge entries for embedding generation...")
            knowledge_entries = get_all_knowledge(driver)
        else:
            print("Fetching knowledge entries without embeddings...")
            knowledge_entries = get_knowledge_without_embeddings(driver)
        
        print(f"Found {len(knowledge_entries)} entries to process")
        
        if not knowledge_entries:
            print("No entries need embedding generation")
            return
        
        # Prepare texts for batch embedding
        texts = []
        for entry in knowledge_entries:
            # Convert entry to dict for the service
            entry_dict = dict(entry)
            
            # Parse JSON fields if they're strings
            if entry_dict.get('context') and isinstance(entry_dict['context'], str):
                try:
                    entry_dict['context'] = json.loads(entry_dict['context'])
                except:
                    pass
            
            if entry_dict.get('tags') and isinstance(entry_dict['tags'], str):
                try:
                    entry_dict['tags'] = json.loads(entry_dict['tags'])
                except:
                    pass
            
            text = embedding_service.prepare_knowledge_text(entry_dict)
            texts.append(text)
        
        # Generate embeddings in batch
        print(f"Generating embeddings for {len(texts)} texts...")
        embeddings = embedding_service.generate_embeddings_batch(texts)
        
        # Update Neo4j with embeddings
        success_count = 0
        for entry, embedding in zip(knowledge_entries, embeddings):
            knowledge_id = entry.get('id', 'unknown')
            knowledge_type = entry.get('type', 'unknown')
            
            if knowledge_id and knowledge_id != 'unknown':
                if update_knowledge_embedding(driver, knowledge_id, embedding):
                    success_count += 1
                    print(f"✓ Updated embedding for: {knowledge_id[:8]}... ({knowledge_type})")
                else:
                    print(f"✗ Failed to update: {knowledge_id[:8]}...")
            else:
                print(f"⚠️ Skipping entry with no ID")
        
        print(f"\nSuccessfully updated {success_count}/{len(knowledge_entries)} entries")
        
        # Verify vector index is being used
        with driver.session() as session:
            result = session.run("SHOW INDEXES WHERE name = 'knowledge_embeddings'")
            indexes = list(result)
            if indexes:
                print("\n✓ Vector index 'knowledge_embeddings' is active")
            else:
                print("\n⚠️ Vector index not found - creating it now...")
                session.run("""
                    CREATE VECTOR INDEX knowledge_embeddings IF NOT EXISTS
                    FOR (k:Knowledge)
                    ON k.embedding
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 384,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                """)
                print("✓ Vector index created")
        
    finally:
        driver.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate embeddings for knowledge entries")
    parser.add_argument("--regenerate-all", action="store_true", 
                        help="Regenerate embeddings for all entries")
    args = parser.parse_args()
    
    main(regenerate_all=args.regenerate_all)