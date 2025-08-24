#!/usr/bin/env python3
"""
KB Standards Migration Script

Migrates existing knowledge entries to follow new standardized patterns:
- Adds content prefixes based on type and content analysis
- Standardizes tags into categories
- Ensures summaries exist
- Normalizes confidence scores
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, "/home/opsvi/master_root")

from neo4j import GraphDatabase

from apps.knowledge_system.knowledge_nano_agent import KnowledgeNanoAgent


class KBStandardsMigrator:
    """Migrates existing KB entries to new standards"""

    # Content prefix mappings based on patterns
    PREFIX_PATTERNS = {
        "MEMENTO NOTE:": [
            r"remember",
            r"note to self",
            r"important to note",
            r"personal reminder",
        ],
        "SYSTEM TRUTH:": [
            r"verified",
            r"confirmed",
            r"system fact",
            r"architecture truth",
        ],
        "BUG DISCOVERED:": [
            r"bug found",
            r"error discovered",
            r"problem:",
            r"issue:",
            r"broken",
        ],
        "FIX APPLIED:": [
            r"fix:",
            r"solution:",
            r"resolved:",
            r"fixed by",
            r"workaround:",
        ],
        "SESSION CONTEXT:": [
            r"session",
            r"current context",
            r"working on",
            r"task context",
        ],
        "GLOBAL OPERATIONAL INSTRUCTIONS": [
            r"global",
            r"operational",
            r"instructions",
            r"mandatory",
            r"protocol",
        ],
        "OPTIMIZATION OPPORTUNITY:": [
            r"optimize",
            r"improve",
            r"enhancement",
            r"could be better",
        ],
        "PATTERN OBSERVED:": [
            r"pattern",
            r"recurring",
            r"noticed",
            r"trend",
            r"observation",
        ],
        "PROJECT INTELLIGENCE:": [
            r"project analysis",
            r"project structure",
            r"project map",
            r"collector",
        ],
    }

    # Standard tag categories
    PROJECT_TAGS = ["accf", "knowledge-system", "project-intelligence", "master-root"]
    TECH_TAGS = [
        "python",
        "typescript",
        "javascript",
        "neo4j",
        "mcp",
        "fastmcp",
        "openai",
        "claude",
        "gpt-5",
        "docker",
        "git",
    ]
    TYPE_TAGS = [
        "bug",
        "fix",
        "architecture",
        "critical",
        "session",
        "workflow",
        "error",
        "solution",
    ]
    SOURCE_TAGS = [
        "source-code",
        "documentation",
        "analysis",
        "user-input",
        "research",
        "testing",
    ]

    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.nano_agent = KnowledgeNanoAgent()
        self.stats = {
            "total": 0,
            "migrated": 0,
            "prefixed": 0,
            "tagged": 0,
            "summarized": 0,
            "confidence_normalized": 0,
            "errors": 0,
        }

    def detect_prefix(self, content: str, knowledge_type: str) -> Optional[str]:
        """Detect appropriate prefix for content"""
        if not content:
            return None

        # Check if already has a prefix
        for prefix in self.PREFIX_PATTERNS.keys():
            if content.startswith(prefix):
                return None  # Already prefixed

        content_lower = content.lower()

        # Check patterns to determine prefix
        for prefix, patterns in self.PREFIX_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return prefix

        # Type-based defaults
        type_prefix_map = {
            "ERROR_SOLUTION": "FIX APPLIED:",
            "WORKFLOW": "WORKFLOW:",
            "CONTEXT_PATTERN": "SESSION CONTEXT:",
            "CODE_PATTERN": "CODE PATTERN:",
            "TOOL_USAGE": "TOOL USAGE:",
            "USER_PREFERENCE": "PREFERENCE:",
            "PROJECT_INTELLIGENCE": "PROJECT INTELLIGENCE:",
        }

        return type_prefix_map.get(knowledge_type, None)

    def standardize_tags(self, existing_tags: List[str], content: str) -> List[str]:
        """Standardize and enhance tags"""
        if not existing_tags:
            existing_tags = []

        standardized = set(existing_tags)
        content_lower = content.lower() if content else ""

        # Add project tags
        for tag in self.PROJECT_TAGS:
            if tag in content_lower:
                standardized.add(tag)

        # Add tech tags
        for tag in self.TECH_TAGS:
            if tag in content_lower:
                standardized.add(tag)

        # Add type tags based on content
        if "error" in content_lower or "bug" in content_lower:
            standardized.add("bug")
        if "fix" in content_lower or "solution" in content_lower:
            standardized.add("fix")
        if "workflow" in content_lower or "process" in content_lower:
            standardized.add("workflow")

        # Ensure at least some tags
        if len(standardized) < 3:
            standardized.add("legacy")  # Mark as pre-migration
            standardized.add("needs-review")

        return list(standardized)

    def normalize_confidence(self, confidence: Optional[float], content: str) -> float:
        """Normalize confidence score based on content indicators"""
        if confidence is not None and 0.0 <= confidence <= 1.0:
            return confidence

        # Analyze content for confidence indicators
        content_lower = content.lower() if content else ""

        if any(
            word in content_lower
            for word in ["verified", "tested", "confirmed", "production"]
        ):
            return 0.9
        elif any(word in content_lower for word in ["solution", "fixed", "resolved"]):
            return 0.8
        elif any(
            word in content_lower for word in ["pattern", "observation", "noticed"]
        ):
            return 0.6
        elif any(
            word in content_lower for word in ["experimental", "uncertain", "maybe"]
        ):
            return 0.4
        else:
            return 0.5  # Default middle confidence

    def generate_summary(self, content: str, knowledge_type: str) -> str:
        """Generate summary if missing"""
        if not content:
            return f"Legacy {knowledge_type} entry"

        # Take first 100 chars and clean up
        summary = content[:100].replace("\n", " ").strip()

        # Remove prefix if present
        for prefix in self.PREFIX_PATTERNS.keys():
            if summary.startswith(prefix):
                summary = summary[len(prefix) :].strip()

        # Ensure it ends properly
        if len(content) > 100:
            summary = summary.rstrip(".,;:") + "..."

        return summary

    async def migrate_entry(self, knowledge_id: str, entry: Dict) -> bool:
        """Migrate a single knowledge entry"""
        try:
            updates = {}
            content = entry.get("content", "")
            knowledge_type = entry.get("knowledge_type") or entry.get(
                "type", "CONTEXT_PATTERN"
            )

            # Add prefix if needed
            prefix = self.detect_prefix(content, knowledge_type)
            if prefix and content:
                updates["content"] = f"{prefix} {content}"
                self.stats["prefixed"] += 1

            # Standardize tags
            existing_tags = entry.get("tags", [])
            new_tags = self.standardize_tags(existing_tags, content)
            if set(new_tags) != set(existing_tags):
                updates["tags"] = new_tags
                self.stats["tagged"] += 1

            # Generate summary if missing
            if not entry.get("summary"):
                updates["summary"] = self.generate_summary(content, knowledge_type)
                self.stats["summarized"] += 1

            # Normalize confidence
            old_confidence = entry.get("confidence") or entry.get("confidence_score")
            new_confidence = self.normalize_confidence(old_confidence, content)
            if old_confidence != new_confidence:
                updates["confidence"] = new_confidence
                self.stats["confidence_normalized"] += 1

            # Apply updates if any
            if updates:
                with self.driver.session() as session:
                    # Build SET clause
                    set_clauses = []
                    params = {"kid": knowledge_id}

                    for key, value in updates.items():
                        set_clauses.append(f"k.{key} = ${key}")
                        params[key] = value

                    if set_clauses:
                        query = f"""
                        MATCH (k:Knowledge {{knowledge_id: $kid}})
                        SET {', '.join(set_clauses)}, k.migrated_at = datetime()
                        RETURN k.knowledge_id as id
                        """

                        result = session.run(query, params)
                        if result.single():
                            self.stats["migrated"] += 1
                            return True

            return False

        except Exception as e:
            print(f"Error migrating {knowledge_id}: {e}")
            self.stats["errors"] += 1
            return False

    async def migrate_all(self, batch_size: int = 100):
        """Migrate all knowledge entries"""
        print("Starting KB Standards Migration...")
        print("=" * 60)

        # Get all knowledge entries
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.migrated_at IS NULL
                RETURN k.knowledge_id as id,
                       k.content as content,
                       k.knowledge_type as knowledge_type,
                       k.type as type,
                       k.tags as tags,
                       k.summary as summary,
                       k.confidence as confidence,
                       k.confidence_score as confidence_score
                ORDER BY k.created_at DESC
            """
            )

            entries = list(result)
            self.stats["total"] = len(entries)

        print(f"Found {self.stats['total']} entries to migrate")

        # Process in batches
        for i in range(0, len(entries), batch_size):
            batch = entries[i : i + batch_size]
            print(
                f"\nProcessing batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, len(entries))})"
            )

            tasks = []
            for entry in batch:
                task = self.migrate_entry(
                    entry["id"],
                    {
                        "content": entry["content"],
                        "knowledge_type": entry["knowledge_type"] or entry["type"],
                        "tags": entry["tags"],
                        "summary": entry["summary"],
                        "confidence": entry["confidence"],
                        "confidence_score": entry["confidence_score"],
                    },
                )
                tasks.append(task)

            await asyncio.gather(*tasks)
            print(f"  Migrated: {self.stats['migrated']}/{self.stats['total']}")

        # Print final stats
        print("\n" + "=" * 60)
        print("Migration Complete!")
        print(f"Total entries: {self.stats['total']}")
        print(f"Migrated: {self.stats['migrated']}")
        print(f"  - Added prefixes: {self.stats['prefixed']}")
        print(f"  - Standardized tags: {self.stats['tagged']}")
        print(f"  - Generated summaries: {self.stats['summarized']}")
        print(f"  - Normalized confidence: {self.stats['confidence_normalized']}")
        print(f"Errors: {self.stats['errors']}")

        # Mark migration complete
        with self.driver.session() as session:
            session.run(
                """
                CREATE (m:Metadata {
                    type: 'migration',
                    name: 'kb_standards_v1',
                    completed_at: datetime(),
                    stats: $stats
                })
            """,
                {"stats": json.dumps(self.stats)},
            )


async def main():
    """Run the migration"""
    migrator = KBStandardsMigrator()
    await migrator.migrate_all()


if __name__ == "__main__":
    asyncio.run(main())
