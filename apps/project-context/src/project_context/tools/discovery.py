"""Discovery tools for project context analysis."""

import asyncio
import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.cache import cache_tool_result
from ..db.connections import get_db


@cache_tool_result(ttl=60, cache_type="file_data", key_prefix="file_info_")
async def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific file.

    Args:
        file_path: Path to the file to analyze

    Returns:
        Dictionary containing file information including:
        - Basic file metadata (size, modified time, etc.)
        - Code elements found in the file
        - Complexity metrics
        - File relationships from Neo4j (if available)
    """
    try:
        # Normalize the file path
        normalized_path = os.path.abspath(file_path)

        # Basic file system info
        file_info = await _get_file_system_info(normalized_path)

        # Get database connections
        db = await get_db()

        # Get code elements for this file
        code_elements = await _get_code_elements(db, normalized_path)

        # Get context items related to this file using enhanced unified context
        context_data = await db.get_file_context(normalized_path)

        # Get monitoring metrics for this file
        monitoring_data = await _get_monitoring_metrics(db, normalized_path)

        # Get file relationships from Neo4j (if available)
        relationships = await _get_file_relationships(db, normalized_path)

        # Calculate aggregated complexity metrics
        complexity_summary = _calculate_complexity_summary(code_elements)

        result = {
            "file_path": normalized_path,
            "file_system": file_info,
            "code_elements": {
                "total_count": len(code_elements),
                "elements": code_elements,
                "by_type": _group_elements_by_type(code_elements),
                "complexity": complexity_summary,
            },
            "context_items": context_data,
            "monitoring": monitoring_data,
            "relationships": relationships,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

        return result

    except Exception as e:
        return {
            "error": f"Failed to get file info: {str(e)}",
            "traceback": traceback.format_exc(),
            "file_path": file_path,
        }


@cache_tool_result(ttl=300, cache_type="project_stats", key_prefix="project_summary_")
async def get_project_summary() -> Dict[str, Any]:
    """Get overall project statistics and summary.

    Queries PostgreSQL tables to aggregate comprehensive project statistics
    including file counts, session counts, token usage, and language distribution.

    Returns:
        Dict containing project overview with statistics and metrics
    """
    try:
        db = await get_db()

        # Use enhanced project stats from unified context
        project_stats = await db.get_project_stats()

        # Initialize results structure
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "project_overview": project_stats,
            "file_statistics": {},
            "session_statistics": {},
            "language_distribution": {},
            "token_usage": {},
            "monitoring_metrics": {},
            "recent_activity": [],
        }

        # Execute all queries concurrently for better performance
        tasks = [
            _get_context_statistics(db),
            _get_code_statistics(db),
            _get_session_statistics(db),
            _get_language_distribution(db),
            _get_token_usage(db),
            _get_monitoring_overview(db),
            _get_recent_activity(db),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Query {i} failed: {result}")
                continue

            if i == 0:  # context statistics
                summary["project_overview"] = result
            elif i == 1:  # code statistics
                summary["file_statistics"] = result
            elif i == 2:  # session statistics
                summary["session_statistics"] = result
            elif i == 3:  # language distribution
                summary["language_distribution"] = result
            elif i == 4:  # token usage
                summary["token_usage"] = result
            elif i == 5:  # monitoring overview
                summary["monitoring_metrics"] = result
            elif i == 6:  # recent activity
                summary["recent_activity"] = result

        return summary

    except Exception as e:
        return {
            "error": f"Failed to generate project summary: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def _get_context_statistics(db) -> Dict[str, Any]:
    """Get statistics from context_items table."""
    try:
        async with db.pg_pool.acquire() as conn:
            # Total context items
            total_items = await conn.fetchval("SELECT COUNT(*) FROM context_items")

            # Items by source type
            source_types = await conn.fetch(
                """
                SELECT source_type, COUNT(*) as count
                FROM context_items
                GROUP BY source_type
                ORDER BY count DESC
            """
            )

            # Items by entity type
            entity_types = await conn.fetch(
                """
                SELECT entity_type, COUNT(*) as count
                FROM context_items
                GROUP BY entity_type
                ORDER BY count DESC
            """
            )

            return {
                "total_items": total_items,
                "by_source_type": [dict(row) for row in source_types],
                "by_entity_type": [dict(row) for row in entity_types],
            }
    except Exception as e:
        return {"error": str(e)}


async def _get_code_statistics(db) -> Dict[str, Any]:
    """Get statistics from code_elements table."""
    try:
        async with db.pg_pool.acquire() as conn:
            # Total code elements
            total_elements = await conn.fetchval("SELECT COUNT(*) FROM code_elements")

            # Elements by type
            element_types = await conn.fetch(
                """
                SELECT element_type, COUNT(*) as count
                FROM code_elements
                GROUP BY element_type
                ORDER BY count DESC
            """
            )

            # Unique files
            unique_files = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT file_path) FROM code_elements
            """
            )

            # Complexity statistics
            complexity_stats = await conn.fetchrow(
                """
                SELECT
                    AVG(complexity_score) as avg_complexity,
                    MIN(complexity_score) as min_complexity,
                    MAX(complexity_score) as max_complexity,
                    COUNT(*) FILTER (WHERE complexity_score > 10) as high_complexity_count
                FROM code_elements
                WHERE complexity_score IS NOT NULL
            """
            )

            return {
                "total_elements": total_elements,
                "unique_files": unique_files,
                "by_element_type": [dict(row) for row in element_types],
                "complexity": dict(complexity_stats) if complexity_stats else {},
            }
    except Exception as e:
        return {"error": str(e)}


async def _get_session_statistics(db) -> Dict[str, Any]:
    """Get session-related statistics from context_items."""
    try:
        async with db.pg_pool.acquire() as conn:
            # Unique sessions
            unique_sessions = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT session_id) FROM context_items
                WHERE session_id IS NOT NULL
            """
            )

            # Items per session
            session_activity = await conn.fetch(
                """
                SELECT session_id, COUNT(*) as item_count
                FROM context_items
                WHERE session_id IS NOT NULL
                GROUP BY session_id
                ORDER BY item_count DESC
                LIMIT 10
            """
            )

            return {
                "unique_sessions": unique_sessions,
                "top_sessions_by_activity": [dict(row) for row in session_activity],
            }
    except Exception as e:
        return {"error": str(e)}


async def _get_language_distribution(db) -> Dict[str, Any]:
    """Get language distribution from code_elements."""
    try:
        async with db.pg_pool.acquire() as conn:
            # Language distribution
            languages = await conn.fetch(
                """
                SELECT language, COUNT(*) as count, COUNT(DISTINCT file_path) as file_count
                FROM code_elements
                WHERE language IS NOT NULL
                GROUP BY language
                ORDER BY count DESC
            """
            )

            return {"languages": [dict(row) for row in languages]}
    except Exception as e:
        return {"error": str(e)}


async def _get_token_usage(db) -> Dict[str, Any]:
    """Extract token usage from context_items metrics."""
    try:
        async with db.pg_pool.acquire() as conn:
            # Token usage from metrics JSONB field
            token_stats = await conn.fetchrow(
                """
                SELECT
                    SUM(CAST(metrics->>'token_count' AS INTEGER)) as total_tokens,
                    AVG(CAST(metrics->>'token_count' AS INTEGER)) as avg_tokens_per_item,
                    COUNT(*) FILTER (WHERE metrics->>'token_count' IS NOT NULL) as items_with_tokens
                FROM context_items
                WHERE metrics IS NOT NULL
                AND metrics->>'token_count' IS NOT NULL
                AND metrics->>'token_count' ~ '^[0-9]+$'
            """
            )

            return dict(token_stats) if token_stats else {}
    except Exception as e:
        return {"error": str(e)}


async def _get_monitoring_overview(db) -> Dict[str, Any]:
    """Get overview from monitoring_metrics table."""
    try:
        async with db.pg_pool.acquire() as conn:
            # Recent metrics count
            total_metrics = await conn.fetchval(
                "SELECT COUNT(*) FROM monitoring_metrics"
            )

            # Metrics by name
            metric_types = await conn.fetch(
                """
                SELECT metric_name, COUNT(*) as count
                FROM monitoring_metrics
                GROUP BY metric_name
                ORDER BY count DESC
                LIMIT 10
            """
            )

            # Recent timestamp
            latest_metric = await conn.fetchrow(
                """
                SELECT time as timestamp, metric_name, metric_value as value
                FROM monitoring_metrics
                ORDER BY time DESC
                LIMIT 1
            """
            )

            return {
                "total_metrics": total_metrics,
                "by_metric_name": [dict(row) for row in metric_types],
                "latest_metric": dict(latest_metric) if latest_metric else None,
            }
    except Exception as e:
        return {"error": str(e)}


async def _get_recent_activity(db) -> List[Dict[str, Any]]:
    """Get recent activity across all tables."""
    try:
        async with db.pg_pool.acquire() as conn:
            # Most recent context items (assuming there's a timestamp or ID)
            recent_contexts = await conn.fetch(
                """
                SELECT source_type, entity_type, session_id
                FROM context_items
                ORDER BY id DESC
                LIMIT 5
            """
            )

            # Recent monitoring metrics
            recent_metrics = await conn.fetch(
                """
                SELECT metric_name, metric_value as value, time as timestamp
                FROM monitoring_metrics
                ORDER BY time DESC
                LIMIT 5
            """
            )

            activity = []

            # Add context activities
            for row in recent_contexts:
                activity.append(
                    {
                        "type": "context_item",
                        "source_type": row["source_type"],
                        "entity_type": row["entity_type"],
                        "session_id": row["session_id"],
                    }
                )

            # Add metric activities
            for row in recent_metrics:
                activity.append(
                    {
                        "type": "monitoring_metric",
                        "metric_name": row["metric_name"],
                        "value": row["value"],
                        "timestamp": row["timestamp"].isoformat()
                        if row["timestamp"]
                        else None,
                    }
                )

            return activity[:10]  # Return top 10 recent activities

    except Exception as e:
        return [{"error": str(e)}]


async def find_files(
    pattern: str = "*",
    file_type: Optional[str] = None,
    element_type: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Search files by pattern or criteria.

    Args:
        pattern: File path pattern (supports glob patterns like *.py, **/*.js)
        file_type: Filter by file extension (e.g., 'py', 'js', 'md')
        element_type: Filter by code element type (e.g., 'function', 'class')
        language: Filter by programming language
        limit: Maximum number of results to return

    Returns:
        Dict containing matched files and metadata
    """
    try:
        db = await get_db()

        # Use unified context search for enhanced file discovery
        search_params = {"limit": limit}

        # Pattern matching for file paths
        if pattern and pattern != "*":
            # Convert glob pattern for unified context search
            sql_pattern = pattern.replace("*", "").replace("?", "_")
            search_params["file_path"] = sql_pattern

        # File type filter
        if file_type:
            if "file_path" in search_params:
                search_params["file_path"] += f".{file_type}"
            else:
                search_params["file_path"] = f".{file_type}"

        # Entity type filter for code elements
        entity_types = []
        if element_type:
            entity_types.append(element_type)
        if entity_types:
            search_params["entity_types"] = entity_types

        # Language filtering (handled via source_types in unified context)
        source_types = ["code"]  # Focus on code-related items
        if language:
            # Could extend this to filter by language in metrics/tags
            search_params["source_types"] = source_types
        else:
            search_params["source_types"] = source_types

        # Search unified context for file-related items
        context_items = await db.search_context_items(**search_params)

        # Process unified context results to extract file information
        file_map = {}
        for item in context_items:
            file_path = item.get("file_path")
            if not file_path:
                continue

            if file_path not in file_map:
                file_map[file_path] = {
                    "file_path": file_path,
                    "entity_types": set(),
                    "source_types": set(),
                    "items": [],
                    "complexity_scores": [],
                }

            file_info = file_map[file_path]
            file_info["entity_types"].add(item.get("entity_type", "unknown"))
            file_info["source_types"].add(item.get("source_type", "unknown"))
            file_info["items"].append(item)

            # Extract complexity from metrics if available
            metrics = item.get("metrics", {})
            if isinstance(metrics, dict) and "complexity_score" in metrics:
                try:
                    score = float(metrics["complexity_score"])
                    file_info["complexity_scores"].append(score)
                except (ValueError, TypeError):
                    pass

        # Convert to final format
        files = []
        for file_path, file_info in file_map.items():
            complexity_scores = file_info["complexity_scores"]
            file_data = {
                "file_path": file_path,
                "entity_count": len(file_info["items"]),
                "entity_types": list(file_info["entity_types"]),
                "source_types": list(file_info["source_types"]),
                "max_complexity": max(complexity_scores) if complexity_scores else None,
                "avg_complexity": sum(complexity_scores) / len(complexity_scores)
                if complexity_scores
                else None,
                "item_count": len(file_info["items"]),
            }
            files.append(file_data)

        # Sort by file path
        files.sort(key=lambda x: x["file_path"])

        # Summary statistics
        total_files = len(files)
        entity_types = list(set(et for f in files for et in f["entity_types"]))
        source_types = list(set(st for f in files for st in f["source_types"]))
        total_items = sum(f["item_count"] for f in files)

        return {
            "success": True,
            "pattern": pattern,
            "filters": {
                "file_type": file_type,
                "element_type": element_type,
                "language": language,
            },
            "summary": {
                "total_files": total_files,
                "total_items": total_items,
                "entity_types": entity_types,
                "source_types": source_types,
                "limit_applied": total_files == limit,
            },
            "files": files,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "pattern": pattern,
            "filters": {
                "file_type": file_type,
                "element_type": element_type,
                "language": language,
            },
            "files": [],
        }


# Helper functions for get_file_info


async def _get_file_system_info(file_path: str) -> Dict[str, Any]:
    """Get basic file system information."""
    try:
        if not os.path.exists(file_path):
            return {"exists": False, "error": "File not found"}

        stat = os.stat(file_path)
        path_obj = Path(file_path)

        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "size_human": _format_file_size(stat.st_size),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "is_file": path_obj.is_file(),
            "is_directory": path_obj.is_dir(),
            "suffix": path_obj.suffix,
            "name": path_obj.name,
            "parent": str(path_obj.parent),
            "permissions": oct(stat.st_mode)[-3:],
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}


async def _get_code_elements(db, file_path: str) -> List[Dict[str, Any]]:
    """Get code elements for the specified file."""
    try:
        query = """
        SELECT
            file_path,
            element_type,
            element_name,
            language,
            complexity_score as complexity
        FROM code_elements
        WHERE file_path = $1
        ORDER BY element_type, element_name
        """

        rows = await db.fetch_many(query, file_path)
        return rows

    except Exception as e:
        return [{"error": f"Failed to fetch code elements: {str(e)}"}]


async def _get_context_items(db, file_path: str) -> List[Dict[str, Any]]:
    """Get context items related to the file."""
    try:
        # Query for context items that mention this file
        query = """
        SELECT
            source_type,
            entity_type,
            content,
            metrics,
            session_id
        FROM context_items
        WHERE content LIKE '%' || $1 || '%'
           OR (metrics->>'file_path') = $1
        ORDER BY id DESC
        LIMIT 50
        """

        rows = await db.fetch_many(query, file_path)
        return rows

    except Exception as e:
        return [{"error": f"Failed to fetch context items: {str(e)}"}]


async def _get_monitoring_metrics(db, file_path: str) -> Dict[str, Any]:
    """Get monitoring metrics for the file."""
    try:
        query = """
        SELECT
            metric_name,
            metric_value as value,
            time as timestamp,
            labels as tags
        FROM monitoring_metrics
        WHERE labels->>'file_path' = $1
        ORDER BY time DESC
        LIMIT 100
        """

        rows = await db.fetch_many(query, file_path)

        # Group metrics by name for easier analysis
        metrics_by_name = {}
        for row in rows:
            name = row["metric_name"]
            if name not in metrics_by_name:
                metrics_by_name[name] = []
            metrics_by_name[name].append(row)

        return {
            "total_metrics": len(rows),
            "metrics_by_name": metrics_by_name,
            "recent_metrics": rows[:10],  # Most recent 10 metrics
        }

    except Exception as e:
        return {"error": f"Failed to fetch monitoring metrics: {str(e)}"}


async def _get_file_relationships(db, file_path: str) -> Dict[str, Any]:
    """Get file relationships from Neo4j if available."""
    try:
        if not db.neo4j_driver:
            return {"available": False, "reason": "Neo4j not connected"}

        # Query for file node and its relationships
        cypher_query = """
        MATCH (f:File {path: $file_path})
        OPTIONAL MATCH (f)-[r]-(related)
        RETURN
            f as file_node,
            collect(DISTINCT {
                relationship_type: type(r),
                related_node: related,
                direction: CASE
                    WHEN startNode(r) = f THEN 'outgoing'
                    ELSE 'incoming'
                END
            }) as relationships
        """

        results = await db.run_cypher(cypher_query, file_path=file_path)

        if not results:
            return {
                "available": True,
                "found": False,
                "message": "File not found in graph database",
            }

        return {
            "available": True,
            "found": True,
            "file_node": results[0].get("file_node"),
            "relationships": results[0].get("relationships", []),
            "relationship_count": len(results[0].get("relationships", [])),
        }

    except Exception as e:
        return {"available": True, "error": f"Failed to query Neo4j: {str(e)}"}


def _group_elements_by_type(elements: List[Dict[str, Any]]) -> Dict[str, int]:
    """Group code elements by type and count them."""
    type_counts = {}
    for element in elements:
        if "error" in element:
            continue
        element_type = element.get("element_type", "unknown")
        type_counts[element_type] = type_counts.get(element_type, 0) + 1
    return type_counts


def _group_context_by_type(context_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Group context items by type and count them."""
    type_counts = {}
    for item in context_items:
        if "error" in item:
            continue
        item_type = item.get("entity_type", "unknown")
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    return type_counts


def _calculate_complexity_summary(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregated complexity metrics."""
    if not elements or any("error" in elem for elem in elements):
        return {"error": "No valid elements for complexity calculation"}

    complexities = []
    for element in elements:
        if element.get("complexity") is not None:
            try:
                complexities.append(float(element["complexity"]))
            except (ValueError, TypeError):
                continue

    if not complexities:
        return {"total_elements": len(elements), "complexity_available": False}

    return {
        "total_elements": len(elements),
        "complexity_available": True,
        "total_complexity": sum(complexities),
        "average_complexity": sum(complexities) / len(complexities),
        "max_complexity": max(complexities),
        "min_complexity": min(complexities),
        "elements_with_complexity": len(complexities),
    }


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"


async def find_symbols(
    name: Optional[str] = None,
    symbol_type: Optional[str] = None,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Search for functions, classes, variables, and other code symbols.

    Args:
        name: Symbol name to search for (supports partial matching)
        symbol_type: Type of symbol (function, class, variable, method, constant)
        file_path: File path to search within (supports partial matching)
        language: Programming language to filter by
        limit: Maximum number of results to return (default: 50)

    Returns:
        Dictionary containing search results with symbol information including
        file location, symbol type, and signature/definition details.
    """
    try:
        db = await get_db()

        # Build the query dynamically based on provided filters
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

        if name:
            param_count += 1
            base_query += f" AND element_name ILIKE ${param_count}"
            params.append(f"%{name}%")

        if symbol_type:
            param_count += 1
            base_query += f" AND element_type = ${param_count}"
            params.append(symbol_type)

        if file_path:
            param_count += 1
            base_query += f" AND file_path ILIKE ${param_count}"
            params.append(f"%{file_path}%")

        if language:
            param_count += 1
            base_query += f" AND language = ${param_count}"
            params.append(language)

        # Add ordering and limit - adjust based on whether name filter exists
        if name:
            # Find the index of the name parameter for ordering
            name_param_idx = next(
                i + 1 for i, p in enumerate(params) if p == f"%{name}%"
            )
            base_query += f"""
            ORDER BY
                CASE WHEN element_name ILIKE ${name_param_idx} THEN 0 ELSE 1 END,
                file_path,
                COALESCE(line_start, 0)
            LIMIT ${param_count + 1}
            """
        else:
            base_query += f"""
            ORDER BY
                file_path,
                COALESCE(line_start, 0)
            LIMIT ${param_count + 1}
            """

        params.append(limit)

        async with db.pg_pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)

            results = []
            for row in rows:
                # Extract additional metadata from proj_intel_data if available
                proj_data = row.get("proj_intel_data") or {}

                result = {
                    "file_path": row["file_path"],
                    "symbol_type": row["element_type"],
                    "name": row["element_name"],
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
                    "modifiers": proj_data.get("modifiers", []),
                    "parameters": proj_data.get("parameters", []),
                    "return_type": proj_data.get("return_type"),
                    "decorators": proj_data.get("decorators", []),
                }
                results.append(result)

            return {
                "success": True,
                "results": results,
                "count": len(results),
                "filters_applied": {
                    "name": name,
                    "symbol_type": symbol_type,
                    "file_path": file_path,
                    "language": language,
                    "limit": limit,
                },
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search symbols: {str(e)}",
            "results": [],
            "count": 0,
        }


async def get_symbol_details(file_path: str, symbol_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific symbol in a file.

    Args:
        file_path: Path to the file containing the symbol
        symbol_name: Name of the symbol to get details for

    Returns:
        Dictionary containing detailed symbol information including full content,
        dependencies, and usage patterns.
    """
    try:
        db = await get_db()

        query = """
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
            proj_intel_data,
            dependencies
        FROM code_elements
        WHERE file_path = $1 AND element_name = $2
        """

        async with db.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query, file_path, symbol_name)

            if not row:
                return {
                    "success": False,
                    "error": f"Symbol '{symbol_name}' not found in '{file_path}'",
                    "result": None,
                }

            proj_data = row.get("proj_intel_data") or {}

            result = {
                "file_path": row["file_path"],
                "symbol_type": row["element_type"],
                "name": row["element_name"],
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
                "modifiers": proj_data.get("modifiers", []),
                "parameters": proj_data.get("parameters", []),
                "return_type": proj_data.get("return_type"),
                "decorators": proj_data.get("decorators", []),
                "dependencies": row["dependencies"] or [],
                "calls": proj_data.get("calls", []),
                "full_content": proj_data.get("full_content"),
            }

            return {"success": True, "result": result}

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get symbol details: {str(e)}",
            "result": None,
        }


async def find_symbol_usages(
    symbol_name: str, symbol_type: Optional[str] = None
) -> Dict[str, Any]:
    """Find all usages/references of a symbol across the codebase.

    Args:
        symbol_name: Name of the symbol to find usages for
        symbol_type: Optional symbol type to filter results

    Returns:
        Dictionary containing all files and locations where the symbol is used.
    """
    try:
        db = await get_db()

        # Find the symbol definitions first
        definition_query = """
        SELECT file_path, element_type, signature, line_start, line_end
        FROM code_elements
        WHERE element_name = $1
        """
        params = [symbol_name]

        if symbol_type:
            definition_query += " AND element_type = $2"
            params.append(symbol_type)

        # Find usages in dependencies or other references
        usage_query = """
        SELECT file_path, element_type, element_name as context_name,
               line_start, line_end, dependencies, proj_intel_data
        FROM code_elements
        WHERE (dependencies::text ILIKE $1
               OR proj_intel_data::text ILIKE $1
               OR signature ILIKE $1
               OR docstring ILIKE $1)
        AND element_name != $2
        """
        usage_params = [f"%{symbol_name}%", symbol_name]

        async with db.pg_pool.acquire() as conn:
            # Get definitions
            definition_rows = await conn.fetch(definition_query, *params)

            # Get usages
            usage_rows = await conn.fetch(usage_query, *usage_params)

            definitions = []
            for row in definition_rows:
                definitions.append(
                    {
                        "file_path": row["file_path"],
                        "symbol_type": row["element_type"],
                        "start_line": row["line_start"],
                        "end_line": row["line_end"],
                        "signature": row["signature"],
                    }
                )

            usages = []
            for row in usage_rows:
                # Check if the symbol is actually referenced
                dependencies = row.get("dependencies") or []
                proj_data = row.get("proj_intel_data") or {}
                calls = proj_data.get("calls", [])

                if (
                    symbol_name in str(dependencies)
                    or symbol_name in str(calls)
                    or symbol_name in str(proj_data)
                ):
                    usages.append(
                        {
                            "file_path": row["file_path"],
                            "context_name": row["context_name"],
                            "context_type": row["element_type"],
                            "start_line": row["line_start"],
                            "end_line": row["line_end"],
                        }
                    )

            return {
                "success": True,
                "symbol_name": symbol_name,
                "definitions": definitions,
                "usages": usages,
                "definition_count": len(definitions),
                "usage_count": len(usages),
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find symbol usages: {str(e)}",
            "symbol_name": symbol_name,
            "definitions": [],
            "usages": [],
            "definition_count": 0,
            "usage_count": 0,
        }
