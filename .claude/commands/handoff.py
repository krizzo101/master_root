#!/usr/bin/env python3
"""
Enhanced Session Handoff Script - Agent briefing using compact analysis
Usage: python .claude/commands/handoff.py <session-id-partial>
"""

import os
import subprocess
import sys
from pathlib import Path


def find_session_file(session_id_partial):
    """Find the full session file path from partial ID"""
    # First, look in symlinked chat_logs directory
    chat_logs_dir = Path("/home/opsvi/master_root/chat_logs")
    if chat_logs_dir.exists():
        for file_path in chat_logs_dir.glob("*.jsonl"):
            if session_id_partial in file_path.name:
                return str(file_path)

    # Fallback: search the filesystem for session files
    search_paths = [
        "/home/opsvi/.claude/projects/-home-opsvi-master-root",
        "/home/opsvi/master_root/apps/session-optimizer/test_sessions",
        "/home/opsvi/master_root",
    ]

    for search_path in search_paths:
        search_dir = Path(search_path)
        if search_dir.exists():
            for file_path in search_dir.rglob("*.jsonl"):
                if (
                    session_id_partial in file_path.name
                    and "sessionId" in file_path.read_text(errors="ignore")
                ):
                    return str(file_path)

    return None


def run_compact_analysis(session_file):
    """Run the compact analysis tool on the session file"""
    cmd = [
        "python",
        "apps/chat-search/jsonl_to_markdown.py",
        session_file,
        "--compact",
        "--compact-length",
        "1000",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd="/home/opsvi/master_root"
        )

        if result.returncode == 0:
            # Find the output file (same name as input but .md extension)
            input_path = Path(session_file)
            output_file = input_path.with_suffix(".md")

            if output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return result.stdout
        else:
            return f"ERROR running compact analysis: {result.stderr}"

    except Exception as e:
        return f"ERROR: {str(e)}"


def main():
    if len(sys.argv) != 2:
        print("Usage: python handoff.py <session-id-partial>")
        print("Example: python handoff.py fc3b7d3d")
        sys.exit(1)

    session_id_partial = sys.argv[1]

    print(f"🔍 SEARCHING FOR SESSION: {session_id_partial}")
    print("=" * 60)

    # Find the session file
    session_file = find_session_file(session_id_partial)

    if not session_file:
        print(f"❌ No session file found containing '{session_id_partial}'")
        print("\nTip: Try with more characters from the session ID")
        sys.exit(1)

    print(f"✅ Found session file: {session_file}")
    print("🤖 Generating agent briefing...")
    print("=" * 60)

    # Run compact analysis
    briefing = run_compact_analysis(session_file)

    if briefing.startswith("ERROR"):
        print(briefing)
        sys.exit(1)

    # Display the briefing
    print(briefing)

    # Add handoff instructions
    print("\n" + "=" * 60)
    print("📝 AGENT HANDOFF INSTRUCTIONS:")
    print("=" * 60)
    print("The above briefing provides:")
    print("✓ Complete conversation flow with user requests and responses")
    print("✓ Performance metrics (tokens, cache efficiency, tool success)")
    print("✓ Technical context (files accessed, tools used, model info)")
    print("✓ Session timeline and duration")
    print("✓ Last user request and continuation context")
    print()
    print("🎯 NEXT STEPS:")
    print("1. Review the conversation flow to understand the context")
    print("2. Check the last user request for current task state")
    print("3. Note any interrupted responses that need completion")
    print("4. Ask user for clarification if needed before proceeding")
    print()
    print("⚠️  Always confirm with user before taking significant action!")


if __name__ == "__main__":
    main()
