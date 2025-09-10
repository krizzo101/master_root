#!/usr/bin/env python3
"""
Analyze response times and activity patterns from chat logs
"""

import json
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


class ResponseTimeAnalyzer:
    """Analyze response times and activity patterns in chat logs"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_response_times(self, session_id: Optional[str] = None) -> Dict:
        """Calculate response time metrics for prompts"""

        # Query to get user messages and subsequent assistant responses
        query = """
        WITH user_assistant_pairs AS (
            SELECT
                u.uuid as user_uuid,
                u.timestamp as user_time,
                u.session_id,
                json_extract(u.raw_json, '$.message.content') as user_content,
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
            user_uuid,
            user_time,
            assistant_time,
            session_id,
            SUBSTR(user_content, 1, 100) as prompt_preview,
            CAST((julianday(assistant_time) - julianday(user_time)) * 86400 AS REAL) as response_seconds
        FROM user_assistant_pairs
        WHERE assistant_time IS NOT NULL
        ORDER BY user_time
        """

        if session_id:
            query = query.format("AND u.session_id = ?")
            cursor = self.conn.execute(query, (session_id,))
        else:
            query = query.format("")
            cursor = self.conn.execute(query)

        results = cursor.fetchall()

        if not results:
            return {
                "average": 0,
                "median": 0,
                "shortest": {"time": 0, "prompt": ""},
                "longest": {"time": 0, "prompt": ""},
                "total_prompts": 0,
                "by_session": {},
            }

        # Calculate metrics
        response_times = [
            r["response_seconds"] for r in results if r["response_seconds"] is not None
        ]

        if not response_times:
            return {
                "average": 0,
                "median": 0,
                "shortest": {"time": 0, "prompt": ""},
                "longest": {"time": 0, "prompt": ""},
                "total_prompts": 0,
                "by_session": {},
            }

        # Find shortest and longest
        sorted_results = sorted(
            results, key=lambda x: x["response_seconds"] or float("inf")
        )
        shortest = sorted_results[0] if sorted_results else None
        longest = (
            sorted_results[-1]
            if sorted_results and sorted_results[-1]["response_seconds"]
            else None
        )

        # Group by session
        by_session = {}
        for r in results:
            sid = r["session_id"]
            if sid not in by_session:
                by_session[sid] = []
            if r["response_seconds"] is not None:
                by_session[sid].append(r["response_seconds"])

        session_stats = {}
        for sid, times in by_session.items():
            if times:
                session_stats[sid] = {
                    "average": statistics.mean(times),
                    "median": statistics.median(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times),
                }

        return {
            "average": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "shortest": {
                "time": shortest["response_seconds"] if shortest else 0,
                "prompt": shortest["prompt_preview"] if shortest else "",
                "timestamp": shortest["user_time"] if shortest else "",
            },
            "longest": {
                "time": longest["response_seconds"] if longest else 0,
                "prompt": longest["prompt_preview"] if longest else "",
                "timestamp": longest["user_time"] if longest else "",
            },
            "total_prompts": len(response_times),
            "by_session": session_stats,
        }

    def get_activity_timeline(self, session_id: str) -> List[Dict]:
        """Get activity vs dead space timeline for a session"""

        query = """
        SELECT
            uuid,
            node_type,
            timestamp,
            CASE
                WHEN node_type = 'assistant' THEN
                    json_extract(raw_json, '$.message.content[0].type')
                ELSE NULL
            END as content_type
        FROM nodes
        WHERE session_id = ?
        ORDER BY timestamp
        """

        cursor = self.conn.execute(query, (session_id,))
        nodes = cursor.fetchall()

        if not nodes:
            return []

        timeline = []
        prev_time = None

        for i, node in enumerate(nodes):
            curr_time = datetime.fromisoformat(node["timestamp"].replace("Z", "+00:00"))

            if prev_time:
                gap_seconds = (curr_time - prev_time).total_seconds()

                # Mark as activity or dead space
                if gap_seconds > 5:  # More than 5 seconds is considered dead space
                    timeline.append(
                        {
                            "start": prev_time.isoformat(),
                            "end": curr_time.isoformat(),
                            "duration": gap_seconds,
                            "type": "dead_space",
                            "description": f"Idle for {gap_seconds:.1f}s",
                        }
                    )

                # Add the activity
                timeline.append(
                    {
                        "start": curr_time.isoformat(),
                        "end": curr_time.isoformat(),
                        "duration": 0,
                        "type": "activity",
                        "node_type": node["node_type"],
                        "content_type": node["content_type"],
                        "description": f"{node['node_type']} message",
                    }
                )
            else:
                # First node
                timeline.append(
                    {
                        "start": curr_time.isoformat(),
                        "end": curr_time.isoformat(),
                        "duration": 0,
                        "type": "activity",
                        "node_type": node["node_type"],
                        "description": "Session start",
                    }
                )

            prev_time = curr_time

        return timeline

    def get_activity_summary(self, session_id: Optional[str] = None) -> Dict:
        """Get summary of activity vs dead space"""

        query = """
        WITH time_gaps AS (
            SELECT
                session_id,
                timestamp,
                LAG(timestamp) OVER (PARTITION BY session_id ORDER BY timestamp) as prev_timestamp,
                node_type
            FROM nodes
            WHERE session_id {}
            ORDER BY session_id, timestamp
        ),
        gap_analysis AS (
            SELECT
                session_id,
                timestamp,
                prev_timestamp,
                node_type,
                CAST((julianday(timestamp) - julianday(prev_timestamp)) * 86400 AS REAL) as gap_seconds
            FROM time_gaps
            WHERE prev_timestamp IS NOT NULL
        )
        SELECT
            session_id,
            COUNT(*) as total_nodes,
            SUM(CASE WHEN gap_seconds <= 5 THEN gap_seconds ELSE 0 END) as active_time,
            SUM(CASE WHEN gap_seconds > 5 THEN gap_seconds ELSE 0 END) as dead_time,
            MAX(gap_seconds) as max_gap,
            AVG(gap_seconds) as avg_gap
        FROM gap_analysis
        GROUP BY session_id
        """

        if session_id:
            query = query.format("= ?")
            cursor = self.conn.execute(query, (session_id,))
        else:
            query = query.format("IS NOT NULL")
            cursor = self.conn.execute(query)

        results = cursor.fetchall()

        summary = {}
        for row in results:
            total_time = (row["active_time"] or 0) + (row["dead_time"] or 0)
            summary[row["session_id"]] = {
                "total_nodes": row["total_nodes"],
                "active_time_seconds": row["active_time"] or 0,
                "dead_time_seconds": row["dead_time"] or 0,
                "total_time_seconds": total_time,
                "active_percentage": (row["active_time"] / total_time * 100)
                if total_time > 0
                else 0,
                "dead_percentage": (row["dead_time"] / total_time * 100)
                if total_time > 0
                else 0,
                "max_gap_seconds": row["max_gap"] or 0,
                "avg_gap_seconds": row["avg_gap"] or 0,
            }

        return summary


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
    analyzer = ResponseTimeAnalyzer()

    # Get overall response times
    print("\n=== RESPONSE TIME ANALYSIS ===")
    metrics = analyzer.get_response_times()
    print(f"Average response time: {format_duration(metrics['average'])}")
    print(f"Median response time: {format_duration(metrics['median'])}")
    print(
        f"Shortest: {format_duration(metrics['shortest']['time'])} - {metrics['shortest']['prompt'][:50]}..."
    )
    print(
        f"Longest: {format_duration(metrics['longest']['time'])} - {metrics['longest']['prompt'][:50]}..."
    )
    print(f"Total prompts analyzed: {metrics['total_prompts']}")

    # Get activity summary
    print("\n=== ACTIVITY ANALYSIS ===")
    activity = analyzer.get_activity_summary()
    for session_id, stats in list(activity.items())[:5]:  # Show first 5 sessions
        print(f"\nSession {session_id[:8]}...")
        print(
            f"  Active time: {format_duration(stats['active_time_seconds'])} ({stats['active_percentage']:.1f}%)"
        )
        print(
            f"  Dead time: {format_duration(stats['dead_time_seconds'])} ({stats['dead_percentage']:.1f}%)"
        )
        print(f"  Max gap: {format_duration(stats['max_gap_seconds'])}")

    analyzer.close()
