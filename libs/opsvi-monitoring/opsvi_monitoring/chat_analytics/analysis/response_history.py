#!/usr/bin/env python3
"""
Get response time history over time for visualization
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


def get_response_time_history(session_id: str = None) -> List[Dict]:
    """Get response times over time for visualization"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
    WITH user_assistant_pairs AS (
        SELECT
            u.uuid as user_uuid,
            u.timestamp as user_time,
            u.session_id,
            (
                SELECT MIN(a.timestamp)
                FROM nodes a
                WHERE a.node_type = 'assistant'
                AND a.session_id = u.session_id
                AND a.timestamp > u.timestamp
            ) as assistant_time
        FROM nodes u
        WHERE u.node_type = 'user'
        {}
    )
    SELECT
        user_time,
        assistant_time,
        session_id,
        CAST((julianday(assistant_time) - julianday(user_time)) * 86400 AS REAL) as response_seconds
    FROM user_assistant_pairs
    WHERE assistant_time IS NOT NULL
    ORDER BY user_time
    """

    if session_id:
        query = query.format("AND u.session_id = ?")
        cursor = conn.execute(query, (session_id,))
    else:
        query = query.format("")
        cursor = conn.execute(query)

    results = []
    for row in cursor.fetchall():
        results.append(
            {
                "timestamp": row["user_time"],
                "response_seconds": row["response_seconds"],
                "session_id": row["session_id"],
            }
        )

    conn.close()
    return results


if __name__ == "__main__":
    import sys

    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    history = get_response_time_history(session_id)
    print(json.dumps(history[:100], indent=2))  # Show first 100 for testing
