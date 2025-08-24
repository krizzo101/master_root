#!/usr/bin/env python3
"""
Estimate token usage for KB enrichment
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root")

import tiktoken
from neo4j import GraphDatabase


def estimate_tokens():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    # Get tokenizer for GPT models (gpt-5-nano likely uses same tokenization)
    enc = tiktoken.get_encoding("cl100k_base")

    with driver.session() as session:
        # Get all entries that need summaries
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.content IS NOT NULL
              AND k.summary IS NULL
              AND size(k.content) > 100
            RETURN k.content as content
        """
        )

        total_input_tokens = 0
        total_output_tokens = 0
        entry_count = 0

        # System prompt we use (constant per request)
        system_prompt = """Create a one-line summary (max 100 chars) that:
1. Captures the MAIN point/action
2. Includes key context (tool/file/error if relevant)
3. Is searchable and specific
4. No fluff words

Examples:
- "Fixed authentication loop in ACCF by adding session validation"
- "MetaGPT roles require use_fixed_sop=True to process messages"
- "Knowledge system uses Neo4j with 3000+ entries for semantic search"

Return ONLY the summary line."""

        system_tokens = len(enc.encode(system_prompt))

        for record in result:
            content = record["content"]
            if content:
                entry_count += 1

                # For input: system prompt + first 500 chars of content
                input_text = f"Content: {content[:500]}"
                try:
                    input_tokens = system_tokens + len(
                        enc.encode(input_text, disallowed_special=())
                    )
                except:
                    # Fallback: estimate 1 token per 4 chars
                    input_tokens = system_tokens + len(input_text) // 4
                total_input_tokens += input_tokens

                # For output: estimate ~100 chars (20-25 tokens typically)
                total_output_tokens += 25

        # Calculate averages
        avg_input_per_entry = (
            total_input_tokens // entry_count if entry_count > 0 else 0
        )
        avg_output_per_entry = (
            total_output_tokens // entry_count if entry_count > 0 else 0
        )

        # Print estimates
        print("Token Usage Estimation for KB Enrichment")
        print("=" * 60)
        print(f"Entries needing summaries: {entry_count}")
        print()
        print("DETAILED BREAKDOWN PER ENTRY:")
        print(f"  Instructions/System prompt: {system_tokens} tokens")
        print(
            f"  User input (first 500 chars of content): ~{avg_input_per_entry - system_tokens} tokens"
        )
        print(f"  Total INPUT tokens per entry: ~{avg_input_per_entry} tokens")
        print(f"  Expected OUTPUT tokens (summary): ~{avg_output_per_entry} tokens")
        print(
            f"  TOTAL per entry: ~{avg_input_per_entry + avg_output_per_entry} tokens"
        )
        print()
        print("TOTAL ESTIMATION FOR ALL {entry_count} ENTRIES:")
        print(f"  Total INPUT tokens (instructions + content): {total_input_tokens:,}")
        print(f"  Total OUTPUT tokens (summaries): {total_output_tokens:,}")
        print(f"  GRAND TOTAL: {total_input_tokens + total_output_tokens:,} tokens")
        print()
        print("Daily Limit Comparison:")
        total = total_input_tokens + total_output_tokens
        print(f"  Daily free limit: 10,000,000 tokens")
        print(f"  This job needs: {total:,} tokens")
        print(f"  Percentage of daily limit: {total * 100 / 10_000_000:.1f}%")
        print(f"  Remaining after job: {10_000_000 - total:,} tokens")

        # Also estimate time
        print()
        print("Time Estimation:")
        print(f"  Batches of 10 entries")
        print(f"  1 second delay between batches")
        print(f"  Total batches: {entry_count // 10}")
        print(f"  Estimated time: {entry_count // 10 / 60:.1f} minutes")


if __name__ == "__main__":
    estimate_tokens()
