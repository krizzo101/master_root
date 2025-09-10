#!/usr/bin/env python3
"""
Analyze the actual content lengths in the KB
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root")

from collections import Counter

from neo4j import GraphDatabase


def analyze_content_lengths():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    with driver.session() as session:
        # Get all content lengths
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.content IS NOT NULL
            RETURN
                size(k.content) as content_length,
                k.summary IS NOT NULL as has_summary,
                k.knowledge_type as type,
                substring(k.content, 0, 200) as preview
        """
        )

        entries = list(result)

        # Analyze lengths
        lengths = [e["content_length"] for e in entries]

        # Distribution
        very_short = sum(1 for l in lengths if l < 100)
        short = sum(1 for l in lengths if 100 <= l < 300)
        medium = sum(1 for l in lengths if 300 <= l < 1000)
        long = sum(1 for l in lengths if 1000 <= l < 3000)
        very_long = sum(1 for l in lengths if l >= 3000)

        # Missing summaries by length
        missing_summary_short = sum(
            1 for e in entries if e["content_length"] < 100 and not e["has_summary"]
        )
        missing_summary_long = sum(
            1 for e in entries if e["content_length"] >= 300 and not e["has_summary"]
        )

        print("KB Content Length Analysis")
        print("=" * 60)
        print(f"Total entries with content: {len(entries)}")
        print(f"\nContent Length Distribution:")
        print(
            f"  < 100 chars (very short):   {very_short:4d} ({very_short*100//len(entries)}%)"
        )
        print(f"  100-300 chars (short):      {short:4d} ({short*100//len(entries)}%)")
        print(
            f"  300-1000 chars (medium):    {medium:4d} ({medium*100//len(entries)}%)"
        )
        print(f"  1000-3000 chars (long):     {long:4d} ({long*100//len(entries)}%)")
        print(
            f"  >= 3000 chars (very long):  {very_long:4d} ({very_long*100//len(entries)}%)"
        )

        print(f"\nSummary Status:")
        print(f"  Short entries (<100) without summary: {missing_summary_short}")
        print(f"  Long entries (>=300) without summary: {missing_summary_long}")

        print(f"\nStatistics:")
        print(f"  Average length: {sum(lengths)//len(lengths)} chars")
        print(f"  Median length: {sorted(lengths)[len(lengths)//2]} chars")
        print(f"  Shortest: {min(lengths)} chars")
        print(f"  Longest: {max(lengths)} chars")

        # Show some examples of short entries
        print(f"\n--- Examples of Very Short Entries (<100 chars) ---")
        short_examples = [e for e in entries if e["content_length"] < 100][:5]
        for i, e in enumerate(short_examples, 1):
            print(f"\n{i}. Type: {e['type']}, Length: {e['content_length']}")
            print(f"   Content: {e['preview']}")

        # Show some examples of entries that might need summaries
        print(f"\n--- Examples of Long Entries (>1000 chars) ---")
        long_examples = [
            e for e in entries if e["content_length"] > 1000 and not e["has_summary"]
        ][:3]
        for i, e in enumerate(long_examples, 1):
            print(f"\n{i}. Type: {e['type']}, Length: {e['content_length']}")
            print(f"   Preview: {e['preview'][:150]}...")


if __name__ == "__main__":
    analyze_content_lengths()
