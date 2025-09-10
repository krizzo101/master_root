"""Analysis tools for code complexity metrics and call graph analysis."""

import asyncio
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from ..db.connections import get_db

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


async def get_complexity(
    file_path: Optional[str] = None,
    element_type: Optional[str] = None,
    language: Optional[str] = None,
    threshold: float = 10.0,
) -> Dict[str, Any]:
    """
    Get complexity metrics from code elements.

    Args:
        file_path: Optional file path to filter by
        element_type: Optional element type (function, class, etc.)
        language: Optional programming language filter
        threshold: Complexity threshold for identifying hotspots (default: 10.0)

    Returns:
        Dict containing complexity statistics, distribution, and hotspots
    """
    db = await get_db()

    # Build dynamic query with optional filters
    where_conditions = []
    params = []
    param_counter = 1

    if file_path:
        where_conditions.append(f"file_path = ${param_counter}")
        params.append(file_path)
        param_counter += 1

    if element_type:
        where_conditions.append(f"element_type = ${param_counter}")
        params.append(element_type)
        param_counter += 1

    if language:
        where_conditions.append(f"language = ${param_counter}")
        params.append(language)
        param_counter += 1

    # Add complexity filter (only include elements with numeric complexity)
    where_conditions.append("complexity_score IS NOT NULL AND complexity_score > 0")

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    # Search for code elements with complexity data from unified context
    search_params = {"source_types": ["code"], "limit": 10000}

    if file_path:
        search_params["file_path"] = file_path
    if element_type:
        search_params["entity_types"] = [element_type]

    context_items = await db.search_context_items(**search_params)

    # Extract complexity scores from unified context items
    complexity_scores = []
    elements_data = []

    for item in context_items:
        metrics = item.get("metrics", {})
        if isinstance(metrics, dict) and "complexity_score" in metrics:
            try:
                score = float(metrics["complexity_score"])
                if score > 0:  # Only include valid positive scores
                    complexity_scores.append(score)
                    elements_data.append(
                        {
                            "file_path": item.get("file_path"),
                            "entity_type": item.get("entity_type"),
                            "complexity_score": score,
                            "title": item.get("title"),
                            "function_name": item.get("function_name"),
                            "class_name": item.get("class_name"),
                        }
                    )
            except (ValueError, TypeError):
                continue

    # Calculate statistics
    if complexity_scores:
        complexity_scores.sort()
        total_elements = len(complexity_scores)
        avg_complexity = sum(complexity_scores) / total_elements
        min_complexity = min(complexity_scores)
        max_complexity = max(complexity_scores)

        # Calculate percentiles
        def percentile(data, p):
            k = (len(data) - 1) * p
            f = int(k)
            c = f + 1
            if c >= len(data):
                return data[-1]
            return data[f] + (data[c] - data[f]) * (k - f)

        median_complexity = percentile(complexity_scores, 0.5)
        p75_complexity = percentile(complexity_scores, 0.75)
        p95_complexity = percentile(complexity_scores, 0.95)
        high_complexity_count = sum(
            1 for score in complexity_scores if score > threshold
        )

        stats = {
            "total_elements": total_elements,
            "avg_complexity": avg_complexity,
            "min_complexity": min_complexity,
            "max_complexity": max_complexity,
            "median_complexity": median_complexity,
            "p75_complexity": p75_complexity,
            "p95_complexity": p95_complexity,
            "high_complexity_count": high_complexity_count,
        }
    else:
        stats = {
            "total_elements": 0,
            "avg_complexity": None,
            "min_complexity": None,
            "max_complexity": None,
            "median_complexity": None,
            "p75_complexity": None,
            "p95_complexity": None,
            "high_complexity_count": 0,
        }

    # Calculate complexity distribution from unified context data
    distribution_buckets = {
        "1-5 (Low)": 0,
        "6-10 (Medium)": 0,
        "11-20 (High)": 0,
        "21+ (Very High)": 0,
    }

    for score in complexity_scores:
        if score <= 5:
            distribution_buckets["1-5 (Low)"] += 1
        elif score <= 10:
            distribution_buckets["6-10 (Medium)"] += 1
        elif score <= 20:
            distribution_buckets["11-20 (High)"] += 1
        else:
            distribution_buckets["21+ (Very High)"] += 1

    total_for_dist = sum(distribution_buckets.values())
    distribution = []
    for bucket, count in distribution_buckets.items():
        percentage = (
            round(count * 100.0 / total_for_dist, 2) if total_for_dist > 0 else 0
        )
        distribution.append(
            {"complexity_bucket": bucket, "count": count, "percentage": percentage}
        )

    # Find high-complexity hotspots from unified context data
    high_complexity_elements = [
        elem for elem in elements_data if elem["complexity_score"] > threshold
    ]
    high_complexity_elements.sort(key=lambda x: x["complexity_score"], reverse=True)

    hotspots = []
    for elem in high_complexity_elements[:20]:  # Top 20 hotspots
        hotspots.append(
            {
                "file_path": elem["file_path"],
                "element_type": elem["entity_type"],
                "name": elem["function_name"] or elem["class_name"] or elem["title"],
                "complexity": elem["complexity_score"],
            }
        )

    # Calculate complexity by file (aggregated) from unified context data
    file_stats = {}
    for elem in elements_data:
        file_path = elem["file_path"]
        if file_path not in file_stats:
            file_stats[file_path] = {
                "file_path": file_path,
                "element_count": 0,
                "complexity_scores": [],
            }
        file_stats[file_path]["element_count"] += 1
        file_stats[file_path]["complexity_scores"].append(elem["complexity_score"])

    file_complexity = []
    for file_path, data in file_stats.items():
        scores = data["complexity_scores"]
        file_complexity.append(
            {
                "file_path": file_path,
                "element_count": data["element_count"],
                "avg_complexity": sum(scores) / len(scores),
                "max_complexity": max(scores),
                "total_complexity": sum(scores),
            }
        )
    file_complexity.sort(key=lambda x: x["avg_complexity"], reverse=True)
    file_complexity = file_complexity[:10]  # Top 10 files

    # Calculate complexity by element type from unified context data
    type_stats = {}
    for elem in elements_data:
        entity_type = elem["entity_type"] or "unknown"
        if entity_type not in type_stats:
            type_stats[entity_type] = {
                "element_type": entity_type,
                "element_count": 0,
                "complexity_scores": [],
            }
        type_stats[entity_type]["element_count"] += 1
        type_stats[entity_type]["complexity_scores"].append(elem["complexity_score"])

    type_complexity = []
    for entity_type, data in type_stats.items():
        scores = data["complexity_scores"]
        type_complexity.append(
            {
                "element_type": entity_type,
                "element_count": data["element_count"],
                "avg_complexity": sum(scores) / len(scores),
                "min_complexity": min(scores),
                "max_complexity": max(scores),
            }
        )
    type_complexity.sort(key=lambda x: x["avg_complexity"], reverse=True)

    # Format results
    result = {
        "summary": {
            "total_elements": stats["total_elements"] if stats else 0,
            "average_complexity": round(float(stats["avg_complexity"]), 2)
            if stats and stats["avg_complexity"]
            else 0,
            "median_complexity": round(float(stats["median_complexity"]), 2)
            if stats and stats["median_complexity"]
            else 0,
            "min_complexity": float(stats["min_complexity"])
            if stats and stats["min_complexity"]
            else 0,
            "max_complexity": float(stats["max_complexity"])
            if stats and stats["max_complexity"]
            else 0,
            "p75_complexity": round(float(stats["p75_complexity"]), 2)
            if stats and stats["p75_complexity"]
            else 0,
            "p95_complexity": round(float(stats["p95_complexity"]), 2)
            if stats and stats["p95_complexity"]
            else 0,
            "high_complexity_count": stats["high_complexity_count"] if stats else 0,
            "high_complexity_percentage": round(
                (stats["high_complexity_count"] / stats["total_elements"] * 100), 2
            )
            if stats and stats["total_elements"] > 0
            else 0,
        },
        "distribution": [
            {
                "complexity_range": row["complexity_bucket"],
                "count": row["count"],
                "percentage": float(row["percentage"]),
            }
            for row in distribution
        ],
        "hotspots": [
            {
                "file_path": row["file_path"],
                "element_type": row["element_type"],
                "name": row["name"],
                "complexity": float(row["complexity"]),
                "language": row["language"],
                "location": {
                    "line_start": row["line_start"],
                    "line_end": row["line_end"],
                }
                if row["line_start"] and row["line_end"]
                else None,
            }
            for row in hotspots
        ],
        "by_file": [
            {
                "file_path": row["file_path"],
                "language": row["language"],
                "element_count": row["element_count"],
                "average_complexity": round(float(row["avg_complexity"]), 2),
                "max_complexity": float(row["max_complexity"]),
                "total_complexity": float(row["total_complexity"]),
            }
            for row in file_complexity
        ],
        "by_element_type": [
            {
                "element_type": row["element_type"],
                "element_count": row["element_count"],
                "average_complexity": round(float(row["avg_complexity"]), 2),
                "min_complexity": float(row["min_complexity"]),
                "max_complexity": float(row["max_complexity"]),
            }
            for row in type_complexity
        ],
        "filters": {
            "file_path": file_path,
            "element_type": element_type,
            "language": language,
            "complexity_threshold": threshold,
        },
    }

    return result


async def get_call_graph(
    file_path: Optional[str] = None,
    include_external: bool = True,
    max_depth: int = 10,
    complexity_threshold: float = 15.0,
) -> Dict[str, Any]:
    """
    Get function call relationships by combining Neo4j CALLS relationships with PostgreSQL code analysis.

    Args:
        file_path: Optional file path to filter by
        include_external: Whether to include external library calls (default: True)
        max_depth: Maximum depth for call hierarchy analysis (default: 10)
        complexity_threshold: Threshold for identifying complex call chains (default: 15.0)

    Returns:
        Dictionary containing call hierarchy with:
        - nodes: List of functions/methods with metadata including complexity
        - edges: List of call relationships with frequency and context
        - hierarchy: Nested structure showing call chains with depth analysis
        - statistics: Comprehensive call frequency, complexity, and relationship metrics
        - insights: Analytical insights about call patterns and potential issues
    """
    db = await get_db()

    # Initialize result structure
    call_graph = {
        "nodes": [],
        "edges": [],
        "hierarchy": {},
        "statistics": {
            "total_functions": 0,
            "total_calls": 0,
            "max_depth": 0,
            "avg_calls_per_function": 0.0,
            "most_called": [],
            "most_calling": [],
            "call_frequency": {},
            "complexity_metrics": {},
            "hotspots": [],
        },
        "insights": {
            "circular_dependencies": [],
            "dead_code_candidates": [],
            "refactoring_suggestions": [],
            "architectural_patterns": [],
        },
    }

    try:
        # Build dynamic query with optional filters
        where_conditions = ["element_type IN ('function', 'method', 'async_function')"]
        params = []

        if file_path:
            where_conditions.append("file_path = $1")
            params.append(file_path)

        where_clause = " AND ".join(where_conditions)

        # Enhanced query for functions with additional metadata
        functions_query = f"""
        SELECT
            file_path,
            element_name,
            element_type,
            line_start,
            line_end,
            complexity_score as complexity,
            proj_intel_data->>'content' as content,
            proj_intel_data->>'signature' as signature,
            proj_intel_data->>'docstring' as docstring,
            proj_intel_data->>'parameters' as parameters,
            language
        FROM code_elements
        WHERE {where_clause}
        ORDER BY file_path, line_start
        """

        functions = await db.fetch_many(functions_query, *params)
        function_lookup = {}

        # Build enhanced nodes list
        for func in functions:
            node_id = f"{func['file_path']}:{func['element_name']}"
            node = {
                "id": node_id,
                "name": func["element_name"],
                "file": func["file_path"],
                "type": func["element_type"],
                "line_start": func["line_start"],
                "line_end": func["line_end"],
                "complexity": func["complexity"] or 0,
                "language": func["language"],
                "signature": func["signature"],
                "docstring": func["docstring"],
                "parameters": func["parameters"],
                "calls_out": [],
                "called_by": [],
                "in_degree": 0,
                "out_degree": 0,
            }
            call_graph["nodes"].append(node)
            function_lookup[node_id] = node

        call_graph["statistics"]["total_functions"] = len(functions)

        # Enhanced Neo4j query for CALLS relationships with more context
        file_filter = ""
        cypher_params = {}

        if file_path:
            file_filter = (
                "WHERE caller.file_path = $file_path OR callee.file_path = $file_path"
            )
            cypher_params["file_path"] = file_path

        cypher_query = f"""
        MATCH (caller:Function)-[r:CALLS]->(callee:Function)
        {file_filter}
        RETURN
            caller.file_path as caller_file,
            caller.name as caller_name,
            caller.complexity as caller_complexity,
            callee.file_path as callee_file,
            callee.name as callee_name,
            callee.complexity as callee_complexity,
            r.frequency as call_frequency,
            r.line_number as call_line,
            r.context as call_context,
            r.is_recursive as is_recursive,
            r.call_type as call_type
        ORDER BY r.frequency DESC, caller_file, caller_name
        """

        neo4j_results = await db.run_cypher(cypher_query, **cypher_params)

        call_frequency = defaultdict(int)
        caller_frequency = defaultdict(int)
        complexity_weights = {}

        # Process CALLS relationships from Neo4j
        for record in neo4j_results:
            caller_id = f"{record['caller_file']}:{record['caller_name']}"
            callee_id = f"{record['callee_file']}:{record['callee_name']}"
            frequency = record.get("call_frequency", 1)
            call_line = record.get("call_line")
            call_context = record.get("call_context", "")
            is_recursive = record.get("is_recursive", False)
            call_type = record.get("call_type", "direct")
            caller_complexity = record.get("caller_complexity", 0)
            callee_complexity = record.get("callee_complexity", 0)

            # Filter external calls if not requested
            if not include_external and (
                "/site-packages/" in record["callee_file"]
                or record["callee_file"].startswith("external:")
            ):
                continue

            edge = {
                "from": caller_id,
                "to": callee_id,
                "frequency": frequency,
                "call_line": call_line,
                "context": call_context,
                "is_recursive": is_recursive,
                "call_type": call_type,
                "weight": frequency
                * (1 + (caller_complexity + callee_complexity) / 20.0),
            }
            call_graph["edges"].append(edge)

            # Update nodes with enhanced call relationships
            if caller_id in function_lookup:
                function_lookup[caller_id]["calls_out"].append(
                    {
                        "function": callee_id,
                        "frequency": frequency,
                        "line": call_line,
                        "context": call_context,
                        "is_recursive": is_recursive,
                        "call_type": call_type,
                    }
                )
                function_lookup[caller_id]["out_degree"] += 1

            if callee_id in function_lookup:
                function_lookup[callee_id]["called_by"].append(
                    {
                        "function": caller_id,
                        "frequency": frequency,
                        "context": call_context,
                    }
                )
                function_lookup[callee_id]["in_degree"] += 1

            # Track comprehensive statistics
            call_frequency[callee_id] += frequency
            caller_frequency[caller_id] += frequency
            complexity_weights[caller_id] = caller_complexity
            complexity_weights[callee_id] = callee_complexity

        call_graph["statistics"]["total_calls"] = len(neo4j_results)

        # If Neo4j doesn't have call data, fallback to code analysis
        if not neo4j_results:
            await _analyze_calls_from_code(
                db, call_graph, function_lookup, file_path, include_external
            )

        # Build enhanced hierarchy and statistics
        await _build_enhanced_call_hierarchy(call_graph, function_lookup, max_depth)

        # Calculate comprehensive statistics
        total_functions = len(function_lookup)
        total_calls = len(call_graph["edges"])

        call_graph["statistics"]["avg_calls_per_function"] = round(
            total_calls / total_functions if total_functions > 0 else 0, 2
        )

        # Most called functions
        if call_frequency:
            sorted_calls = sorted(
                call_frequency.items(), key=lambda x: x[1], reverse=True
            )
            call_graph["statistics"]["most_called"] = [
                {
                    "function": func_id,
                    "frequency": freq,
                    "complexity": complexity_weights.get(func_id, 0),
                    "in_degree": function_lookup.get(func_id, {}).get("in_degree", 0),
                }
                for func_id, freq in sorted_calls[:10]
            ]

        # Most calling functions (high fan-out)
        if caller_frequency:
            sorted_callers = sorted(
                caller_frequency.items(), key=lambda x: x[1], reverse=True
            )
            call_graph["statistics"]["most_calling"] = [
                {
                    "function": func_id,
                    "call_count": count,
                    "complexity": complexity_weights.get(func_id, 0),
                    "out_degree": function_lookup.get(func_id, {}).get("out_degree", 0),
                }
                for func_id, count in sorted_callers[:10]
            ]

        # Complexity-based hotspots
        hotspots = []
        for node in call_graph["nodes"]:
            if node["complexity"] >= complexity_threshold or (
                node["in_degree"] >= 5 and node["complexity"] >= 8
            ):
                hotspots.append(
                    {
                        "function": node["id"],
                        "name": node["name"],
                        "file": node["file"],
                        "complexity": node["complexity"],
                        "in_degree": node["in_degree"],
                        "out_degree": node["out_degree"],
                        "hotspot_score": node["complexity"]
                        + (node["in_degree"] * 2)
                        + node["out_degree"],
                    }
                )

        hotspots.sort(key=lambda x: x["hotspot_score"], reverse=True)
        call_graph["statistics"]["hotspots"] = hotspots[:15]

        # Generate analytical insights
        await _generate_call_graph_insights(
            call_graph, function_lookup, complexity_threshold
        )

        call_graph["statistics"]["call_frequency"] = dict(call_frequency)
        call_graph["statistics"]["complexity_metrics"] = {
            "avg_complexity": round(
                sum(complexity_weights.values()) / len(complexity_weights)
                if complexity_weights
                else 0,
                2,
            ),
            "max_complexity": max(complexity_weights.values())
            if complexity_weights
            else 0,
            "high_complexity_functions": len(
                [c for c in complexity_weights.values() if c >= complexity_threshold]
            ),
        }

    except Exception as e:
        return {
            "error": f"Failed to build call graph: {str(e)}",
            "nodes": [],
            "edges": [],
            "hierarchy": {},
            "statistics": {"total_functions": 0, "total_calls": 0},
        }

    return call_graph


async def _analyze_calls_from_code(
    db, call_graph, function_lookup, file_path=None, include_external=True
):
    """Fallback: Analyze function calls from code content when Neo4j data unavailable."""

    # Pattern to match function calls in code
    call_patterns = [
        r"(\w+)\s*\(",  # Simple function calls
        r"self\.(\w+)\s*\(",  # Method calls on self
        r"(\w+)\.(\w+)\s*\(",  # Method calls on objects
        r"await\s+(\w+)\s*\(",  # Async function calls
    ]

    for node in call_graph["nodes"]:
        try:
            # Get the function's code content
            content_query = """
            SELECT proj_intel_data->>'content' as content FROM code_elements
            WHERE file_path = $1 AND element_name = $2
            LIMIT 1
            """
            result = await db.fetch_one(content_query, node["file"], node["name"])

            if not result or not result.get("content"):
                continue

            content = result["content"]

            # Find function calls in the content
            for pattern in call_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)

                for match in matches:
                    called_func = match.group(1)

                    # Skip common built-ins and keywords
                    if called_func in [
                        "print",
                        "len",
                        "str",
                        "int",
                        "float",
                        "list",
                        "dict",
                        "set",
                        "if",
                        "for",
                        "while",
                        "try",
                        "def",
                        "class",
                    ]:
                        continue

                    # Try to find the called function in our function lookup
                    possible_targets = [
                        f"{node['file']}:{called_func}",  # Same file
                        called_func,  # Search by name across files
                    ]

                    target_id = None
                    for possible_id in possible_targets:
                        if possible_id in function_lookup:
                            target_id = possible_id
                            break

                    # If not found by exact match, search by function name
                    if not target_id:
                        for func_id in function_lookup.keys():
                            if func_id.endswith(f":{called_func}"):
                                target_id = func_id
                                break

                    if target_id and target_id != node["id"]:
                        # Add edge if not already exists
                        edge = {
                            "from": node["id"],
                            "to": target_id,
                            "frequency": 1,
                            "call_line": None,
                        }

                        # Check if edge already exists
                        edge_exists = any(
                            e["from"] == edge["from"] and e["to"] == edge["to"]
                            for e in call_graph["edges"]
                        )

                        if not edge_exists:
                            call_graph["edges"].append(edge)

                            # Update nodes
                            function_lookup[node["id"]]["calls_out"].append(
                                {"function": target_id, "frequency": 1, "line": None}
                            )

                            function_lookup[target_id]["called_by"].append(
                                {"function": node["id"], "frequency": 1}
                            )

        except Exception as e:
            print(f"Error analyzing calls for {node['id']}: {e}")
            continue


async def _build_enhanced_call_hierarchy(call_graph, function_lookup, max_depth=10):
    """Build hierarchical call structure and calculate depth metrics."""

    hierarchy = {}

    # Find root functions (not called by others or entry points)
    root_functions = []
    for node in call_graph["nodes"]:
        if not node["called_by"] or any(
            "main" in node["name"].lower() for node in [node]
        ):
            root_functions.append(node["id"])

    # If no clear roots, use functions with the most outgoing calls
    if not root_functions:
        root_functions = sorted(
            call_graph["nodes"], key=lambda x: len(x["calls_out"]), reverse=True
        )[:5]
        root_functions = [f["id"] for f in root_functions]

    actual_max_depth = 0

    def build_tree(func_id, visited=None, depth=0):
        nonlocal actual_max_depth

        if visited is None:
            visited = set()

        if func_id in visited:  # Prevent infinite recursion
            return {"function": func_id, "calls": [], "depth": depth, "cyclic": True}

        if depth >= max_depth:  # Respect max_depth limit
            return {"function": func_id, "calls": [], "depth": depth, "truncated": True}

        visited.add(func_id)
        actual_max_depth = max(actual_max_depth, depth)

        node = function_lookup.get(func_id, {})
        calls = []

        for call_info in node.get("calls_out", []):
            called_func = call_info["function"]
            subtree = build_tree(called_func, visited.copy(), depth + 1)
            subtree["call_frequency"] = call_info.get("frequency", 1)
            subtree["call_context"] = call_info.get("context", "")
            subtree["is_recursive"] = call_info.get("is_recursive", False)
            calls.append(subtree)

        # Sort calls by frequency for better visualization
        calls.sort(key=lambda x: x.get("call_frequency", 0), reverse=True)

        return {
            "function": func_id,
            "name": node.get("name", func_id.split(":")[-1]),
            "file": node.get("file", ""),
            "calls": calls,
            "depth": depth,
            "complexity": node.get("complexity", 0),
            "in_degree": node.get("in_degree", 0),
            "out_degree": node.get("out_degree", 0),
            "signature": node.get("signature", ""),
            "cyclic": False,
            "truncated": False,
        }

    # Build hierarchy trees from root functions
    for root_id in root_functions:
        if root_id in function_lookup:
            hierarchy[root_id] = build_tree(root_id)

    call_graph["hierarchy"] = hierarchy
    call_graph["statistics"]["max_depth"] = actual_max_depth


async def get_imports() -> Dict[str, Any]:
    """Import analysis - Query code_elements for import statements, group by module and package, identify circular dependencies.

    Returns:
        Dictionary containing:
        - imports_by_file: Mapping of file paths to their import statements
        - imports_by_module: Grouping of imports by target module/package
        - circular_dependencies: List of circular dependency chains
        - import_statistics: Overall import statistics
        - dependency_graph: Adjacency list representation of file dependencies
    """
    # Get database connection
    db = await get_db()

    # Import patterns for different languages
    import_patterns = {
        "python": [
            r"^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
            r"^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import",
        ],
        "javascript": [
            r'^\s*import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'^\s*const\s+.*?\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            r'^\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        ],
        "typescript": [
            r'^\s*import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'^\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        ],
        "java": [
            r"^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
        ],
        "go": [
            r'^\s*import\s+[\'"]([^\'"]+)[\'"]',
            r'^\s*import\s+.*?\s+[\'"]([^\'"]+)[\'"]',
        ],
        "rust": [
            r"^\s*use\s+([a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)",
            r"^\s*extern\s+crate\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        ],
        "c": [
            r'^\s*#include\s+[<"]([^>"]+)[>"]',
        ],
        "cpp": [
            r'^\s*#include\s+[<"]([^>"]+)[>"]',
        ],
    }

    imports_by_file = {}
    imports_by_module = defaultdict(list)
    dependency_graph = defaultdict(set)
    import_statistics = {
        "total_files_with_imports": 0,
        "total_import_statements": 0,
        "imports_by_language": defaultdict(int),
        "most_imported_modules": defaultdict(int),
        "files_without_imports": [],
    }

    try:
        # Query code_elements for import statements
        query = """
        SELECT DISTINCT file_path, content, language, line_start, element_type, element_name
        FROM code_elements
        WHERE element_type = 'import'
           OR content ~ ANY(%s)
        ORDER BY file_path, line_start
        """

        # Combine all patterns for database query
        all_patterns = []
        for patterns in import_patterns.values():
            all_patterns.extend(patterns)

        results = await db.fetch_many(query, all_patterns)

        # Process each result
        for row in results:
            file_path = row["file_path"]
            content = row["content"] or ""
            language = (row["language"] or "").lower()
            line_start = row["line_start"] or 0
            element_type = row["element_type"]
            element_name = row["element_name"]

            # Initialize file entry
            if file_path not in imports_by_file:
                imports_by_file[file_path] = {
                    "language": language,
                    "imports": [],
                    "import_count": 0,
                }

            # If it's explicitly marked as import type in the database
            if element_type == "import" and element_name:
                import_info = {
                    "module": element_name,
                    "line": line_start,
                    "type": "explicit",
                    "raw_statement": content[:100]
                    if content
                    else element_name,  # Truncate for display
                }
                imports_by_file[file_path]["imports"].append(import_info)
                imports_by_module[element_name].append(
                    {"file": file_path, "line": line_start}
                )
                dependency_graph[file_path].add(element_name)
                import_statistics["total_import_statements"] += 1
                import_statistics["imports_by_language"][language] += 1
                import_statistics["most_imported_modules"][element_name] += 1

            # Also parse content for import patterns
            if content and language in import_patterns:
                patterns = import_patterns[language]

                for pattern in patterns:
                    matches = re.finditer(
                        pattern, content, re.MULTILINE | re.IGNORECASE
                    )

                    for match in matches:
                        module = match.group(1)

                        # Skip if we already have this import for this file
                        existing_modules = {
                            imp["module"]
                            for imp in imports_by_file[file_path]["imports"]
                        }
                        if module in existing_modules:
                            continue

                        import_info = {
                            "module": module,
                            "line": line_start,
                            "type": "parsed",
                            "raw_statement": match.group(0).strip(),
                        }

                        imports_by_file[file_path]["imports"].append(import_info)
                        imports_by_module[module].append(
                            {"file": file_path, "line": line_start}
                        )
                        dependency_graph[file_path].add(module)
                        import_statistics["total_import_statements"] += 1
                        import_statistics["imports_by_language"][language] += 1
                        import_statistics["most_imported_modules"][module] += 1

        # Update import counts for each file
        for file_path in imports_by_file:
            imports_by_file[file_path]["import_count"] = len(
                imports_by_file[file_path]["imports"]
            )

        import_statistics["total_files_with_imports"] = len(imports_by_file)

        # Get files without imports
        all_files_query = """
        SELECT DISTINCT file_path
        FROM code_elements
        WHERE element_type = 'file'
        """
        all_files_result = await db.fetch_many(all_files_query)
        all_file_paths = {row["file_path"] for row in all_files_result}

        files_with_imports = set(imports_by_file.keys())
        files_without_imports = all_file_paths - files_with_imports
        import_statistics["files_without_imports"] = list(files_without_imports)[
            :20
        ]  # Limit for display

        # Detect circular dependencies
        circular_dependencies = await _detect_circular_dependencies(
            dependency_graph, imports_by_file
        )

        # Convert imports_by_module defaultdict to regular dict for JSON serialization
        imports_by_module_dict = dict(imports_by_module)

        # Sort most imported modules
        most_imported = dict(
            sorted(
                import_statistics["most_imported_modules"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:20]
        )  # Top 20
        import_statistics["most_imported_modules"] = most_imported

        # Convert dependency_graph to serializable format
        dependency_graph_dict = {k: list(v) for k, v in dependency_graph.items()}

        result = {
            "imports_by_file": imports_by_file,
            "imports_by_module": imports_by_module_dict,
            "circular_dependencies": circular_dependencies,
            "import_statistics": dict(import_statistics),
            "dependency_graph": dependency_graph_dict,
        }

        return result

    except Exception as e:
        return {
            "error": f"Failed to analyze imports: {str(e)}",
            "imports_by_file": {},
            "imports_by_module": {},
            "circular_dependencies": [],
            "import_statistics": {},
            "dependency_graph": {},
        }


async def _detect_circular_dependencies(
    dependency_graph: Dict[str, Set[str]], imports_by_file: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Detect circular dependencies in the import graph.

    Args:
        dependency_graph: Mapping of files to their dependencies
        imports_by_file: Import information per file

    Returns:
        List of circular dependency chains with details
    """
    circular_deps = []

    try:
        if not HAS_NETWORKX:
            # NetworkX not available, use a simpler DFS-based approach
            return await _simple_cycle_detection(dependency_graph, imports_by_file)

        # Create a NetworkX directed graph for cycle detection
        G = nx.DiGraph()

        # Add file-to-file dependencies by resolving module names to file paths
        file_to_modules = {}
        module_to_files = defaultdict(list)

        # Build reverse mapping from modules to files
        for file_path, file_info in imports_by_file.items():
            # Extract likely module name from file path
            # This is a heuristic and may need refinement based on project structure
            if file_path.endswith(".py"):
                module_name = (
                    file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
                )
                # Remove common prefixes like 'src.' if present
                if module_name.startswith("src."):
                    module_name = module_name[4:]
                file_to_modules[file_path] = module_name
                module_to_files[module_name].append(file_path)

        # Add edges between files based on imports
        for file_path, dependencies in dependency_graph.items():
            for dep_module in dependencies:
                # Try to resolve module to file path
                potential_files = module_to_files.get(dep_module, [])

                if potential_files:
                    for dep_file in potential_files:
                        if dep_file != file_path:  # Avoid self-loops
                            G.add_edge(file_path, dep_file)
                else:
                    # Check if the module might be a relative import within the same directory
                    file_dir = "/".join(file_path.split("/")[:-1])
                    potential_relative = f"{file_dir}/{dep_module}.py"

                    if potential_relative in imports_by_file:
                        G.add_edge(file_path, potential_relative)

        # Find all strongly connected components (cycles)
        try:
            sccs = list(nx.strongly_connected_components(G))

            for scc in sccs:
                if len(scc) > 1:  # Circular dependency involves multiple files
                    # Find the actual cycle path
                    scc_list = list(scc)
                    try:
                        # Try to find a cycle within this strongly connected component
                        subgraph = G.subgraph(scc_list)
                        cycles = list(nx.simple_cycles(subgraph))

                        if cycles:
                            for cycle in cycles[:5]:  # Limit to first 5 cycles per SCC
                                cycle_info = {
                                    "files": cycle,
                                    "length": len(cycle),
                                    "type": "file_level",
                                    "dependencies": [],
                                }

                                # Add dependency details for each step in the cycle
                                for i in range(len(cycle)):
                                    current_file = cycle[i]
                                    next_file = cycle[(i + 1) % len(cycle)]

                                    # Find which imports create this dependency
                                    if current_file in imports_by_file:
                                        relevant_imports = []
                                        for imp in imports_by_file[current_file][
                                            "imports"
                                        ]:
                                            # Check if this import could lead to next_file
                                            module = imp["module"]
                                            if next_file in module_to_files.get(
                                                module, []
                                            ) or next_file.endswith(f"{module}.py"):
                                                relevant_imports.append(imp)

                                        cycle_info["dependencies"].append(
                                            {
                                                "from_file": current_file,
                                                "to_file": next_file,
                                                "imports": relevant_imports,
                                            }
                                        )

                                circular_deps.append(cycle_info)

                    except Exception as cycle_error:
                        # Fallback: just report the SCC as a circular dependency
                        circular_deps.append(
                            {
                                "files": scc_list,
                                "length": len(scc_list),
                                "type": "strongly_connected_component",
                                "dependencies": [],
                                "note": f"Cycle detection failed: {str(cycle_error)}",
                            }
                        )

        except Exception as scc_error:
            # If SCC detection fails, try a simpler approach
            circular_deps.append(
                {
                    "files": [],
                    "length": 0,
                    "type": "detection_failed",
                    "dependencies": [],
                    "error": f"Circular dependency detection failed: {str(scc_error)}",
                }
            )

    except ImportError:
        # NetworkX not available, use a simpler DFS-based approach
        circular_deps = await _simple_cycle_detection(dependency_graph, imports_by_file)
    except Exception as e:
        circular_deps.append(
            {
                "files": [],
                "length": 0,
                "type": "analysis_error",
                "dependencies": [],
                "error": f"Import analysis error: {str(e)}",
            }
        )

    return circular_deps


async def _simple_cycle_detection(
    dependency_graph: Dict[str, Set[str]], imports_by_file: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Simple DFS-based cycle detection as fallback when NetworkX is unavailable."""
    circular_deps = []

    def dfs_detect_cycle(start_file, current_file, visited, path):
        if current_file in path:
            # Found a cycle
            cycle_start = path.index(current_file)
            cycle = path[cycle_start:] + [current_file]
            return [cycle]

        if current_file in visited:
            return []

        visited.add(current_file)
        path.append(current_file)

        cycles = []

        # Check dependencies
        dependencies = dependency_graph.get(current_file, set())
        for dep in dependencies:
            # For simplicity, assume module names might match file names
            potential_files = []
            for file_path in imports_by_file.keys():
                if dep in file_path or file_path.endswith(f"{dep}.py"):
                    potential_files.append(file_path)

            for dep_file in potential_files:
                if dep_file != current_file:
                    cycles.extend(
                        dfs_detect_cycle(
                            start_file, dep_file, visited.copy(), path.copy()
                        )
                    )

        return cycles

    visited_global = set()

    for file_path in imports_by_file.keys():
        if file_path not in visited_global:
            cycles = dfs_detect_cycle(file_path, file_path, set(), [])

            for cycle in cycles[:3]:  # Limit cycles per file
                if len(cycle) > 2:  # Only consider actual cycles
                    cycle_info = {
                        "files": cycle[:-1],  # Remove duplicate last element
                        "length": len(cycle) - 1,
                        "type": "simple_detection",
                        "dependencies": [],
                        "note": "Detected using simple DFS (NetworkX unavailable)",
                    }
                    circular_deps.append(cycle_info)

            visited_global.update(cycle)

    return circular_deps


async def get_documentation(
    file_path: Optional[str] = None,
    element_type: Optional[str] = None,
    language: Optional[str] = None,
    include_private: bool = False,
) -> Dict[str, Any]:
    """
    Get documentation coverage metrics from code elements.

    Args:
        file_path: Optional file path to filter by
        element_type: Optional element type (function, class, method, etc.)
        language: Optional programming language filter
        include_private: Whether to include private elements (default: False)

    Returns:
        Dict containing documentation coverage statistics, undocumented elements, and analysis
    """
    db = await get_db()

    # Build dynamic query with optional filters
    where_conditions = []
    params = []
    param_counter = 1

    if file_path:
        where_conditions.append(f"file_path = ${param_counter}")
        params.append(file_path)
        param_counter += 1

    if element_type:
        where_conditions.append(f"element_type = ${param_counter}")
        params.append(element_type)
        param_counter += 1

    if language:
        where_conditions.append(f"language = ${param_counter}")
        params.append(language)
        param_counter += 1

    # Filter for documentable elements (functions, classes, methods)
    documentable_types = ["function", "class", "method", "async_function", "property"]
    type_placeholders = ", ".join(
        [f"${param_counter + i}" for i in range(len(documentable_types))]
    )
    where_conditions.append(f"element_type IN ({type_placeholders})")
    params.extend(documentable_types)
    param_counter += len(documentable_types)

    # Exclude private elements unless specifically requested
    if not include_private:
        where_conditions.append("(element_name NOT LIKE '_%' OR element_name IS NULL)")

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    # Query for documentation coverage statistics
    coverage_query = f"""
        WITH documented_elements AS (
            SELECT
                *,
                CASE
                    WHEN proj_intel_data->>'docstring' IS NOT NULL
                         AND proj_intel_data->>'docstring' != ''
                         AND proj_intel_data->>'docstring' != 'null'
                    THEN true
                    WHEN content ~ '('''.*?'''|\"\"\".*?\"\"\"|/\\*\\*.*?\\*/|//.*?$)'
                    THEN true
                    ELSE false
                END as is_documented,
                CASE
                    WHEN element_name LIKE '_%' THEN 'private'
                    WHEN element_name ~ '^[A-Z]' THEN 'public_class'
                    WHEN element_type IN ('function', 'method', 'async_function') THEN 'public_function'
                    ELSE 'public_other'
                END as visibility_type
            FROM code_elements
            WHERE {where_clause}
        )
        SELECT
            COUNT(*) as total_elements,
            SUM(CASE WHEN is_documented THEN 1 ELSE 0 END) as documented_elements,
            ROUND(
                (SUM(CASE WHEN is_documented THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0),
                2
            ) as documentation_percentage,
            COUNT(CASE WHEN visibility_type = 'public_function' THEN 1 END) as public_functions,
            SUM(CASE WHEN visibility_type = 'public_function' AND is_documented THEN 1 ELSE 0 END) as documented_public_functions,
            COUNT(CASE WHEN visibility_type = 'public_class' THEN 1 END) as public_classes,
            SUM(CASE WHEN visibility_type = 'public_class' AND is_documented THEN 1 ELSE 0 END) as documented_public_classes,
            COUNT(CASE WHEN visibility_type = 'private' THEN 1 END) as private_elements,
            SUM(CASE WHEN visibility_type = 'private' AND is_documented THEN 1 ELSE 0 END) as documented_private_elements
        FROM documented_elements
    """

    coverage_stats = await db.fetch_one(coverage_query, *params)

    # Query for undocumented public APIs
    undocumented_query = f"""
        WITH documented_elements AS (
            SELECT
                *,
                CASE
                    WHEN proj_intel_data->>'docstring' IS NOT NULL
                         AND proj_intel_data->>'docstring' != ''
                         AND proj_intel_data->>'docstring' != 'null'
                    THEN true
                    WHEN content ~ '('''.*?'''|\"\"\".*?\"\"\"|/\\*\\*.*?\\*/|//.*?$)'
                    THEN true
                    ELSE false
                END as is_documented
            FROM code_elements
            WHERE {where_clause}
        )
        SELECT
            file_path,
            element_type,
            element_name,
            line_start,
            line_end,
            language,
            proj_intel_data->>'signature' as signature,
            CASE
                WHEN element_name LIKE '_%' THEN 'private'
                WHEN element_name ~ '^[A-Z]' THEN 'public_class'
                WHEN element_type IN ('function', 'method', 'async_function') THEN 'public_function'
                ELSE 'public_other'
            END as visibility_type
        FROM documented_elements
        WHERE NOT is_documented
        ORDER BY
            CASE
                WHEN element_name ~ '^[A-Z]' THEN 1  -- Classes first
                WHEN element_type IN ('function', 'method', 'async_function') THEN 2  -- Functions
                ELSE 3  -- Others
            END,
            file_path, line_start
        LIMIT 50
    """

    undocumented = await db.fetch_many(undocumented_query, *params)

    # Query for documentation coverage by file
    file_coverage_query = f"""
        WITH documented_elements AS (
            SELECT
                file_path,
                language,
                CASE
                    WHEN proj_intel_data->>'docstring' IS NOT NULL
                         AND proj_intel_data->>'docstring' != ''
                         AND proj_intel_data->>'docstring' != 'null'
                    THEN true
                    WHEN content ~ '('''.*?'''|\"\"\".*?\"\"\"|/\\*\\*.*?\\*/|//.*?$)'
                    THEN true
                    ELSE false
                END as is_documented
            FROM code_elements
            WHERE {where_clause}
        )
        SELECT
            file_path,
            language,
            COUNT(*) as total_elements,
            SUM(CASE WHEN is_documented THEN 1 ELSE 0 END) as documented_elements,
            ROUND(
                (SUM(CASE WHEN is_documented THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0),
                2
            ) as coverage_percentage
        FROM documented_elements
        GROUP BY file_path, language
        ORDER BY coverage_percentage ASC, total_elements DESC
        LIMIT 20
    """

    file_coverage = await db.fetch_many(file_coverage_query, *params)

    # Query for documentation coverage by element type
    type_coverage_query = f"""
        WITH documented_elements AS (
            SELECT
                element_type,
                CASE
                    WHEN proj_intel_data->>'docstring' IS NOT NULL
                         AND proj_intel_data->>'docstring' != ''
                         AND proj_intel_data->>'docstring' != 'null'
                    THEN true
                    WHEN content ~ '('''.*?'''|\"\"\".*?\"\"\"|/\\*\\*.*?\\*/|//.*?$)'
                    THEN true
                    ELSE false
                END as is_documented
            FROM code_elements
            WHERE {where_clause}
        )
        SELECT
            element_type,
            COUNT(*) as total_elements,
            SUM(CASE WHEN is_documented THEN 1 ELSE 0 END) as documented_elements,
            ROUND(
                (SUM(CASE WHEN is_documented THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0),
                2
            ) as coverage_percentage
        FROM documented_elements
        GROUP BY element_type
        ORDER BY coverage_percentage DESC
    """

    type_coverage = await db.fetch_many(type_coverage_query, *params)

    # Query for recently documented elements (if we have timestamp data)
    recent_docs_query = f"""
        WITH documented_elements AS (
            SELECT
                file_path,
                element_type,
                element_name,
                proj_intel_data->>'docstring' as docstring_content,
                CASE
                    WHEN proj_intel_data->>'docstring' IS NOT NULL
                         AND proj_intel_data->>'docstring' != ''
                         AND proj_intel_data->>'docstring' != 'null'
                    THEN true
                    ELSE false
                END as is_documented
            FROM code_elements
            WHERE {where_clause}
        )
        SELECT
            file_path,
            element_type,
            element_name,
            LENGTH(docstring_content) as docstring_length
        FROM documented_elements
        WHERE is_documented AND docstring_content IS NOT NULL
        ORDER BY docstring_length DESC
        LIMIT 10
    """

    well_documented = await db.fetch_many(recent_docs_query, *params)

    # Calculate public API documentation percentage
    public_function_coverage = 0.0
    public_class_coverage = 0.0

    if coverage_stats:
        if coverage_stats["public_functions"] > 0:
            public_function_coverage = round(
                (
                    coverage_stats["documented_public_functions"]
                    / coverage_stats["public_functions"]
                    * 100
                ),
                2,
            )

        if coverage_stats["public_classes"] > 0:
            public_class_coverage = round(
                (
                    coverage_stats["documented_public_classes"]
                    / coverage_stats["public_classes"]
                    * 100
                ),
                2,
            )

    # Format results
    result = {
        "summary": {
            "total_elements": coverage_stats["total_elements"] if coverage_stats else 0,
            "documented_elements": coverage_stats["documented_elements"]
            if coverage_stats
            else 0,
            "undocumented_elements": (
                coverage_stats["total_elements"] - coverage_stats["documented_elements"]
            )
            if coverage_stats
            else 0,
            "documentation_percentage": coverage_stats["documentation_percentage"]
            if coverage_stats
            else 0.0,
            "public_api_coverage": {
                "functions": {
                    "total": coverage_stats["public_functions"]
                    if coverage_stats
                    else 0,
                    "documented": coverage_stats["documented_public_functions"]
                    if coverage_stats
                    else 0,
                    "percentage": public_function_coverage,
                },
                "classes": {
                    "total": coverage_stats["public_classes"] if coverage_stats else 0,
                    "documented": coverage_stats["documented_public_classes"]
                    if coverage_stats
                    else 0,
                    "percentage": public_class_coverage,
                },
            },
            "private_coverage": {
                "total": coverage_stats["private_elements"] if coverage_stats else 0,
                "documented": coverage_stats["documented_private_elements"]
                if coverage_stats
                else 0,
                "percentage": round(
                    (
                        coverage_stats["documented_private_elements"]
                        / coverage_stats["private_elements"]
                        * 100
                    ),
                    2,
                )
                if coverage_stats and coverage_stats["private_elements"] > 0
                else 0.0,
            },
        },
        "undocumented_public_apis": [
            {
                "file_path": row["file_path"],
                "element_type": row["element_type"],
                "element_name": row["element_name"],
                "visibility": row["visibility_type"],
                "language": row["language"],
                "signature": row["signature"],
                "location": {
                    "line_start": row["line_start"],
                    "line_end": row["line_end"],
                }
                if row["line_start"] and row["line_end"]
                else None,
            }
            for row in undocumented
            if row["visibility_type"]
            in ["public_function", "public_class", "public_other"]
        ],
        "coverage_by_file": [
            {
                "file_path": row["file_path"],
                "language": row["language"],
                "total_elements": row["total_elements"],
                "documented_elements": row["documented_elements"],
                "coverage_percentage": float(row["coverage_percentage"]),
            }
            for row in file_coverage
        ],
        "coverage_by_type": [
            {
                "element_type": row["element_type"],
                "total_elements": row["total_elements"],
                "documented_elements": row["documented_elements"],
                "coverage_percentage": float(row["coverage_percentage"]),
            }
            for row in type_coverage
        ],
        "well_documented_examples": [
            {
                "file_path": row["file_path"],
                "element_type": row["element_type"],
                "element_name": row["element_name"],
                "docstring_length": row["docstring_length"],
            }
            for row in well_documented
        ],
        "recommendations": _generate_documentation_recommendations(
            coverage_stats, undocumented, file_coverage
        ),
        "filters": {
            "file_path": file_path,
            "element_type": element_type,
            "language": language,
            "include_private": include_private,
        },
    }

    return result


def _generate_documentation_recommendations(
    coverage_stats, undocumented, file_coverage
) -> List[str]:
    """Generate actionable documentation recommendations based on analysis."""
    recommendations = []

    if not coverage_stats:
        return ["No code elements found to analyze."]

    total_coverage = coverage_stats.get("documentation_percentage", 0)

    # Overall coverage recommendations
    if total_coverage < 30:
        recommendations.append(
            "📚 Documentation coverage is critically low. Prioritize documenting public APIs."
        )
    elif total_coverage < 60:
        recommendations.append(
            "📖 Documentation coverage needs improvement. Focus on public functions and classes."
        )
    elif total_coverage < 80:
        recommendations.append(
            "✨ Good documentation coverage! Consider documenting remaining public APIs."
        )
    else:
        recommendations.append(
            "🎉 Excellent documentation coverage! Consider adding usage examples."
        )

    # Public API specific recommendations
    public_functions = coverage_stats.get("public_functions", 0)
    documented_public_functions = coverage_stats.get("documented_public_functions", 0)

    if public_functions > 0:
        public_func_coverage = (documented_public_functions / public_functions) * 100
        if public_func_coverage < 50:
            recommendations.append(
                "🔧 Less than half of public functions are documented. These are your API entry points!"
            )

    # File-specific recommendations
    if file_coverage:
        poorly_documented_files = [
            f for f in file_coverage if f["coverage_percentage"] < 20
        ]
        if poorly_documented_files:
            file_names = [
                f["file_path"].split("/")[-1] for f in poorly_documented_files[:3]
            ]
            recommendations.append(
                f"📁 Focus on these poorly documented files: {', '.join(file_names)}"
            )

    # Undocumented API recommendations
    undoc_classes = [u for u in undocumented if u["visibility_type"] == "public_class"]
    undoc_functions = [
        u for u in undocumented if u["visibility_type"] == "public_function"
    ]

    if undoc_classes:
        recommendations.append(
            f"🏗️ {len(undoc_classes)} public classes need documentation."
        )

    if undoc_functions:
        recommendations.append(
            f"⚙️ {len(undoc_functions)} public functions need documentation."
        )

    # Best practices
    if total_coverage > 60:
        recommendations.extend(
            [
                "💡 Consider using docstring linting tools (e.g., pydocstyle, eslint-plugin-jsdoc)",
                "📋 Add parameter descriptions and return value documentation",
                "🧪 Include usage examples in complex function documentation",
            ]
        )

    return recommendations[:8]  # Limit to top 8 recommendations


async def _generate_call_graph_insights(
    call_graph, function_lookup, complexity_threshold
):
    """Generate analytical insights about call patterns and potential issues."""
    insights = call_graph["insights"]

    # Detect circular dependencies in call graph
    circular_deps = []
    visited = set()
    rec_stack = set()

    def detect_cycles(func_id, path):
        if func_id in rec_stack:
            cycle_start = path.index(func_id)
            cycle = path[cycle_start:] + [func_id]
            return [cycle]

        if func_id in visited:
            return []

        visited.add(func_id)
        rec_stack.add(func_id)

        cycles = []
        node = function_lookup.get(func_id, {})
        for call_info in node.get("calls_out", []):
            called_func = call_info["function"]
            cycles.extend(detect_cycles(called_func, path + [func_id]))

        rec_stack.remove(func_id)
        return cycles

    for func_id in function_lookup:
        if func_id not in visited:
            cycles = detect_cycles(func_id, [])
            circular_deps.extend(cycles)

    insights["circular_dependencies"] = [
        {
            "cycle": cycle[:-1],  # Remove duplicate last element
            "length": len(cycle) - 1,
            "functions": [
                function_lookup.get(f, {}).get("name", f) for f in cycle[:-1]
            ],
        }
        for cycle in circular_deps[:10]  # Limit to first 10
    ]

    # Identify dead code candidates (functions that are never called)
    called_functions = set()
    for edge in call_graph["edges"]:
        called_functions.add(edge["to"])

    dead_code_candidates = []
    for func_id, node in function_lookup.items():
        if (
            func_id not in called_functions
            and not node["name"].startswith("_")
            and "main" not in node["name"].lower()  # Skip private functions
            and "test" not in node["name"].lower()  # Skip main functions
            and "__init__" not in node["name"]  # Skip test functions
        ):  # Skip constructors
            dead_code_candidates.append(
                {
                    "function": func_id,
                    "name": node["name"],
                    "file": node["file"],
                    "complexity": node.get("complexity", 0),
                    "lines": node.get("line_end", 0) - node.get("line_start", 0) + 1,
                }
            )

    insights["dead_code_candidates"] = sorted(
        dead_code_candidates, key=lambda x: x["complexity"], reverse=True
    )[:20]

    # Generate refactoring suggestions
    refactoring_suggestions = []

    # High complexity + high in_degree = refactoring candidate
    for func_id, node in function_lookup.items():
        if (
            node.get("complexity", 0) >= complexity_threshold
            and node.get("in_degree", 0) >= 5
        ):
            refactoring_suggestions.append(
                {
                    "type": "extract_method",
                    "function": func_id,
                    "name": node["name"],
                    "file": node["file"],
                    "reason": f"High complexity ({node['complexity']}) with many callers ({node['in_degree']})",
                    "priority": "high",
                }
            )

    # High out_degree = potential god function
    for func_id, node in function_lookup.items():
        if node.get("out_degree", 0) >= 15:
            refactoring_suggestions.append(
                {
                    "type": "split_function",
                    "function": func_id,
                    "name": node["name"],
                    "file": node["file"],
                    "reason": f"Calls too many functions ({node['out_degree']})",
                    "priority": "medium",
                }
            )

    # Functions with no incoming calls but high complexity
    for func_id, node in function_lookup.items():
        if (
            node.get("in_degree", 0) == 0
            and node.get("complexity", 0) >= complexity_threshold
            and not node["name"].startswith("_")
            and "main" not in node["name"].lower()
        ):
            refactoring_suggestions.append(
                {
                    "type": "review_necessity",
                    "function": func_id,
                    "name": node["name"],
                    "file": node["file"],
                    "reason": f"High complexity ({node['complexity']}) but never called",
                    "priority": "low",
                }
            )

    insights["refactoring_suggestions"] = refactoring_suggestions[:15]

    # Identify architectural patterns
    patterns = []

    # Identify potential factory pattern (functions that create many objects)
    for func_id, node in function_lookup.items():
        calls_out = node.get("calls_out", [])
        constructor_calls = sum(
            1 for call in calls_out if "__init__" in call.get("function", "").lower()
        )
        if constructor_calls >= 3:
            patterns.append(
                {
                    "pattern": "factory",
                    "function": func_id,
                    "name": node["name"],
                    "file": node["file"],
                    "evidence": f"Creates {constructor_calls} different object types",
                }
            )

    # Identify potential adapter pattern (high in_degree + high out_degree)
    for func_id, node in function_lookup.items():
        if (
            node.get("in_degree", 0) >= 3
            and node.get("out_degree", 0) >= 3
            and node.get("complexity", 0) < 10
        ):  # Low complexity suggests delegation
            patterns.append(
                {
                    "pattern": "adapter/proxy",
                    "function": func_id,
                    "name": node["name"],
                    "file": node["file"],
                    "evidence": f"High connectivity (in: {node['in_degree']}, out: {node['out_degree']}) with low complexity",
                }
            )

    # Identify potential observer pattern (many functions calling the same function)
    for func_id, node in function_lookup.items():
        if node.get("in_degree", 0) >= 8:
            patterns.append(
                {
                    "pattern": "observer/publisher",
                    "function": func_id,
                    "name": node["name"],
                    "file": node["file"],
                    "evidence": f"Called by {node['in_degree']} different functions",
                }
            )

    insights["architectural_patterns"] = patterns[:10]
