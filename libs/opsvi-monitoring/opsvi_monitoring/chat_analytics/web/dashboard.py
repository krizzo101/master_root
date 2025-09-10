#!/usr/bin/env python3
"""
Web interface for chat logs analysis and reporting
"""

import hashlib
import json
import os
import pickle
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from flask import Flask, jsonify, render_template, request

current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, "..", "templates")
static_dir = os.path.join(current_dir, "..", "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")
CACHE_DIR = Path("/home/opsvi/master_root/.cache")
CACHE_DIR.mkdir(exist_ok=True)

# Cache configuration
SUMMARY_CACHE_TTL = 3600  # 1 hour cache for summaries
session_summary_cache = {}
response_time_cache = {}  # Cache for response time metrics
RESPONSE_TIME_CACHE_TTL = 600  # 10 minutes cache for response times


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """Main dashboard"""
    return render_template("dashboard.html")


@app.route("/api/overview")
def api_overview():
    """Get overview statistics"""
    conn = get_db()
    cursor = conn.cursor()

    # Overall stats
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(*) as total_nodes,
            COUNT(CASE WHEN node_type = 'user' THEN 1 END) as user_messages,
            COUNT(CASE WHEN node_type = 'assistant' THEN 1 END) as assistant_messages,
            MIN(timestamp) as first_activity,
            MAX(timestamp) as last_activity
        FROM nodes
    """
    )
    overview = dict(cursor.fetchone())

    # Tool stats
    cursor.execute(
        """
        SELECT COUNT(*) as total_tool_calls,
               COUNT(DISTINCT tool_name) as unique_tools
        FROM tool_calls
    """
    )
    tool_stats = dict(cursor.fetchone())
    overview.update(tool_stats)

    # File stats
    cursor.execute(
        """
        SELECT COUNT(DISTINCT file_path) as unique_files,
               COUNT(*) as total_file_operations
        FROM file_operations
    """
    )
    file_stats = dict(cursor.fetchone())
    overview.update(file_stats)

    conn.close()
    return jsonify(overview)


@app.route("/api/productivity")
def api_productivity():
    """Developer productivity metrics"""
    conn = get_db()
    cursor = conn.cursor()

    # Files per session
    cursor.execute(
        """
        SELECT
            n.session_id,
            COUNT(DISTINCT fo.file_path) as files_touched,
            COUNT(fo.id) as total_operations,
            COUNT(DISTINCT DATE(n.timestamp)) as days_active
        FROM nodes n
        JOIN tool_calls tc ON n.uuid = tc.node_uuid
        JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
        GROUP BY n.session_id
        ORDER BY COUNT(fo.id) DESC
        LIMIT 20
    """
    )
    sessions = [dict(row) for row in cursor.fetchall()]

    # Hourly activity pattern
    cursor.execute(
        """
        SELECT
            CAST(strftime('%H', timestamp) AS INTEGER) as hour,
            COUNT(*) as activity_count,
            COUNT(DISTINCT session_id) as unique_sessions
        FROM nodes
        WHERE timestamp IS NOT NULL
        GROUP BY hour
        ORDER BY hour
    """
    )
    hourly = [dict(row) for row in cursor.fetchall()]

    # Task completion patterns (based on TodoWrite usage) - use node timestamp
    cursor.execute(
        """
        SELECT
            DATE(n.timestamp) as date,
            COUNT(*) as todos_written
        FROM tool_calls tc
        JOIN nodes n ON tc.node_uuid = n.uuid
        WHERE tc.tool_name = 'TodoWrite'
        AND n.timestamp IS NOT NULL
        GROUP BY DATE(n.timestamp)
        ORDER BY date DESC
        LIMIT 30
    """
    )
    todos = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(
        {"sessions": sessions, "hourly_activity": hourly, "todo_patterns": todos}
    )


@app.route("/api/tools")
def api_tools():
    """Tool utilization analysis"""
    conn = get_db()
    cursor = conn.cursor()

    # Tool frequency
    cursor.execute(
        """
        SELECT
            tool_name,
            COUNT(*) as usage_count,
            COUNT(DISTINCT n.session_id) as sessions_used,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tool_calls), 2) as percentage
        FROM tool_calls tc
        JOIN nodes n ON tc.node_uuid = n.uuid
        GROUP BY tool_name
        ORDER BY usage_count DESC
    """
    )
    tool_frequency = [dict(row) for row in cursor.fetchall()]

    # Tool sequences (what tools follow what) - simplified query
    cursor.execute(
        """
        WITH ordered_tools AS (
            SELECT
                tc.tool_name,
                n.session_id,
                n.timestamp,
                LAG(tc.tool_name) OVER (PARTITION BY n.session_id ORDER BY n.timestamp) as prev_tool
            FROM tool_calls tc
            JOIN nodes n ON tc.node_uuid = n.uuid
            WHERE n.timestamp IS NOT NULL
        )
        SELECT
            prev_tool || ' → ' || tool_name as sequence,
            COUNT(*) as count
        FROM ordered_tools
        WHERE prev_tool IS NOT NULL
        GROUP BY sequence
        ORDER BY count DESC
        LIMIT 20
    """
    )
    sequences = [dict(row) for row in cursor.fetchall()]

    # Tool categories
    categories = {
        "File Operations": ["Read", "Write", "Edit", "MultiEdit"],
        "Shell": ["Bash", "Grep", "LS", "Glob"],
        "Web": ["WebSearch", "WebFetch"],
        "Task Management": ["TodoWrite", "Task"],
        "Thinking": [
            "mcp__thinking__metacognitivethinking",
            "mcp__thinking__sequentialthinking",
        ],
    }

    category_stats = {}
    for category, tools in categories.items():
        placeholders = ",".join("?" * len(tools))
        cursor.execute(
            f"""
            SELECT COUNT(*) as count
            FROM tool_calls
            WHERE tool_name IN ({placeholders})
        """,
            tools,
        )
        result = cursor.fetchone()
        category_stats[category] = result["count"] if result else 0

    # Tool usage over time (for top 5 tools)
    cursor.execute(
        """
        WITH top_tools AS (
            SELECT tool_name
            FROM tool_calls
            GROUP BY tool_name
            ORDER BY COUNT(*) DESC
            LIMIT 5
        )
        SELECT
            tc.tool_name,
            DATE(n.timestamp) as date,
            COUNT(*) as usage_count
        FROM tool_calls tc
        JOIN nodes n ON tc.node_uuid = n.uuid
        WHERE tc.tool_name IN (SELECT tool_name FROM top_tools)
        AND n.timestamp IS NOT NULL
        GROUP BY tc.tool_name, DATE(n.timestamp)
        ORDER BY DATE(n.timestamp), tc.tool_name
    """
    )

    tool_timeline = defaultdict(list)
    for row in cursor.fetchall():
        tool_timeline[row["tool_name"]].append(
            {"date": row["date"], "count": row["usage_count"]}
        )

    conn.close()
    return jsonify(
        {
            "frequency": tool_frequency,
            "sequences": sequences,
            "categories": category_stats,
            "timeline": dict(tool_timeline),
        }
    )


@app.route("/api/files")
def api_files():
    """File operation analysis"""
    conn = get_db()
    cursor = conn.cursor()

    # Most edited files
    cursor.execute(
        """
        SELECT
            file_path,
            COUNT(*) as edit_count,
            COUNT(DISTINCT n.session_id) as sessions,
            COUNT(CASE WHEN operation = 'read' THEN 1 END) as reads,
            COUNT(CASE WHEN operation = 'write' THEN 1 END) as writes,
            COUNT(CASE WHEN operation = 'edit' THEN 1 END) as edits
        FROM file_operations fo
        JOIN tool_calls tc ON fo.tool_call_id = tc.tool_use_id
        JOIN nodes n ON tc.node_uuid = n.uuid
        GROUP BY file_path
        ORDER BY edit_count DESC
        LIMIT 50
    """
    )
    hot_files = [dict(row) for row in cursor.fetchall()]

    # File type distribution
    cursor.execute(
        """
        SELECT
            CASE
                WHEN file_path LIKE '%.py' THEN 'Python'
                WHEN file_path LIKE '%.js' OR file_path LIKE '%.ts' THEN 'JavaScript/TypeScript'
                WHEN file_path LIKE '%.md' THEN 'Markdown'
                WHEN file_path LIKE '%.json' THEN 'JSON'
                WHEN file_path LIKE '%.yaml' OR file_path LIKE '%.yml' THEN 'YAML'
                WHEN file_path LIKE '%.html' THEN 'HTML'
                WHEN file_path LIKE '%.css' THEN 'CSS'
                WHEN file_path LIKE '%.sh' THEN 'Shell'
                ELSE 'Other'
            END as file_type,
            COUNT(*) as count
        FROM file_operations
        GROUP BY file_type
        ORDER BY count DESC
    """
    )
    file_types = [dict(row) for row in cursor.fetchall()]

    # Directory heat map
    cursor.execute(
        """
        SELECT
            SUBSTR(file_path, 1,
                CASE
                    WHEN INSTR(SUBSTR(file_path, 2), '/') > 0
                    THEN INSTR(SUBSTR(file_path, 2), '/') + 1
                    ELSE LENGTH(file_path)
                END
            ) as directory,
            COUNT(*) as operations
        FROM file_operations
        WHERE file_path LIKE '/%'
        GROUP BY directory
        ORDER BY operations DESC
        LIMIT 20
    """
    )
    directories = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(
        {"hot_files": hot_files, "file_types": file_types, "directories": directories}
    )


@app.route("/api/cognitive")
def api_cognitive():
    """Cognitive and thinking patterns"""
    conn = get_db()
    cursor = conn.cursor()

    # Thinking tool usage - use node timestamp since tool_calls timestamp is incorrect
    cursor.execute(
        """
        SELECT
            tc.tool_name,
            COUNT(*) as usage_count,
            DATE(n.timestamp) as date
        FROM tool_calls tc
        JOIN nodes n ON tc.node_uuid = n.uuid
        WHERE (tc.tool_name LIKE '%thinking%' OR tc.tool_name LIKE '%Task%')
        AND n.timestamp IS NOT NULL
        GROUP BY tc.tool_name, DATE(n.timestamp)
        ORDER BY DATE(n.timestamp) DESC
    """
    )
    thinking_patterns = defaultdict(list)
    for row in cursor.fetchall():
        thinking_patterns[row["tool_name"]].append(
            {"date": row["date"], "count": row["usage_count"]}
        )

    # Session complexity (based on node count and tool diversity)
    cursor.execute(
        """
        SELECT
            n.session_id,
            COUNT(DISTINCT n.uuid) as node_count,
            COUNT(DISTINCT tc.tool_name) as tool_diversity,
            COUNT(DISTINCT fo.file_path) as file_diversity,
            CAST((julianday(MAX(n.timestamp)) - julianday(MIN(n.timestamp))) * 24 * 60 AS INTEGER) as duration_minutes
        FROM nodes n
        LEFT JOIN tool_calls tc ON n.uuid = tc.node_uuid
        LEFT JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
        GROUP BY n.session_id
        HAVING node_count > 10
        ORDER BY node_count DESC
        LIMIT 30
    """
    )
    complexity = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(
        {"thinking_patterns": dict(thinking_patterns), "session_complexity": complexity}
    )


@app.route("/api/timeline")
def api_timeline():
    """Activity timeline"""
    conn = get_db()
    cursor = conn.cursor()

    # Daily activity
    cursor.execute(
        """
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as total_nodes,
            COUNT(DISTINCT session_id) as sessions,
            COUNT(CASE WHEN node_type = 'user' THEN 1 END) as user_messages,
            COUNT(CASE WHEN node_type = 'assistant' THEN 1 END) as assistant_messages
        FROM nodes
        WHERE timestamp IS NOT NULL
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 60
    """
    )
    daily = [dict(row) for row in cursor.fetchall()]

    # Recent sessions with details
    cursor.execute(
        """
        SELECT
            n.session_id,
            MIN(n.timestamp) as start_time,
            MAX(n.timestamp) as end_time,
            COUNT(*) as node_count,
            s.cwd
        FROM nodes n
        JOIN sessions s ON n.session_id = s.session_id
        GROUP BY n.session_id, s.cwd
        ORDER BY MAX(n.timestamp) DESC
        LIMIT 20
    """
    )
    recent = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify({"daily_activity": daily, "recent_sessions": recent})


@app.route("/api/search")
def api_search():
    """Search functionality"""
    query = request.args.get("q", "")
    search_type = request.args.get("type", "all")

    if not query:
        return jsonify({"results": []})

    conn = get_db()
    cursor = conn.cursor()
    results = []

    if search_type in ["all", "messages"]:
        # Search in messages
        cursor.execute(
            """
            SELECT
                session_id,
                timestamp,
                node_type,
                SUBSTR(raw_json, 1, 500) as snippet
            FROM nodes
            WHERE raw_json LIKE ?
            ORDER BY timestamp DESC
            LIMIT 20
        """,
            (f"%{query}%",),
        )

        for row in cursor.fetchall():
            results.append(
                {
                    "type": "message",
                    "session_id": row["session_id"],
                    "timestamp": row["timestamp"],
                    "node_type": row["node_type"],
                    "snippet": row["snippet"],
                }
            )

    if search_type in ["all", "files"]:
        # Search in file paths
        cursor.execute(
            """
            SELECT DISTINCT
                file_path,
                COUNT(*) as operation_count
            FROM file_operations
            WHERE file_path LIKE ?
            GROUP BY file_path
            ORDER BY operation_count DESC
            LIMIT 20
        """,
            (f"%{query}%",),
        )

        for row in cursor.fetchall():
            results.append(
                {
                    "type": "file",
                    "file_path": row["file_path"],
                    "operation_count": row["operation_count"],
                }
            )

    conn.close()
    return jsonify({"results": results})


@app.route("/api/session/<session_id>")
def api_session_detail(session_id):
    """Detailed session analysis"""
    conn = get_db()
    cursor = conn.cursor()

    # Session overview
    cursor.execute(
        """
        SELECT
            s.*,
            COUNT(n.uuid) as node_count,
            MIN(n.timestamp) as start_time,
            MAX(n.timestamp) as end_time
        FROM sessions s
        JOIN nodes n ON s.session_id = n.session_id
        WHERE s.session_id = ?
        GROUP BY s.session_id
    """,
        (session_id,),
    )

    session = dict(cursor.fetchone()) if cursor.fetchone() else None

    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Timeline of events
    cursor.execute(
        """
        SELECT
            n.timestamp,
            n.node_type,
            tc.tool_name,
            fo.file_path,
            fo.operation
        FROM nodes n
        LEFT JOIN tool_calls tc ON n.uuid = tc.node_uuid
        LEFT JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
        WHERE n.session_id = ?
        ORDER BY n.timestamp
    """,
        (session_id,),
    )

    timeline = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify({"session": session, "timeline": timeline})


@app.route("/api/sessions/summaries")
def api_session_summaries():
    """Get session summaries with highlights"""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    # Generate cache key
    cache_key = f"summaries_{limit}_{offset}"

    # Check cache
    if cache_key in session_summary_cache:
        cached_data, cached_time = session_summary_cache[cache_key]
        if time.time() - cached_time < SUMMARY_CACHE_TTL:
            return jsonify(cached_data)

    conn = get_db()
    cursor = conn.cursor()

    # Get sessions with comprehensive statistics
    cursor.execute(
        """
        WITH session_stats AS (
            SELECT
                s.session_id,
                s.cwd,
                MIN(n.timestamp) as start_time,
                MAX(n.timestamp) as end_time,
                COUNT(DISTINCT n.uuid) as total_nodes,
                COUNT(DISTINCT CASE WHEN n.node_type = 'user' THEN n.uuid END) as user_messages,
                COUNT(DISTINCT CASE WHEN n.node_type = 'assistant' THEN n.uuid END) as assistant_messages,
                CAST((julianday(MAX(n.timestamp)) - julianday(MIN(n.timestamp))) * 24 * 60 AS INTEGER) as duration_minutes
            FROM sessions s
            JOIN nodes n ON s.session_id = n.session_id
            WHERE n.timestamp IS NOT NULL
            GROUP BY s.session_id
        ),
        tool_stats AS (
            SELECT
                n.session_id,
                COUNT(DISTINCT tc.tool_name) as unique_tools,
                COUNT(tc.id) as total_tool_calls,
                GROUP_CONCAT(tc.tool_name) as tools_used
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            GROUP BY n.session_id
        ),
        file_stats AS (
            SELECT
                n.session_id,
                COUNT(DISTINCT fo.file_path) as files_touched,
                COUNT(fo.id) as file_operations
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
            GROUP BY n.session_id
        ),
        agent_stats AS (
            SELECT
                n.session_id,
                GROUP_CONCAT(
                    CASE
                        WHEN tc.input_json LIKE '%subagent_type%'
                        THEN json_extract(tc.input_json, '$.subagent_type')
                        ELSE NULL
                    END
                ) as agents_used
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            WHERE tc.tool_name = 'Task'
            GROUP BY n.session_id
        ),
        thinking_stats AS (
            SELECT
                n.session_id,
                COUNT(tc.id) as thinking_calls
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            WHERE tc.tool_name LIKE '%thinking%' OR tc.tool_name = 'Task'
            GROUP BY n.session_id
        ),
        todo_stats AS (
            SELECT
                n.session_id,
                COUNT(tc.id) as todo_calls
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            WHERE tc.tool_name = 'TodoWrite'
            GROUP BY n.session_id
        )
        SELECT
            ss.*,
            COALESCE(ts.unique_tools, 0) as unique_tools,
            COALESCE(ts.total_tool_calls, 0) as total_tool_calls,
            COALESCE(ts.tools_used, '') as tools_used,
            COALESCE(fs.files_touched, 0) as files_touched,
            COALESCE(fs.file_operations, 0) as file_operations,
            COALESCE(ags.agents_used, '') as agents_used,
            COALESCE(ths.thinking_calls, 0) as thinking_calls,
            COALESCE(tds.todo_calls, 0) as todo_calls
        FROM session_stats ss
        LEFT JOIN tool_stats ts ON ss.session_id = ts.session_id
        LEFT JOIN file_stats fs ON ss.session_id = fs.session_id
        LEFT JOIN agent_stats ags ON ss.session_id = ags.session_id
        LEFT JOIN thinking_stats ths ON ss.session_id = ths.session_id
        LEFT JOIN todo_stats tds ON ss.session_id = tds.session_id
        ORDER BY ss.start_time DESC
        LIMIT ? OFFSET ?
    """,
        (limit, offset),
    )

    sessions = []
    for row in cursor.fetchall():
        session = dict(row)

        # Get first few user messages to understand what was being worked on
        cursor.execute(
            """
            SELECT raw_json
            FROM nodes
            WHERE session_id = ? AND node_type = 'user'
            ORDER BY timestamp
            LIMIT 3
        """,
            (session["session_id"],),
        )

        user_messages = []
        for msg_row in cursor.fetchall():
            try:
                msg_data = json.loads(msg_row["raw_json"])
                # Check for message.content structure
                if "message" in msg_data and "content" in msg_data["message"]:
                    content = msg_data["message"]["content"]
                    # Skip session hooks and system messages
                    if not content.startswith("<session-") and not content.startswith(
                        "<system-"
                    ):
                        if isinstance(content, list):
                            # Extract text from content blocks
                            text = " ".join(
                                [
                                    c.get("text", "")
                                    for c in content
                                    if c.get("type") == "text"
                                ]
                            )
                        else:
                            text = str(content)
                        if text and len(text) > 10:
                            user_messages.append(
                                text[:300]
                            )  # First 300 chars for better context
            except:
                pass

        # Process agent activations
        agents_activated = []
        if session["agents_used"]:
            # Clean up agent names
            agent_list = [
                a.strip('"')
                for a in session["agents_used"].split(",")
                if a and a.strip() and a.strip() != "None"
            ]
            agents_activated = list(set(agent_list))  # Unique agents

        # Generate highlights based on statistics
        highlights = []

        # Agent activations highlight
        if agents_activated:
            if len(agents_activated) == 1:
                highlights.append(f"🤖 Agent: {agents_activated[0]}")
            else:
                highlights.append(
                    f"🤖 {len(agents_activated)} agents: {', '.join(agents_activated[:3])}"
                )

        # Duration highlight
        if session["duration_minutes"] and session["duration_minutes"] > 60:
            hours = session["duration_minutes"] // 60
            mins = session["duration_minutes"] % 60
            highlights.append(f"⏱️ {hours}h {mins}m session")
        elif session["duration_minutes"] and session["duration_minutes"] > 20:
            highlights.append(f"⏱️ {session['duration_minutes']}m session")

        # Tool usage highlight (only if significant)
        if session["unique_tools"] > 10:
            highlights.append(f"🔧 {session['unique_tools']} different tools")

        # Thinking/planning highlight
        if session["thinking_calls"] > 5:
            highlights.append(f"🧠 {session['thinking_calls']} planning steps")

        # Task management highlight
        if session["todo_calls"] > 5:
            highlights.append(f"✅ {session['todo_calls']} tasks tracked")

        # File activity (only if significant)
        if session["files_touched"] > 10:
            highlights.append(f"📁 {session['files_touched']} files modified")

        # Check for analyzed summary first
        cursor.execute(
            """
            SELECT title, summary, bullet_points
            FROM session_analyses
            WHERE session_id = ?
        """,
            (session["session_id"],),
        )

        analysis = cursor.fetchone()
        if analysis:
            # Use the analyzed summary
            session["title"] = analysis["title"]
            session["summary"] = analysis["summary"]
            try:
                session["bullets"] = json.loads(analysis["bullet_points"])
            except:
                session["bullets"] = []
        else:
            # Fallback to heuristic summary
            summary = _generate_content_aware_summary(
                session, user_messages, agents_activated
            )
            session["title"] = summary
            session["summary"] = summary
            session["bullets"] = []

        session["highlights"] = highlights
        sessions.append(session)

    # Get total count
    cursor.execute("SELECT COUNT(DISTINCT session_id) as total FROM sessions")
    total = cursor.fetchone()["total"]

    conn.close()

    result = {"sessions": sessions, "total": total, "limit": limit, "offset": offset}

    # Cache the result
    session_summary_cache[cache_key] = (result, time.time())

    # Clean old cache entries (keep only 10 most recent)
    if len(session_summary_cache) > 10:
        oldest_keys = sorted(
            session_summary_cache.keys(), key=lambda k: session_summary_cache[k][1]
        )[: len(session_summary_cache) - 10]
        for key in oldest_keys:
            del session_summary_cache[key]

    return jsonify(result)


def _generate_content_aware_summary(session, user_messages, agents_activated):
    """Generate a meaningful summary based on actual session content"""

    # Analyze user messages to understand what was being worked on
    keywords = {
        "build": ["build", "create", "implement", "develop", "add", "feature"],
        "fix": ["fix", "bug", "error", "issue", "problem", "debug", "solve"],
        "analyze": [
            "analyze",
            "review",
            "understand",
            "explore",
            "investigate",
            "find",
        ],
        "design": ["design", "architect", "plan", "structure", "organize"],
        "refactor": ["refactor", "improve", "optimize", "clean", "reorganize"],
        "test": ["test", "verify", "check", "validate", "ensure"],
        "document": ["document", "explain", "describe", "write", "readme"],
        "deploy": ["deploy", "release", "publish", "ship", "launch"],
        "configure": ["configure", "setup", "install", "config", "settings"],
    }

    # Combine all user messages
    full_context = " ".join(user_messages).lower() if user_messages else ""

    # Determine primary activity
    primary_activity = None
    activity_scores = {}
    for activity, terms in keywords.items():
        score = sum(1 for term in terms if term in full_context)
        if score > 0:
            activity_scores[activity] = score

    if activity_scores:
        primary_activity = max(activity_scores, key=activity_scores.get)

    # Build the summary
    summary_parts = []

    # Activity-based opening
    if primary_activity == "build":
        if (
            "dashboard" in full_context
            or "interface" in full_context
            or "ui" in full_context
        ):
            summary_parts.append("Built web interface/dashboard features")
        elif "api" in full_context or "endpoint" in full_context:
            summary_parts.append("Developed API endpoints")
        elif "parser" in full_context or "ingest" in full_context:
            summary_parts.append("Created data parsing/ingestion system")
        else:
            summary_parts.append("Implemented new functionality")
    elif primary_activity == "fix":
        summary_parts.append("Fixed bugs and resolved issues")
    elif primary_activity == "analyze":
        if "log" in full_context or "data" in full_context:
            summary_parts.append("Analyzed logs and data patterns")
        else:
            summary_parts.append("Investigated and analyzed codebase")
    elif primary_activity == "design":
        summary_parts.append("Designed system architecture")
    elif primary_activity == "refactor":
        summary_parts.append("Refactored and improved code quality")
    elif primary_activity == "test":
        summary_parts.append("Tested and validated functionality")
    elif primary_activity == "document":
        summary_parts.append("Created documentation")
    elif primary_activity == "deploy":
        summary_parts.append("Deployed to production")
    elif primary_activity == "configure":
        summary_parts.append("Configured system settings")
    else:
        # Fallback to tool-based summary
        if session["files_touched"] > 5:
            summary_parts.append("Worked on multiple files")
        elif session["thinking_calls"] > 3:
            summary_parts.append("Planned complex implementation")
        else:
            summary_parts.append("General development work")

    # Add agent context if relevant
    if agents_activated:
        if "test-remediation-specialist" in agents_activated:
            summary_parts.append("with automated testing")
        elif "excellence-optimizer" in agents_activated:
            summary_parts.append("with optimization focus")
        elif "research" in str(agents_activated).lower():
            summary_parts.append("with research analysis")

    # Extract specific features/components mentioned
    feature_keywords = [
        "session",
        "chart",
        "graph",
        "report",
        "dashboard",
        "timeline",
        "api",
        "endpoint",
        "database",
        "cache",
        "query",
        "tool",
        "agent",
    ]
    mentioned_features = [kw for kw in feature_keywords if kw in full_context]
    if mentioned_features:
        summary_parts.append(f"({', '.join(mentioned_features[:3])})")

    return ". ".join(summary_parts) if summary_parts else "Development session"


def _generate_session_summary(session):
    """Fallback summary generator"""
    return "Session with minimal context available"


@app.route("/api/response-times-history")
def api_response_times_history():
    """Get response time history over time"""
    from ..analysis.response_history import get_response_time_history

    session_id = request.args.get("session_id")
    history = get_response_time_history(session_id)

    return jsonify(history)


@app.route("/api/response-times")
def api_response_times():
    """Get response time metrics with caching"""
    import time

    from ..analysis import ResponseTimeAnalyzer, format_duration

    session_id = request.args.get("session_id")
    cache_key = f"response_times_{session_id or 'all'}"

    # Check cache
    if cache_key in response_time_cache:
        cached_data, cached_time = response_time_cache[cache_key]
        if time.time() - cached_time < RESPONSE_TIME_CACHE_TTL:
            return jsonify(cached_data)

    # If not in cache or expired, calculate using fast analyzer
    from ..analysis.response_analyzer_fast import FastResponseTimeAnalyzer

    analyzer = FastResponseTimeAnalyzer()
    metrics = analyzer.get_response_times_fast(session_id)
    analyzer.close()

    # Format for display
    result = {
        "average": format_duration(metrics["average"]),
        "average_seconds": metrics["average"],
        "median": format_duration(metrics["median"]),
        "median_seconds": metrics["median"],
        "shortest": {
            "time": format_duration(metrics["shortest"]["time"]),
            "seconds": metrics["shortest"]["time"],
            "prompt": metrics["shortest"]["prompt"],
            "timestamp": metrics["shortest"]["timestamp"],
        },
        "longest": {
            "time": format_duration(metrics["longest"]["time"]),
            "seconds": metrics["longest"]["time"],
            "prompt": metrics["longest"]["prompt"],
            "timestamp": metrics["longest"]["timestamp"],
        },
        "total_prompts": metrics["total_prompts"],
        "by_session": {},
    }

    # Format session stats
    for sid, stats in metrics["by_session"].items():
        result["by_session"][sid] = {
            "average": format_duration(stats["average"]),
            "median": format_duration(stats["median"]),
            "min": format_duration(stats["min"]),
            "max": format_duration(stats["max"]),
            "count": stats["count"],
        }

    # Cache the result
    response_time_cache[cache_key] = (result, time.time())

    return jsonify(result)


@app.route("/api/activity-timeline/<session_id>")
def api_activity_timeline(session_id):
    """Get activity timeline for a session"""
    from response_time_analyzer import ResponseTimeAnalyzer

    analyzer = ResponseTimeAnalyzer()
    timeline = analyzer.get_activity_timeline(session_id)
    analyzer.close()

    return jsonify(timeline)


@app.route("/api/activity-summary")
def api_activity_summary():
    """Get activity vs dead space summary"""
    from ..analysis import ResponseTimeAnalyzer, format_duration

    session_id = request.args.get("session_id")

    analyzer = ResponseTimeAnalyzer()
    summary = analyzer.get_activity_summary(session_id)
    analyzer.close()

    # Format for display
    result = {}
    for sid, stats in summary.items():
        result[sid] = {
            "total_nodes": stats["total_nodes"],
            "active_time": format_duration(stats["active_time_seconds"]),
            "dead_time": format_duration(stats["dead_time_seconds"]),
            "total_time": format_duration(stats["total_time_seconds"]),
            "active_percentage": round(stats["active_percentage"], 1),
            "dead_percentage": round(stats["dead_percentage"], 1),
            "max_gap": format_duration(stats["max_gap_seconds"]),
            "avg_gap": format_duration(stats["avg_gap_seconds"]),
        }

    return jsonify(result)


@app.route("/api/cache/clear", methods=["POST"])
def api_clear_cache():
    """Clear the session summary cache"""
    global session_summary_cache
    session_summary_cache.clear()
    return jsonify({"status": "success", "message": "Cache cleared"})


@app.route("/api/config")
def api_config():
    """Get application configuration and settings"""
    config = {
        "database": {
            "path": str(DB_PATH),
            "exists": DB_PATH.exists(),
            "size_mb": DB_PATH.stat().st_size / (1024 * 1024)
            if DB_PATH.exists()
            else 0,
        },
        "cache": {
            "directory": str(CACHE_DIR),
            "summary_ttl_seconds": SUMMARY_CACHE_TTL,
            "cached_summaries": len(session_summary_cache),
        },
        "project": {
            "root": "/home/opsvi/master_root",
            "logs_directory": str(
                Path.home() / ".claude" / "projects" / "-home-opsvi-master-root"
            ),
            "proj_intel_exists": Path("/home/opsvi/master_root/.proj-intel").exists(),
        },
        "server": {"host": "localhost", "port": 5001, "debug": app.debug},
    }
    return jsonify(config)


if __name__ == "__main__":
    # Create templates directory
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    # Create static directory
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)

    app.run(debug=True, host="0.0.0.0", port=5000)
