#!/usr/bin/env python3
"""
Intelligent KB Enrichment System

Instead of rigid rules, this system ENRICHES existing knowledge by:
1. Generating intelligent summaries using AI
2. Detecting relationships between entries
3. Scoring quality based on actual usage
4. Marking deprecated/critical entries only where needed
5. Building a knowledge graph for better discovery

This respects the organic nature of the KB while adding intelligence.
"""

import asyncio
import hashlib
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, "/home/opsvi/master_root")

from neo4j import GraphDatabase
from openai import AsyncOpenAI


class IntelligentKBEnricher:
    """Enriches KB with intelligence rather than rigid structure"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.client = AsyncOpenAI()
        self.stats = defaultdict(int)

        # For similarity detection
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")

    async def generate_smart_summary(self, content: str, knowledge_type: str) -> str:
        """Generate intelligent summary using GPT-5-nano"""
        if not content:
            return f"Empty {knowledge_type} entry"

        # Already has a good summary pattern?
        first_line = content.split("\n")[0]
        if len(first_line) < 100 and not first_line.startswith("File:"):
            return first_line

        try:
            response = await self.client.responses.create(
                model="gpt-5-nano",
                input=f"Content: {content[:500]}",
                instructions="""Create a one-line summary (max 100 chars) that:
1. Captures the MAIN point/action
2. Includes key context (tool/file/error if relevant)
3. Is searchable and specific
4. No fluff words

Examples:
- "Fixed authentication loop in ACCF by adding session validation"
- "MetaGPT roles require use_fixed_sop=True to process messages"
- "Knowledge system uses Neo4j with 3000+ entries for semantic search"

Return ONLY the summary line.""",
            )

            # Extract text from response
            if response and hasattr(response, "output"):
                for output in response.output:
                    if hasattr(output, "content") and output.content:
                        for content_item in output.content:
                            if hasattr(content_item, "text"):
                                summary = content_item.text.strip()
                                return summary[:100] if len(summary) > 100 else summary

        except Exception as e:
            print(f"Summary generation failed: {e}")

        # Fallback to simple truncation
        clean = content.replace("\n", " ").strip()[:97] + "..."
        return clean

    def calculate_quality_score(self, entry: Dict) -> float:
        """Calculate quality score based on multiple factors"""
        score = 0.5  # Base score

        # Usage-based scoring (most important)
        usage_count = entry.get("usage_count") or 0
        success_rate = entry.get("success_rate") or 0.0

        if usage_count > 0:
            # Highly used = likely valuable
            score += min(0.2, usage_count * 0.01)  # Up to +0.2 for usage

            # High success rate = actually works
            score += success_rate * 0.2  # Up to +0.2 for success

        # Content quality indicators
        content = entry.get("content", "")
        if content:
            # Has code blocks
            if "```" in content or "def " in content or "class " in content:
                score += 0.05

            # Has specific details (paths, commands, etc)
            if "/" in content or "git " in content or "python " in content:
                score += 0.05

            # Well-structured (has sections/bullets)
            if "\n- " in content or "\n1." in content or "##" in content:
                score += 0.05

        # Has relationships
        if entry.get("supersedes") or entry.get("related_to"):
            score += 0.05

        # Recency bonus (newer might be more relevant)
        created = entry.get("created_at")
        if created:
            # Handle Neo4j DateTime objects
            if hasattr(created, "to_native"):
                created = created.to_native()
            # Make datetime timezone-aware
            now = datetime.now(timezone.utc) if created.tzinfo else datetime.now()
            age_days = (now - created).days
            if age_days < 7:
                score += 0.1
            elif age_days < 30:
                score += 0.05

        return min(1.0, score)  # Cap at 1.0

    def detect_relationships(
        self, entries: List[Dict]
    ) -> Dict[str, List[Tuple[str, str, float]]]:
        """Detect relationships between knowledge entries"""
        relationships = defaultdict(list)

        # Prepare content for vectorization
        contents = []
        valid_entries = []

        for entry in entries:
            content = entry.get("content", "")
            if content and entry.get("id"):
                contents.append(content)
                valid_entries.append(entry)

        if len(contents) < 2:
            return relationships

        # Compute TF-IDF vectors
        try:
            tfidf_matrix = self.vectorizer.fit_transform(contents)

            # Compute pairwise similarities
            similarities = cosine_similarity(tfidf_matrix)

            # Find related entries (similarity > 0.3 but not identical)
            for i in range(len(valid_entries)):
                for j in range(i + 1, len(valid_entries)):
                    sim = similarities[i][j]

                    if 0.3 < sim < 0.95:  # Related but not duplicate
                        id1 = valid_entries[i]["id"]
                        id2 = valid_entries[j]["id"]

                        relationships[id1].append((id2, "RELATED_TO", sim))
                        relationships[id2].append((id1, "RELATED_TO", sim))

                    elif sim >= 0.95:  # Likely duplicate or superseded
                        # The newer one supersedes the older
                        created1 = valid_entries[i].get("created_at", datetime.min)
                        created2 = valid_entries[j].get("created_at", datetime.min)

                        # Handle Neo4j DateTime objects
                        if hasattr(created1, "to_native"):
                            created1 = created1.to_native()
                        if hasattr(created2, "to_native"):
                            created2 = created2.to_native()

                        if created1 > created2:
                            relationships[valid_entries[i]["id"]].append(
                                (valid_entries[j]["id"], "SUPERSEDES", sim)
                            )
                        else:
                            relationships[valid_entries[j]["id"]].append(
                                (valid_entries[i]["id"], "SUPERSEDES", sim)
                            )

        except Exception as e:
            print(f"Relationship detection failed: {e}")

        return relationships

    def identify_critical_entries(self, entry: Dict) -> bool:
        """Identify if an entry is critical and needs CRITICAL: prefix"""
        content = entry.get("content") or ""
        content = content.lower() if content else ""

        critical_indicators = [
            "mandatory",
            "critical",
            "must ",
            "never ",
            "always ",
            "required",
            "forbidden",
            "global operational",
            "breaking change",
            "security",
            "credential",
        ]

        return any(indicator in content for indicator in critical_indicators)

    def identify_deprecated_entries(self, entry: Dict, relationships: Dict) -> bool:
        """Identify if an entry is deprecated"""
        # Already marked as deprecated
        if entry.get("deprecated"):
            return True

        # Has been superseded by another entry
        entry_id = entry.get("id")
        if entry_id and entry_id in relationships:
            for related_id, rel_type, _ in relationships[entry_id]:
                if rel_type == "SUPERSEDES":
                    return True

        # Old with very low success rate
        created = entry.get("created_at")
        if created:
            # Handle Neo4j DateTime objects
            if hasattr(created, "to_native"):
                created = created.to_native()
            # Make datetime timezone-aware
            now = datetime.now(timezone.utc) if created.tzinfo else datetime.now()
            age_days = (now - created).days
            success_rate = entry.get("success_rate", 1.0)

            if age_days > 90 and success_rate < 0.3:
                return True

        return False

    async def enrich_entry(self, entry: Dict, relationships: Dict) -> Dict[str, any]:
        """Enrich a single knowledge entry"""
        updates = {}
        entry_id = entry.get("id")

        # 1. Generate summary if missing
        if not entry.get("summary"):
            summary = await self.generate_smart_summary(
                entry.get("content", ""), entry.get("knowledge_type", "GENERAL")
            )
            updates["summary"] = summary
            self.stats["summaries_generated"] += 1

        # 2. Calculate quality score
        quality = self.calculate_quality_score(entry)
        old_confidence = entry.get("confidence") or 0.5
        if abs(quality - old_confidence) > 0.1:
            updates["confidence"] = quality
            self.stats["quality_scored"] += 1

        # 3. Add minimal prefixes only where needed
        content = entry.get("content", "")

        # Add CRITICAL: prefix
        if self.identify_critical_entries(entry) and not content.startswith(
            "CRITICAL:"
        ):
            updates["content"] = f"CRITICAL: {content}"
            self.stats["critical_marked"] += 1

        # Add DEPRECATED: prefix
        elif self.identify_deprecated_entries(
            entry, relationships
        ) and not content.startswith("DEPRECATED:"):
            updates["content"] = f"DEPRECATED: {content}"
            updates["deprecated"] = True
            updates["deprecated_at"] = datetime.now()
            self.stats["deprecated_marked"] += 1

        # 4. Enhance tags intelligently
        existing_tags = entry.get("tags") or []
        existing_tags = set(existing_tags) if existing_tags else set()
        enhanced_tags = existing_tags.copy()

        # Add quality indicators
        if quality > 0.8:
            enhanced_tags.add("high-quality")
        elif quality < 0.3:
            enhanced_tags.add("needs-review")

        # Add usage indicators
        usage = entry.get("usage_count") or 0
        if usage > 10:
            enhanced_tags.add("frequently-used")

        # Add recency
        created = entry.get("created_at")
        if created:
            # Handle Neo4j DateTime objects
            if hasattr(created, "to_native"):
                created = created.to_native()
            # Make datetime timezone-aware
            now = datetime.now(timezone.utc) if created.tzinfo else datetime.now()
            age_days = (now - created).days
            if age_days < 7:
                enhanced_tags.add("recent")
            elif age_days > 180:
                enhanced_tags.add("old")

        if enhanced_tags != existing_tags:
            updates["tags"] = list(enhanced_tags)
            self.stats["tags_enhanced"] += 1

        return updates

    async def enrich_knowledge_base(
        self, batch_size: int = 100, max_entries: int = None
    ):
        """Main enrichment process"""
        print("Starting Intelligent KB Enrichment...")
        print("=" * 60)

        # Get all knowledge entries
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge)
                RETURN k.knowledge_id as id,
                       k.content as content,
                       k.knowledge_type as knowledge_type,
                       k.tags as tags,
                       k.summary as summary,
                       k.confidence as confidence,
                       k.usage_count as usage_count,
                       k.success_rate as success_rate,
                       k.created_at as created_at,
                       k.deprecated as deprecated
                ORDER BY k.created_at DESC
            """
            )

            entries = list(result)

        # Limit entries if requested (for testing)
        if max_entries:
            entries = entries[:max_entries]

        total = len(entries)

        print(f"Found {total} entries to enrich")

        # Detect relationships across entire KB
        print("\nPhase 1: Detecting relationships...")
        relationships = self.detect_relationships(entries)
        print(f"  Found {sum(len(v) for v in relationships.values())} relationships")

        # Store relationships in Neo4j
        with self.driver.session() as session:
            for source_id, related_list in relationships.items():
                for target_id, rel_type, strength in related_list:
                    session.run(
                        f"""
                        MATCH (k1:Knowledge {{knowledge_id: $source}})
                        MATCH (k2:Knowledge {{knowledge_id: $target}})
                        MERGE (k1)-[r:{rel_type}]->(k2)
                        SET r.strength = $strength,
                            r.detected_at = datetime()
                    """,
                        {
                            "source": source_id,
                            "target": target_id,
                            "strength": strength,
                        },
                    )

        # Process entries in batches
        print("\nPhase 2: Enriching entries...")
        for i in range(0, total, batch_size):
            batch = entries[i : i + batch_size]
            print(f"\nBatch {i//batch_size + 1} ({i+1}-{min(i+batch_size, total)})")

            # Enrich each entry with rate limiting
            tasks = []
            for entry in batch:
                task = self.enrich_entry(entry, relationships)
                tasks.append(task)

            # No delay needed with GPT-5-nano's high rate limits
            # Process batches as fast as possible

            updates_list = await asyncio.gather(*tasks)

            # Apply updates
            with self.driver.session() as session:
                for entry, updates in zip(batch, updates_list):
                    if updates:
                        set_clauses = []
                        params = {"kid": entry["id"]}

                        for key, value in updates.items():
                            set_clauses.append(f"k.{key} = ${key}")
                            params[key] = value

                        if set_clauses:
                            query = f"""
                            MATCH (k:Knowledge {{knowledge_id: $kid}})
                            SET {', '.join(set_clauses)}, k.enriched_at = datetime()
                            RETURN k.knowledge_id as id
                            """
                            session.run(query, params)
                            self.stats["enriched"] += 1

            print(f"  Enriched: {self.stats['enriched']}/{total}")

        # Phase 3: Build knowledge clusters (skip - requires GDS)
        print("\nPhase 3: Knowledge clustering...")
        print("  Clustering skipped (requires Neo4j GDS plugin)")

        # Print final statistics
        print("\n" + "=" * 60)
        print("Enrichment Complete!")
        print(f"Total entries processed: {total}")
        print(f"Entries enriched: {self.stats['enriched']}")
        print(f"  - Summaries generated: {self.stats['summaries_generated']}")
        print(f"  - Quality scored: {self.stats['quality_scored']}")
        print(f"  - Critical marked: {self.stats['critical_marked']}")
        print(f"  - Deprecated marked: {self.stats['deprecated_marked']}")
        print(f"  - Tags enhanced: {self.stats['tags_enhanced']}")
        print(f"Relationships created: {sum(len(v) for v in relationships.values())}")

        # Store enrichment metadata
        with self.driver.session() as session:
            session.run(
                """
                CREATE (m:Metadata {
                    type: 'enrichment',
                    name: 'intelligent_enrichment_v1',
                    completed_at: datetime(),
                    stats: $stats
                })
            """,
                {"stats": json.dumps(dict(self.stats))},
            )


async def main():
    """Run the intelligent enrichment"""
    enricher = IntelligentKBEnricher()
    await enricher.enrich_knowledge_base()


if __name__ == "__main__":
    # Install required packages if needed
    import subprocess

    try:
        import sklearn
    except ImportError:
        print("Installing scikit-learn...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])

    asyncio.run(main())
