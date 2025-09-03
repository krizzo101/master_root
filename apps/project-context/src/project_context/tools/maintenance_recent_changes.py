"""Recent changes tracking for Project Context MCP Server."""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..db.connections import get_db


async def get_recent_changes(hours_back: int = 24, limit: int = 100) -> Dict[str, Any]:
    """Recent changes from context_items - Time-series queries for changes.

    Analyzes recent changes across multiple tables using time-series queries:
    - Recent context_items entries with change analysis
    - Code element modifications and additions
    - Cross-reference with monitoring_metrics for activity patterns
    - Session-based change tracking and file modification patterns

    Args:
        hours_back: How many hours back to look for changes (default: 24)
        limit: Maximum number of recent changes to return (default: 100)

    Returns:
        Dictionary containing recent changes analysis:
        - recent_context_changes: Latest context_items with change metadata
        - code_element_changes: Recent code modifications and additions
        - session_activity: Recent session-based activities
        - file_changes: File-level change patterns and frequency
        - time_series_data: Temporal analysis of change patterns
        - change_velocity: Rate of changes over time periods
        - top_active_files: Files with most recent activity
        - recommendations: Insights based on recent change patterns
    """

    try:
        db = await get_db()

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "time_window_hours": hours_back,
            "recent_context_changes": [],
            "code_element_changes": [],
            "session_activity": [],
            "file_changes": {},
            "time_series_data": {},
            "change_velocity": {},
            "top_active_files": [],
            "stats": {
                "total_changes": 0,
                "unique_sessions": 0,
                "unique_files": 0,
                "change_types": {},
            },
            "recommendations": [],
        }

        # Query recent context_items changes
        try:
            context_query = """
            SELECT
                id,
                source_type,
                entity_type,
                content,
                metrics,
                session_id,
                created_at,
                EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as hours_ago
            FROM context_items
            WHERE created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT %s
            """ % (
                hours_back,
                limit,
            )

            context_changes = await db.fetch_many(context_query)

            # Process context changes and extract file paths
            file_activity = {}
            session_activity = {}
            change_types = {}

            for change in context_changes:
                # Extract file path from content or metrics
                file_path = None
                if change["metrics"]:
                    if isinstance(change["metrics"], dict):
                        file_path = change["metrics"].get("file_path")
                    elif isinstance(change["metrics"], str):
                        try:
                            metrics_dict = json.loads(change["metrics"])
                            file_path = metrics_dict.get("file_path")
                        except:
                            pass

                # If no file path in metrics, try to extract from content
                if not file_path and change["content"]:
                    path_patterns = [
                        r"(?:file|path):\s*([^\s\n]+)",
                        r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.[a-z]+)",
                        r"/([a-zA-Z0-9_/.-]+\.[a-z]+)",
                    ]
                    for pattern in path_patterns:
                        match = re.search(pattern, change["content"], re.IGNORECASE)
                        if match:
                            file_path = match.group(1)
                            break

                # Track file activity
                if file_path:
                    if file_path not in file_activity:
                        file_activity[file_path] = {
                            "change_count": 0,
                            "sessions": set(),
                            "source_types": set(),
                            "entity_types": set(),
                            "latest_change": change["created_at"],
                            "earliest_change": change["created_at"],
                        }

                    file_activity[file_path]["change_count"] += 1
                    if change["session_id"]:
                        file_activity[file_path]["sessions"].add(change["session_id"])
                    file_activity[file_path]["source_types"].add(change["source_type"])
                    file_activity[file_path]["entity_types"].add(change["entity_type"])
                    if change["created_at"] > file_activity[file_path]["latest_change"]:
                        file_activity[file_path]["latest_change"] = change["created_at"]
                    if (
                        change["created_at"]
                        < file_activity[file_path]["earliest_change"]
                    ):
                        file_activity[file_path]["earliest_change"] = change[
                            "created_at"
                        ]

                # Track session activity
                if change["session_id"]:
                    if change["session_id"] not in session_activity:
                        session_activity[change["session_id"]] = {
                            "change_count": 0,
                            "source_types": set(),
                            "entity_types": set(),
                            "files": set(),
                            "latest_activity": change["created_at"],
                            "earliest_activity": change["created_at"],
                        }

                    session_activity[change["session_id"]]["change_count"] += 1
                    session_activity[change["session_id"]]["source_types"].add(
                        change["source_type"]
                    )
                    session_activity[change["session_id"]]["entity_types"].add(
                        change["entity_type"]
                    )
                    if file_path:
                        session_activity[change["session_id"]]["files"].add(file_path)
                    if (
                        change["created_at"]
                        > session_activity[change["session_id"]]["latest_activity"]
                    ):
                        session_activity[change["session_id"]][
                            "latest_activity"
                        ] = change["created_at"]
                    if (
                        change["created_at"]
                        < session_activity[change["session_id"]]["earliest_activity"]
                    ):
                        session_activity[change["session_id"]][
                            "earliest_activity"
                        ] = change["created_at"]

                # Track change types
                change_key = f"{change['source_type']}:{change['entity_type']}"
                change_types[change_key] = change_types.get(change_key, 0) + 1

            result["recent_context_changes"] = context_changes
            result["stats"]["total_changes"] = len(context_changes)
            result["stats"]["change_types"] = change_types

        except Exception as e:
            result["recent_context_changes"] = []
            result["recommendations"].append(
                f"Failed to query recent context changes: {str(e)}"
            )

        # Query recent code element changes (if table exists)
        try:
            code_query = """
            SELECT
                file_path,
                element_name,
                element_type,
                line_start,
                line_end,
                complexity_score,
                created_at,
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - COALESCE(updated_at, created_at)))/3600 as hours_ago
            FROM code_elements
            WHERE COALESCE(updated_at, created_at) > NOW() - INTERVAL '%s hours'
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT %s
            """ % (
                hours_back,
                limit,
            )

            code_changes = await db.fetch_many(code_query)
            result["code_element_changes"] = code_changes

        except Exception as e:
            result["code_element_changes"] = []
            result["recommendations"].append(
                f"Code elements table not available or error: {str(e)}"
            )

        # Convert sets to lists and process file activity
        processed_file_activity = {}
        for file_path, activity in file_activity.items():
            processed_file_activity[file_path] = {
                "change_count": activity["change_count"],
                "session_count": len(activity["sessions"]),
                "sessions": list(activity["sessions"]),
                "source_types": list(activity["source_types"]),
                "entity_types": list(activity["entity_types"]),
                "latest_change": activity["latest_change"].isoformat()
                if hasattr(activity["latest_change"], "isoformat")
                else str(activity["latest_change"]),
                "earliest_change": activity["earliest_change"].isoformat()
                if hasattr(activity["earliest_change"], "isoformat")
                else str(activity["earliest_change"]),
            }

        result["file_changes"] = processed_file_activity
        result["stats"]["unique_files"] = len(processed_file_activity)

        # Process session activity
        processed_session_activity = []
        for session_id, activity in session_activity.items():
            processed_session_activity.append(
                {
                    "session_id": session_id,
                    "change_count": activity["change_count"],
                    "file_count": len(activity["files"]),
                    "files": list(activity["files"]),
                    "source_types": list(activity["source_types"]),
                    "entity_types": list(activity["entity_types"]),
                    "latest_activity": activity["latest_activity"].isoformat()
                    if hasattr(activity["latest_activity"], "isoformat")
                    else str(activity["latest_activity"]),
                    "earliest_activity": activity["earliest_activity"].isoformat()
                    if hasattr(activity["earliest_activity"], "isoformat")
                    else str(activity["earliest_activity"]),
                }
            )

        result["session_activity"] = sorted(
            processed_session_activity, key=lambda x: x["change_count"], reverse=True
        )
        result["stats"]["unique_sessions"] = len(processed_session_activity)

        # Generate top active files
        result["top_active_files"] = sorted(
            [{"file_path": fp, **data} for fp, data in processed_file_activity.items()],
            key=lambda x: x["change_count"],
            reverse=True,
        )[
            :20
        ]  # Top 20 most active files

        # Time series analysis - group changes by hour
        try:
            time_series_query = (
                """
            SELECT
                DATE_TRUNC('hour', created_at) as hour_bucket,
                COUNT(*) as change_count,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT source_type) as unique_source_types
            FROM context_items
            WHERE created_at > NOW() - INTERVAL '%s hours'
            GROUP BY hour_bucket
            ORDER BY hour_bucket
            """
                % hours_back
            )

            time_series_data = await db.fetch_many(time_series_query)

            # Calculate change velocity (changes per hour)
            if time_series_data:
                total_changes = sum(row["change_count"] for row in time_series_data)
                total_hours = len(time_series_data) if time_series_data else 1
                avg_changes_per_hour = total_changes / total_hours

                result["change_velocity"] = {
                    "total_changes": total_changes,
                    "total_hours": total_hours,
                    "avg_changes_per_hour": round(avg_changes_per_hour, 2),
                    "peak_hour": max(time_series_data, key=lambda x: x["change_count"])
                    if time_series_data
                    else None,
                    "quiet_hour": min(time_series_data, key=lambda x: x["change_count"])
                    if time_series_data
                    else None,
                }

            result["time_series_data"] = time_series_data

        except Exception as e:
            result["time_series_data"] = []
            result["change_velocity"] = {}
            result["recommendations"].append(f"Time series analysis failed: {str(e)}")

        # Generate recommendations based on analysis
        if result["stats"]["total_changes"] == 0:
            result["recommendations"].append(
                "No recent changes detected - system may be inactive"
            )
        elif result["stats"]["total_changes"] > 500:
            result["recommendations"].append(
                "High activity detected - monitor for potential issues"
            )

        if result["stats"]["unique_sessions"] > 10:
            result["recommendations"].append(
                "Multiple active sessions detected - coordinate development efforts"
            )

        if len(result["top_active_files"]) > 0:
            most_active = result["top_active_files"][0]
            if most_active["change_count"] > 50:
                result["recommendations"].append(
                    f"File '{most_active['file_path']}' has very high activity ({most_active['change_count']} changes)"
                )

        if not result["recommendations"]:
            result["recommendations"].append("Change patterns appear normal")

        return result

    except Exception as e:
        return {
            "error": f"Failed to get recent changes: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "time_window_hours": hours_back,
            "recent_context_changes": [],
            "code_element_changes": [],
            "session_activity": [],
            "file_changes": {},
            "time_series_data": {},
            "change_velocity": {},
            "top_active_files": [],
            "stats": {
                "total_changes": 0,
                "unique_sessions": 0,
                "unique_files": 0,
                "change_types": {},
            },
            "recommendations": [
                "Failed to analyze recent changes - check database connection"
            ],
        }
