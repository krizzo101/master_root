#!/usr/bin/env python3
"""
Session Analyzer - Extracts conversation essence and generates intelligent summaries using LLM
"""

import hashlib
import json
import sqlite3
import subprocess
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
                        # Handle content blocks
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
                        user_messages.append(
                            {
                                "timestamp": row["timestamp"],
                                "text": text[:500],  # Cap at 500 chars per message
                            }
                        )
        except:
            pass

    # Get assistant response snippets (first and last parts)
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
                    # Extract text from content blocks
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
                        {
                            "timestamp": row["timestamp"],
                            "start": start_snippet,
                            "end": end_snippet,
                        }
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

    # Get files touched (just count, not listing)
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

    # Build digest
    digest = {
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

    # Calculate size
    digest_json = json.dumps(digest)
    digest_size = len(digest_json)

    return digest, digest_size


def analyze_with_llm(digest):
    """Send digest to LLM for intelligent analysis"""

    # Prepare a concise prompt focusing on user requests
    user_requests = "\n".join(
        [f"- {msg['text']}" for msg in digest["user_messages"][:15]]
    )

    # Get key assistant responses
    assistant_actions = []
    for r in digest["assistant_snippets"][:10]:
        if r["end"] and r["end"] != r["start"]:
            assistant_actions.append(f"- {r['start'][:80]}... → {r['end'][-80:]}")
        else:
            assistant_actions.append(f"- {r['start'][:150]}")
    assistant_text = "\n".join(assistant_actions)

    # Build a focused prompt
    prompt = f"""Analyze this development session and create a descriptive summary.

WHAT THE USER ASKED FOR:
{user_requests}

KEY ASSISTANT RESPONSES:
{assistant_text}

TECHNICAL CONTEXT:
- Duration: {digest['duration_minutes']} minutes
- Files Modified: {digest['files_touched']}
- Main Tools: {', '.join([f"{t['tool']}" for t in digest['tool_patterns'][:3]])}
- Agents: {', '.join(digest['agents_used'][:3]) if digest['agents_used'] else 'None'}

Based on what was requested and accomplished, provide:
1. A descriptive title that captures the main achievement (5-15 words)
2. A paragraph explaining what was built/fixed/analyzed (2-3 sentences)
3. 3-5 specific bullet points of features/components/outcomes

Return ONLY a JSON object with this structure:
{{"title": "...", "summary": "...", "bullets": ["...", "...", "..."]}}"""

    try:
        # Use the MCP claude-wrapper for analysis
        result = subprocess.run(
            [
                "python",
                "-c",
                f"""
import json
import sys
sys.path.append('/home/opsvi/master_root/libs')

# Use MCP tool directly
from subprocess import run, PIPE
import tempfile

prompt = '''{prompt}'''

# Write prompt to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(prompt)
    prompt_file = f.name

# Call claude via MCP
result = run([
    'claude', 'run',
    '--output-format', 'json',
    '--max-thinking-words', '1000',
    'Analyze this session digest and return ONLY valid JSON with title, summary, and bullets fields. No other text.',
    '--file', prompt_file
], capture_output=True, text=True)

import os
os.unlink(prompt_file)

if result.returncode == 0:
    try:
        # Extract JSON from response
        response = result.stdout
        # Find JSON in response
        import re
        json_match = re.search(r'\\{{.*\\}}', response, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
            print(json.dumps(analysis))
        else:
            # Fallback
            print(json.dumps({{
                "title": "Development Session",
                "summary": "A development session with multiple interactions.",
                "bullets": ["Session data analyzed"]
            }}))
    except:
        print(json.dumps({{
            "title": "Development Session",
            "summary": "A development session with multiple interactions.",
            "bullets": ["Session data analyzed"]
        }}))
else:
    # Fallback to basic analysis
    print(json.dumps({{
        "title": "Development Session",
        "summary": "A development session with multiple interactions.",
        "bullets": ["Session data analyzed"]
    }}))
""",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        else:
            # Fallback to heuristic analysis
            return generate_heuristic_summary(digest)
    except Exception as e:
        print(f"LLM analysis failed: {e}")
        return generate_heuristic_summary(digest)


def generate_heuristic_summary(digest):
    """Generate summary using heuristics when LLM is unavailable"""

    # Analyze user messages for keywords
    all_text = " ".join([m["text"].lower() for m in digest["user_messages"]])

    # Determine main activity
    title = "Development Session"
    if "dashboard" in all_text or "web" in all_text:
        title = "Web Dashboard Development"
    elif "api" in all_text or "endpoint" in all_text:
        title = "API Development"
    elif "fix" in all_text or "bug" in all_text:
        title = "Bug Fixes and Debugging"
    elif "test" in all_text:
        title = "Testing and Validation"
    elif "analyze" in all_text or "report" in all_text:
        title = "Data Analysis and Reporting"

    # Build summary
    summary = f"A {digest['duration_minutes']}-minute session working on {digest['files_touched']} files."
    if digest["agents_used"]:
        summary += f" Utilized {len(digest['agents_used'])} specialized agents."

    # Generate bullets based on tools
    bullets = []
    if digest["files_touched"] > 0:
        bullets.append(f"Modified {digest['files_touched']} files")
    if any(t["tool"] == "Bash" for t in digest["tool_patterns"]):
        bullets.append("Executed system commands")
    if any(
        "Write" in t["tool"] or "Edit" in t["tool"] for t in digest["tool_patterns"]
    ):
        bullets.append("Implemented code changes")
    if digest["agents_used"]:
        bullets.append(f"Leveraged {', '.join(digest['agents_used'][:3])} agents")

    return {"title": title, "summary": summary, "bullets": bullets}


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
            return  # Already analyzed

    # Extract digest
    result = extract_session_digest(session_id)
    if not result:
        conn.close()
        return

    digest, digest_size = result

    # Analyze with LLM
    analysis = analyze_with_llm(digest)

    # Store results
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

    print(f"Analyzed session {session_id}: {analysis['title']}")
    return analysis


def analyze_all_sessions(limit=100):
    """Analyze all unanalyzed sessions"""
    conn = get_db()
    cursor = conn.cursor()

    # Get sessions that haven't been analyzed
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

    for i, session_id in enumerate(sessions):
        print(f"Analyzing {i+1}/{len(sessions)}: {session_id}")
        try:
            analyze_session(session_id)
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"Failed to analyze {session_id}: {e}")

    print("Analysis complete!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            analyze_all_sessions()
        else:
            # Analyze specific session
            analyze_session(sys.argv[1], force=True)
    else:
        # Test with a recent session
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
            print(f"Testing with recent session: {recent['session_id']}")
            result = analyze_session(recent["session_id"], force=True)
            if result:
                print(json.dumps(result, indent=2))
