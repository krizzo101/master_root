#!/usr/bin/env python3
"""
Optimized KB Enrichment - Smart relationship detection + full enrichment
"""

import asyncio
import sys
import time

sys.path.insert(0, "/home/opsvi/master_root")

import random
from collections import defaultdict

from kb_intelligent_enrichment import IntelligentKBEnricher


class OptimizedEnricher(IntelligentKBEnricher):
    """Optimized enricher with smart relationship detection"""

    def detect_relationships_smart(self, entries):
        """Detect relationships more efficiently"""
        print("\nPhase 1: Smart Relationship Detection")
        print("-" * 40)

        relationships = defaultdict(list)

        # Group entries by type for more relevant comparisons
        by_type = defaultdict(list)
        for entry in entries:
            if entry.get("id") and entry.get("content"):
                by_type[entry.get("knowledge_type", "GENERAL")].append(entry)

        print(f"Grouped into {len(by_type)} knowledge types:")
        for ktype, items in by_type.items():
            print(f"  {ktype}: {len(items)} entries")

        # Process each type group
        total_comparisons = 0
        for ktype, type_entries in by_type.items():
            n = len(type_entries)

            # For large groups, use sampling
            if n > 500:
                print(
                    f"\n{ktype}: Sampling 500 from {n} entries (too many for full comparison)"
                )
                type_entries = random.sample(type_entries, 500)
                n = 500

            if n < 2:
                continue

            comparisons = n * (n - 1) // 2
            total_comparisons += comparisons
            print(f"\n{ktype}: Computing {comparisons} comparisons...")

            # Prepare content
            contents = [e["content"] for e in type_entries]

            try:
                # Compute TF-IDF vectors
                tfidf_matrix = self.vectorizer.fit_transform(contents)

                # Compute similarities
                from sklearn.metrics.pairwise import cosine_similarity

                similarities = cosine_similarity(tfidf_matrix)

                # Find relationships
                found = 0
                for i in range(n):
                    for j in range(i + 1, n):
                        sim = similarities[i][j]

                        if 0.3 < sim < 0.95:  # Related but not duplicate
                            id1 = type_entries[i]["id"]
                            id2 = type_entries[j]["id"]
                            relationships[id1].append((id2, "RELATED_TO", sim))
                            relationships[id2].append((id1, "RELATED_TO", sim))
                            found += 1

                        elif sim >= 0.95:  # Potential duplicate
                            # Check dates to determine supersedes
                            created1 = type_entries[i].get("created_at")
                            created2 = type_entries[j].get("created_at")

                            if hasattr(created1, "to_native"):
                                created1 = created1.to_native()
                            if hasattr(created2, "to_native"):
                                created2 = created2.to_native()

                            if created1 and created2:
                                if created1 > created2:
                                    relationships[type_entries[i]["id"]].append(
                                        (type_entries[j]["id"], "SUPERSEDES", sim)
                                    )
                                else:
                                    relationships[type_entries[j]["id"]].append(
                                        (type_entries[i]["id"], "SUPERSEDES", sim)
                                    )
                                found += 1

                print(f"  Found {found} relationships")

            except Exception as e:
                print(f"  Error processing {ktype}: {e}")

        total_rels = sum(len(v) for v in relationships.values())
        print(f"\nTotal relationships found: {total_rels}")
        print(
            f"Total comparisons made: {total_comparisons} (vs {len(entries)*(len(entries)-1)//2} for all)"
        )

        return relationships

    async def enrich_knowledge_base(
        self, batch_size: int = 100, max_entries: int = None
    ):
        """Optimized enrichment with progress tracking"""
        start_time = time.time()

        print("Starting Optimized KB Enrichment")
        print("=" * 60)

        # Get entries needing enrichment
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.content IS NOT NULL
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

        if max_entries:
            entries = entries[:max_entries]

        total = len(entries)
        needs_summary = sum(
            1
            for e in entries
            if not e.get("summary") and len(e.get("content", "")) > 100
        )

        print(f"Total entries: {total}")
        print(f"Needs summaries: {needs_summary}")
        print()

        # Phase 1: Detect relationships (optimized)
        relationships = self.detect_relationships_smart(entries)

        # Store relationships
        print("\nStoring relationships in database...")
        with self.driver.session() as session:
            stored = 0
            for source_id, related_list in relationships.items():
                for target_id, rel_type, strength in related_list:
                    try:
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
                        stored += 1
                    except:
                        pass  # Skip if relationship already exists
            print(f"Stored {stored} relationships")

        # Phase 2: Enrich entries
        print("\nPhase 2: Enriching Entries")
        print("-" * 40)

        for i in range(0, total, batch_size):
            batch = entries[i : i + batch_size]
            batch_end = min(i + batch_size, total)

            # Calculate ETA
            if i > 0:
                elapsed = time.time() - start_time
                per_entry = elapsed / i
                remaining = (total - i) * per_entry
                eta_min = int(remaining / 60)
                eta_sec = int(remaining % 60)
                print(
                    f"\nBatch {i//batch_size + 1} ({i+1}-{batch_end}/{total}) - ETA: {eta_min}m {eta_sec}s"
                )
            else:
                print(f"\nBatch 1 (1-{batch_end}/{total})")

            # Process batch in parallel
            tasks = []
            for entry in batch:
                task = self.enrich_entry(entry, relationships)
                tasks.append(task)

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
                            """
                            session.run(query, params)
                            self.stats["enriched"] += 1

            print(f"  Enriched: {self.stats['enriched']}/{total}")

            # Show what was done
            if self.stats["summaries_generated"] > 0:
                print(f"  Summaries: {self.stats['summaries_generated']}")

        # Final statistics
        elapsed_total = time.time() - start_time
        print("\n" + "=" * 60)
        print("Enrichment Complete!")
        print(f"Time taken: {int(elapsed_total/60)}m {int(elapsed_total%60)}s")
        print(f"Total entries processed: {total}")
        print(f"Entries enriched: {self.stats['enriched']}")
        print(f"  - Summaries generated: {self.stats['summaries_generated']}")
        print(f"  - Quality scored: {self.stats['quality_scored']}")
        print(f"  - Critical marked: {self.stats['critical_marked']}")
        print(f"  - Deprecated marked: {self.stats['deprecated_marked']}")
        print(f"  - Tags enhanced: {self.stats['tags_enhanced']}")
        print(f"Relationships created: {sum(len(v) for v in relationships.values())}")


async def main():
    enricher = OptimizedEnricher()
    await enricher.enrich_knowledge_base(batch_size=100)


if __name__ == "__main__":
    asyncio.run(main())
