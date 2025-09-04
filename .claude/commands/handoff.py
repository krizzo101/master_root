#!/usr/bin/env python3
"""
Session Handoff Script - Get up to speed on prior session efficiently
Usage: python .claude/commands/handoff.py <session-id-partial>
"""

import json
import subprocess
import sys
from pathlib import Path


def run_search(query, session_id, limit=10, msg_type="all"):
    """Run chat_search.py and return results"""
    cmd = [
        "python",
        "apps/chat-search/chat_search.py",
        "--file-filter",
        session_id,
        "--limit",
        str(limit),
        "--type",
        msg_type,
        query,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd="/home/opsvi/master_root"
        )
        return (
            result.stdout.strip()
            if result.returncode == 0
            else f"ERROR: {result.stderr}"
        )
    except Exception as e:
        return f"ERROR: {str(e)}"


def main():
    if len(sys.argv) != 2:
        print("Usage: python handoff.py <session-id-partial>")
        sys.exit(1)

    session_id = sys.argv[1]

    print(f"🔍 HANDOFF ANALYSIS FOR SESSION: {session_id}")
    print("=" * 60)

    # 1. Session Scope & Timeline
    print("\n📋 1. SESSION SCOPE & TIMELINE")
    print("-" * 30)
    scope_results = run_search(".*", session_id, limit=5, msg_type="user")
    print(scope_results)

    # 2. Final User State
    print("\n🎯 2. FINAL USER STATE")
    print("-" * 30)
    final_results = run_search(".*", session_id, limit=3, msg_type="user")
    print("LAST 3 USER MESSAGES:")
    print(final_results)

    # 3. Handoff Markers (Priority Search)
    print("\n🎯 3. HANDOFF MARKERS (PRIORITY)")
    print("-" * 30)
    handoff_results = run_search(
        "HANDOFF_READY:|BLOCKED_ON:|NEXT_AGENT_SHOULD:|CONTEXT_SUMMARY:|COMPLETED_SUCCESSFULLY:|TECHNICAL_BLOCKER:",
        session_id,
        limit=10,
    )
    if "Found 0 matches" in handoff_results:
        print(
            "No standardized handoff markers found. Falling back to generic progress search..."
        )
        progress_results = run_search(
            "TodoWrite|completed|error|failed|successfully|finished",
            session_id,
            limit=10,
        )
        print(progress_results)
    else:
        print(handoff_results)

    # 4. Knowledge Context
    print("\n🧠 4. KNOWLEDGE CONTEXT")
    print("-" * 30)
    knowledge_results = run_search(
        "Read.*file_path|understood|learned|explored|architecture|framework",
        session_id,
        limit=15,
    )
    print(knowledge_results)

    # 5. Technical Dependencies
    print("\n🔧 5. TECHNICAL DEPENDENCIES")
    print("-" * 30)
    tech_results = run_search(
        "tool_use.*name.*(Read|Write|Edit|Bash)|git.*commit", session_id, limit=10
    )
    print(tech_results)

    # Summary
    print("\n" + "=" * 60)
    print("📝 HANDOFF INSTRUCTIONS:")
    print("=" * 60)
    print("Now analyze the above output and provide:")
    print("1. SUMMARY: What the user wanted and what was accomplished")
    print("2. NEXT ACTION: What the previous agent was planning to do")
    print("3. CONTEXT: Key technical details for continuation")
    print("4. GAPS: What needs clarification")
    print("5. WAIT: Ask user for instructions before proceeding")
    print()
    print("⚠️  DO NOT automatically continue the previous work!")
    print("⚠️  Wait for user confirmation before taking action!")


if __name__ == "__main__":
    main()
