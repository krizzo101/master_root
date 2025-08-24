#!/usr/bin/env python3
"""
Fast KB Enrichment - Focus on summaries only, skip expensive relationship detection
"""

import asyncio
import sys

sys.path.insert(0, "/home/opsvi/master_root")

from kb_intelligent_enrichment import IntelligentKBEnricher


class FastEnricher(IntelligentKBEnricher):
    """Fast enricher that skips relationship detection"""

    async def enrich_knowledge_base(
        self, batch_size: int = 100, max_entries: int = None
    ):
        """Fast enrichment - summaries and scores only"""
        print("Starting FAST KB Enrichment (summaries + scores only)...")
        print("=" * 60)

        # Get all knowledge entries
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.content IS NOT NULL
                  AND k.summary IS NULL
                  AND size(k.content) > 100
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
        print(f"Found {total} entries needing summaries")

        # Skip relationship detection - too expensive
        print("\nSkipping relationship detection (too expensive for 3000+ entries)")
        relationships = {}

        # Process entries in batches
        print("\nEnriching entries with summaries and scores...")
        for i in range(0, total, batch_size):
            batch = entries[i : i + batch_size]
            batch_end = min(i + batch_size, total)
            print(f"\nBatch {i//batch_size + 1} ({i+1}-{batch_end}/{total})")

            # Enrich each entry in parallel
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
                            RETURN k.knowledge_id as id
                            """
                            session.run(query, params)
                            self.stats["enriched"] += 1

            print(f"  Progress: {self.stats['enriched']}/{total} enriched")

            # Show estimated time remaining
            if self.stats["enriched"] > 0:
                elapsed_batches = (i // batch_size) + 1
                total_batches = (total + batch_size - 1) // batch_size
                remaining_batches = total_batches - elapsed_batches
                print(f"  Estimated batches remaining: {remaining_batches}")

        # Print final statistics
        print("\n" + "=" * 60)
        print("Fast Enrichment Complete!")
        print(f"Total entries processed: {total}")
        print(f"Entries enriched: {self.stats['enriched']}")
        print(f"  - Summaries generated: {self.stats['summaries_generated']}")
        print(f"  - Quality scored: {self.stats['quality_scored']}")
        print(f"  - Critical marked: {self.stats['critical_marked']}")
        print(f"  - Deprecated marked: {self.stats['deprecated_marked']}")
        print(f"  - Tags enhanced: {self.stats['tags_enhanced']}")
        print("\nRelationship detection skipped (run separately if needed)")


async def main():
    """Run fast enrichment"""
    enricher = FastEnricher()
    await enricher.enrich_knowledge_base(batch_size=100)


if __name__ == "__main__":
    asyncio.run(main())
