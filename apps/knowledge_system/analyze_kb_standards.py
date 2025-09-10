#!/usr/bin/env python3
"""
Analyze current KB entries to understand migration needs
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root")

from collections import Counter

from neo4j import GraphDatabase


def analyze_kb():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    with driver.session() as session:
        # Get sample of entries
        result = session.run(
            """
            MATCH (k:Knowledge)
            RETURN
                k.knowledge_id as id,
                k.content as content,
                k.knowledge_type as knowledge_type,
                k.type as type,
                k.tags as tags,
                k.summary as summary,
                k.confidence as confidence,
                k.confidence_score as confidence_score,
                k.created_at as created_at
            LIMIT 100
        """
        )

        entries = list(result)

        # Analyze patterns
        stats = {
            "total_sampled": len(entries),
            "has_prefix": 0,
            "has_summary": 0,
            "has_tags": 0,
            "has_confidence": 0,
            "types": Counter(),
            "prefix_types": Counter(),
            "tag_examples": set(),
        }

        prefixes = [
            "MEMENTO NOTE:",
            "SYSTEM TRUTH:",
            "BUG DISCOVERED:",
            "FIX APPLIED:",
            "SESSION CONTEXT:",
            "GLOBAL OPERATIONAL",
            "OPTIMIZATION OPPORTUNITY:",
            "PATTERN OBSERVED:",
            "PROJECT INTELLIGENCE:",
        ]

        for entry in entries:
            # Check content prefixes
            content = entry.get("content", "")
            if content:
                for prefix in prefixes:
                    if content.startswith(prefix):
                        stats["has_prefix"] += 1
                        stats["prefix_types"][prefix] += 1
                        break

            # Check other fields
            if entry.get("summary"):
                stats["has_summary"] += 1

            tags = entry.get("tags", [])
            if tags:
                stats["has_tags"] += 1
                for tag in tags[:3]:  # Sample first 3
                    stats["tag_examples"].add(tag)

            if entry.get("confidence") or entry.get("confidence_score"):
                stats["has_confidence"] += 1

            # Count types
            ktype = entry.get("knowledge_type") or entry.get("type", "UNKNOWN")
            stats["types"][ktype] += 1

        # Print analysis
        print("KB Standards Analysis")
        print("=" * 60)
        print(f"Sampled {stats['total_sampled']} entries")
        print(f"\nContent Prefixes:")
        print(
            f"  Has prefix: {stats['has_prefix']}/{stats['total_sampled']} ({stats['has_prefix']*100//stats['total_sampled']}%)"
        )
        print(f"  Prefix types found: {dict(stats['prefix_types'])}")
        print(f"\nSummaries:")
        print(
            f"  Has summary: {stats['has_summary']}/{stats['total_sampled']} ({stats['has_summary']*100//stats['total_sampled']}%)"
        )
        print(f"\nTags:")
        print(
            f"  Has tags: {stats['has_tags']}/{stats['total_sampled']} ({stats['has_tags']*100//stats['total_sampled']}%)"
        )
        print(f"  Example tags: {list(stats['tag_examples'])[:10]}")
        print(f"\nConfidence Scores:")
        print(
            f"  Has confidence: {stats['has_confidence']}/{stats['total_sampled']} ({stats['has_confidence']*100//stats['total_sampled']}%)"
        )
        print(f"\nKnowledge Types:")
        for ktype, count in stats["types"].most_common():
            print(f"  {ktype}: {count}")

        # Get total count
        result = session.run("MATCH (k:Knowledge) RETURN COUNT(k) as total")
        total = result.single()["total"]
        print(f"\nTotal KB entries: {total}")

        # Estimate migration needs
        print(f"\nEstimated Migration Needs (based on sample):")
        print(
            f"  Needs prefix: ~{(stats['total_sampled'] - stats['has_prefix']) * total // stats['total_sampled']}"
        )
        print(
            f"  Needs summary: ~{(stats['total_sampled'] - stats['has_summary']) * total // stats['total_sampled']}"
        )
        print(
            f"  Needs tags: ~{(stats['total_sampled'] - stats['has_tags']) * total // stats['total_sampled']}"
        )
        print(
            f"  Needs confidence: ~{(stats['total_sampled'] - stats['has_confidence']) * total // stats['total_sampled']}"
        )


if __name__ == "__main__":
    analyze_kb()
