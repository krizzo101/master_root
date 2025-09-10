#!/usr/bin/env python3
"""
Analyze available metrics in the chat logs database
to determine what reports would be most valuable
"""

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


def analyze_data_structure():
    """Analyze the structure and relationships in the data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    analyses = {}

    # 1. Session patterns
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT session_id) as total_sessions,
            AVG(node_count) as avg_nodes_per_session,
            MAX(node_count) as max_nodes,
            MIN(node_count) as min_nodes,
            AVG(duration_minutes) as avg_duration
        FROM (
            SELECT
                session_id,
                COUNT(*) as node_count,
                CAST((julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 24 * 60 AS INTEGER) as duration_minutes
            FROM nodes
            GROUP BY session_id
        )
    """
    )
    analyses["session_patterns"] = cursor.fetchone()

    # 2. Tool usage patterns
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT tool_name) as unique_tools,
            COUNT(*) as total_calls,
            AVG(calls_per_session) as avg_calls_per_session
        FROM (
            SELECT
                n.session_id,
                COUNT(*) as calls_per_session
            FROM tool_calls tc
            JOIN nodes n ON tc.node_uuid = n.uuid
            GROUP BY n.session_id
        )
    """
    )
    analyses["tool_patterns"] = cursor.fetchone()

    # 3. File operation patterns
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT file_path) as unique_files,
            COUNT(*) as total_operations,
            COUNT(DISTINCT SUBSTR(file_path, 1, INSTR(file_path || '/', '/') - 1)) as unique_directories
        FROM file_operations
    """
    )
    analyses["file_patterns"] = cursor.fetchone()

    # 4. Time patterns
    cursor.execute(
        """
        SELECT
            strftime('%H', timestamp) as hour,
            COUNT(*) as activity_count
        FROM nodes
        WHERE timestamp IS NOT NULL
        GROUP BY hour
        ORDER BY hour
    """
    )
    analyses["hourly_activity"] = cursor.fetchall()

    # 5. Conversation patterns
    cursor.execute(
        """
        SELECT
            node_type,
            COUNT(*) as count,
            AVG(LENGTH(raw_json)) as avg_size
        FROM nodes
        GROUP BY node_type
    """
    )
    analyses["node_types"] = cursor.fetchall()

    conn.close()
    return analyses


def identify_report_categories():
    """Based on analysis, identify valuable report categories"""

    reports = {
        "Developer Productivity": {
            "description": "Track coding efficiency and patterns",
            "metrics": [
                "Files edited per session",
                "Tool success rates",
                "Time to complete tasks",
                "Code vs planning ratio",
                "Error recovery patterns",
            ],
            "visualizations": ["timeline", "heatmap", "bar_chart"],
        },
        "Project Evolution": {
            "description": "Understand how the codebase evolves",
            "metrics": [
                "File modification frequency",
                "Hot spots in codebase",
                "Refactoring patterns",
                "New vs modified files",
                "Directory growth",
            ],
            "visualizations": ["treemap", "line_chart", "sunburst"],
        },
        "Tool Utilization": {
            "description": "Optimize tool usage and identify bottlenecks",
            "metrics": [
                "Tool usage frequency",
                "Tool chains (sequences)",
                "Error rates by tool",
                "Tool performance times",
                "Most effective combinations",
            ],
            "visualizations": ["sankey", "pie_chart", "stacked_bar"],
        },
        "Cognitive Patterns": {
            "description": "Analyze thinking and problem-solving approaches",
            "metrics": [
                "Thinking tool usage",
                "Task complexity indicators",
                "Iteration patterns",
                "Decision reversal frequency",
                "Planning vs execution ratio",
            ],
            "visualizations": ["flow_diagram", "radar_chart", "scatter"],
        },
        "Session Intelligence": {
            "description": "Deep dive into individual sessions",
            "metrics": [
                "Session timeline",
                "Goal achievement",
                "Context switches",
                "Momentum indicators",
                "Completion rates",
            ],
            "visualizations": ["gantt", "timeline", "progress_bar"],
        },
        "Error Analysis": {
            "description": "Learn from failures and improve",
            "metrics": [
                "Error frequency by type",
                "Recovery strategies",
                "Repeated errors",
                "Time to resolution",
                "Prevention patterns",
            ],
            "visualizations": ["pareto", "bubble_chart", "matrix"],
        },
        "Knowledge Discovery": {
            "description": "Find patterns and insights in conversations",
            "metrics": [
                "Topic clusters",
                "Question patterns",
                "Solution reuse",
                "Learning curves",
                "Knowledge gaps",
            ],
            "visualizations": ["network", "wordcloud", "dendogram"],
        },
        "Performance Metrics": {
            "description": "System and execution performance",
            "metrics": [
                "Response times",
                "Token usage estimates",
                "Parallel execution patterns",
                "Resource utilization",
                "Optimization opportunities",
            ],
            "visualizations": ["gauge", "area_chart", "boxplot"],
        },
    }

    return reports


def main():
    """Analyze and print findings"""
    print("CHAT LOG METRICS ANALYSIS")
    print("=" * 60)

    analyses = analyze_data_structure()

    print("\nDATA STRUCTURE ANALYSIS:")
    print(f"Session Patterns: {analyses['session_patterns']}")
    print(f"Tool Patterns: {analyses['tool_patterns']}")
    print(f"File Patterns: {analyses['file_patterns']}")

    print("\nACTIVITY BY HOUR:")
    for hour, count in analyses["hourly_activity"][:5]:
        print(f"  Hour {hour}: {count} activities")

    print("\nNODE TYPE DISTRIBUTION:")
    for node_type, count, avg_size in analyses["node_types"]:
        print(f"  {node_type}: {count} nodes, avg size: {avg_size:.0f} bytes")

    reports = identify_report_categories()
    print("\nRECOMMENDED REPORT CATEGORIES:")
    for category, details in reports.items():
        print(f"\n{category}:")
        print(f"  {details['description']}")
        print(f"  Visualizations: {', '.join(details['visualizations'])}")


if __name__ == "__main__":
    main()
