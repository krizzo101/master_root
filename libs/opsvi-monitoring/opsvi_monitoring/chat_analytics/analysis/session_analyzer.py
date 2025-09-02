#!/usr/bin/env python3
"""
Session Analyzer using Claude for intelligent analysis
"""

import json
import os
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def extract_session_digest(session_id, limit_exchanges=50):
    """Extract the essence of a session for LLM analysis"""
    conn = get_db()
    cursor = conn.cursor()

    # Get session metadata
    cursor.execute(
        """
        SELECT
            s.session_id,
            s.cwd,
            MIN(n.timestamp) as start_time,
            MAX(n.timestamp) as end_time,
            COUNT(DISTINCT n.uuid) as total_nodes,
            CAST((julianday(MAX(n.timestamp)) - julianday(MIN(n.timestamp))) * 24 * 60 AS INTEGER) as duration_minutes
        FROM sessions s
        JOIN nodes n ON s.session_id = n.session_id
        WHERE s.session_id = ?
        GROUP BY s.session_id
    """,
        (session_id,),
    )

    session_meta = dict(cursor.fetchone()) if cursor.rowcount else None
    if not session_meta:
        conn.close()
        return None

    # Get all user messages
    cursor.execute(
        """
        SELECT raw_json, timestamp
        FROM nodes
        WHERE session_id = ? AND node_type = 'user'
        ORDER BY timestamp
        LIMIT ?
    """,
        (session_id, limit_exchanges),
    )

    user_messages = []
    for row in cursor.fetchall():
        try:
            data = json.loads(row["raw_json"])
            if "message" in data and "content" in data["message"]:
                content = data["message"]["content"]
                # Skip session hooks and system messages
                if not str(content).startswith("<session-") and not str(
                    content
                ).startswith("<system-"):
                    if isinstance(content, list):
                        text = " ".join(
                            [
                                c.get("text", "")
                                for c in content
                                if c.get("type") == "text"
                            ]
                        )
                    else:
                        text = str(content)
                    if text and len(text) > 10:
                        user_messages.append(text[:500])
        except:
            pass

    # Get assistant response snippets
    cursor.execute(
        """
        SELECT raw_json, timestamp
        FROM nodes
        WHERE session_id = ? AND node_type = 'assistant'
        ORDER BY timestamp
        LIMIT ?
    """,
        (session_id, limit_exchanges),
    )

    assistant_responses = []
    for row in cursor.fetchall():
        try:
            data = json.loads(row["raw_json"])
            if "message" in data and "content" in data["message"]:
                content = data["message"]["content"]
                if isinstance(content, list):
                    text_parts = [
                        c.get("text", "") for c in content if c.get("type") == "text"
                    ]
                    text = " ".join(text_parts)
                else:
                    text = str(content)

                if text and len(text) > 20:
                    # Get beginning and end snippets
                    start_snippet = text[:200].strip()
                    end_snippet = text[-200:].strip() if len(text) > 400 else ""
                    assistant_responses.append(
                        {"start": start_snippet, "end": end_snippet}
                    )
        except:
            pass

    # Get tool usage patterns
    cursor.execute(
        """
        SELECT
            tc.tool_name,
            COUNT(*) as usage_count
        FROM tool_calls tc
        JOIN nodes n ON tc.node_uuid = n.uuid
        WHERE n.session_id = ?
        GROUP BY tc.tool_name
        ORDER BY usage_count DESC
        LIMIT 10
    """,
        (session_id,),
    )

    tool_patterns = [
        {"tool": row["tool_name"], "count": row["usage_count"]}
        for row in cursor.fetchall()
    ]

    # Get agent activations
    cursor.execute(
        """
        SELECT DISTINCT
            json_extract(tc.input_json, '$.subagent_type') as agent
        FROM tool_calls tc
        JOIN nodes n ON tc.node_uuid = n.uuid
        WHERE n.session_id = ? AND tc.tool_name = 'Task'
    """,
        (session_id,),
    )

    agents = [row["agent"] for row in cursor.fetchall() if row["agent"]]

    # Get files touched
    cursor.execute(
        """
        SELECT COUNT(DISTINCT fo.file_path) as files_touched
        FROM file_operations fo
        JOIN tool_calls tc ON fo.tool_call_id = tc.tool_use_id
        JOIN nodes n ON tc.node_uuid = n.uuid
        WHERE n.session_id = ?
    """,
        (session_id,),
    )

    files_touched = cursor.fetchone()["files_touched"] if cursor.rowcount else 0

    conn.close()

    return {
        "session_id": session_id,
        "duration_minutes": session_meta["duration_minutes"],
        "total_nodes": session_meta["total_nodes"],
        "cwd": session_meta["cwd"],
        "user_messages": user_messages,
        "assistant_snippets": assistant_responses,
        "tool_patterns": tool_patterns,
        "agents_used": agents,
        "files_touched": files_touched,
    }


def analyze_with_claude(digest):
    """Use Claude to analyze the session digest"""

    # Build a focused prompt
    user_requests = "\n".join([f"- {msg}" for msg in digest["user_messages"][:15]])

    assistant_actions = []
    for r in digest["assistant_snippets"][:10]:
        if r.get("end") and r["end"] != r["start"]:
            assistant_actions.append(
                f"- Started: {r['start'][:100]}... Ended: {r['end'][-100:]}"
            )
        else:
            assistant_actions.append(f"- {r['start'][:150]}")
    assistant_text = "\n".join(assistant_actions)

    tools_text = ", ".join(
        [f"{t['tool']} ({t['count']}x)" for t in digest["tool_patterns"][:5]]
    )

    prompt = f"""Analyze this development session and provide a comprehensive summary.

USER REQUESTS:
{user_requests}

ASSISTANT ACTIONS:
{assistant_text}

TECHNICAL CONTEXT:
- Duration: {digest['duration_minutes']} minutes
- Files Modified: {digest['files_touched']}
- Tools Used: {tools_text}
- Agents: {', '.join(digest['agents_used']) if digest['agents_used'] else 'None'}

Based on this session, provide:
1. A descriptive title (5-15 words) that captures what was accomplished
2. A 2-3 sentence summary explaining what was built/fixed/analyzed
3. 3-5 bullet points of specific achievements or features

Focus on WHAT was done, not HOW. Be specific about components and outcomes.

Return your response as valid JSON with this exact structure:
{{"title": "...", "summary": "...", "bullets": ["...", "...", "..."]}}"""

    try:
        # Use claude CLI in headless mode
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--output-format",
                "json",
                "--model",
                "haiku",  # Fast and cheap for this task
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and result.stdout:
            # Parse the JSON response
            response_data = json.loads(result.stdout)

            # Extract the actual response text
            if "result" in response_data:
                # Try to parse the result as JSON
                try:
                    analysis = json.loads(response_data["result"])
                    return analysis
                except:
                    # If not JSON, try to extract from text
                    text = response_data["result"]
                    import re

                    json_match = re.search(r"\{.*\}", text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())

        # Fallback to heuristic
        return generate_fallback_summary(digest)

    except Exception as e:
        print(f"Claude analysis failed: {e}")
        return generate_fallback_summary(digest)


def generate_fallback_summary(digest):
    """Fallback summary when Claude is unavailable"""
    return {
        "title": "Development Session",
        "summary": f"A {digest['duration_minutes']}-minute session with {digest['files_touched']} files modified.",
        "bullets": [
            f"Modified {digest['files_touched']} files",
            f"Used {len(digest['tool_patterns'])} different tools",
            "Session activity completed",
        ],
    }


def analyze_session(session_id, force=False):
    """Analyze a single session and store results"""
    conn = get_db()
    cursor = conn.cursor()

    # Check if already analyzed (unless forced)
    if not force:
        cursor.execute(
            "SELECT * FROM session_analyses WHERE session_id = ?", (session_id,)
        )
        if cursor.fetchone():
            conn.close()
            return None

    # Extract digest
    digest = extract_session_digest(session_id)
    if not digest:
        conn.close()
        return None

    digest_size = len(json.dumps(digest))
    print(f"\nAnalyzing session {session_id}")
    print(f"Digest size: {digest_size} bytes")
    print(f"User messages: {len(digest['user_messages'])}")

    # Skip sessions with no meaningful content
    if not digest["user_messages"]:
        print("Skipping - no user messages")
        conn.close()
        return None

    # Analyze with Claude
    analysis = analyze_with_claude(digest)

    # Store results
    cursor.execute(
        """
        INSERT OR REPLACE INTO session_analyses
        (session_id, title, summary, bullet_points, digest_size, analyzed_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
    print(f"Summary: {analysis['summary'][:100]}...")

    return analysis


def clear_cache():
    """Clear the session summary cache in the web server"""
    # The cache is in-memory, so we need to restart the server
    print("Clearing web server cache...")
    subprocess.run(["pkill", "-f", "chat_logs_web.py"], capture_output=True)
    time.sleep(1)
    # Server will be restarted manually
    print("Cache cleared. Please restart the web server.")


def analyze_all_unanalyzed(limit=20):
    """Analyze all unanalyzed sessions"""
    conn = get_db()
    cursor = conn.cursor()

    # Get unanalyzed sessions
    cursor.execute(
        """
        SELECT s.session_id
        FROM sessions s
        LEFT JOIN session_analyses sa ON s.session_id = sa.session_id
        WHERE sa.session_id IS NULL
        ORDER BY (SELECT MAX(timestamp) FROM nodes WHERE session_id = s.session_id) DESC
        LIMIT ?
    """,
        (limit,),
    )

    sessions = [row["session_id"] for row in cursor.fetchall()]
    conn.close()

    print(f"Found {len(sessions)} unanalyzed sessions")

    for i, session_id in enumerate(sessions, 1):
        print(f"\n[{i}/{len(sessions)}] Processing {session_id}")
        try:
            analyze_session(session_id)
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"Error: {e}")

    print("\n✅ Analysis complete!")
    clear_cache()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            analyze_all_unanalyzed()
        elif sys.argv[1] == "clear-cache":
            clear_cache()
        else:
            # Analyze specific session
            result = analyze_session(sys.argv[1], force=True)
            if result:
                print(json.dumps(result, indent=2))
    else:
        # Test with most recent session
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id FROM sessions
            ORDER BY (SELECT MAX(timestamp) FROM nodes WHERE session_id = sessions.session_id) DESC
            LIMIT 1
        """
        )
        recent = cursor.fetchone()
        conn.close()

        if recent:
            print(f"Testing with session: {recent['session_id']}")
            result = analyze_session(recent["session_id"], force=True)
            if result:
                print(json.dumps(result, indent=2))
