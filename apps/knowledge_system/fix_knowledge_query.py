#!/usr/bin/env python3
"""
Fix for knowledge query tool to show ALL knowledge, not just high-confidence
The truth: 2,799 total items but MCP tool only shows ~100 due to filters
"""

import os
import sys

sys.path.insert(0, "/home/opsvi/master_root")

print("KNOWLEDGE QUERY FIX")
print("=" * 70)

# The problem analysis
print("\nPROBLEM IDENTIFIED:")
print("1. Total knowledge in DB: 2,799 items")
print("2. MCP tool shows: ~100 items")
print("3. Root cause: min_confidence defaults to 0.7")
print("4. Most knowledge has NULL deprecated field (2,690 items)")
print("5. Embeddings only on 102 items, Qdrant not connected")

print("\nFIX REQUIRED:")
print("1. Change default min_confidence from 0.7 to 0.0")
print("2. Handle NULL deprecated as false")
print("3. Fix search to include all content")
print("4. Preserve original content during transformation")

# Create the fixed query implementation
fixed_code = '''
# FIX 1: Change default min_confidence to 0.0 in query method
def query(
    self,
    query_type: str,
    query_text: Optional[str] = None,
    knowledge_type: Optional[str] = None,
    min_confidence: float = 0.0,  # CHANGED FROM 0.7 TO 0.0
    limit: int = 5,
    direct_execute: bool = True,
) -> Dict[str, Any]:
    """Query knowledge with optional direct execution."""

    # FIX 2: Update all queries to handle NULL deprecated
    if query_type == "search":
        cypher = """
        MATCH (k:Knowledge)
        WHERE (k.deprecated = false OR k.deprecated IS NULL)  # HANDLE NULL
        AND (toLower(k.content) CONTAINS toLower($query_text)
        OR any(tag IN k.tags WHERE toLower(tag) CONTAINS toLower($query_text)))
        AND k.confidence_score >= $min_confidence
        RETURN k
        ORDER BY k.confidence_score DESC, k.usage_count DESC
        LIMIT $limit
        """

    elif query_type == "recent":
        cypher = """
        MATCH (k:Knowledge)
        WHERE (k.deprecated = false OR k.deprecated IS NULL)  # HANDLE NULL
        AND (k.confidence_score >= $min_confidence OR k.confidence_score IS NULL)
        RETURN k
        ORDER BY COALESCE(k.updated_at, k.created_at) DESC  # HANDLE MISSING updated_at
        LIMIT $limit
        """
'''

print("\nFIX IMPLEMENTATION:")
print(fixed_code)

print("\nACTION REQUIRED:")
print("1. Edit /home/opsvi/master_root/apps/knowledge_system/mcp_knowledge_tools.py")
print("2. Change default min_confidence from 0.7 to 0.0 (line ~427)")
print("3. Update WHERE clauses to handle NULL deprecated")
print("4. User must restart session for changes to take effect")
print("5. Then test with mcp__knowledge__knowledge_query")

print("\n" + "=" * 70)
print("FIX SCRIPT COMPLETE")
