#!/usr/bin/env python3
"""
Add relationships between Knowledge nodes for better graph traversal
"""

import re
import sys
from collections import defaultdict

from neo4j import GraphDatabase

sys.path.insert(0, "/home/opsvi/master_root")


def create_knowledge_relationships():
    """Create relationships between related Knowledge nodes"""

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    with driver.session() as session:
        # 1. Link chunks from the same source file
        print("Creating NEXT_CHUNK relationships...")
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.direct_ingestion = true AND k.source CONTAINS '[part'
            RETURN k.knowledge_id as id, k.source as source
            ORDER BY k.source
        """
        )

        # Group by base source
        chunks_by_source = defaultdict(list)
        for record in result:
            source = record["source"]
            # Extract base source (before [part X/Y])
            base = re.sub(r"\s*\[part \d+/\d+\]", "", source)
            chunks_by_source[base].append((record["id"], source))

        # Create NEXT_CHUNK relationships
        relationships_created = 0
        for base_source, chunks in chunks_by_source.items():
            # Sort chunks by part number
            def get_part_num(chunk_tuple):
                match = re.search(r"\[part (\d+)/\d+\]", chunk_tuple[1])
                return int(match.group(1)) if match else 0

            sorted_chunks = sorted(chunks, key=get_part_num)

            # Link sequential chunks
            for i in range(len(sorted_chunks) - 1):
                current_id = sorted_chunks[i][0]
                next_id = sorted_chunks[i + 1][0]

                session.run(
                    """
                    MATCH (k1:Knowledge {knowledge_id: $current_id})
                    MATCH (k2:Knowledge {knowledge_id: $next_id})
                    MERGE (k1)-[:NEXT_CHUNK]->(k2)
                """,
                    current_id=current_id,
                    next_id=next_id,
                )
                relationships_created += 1

        print(f"  Created {relationships_created} NEXT_CHUNK relationships")

        # 2. Link Knowledge nodes by shared tags
        print("\nCreating SHARES_TAG relationships...")
        result = session.run(
            """
            MATCH (k1:Knowledge), (k2:Knowledge)
            WHERE k1.direct_ingestion = true
              AND k2.direct_ingestion = true
              AND k1.knowledge_id < k2.knowledge_id
              AND SIZE([tag IN k1.tags WHERE tag IN k2.tags]) > 0
            WITH k1, k2, [tag IN k1.tags WHERE tag IN k2.tags] as shared_tags
            LIMIT 100
            MERGE (k1)-[r:SHARES_TAG]->(k2)
            SET r.tags = shared_tags
            RETURN count(r) as count
        """
        )
        count = result.single()["count"]
        print(f"  Created {count} SHARES_TAG relationships")

        # 3. Link by knowledge type
        print("\nCreating SAME_TYPE relationships for CODE examples...")
        result = session.run(
            """
            MATCH (k1:Knowledge {knowledge_type: 'CODE'})
            MATCH (k2:Knowledge {knowledge_type: 'CODE'})
            WHERE k1.direct_ingestion = true
              AND k2.direct_ingestion = true
              AND k1.knowledge_id < k2.knowledge_id
              AND k1.source CONTAINS 'openai'
              AND k2.source CONTAINS 'openai'
            WITH k1, k2
            LIMIT 50
            MERGE (k1)-[:SAME_TYPE {type: 'CODE'}]->(k2)
            RETURN count(*) as count
        """
        )
        count = result.single()["count"]
        print(f"  Created {count} SAME_TYPE relationships")

        # 4. Create SOURCE_FILE nodes and link chunks to them
        print("\nCreating SOURCE_FILE nodes...")
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.direct_ingestion = true
            WITH DISTINCT
                CASE
                    WHEN k.source CONTAINS '[part'
                    THEN trim(split(k.source, '[part')[0])
                    WHEN k.source CONTAINS '(chunk'
                    THEN trim(split(k.source, '(chunk')[0])
                    ELSE k.source
                END as file_path
            MERGE (s:SourceFile {path: file_path})
            RETURN count(s) as count
        """
        )
        count = result.single()["count"]
        print(f"  Created {count} SourceFile nodes")

        # Link Knowledge to SourceFile
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.direct_ingestion = true
            WITH k,
                CASE
                    WHEN k.source CONTAINS '[part'
                    THEN trim(split(k.source, '[part')[0])
                    WHEN k.source CONTAINS '(chunk'
                    THEN trim(split(k.source, '(chunk')[0])
                    ELSE k.source
                END as file_path
            MATCH (s:SourceFile {path: file_path})
            MERGE (s)-[:CONTAINS]->(k)
            RETURN count(*) as count
        """
        )
        count = result.single()["count"]
        print(f"  Created {count} CONTAINS relationships")

        # 5. Summary
        print("\n" + "=" * 60)
        print("Relationship creation complete!")

        result = session.run(
            """
            MATCH (k:Knowledge)-[r]-(k2:Knowledge)
            WHERE k.direct_ingestion = true
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """
        )

        print("\nKnowledge-to-Knowledge relationships:")
        for record in result:
            print(f"  {record['rel_type']}: {record['count']}")

        result = session.run(
            """
            MATCH (s:SourceFile)-[r:CONTAINS]->(k:Knowledge)
            RETURN count(DISTINCT s) as files, count(r) as relationships
        """
        )
        record = result.single()
        print(f"\nSourceFile nodes: {record['files']}")
        print(f"SourceFile->Knowledge relationships: {record['relationships']}")

    driver.close()


if __name__ == "__main__":
    create_knowledge_relationships()
