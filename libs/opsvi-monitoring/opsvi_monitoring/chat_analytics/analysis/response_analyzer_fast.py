#!/usr/bin/env python3
"""
Fast response time analyzer with optimized queries
"""

import json
import sqlite3
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


class FastResponseTimeAnalyzer:
    """Optimized response time analyzer"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_response_times_fast(
        self, session_id: Optional[str] = None, limit: int = 5000
    ) -> Dict:
        """Fast calculation of response time metrics"""

        # Much faster query using window functions
        if session_id:
            query = """
            WITH message_pairs AS (
                SELECT
                    timestamp,
                    node_type,
                    session_id,
                    LEAD(timestamp) OVER (PARTITION BY session_id ORDER BY timestamp) as next_timestamp,
                    LEAD(node_type) OVER (PARTITION BY session_id ORDER BY timestamp) as next_type,
                    SUBSTR(json_extract(raw_json, '$.message.content'), 1, 100) as content_preview
                FROM nodes
                WHERE session_id = ?
                    AND node_type IN ('user', 'assistant')
                ORDER BY timestamp
            )
            SELECT
                session_id,
                content_preview,
                timestamp as user_time,
                next_timestamp as assistant_time,
                CAST((julianday(next_timestamp) - julianday(timestamp)) * 86400 AS REAL) as response_seconds
            FROM message_pairs
            WHERE node_type = 'user'
                AND next_type = 'assistant'
                AND response_seconds IS NOT NULL
            LIMIT ?
            """
            cursor = self.conn.execute(query, (session_id, limit))
        else:
            # For all sessions, sample to keep it fast
            query = """
            WITH sampled_sessions AS (
                SELECT DISTINCT session_id
                FROM sessions
                ORDER BY created_at DESC
                LIMIT 100
            ),
            message_pairs AS (
                SELECT
                    n.timestamp,
                    n.node_type,
                    n.session_id,
                    LEAD(n.timestamp) OVER (PARTITION BY n.session_id ORDER BY n.timestamp) as next_timestamp,
                    LEAD(n.node_type) OVER (PARTITION BY n.session_id ORDER BY n.timestamp) as next_type,
                    SUBSTR(json_extract(n.raw_json, '$.message.content'), 1, 100) as content_preview
                FROM nodes n
                INNER JOIN sampled_sessions s ON n.session_id = s.session_id
                WHERE n.node_type IN ('user', 'assistant')
            )
            SELECT
                session_id,
                content_preview,
                timestamp as user_time,
                next_timestamp as assistant_time,
                CAST((julianday(next_timestamp) - julianday(timestamp)) * 86400 AS REAL) as response_seconds
            FROM message_pairs
            WHERE node_type = 'user'
                AND next_type = 'assistant'
                AND response_seconds IS NOT NULL
                AND response_seconds < 86400  -- Exclude responses > 1 day (likely errors)
            LIMIT ?
            """
            cursor = self.conn.execute(query, (limit,))

        results = cursor.fetchall()

        if not results:
            return {
                "average": 0,
                "median": 0,
                "shortest": {"time": 0, "prompt": "", "timestamp": ""},
                "longest": {"time": 0, "prompt": "", "timestamp": ""},
                "total_prompts": 0,
                "by_session": {},
            }

        # Process results
        response_times = []
        by_session = {}

        for row in results:
            if row["response_seconds"] and row["response_seconds"] > 0:
                response_times.append(row["response_seconds"])

                sid = row["session_id"]
                if sid not in by_session:
                    by_session[sid] = []
                by_session[sid].append(row["response_seconds"])

        if not response_times:
            return {
                "average": 0,
                "median": 0,
                "shortest": {"time": 0, "prompt": "", "timestamp": ""},
                "longest": {"time": 0, "prompt": "", "timestamp": ""},
                "total_prompts": 0,
                "by_session": {},
            }

        # Find extremes
        sorted_results = sorted(
            results, key=lambda x: x["response_seconds"] or float("inf")
        )
        shortest = sorted_results[0]
        longest = sorted_results[-1]

        # Calculate session stats (limit to top 10 for display)
        session_stats = {}
        for sid, times in list(by_session.items())[:10]:
            if times:
                session_stats[sid] = {
                    "average": statistics.mean(times),
                    "median": statistics.median(times) if len(times) > 1 else times[0],
                    "min": min(times),
                    "max": max(times),
                    "count": len(times),
                }

        return {
            "average": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "shortest": {
                "time": shortest["response_seconds"],
                "prompt": shortest["content_preview"] or "",
                "timestamp": shortest["user_time"],
            },
            "longest": {
                "time": longest["response_seconds"],
                "prompt": longest["content_preview"] or "",
                "timestamp": longest["user_time"],
            },
            "total_prompts": len(response_times),
            "by_session": session_stats,
        }


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


if __name__ == "__main__":
    import time

    print("Testing fast response time analyzer...")
    start = time.time()

    analyzer = FastResponseTimeAnalyzer()
    metrics = analyzer.get_response_times_fast()

    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.2f} seconds")

    print(f"Average: {format_duration(metrics['average'])}")
    print(f"Median: {format_duration(metrics['median'])}")
    print(f"Shortest: {format_duration(metrics['shortest']['time'])}")
    print(f"Longest: {format_duration(metrics['longest']['time'])}")
    print(f"Total prompts: {metrics['total_prompts']}")

    analyzer.close()
