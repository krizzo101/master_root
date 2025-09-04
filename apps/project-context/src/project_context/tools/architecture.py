"""Architecture analysis tools for MCP server."""

import asyncio
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..db.connections import get_db


async def get_project_summary() -> Dict[str, Any]:
    """Get overall project statistics and summary.
    
    Returns:
        Dictionary containing project overview with:
        - file_count: Number of files in the project
        - language_breakdown: Files by programming language  
        - directory_structure: High-level directory overview
        - total_lines: Estimated lines of code
        - last_modified: Most recent modification timestamp
    """
    try:
        # For now, return a simple summary based on the .proj-intel directory
        proj_intel_path = Path.cwd() / ".proj-intel"
        
        summary = {
            "project_name": Path.cwd().name,
            "intel_directory": str(proj_intel_path),
            "intel_exists": proj_intel_path.exists(),
            "summary_generated": True,
            "timestamp": "now",
            "tool_count": 21,  # We have 21 semantic tools planned
            "status": "MCP Server running - basic monitoring active"
        }
        
        # Try to get basic database stats if available
        try:
            db = await get_db()
            # Simple query to get context item count
            count_query = "SELECT COUNT(*) as total FROM context_items"
            result = await db.fetch_one(count_query)
            if result:
                summary["context_items"] = result["total"]
        except Exception:
            summary["context_items"] = "Database not available"
            
        return summary
        
    except Exception as e:
        return {
            "error": f"Failed to generate project summary: {str(e)}",
            "project_name": Path.cwd().name,
            "status": "MCP Server running with errors"
        }


async def get_api_endpoints() -> List[Dict[str, Any]]:
    """List API routes by searching for FastAPI/Flask route decorators.

    Returns:
        List of dictionaries containing endpoint information with:
        - path: The endpoint path
        - methods: HTTP methods (GET, POST, etc.)
        - file: Source file containing the endpoint
        - line: Line number in source file
        - function: Function name handling the endpoint
    """
    endpoints = []

    # Get database connection
    db = await get_db()

    # Search for route decorators in code_elements table
    route_patterns = [
        r'@app\.(?:get|post|put|delete|patch|head|options|trace)\s*\(\s*["\']([^"\']+)["\']',
        r'@router\.(?:get|post|put|delete|patch|head|options|trace)\s*\(\s*["\']([^"\']+)["\']',
        r'@app\.route\s*\(\s*["\']([^"\']+)["\'](?:.*methods\s*=\s*\[([^\]]+)\])?',
        r'@.*\.route\s*\(\s*["\']([^"\']+)["\'](?:.*methods\s*=\s*\[([^\]]+)\])?',
    ]

    # Search unified context for API route patterns
    search_params = {
        "source_types": ["code"],
        "entity_types": ["function", "method"],
        "limit": 1000,
    }

    # Get all code elements that might contain route decorators
    context_items = await db.search_context_items(**search_params)

    # Process each route pattern
    for pattern in route_patterns:
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)

            for item in context_items:
                content = item.get("content", "")
                if not content:
                    continue

                matches = compiled_pattern.finditer(content)
                for match in matches:
                    file_path = item.get("file_path", "")
                    function_name = item.get("function_name") or item.get("title", "")
                    line_start = item.get("line_start")

                    endpoint_path = match.group(1)

                    # Extract HTTP methods from the matched pattern
                    methods = []
                    match_str = match.group(0).lower()

                    if "get(" in match_str:
                        methods = ["GET"]
                    elif "post(" in match_str:
                        methods = ["POST"]
                    elif "put(" in match_str:
                        methods = ["PUT"]
                    elif "delete(" in match_str:
                        methods = ["DELETE"]
                    elif "patch(" in match_str:
                        methods = ["PATCH"]
                    elif "head(" in match_str:
                        methods = ["HEAD"]
                    elif "options(" in match_str:
                        methods = ["OPTIONS"]
                    elif "trace(" in match_str:
                        methods = ["TRACE"]
                    elif len(match.groups()) > 1 and match.group(2):
                        # Parse methods from Flask route decorator
                        methods_str = match.group(2)
                        methods = [
                            m.strip().strip("'\"") for m in methods_str.split(",")
                        ]
                    else:
                        methods = ["GET"]  # Default for Flask routes

                    endpoint_info = {
                        "path": endpoint_path,
                        "methods": methods,
                        "file": file_path,
                        "line": line_start,
                        "function": function_name,
                    }

                    # Avoid duplicates
                    if endpoint_info not in endpoints:
                        endpoints.append(endpoint_info)

        except Exception as e:
            print(f"Error querying pattern {pattern}: {e}")
            continue

    # Also search Neo4j for code relationships if available
    try:
        cypher_query = """
        MATCH (f:Function)-[:DECORATED_WITH]->(d:Decorator)
        WHERE d.name CONTAINS 'route' OR d.name CONTAINS 'get' OR d.name CONTAINS 'post'
        RETURN f.name as function_name, f.file_path as file_path,
               f.line_start as line_start, d.name as decorator_name,
               d.arguments as decorator_args
        ORDER BY file_path, line_start
        """

        neo4j_results = await db.run_cypher(cypher_query)

        for record in neo4j_results:
            # Extract endpoint path from decorator arguments
            decorator_args = record.get("decorator_args", "")
            path_match = re.search(r'["\']([^"\']+)["\']', decorator_args)

            if path_match:
                endpoint_path = path_match.group(1)
                decorator_name = record["decorator_name"]

                # Determine HTTP method from decorator name
                methods = []
                if "get" in decorator_name.lower():
                    methods = ["GET"]
                elif "post" in decorator_name.lower():
                    methods = ["POST"]
                elif "put" in decorator_name.lower():
                    methods = ["PUT"]
                elif "delete" in decorator_name.lower():
                    methods = ["DELETE"]
                elif "patch" in decorator_name.lower():
                    methods = ["PATCH"]
                else:
                    methods = ["GET"]  # Default

                endpoint_info = {
                    "path": endpoint_path,
                    "methods": methods,
                    "file": record["file_path"],
                    "line": record["line_start"],
                    "function": record["function_name"],
                }

                # Avoid duplicates
                if endpoint_info not in endpoints:
                    endpoints.append(endpoint_info)

    except Exception as e:
        print(f"Error querying Neo4j for endpoints: {e}")
        # Continue without Neo4j results
        pass

    # Sort results by file path and line number
    endpoints.sort(key=lambda x: (x["file"], x["line"]))

    return endpoints


async def get_dependencies() -> Dict[str, Any]:
    """Get project dependency graph by querying Neo4j for DEPENDS_ON relationships
    and combining with code_elements imports data.

    Returns:
        Dictionary containing dependency tree structure with:
        - nodes: List of nodes (modules/files) in the dependency graph
        - edges: List of dependency relationships
        - import_tree: Hierarchical structure of dependencies
        - circular_dependencies: List of detected circular dependency chains
        - summary: Statistics about the dependency graph
    """
    db = await get_db()

    # Initialize result structure
    result = {
        "nodes": [],
        "edges": [],
        "import_tree": {},
        "circular_dependencies": [],
        "summary": {
            "total_nodes": 0,
            "total_edges": 0,
            "circular_count": 0,
            "orphaned_files": 0,
        },
    }

    try:
        # Query Neo4j for DEPENDS_ON relationships
        cypher_query = """
        MATCH (source)-[:DEPENDS_ON]->(target)
        RETURN source.name as source_name,
               source.file_path as source_file,
               source.type as source_type,
               target.name as target_name,
               target.file_path as target_file,
               target.type as target_type,
               'DEPENDS_ON' as relationship_type
        ORDER BY source_file, target_file
        """

        neo4j_dependencies = await db.run_cypher(cypher_query)

        # Process Neo4j dependencies
        nodes_set = set()
        edges_list = []

        for record in neo4j_dependencies:
            source_file = record["source_file"]
            target_file = record["target_file"]
            source_name = record["source_name"]
            target_name = record["target_name"]

            # Add nodes
            nodes_set.add((source_file, source_name, record["source_type"]))
            nodes_set.add((target_file, target_name, record["target_type"]))

            # Add edge
            edge = {
                "source": source_file,
                "target": target_file,
                "source_name": source_name,
                "target_name": target_name,
                "relationship_type": "DEPENDS_ON",
                "source_in_neo4j": True,
            }
            edges_list.append(edge)

    except Exception as e:
        print(f"Error querying Neo4j for dependencies: {e}")
        neo4j_dependencies = []
        nodes_set = set()
        edges_list = []

    # Query PostgreSQL code_elements for import data
    try:
        import_query = """
        SELECT
            file_path,
            element_name,
            content,
            element_type,
            line_start,
            language
        FROM code_elements
        WHERE element_type IN ('import', 'module')
           OR content ~ 'import\\s+\\w+'
           OR content ~ 'from\\s+\\w+\\s+import'
           OR content ~ '#include\\s*<'
           OR content ~ 'require\\s*\\('
        ORDER BY file_path, line_start
        """

        import_results = await db.fetch_many(import_query)

        # Process import statements
        import_patterns = {
            "python": [
                r"import\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
                r"from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import",
            ],
            "javascript": [
                r'import.*from\s+[\'"]([^\'\"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'\"]+)[\'"]\s*\)',
            ],
            "java": [
                r"import\s+([a-zA-Z_][a-zA-Z0-9_.]*);",
            ],
            "cpp": [
                r"#include\s*<([^>]+)>",
                r'#include\s*"([^"]+)"',
            ],
        }

        for row in import_results:
            file_path = row["file_path"]
            content = row["content"]
            language = row["language"] or "python"  # Default to python

            # Add file as a node if not already present
            nodes_set.add((file_path, file_path, "file"))

            # Extract imports based on language
            patterns = import_patterns.get(language.lower(), import_patterns["python"])

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)

                for match in matches:
                    imported_module = match.group(1)

                    # Skip relative imports and standard library
                    if imported_module.startswith(".") or imported_module in [
                        "os",
                        "sys",
                        "json",
                        "datetime",
                        "re",
                    ]:
                        continue

                    # Add dependency edge
                    edge = {
                        "source": file_path,
                        "target": imported_module,
                        "source_name": file_path,
                        "target_name": imported_module,
                        "relationship_type": "IMPORTS",
                        "source_in_neo4j": False,
                        "line": row["line_start"],
                    }
                    edges_list.append(edge)

                    # Add imported module as node
                    nodes_set.add((imported_module, imported_module, "module"))

    except Exception as e:
        print(f"Error querying PostgreSQL for imports: {e}")

    # Convert nodes set to list
    result["nodes"] = [
        {"id": node[0], "name": node[1], "type": node[2]} for node in nodes_set
    ]

    result["edges"] = edges_list

    # Build import tree (hierarchical structure)
    import_tree = {}
    file_dependencies = {}

    for edge in edges_list:
        source = edge["source"]
        target = edge["target"]

        if source not in file_dependencies:
            file_dependencies[source] = []
        file_dependencies[source].append(target)

        # Build tree structure
        if source not in import_tree:
            import_tree[source] = {"dependencies": [], "dependents": []}
        if target not in import_tree:
            import_tree[target] = {"dependencies": [], "dependents": []}

        import_tree[source]["dependencies"].append(target)
        import_tree[target]["dependents"].append(source)

    result["import_tree"] = import_tree

    # Detect circular dependencies using DFS
    def detect_cycles(graph, start, visited, rec_stack, path):
        visited.add(start)
        rec_stack.add(start)
        path.append(start)

        cycles = []

        if start in graph:
            for neighbor in graph[start]:
                if neighbor not in visited:
                    cycles.extend(
                        detect_cycles(graph, neighbor, visited, rec_stack, path)
                    )
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start_idx = path.index(neighbor)
                    cycle = path[cycle_start_idx:] + [neighbor]
                    cycles.append(cycle)

        path.pop()
        rec_stack.remove(start)
        return cycles

    # Find circular dependencies
    visited = set()
    all_cycles = []

    for node in file_dependencies:
        if node not in visited:
            cycles = detect_cycles(file_dependencies, node, visited, set(), [])
            all_cycles.extend(cycles)

    # Remove duplicate cycles
    unique_cycles = []
    for cycle in all_cycles:
        if cycle not in unique_cycles:
            unique_cycles.append(cycle)

    result["circular_dependencies"] = unique_cycles

    # Calculate summary statistics
    result["summary"] = {
        "total_nodes": len(result["nodes"]),
        "total_edges": len(result["edges"]),
        "circular_count": len(unique_cycles),
        "orphaned_files": len(
            [
                node
                for node in result["nodes"]
                if node["id"] not in import_tree
                or (
                    not import_tree[node["id"]]["dependencies"]
                    and not import_tree[node["id"]]["dependents"]
                )
            ]
        ),
    }

    return result


async def get_entry_points() -> List[Dict[str, Any]]:
    """Find CLI and main entries by searching for main functions, __main__ blocks, and CLI command definitions.

    Returns:
        List of dictionaries containing entry point information with:
        - type: Entry point type ('main_function', 'main_block', 'cli_command', 'script')
        - file: Source file containing the entry point
        - line: Line number in source file
        - name: Name of the entry point (function name, command name, etc.)
        - description: Brief description if available
        - framework: CLI framework used (click, argparse, etc.)
    """
    entry_points = []

    # Get database connection
    db = await get_db()

    try:
        # 1. Search for main functions
        main_function_query = """
        SELECT file_path, content, line_start, line_end, element_name
        FROM code_elements
        WHERE element_type = 'function'
        AND (element_name = 'main' OR element_name LIKE '%main%')
        ORDER BY file_path, line_start
        """

        main_functions = await db.fetch_many(main_function_query)

        for row in main_functions:
            entry_points.append(
                {
                    "type": "main_function",
                    "file": row["file_path"],
                    "line": row["line_start"],
                    "name": row["element_name"],
                    "description": f"Main function in {Path(row['file_path']).name}",
                    "framework": "standard",
                }
            )

        # 2. Search for __main__ blocks
        main_block_query = """
        SELECT file_path, content, line_start, line_end
        FROM code_elements
        WHERE content ~ '__main__'
        AND (element_type = 'module' OR element_type = 'block')
        ORDER BY file_path, line_start
        """

        main_blocks = await db.fetch_many(main_block_query)

        for row in main_blocks:
            # Extract the actual if __main__ statement
            content = row["content"]
            if "__main__" in content:
                entry_points.append(
                    {
                        "type": "main_block",
                        "file": row["file_path"],
                        "line": row["line_start"],
                        "name": f"if __name__ == '__main__'",
                        "description": f"Main execution block in {Path(row['file_path']).name}",
                        "framework": "standard",
                    }
                )

        # 3. Search for Click CLI commands
        click_patterns = [
            r"@click\.command\s*\(",
            r"@click\.group\s*\(",
            r"@.*\.command\s*\(",
            r"@.*\.group\s*\(",
        ]

        for pattern in click_patterns:
            click_query = """
            SELECT file_path, content, line_start, line_end, element_name
            FROM code_elements
            WHERE content ~ %s
            AND element_type IN ('function', 'method')
            ORDER BY file_path, line_start
            """

            click_results = await db.fetch_many(click_query, pattern)

            for row in click_results:
                content = row["content"]

                # Extract command name from decorator or function name
                command_name = row["element_name"]

                # Try to extract name from decorator
                name_match = re.search(
                    r'@(?:.*\.)?(?:command|group)\s*\(\s*["\']?([^"\')\s]+)', content
                )
                if name_match:
                    command_name = name_match.group(1)

                entry_points.append(
                    {
                        "type": "cli_command",
                        "file": row["file_path"],
                        "line": row["line_start"],
                        "name": command_name,
                        "description": f"Click command: {command_name}",
                        "framework": "click",
                    }
                )

        # 4. Search for argparse CLI definitions
        argparse_patterns = [
            r"ArgumentParser\s*\(",
            r"argparse\.ArgumentParser",
            r"add_parser\s*\(",
        ]

        for pattern in argparse_patterns:
            argparse_query = """
            SELECT file_path, content, line_start, line_end, element_name
            FROM code_elements
            WHERE content ~ %s
            AND element_type IN ('function', 'method', 'module')
            ORDER BY file_path, line_start
            """

            argparse_results = await db.fetch_many(argparse_query, pattern)

            for row in argparse_results:
                content = row["content"]

                # Try to extract program name or description
                prog_match = re.search(r'prog\s*=\s*["\']([^"\']+)["\']', content)
                desc_match = re.search(
                    r'description\s*=\s*["\']([^"\']+)["\']', content
                )

                name = (
                    prog_match.group(1) if prog_match else Path(row["file_path"]).stem
                )
                description = (
                    desc_match.group(1)
                    if desc_match
                    else f"Argparse CLI in {Path(row['file_path']).name}"
                )

                entry_points.append(
                    {
                        "type": "cli_command",
                        "file": row["file_path"],
                        "line": row["line_start"],
                        "name": name,
                        "description": description,
                        "framework": "argparse",
                    }
                )

        # 5. Search for executable scripts (shebang lines)
        shebang_query = """
        SELECT file_path, content, line_start
        FROM code_elements
        WHERE content ~ '^#!'
        AND element_type = 'module'
        ORDER BY file_path
        """

        script_results = await db.fetch_many(shebang_query)

        for row in script_results:
            content = row["content"]

            # Extract shebang line
            shebang_match = re.search(r"^#!(.+)", content, re.MULTILINE)
            if shebang_match:
                shebang = shebang_match.group(1).strip()

                entry_points.append(
                    {
                        "type": "script",
                        "file": row["file_path"],
                        "line": row["line_start"],
                        "name": Path(row["file_path"]).name,
                        "description": f"Executable script ({shebang})",
                        "framework": "script",
                    }
                )

    except Exception as e:
        print(f"Error querying PostgreSQL for entry points: {e}")
        # Continue to try Neo4j
        pass

    # 6. Also search Neo4j for entry points if available
    try:
        cypher_query = """
        MATCH (f:Function)
        WHERE f.name = 'main'
           OR f.name CONTAINS '__main__'
           OR EXISTS((f)-[:DECORATED_WITH]->(:Decorator {name: 'click.command'}))
           OR EXISTS((f)-[:DECORATED_WITH]->(:Decorator {name: 'click.group'}))
        RETURN f.name as function_name, f.file_path as file_path,
               f.line_start as line_start, f.docstring as description
        ORDER BY file_path, line_start
        """

        neo4j_results = await db.run_cypher(cypher_query)

        for record in neo4j_results:
            function_name = record["function_name"]
            file_path = record["file_path"]

            # Determine entry point type
            entry_type = "main_function"
            framework = "standard"

            if "__main__" in function_name:
                entry_type = "main_block"
            elif "click" in str(record.get("decorator_name", "")):
                entry_type = "cli_command"
                framework = "click"

            # Avoid duplicates by checking if this entry point already exists
            existing = any(
                ep["file"] == file_path
                and ep["name"] == function_name
                and ep["line"] == record["line_start"]
                for ep in entry_points
            )

            if not existing:
                entry_points.append(
                    {
                        "type": entry_type,
                        "file": file_path,
                        "line": record["line_start"],
                        "name": function_name,
                        "description": record.get(
                            "description", f"Entry point in {Path(file_path).name}"
                        ),
                        "framework": framework,
                    }
                )

    except Exception as e:
        print(f"Error querying Neo4j for entry points: {e}")
        # Continue without Neo4j results
        pass

    # 7. Look for setup.py entry points
    try:
        setup_query = """
        SELECT file_path, content, line_start
        FROM code_elements
        WHERE file_path LIKE '%setup.py'
        AND content ~ 'entry_points'
        ORDER BY file_path
        """

        setup_results = await db.fetch_many(setup_query)

        for row in setup_results:
            content = row["content"]

            # Extract entry points from setup.py
            entry_points_match = re.search(
                r"entry_points\s*=\s*\{([^}]+)\}", content, re.DOTALL
            )
            if entry_points_match:
                entry_points_text = entry_points_match.group(1)

                # Parse console_scripts
                console_scripts_match = re.search(
                    r'["\']console_scripts["\']\s*:\s*\[([^\]]+)\]', entry_points_text
                )
                if console_scripts_match:
                    scripts_text = console_scripts_match.group(1)

                    # Extract individual script definitions
                    script_matches = re.findall(
                        r'["\']([^=]+)=([^"\']+)["\']', scripts_text
                    )

                    for script_name, script_target in script_matches:
                        entry_points.append(
                            {
                                "type": "cli_command",
                                "file": row["file_path"],
                                "line": row["line_start"],
                                "name": script_name.strip(),
                                "description": f"Setup.py entry point: {script_target.strip()}",
                                "framework": "setuptools",
                            }
                        )

    except Exception as e:
        print(f"Error searching setup.py entry points: {e}")
        # Continue without setup.py results
        pass

    # Remove duplicates and sort results
    unique_entries = []
    seen = set()

    for entry in entry_points:
        key = (entry["file"], entry["name"], entry["line"])
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    # Sort by file path and line number
    unique_entries.sort(key=lambda x: (x["file"], x["line"]))

    return unique_entries


async def find_agents(
    agent_type: Optional[str] = None,
    session_id: Optional[str] = None,
    days_back: int = 7,
    include_performance: bool = True,
    limit: int = 100,
) -> Dict[str, Any]:
    """Discover agent architectures and usage patterns.

    Queries the agent_usage table to discover agent invocations,
    aggregates by agent_type and session, and includes performance metrics.

    Args:
        agent_type: Filter by specific agent type/class
        session_id: Filter by specific session ID
        days_back: How many days back to look for data
        include_performance: Include performance metrics in results
        limit: Maximum number of results to return

    Returns:
        Dictionary containing agent usage data, performance metrics, and Neo4j correlations
    """
    from datetime import datetime, timedelta

    db = await get_db()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Build PostgreSQL query for agent usage
    where_conditions = ["timestamp >= $1", "timestamp <= $2"]
    params = [start_date, end_date]
    param_count = 2

    if agent_type:
        param_count += 1
        where_conditions.append(f"agent_class = ${param_count}")
        params.append(agent_type)

    if session_id:
        param_count += 1
        where_conditions.append(f"session_id = ${param_count}")
        params.append(session_id)

    # Main query to get agent usage data
    agent_usage_query = f"""
        SELECT
            agent_class,
            agent_token,
            session_id,
            task_description,
            timestamp,
            execution_time_ms,
            tokens_used,
            success,
            file_paths,
            methods_invoked,
            context_data,
            neo4j_node_id
        FROM agent_usage
        WHERE {' AND '.join(where_conditions)}
        ORDER BY timestamp DESC
        LIMIT ${param_count + 1}
    """
    params.append(limit)

    agent_data = await db.fetch_many(agent_usage_query, *params)

    # Aggregate performance metrics by agent type
    aggregation_query = f"""
        SELECT
            agent_class,
            COUNT(*) as total_invocations,
            COUNT(DISTINCT session_id) as unique_sessions,
            AVG(execution_time_ms) as avg_execution_time,
            MAX(execution_time_ms) as max_execution_time,
            MIN(execution_time_ms) as min_execution_time,
            SUM(tokens_used) as total_tokens,
            AVG(tokens_used) as avg_tokens,
            COUNT(*) FILTER (WHERE success = true) as successful_invocations,
            COUNT(*) FILTER (WHERE success = false) as failed_invocations,
            ROUND(
                (COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*))::numeric,
                2
            ) as success_rate
        FROM agent_usage
        WHERE {' AND '.join(where_conditions[:-1])}  -- Remove limit condition
        GROUP BY agent_class
        ORDER BY total_invocations DESC
    """

    # Remove the limit param for aggregation query
    agg_params = params[:-1]
    performance_data = await db.fetch_many(aggregation_query, *agg_params)

    # Get session correlation data
    session_query = f"""
        SELECT DISTINCT
            au.session_id,
            cs.started_at,
            cs.ended_at,
            cs.project_path,
            cs.total_tokens as session_total_tokens,
            cs.model_used,
            COUNT(au.id) as agent_invocations_in_session
        FROM agent_usage au
        LEFT JOIN chat_sessions cs ON au.session_id = cs.id
        WHERE {' AND '.join(where_conditions[:-1])}  -- Remove limit condition
        GROUP BY au.session_id, cs.started_at, cs.ended_at, cs.project_path,
                 cs.total_tokens, cs.model_used
        ORDER BY cs.started_at DESC
    """

    session_data = await db.fetch_many(session_query, *agg_params)

    # Query Neo4j for additional relationship data if available
    neo4j_data = []
    if any(row.get("neo4j_node_id") for row in agent_data):
        # Get unique Neo4j node IDs from the agent data
        neo4j_node_ids = [
            row["neo4j_node_id"] for row in agent_data if row.get("neo4j_node_id")
        ]

        if neo4j_node_ids:
            # Query Neo4j for relationship data
            cypher_query = """
                MATCH (agent:Agent)
                WHERE agent.usage_id IN $node_ids
                OPTIONAL MATCH (agent)-[r1]->(related)
                OPTIONAL MATCH (agent)<-[r2]-(dependent)
                RETURN agent.usage_id as usage_id,
                       agent.agent_class as agent_class,
                       collect(DISTINCT {
                           type: type(r1),
                           target: labels(related)[0],
                           target_name: related.name
                       }) as outgoing_relationships,
                       collect(DISTINCT {
                           type: type(r2),
                           source: labels(dependent)[0],
                           source_name: dependent.name
                       }) as incoming_relationships
            """

            try:
                neo4j_results = await db.run_cypher(
                    cypher_query, node_ids=neo4j_node_ids
                )
                neo4j_data = neo4j_results
            except Exception as e:
                # Neo4j is optional, log but don't fail
                print(f"Warning: Neo4j query failed: {e}")

    # Structure the response
    result = {
        "query_info": {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days_back": days_back,
            },
            "filters": {"agent_type": agent_type, "session_id": session_id},
            "result_count": len(agent_data),
            "query_timestamp": datetime.now().isoformat(),
        },
        "agent_invocations": agent_data,
        "performance_summary": performance_data if include_performance else [],
        "session_correlation": session_data,
        "neo4j_relationships": neo4j_data,
        "summary": {
            "total_agents_found": len(set(row["agent_class"] for row in agent_data)),
            "total_sessions": len(set(row["session_id"] for row in agent_data)),
            "total_invocations": len(agent_data),
            "date_range_covered": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        },
    }

    return result


async def get_data_models() -> List[Dict[str, Any]]:
    """Find data structures by searching for Pydantic BaseModel, SQLAlchemy models, and dataclass definitions.

    Returns:
        List of dictionaries containing data model information with:
        - name: The model/class name
        - type: Type of data structure (pydantic, sqlalchemy, dataclass, typeddict)
        - file: Source file containing the model
        - line: Line number in source file
        - fields: List of field information
        - base_classes: Base classes the model inherits from
        - decorators: Applied decorators (for dataclasses)
    """
    models = []

    # Get database connection
    db = await get_db()

    try:
        # Search for Pydantic BaseModel classes
        pydantic_query = """
        SELECT file_path, element_name, content, line_start, line_end
        FROM code_elements
        WHERE element_type = 'class'
        AND (
            content ~ 'class\\s+\\w+\\s*\\([^)]*BaseModel[^)]*\\)'
            OR content ~ 'from\\s+pydantic\\s+import.*BaseModel'
            OR content ~ 'import\\s+pydantic'
        )
        ORDER BY file_path, line_start
        """

        pydantic_results = await db.fetch_many(pydantic_query)

        for row in pydantic_results:
            model_info = await _extract_pydantic_model_info(row)
            if model_info:
                models.append(model_info)

        # Search for SQLAlchemy models
        sqlalchemy_query = """
        SELECT file_path, element_name, content, line_start, line_end
        FROM code_elements
        WHERE element_type = 'class'
        AND (
            content ~ 'class\\s+\\w+\\s*\\([^)]*Base[^)]*\\)'
            OR content ~ 'from\\s+sqlalchemy\\s+'
            OR content ~ '__tablename__'
            OR content ~ 'Column\\('
            OR content ~ 'declarative_base'
        )
        ORDER BY file_path, line_start
        """

        sqlalchemy_results = await db.fetch_many(sqlalchemy_query)

        for row in sqlalchemy_results:
            model_info = await _extract_sqlalchemy_model_info(row)
            if model_info:
                models.append(model_info)

        # Search for dataclasses
        dataclass_query = """
        SELECT file_path, element_name, content, line_start, line_end
        FROM code_elements
        WHERE element_type = 'class'
        AND (
            content ~ '@dataclass'
            OR content ~ 'from\\s+dataclasses\\s+import.*dataclass'
            OR content ~ 'import\\s+dataclasses'
        )
        ORDER BY file_path, line_start
        """

        dataclass_results = await db.fetch_many(dataclass_query)

        for row in dataclass_results:
            model_info = await _extract_dataclass_info(row)
            if model_info:
                models.append(model_info)

        # Search for TypedDict definitions
        typeddict_query = """
        SELECT file_path, element_name, content, line_start, line_end
        FROM code_elements
        WHERE element_type = 'class'
        AND (
            content ~ 'class\\s+\\w+\\s*\\([^)]*TypedDict[^)]*\\)'
            OR content ~ 'from\\s+typing\\s+import.*TypedDict'
            OR content ~ 'from\\s+typing_extensions\\s+import.*TypedDict'
        )
        ORDER BY file_path, line_start
        """

        typeddict_results = await db.fetch_many(typeddict_query)

        for row in typeddict_results:
            model_info = await _extract_typeddict_info(row)
            if model_info:
                models.append(model_info)

        # Query Neo4j for additional model relationships if available
        try:
            cypher_query = """
            MATCH (c:Class)-[:INHERITS_FROM]->(base:Class)
            WHERE base.name IN ['BaseModel', 'Base', 'DeclarativeBase']
            OR c.decorators CONTAINS 'dataclass'
            RETURN c.name as class_name, c.file_path as file_path,
                   c.line_start as line_start, base.name as base_class,
                   c.fields as class_fields, c.decorators as decorators
            ORDER BY file_path, line_start
            """

            neo4j_results = await db.run_cypher(cypher_query)

            for record in neo4j_results:
                # Create model info from Neo4j data
                model_type = _determine_model_type_from_base(
                    record.get("base_class", "")
                )
                decorators = record.get("decorators", [])
                if "dataclass" in decorators:
                    model_type = "dataclass"

                model_info = {
                    "name": record["class_name"],
                    "type": model_type,
                    "file": record["file_path"],
                    "line": record["line_start"],
                    "fields": _parse_neo4j_fields(record.get("class_fields", [])),
                    "base_classes": [record.get("base_class")]
                    if record.get("base_class")
                    else [],
                    "decorators": decorators,
                }

                # Avoid duplicates
                existing = next(
                    (
                        m
                        for m in models
                        if m["name"] == model_info["name"]
                        and m["file"] == model_info["file"]
                    ),
                    None,
                )
                if not existing:
                    models.append(model_info)

        except Exception as e:
            print(f"Error querying Neo4j for data models: {e}")
            # Continue without Neo4j results
            pass

        # Remove duplicates and sort results
        unique_models = _remove_duplicate_models(models)
        unique_models.sort(key=lambda x: (x["file"], x["line"]))

        return unique_models

    except Exception as e:
        print(f"Error searching for data models: {e}")
        return [{"error": f"Failed to search for data models: {str(e)}"}]


async def _extract_pydantic_model_info(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract information from a Pydantic BaseModel class definition."""
    try:
        content = row["content"]

        # Check if this is actually a Pydantic model
        if "BaseModel" not in content:
            return None

        # Extract class definition line
        class_match = re.search(r"class\s+(\w+)\s*\([^)]*BaseModel[^)]*\)", content)
        if not class_match:
            return None

        class_name = class_match.group(1)

        # Extract base classes
        base_classes = _extract_base_classes(content, class_name)

        # Extract fields using regex patterns
        fields = _extract_pydantic_fields(content)

        return {
            "name": class_name,
            "type": "pydantic",
            "file": row["file_path"],
            "line": row["line_start"],
            "fields": fields,
            "base_classes": base_classes,
            "decorators": [],
        }

    except Exception as e:
        print(f"Error extracting Pydantic model info: {e}")
        return None


async def _extract_sqlalchemy_model_info(
    row: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Extract information from a SQLAlchemy model class definition."""
    try:
        content = row["content"]

        # Check if this looks like a SQLAlchemy model
        if not any(
            marker in content for marker in ["__tablename__", "Column(", "Base"]
        ):
            return None

        # Extract class name
        class_match = re.search(r"class\s+(\w+)\s*\([^)]*\)", content)
        if not class_match:
            return None

        class_name = class_match.group(1)

        # Extract base classes
        base_classes = _extract_base_classes(content, class_name)

        # Extract table name if present
        table_match = re.search(r'__tablename__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        table_name = table_match.group(1) if table_match else None

        # Extract SQLAlchemy columns
        fields = _extract_sqlalchemy_fields(content)
        if table_name:
            fields.insert(
                0,
                {
                    "name": "__tablename__",
                    "type": "str",
                    "description": f"Table name: {table_name}",
                    "required": True,
                },
            )

        return {
            "name": class_name,
            "type": "sqlalchemy",
            "file": row["file_path"],
            "line": row["line_start"],
            "fields": fields,
            "base_classes": base_classes,
            "decorators": [],
        }

    except Exception as e:
        print(f"Error extracting SQLAlchemy model info: {e}")
        return None


async def _extract_dataclass_info(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract information from a dataclass definition."""
    try:
        content = row["content"]

        # Check if this has @dataclass decorator
        if "@dataclass" not in content:
            return None

        # Extract class name
        class_match = re.search(r"class\s+(\w+)\s*(?:\([^)]*\))?:", content)
        if not class_match:
            return None

        class_name = class_match.group(1)

        # Extract base classes
        base_classes = _extract_base_classes(content, class_name)

        # Extract dataclass fields
        fields = _extract_dataclass_fields(content)

        # Extract decorators
        decorators = _extract_decorators(content)

        return {
            "name": class_name,
            "type": "dataclass",
            "file": row["file_path"],
            "line": row["line_start"],
            "fields": fields,
            "base_classes": base_classes,
            "decorators": decorators,
        }

    except Exception as e:
        print(f"Error extracting dataclass info: {e}")
        return None


async def _extract_typeddict_info(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract information from a TypedDict definition."""
    try:
        content = row["content"]

        # Check if this is a TypedDict
        if "TypedDict" not in content:
            return None

        # Extract class name
        class_match = re.search(r"class\s+(\w+)\s*\([^)]*TypedDict[^)]*\)", content)
        if not class_match:
            return None

        class_name = class_match.group(1)

        # Extract fields from TypedDict
        fields = _extract_typeddict_fields(content)

        return {
            "name": class_name,
            "type": "typeddict",
            "file": row["file_path"],
            "line": row["line_start"],
            "fields": fields,
            "base_classes": ["TypedDict"],
            "decorators": [],
        }

    except Exception as e:
        print(f"Error extracting TypedDict info: {e}")
        return None


def _extract_base_classes(content: str, class_name: str) -> List[str]:
    """Extract base classes from a class definition."""
    try:
        pattern = rf"class\s+{re.escape(class_name)}\s*\(([^)]+)\)"
        match = re.search(pattern, content)

        if match:
            bases_str = match.group(1)
            # Split by comma and clean up
            bases = [base.strip() for base in bases_str.split(",")]
            # Filter out empty strings and remove generic brackets
            bases = [
                re.sub(r"\[.*\]", "", base).strip() for base in bases if base.strip()
            ]
            return bases

        return []
    except Exception:
        return []


def _extract_pydantic_fields(content: str) -> List[Dict[str, Any]]:
    """Extract field definitions from Pydantic model content."""
    fields = []

    try:
        # Look for field definitions: field_name: Type = Field(...)
        field_patterns = [
            r"(\w+)\s*:\s*([^=\n]+?)(?:\s*=\s*Field\(([^)]*)\))?",
            r"(\w+)\s*:\s*([^=\n]+?)(?:\s*=\s*([^=\n]+?))?$",
        ]

        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if (
                not line
                or line.startswith("#")
                or line.startswith('"""')
                or line.startswith("'''")
            ):
                continue

            for pattern in field_patterns:
                match = re.match(pattern, line)
                if match:
                    field_name = match.group(1)
                    field_type = match.group(2).strip()
                    default_value = match.group(3) if len(match.groups()) > 2 else None

                    # Skip class methods and special attributes
                    if field_name.startswith("_") or "def " in line or "class " in line:
                        continue

                    field_info = {
                        "name": field_name,
                        "type": field_type,
                        "required": default_value is None
                        or "Field()" in str(default_value),
                        "description": _extract_field_description(
                            str(default_value) if default_value else ""
                        ),
                    }

                    if default_value:
                        field_info["default"] = default_value

                    fields.append(field_info)
                    break

        return fields
    except Exception as e:
        print(f"Error extracting Pydantic fields: {e}")
        return []


def _extract_sqlalchemy_fields(content: str) -> List[Dict[str, Any]]:
    """Extract column definitions from SQLAlchemy model content."""
    fields = []

    try:
        # Look for Column definitions
        column_pattern = r"(\w+)\s*=\s*Column\(([^)]+)\)"

        matches = re.finditer(column_pattern, content, re.MULTILINE)
        for match in matches:
            field_name = match.group(1)
            column_def = match.group(2)

            # Parse column type
            type_match = re.search(
                r"(Integer|String|Text|Boolean|DateTime|Float|Numeric)\(?([^,)]*)\)?",
                column_def,
            )
            field_type = type_match.group(1) if type_match else "Unknown"

            # Check for primary key, nullable, etc.
            required = (
                "nullable=False" in column_def or "primary_key=True" in column_def
            )
            is_primary = "primary_key=True" in column_def

            field_info = {
                "name": field_name,
                "type": field_type,
                "required": required,
                "description": f"SQLAlchemy column{' (Primary Key)' if is_primary else ''}",
            }

            fields.append(field_info)

        return fields
    except Exception as e:
        print(f"Error extracting SQLAlchemy fields: {e}")
        return []


def _extract_dataclass_fields(content: str) -> List[Dict[str, Any]]:
    """Extract field definitions from dataclass content."""
    fields = []

    try:
        # Look for field annotations: field_name: Type = default_value
        field_pattern = r"(\w+)\s*:\s*([^=\n]+?)(?:\s*=\s*([^=\n]+?))?$"

        lines = content.split("\n")
        in_class = False

        for line in lines:
            stripped_line = line.strip()

            # Track if we're inside the class definition
            if stripped_line.startswith("class ") and ":" in stripped_line:
                in_class = True
                continue
            elif stripped_line.startswith("class "):
                in_class = False
                continue
            elif stripped_line.startswith("def ") and in_class:
                break  # Stop at first method definition

            if not in_class or not stripped_line:
                continue

            match = re.match(field_pattern, stripped_line)
            if match:
                field_name = match.group(1)
                field_type = match.group(2).strip()
                default_value = match.group(3) if len(match.groups()) > 2 else None

                # Skip methods and special attributes
                if field_name.startswith("_") or "def " in line:
                    continue

                field_info = {
                    "name": field_name,
                    "type": field_type,
                    "required": default_value is None,
                    "description": "Dataclass field",
                }

                if default_value:
                    field_info["default"] = default_value

                fields.append(field_info)

        return fields
    except Exception as e:
        print(f"Error extracting dataclass fields: {e}")
        return []


def _extract_typeddict_fields(content: str) -> List[Dict[str, Any]]:
    """Extract field definitions from TypedDict content."""
    fields = []

    try:
        # Look for field annotations in TypedDict
        field_pattern = r"(\w+)\s*:\s*([^=\n]+?)$"

        lines = content.split("\n")
        in_class = False

        for line in lines:
            stripped_line = line.strip()

            # Track if we're inside the class definition
            if stripped_line.startswith("class ") and "TypedDict" in stripped_line:
                in_class = True
                continue
            elif stripped_line.startswith("class "):
                in_class = False
                continue

            if not in_class or not stripped_line:
                continue

            match = re.match(field_pattern, stripped_line)
            if match:
                field_name = match.group(1)
                field_type = match.group(2).strip()

                field_info = {
                    "name": field_name,
                    "type": field_type,
                    "required": True,  # TypedDict fields are required by default
                    "description": "TypedDict field",
                }

                fields.append(field_info)

        return fields
    except Exception as e:
        print(f"Error extracting TypedDict fields: {e}")
        return []


def _extract_decorators(content: str) -> List[str]:
    """Extract decorator names from content."""
    decorators = []

    try:
        decorator_pattern = r"@(\w+)(?:\([^)]*\))?"
        matches = re.findall(decorator_pattern, content)
        decorators = list(set(matches))  # Remove duplicates

        return decorators
    except Exception:
        return []


def _extract_field_description(field_def: str) -> str:
    """Extract description from field definition."""
    try:
        # Look for description in Field() call
        desc_match = re.search(r'description\s*=\s*[\'"]([^\'"]+)[\'"]', field_def)
        if desc_match:
            return desc_match.group(1)

        return "Model field"
    except Exception:
        return "Model field"


def _determine_model_type_from_base(base_class: str) -> str:
    """Determine model type from base class name."""
    if "BaseModel" in base_class:
        return "pydantic"
    elif "Base" in base_class or "DeclarativeBase" in base_class:
        return "sqlalchemy"
    elif "TypedDict" in base_class:
        return "typeddict"
    else:
        return "unknown"


def _parse_neo4j_fields(fields_data: List[Any]) -> List[Dict[str, Any]]:
    """Parse field information from Neo4j data."""
    try:
        if not fields_data or not isinstance(fields_data, list):
            return []

        parsed_fields = []
        for field in fields_data:
            if isinstance(field, dict):
                parsed_fields.append(
                    {
                        "name": field.get("name", "unknown"),
                        "type": field.get("type", "unknown"),
                        "required": field.get("required", False),
                        "description": field.get(
                            "description", "Field from graph data"
                        ),
                    }
                )

        return parsed_fields
    except Exception:
        return []


def _remove_duplicate_models(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate models based on name and file path."""
    seen = set()
    unique_models = []

    for model in models:
        key = (model["name"], model["file"])
        if key not in seen:
            seen.add(key)
            unique_models.append(model)

    return unique_models
