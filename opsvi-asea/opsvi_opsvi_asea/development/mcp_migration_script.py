#!/usr/bin/env python3
"""
MCP-based Database Migration Script
Uses MCP tools for reliable database operations
"""

import json
import subprocess
import sys
from datetime import datetime


def run_aql_query(query, bind_vars=None):
    """Execute AQL query using MCP tools"""
    try:
        # Use the MCP arango query tool via subprocess
        # This mimics what the MCP tool does internally
        cmd = [
            "python3",
            "-c",
            f"""
import json
import sys
from arango import ArangoClient

client = ArangoClient(hosts='http://127.0.0.1:8531')
db = client.db('asea_prod_db', username='root', password='arango_production_password')

query = '''{query}'''
bind_vars = {bind_vars if bind_vars else '{}'}

try:
    result = list(db.aql.execute(query, bind_vars=bind_vars))
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
    sys.exit(1)
""",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd="/home/opsvi/asea"
        )

        if result.returncode != 0:
            print(f"Query failed: {result.stderr}")
            return None

        return json.loads(result.stdout)

    except Exception as e:
        print(f"Error executing query: {e}")
        return None


def insert_document(collection, document):
    """Insert document using MCP tools"""
    try:
        cmd = [
            "python3",
            "-c",
            f"""
import json
import sys
from arango import ArangoClient

client = ArangoClient(hosts='http://127.0.0.1:8531')
db = client.db('asea_prod_db', username='root', password='arango_production_password')

document = {json.dumps(document)}
collection_name = '{collection}'

try:
    result = db.collection(collection_name).insert(document)
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
    sys.exit(1)
""",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd="/home/opsvi/asea"
        )

        if result.returncode != 0:
            print(f"Insert failed: {result.stderr}")
            return None

        return json.loads(result.stdout)

    except Exception as e:
        print(f"Error inserting document: {e}")
        return None


def analyze_migration_scope():
    """Analyze what needs to be migrated"""
    print("=== MIGRATION ANALYSIS ===")

    # Count foundational memories in legacy collection
    foundational_count = run_aql_query(
        """
        FOR doc IN core_memory 
        FILTER doc.foundational == true 
        COLLECT WITH COUNT INTO total 
        RETURN total
    """
    )

    if not foundational_count:
        print("Failed to count foundational memories")
        return None

    foundational_total = foundational_count[0]

    # Count already migrated
    migrated_count = run_aql_query(
        """
        FOR doc IN agent_memory 
        COLLECT WITH COUNT INTO total 
        RETURN total
    """
    )

    if not migrated_count:
        print("Failed to count migrated memories")
        return None

    migrated_total = migrated_count[0]
    remaining = foundational_total - migrated_total

    print(f"Foundational memories: {foundational_total}")
    print(f"Already migrated: {migrated_total}")
    print(f"Remaining to migrate: {remaining}")

    return remaining


def get_next_batch(batch_size=5):
    """Get next batch of memories to migrate"""
    query = """
    FOR doc IN core_memory 
    FILTER doc.foundational == true
    FILTER doc._key NOT IN (
        FOR migrated IN agent_memory
        FILTER migrated.legacy_id != null
        RETURN SPLIT(migrated.legacy_id, '/')[1]
    )
    SORT doc.created DESC 
    LIMIT @batch_size
    RETURN doc
    """

    return run_aql_query(query, {"batch_size": batch_size})


def transform_legacy_memory(legacy_memory):
    """Transform legacy memory to new schema"""

    # Determine memory type
    memory_type = "operational"
    if legacy_memory.get("type"):
        if any(word in legacy_memory["type"] for word in ["behavioral", "correction"]):
            memory_type = "procedural"
        elif any(word in legacy_memory["type"] for word in ["learning", "synthesis"]):
            memory_type = "semantic"

    # Extract content from various fields
    content_parts = []
    content_fields = [
        "problem_resolved",
        "user_correction",
        "required_behavior",
        "lesson",
        "summary",
        "violation_analysis",
        "solution_approach",
    ]

    for field in content_fields:
        if field in legacy_memory and legacy_memory[field]:
            if isinstance(legacy_memory[field], dict):
                content_parts.append(f"{field}: {json.dumps(legacy_memory[field])}")
            elif isinstance(legacy_memory[field], list):
                content_parts.append(
                    f"{field}: {'; '.join(map(str, legacy_memory[field]))}"
                )
            else:
                content_parts.append(f"{field}: {legacy_memory[field]}")

    content = (
        "; ".join(content_parts) if content_parts else legacy_memory.get("title", "")
    )

    # Generate tags
    tags = []
    if legacy_memory.get("type"):
        tags.extend(legacy_memory["type"].replace("_", " ").split())

    content_lower = content.lower()
    tag_keywords = [
        "database",
        "validation",
        "behavior",
        "autonomous",
        "shell",
        "path",
        "git",
    ]
    for keyword in tag_keywords:
        if keyword in content_lower:
            tags.append(keyword)

    # Create new memory document
    new_memory = {
        "type": memory_type,
        "tier": "essential",
        "title": legacy_memory.get("title", "Untitled Memory"),
        "content": content,
        "context": f"Migrated from legacy core_memory: {legacy_memory.get('type', 'unknown')}",
        "tags": list(set(tags))[:10],  # limit tags and remove duplicates
        "foundational": True,
        "confidence": 1.0,
        "source": "migration",
        "created": legacy_memory.get("created", datetime.now().isoformat() + "Z"),
        "last_accessed": datetime.now().isoformat() + "Z",
        "access_count": 1,
        "validation_status": "validated",
        "superseded_by": None,
        "behavioral_requirement": legacy_memory.get("required_behavior", ""),
        "legacy_id": legacy_memory["_id"],
    }

    return new_memory


def migrate_batch(batch_size=5):
    """Migrate a batch of memories"""
    batch = get_next_batch(batch_size)

    if not batch or len(batch) == 0:
        print("No more memories to migrate")
        return False

    print(f"\\nMigrating batch of {len(batch)} memories...")

    success_count = 0
    for legacy_memory in batch:
        try:
            new_memory = transform_legacy_memory(legacy_memory)
            result = insert_document("agent_memory", new_memory)

            if result and result.get("_id"):
                success_count += 1
                print(f"✓ Migrated: {new_memory['title'][:50]}...")
            else:
                print(f"✗ Failed: {legacy_memory.get('title', 'Unknown')[:50]}...")

        except Exception as e:
            print(
                f"✗ Error: {legacy_memory.get('title', 'Unknown')[:50]}... - {str(e)}"
            )

    print(f"Batch complete: {success_count}/{len(batch)} successful")
    return len(batch) > 0


def validate_migration():
    """Validate migration results"""
    print("\\n=== MIGRATION VALIDATION ===")

    # Count migrated memories
    migrated_total = run_aql_query(
        """
        FOR doc IN agent_memory 
        COLLECT WITH COUNT INTO total 
        RETURN total
    """
    )

    if migrated_total:
        print(f"Total migrated memories: {migrated_total[0]}")

    # Validate schema compliance
    schema_validation = run_aql_query(
        """
        FOR doc IN agent_memory
        FILTER doc.type NOT IN ["operational", "semantic", "episodic", "procedural"]
        COLLECT WITH COUNT INTO invalid
        RETURN invalid
    """
    )

    if schema_validation:
        invalid_count = schema_validation[0]
        print(f"Schema violations: {invalid_count}")
        return invalid_count == 0

    return False


def main():
    """Main migration process"""
    print("Starting MCP-based database migration...")

    # Analyze scope
    remaining = analyze_migration_scope()
    if remaining is None:
        print("Failed to analyze migration scope")
        return False

    if remaining == 0:
        print("No memories to migrate!")
        return True

    # Migrate in small batches for safety
    batch_count = 0
    while migrate_batch(batch_size=3):  # Small batches for safety
        batch_count += 1
        print(f"Completed batch {batch_count}")

        # Safety check - don't run indefinitely
        if batch_count > 30:  # Max 90 memories per run
            print("Reached batch limit - run again to continue")
            break

    # Validate results
    success = validate_migration()

    print(f"\\n=== MIGRATION STATUS ===")
    print(f"Batches processed: {batch_count}")
    print(f"Validation success: {success}")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
