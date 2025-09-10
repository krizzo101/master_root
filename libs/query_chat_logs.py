#!/usr/bin/env python3
"""
Query interface for the chat logs database
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


def query_recent_sessions(limit=10):
    """Get most recent sessions"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            s.session_id,
            s.cwd,
            COUNT(n.uuid) as message_count,
            MIN(n.timestamp) as start_time,
            MAX(n.timestamp) as end_time
        FROM sessions s
        JOIN nodes n ON s.session_id = n.session_id
        GROUP BY s.session_id
        ORDER BY MAX(n.timestamp) DESC
        LIMIT ?
    """,
        (limit,),
    )

    results = cursor.fetchall()
    conn.close()

    print(f"\n=== MOST RECENT {limit} SESSIONS ===")
    for row in results:
        print(f"\nSession: {row['session_id'][:8]}...")
        print(f"  CWD: {row['cwd']}")
        print(f"  Messages: {row['message_count']}")
        print(f"  Start: {row['start_time']}")
        print(f"  End: {row['end_time']}")


def query_file_activity(file_pattern):
    """Query activity on specific files"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            fo.file_path,
            fo.operation,
            tc.timestamp,
            tc.tool_name,
            n.session_id
        FROM file_operations fo
        JOIN tool_calls tc ON fo.tool_call_id = tc.tool_use_id
        JOIN nodes n ON tc.node_uuid = n.uuid
        WHERE fo.file_path LIKE ?
        ORDER BY tc.timestamp DESC
        LIMIT 20
    """,
        (f"%{file_pattern}%",),
    )

    results = cursor.fetchall()
    conn.close()

    print(f"\n=== FILE ACTIVITY: {file_pattern} ===")
    for row in results:
        print(f"\n{row['timestamp']}")
        print(f"  File: {row['file_path']}")
        print(f"  Operation: {row['operation']}")
        print(f"  Tool: {row['tool_name']}")
        print(f"  Session: {row['session_id'][:8]}...")


def query_tool_errors():
    """Find tool errors"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            tc.tool_name,
            COUNT(*) as error_count,
            COUNT(DISTINCT n.session_id) as sessions_affected
        FROM tool_results tr
        JOIN tool_calls tc ON tr.tool_use_id = tc.tool_use_id
        JOIN nodes n ON tr.node_uuid = n.uuid
        WHERE tr.is_error = 1
        GROUP BY tc.tool_name
        ORDER BY error_count DESC
        LIMIT 10
    """
    )

    results = cursor.fetchall()
    conn.close()

    print("\n=== TOP TOOL ERRORS ===")
    for row in results:
        print(
            f"{row['tool_name']:30} Errors: {row['error_count']:5}  Sessions: {row['sessions_affected']}"
        )


def search_messages(search_term):
    """Search in user messages"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            n.session_id,
            n.timestamp,
            n.raw_json
        FROM nodes n
        WHERE n.node_type = 'user'
        AND n.raw_json LIKE ?
        ORDER BY n.timestamp DESC
        LIMIT 10
    """,
        (f"%{search_term}%",),
    )

    results = cursor.fetchall()
    conn.close()

    print(f"\n=== SEARCH RESULTS: '{search_term}' ===")
    for row in results:
        try:
            data = json.loads(row["raw_json"])
            content = data.get("message", {}).get("content", "")[:200]
            print(f"\n{row['timestamp']}")
            print(f"  Session: {row['session_id'][:8]}...")
            print(f"  Content: {content}...")
        except:
            continue


def main():
    """Run example queries"""
    print("CHAT LOG QUERY EXAMPLES")
    print("=" * 60)

    # Recent sessions
    query_recent_sessions(5)

    # File activity
    query_file_activity("UNIFIED_CONTEXT_SYSTEM")

    # Tool errors
    query_tool_errors()

    # Search messages
    search_messages("taxonomy")


if __name__ == "__main__":
    main()
