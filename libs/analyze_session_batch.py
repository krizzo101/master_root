#!/usr/bin/env python3
"""
Batch analyze sessions using LLM
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.append("/home/opsvi/master_root/libs")
from session_analyzer import extract_session_digest, generate_heuristic_summary

DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


def analyze_and_store(session_id):
    """Extract digest and use MCP tool for analysis"""

    # Extract the digest
    result = extract_session_digest(session_id)
    if not result:
        return None

    digest, digest_size = result

    # Format for analysis
    user_requests = "\n".join(
        [f"- {msg['text']}" for msg in digest["user_messages"][:10]]
    )

    assistant_actions = []
    for r in digest["assistant_snippets"][:8]:
        if r.get("end") and r["end"] != r["start"]:
            assistant_actions.append(f"- {r['start'][:80]}... → {r['end'][-80:]}")
        else:
            assistant_actions.append(f"- {r['start'][:150]}")

    # Print digest info
    print(f"\nSession: {session_id}")
    print(f"Digest size: {digest_size} bytes")
    print(f"Duration: {digest['duration_minutes']} minutes")
    print(f"User messages: {len(digest['user_messages'])}")

    if not digest["user_messages"]:
        # Use heuristic for empty sessions
        analysis = generate_heuristic_summary(digest)
    else:
        # For now, use improved heuristic analysis
        # (We'll add LLM integration once we verify the data extraction)
        all_text = " ".join([m["text"].lower() for m in digest["user_messages"]])

        # Enhanced keyword analysis
        title = "Development Session"
        bullets = []

        if "dashboard" in all_text or "web interface" in all_text:
            title = "Chat Analytics Dashboard Development"
            if "session" in all_text and "summar" in all_text:
                title = "Session Summary and Analytics Implementation"
                bullets.append("Implemented session summary generation")
            if "chart" in all_text or "graph" in all_text:
                bullets.append("Created data visualization charts")
            if "api" in all_text or "endpoint" in all_text:
                bullets.append("Developed API endpoints for data access")
        elif "chat log" in all_text or "taxonomy" in all_text:
            title = "Chat Log Parsing and Analysis System"
            bullets.append("Built JSONL parser for chat logs")
            if "ingest" in all_text:
                bullets.append("Created data ingestion pipeline")
            if "database" in all_text or "sqlite" in all_text:
                bullets.append("Implemented SQLite storage backend")
        elif "fix" in all_text or "bug" in all_text or "error" in all_text:
            title = "Bug Fixes and Issue Resolution"
            if "chart" in all_text:
                bullets.append("Fixed chart rendering issues")
            if "sql" in all_text or "query" in all_text:
                bullets.append("Resolved database query problems")
        elif "agent" in all_text:
            title = "Agent System Development"
            bullets.append("Worked on agent activation tracking")

        # Add file activity if significant
        if digest["files_touched"] > 5:
            bullets.append(
                f"Modified {digest['files_touched']} files across the codebase"
            )

        # Add agent usage if present
        if digest["agents_used"]:
            bullets.append(f"Utilized {', '.join(digest['agents_used'][:2])} agents")

        # Build summary
        summary = f"A {digest['duration_minutes']}-minute development session "
        if "build" in all_text or "create" in all_text or "implement" in all_text:
            summary += "implementing new functionality"
        elif "fix" in all_text:
            summary += "resolving issues and bugs"
        elif "analyze" in all_text:
            summary += "analyzing and processing data"
        else:
            summary += "working on the codebase"

        if digest["files_touched"] > 0:
            summary += f", modifying {digest['files_touched']} files"
        summary += "."

        analysis = {
            "title": title,
            "summary": summary,
            "bullets": bullets if bullets else ["Development work completed"],
        }

    # Store in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO session_analyses
        (session_id, title, summary, bullet_points, digest_size)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            session_id,
            analysis["title"],
            analysis["summary"],
            json.dumps(analysis["bullets"]),
            digest_size,
        ),
    )

    conn.commit()
    conn.close()

    print(f"Title: {analysis['title']}")
    print(f"Summary: {analysis['summary']}")
    print(f"Bullets: {json.dumps(analysis['bullets'], indent=2)}")

    return analysis


if __name__ == "__main__":
    # Get recent sessions to analyze
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get unanalyzed sessions
    cursor.execute(
        """
        SELECT s.session_id
        FROM sessions s
        LEFT JOIN session_analyses sa ON s.session_id = sa.session_id
        WHERE sa.session_id IS NULL
        ORDER BY (SELECT MAX(timestamp) FROM nodes WHERE session_id = s.session_id) DESC
        LIMIT 10
    """
    )

    sessions = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"Analyzing {len(sessions)} sessions...")

    for session_id in sessions:
        try:
            analyze_and_store(session_id)
        except Exception as e:
            print(f"Error analyzing {session_id}: {e}")

    print("\nAnalysis complete!")
