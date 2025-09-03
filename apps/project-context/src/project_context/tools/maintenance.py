"""Maintenance Tools for MCP - TODO/FIXME tracking and code maintenance analysis."""

import ast
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..db.connections import get_db


async def get_todos() -> Dict[str, Any]:
    """TODO/FIXME items - Search code_elements content for TODO, FIXME, HACK patterns.

    Searches through all code elements for TODO, FIXME, and HACK comments,
    extracts comment text and location, groups by priority, and provides
    time-series analysis of TODO changes over time.

    Returns:
        Dictionary containing TODO items grouped by type and priority,
        with location information, change tracking, and statistics.
    """

    try:
        db = get_db()

        # Main query with time-series context
        query = """
        SELECT
            ce.file_path,
            ce.element_name,
            ce.element_type,
            ce.line_start,
            ce.line_end,
            ce.last_modified,
            ce.content_hash,
            ce.proj_intel_data->>'content' as content,
            -- Get recent activity for this file
            COALESCE(fa.action_counts, '{}'::jsonb) as action_counts,
            fa.last_activity
        FROM code_elements ce
        LEFT JOIN (
            SELECT
                file_path,
                jsonb_object_agg(action, count) as action_counts,
                MAX(timestamp) as last_activity
            FROM file_activity
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY file_path
        ) fa ON ce.file_path = fa.file_path
        WHERE ce.proj_intel_data->>'content' IS NOT NULL
        ORDER BY ce.file_path, ce.line_start
        """

        elements = await db.fetch_many(query)

        # Get historical TODO tracking from context_items if available
        history_query = """
        SELECT
            ci.source_path,
            ci.timestamp,
            ci.entity_metadata->>'todo_type' as todo_type,
            ci.entity_metadata->>'todo_text' as todo_text,
            ci.entity_metadata->>'action' as action,
            ci.entity_metadata->>'line_number' as line_number
        FROM context_items ci
        WHERE ci.entity_type = 'todo_change'
        AND ci.timestamp >= NOW() - INTERVAL '90 days'
        ORDER BY ci.timestamp DESC
        LIMIT 1000
        """

        try:
            history = await db.fetch_many(history_query)
        except Exception:
            # Table might not have todo_change records yet
            history = []

        result = {
            "todos": [],
            "fixmes": [],
            "hacks": [],
            "grouped_by_priority": {
                "high": [],
                "medium": [],
                "low": [],
                "untagged": [],
            },
            "stats": {
                "total_items": 0,
                "todos_count": 0,
                "fixmes_count": 0,
                "hacks_count": 0,
                "files_with_todos": set(),
                "priority_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "untagged": 0,
                },
                "files_with_recent_activity": 0,
                "avg_age_days": 0,
            },
            "time_series": {
                "recent_changes": [],
                "activity_by_file": {},
                "todo_history": history,
                "change_patterns": {"added": 0, "resolved": 0, "modified": 0},
            },
        }

        # Patterns to match TODO/FIXME/HACK comments with optional priority
        patterns = {
            "todo": re.compile(r"#\s*TODO(\s*\([^)]*\))?\s*:?\s*(.+)", re.IGNORECASE),
            "fixme": re.compile(r"#\s*FIXME(\s*\([^)]*\))?\s*:?\s*(.+)", re.IGNORECASE),
            "hack": re.compile(r"#\s*HACK(\s*\([^)]*\))?\s*:?\s*(.+)", re.IGNORECASE),
        }

        # Priority patterns to extract from parentheses
        priority_pattern = re.compile(
            r"\(([^)]*priority[^)]*|high|medium|low)\)", re.IGNORECASE
        )

        for element in elements:
            if not element["content"]:
                continue

            content = element["content"]
            lines = content.split("\n")

            for line_idx, line in enumerate(lines):
                actual_line_number = (
                    element["line_start"] + line_idx
                    if element["line_start"]
                    else line_idx + 1
                )

                for todo_type, pattern in patterns.items():
                    matches = pattern.finditer(line)

                    for match in matches:
                        priority_match = match.group(1)
                        comment_text = match.group(2).strip()

                        # Extract priority if present
                        priority = "untagged"
                        if priority_match:
                            priority_search = priority_pattern.search(priority_match)
                            if priority_search:
                                priority_text = priority_search.group(1).lower()
                                if "high" in priority_text or "urgent" in priority_text:
                                    priority = "high"
                                elif (
                                    "medium" in priority_text or "med" in priority_text
                                ):
                                    priority = "medium"
                                elif "low" in priority_text:
                                    priority = "low"

                        # Calculate age if last_modified is available
                        age_days = None
                        if element.get("last_modified"):
                            try:
                                from datetime import datetime, timezone

                                last_mod = element["last_modified"]
                                if isinstance(last_mod, str):
                                    last_mod = datetime.fromisoformat(
                                        last_mod.replace("Z", "+00:00")
                                    )
                                elif not last_mod.tzinfo:
                                    last_mod = last_mod.replace(tzinfo=timezone.utc)
                                age_days = (datetime.now(timezone.utc) - last_mod).days
                            except Exception:
                                age_days = None

                        todo_item = {
                            "type": todo_type.upper(),
                            "text": comment_text,
                            "file_path": element["file_path"],
                            "element_name": element["element_name"],
                            "element_type": element["element_type"],
                            "line_number": actual_line_number,
                            "priority": priority,
                            "raw_line": line.strip(),
                            "context": {
                                "element_line_start": element["line_start"],
                                "element_line_end": element["line_end"],
                            },
                            "time_series": {
                                "last_modified": element.get("last_modified"),
                                "age_days": age_days,
                                "content_hash": element.get("content_hash"),
                                "recent_activity": element.get("action_counts", {}),
                                "last_activity": element.get("last_activity"),
                            },
                        }

                        # Add to appropriate lists
                        result[f"{todo_type}s"].append(todo_item)
                        result["grouped_by_priority"][priority].append(todo_item)

                        # Update stats
                        result["stats"][f"{todo_type}s_count"] += 1
                        result["stats"]["priority_distribution"][priority] += 1
                        result["stats"]["files_with_todos"].add(element["file_path"])

        # Convert set to list for JSON serialization and final stats
        result["stats"]["files_with_todos"] = list(result["stats"]["files_with_todos"])
        result["stats"]["total_items"] = (
            result["stats"]["todos_count"]
            + result["stats"]["fixmes_count"]
            + result["stats"]["hacks_count"]
        )
        result["stats"]["unique_files_count"] = len(result["stats"]["files_with_todos"])

        # Calculate time-series statistics
        all_todos = result["todos"] + result["fixmes"] + result["hacks"]

        # Files with recent activity
        files_with_activity = set()
        total_age_days = 0
        valid_ages = 0

        for todo in all_todos:
            ts_data = todo.get("time_series", {})
            if ts_data.get("recent_activity"):
                files_with_activity.add(todo["file_path"])

            if ts_data.get("age_days") is not None:
                total_age_days += ts_data["age_days"]
                valid_ages += 1

        result["stats"]["files_with_recent_activity"] = len(files_with_activity)
        result["stats"]["avg_age_days"] = (
            total_age_days / valid_ages if valid_ages > 0 else 0
        )

        # Process activity by file for time series
        for todo in all_todos:
            file_path = todo["file_path"]
            if file_path not in result["time_series"]["activity_by_file"]:
                result["time_series"]["activity_by_file"][file_path] = {
                    "todo_count": 0,
                    "last_modified": None,
                    "recent_activity": {},
                    "avg_age_days": 0,
                }

            file_data = result["time_series"]["activity_by_file"][file_path]
            file_data["todo_count"] += 1

            ts_data = todo.get("time_series", {})
            if ts_data.get("last_modified"):
                if (
                    not file_data["last_modified"]
                    or ts_data["last_modified"] > file_data["last_modified"]
                ):
                    file_data["last_modified"] = ts_data["last_modified"]

            if ts_data.get("recent_activity"):
                file_data["recent_activity"] = ts_data["recent_activity"]

            if ts_data.get("age_days") is not None:
                file_data["avg_age_days"] = (
                    file_data.get("avg_age_days", 0) + ts_data["age_days"]
                ) / 2

        # Process historical changes
        for change in history:
            action = change.get("action", "").lower()
            if action in ["added", "created"]:
                result["time_series"]["change_patterns"]["added"] += 1
            elif action in ["resolved", "completed", "fixed"]:
                result["time_series"]["change_patterns"]["resolved"] += 1
            elif action in ["modified", "updated"]:
                result["time_series"]["change_patterns"]["modified"] += 1

        # Sort items by priority and then by file path
        priority_order = {"high": 0, "medium": 1, "low": 2, "untagged": 3}

        for todo_list in [result["todos"], result["fixmes"], result["hacks"]]:
            todo_list.sort(
                key=lambda x: (
                    priority_order[x["priority"]],
                    x["file_path"],
                    x["line_number"],
                )
            )

        for priority_list in result["grouped_by_priority"].values():
            priority_list.sort(key=lambda x: (x["file_path"], x["line_number"]))

        return result

    except Exception as e:
        return {
            "error": f"Failed to get TODO items: {str(e)}",
            "todos": [],
            "fixmes": [],
            "hacks": [],
            "grouped_by_priority": {
                "high": [],
                "medium": [],
                "low": [],
                "untagged": [],
            },
            "stats": {
                "total_items": 0,
                "todos_count": 0,
                "fixmes_count": 0,
                "hacks_count": 0,
                "files_with_todos": [],
                "unique_files_count": 0,
                "priority_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "untagged": 0,
                },
                "files_with_recent_activity": 0,
                "avg_age_days": 0,
            },
            "time_series": {
                "recent_changes": [],
                "activity_by_file": {},
                "todo_history": [],
                "change_patterns": {"added": 0, "resolved": 0, "modified": 0},
            },
        }


async def validate_intelligence() -> Dict[str, Any]:
    """Validate data consistency across tables using time-series queries.

    Performs comprehensive data integrity validation including:
    - Cross-reference checks between code_elements and context_items
    - Time-series analysis for data changes and anomalies
    - Orphaned record detection across multiple tables
    - Data freshness validation using timestamp analysis

    Returns:
        Dictionary containing validation results:
        - connection_status: Status of all database connections
        - consistency_checks: Cross-table validation results
        - time_series_analysis: Temporal data patterns and anomalies
        - orphaned_records: Records without valid references
        - data_freshness: Analysis of recent updates and activity
        - health_score: Overall data integrity score (0-100)
        - recommendations: Specific remediation suggestions
    """
    db = get_db()

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connection_status": {},
        "consistency_checks": {},
        "time_series_analysis": {},
        "orphaned_records": {},
        "data_freshness": {},
        "postgresql_stats": {},
        "neo4j_stats": {},
        "redis_stats": {},
        "health_score": 0,
        "recommendations": [],
    }

    # Test PostgreSQL connection and perform comprehensive validation
    try:
        async with db.pg_pool.acquire() as conn:
            # Test basic connectivity
            await conn.fetchval("SELECT 1")
            result["connection_status"]["postgresql"] = "connected"

            # 1. Cross-reference validation between tables
            result["consistency_checks"] = await _validate_cross_references(conn)

            # 2. Time-series analysis for data patterns
            result["time_series_analysis"] = await _analyze_time_series_patterns(conn)

            # 3. Orphaned records detection
            result["orphaned_records"] = await _detect_orphaned_records(conn)

            # 4. Data freshness analysis
            result["data_freshness"] = await _analyze_data_freshness(conn)

            # 5. Basic table statistics
            table_queries = {
                "context_items": "SELECT COUNT(*) FROM context_items",
                "code_elements": "SELECT COUNT(*) FROM code_elements",
                "monitoring_metrics": "SELECT COUNT(*) FROM monitoring_metrics",
            }

            # Check if agent_usage table exists
            agent_table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'agent_usage'
                )
            """
            )

            if agent_table_exists:
                table_queries["agent_usage"] = "SELECT COUNT(*) FROM agent_usage"

            for table_name, query in table_queries.items():
                try:
                    count = await conn.fetchval(query)
                    result["postgresql_stats"][f"{table_name}_count"] = count
                except Exception as e:
                    result["postgresql_stats"][
                        f"{table_name}_count"
                    ] = f"error: {str(e)}"
                    result["recommendations"].append(
                        f"Check {table_name} table integrity"
                    )

            # Get database size and other health metrics
            try:
                db_size = await conn.fetchval(
                    """
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """
                )
                result["postgresql_stats"]["database_size"] = db_size

                # Check for recent activity (last hour)
                recent_context = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM context_items
                    WHERE created_at > NOW() - INTERVAL '1 hour'
                """
                )
                result["postgresql_stats"]["recent_context_items"] = recent_context

            except Exception as e:
                result["postgresql_stats"]["additional_metrics"] = f"error: {str(e)}"

    except Exception as e:
        result["connection_status"]["postgresql"] = f"error: {str(e)}"
        result["recommendations"].append("Check PostgreSQL connection configuration")

    # Test Neo4j connection and get node/relationship counts
    try:
        if db.neo4j_driver:
            async with db.neo4j_driver.session() as session:
                # Test basic connectivity
                await session.run("RETURN 1")
                result["connection_status"]["neo4j"] = "connected"

                # Get node counts by label (using basic queries, not APOC)
                try:
                    # Try to get all labels first
                    labels_result = await session.run(
                        "CALL db.labels() YIELD label RETURN label"
                    )
                    labels = [record["label"] async for record in labels_result]

                    node_counts = {}
                    total_nodes = 0
                    for label in labels:
                        count_result = await session.run(
                            f"MATCH (n:{label}) RETURN count(n) as count"
                        )
                        count = await count_result.single()
                        count_value = count["count"]
                        node_counts[label] = count_value
                        total_nodes += count_value

                    result["neo4j_stats"]["nodes_by_label"] = node_counts
                    result["neo4j_stats"]["total_nodes"] = total_nodes

                except Exception as label_error:
                    # Fallback to simple total count
                    node_result = await session.run(
                        "MATCH (n) RETURN count(n) as count"
                    )
                    node_record = await node_result.single()
                    result["neo4j_stats"]["total_nodes"] = node_record["count"]

                # Get relationship counts by type
                try:
                    types_result = await session.run(
                        "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
                    )
                    rel_types = [
                        record["relationshipType"] async for record in types_result
                    ]

                    rel_counts = {}
                    total_rels = 0
                    for rel_type in rel_types:
                        count_result = await session.run(
                            f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                        )
                        count = await count_result.single()
                        count_value = count["count"]
                        rel_counts[rel_type] = count_value
                        total_rels += count_value

                    result["neo4j_stats"]["relationships_by_type"] = rel_counts
                    result["neo4j_stats"]["total_relationships"] = total_rels

                except Exception as rel_error:
                    # Fallback to simple total count
                    rel_result = await session.run(
                        "MATCH ()-[r]->() RETURN count(r) as count"
                    )
                    rel_record = await rel_result.single()
                    result["neo4j_stats"]["total_relationships"] = rel_record["count"]

        else:
            result["connection_status"]["neo4j"] = "not_configured"
            result["neo4j_stats"] = {"message": "Neo4j not configured or unavailable"}

    except Exception as e:
        result["connection_status"]["neo4j"] = f"error: {str(e)}"
        result["recommendations"].append("Check Neo4j connection configuration")

    # Test Redis connection
    try:
        if db.redis_client:
            await db.redis_client.ping()
            result["connection_status"]["redis"] = "connected"

            # Get basic Redis info
            info = await db.redis_client.info()
            result["redis_stats"] = {
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
        else:
            result["connection_status"]["redis"] = "not_configured"
            result["redis_stats"] = {"message": "Redis not configured or unavailable"}

    except Exception as e:
        result["connection_status"]["redis"] = f"error: {str(e)}"
        result["recommendations"].append("Check Redis connection configuration")

    # Calculate health score
    health_score = 0
    max_score = 100

    # Database connectivity (40 points total)
    if result["connection_status"].get("postgresql") == "connected":
        health_score += 25
    if result["connection_status"].get("neo4j") in ["connected", "not_configured"]:
        health_score += 10  # Lower weight since it's optional
    if result["connection_status"].get("redis") in ["connected", "not_configured"]:
        health_score += 5  # Lower weight since it's optional

    # Data presence (40 points total)
    pg_stats = result["postgresql_stats"]
    if (
        isinstance(pg_stats.get("context_items_count"), int)
        and pg_stats["context_items_count"] > 0
    ):
        health_score += 15
    if (
        isinstance(pg_stats.get("code_elements_count"), int)
        and pg_stats["code_elements_count"] > 0
    ):
        health_score += 15
    if isinstance(pg_stats.get("monitoring_metrics_count"), int):
        health_score += 10

    # Recent activity (20 points)
    if isinstance(pg_stats.get("recent_context_items"), int):
        if pg_stats["recent_context_items"] > 0:
            health_score += 20
        elif pg_stats["recent_context_items"] == 0:
            health_score += 10  # No recent activity but data exists
            result["recommendations"].append(
                "No recent activity detected in the last hour"
            )

    result["health_score"] = min(health_score, max_score)

    # Add recommendations based on health score
    if result["health_score"] < 50:
        result["recommendations"].append(
            "System health is poor - multiple issues detected"
        )
    elif result["health_score"] < 75:
        result["recommendations"].append(
            "System health is fair - some issues need attention"
        )
    elif result["health_score"] < 90:
        result["recommendations"].append("System health is good with minor issues")

    # Add specific recommendations
    if not result["postgresql_stats"]:
        result["recommendations"].append(
            "PostgreSQL connection failed - check database server"
        )

    if len(result["recommendations"]) == 0:
        result["recommendations"].append("System is healthy - no issues detected")

    return result


async def get_security_issues() -> Dict[str, Any]:
    """Security patterns from monitoring_metrics using time-series queries.

    Queries monitoring_metrics table for security-related events and patterns:
    - Failed authentication attempts
    - Suspicious file access patterns
    - Unusual network activity
    - Error patterns that may indicate attacks
    - Performance anomalies that could indicate compromise

    Cross-references with code_elements and context_items for context.

    Returns:
        Dictionary containing security findings with temporal analysis,
        threat severity, and remediation recommendations.
    """

    try:
        db = get_db()

        result = {
            "security_events": [],
            "failed_authentications": [],
            "suspicious_patterns": [],
            "error_anomalies": [],
            "performance_anomalies": [],
            "time_series_analysis": {"last_24h": {}, "last_7d": {}, "trends": {}},
            "summary": {
                "total_security_events": 0,
                "critical_events": 0,
                "high_events": 0,
                "medium_events": 0,
                "low_events": 0,
                "unique_sources": set(),
                "time_range": {},
            },
            "recommendations": [],
        }

        # Query monitoring_metrics for security-related patterns
        # Look for failed authentication patterns
        auth_query = """
        SELECT
            timestamp,
            metric_name,
            metric_value,
            labels,
            source_component,
            tags
        FROM monitoring_metrics
        WHERE (
            lower(metric_name) LIKE '%auth%' OR
            lower(metric_name) LIKE '%login%' OR
            lower(metric_name) LIKE '%fail%' OR
            lower(labels::text) LIKE '%fail%' OR
            lower(tags::text) LIKE '%error%'
        )
        AND timestamp >= NOW() - INTERVAL '7 days'
        ORDER BY timestamp DESC
        LIMIT 1000
        """

        auth_events = await db.fetch_many(auth_query)

        for event in auth_events:
            severity = _classify_security_event_severity(event)

            security_event = {
                "event_type": "authentication",
                "timestamp": event["timestamp"].isoformat()
                if event["timestamp"]
                else None,
                "metric_name": event["metric_name"],
                "metric_value": event["metric_value"],
                "source": event["source_component"],
                "severity": severity,
                "labels": event.get("labels", {}),
                "tags": event.get("tags", {}),
                "description": f"Authentication event: {event['metric_name']}",
            }

            if (
                "fail" in str(event["metric_name"]).lower()
                or "fail" in str(event.get("labels", {})).lower()
            ):
                result["failed_authentications"].append(security_event)

            result["security_events"].append(security_event)
            result["summary"]["unique_sources"].add(
                event["source_component"] or "unknown"
            )

        # Query for error patterns that might indicate attacks
        error_query = """
        WITH error_patterns AS (
            SELECT
                timestamp,
                metric_name,
                metric_value,
                labels,
                source_component,
                tags,
                COUNT(*) OVER (
                    PARTITION BY source_component, metric_name
                    ORDER BY timestamp
                    RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
                ) as error_frequency
            FROM monitoring_metrics
            WHERE (
                lower(metric_name) LIKE '%error%' OR
                lower(metric_name) LIKE '%exception%' OR
                lower(metric_name) LIKE '%fail%' OR
                metric_value::text ~ '^[0-9]+$' AND metric_value::numeric > 100
            )
            AND timestamp >= NOW() - INTERVAL '7 days'
        )
        SELECT * FROM error_patterns
        WHERE error_frequency > 10
        ORDER BY error_frequency DESC, timestamp DESC
        LIMIT 500
        """

        error_events = await db.fetch_many(error_query)

        for event in error_events:
            severity = "high" if event["error_frequency"] > 50 else "medium"

            anomaly = {
                "event_type": "error_anomaly",
                "timestamp": event["timestamp"].isoformat()
                if event["timestamp"]
                else None,
                "metric_name": event["metric_name"],
                "metric_value": event["metric_value"],
                "source": event["source_component"],
                "severity": severity,
                "frequency": event["error_frequency"],
                "description": f"High frequency error pattern detected: {event['error_frequency']} occurrences",
            }

            result["error_anomalies"].append(anomaly)
            result["security_events"].append(anomaly)
            result["summary"]["unique_sources"].add(
                event["source_component"] or "unknown"
            )

        # Query for performance anomalies that could indicate compromise
        performance_query = """
        WITH perf_stats AS (
            SELECT
                timestamp,
                metric_name,
                metric_value,
                source_component,
                AVG(metric_value::numeric) OVER (
                    PARTITION BY metric_name, source_component
                    ORDER BY timestamp
                    ROWS BETWEEN 50 PRECEDING AND 1 PRECEDING
                ) as baseline_avg,
                STDDEV(metric_value::numeric) OVER (
                    PARTITION BY metric_name, source_component
                    ORDER BY timestamp
                    ROWS BETWEEN 50 PRECEDING AND 1 PRECEDING
                ) as baseline_stddev
            FROM monitoring_metrics
            WHERE metric_value::text ~ '^[0-9.]+$'
            AND timestamp >= NOW() - INTERVAL '7 days'
            AND (
                lower(metric_name) LIKE '%cpu%' OR
                lower(metric_name) LIKE '%memory%' OR
                lower(metric_name) LIKE '%disk%' OR
                lower(metric_name) LIKE '%network%' OR
                lower(metric_name) LIKE '%response%' OR
                lower(metric_name) LIKE '%latency%'
            )
        )
        SELECT
            timestamp,
            metric_name,
            metric_value,
            source_component,
            baseline_avg,
            baseline_stddev,
            ABS(metric_value::numeric - baseline_avg) / NULLIF(baseline_stddev, 0) as z_score
        FROM perf_stats
        WHERE baseline_stddev > 0
        AND ABS(metric_value::numeric - baseline_avg) / baseline_stddev > 3
        ORDER BY z_score DESC, timestamp DESC
        LIMIT 200
        """

        perf_events = await db.fetch_many(performance_query)

        for event in perf_events:
            z_score = event.get("z_score", 0)
            severity = (
                "critical" if z_score > 5 else "high" if z_score > 4 else "medium"
            )

            anomaly = {
                "event_type": "performance_anomaly",
                "timestamp": event["timestamp"].isoformat()
                if event["timestamp"]
                else None,
                "metric_name": event["metric_name"],
                "metric_value": event["metric_value"],
                "source": event["source_component"],
                "severity": severity,
                "z_score": float(z_score) if z_score else 0,
                "baseline_avg": float(event["baseline_avg"])
                if event["baseline_avg"]
                else 0,
                "description": f"Performance anomaly detected: {z_score:.2f} standard deviations from baseline",
            }

            result["performance_anomalies"].append(anomaly)
            result["security_events"].append(anomaly)
            result["summary"]["unique_sources"].add(
                event["source_component"] or "unknown"
            )

        # Cross-reference with code_elements for context
        if result["security_events"]:
            context_query = """
            SELECT DISTINCT
                ce.file_path,
                ce.element_name,
                ce.element_type,
                ce.proj_intel_data
            FROM code_elements ce
            WHERE ce.proj_intel_data->>'content' IS NOT NULL
            AND (
                lower(ce.proj_intel_data->>'content') LIKE '%auth%' OR
                lower(ce.proj_intel_data->>'content') LIKE '%security%' OR
                lower(ce.proj_intel_data->>'content') LIKE '%password%' OR
                lower(ce.proj_intel_data->>'content') LIKE '%token%'
            )
            LIMIT 100
            """

            security_related_code = await db.fetch_many(context_query)

            # Add code context to security events
            for event in result["security_events"]:
                event["related_code_elements"] = [
                    {
                        "file_path": elem["file_path"],
                        "element_name": elem["element_name"],
                        "element_type": elem["element_type"],
                    }
                    for elem in security_related_code[:3]  # Limit to first 3 matches
                ]

        # Time series analysis
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        # Count events by time periods
        events_24h = len(
            [
                e
                for e in result["security_events"]
                if e.get("timestamp")
                and datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
                > last_24h
            ]
        )
        events_7d = len(
            [
                e
                for e in result["security_events"]
                if e.get("timestamp")
                and datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
                > last_7d
            ]
        )

        result["time_series_analysis"]["last_24h"] = {
            "total_events": events_24h,
            "critical_events": len(
                [
                    e
                    for e in result["security_events"]
                    if e.get("severity") == "critical"
                    and e.get("timestamp")
                    and datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
                    > last_24h
                ]
            ),
        }

        result["time_series_analysis"]["last_7d"] = {
            "total_events": events_7d,
            "daily_average": events_7d / 7.0 if events_7d > 0 else 0,
        }

        # Calculate summary statistics
        all_events = result["security_events"]
        result["summary"]["total_security_events"] = len(all_events)
        result["summary"]["unique_sources"] = list(result["summary"]["unique_sources"])

        for event in all_events:
            severity = event.get("severity", "low")
            result["summary"][f"{severity}_events"] += 1

        # Set time range
        if all_events:
            timestamps = [e.get("timestamp") for e in all_events if e.get("timestamp")]
            if timestamps:
                result["summary"]["time_range"] = {
                    "earliest": min(timestamps),
                    "latest": max(timestamps),
                }

        # Generate security recommendations
        result["recommendations"] = _generate_monitoring_security_recommendations(
            result
        )

        return result

    except Exception as e:
        return {
            "error": f"Failed to analyze security issues from monitoring metrics: {str(e)}",
            "security_events": [],
            "failed_authentications": [],
            "suspicious_patterns": [],
            "error_anomalies": [],
            "performance_anomalies": [],
            "time_series_analysis": {"last_24h": {}, "last_7d": {}, "trends": {}},
            "summary": {"total_security_events": 0, "unique_sources": []},
            "recommendations": [],
        }


def _classify_security_event_severity(event: Dict[str, Any]) -> str:
    """Classify security event severity based on metric patterns."""
    metric_name = str(event.get("metric_name", "")).lower()
    metric_value = event.get("metric_value", "")
    labels = str(event.get("labels", {})).lower()
    tags = str(event.get("tags", {})).lower()

    # Critical patterns
    if any(
        pattern in metric_name
        for pattern in ["critical", "breach", "compromise", "attack"]
    ):
        return "critical"

    if any(pattern in labels for pattern in ["critical", "breach", "compromise"]):
        return "critical"

    # High severity patterns
    if any(
        pattern in metric_name
        for pattern in ["auth_fail", "login_fail", "unauthorized"]
    ):
        return "high"

    if any(pattern in metric_name for pattern in ["error", "exception", "fail"]) and (
        isinstance(metric_value, (int, float)) and metric_value > 50
    ):
        return "high"

    # Medium severity patterns
    if any(pattern in metric_name for pattern in ["warning", "suspicious", "anomaly"]):
        return "medium"

    if "fail" in metric_name or "error" in labels:
        return "medium"

    # Default to low
    return "low"


def _generate_monitoring_security_recommendations(
    analysis_result: Dict[str, Any]
) -> List[str]:
    """Generate security recommendations based on monitoring metrics analysis."""
    recommendations = []

    if analysis_result["failed_authentications"]:
        recommendations.extend(
            [
                "Investigate failed authentication patterns and implement account lockout policies",
                "Review authentication logs for brute force attack indicators",
                "Consider implementing multi-factor authentication (MFA)",
                "Set up alerts for authentication failure rate thresholds",
                "Review and strengthen password policies",
            ]
        )

    if analysis_result["error_anomalies"]:
        recommendations.extend(
            [
                "Investigate high-frequency error patterns for potential attack indicators",
                "Review application logs for error patterns that may indicate exploitation attempts",
                "Implement proper error handling to avoid information disclosure",
                "Set up monitoring dashboards for error rate anomalies",
                "Consider implementing rate limiting for error-prone endpoints",
            ]
        )

    if analysis_result["performance_anomalies"]:
        recommendations.extend(
            [
                "Investigate performance anomalies for signs of resource exhaustion attacks",
                "Monitor for unusual CPU, memory, or network usage patterns",
                "Review system capacity and scaling policies",
                "Implement performance baselines and alerting thresholds",
                "Consider DDoS protection for network-related anomalies",
            ]
        )

    # Time-based recommendations
    time_analysis = analysis_result.get("time_series_analysis", {})
    if time_analysis.get("last_24h", {}).get("critical_events", 0) > 0:
        recommendations.append(
            "Recent critical security events detected - immediate investigation recommended"
        )

    if time_analysis.get("last_7d", {}).get("daily_average", 0) > 10:
        recommendations.append(
            "High daily average of security events - review security posture and monitoring rules"
        )

    # General recommendations
    if analysis_result["summary"]["total_security_events"] > 0:
        recommendations.extend(
            [
                "Establish security incident response procedures",
                "Implement centralized logging and SIEM solution",
                "Regular security monitoring and threat hunting",
                "Review and update security monitoring rules and thresholds",
                "Consider implementing automated incident response workflows",
            ]
        )

    # Source-based recommendations
    unique_sources = analysis_result["summary"].get("unique_sources", [])
    if len(unique_sources) > 5:
        recommendations.append(
            "Multiple security event sources detected - review cross-component security coordination"
        )

    return list(set(recommendations))  # Remove duplicates


def _should_skip_file(file_path: Path) -> bool:
    """Check if a file should be skipped during security scanning."""
    skip_patterns = [
        "__pycache__",
        ".git",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".tox",
        "build",
        "dist",
        ".coverage",
        ".nyc_output",
        "coverage",
        ".DS_Store",
        ".idea",
        ".vscode",
    ]

    # Check if any part of the path contains skip patterns
    for part in file_path.parts:
        if any(skip in part for skip in skip_patterns):
            return True

    # Skip very large files (> 10MB)
    try:
        if file_path.stat().st_size > 10 * 1024 * 1024:
            return True
    except:
        pass

    return False


def _find_hardcoded_secrets(
    content: str, file_path: str, file_ext: str
) -> List[Dict[str, Any]]:
    """Find hardcoded secrets in file content."""
    secrets = []

    # Common secret patterns
    secret_patterns = [
        # API Keys
        (
            r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            "api_key",
            "high",
        ),
        (
            r'(?i)(access[_-]?key|accesskey)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            "access_key",
            "high",
        ),
        (
            r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            "secret_key",
            "critical",
        ),
        # AWS Keys
        (r"(AKIA[0-9A-Z]{16})", "aws_access_key", "critical"),
        (
            r'(?i)aws.{0,20}(secret|access).{0,20}[:=]\s*["\']([a-zA-Z0-9+/]{40})["\']',
            "aws_secret",
            "critical",
        ),
        # GitHub tokens
        (r"(gh[ps]_[a-zA-Z0-9]{36})", "github_token", "high"),
        (
            r'(?i)github.{0,20}token.{0,20}[:=]\s*["\']([a-zA-Z0-9_]{40})["\']',
            "github_token",
            "high",
        ),
        # Database passwords
        (
            r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']([^"\'\s]{8,})["\']',
            "password",
            "medium",
        ),
        (
            r'(?i)(db[_-]?password|database[_-]?password)\s*[:=]\s*["\']([^"\'\s]{1,})["\']',
            "db_password",
            "high",
        ),
        # JWT tokens
        (
            r"(eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+)",
            "jwt_token",
            "medium",
        ),
        # Generic tokens
        (
            r'(?i)(token|bearer)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            "token",
            "medium",
        ),
        # SSH keys
        (
            r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
            "ssh_private_key",
            "critical",
        ),
        # Slack tokens
        (r"(xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24})", "slack_token", "high"),
        # Generic secrets (longer base64-like strings)
        (
            r'(?i)(secret|key|token|password)\s*[:=]\s*["\']([a-zA-Z0-9+/]{32,}={0,2})["\']',
            "generic_secret",
            "medium",
        ),
    ]

    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for pattern, secret_type, severity in secret_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                # Skip obvious test/example values
                if _is_test_or_example_value(match.group(0)):
                    continue

                secrets.append(
                    {
                        "type": secret_type,
                        "severity": severity,
                        "file": file_path,
                        "line": line_num,
                        "content": line.strip()[:100] + "..."
                        if len(line.strip()) > 100
                        else line.strip(),
                        "description": f"Potential {secret_type.replace('_', ' ')} found in code",
                        "recommendation": "Move secrets to environment variables or secure secret management",
                    }
                )

    return secrets


def _find_unsafe_functions(
    content: str, file_path: str, file_ext: str
) -> List[Dict[str, Any]]:
    """Find unsafe function usage in file content."""
    unsafe_functions = []

    # Python-specific unsafe patterns
    if file_ext == ".py":
        # Try AST parsing for more accurate detection
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = _get_function_name(node.func)
                    if func_name in ["eval", "exec", "compile"]:
                        unsafe_functions.append(
                            {
                                "type": "dangerous_builtin",
                                "severity": "critical",
                                "file": file_path,
                                "line": node.lineno,
                                "function": func_name,
                                "description": f"Use of dangerous builtin function '{func_name}'",
                                "recommendation": "Avoid dynamic code execution. Use safer alternatives.",
                            }
                        )
                    elif (
                        func_name == "subprocess.call" or func_name == "subprocess.run"
                    ):
                        # Check for shell=True in keyword arguments
                        for keyword in node.keywords:
                            if (
                                keyword.arg == "shell"
                                and isinstance(keyword.value, ast.Constant)
                                and keyword.value.value is True
                            ):
                                unsafe_functions.append(
                                    {
                                        "type": "shell_injection",
                                        "severity": "high",
                                        "file": file_path,
                                        "line": node.lineno,
                                        "function": func_name,
                                        "description": f"subprocess call with shell=True is vulnerable to command injection",
                                        "recommendation": "Use shell=False and pass command as list, or validate input thoroughly",
                                    }
                                )
        except SyntaxError:
            # Fall back to regex patterns if AST parsing fails
            pass

    # General unsafe patterns (regex-based for all file types)
    unsafe_patterns = [
        # Python
        (r"\beval\s*\(", "eval", "critical", "Dynamic code execution"),
        (r"\bexec\s*\(", "exec", "critical", "Dynamic code execution"),
        (
            r"subprocess\.(call|run|Popen).*shell\s*=\s*True",
            "subprocess_shell",
            "high",
            "Command injection risk",
        ),
        (r"os\.system\s*\(", "os_system", "high", "Command injection risk"),
        (r"os\.popen\s*\(", "os_popen", "high", "Command injection risk"),
        # JavaScript
        (r"\beval\s*\(", "eval_js", "critical", "Dynamic code execution"),
        (
            r"new\s+Function\s*\(",
            "function_constructor",
            "high",
            "Dynamic code execution",
        ),
        (
            r'setTimeout\s*\(\s*["\'].*["\']',
            "settimeout_string",
            "medium",
            "Code injection risk",
        ),
        (
            r'setInterval\s*\(\s*["\'].*["\']',
            "setinterval_string",
            "medium",
            "Code injection risk",
        ),
        # Generic deserialization
        (r"pickle\.loads?\s*\(", "pickle", "high", "Insecure deserialization"),
        (
            r"yaml\.load\s*\((?!.*Loader=)",
            "yaml_load",
            "medium",
            "Insecure YAML loading",
        ),
        (
            r"json\.loads?\s*\(.*shell",
            "json_shell",
            "medium",
            "Potential code injection",
        ),
    ]

    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for pattern, func_type, severity, description in unsafe_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                unsafe_functions.append(
                    {
                        "type": func_type,
                        "severity": severity,
                        "file": file_path,
                        "line": line_num,
                        "content": line.strip()[:100] + "..."
                        if len(line.strip()) > 100
                        else line.strip(),
                        "description": description,
                        "recommendation": "Use safer alternatives or implement proper input validation",
                    }
                )

    return unsafe_functions


def _find_sql_injection_risks(
    content: str, file_path: str, file_ext: str
) -> List[Dict[str, Any]]:
    """Find SQL injection risks in file content."""
    sql_risks = []

    # SQL injection patterns
    sql_patterns = [
        # String concatenation in SQL
        (
            r'["\']SELECT.*["\'].*([\+%]|\.format\(|f["\'])',
            "string_concat_select",
            "high",
        ),
        (
            r'["\']INSERT.*["\'].*([\+%]|\.format\(|f["\'])',
            "string_concat_insert",
            "high",
        ),
        (
            r'["\']UPDATE.*["\'].*([\+%]|\.format\(|f["\'])',
            "string_concat_update",
            "high",
        ),
        (
            r'["\']DELETE.*["\'].*([\+%]|\.format\(|f["\'])',
            "string_concat_delete",
            "critical",
        ),
        # % string formatting in SQL
        (
            r'["\'].*(SELECT|INSERT|UPDATE|DELETE).*["\'].*%.*\(',
            "percent_formatting",
            "high",
        ),
        # .format() in SQL
        (
            r'["\'].*(SELECT|INSERT|UPDATE|DELETE).*["\'].*\.format\s*\(',
            "format_method",
            "high",
        ),
        # f-strings in SQL (Python)
        (
            r'f["\'].*(SELECT|INSERT|UPDATE|DELETE).*\{.*\}.*["\']',
            "f_string_sql",
            "high",
        ),
        # execute() with string concat
        (
            r'\.execute\s*\(\s*["\'].*(SELECT|INSERT|UPDATE|DELETE).*["\'].*[\+%]',
            "execute_concat",
            "critical",
        ),
        # Raw SQL in ORM
        (
            r'\.raw\s*\(\s*["\'].*(SELECT|INSERT|UPDATE|DELETE).*["\'].*[\+%]',
            "orm_raw_concat",
            "high",
        ),
        # Cursor execute with formatting
        (r'cursor\.execute\s*\(\s*["\'].*\{.*\}.*["\']', "cursor_format", "high"),
    ]

    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for pattern, risk_type, severity in sql_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Skip if it looks like it's using parameterized queries
                if re.search(r"(%s|\?|\$\d+)", line) and not re.search(
                    r'[\+%].*["\']', line
                ):
                    continue

                sql_risks.append(
                    {
                        "type": risk_type,
                        "severity": severity,
                        "file": file_path,
                        "line": line_num,
                        "content": line.strip()[:100] + "..."
                        if len(line.strip()) > 100
                        else line.strip(),
                        "description": "Potential SQL injection vulnerability from string concatenation",
                        "recommendation": "Use parameterized queries or prepared statements instead",
                    }
                )

    return sql_risks


def _get_function_name(node) -> str:
    """Extract function name from AST node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_function_name(node.value)}.{node.attr}"
    else:
        return "unknown"


def _is_test_or_example_value(value: str) -> bool:
    """Check if a detected secret is likely a test/example value."""
    test_indicators = [
        "test",
        "example",
        "sample",
        "demo",
        "fake",
        "mock",
        "placeholder",
        "xxx",
        "yyy",
        "123",
        "abc",
        "your",
        "my",
        "dummy",
        "null",
        "none",
    ]

    value_lower = value.lower()
    return any(indicator in value_lower for indicator in test_indicators)


def _generate_security_recommendations(analysis_result: Dict[str, Any]) -> List[str]:
    """Generate security recommendations based on analysis results."""
    recommendations = []

    if analysis_result["hardcoded_secrets"]:
        recommendations.extend(
            [
                "Move hardcoded secrets to environment variables or secure secret management systems",
                "Use tools like python-dotenv for loading environment variables",
                "Consider using HashiCorp Vault or AWS Secrets Manager for production",
                "Add .env files to .gitignore to prevent accidental commits",
                "Implement secret scanning in CI/CD pipelines",
            ]
        )

    if analysis_result["unsafe_functions"]:
        recommendations.extend(
            [
                "Avoid using eval() and exec() functions - use safer alternatives",
                "When using subprocess, set shell=False and validate inputs",
                "Use ast.literal_eval() instead of eval() for safe evaluation",
                "Implement input validation and sanitization",
                "Consider using sandboxed execution environments",
            ]
        )

    if analysis_result["sql_injection_risks"]:
        recommendations.extend(
            [
                "Use parameterized queries or prepared statements",
                "Implement an ORM (SQLAlchemy, Django ORM) with built-in protection",
                "Validate and sanitize all user inputs before database operations",
                "Use whitelist validation for dynamic column/table names",
                "Enable SQL query logging to monitor for suspicious activity",
            ]
        )

    # General recommendations
    if analysis_result["summary"]["total_issues"] > 0:
        recommendations.extend(
            [
                "Implement automated security scanning in your CI/CD pipeline",
                "Regular security code reviews and penetration testing",
                "Follow OWASP Top 10 security guidelines",
                "Keep dependencies up to date and scan for vulnerabilities",
                "Implement proper logging and monitoring for security events",
            ]
        )

    return list(set(recommendations))  # Remove duplicates


# Helper functions for validate_intelligence()
async def _validate_cross_references(conn) -> Dict[str, Any]:
    """Validate cross-references between tables."""
    checks = {}

    try:
        # Check code_elements references
        orphaned_elements = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM code_elements ce
            LEFT JOIN context_items ci ON ci.source_path = ce.file_path
            WHERE ci.source_path IS NULL
        """
        )
        checks["orphaned_code_elements"] = orphaned_elements

        # Check context_items with missing file references
        invalid_context = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM context_items ci
            WHERE ci.source_type = 'file'
            AND ci.source_path IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM code_elements ce
                WHERE ce.file_path = ci.source_path
            )
        """
        )
        checks["invalid_context_references"] = invalid_context

    except Exception as e:
        checks["error"] = str(e)

    return checks


async def _analyze_time_series_patterns(conn) -> Dict[str, Any]:
    """Analyze time-series patterns and detect anomalies."""
    analysis = {}

    try:
        # Activity patterns over time
        daily_activity = await conn.fetch(
            """
            SELECT
                DATE_TRUNC('day', timestamp) as day,
                COUNT(*) as activity_count,
                COUNT(DISTINCT source_path) as unique_files
            FROM context_items
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY day DESC
            LIMIT 30
        """
        )

        analysis["daily_activity"] = [
            {
                "date": row["day"].isoformat() if row["day"] else None,
                "activity_count": row["activity_count"],
                "unique_files": row["unique_files"],
            }
            for row in daily_activity
        ]

        # Code elements modification trends
        mod_trends = await conn.fetch(
            """
            SELECT
                DATE_TRUNC('week', last_modified) as week,
                COUNT(*) as modifications,
                COUNT(DISTINCT file_path) as unique_files
            FROM code_elements
            WHERE last_modified >= NOW() - INTERVAL '8 weeks'
            AND last_modified IS NOT NULL
            GROUP BY DATE_TRUNC('week', last_modified)
            ORDER BY week DESC
        """
        )

        analysis["modification_trends"] = [
            {
                "week": row["week"].isoformat() if row["week"] else None,
                "modifications": row["modifications"],
                "unique_files": row["unique_files"],
            }
            for row in mod_trends
        ]

    except Exception as e:
        analysis["error"] = str(e)

    return analysis


async def _detect_orphaned_records(conn) -> Dict[str, Any]:
    """Detect orphaned records across tables."""
    orphans = {}

    try:
        # Context items without corresponding files
        orphaned_context = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM context_items ci
            WHERE ci.entity_type = 'file'
            AND ci.source_path IS NOT NULL
            AND ci.source_path != ''
            AND NOT EXISTS (
                SELECT 1 FROM code_elements ce
                WHERE ce.file_path = ci.source_path
            )
        """
        )
        orphans["context_without_files"] = orphaned_context

        # File activity without code elements
        orphaned_activity = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM file_activity fa
            WHERE NOT EXISTS (
                SELECT 1 FROM code_elements ce
                WHERE ce.file_path = fa.file_path
            )
        """
        )
        orphans["activity_without_elements"] = orphaned_activity

        # Code elements with null or invalid paths
        invalid_elements = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM code_elements
            WHERE file_path IS NULL
            OR file_path = ''
            OR file_path NOT LIKE '%/%'
        """
        )
        orphans["invalid_element_paths"] = invalid_elements

    except Exception as e:
        orphans["error"] = str(e)

    return orphans


async def _analyze_data_freshness(conn) -> Dict[str, Any]:
    """Analyze data freshness and recency."""
    freshness = {}

    try:
        # Most recent context items
        latest_context = await conn.fetchval(
            """
            SELECT MAX(timestamp)
            FROM context_items
        """
        )

        # Most recent code element modification
        latest_modification = await conn.fetchval(
            """
            SELECT MAX(last_modified)
            FROM code_elements
            WHERE last_modified IS NOT NULL
        """
        )

        # Count of stale data (older than 7 days)
        stale_context = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM context_items
            WHERE timestamp < NOW() - INTERVAL '7 days'
        """
        )

        stale_elements = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM code_elements
            WHERE last_modified < NOW() - INTERVAL '7 days'
            OR last_modified IS NULL
        """
        )

        freshness.update(
            {
                "latest_context_timestamp": latest_context.isoformat()
                if latest_context
                else None,
                "latest_modification_timestamp": latest_modification.isoformat()
                if latest_modification
                else None,
                "stale_context_items": stale_context,
                "stale_code_elements": stale_elements,
            }
        )

        # Data age distribution
        age_distribution = await conn.fetch(
            """
            SELECT
                CASE
                    WHEN timestamp > NOW() - INTERVAL '1 hour' THEN 'last_hour'
                    WHEN timestamp > NOW() - INTERVAL '1 day' THEN 'last_day'
                    WHEN timestamp > NOW() - INTERVAL '1 week' THEN 'last_week'
                    WHEN timestamp > NOW() - INTERVAL '1 month' THEN 'last_month'
                    ELSE 'older'
                END as age_bucket,
                COUNT(*) as count
            FROM context_items
            GROUP BY age_bucket
        """
        )

        freshness["age_distribution"] = {
            row["age_bucket"]: row["count"] for row in age_distribution
        }

    except Exception as e:
        freshness["error"] = str(e)

    return freshness


async def search_code(
    query: str,
    file_pattern: Optional[str] = None,
    element_type: Optional[str] = None,
    language: Optional[str] = None,
    time_range_hours: Optional[int] = None,
    include_content: bool = False,
    max_results: int = 100,
) -> Dict[str, Any]:
    """Code search across code_elements with time-series and cross-reference capabilities.

    Performs comprehensive code search across the code_elements table with support for:
    - Full-text search across element names, signatures, docstrings, and content
    - File path pattern matching
    - Element type filtering (function, class, file, import, etc.)
    - Language-specific filtering
    - Time-based queries for recent changes
    - Cross-referencing with chat sessions, symbol references, and context data

    Args:
        query: Search term to find in code elements
        file_pattern: Optional file path pattern (SQL LIKE syntax with % wildcards)
        element_type: Filter by element type (function, class, file, import)
        language: Filter by programming language
        time_range_hours: Only include elements modified in last N hours
        include_content: Include full content/code in results (default False for performance)
        max_results: Maximum number of results to return (default 100)

    Returns:
        Dictionary containing:
        - matches: List of matching code elements with metadata
        - cross_references: Related chat sessions, symbol references, context
        - time_series_data: Recent activity data if time_range specified
        - statistics: Search result statistics and performance metrics
        - suggestions: Query refinement suggestions based on results
    """

    try:
        db = await get_db()

        result = {
            "query": query,
            "filters": {
                "file_pattern": file_pattern,
                "element_type": element_type,
                "language": language,
                "time_range_hours": time_range_hours,
                "include_content": include_content,
                "max_results": max_results,
            },
            "matches": [],
            "cross_references": {
                "chat_sessions": [],
                "symbol_references": [],
                "context_items": [],
                "recent_activity": [],
            },
            "time_series_data": {},
            "statistics": {
                "total_matches": 0,
                "matches_by_type": {},
                "matches_by_language": {},
                "matches_by_file": {},
                "search_time_ms": 0,
                "files_scanned": 0,
            },
            "suggestions": [],
        }

        start_time = datetime.now()

        # Build the main query with dynamic WHERE conditions
        where_conditions = []
        query_params = []
        param_count = 0

        # Full-text search across multiple fields
        if query.strip():
            param_count += 1
            # Use PostgreSQL full-text search with plainto_tsquery
            where_conditions.append(
                f"""
                (search_vector @@ plainto_tsquery(${param_count})
                 OR element_name ILIKE ${param_count + 1}
                 OR signature ILIKE ${param_count + 2}
                 OR docstring ILIKE ${param_count + 3}
                 OR proj_intel_data->>'content' ILIKE ${param_count + 4})
            """
            )
            search_term = query.strip()
            like_pattern = f"%{search_term}%"
            query_params.extend(
                [search_term, like_pattern, like_pattern, like_pattern, like_pattern]
            )
            param_count += 4

        # File pattern matching
        if file_pattern:
            param_count += 1
            where_conditions.append(f"file_path LIKE ${param_count}")
            query_params.append(file_pattern)

        # Element type filtering
        if element_type:
            param_count += 1
            where_conditions.append(f"element_type = ${param_count}")
            query_params.append(element_type)

        # Language filtering
        if language:
            param_count += 1
            where_conditions.append(f"language = ${param_count}")
            query_params.append(language)

        # Time range filtering
        if time_range_hours:
            param_count += 1
            where_conditions.append(
                f"last_modified >= NOW() - INTERVAL '${param_count} hours'"
            )
            query_params.append(str(time_range_hours))

        # Construct the main search query
        base_fields = """
            id,
            file_path,
            element_type,
            element_name,
            signature,
            docstring,
            line_start,
            line_end,
            complexity_score,
            test_coverage,
            dependencies,
            language,
            last_modified,
            content_hash,
            neo4j_node_id
        """

        if include_content:
            base_fields += ", proj_intel_data->>'content' as content"

        main_query = f"""
        SELECT {base_fields}
        FROM code_elements
        WHERE {' AND '.join(where_conditions) if where_conditions else '1=1'}
        ORDER BY
            CASE WHEN element_name ILIKE ${len(query_params) + 1} THEN 1 ELSE 2 END,
            last_modified DESC NULLS LAST,
            file_path,
            line_start
        LIMIT ${len(query_params) + 2}
        """

        # Add params for ordering and limit
        if query.strip():
            query_params.append(
                f"%{query.strip()}%"
            )  # For exact name matching priority
        else:
            query_params.append("%")  # Match all for ordering
        query_params.append(max_results)

        # Execute main search
        matches = await db.fetch_many(main_query, *query_params)
        result["matches"] = []

        # Process matches and gather IDs for cross-referencing
        element_ids = []
        file_paths = set()
        element_names = set()

        for match in matches:
            match_dict = dict(match)

            # Convert timestamps to ISO format
            if match_dict.get("last_modified"):
                match_dict["last_modified"] = match_dict["last_modified"].isoformat()

            # Parse JSON fields safely
            try:
                if match_dict.get("dependencies"):
                    match_dict["dependencies"] = match_dict["dependencies"]
                else:
                    match_dict["dependencies"] = []
            except (TypeError, ValueError):
                match_dict["dependencies"] = []

            result["matches"].append(match_dict)

            # Collect for cross-referencing
            if match_dict.get("id"):
                element_ids.append(str(match_dict["id"]))
            if match_dict.get("file_path"):
                file_paths.add(match_dict["file_path"])
            if match_dict.get("element_name"):
                element_names.add(match_dict["element_name"])

        result["statistics"]["total_matches"] = len(result["matches"])
        result["statistics"]["files_scanned"] = len(file_paths)

        # Generate statistics
        for match in result["matches"]:
            element_type = match.get("element_type", "unknown")
            language = match.get("language", "unknown")
            file_path = match.get("file_path", "unknown")

            result["statistics"]["matches_by_type"][element_type] = (
                result["statistics"]["matches_by_type"].get(element_type, 0) + 1
            )
            result["statistics"]["matches_by_language"][language] = (
                result["statistics"]["matches_by_language"].get(language, 0) + 1
            )
            result["statistics"]["matches_by_file"][file_path] = (
                result["statistics"]["matches_by_file"].get(file_path, 0) + 1
            )

        # Cross-reference with other tables if we have matches
        if element_ids or file_paths or element_names:
            # Find related chat sessions through code_context table
            if file_paths:
                file_paths_list = list(file_paths)
                context_query = """
                SELECT DISTINCT
                    cc.session_id,
                    cc.timestamp,
                    cc.file_path,
                    cc.symbols,
                    cc.change_type,
                    cc.relevance_score,
                    cs.started_at,
                    cs.ended_at,
                    cs.total_tokens,
                    cs.model_used
                FROM code_context cc
                LEFT JOIN chat_sessions cs ON cc.chat_session_id = cs.id
                WHERE cc.file_path = ANY($1)
                ORDER BY cc.timestamp DESC
                LIMIT 20
                """

                try:
                    context_matches = await db.fetch_many(
                        context_query, file_paths_list
                    )
                    for ctx in context_matches:
                        ctx_dict = dict(ctx)
                        if ctx_dict.get("timestamp"):
                            ctx_dict["timestamp"] = ctx_dict["timestamp"].isoformat()
                        if ctx_dict.get("started_at"):
                            ctx_dict["started_at"] = ctx_dict["started_at"].isoformat()
                        if ctx_dict.get("ended_at"):
                            ctx_dict["ended_at"] = ctx_dict["ended_at"].isoformat()
                        result["cross_references"]["chat_sessions"].append(ctx_dict)
                except Exception:
                    # Table may not exist
                    pass

            # Find symbol references
            if element_names:
                element_names_list = list(element_names)
                symbol_query = """
                SELECT
                    session_id,
                    symbol_name,
                    symbol_type,
                    file_path,
                    line_number,
                    reference_type,
                    timestamp
                FROM symbol_references
                WHERE symbol_name = ANY($1)
                ORDER BY timestamp DESC
                LIMIT 50
                """

                try:
                    symbol_matches = await db.fetch_many(
                        symbol_query, element_names_list
                    )
                    for sym in symbol_matches:
                        sym_dict = dict(sym)
                        if sym_dict.get("timestamp"):
                            sym_dict["timestamp"] = sym_dict["timestamp"].isoformat()
                        result["cross_references"]["symbol_references"].append(sym_dict)
                except Exception:
                    # Table may not exist
                    pass

            # Find related context items (from unified context system)
            if file_paths:
                file_paths_list = list(file_paths)
                context_items_query = """
                SELECT
                    source_type,
                    entity_type,
                    timestamp,
                    title,
                    file_path,
                    line_start,
                    line_end,
                    actor_type,
                    session_id,
                    severity,
                    tags
                FROM context_items
                WHERE file_path = ANY($1)
                  AND timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY timestamp DESC
                LIMIT 30
                """

                try:
                    context_items = await db.fetch_many(
                        context_items_query, file_paths_list
                    )
                    for item in context_items:
                        item_dict = dict(item)
                        if item_dict.get("timestamp"):
                            item_dict["timestamp"] = item_dict["timestamp"].isoformat()
                        result["cross_references"]["context_items"].append(item_dict)
                except Exception:
                    # Table may not exist
                    pass

            # Get recent file activity if time range specified
            if time_range_hours and file_paths:
                file_paths_list = list(file_paths)
                activity_query = (
                    """
                SELECT
                    file_path,
                    action,
                    tool_used,
                    timestamp,
                    session_id,
                    functions_affected,
                    classes_affected
                FROM file_activity
                WHERE file_path = ANY($1)
                  AND timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
                LIMIT 20
                """
                    % time_range_hours
                )

                try:
                    activity_matches = await db.fetch_many(
                        activity_query, file_paths_list
                    )
                    for activity in activity_matches:
                        activity_dict = dict(activity)
                        if activity_dict.get("timestamp"):
                            activity_dict["timestamp"] = activity_dict[
                                "timestamp"
                            ].isoformat()
                        result["cross_references"]["recent_activity"].append(
                            activity_dict
                        )
                except Exception:
                    # Table may not exist
                    pass

        # Generate time series data if time range specified
        if time_range_hours and file_paths:
            file_paths_list = list(file_paths)
            time_series_query = f"""
            SELECT
                time_bucket('1 hour', timestamp) AS hour,
                COUNT(*) as activity_count,
                COUNT(DISTINCT session_id) as unique_sessions,
                array_agg(DISTINCT entity_type) as activity_types
            FROM context_items
            WHERE file_path = ANY($1)
              AND timestamp >= NOW() - INTERVAL '{time_range_hours} hours'
            GROUP BY hour
            ORDER BY hour
            """

            try:
                time_series = await db.fetch_many(time_series_query, file_paths_list)
                result["time_series_data"]["hourly_activity"] = []

                for ts in time_series:
                    ts_dict = dict(ts)
                    if ts_dict.get("hour"):
                        ts_dict["hour"] = ts_dict["hour"].isoformat()
                    result["time_series_data"]["hourly_activity"].append(ts_dict)
            except Exception:
                # TimescaleDB functions may not be available
                pass

        # Calculate search performance
        end_time = datetime.now()
        result["statistics"]["search_time_ms"] = int(
            (end_time - start_time).total_seconds() * 1000
        )

        # Generate search suggestions based on results
        suggestions = []

        if result["statistics"]["total_matches"] == 0:
            suggestions.extend(
                [
                    "Try broadening your search terms",
                    "Remove file pattern or element type filters",
                    "Check spelling of search terms",
                    "Try searching for partial matches with wildcards",
                ]
            )
        elif result["statistics"]["total_matches"] == max_results:
            suggestions.append(
                "Results were limited - try adding more specific filters"
            )

        if result["statistics"]["matches_by_language"]:
            top_language = max(
                result["statistics"]["matches_by_language"].items(), key=lambda x: x[1]
            )[0]
            if not language:
                suggestions.append(
                    f"Most matches in {top_language} - try filtering by language"
                )

        if len(result["statistics"]["matches_by_file"]) > 20:
            suggestions.append("Many files matched - try adding file pattern filter")

        if time_range_hours and not result["cross_references"]["recent_activity"]:
            suggestions.append("No recent activity found - try increasing time range")

        result["suggestions"] = suggestions

        return result

    except Exception as e:
        return {
            "error": f"Failed to search code: {str(e)}",
            "query": query,
            "filters": {
                "file_pattern": file_pattern,
                "element_type": element_type,
                "language": language,
                "time_range_hours": time_range_hours,
                "include_content": include_content,
                "max_results": max_results,
            },
            "matches": [],
            "cross_references": {
                "chat_sessions": [],
                "symbol_references": [],
                "context_items": [],
                "recent_activity": [],
            },
            "time_series_data": {},
            "statistics": {"total_matches": 0, "search_time_ms": 0},
            "suggestions": ["Check database connection and try again"],
        }
