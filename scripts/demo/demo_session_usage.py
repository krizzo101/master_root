#!/usr/bin/env python3
"""
Demonstration of Claude Session Manager Usage
Shows how to extract context from the current session
"""

import json
import os
import sys

# Set the current session UUID (discovered via marker technique)
os.environ["CLAUDE_SESSION_UUID"] = "464f3bd5-9e49-4cc4-8ab3-86700d8633b9"

# Add session manager to path
sys.path.insert(0, "/home/opsvi/master_root/.claude/session_manager")

from session_context import SessionContext
from session_detector import SessionDetector


def main():
    print("=== Claude Session Manager Demo ===\n")

    # 1. Detect current session
    detector = SessionDetector()
    session_id, method, confidence = detector.get_current_session_id()

    print(f"Current Session: {session_id}")
    print(f"Detection Method: {method}")
    print(f"Confidence: {confidence:.0%}\n")

    # 2. Get session info
    info = detector.get_session_info()
    print("Session Info:")
    print(f"  File: {info.get('file_path', 'N/A')}")
    print(f"  Lines: {info.get('lines', 0)}")
    print(f"  Size: {info.get('size_kb', 0):.1f} KB")
    print(f"  Modified: {info.get('modified', 'N/A')}\n")

    # 3. Extract context
    context = SessionContext(session_id)

    # Get summary
    summary = context.get_summary_context()
    print("Session Summary:")
    print(f"  User Prompts: {summary['user_prompts']}")
    print(f"  Assistant Responses: {summary['assistant_responses']}")
    print(f"  Tools Used: {summary['tools_used']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Files Modified: {len(summary['files_modified'])}\n")

    # Show recent topics
    if summary["recent_topics"]:
        print("Recent Topics:")
        for i, topic in enumerate(summary["recent_topics"][-3:], 1):
            preview = topic[:100] + "..." if len(topic) > 100 else topic
            print(f"  {i}. {preview}")
        print()

    # 4. Tool usage analysis
    tool_usage = context.get_tool_usage(num_recent=20)
    if tool_usage:
        print("Tool Usage (last 20):")
        for tool, uses in sorted(
            tool_usage.items(), key=lambda x: len(x[1]), reverse=True
        )[:5]:
            print(f"  {tool}: {len(uses)} uses")
        print()

    # 5. Recent code changes
    changes = context.get_code_changes(num_recent=5)
    if changes:
        print("Recent Code Changes:")
        for change in changes[:3]:
            print(f"  [{change['tool']}] {change['file']}")
        print()

    # 6. Export option
    print("To export full context:")
    print(f"  claude-session export session-{session_id[:8]}.json\n")

    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
