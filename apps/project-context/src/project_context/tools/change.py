"""Change tracking tools for project context."""

import json
import re
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from ..db.connections import get_db


async def get_recent_changes(
    session_id: Optional[str] = None,
    limit: int = 50,
    hours_back: int = 24,
    file_pattern: Optional[str] = None,
    action_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Recent changes from context_items - Time-series queries for changes.

    Analyzes recent changes across multiple tables using time-series queries:
    - Recent context_items entries with change analysis
    - Code element modifications and additions
    - Cross-reference with monitoring_metrics for activity patterns
    - Session-based change tracking and file modification patterns
    - Traditional file_activity changes (existing functionality)

    Args:
        session_id: Filter by specific session ID
        limit: Maximum number of changes to return (default: 50)
        hours_back: How many hours back to look (default: 24)
        file_pattern: SQL LIKE pattern to filter file paths
        action_filter: Filter by action type (create, modify, delete, read)

    Returns:
        Dict containing recent changes analysis with time-series data,
        cross-table references, and comprehensive change tracking
    """
    db = await get_db()

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "time_window_hours": hours_back,
        "recent_context_changes": [],
        "recent_file_activity": [],
        "code_element_changes": [],
        "session_activity": [],
        "file_changes": {},
        "time_series_data": {},
        "change_velocity": {},
        "top_active_files": [],
        "legacy_file_activity": {},  # Original file_activity results
        "stats": {
            "total_changes": 0,
            "total_context_changes": 0,
            "total_file_changes": 0,
            "unique_sessions": 0,
            "unique_files": 0,
            "change_types": {},
        },
        "recommendations": [],
    }

    # 1. Query recent context_items changes (New functionality)
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
                if change["created_at"] < file_activity[file_path]["earliest_change"]:
                    file_activity[file_path]["earliest_change"] = change["created_at"]

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
                    session_activity[change["session_id"]]["latest_activity"] = change[
                        "created_at"
                    ]
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
        result["stats"]["total_context_changes"] = len(context_changes)
        result["stats"]["change_types"] = change_types

    except Exception as e:
        result["recent_context_changes"] = []
        result["recommendations"].append(
            f"Failed to query recent context changes: {str(e)}"
        )

    # 2. Query recent code element changes
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

    # 3. Original file_activity query (Legacy functionality)
    # Build the query with optional filters
    where_conditions = ["timestamp >= NOW() - INTERVAL '%s hours'" % hours_back]
    params = []
    param_idx = 1

    if session_id:
        where_conditions.append(f"session_id = ${param_idx}")
        params.append(session_id)
        param_idx += 1

    if file_pattern:
        where_conditions.append(f"file_path LIKE ${param_idx}")
        params.append(file_pattern)
        param_idx += 1

    if action_filter:
        where_conditions.append(f"action = ${param_idx}")
        params.append(action_filter)
        param_idx += 1

    where_clause = " AND ".join(where_conditions)

    # Query for recent changes with grouping
    query = f"""
    SELECT
        fa.session_id,
        fa.timestamp,
        fa.file_path,
        fa.action,
        fa.tool_used,
        fa.functions_affected,
        fa.classes_affected,
        fa.before_hash,
        fa.after_hash,
        -- Session context from chat_sessions if available
        cs.user_id,
        cs.project_path,
        cs.model_used
    FROM file_activity fa
    LEFT JOIN chat_sessions cs ON fa.session_id = cs.id
    WHERE {where_clause}
    ORDER BY fa.timestamp DESC, fa.session_id
    LIMIT ${param_idx}
    """
    params.append(limit)

    try:
        rows = await db.fetch_many(query, *params)
        result["recent_file_activity"] = rows
        result["stats"]["total_file_changes"] = len(rows)
    except Exception as e:
        result["recent_file_activity"] = []
        result["recommendations"].append(
            f"Failed to query file_activity table: {str(e)}"
        )

    # 4. Process and analyze the data
    # Convert sets to lists for JSON serialization
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

    # 5. Time series analysis - group changes by hour
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

    # 6. Process legacy file_activity data for backward compatibility
    rows = result["recent_file_activity"]
    changes_by_session = {}
    all_changes = []
    change_summary = {
        "total_changes": len(rows),
        "sessions_affected": set(),
        "files_affected": set(),
        "action_counts": {},
        "tool_usage": {},
        "time_range": {"earliest": None, "latest": None},
    }

    for row in rows:
        session_id = row["session_id"]
        timestamp = row["timestamp"]
        action = row["action"]
        tool_used = row["tool_used"]

        # Track summary statistics
        change_summary["sessions_affected"].add(session_id)
        change_summary["files_affected"].add(row["file_path"])
        change_summary["action_counts"][action] = (
            change_summary["action_counts"].get(action, 0) + 1
        )
        if tool_used:
            change_summary["tool_usage"][tool_used] = (
                change_summary["tool_usage"].get(tool_used, 0) + 1
            )

        # Track time range
        if (
            change_summary["time_range"]["earliest"] is None
            or timestamp < change_summary["time_range"]["earliest"]
        ):
            change_summary["time_range"]["earliest"] = timestamp
        if (
            change_summary["time_range"]["latest"] is None
            or timestamp > change_summary["time_range"]["latest"]
        ):
            change_summary["time_range"]["latest"] = timestamp

        # Group by session
        if session_id not in changes_by_session:
            changes_by_session[session_id] = {
                "session_id": session_id,
                "user_id": row["user_id"],
                "project_path": row["project_path"],
                "model_used": row["model_used"],
                "changes": [],
                "change_count": 0,
                "files_touched": set(),
                "actions_performed": set(),
            }

        session_group = changes_by_session[session_id]
        session_group["change_count"] += 1
        session_group["files_touched"].add(row["file_path"])
        session_group["actions_performed"].add(action)

        # Individual change record
        change_record = {
            "timestamp": timestamp.isoformat(),
            "file_path": row["file_path"],
            "action": action,
            "tool_used": tool_used,
            "functions_affected": row["functions_affected"]
            if row["functions_affected"]
            else [],
            "classes_affected": row["classes_affected"]
            if row["classes_affected"]
            else [],
            "content_changed": row["before_hash"] != row["after_hash"]
            if row["before_hash"] and row["after_hash"]
            else None,
        }

        session_group["changes"].append(change_record)
        all_changes.append(
            {
                **change_record,
                "session_id": session_id,
                "user_id": row["user_id"],
                "project_path": row["project_path"],
            }
        )

    # Convert sets to lists for JSON serialization
    change_summary["sessions_affected"] = len(change_summary["sessions_affected"])
    change_summary["files_affected"] = len(change_summary["files_affected"])
    change_summary["time_range"]["earliest"] = (
        change_summary["time_range"]["earliest"].isoformat()
        if change_summary["time_range"]["earliest"]
        else None
    )
    change_summary["time_range"]["latest"] = (
        change_summary["time_range"]["latest"].isoformat()
        if change_summary["time_range"]["latest"]
        else None
    )

    for session_data in changes_by_session.values():
        session_data["files_touched"] = list(session_data["files_touched"])
        session_data["actions_performed"] = list(session_data["actions_performed"])

    # Store legacy results for backward compatibility
    result["legacy_file_activity"] = {
        "summary": change_summary,
        "changes_by_session": list(changes_by_session.values()),
        "all_changes": all_changes,
        "query_parameters": {
            "session_id": session_id,
            "limit": limit,
            "hours_back": hours_back,
            "file_pattern": file_pattern,
            "action_filter": action_filter,
        },
    }

    # Calculate total changes from all sources
    result["stats"]["total_changes"] = (
        result["stats"]["total_context_changes"]
        + result["stats"]["total_file_changes"]
        + len(result["code_element_changes"])
    )

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


async def search_code(
    query: str,
    file_pattern: Optional[str] = None,
    language: Optional[str] = None,
    element_type: Optional[str] = None,
    use_regex: bool = False,
    context_lines: int = 3,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Full-text code search using PostgreSQL full-text search and regex patterns.

    Args:
        query: Search query text or regex pattern
        file_pattern: Optional glob-like pattern to filter files (e.g. "*.py", "src/**/*.js")
        language: Programming language filter (e.g. "python", "javascript")
        element_type: Code element type filter (e.g. "function", "class", "import")
        use_regex: If True, treat query as regex pattern; if False, use full-text search
        context_lines: Number of lines of context around matches (default: 3)
        limit: Maximum number of results to return (default: 50)

    Returns:
        Dictionary containing search results with matching code segments,
        file locations, line numbers, and surrounding context.
    """
    try:
        db = await get_db()

        # Build the base query
        base_query = """
        SELECT
            file_path,
            element_type,
            element_name,
            signature,
            docstring,
            line_start,
            line_end,
            language,
            complexity_score,
            last_modified,
            proj_intel_data
        FROM code_elements
        WHERE 1=1
        """

        params = []
        param_count = 0

        # Add search condition based on mode
        if use_regex:
            # Regex search on multiple text fields
            param_count += 1
            base_query += f"""
            AND (
                element_name ~ ${param_count}
                OR signature ~ ${param_count}
                OR docstring ~ ${param_count}
                OR (proj_intel_data->>'full_content') ~ ${param_count}
            )
            """
            params.append(query)
        else:
            # Full-text search using PostgreSQL's to_tsquery
            param_count += 1
            # Convert simple query to tsquery format
            # Handle phrases and multiple terms
            if '"' in query:
                # Phrase search - keep as is but escape single quotes
                ts_query = query.replace("'", "''")
            elif " " in query:
                # Multiple terms - join with &
                terms = query.split()
                ts_query = " & ".join(term.replace("'", "''") for term in terms)
            else:
                # Single term
                ts_query = query.replace("'", "''")

            base_query += f"""
            AND (
                search_vector @@ to_tsquery('english', ${param_count})
                OR element_name ILIKE ${param_count + 1}
                OR signature ILIKE ${param_count + 1}
            )
            """
            params.append(ts_query)
            param_count += 1
            params.append(f"%{query}%")

        # Add file pattern filter
        if file_pattern:
            param_count += 1
            # Convert glob pattern to SQL LIKE pattern
            sql_pattern = file_pattern.replace("*", "%").replace("?", "_")
            base_query += f" AND file_path LIKE ${param_count}"
            params.append(sql_pattern)

        # Add language filter
        if language:
            param_count += 1
            base_query += f" AND language = ${param_count}"
            params.append(language)

        # Add element type filter
        if element_type:
            param_count += 1
            base_query += f" AND element_type = ${param_count}"
            params.append(element_type)

        # Add ordering and limit
        param_count += 1
        order_param = param_count
        params.append(f"%{query}%")

        base_query += f"""
        ORDER BY
            CASE WHEN element_name ILIKE ${order_param} THEN 0 ELSE 1 END,
            complexity_score DESC NULLS LAST,
            file_path,
            COALESCE(line_start, 0)
        LIMIT ${param_count + 1}
        """
        params.append(limit)

        async with db.pg_pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)

            results = []

            for row in rows:
                proj_data = row.get("proj_intel_data") or {}
                full_content = proj_data.get("full_content", "")

                # Extract matching lines with context
                matching_lines = []
                if full_content:
                    matching_lines = await _extract_matching_lines(
                        full_content,
                        query,
                        use_regex,
                        context_lines,
                        row.get("line_start", 1),
                    )

                result = {
                    "file_path": row["file_path"],
                    "element_type": row["element_type"],
                    "element_name": row["element_name"],
                    "language": row["language"],
                    "complexity": float(row["complexity_score"])
                    if row["complexity_score"]
                    else None,
                    "signature": row["signature"],
                    "start_line": row["line_start"],
                    "end_line": row["line_end"],
                    "docstring": row["docstring"],
                    "last_modified": row["last_modified"].isoformat()
                    if row["last_modified"]
                    else None,
                    "matching_lines": matching_lines,
                    "match_count": len(matching_lines),
                }
                results.append(result)

            # Calculate summary statistics
            total_matches = sum(r["match_count"] for r in results)
            unique_files = len(set(r["file_path"] for r in results))
            languages = list(set(r["language"] for r in results if r["language"]))

            return {
                "success": True,
                "query": query,
                "search_mode": "regex" if use_regex else "full_text",
                "filters_applied": {
                    "file_pattern": file_pattern,
                    "language": language,
                    "element_type": element_type,
                    "context_lines": context_lines,
                    "limit": limit,
                },
                "summary": {
                    "total_results": len(results),
                    "total_matches": total_matches,
                    "unique_files": unique_files,
                    "languages": languages,
                    "limit_reached": len(results) == limit,
                },
                "results": results,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search code: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "query": query,
            "search_mode": "regex" if use_regex else "full_text",
            "results": [],
        }


async def _extract_matching_lines(
    content: str,
    query: str,
    use_regex: bool,
    context_lines: int,
    start_line_offset: int = 1,
) -> List[Dict[str, Any]]:
    """
    Extract lines that match the query with surrounding context.

    Args:
        content: Full content to search in
        query: Search query or regex pattern
        use_regex: Whether to use regex matching
        context_lines: Number of context lines around matches
        start_line_offset: Offset to add to line numbers for absolute positioning

    Returns:
        List of dictionaries containing matching lines with context
    """
    if not content:
        return []

    lines = content.split("\n")
    matches = []

    try:
        if use_regex:
            # Compile regex pattern
            try:
                pattern = re.compile(query, re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                # If regex is invalid, treat as literal string
                pattern = re.compile(re.escape(query), re.IGNORECASE)
        else:
            # Simple case-insensitive string search
            query_lower = query.lower()

        for line_idx, line in enumerate(lines):
            line_matches = False

            if use_regex:
                if pattern.search(line):
                    line_matches = True
            else:
                if query_lower in line.lower():
                    line_matches = True

            if line_matches:
                # Calculate context window
                start_ctx = max(0, line_idx - context_lines)
                end_ctx = min(len(lines), line_idx + context_lines + 1)

                # Extract context lines
                context = []
                for ctx_idx in range(start_ctx, end_ctx):
                    context.append(
                        {
                            "line_number": ctx_idx + start_line_offset,
                            "content": lines[ctx_idx],
                            "is_match": ctx_idx == line_idx,
                        }
                    )

                match_info = {
                    "line_number": line_idx + start_line_offset,
                    "line_content": line,
                    "context": context,
                    "context_start": start_ctx + start_line_offset,
                    "context_end": end_ctx + start_line_offset - 1,
                }

                # Add regex match details if applicable
                if use_regex:
                    regex_matches = list(pattern.finditer(line))
                    if regex_matches:
                        match_info["regex_matches"] = [
                            {
                                "match_text": m.group(),
                                "start_pos": m.start(),
                                "end_pos": m.end(),
                                "groups": m.groups(),
                            }
                            for m in regex_matches
                        ]

                matches.append(match_info)

    except Exception as e:
        # Return basic match info on error
        for line_idx, line in enumerate(lines):
            if query.lower() in line.lower():
                matches.append(
                    {
                        "line_number": line_idx + start_line_offset,
                        "line_content": line,
                        "context": [
                            {
                                "line_number": line_idx + start_line_offset,
                                "content": line,
                                "is_match": True,
                            }
                        ],
                        "error": f"Context extraction failed: {str(e)}",
                    }
                )

    return matches


async def search_files_by_content(
    content_query: str,
    file_extension: Optional[str] = None,
    modified_since: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Search for files based on their content using full-text search.

    Args:
        content_query: Text to search for in file contents
        file_extension: Optional file extension filter (e.g. "py", "js")
        modified_since: Optional ISO date string to filter by modification date
        limit: Maximum number of files to return

    Returns:
        Dictionary containing matching files and their metadata
    """
    try:
        db = await get_db()

        query = """
        SELECT DISTINCT
            file_path,
            language,
            last_modified,
            COUNT(*) as element_count,
            array_agg(DISTINCT element_type) as element_types,
            MAX(complexity_score) as max_complexity,
            AVG(complexity_score) as avg_complexity
        FROM code_elements
        WHERE (
            search_vector @@ plainto_tsquery('english', $1)
            OR element_name ILIKE '%' || $1 || '%'
            OR signature ILIKE '%' || $1 || '%'
            OR docstring ILIKE '%' || $1 || '%'
            OR (proj_intel_data->>'full_content') ILIKE '%' || $1 || '%'
        )
        """

        params = [content_query]
        param_count = 1

        # Add file extension filter
        if file_extension:
            param_count += 1
            query += f" AND file_path LIKE '%.{file_extension}'"

        # Add modification date filter
        if modified_since:
            param_count += 1
            query += f" AND last_modified >= ${param_count}"
            params.append(modified_since)

        query += f"""
        GROUP BY file_path, language, last_modified
        ORDER BY
            MAX(complexity_score) DESC NULLS LAST,
            COUNT(*) DESC,
            file_path
        LIMIT ${param_count + 1}
        """
        params.append(limit)

        async with db.pg_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            files = []
            for row in rows:
                file_data = {
                    "file_path": row["file_path"],
                    "language": row["language"],
                    "last_modified": row["last_modified"].isoformat()
                    if row["last_modified"]
                    else None,
                    "element_count": row["element_count"],
                    "element_types": row["element_types"] or [],
                    "max_complexity": float(row["max_complexity"])
                    if row["max_complexity"]
                    else None,
                    "avg_complexity": float(row["avg_complexity"])
                    if row["avg_complexity"]
                    else None,
                }
                files.append(file_data)

        # Summary statistics
        total_files = len(files)
        languages = list(set(f["language"] for f in files if f["language"]))
        total_elements = sum(f["element_count"] for f in files)

        return {
            "success": True,
            "content_query": content_query,
            "filters": {
                "file_extension": file_extension,
                "modified_since": modified_since,
            },
            "summary": {
                "total_files": total_files,
                "total_elements": total_elements,
                "languages": languages,
                "limit_applied": total_files == limit,
            },
            "files": files,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "content_query": content_query,
            "files": [],
        }
