#!/usr/bin/env python3
"""
Intelligent Database Migration Script
Migrates foundational memories from legacy core_memory to new agent_memory schema
"""

import json
import sys
from datetime import datetime
from arango import ArangoClient
from arango.exceptions import DocumentInsertError


class DatabaseMigrator:
    def __init__(self):
        self.client = ArangoClient(hosts="http://127.0.0.1:8531")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_production_password"
        )
        self.migrated_count = 0
        self.failed_migrations = []

    def analyze_legacy_data(self):
        """Analyze what needs to be migrated"""
        print("=== MIGRATION ANALYSIS ===")

        # Count foundational memories
        foundational_query = """
        FOR doc IN core_memory 
        FILTER doc.foundational == true 
        COLLECT WITH COUNT INTO total 
        RETURN total
        """
        foundational_count = list(self.db.aql.execute(foundational_query))[0]

        # Count already migrated
        migrated_query = """
        FOR doc IN agent_memory 
        COLLECT WITH COUNT INTO total 
        RETURN total
        """
        migrated_count = list(self.db.aql.execute(migrated_query))[0]

        remaining = foundational_count - migrated_count

        print(f"Foundational memories: {foundational_count}")
        print(f"Already migrated: {migrated_count}")
        print(f"Remaining to migrate: {remaining}")

        return remaining

    def get_legacy_memories_batch(self, offset=0, limit=10):
        """Get batch of legacy memories to migrate"""
        query = """
        FOR doc IN core_memory 
        FILTER doc.foundational == true
        FILTER doc._key NOT IN (
            FOR migrated IN agent_memory
            FILTER migrated.legacy_id != null
            RETURN SPLIT(migrated.legacy_id, '/')[1]
        )
        SORT doc.created DESC 
        LIMIT @offset, @limit
        RETURN doc
        """

        return list(
            self.db.aql.execute(query, bind_vars={"offset": offset, "limit": limit})
        )

    def transform_memory_to_new_schema(self, legacy_memory):
        """Transform legacy memory to new schema format"""

        # Determine memory type based on legacy data
        memory_type = "operational"  # default
        if legacy_memory.get("type"):
            if (
                "behavioral" in legacy_memory["type"]
                or "correction" in legacy_memory["type"]
            ):
                memory_type = "procedural"
            elif (
                "technical" in legacy_memory["type"]
                or "operational" in legacy_memory["type"]
            ):
                memory_type = "operational"
            elif "learning" in legacy_memory["type"]:
                memory_type = "semantic"

        # Determine tier
        tier = "essential" if legacy_memory.get("foundational") else "operational"

        # Extract content from various legacy fields
        content_parts = []
        for field in [
            "problem_resolved",
            "user_correction",
            "violation_analysis",
            "required_behavior",
            "solution_approach",
            "lesson",
            "summary",
        ]:
            if field in legacy_memory and legacy_memory[field]:
                if isinstance(legacy_memory[field], dict):
                    content_parts.append(f"{field}: {json.dumps(legacy_memory[field])}")
                else:
                    content_parts.append(f"{field}: {legacy_memory[field]}")

        content = (
            "; ".join(content_parts)
            if content_parts
            else legacy_memory.get("title", "")
        )

        # Extract tags from content and type
        tags = []
        if legacy_memory.get("type"):
            tags.extend(legacy_memory["type"].split("_"))

        # Add contextual tags
        content_lower = content.lower()
        if "database" in content_lower:
            tags.append("database")
        if "validation" in content_lower:
            tags.append("validation")
        if "behavior" in content_lower:
            tags.append("behavioral")
        if "autonomous" in content_lower:
            tags.append("autonomy")

        # Create new schema document
        new_memory = {
            "type": memory_type,
            "tier": tier,
            "title": legacy_memory.get("title", "Untitled Memory"),
            "content": content,
            "context": f"Migrated from legacy core_memory: {legacy_memory.get('type', 'unknown_type')}",
            "tags": list(set(tags)),  # remove duplicates
            "foundational": legacy_memory.get("foundational", False),
            "confidence": 1.0 if legacy_memory.get("foundational") else 0.8,
            "source": "migration",
            "created": legacy_memory.get("created", datetime.now().isoformat() + "Z"),
            "last_accessed": datetime.now().isoformat() + "Z",
            "access_count": 1,
            "validation_status": "validated"
            if legacy_memory.get("foundational")
            else "pending",
            "superseded_by": None,
            "behavioral_requirement": legacy_memory.get("required_behavior", ""),
            "legacy_id": legacy_memory["_id"],
        }

        return new_memory

    def migrate_batch(self, batch_size=10):
        """Migrate a batch of memories"""
        batch = self.get_legacy_memories_batch(
            offset=self.migrated_count, limit=batch_size
        )

        if not batch:
            print("No more memories to migrate")
            return False

        print(f"\nMigrating batch of {len(batch)} memories...")

        for legacy_memory in batch:
            try:
                new_memory = self.transform_memory_to_new_schema(legacy_memory)

                # Insert into new schema
                result = self.db.collection("agent_memory").insert(new_memory)

                if result.get("_id"):
                    self.migrated_count += 1
                    print(f"✓ Migrated: {new_memory['title'][:50]}...")
                else:
                    self.failed_migrations.append(
                        {
                            "legacy_id": legacy_memory["_id"],
                            "title": legacy_memory.get("title", "Unknown"),
                            "error": "No _id in result",
                        }
                    )

            except Exception as e:
                self.failed_migrations.append(
                    {
                        "legacy_id": legacy_memory["_id"],
                        "title": legacy_memory.get("title", "Unknown"),
                        "error": str(e),
                    }
                )
                print(
                    f"✗ Failed: {legacy_memory.get('title', 'Unknown')[:50]}... - {str(e)}"
                )

        return True

    def validate_migration(self):
        """Validate migration results"""
        print("\n=== MIGRATION VALIDATION ===")

        # Count migrated memories
        migrated_query = """
        FOR doc IN agent_memory 
        COLLECT WITH COUNT INTO total 
        RETURN total
        """
        migrated_total = list(self.db.aql.execute(migrated_query))[0]

        # Count foundational migrated
        foundational_migrated_query = """
        FOR doc IN agent_memory 
        FILTER doc.foundational == true
        COLLECT WITH COUNT INTO total 
        RETURN total
        """
        foundational_migrated = list(self.db.aql.execute(foundational_migrated_query))[
            0
        ]

        print(f"Total migrated memories: {migrated_total}")
        print(f"Foundational migrated: {foundational_migrated}")
        print(f"Failed migrations: {len(self.failed_migrations)}")

        if self.failed_migrations:
            print("\nFailed migrations:")
            for failure in self.failed_migrations:
                print(f"  - {failure['title'][:30]}...: {failure['error']}")

        return len(self.failed_migrations) == 0

    def run_migration(self, batch_size=10):
        """Run complete migration process"""
        print("Starting intelligent database migration...")

        # Analyze scope
        remaining = self.analyze_legacy_data()

        if remaining == 0:
            print("No memories to migrate!")
            return True

        # Migrate in batches
        while self.migrate_batch(batch_size):
            print(f"Progress: {self.migrated_count} migrated")

        # Validate results
        success = self.validate_migration()

        print(f"\n=== MIGRATION COMPLETE ===")
        print(f"Successfully migrated: {self.migrated_count}")
        print(f"Migration success: {success}")

        return success


if __name__ == "__main__":
    migrator = DatabaseMigrator()

    # Run with small batch size for safety
    success = migrator.run_migration(batch_size=5)

    if success:
        print("✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("✗ Migration completed with errors")
        sys.exit(1)
