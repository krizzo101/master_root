#!/usr/bin/env python3
"""
Migration script to add deprecated=false property to existing Knowledge nodes.

This fixes the Neo4j warnings about missing 'deprecated' property.
"""

import os
import sys

from neo4j import GraphDatabase


def migrate_deprecated_property():
    """Add deprecated=false to all existing Knowledge nodes that don't have it"""

    # Get Neo4j connection details from environment
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    print(f"Connecting to Neo4j at {uri}")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session() as session:
            # Check how many Knowledge nodes exist without deprecated property
            check_query = """
            MATCH (k:Knowledge)
            WHERE k.deprecated IS NULL
            RETURN count(k) as count
            """
            result = session.run(check_query)
            count = result.single()["count"]
            print(f"Found {count} Knowledge nodes missing deprecated property")

            if count == 0:
                print(
                    "No migration needed - all nodes already have deprecated property"
                )
                return

            # Add deprecated=false to all Knowledge nodes that don't have it
            migration_query = """
            MATCH (k:Knowledge)
            WHERE k.deprecated IS NULL
            SET k.deprecated = false
            RETURN count(k) as updated_count
            """

            print("Running migration...")
            result = session.run(migration_query)
            updated_count = result.single()["updated_count"]
            print(f"Successfully updated {updated_count} Knowledge nodes")

            # Verify the migration
            verify_query = """
            MATCH (k:Knowledge)
            WHERE k.deprecated IS NULL
            RETURN count(k) as remaining_count
            """
            result = session.run(verify_query)
            remaining = result.single()["remaining_count"]

            if remaining == 0:
                print(
                    "✅ Migration completed successfully - no nodes missing deprecated property"
                )
            else:
                print(
                    f"⚠️  Migration incomplete - {remaining} nodes still missing deprecated property"
                )

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

    finally:
        driver.close()


if __name__ == "__main__":
    migrate_deprecated_property()
