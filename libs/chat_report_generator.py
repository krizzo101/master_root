#!/usr/bin/env python3
"""
Report Generation System for Chat Logs
Generates various reports from the parsed and stored chat taxonomy data
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import seaborn as sns
from psycopg2.extras import RealDictCursor


class ChatReportGenerator:
    """Generate comprehensive reports from chat log data"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config

    def generate_session_report(self, session_id: str) -> Dict:
        """Generate comprehensive session report"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                report = {
                    "session_id": session_id,
                    "summary": self._get_session_summary(cur, session_id),
                    "timeline": self._get_session_timeline(cur, session_id),
                    "tool_usage": self._get_tool_usage(cur, session_id),
                    "file_operations": self._get_file_operations(cur, session_id),
                    "error_analysis": self._get_error_analysis(cur, session_id),
                    "conversation_flow": self._get_conversation_flow(cur, session_id),
                }
                return report

    def _get_session_summary(self, cur, session_id: str) -> Dict:
        """Get session summary statistics"""
        sql = """
        WITH session_stats AS (
            SELECT
                s.session_id,
                s.cwd,
                s.git_branch,
                s.created_at,
                MIN(n.timestamp) as start_time,
                MAX(n.timestamp) as end_time,
                COUNT(DISTINCT n.uuid) as total_nodes,
                COUNT(DISTINCT CASE WHEN n.node_type = 'user' THEN n.uuid END) as user_messages,
                COUNT(DISTINCT CASE WHEN n.node_type = 'assistant' THEN n.uuid END) as assistant_messages,
                COUNT(DISTINCT CASE WHEN n.node_type = 'system' THEN n.uuid END) as system_events,
                COUNT(DISTINCT CASE WHEN n.node_type = 'summary' THEN n.uuid END) as summaries
            FROM sessions s
            JOIN nodes n ON s.session_id = n.session_id
            WHERE s.session_id = %s
            GROUP BY s.session_id, s.cwd, s.git_branch, s.created_at
        ),
        tool_stats AS (
            SELECT
                COUNT(DISTINCT tc.tool_use_id) as total_tool_calls,
                COUNT(DISTINCT tc.tool_name) as unique_tools,
                COUNT(DISTINCT CASE WHEN tr.is_error THEN tc.tool_use_id END) as failed_tools
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            LEFT JOIN tool_results tr ON tc.tool_use_id = tr.tool_use_id
            WHERE n.session_id = %s
        ),
        file_stats AS (
            SELECT
                COUNT(DISTINCT fo.file_path) as files_touched,
                COUNT(DISTINCT CASE WHEN fo.operation = 'read' THEN fo.file_path END) as files_read,
                COUNT(DISTINCT CASE WHEN fo.operation = 'write' THEN fo.file_path END) as files_written,
                COUNT(DISTINCT CASE WHEN fo.operation = 'edit' THEN fo.file_path END) as files_edited
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
            WHERE n.session_id = %s
        )
        SELECT
            ss.*,
            EXTRACT(EPOCH FROM (ss.end_time - ss.start_time))/60 as duration_minutes,
            ts.total_tool_calls,
            ts.unique_tools,
            ts.failed_tools,
            fs.files_touched,
            fs.files_read,
            fs.files_written,
            fs.files_edited
        FROM session_stats ss
        CROSS JOIN tool_stats ts
        CROSS JOIN file_stats fs
        """
        cur.execute(sql, (session_id, session_id, session_id))
        return cur.fetchone()

    def _get_session_timeline(self, cur, session_id: str) -> List[Dict]:
        """Get timeline of session activity"""
        sql = """
        SELECT
            n.timestamp,
            n.node_type,
            CASE
                WHEN n.node_type = 'user' THEN 'User message'
                WHEN n.node_type = 'assistant' AND tc.tool_use_id IS NOT NULL THEN 'Tool: ' || tc.tool_name
                WHEN n.node_type = 'assistant' THEN 'Assistant response'
                WHEN n.node_type = 'system' THEN 'System event'
                WHEN n.node_type = 'summary' THEN 'Summary generated'
            END as event_type,
            tc.tool_name,
            fo.file_path
        FROM nodes n
        LEFT JOIN tool_calls tc ON n.uuid = tc.node_uuid
        LEFT JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
        WHERE n.session_id = %s
        ORDER BY n.timestamp
        """
        cur.execute(sql, (session_id,))
        return cur.fetchall()

    def _get_tool_usage(self, cur, session_id: str) -> Dict:
        """Get detailed tool usage statistics"""
        sql = """
        SELECT
            tc.tool_name,
            COUNT(*) as usage_count,
            COUNT(DISTINCT n.uuid) as unique_nodes,
            AVG(CASE WHEN tr.is_error THEN 1 ELSE 0 END) * 100 as error_rate,
            MIN(tc.timestamp) as first_used,
            MAX(tc.timestamp) as last_used,
            ARRAY_AGG(DISTINCT
                CASE
                    WHEN tc.tool_name IN ('Read', 'Write', 'Edit', 'MultiEdit') THEN fo.file_path
                    WHEN tc.tool_name = 'Bash' THEN tc.input_json->>'command'
                    ELSE NULL
                END
            ) FILTER (WHERE
                (tc.tool_name IN ('Read', 'Write', 'Edit', 'MultiEdit') AND fo.file_path IS NOT NULL) OR
                (tc.tool_name = 'Bash' AND tc.input_json->>'command' IS NOT NULL)
            ) as targets
        FROM nodes n
        JOIN tool_calls tc ON n.uuid = tc.node_uuid
        LEFT JOIN tool_results tr ON tc.tool_use_id = tr.tool_use_id
        LEFT JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
        WHERE n.session_id = %s
        GROUP BY tc.tool_name
        ORDER BY usage_count DESC
        """
        cur.execute(sql, (session_id,))
        return {"tools": cur.fetchall()}

    def _get_file_operations(self, cur, session_id: str) -> Dict:
        """Get file operation details"""
        sql = """
        WITH file_stats AS (
            SELECT
                fo.file_path,
                COUNT(*) as total_operations,
                COUNT(CASE WHEN fo.operation = 'read' THEN 1 END) as read_count,
                COUNT(CASE WHEN fo.operation = 'write' THEN 1 END) as write_count,
                COUNT(CASE WHEN fo.operation = 'edit' THEN 1 END) as edit_count,
                MIN(tc.timestamp) as first_access,
                MAX(tc.timestamp) as last_access,
                STRING_AGG(DISTINCT fo.operation, ', ') as operations
            FROM nodes n
            JOIN tool_calls tc ON n.uuid = tc.node_uuid
            JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
            WHERE n.session_id = %s
            GROUP BY fo.file_path
        )
        SELECT
            *,
            CASE
                WHEN file_path LIKE '%.py' THEN 'Python'
                WHEN file_path LIKE '%.js' OR file_path LIKE '%.ts' THEN 'JavaScript/TypeScript'
                WHEN file_path LIKE '%.md' THEN 'Markdown'
                WHEN file_path LIKE '%.json' THEN 'JSON'
                WHEN file_path LIKE '%.yaml' OR file_path LIKE '%.yml' THEN 'YAML'
                ELSE 'Other'
            END as file_type
        FROM file_stats
        ORDER BY total_operations DESC
        """
        cur.execute(sql, (session_id,))
        return {"files": cur.fetchall()}

    def _get_error_analysis(self, cur, session_id: str) -> Dict:
        """Analyze errors and failures"""
        sql = """
        SELECT
            tc.tool_name,
            tc.tool_use_id,
            tc.timestamp,
            tr.content_text as error_message,
            tc.input_json
        FROM nodes n
        JOIN tool_calls tc ON n.uuid = tc.node_uuid
        JOIN tool_results tr ON tc.tool_use_id = tr.tool_use_id
        WHERE n.session_id = %s AND tr.is_error = true
        ORDER BY tc.timestamp DESC
        """
        cur.execute(sql, (session_id,))
        errors = cur.fetchall()

        # Group errors by type
        error_types = {}
        for error in errors:
            tool = error["tool_name"]
            if tool not in error_types:
                error_types[tool] = []
            error_types[tool].append(error)

        return {
            "total_errors": len(errors),
            "errors_by_tool": error_types,
            "recent_errors": errors[:10],
        }

    def _get_conversation_flow(self, cur, session_id: str) -> List[Dict]:
        """Get conversation flow with turn pairs"""
        sql = """
        WITH conversation AS (
            SELECT
                n.uuid,
                n.parent_uuid,
                n.node_type,
                n.timestamp,
                CASE
                    WHEN n.node_type = 'user' THEN (n.raw_json->'message'->>'content')::text
                    WHEN n.node_type = 'assistant' THEN 'Assistant response'
                    ELSE n.node_type
                END as content_preview,
                tc.tool_name,
                COUNT(tc.tool_use_id) as tool_count
            FROM nodes n
            LEFT JOIN tool_calls tc ON n.uuid = tc.node_uuid
            WHERE n.session_id = %s AND n.node_type IN ('user', 'assistant')
            GROUP BY n.uuid, n.parent_uuid, n.node_type, n.timestamp, n.raw_json
            ORDER BY n.timestamp
        )
        SELECT * FROM conversation
        """
        cur.execute(sql, (session_id,))
        return cur.fetchall()

    def generate_activity_report(self, days: int = 7) -> Dict:
        """Generate activity report for recent days"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cutoff_date = datetime.now() - timedelta(days=days)

                # Daily activity
                sql = """
                SELECT
                    DATE(n.timestamp) as date,
                    COUNT(DISTINCT n.session_id) as sessions,
                    COUNT(DISTINCT CASE WHEN n.node_type = 'user' THEN n.uuid END) as user_messages,
                    COUNT(DISTINCT tc.tool_use_id) as tool_calls,
                    COUNT(DISTINCT fo.file_path) as files_touched
                FROM nodes n
                LEFT JOIN tool_calls tc ON n.uuid = tc.node_uuid
                LEFT JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
                WHERE n.timestamp >= %s
                GROUP BY DATE(n.timestamp)
                ORDER BY date DESC
                """
                cur.execute(sql, (cutoff_date,))
                daily_activity = cur.fetchall()

                # Top tools
                sql = """
                SELECT
                    tc.tool_name,
                    COUNT(*) as usage_count
                FROM nodes n
                JOIN tool_calls tc ON n.uuid = tc.node_uuid
                WHERE n.timestamp >= %s
                GROUP BY tc.tool_name
                ORDER BY usage_count DESC
                LIMIT 10
                """
                cur.execute(sql, (cutoff_date,))
                top_tools = cur.fetchall()

                # Most edited files
                sql = """
                SELECT
                    fo.file_path,
                    COUNT(*) as edit_count,
                    COUNT(DISTINCT n.session_id) as sessions
                FROM nodes n
                JOIN tool_calls tc ON n.uuid = tc.node_uuid
                JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
                WHERE n.timestamp >= %s AND fo.operation IN ('edit', 'write')
                GROUP BY fo.file_path
                ORDER BY edit_count DESC
                LIMIT 20
                """
                cur.execute(sql, (cutoff_date,))
                most_edited = cur.fetchall()

                return {
                    "period_days": days,
                    "daily_activity": daily_activity,
                    "top_tools": top_tools,
                    "most_edited_files": most_edited,
                }

    def export_to_html(self, report: Dict, output_path: Path):
        """Export report to HTML format"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat Log Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                .metric-label {{ color: #666; font-size: 14px; }}
                .error {{ color: #f44336; }}
                .success {{ color: #4CAF50; }}
            </style>
        </head>
        <body>
            <h1>Session Report: {session_id}</h1>

            <h2>Summary</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{duration:.1f}</div>
                    <div class="metric-label">Duration (minutes)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{total_messages}</div>
                    <div class="metric-label">Total Messages</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{tool_calls}</div>
                    <div class="metric-label">Tool Calls</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{files_touched}</div>
                    <div class="metric-label">Files Touched</div>
                </div>
            </div>

            <h2>Tool Usage</h2>
            <table>
                <tr><th>Tool</th><th>Count</th><th>Error Rate</th></tr>
                {tool_rows}
            </table>

            <h2>File Operations</h2>
            <table>
                <tr><th>File</th><th>Operations</th><th>Read</th><th>Write</th><th>Edit</th></tr>
                {file_rows}
            </table>

            <h2>Errors</h2>
            <div class="errors">
                <p>Total Errors: <span class="error">{error_count}</span></p>
                {error_details}
            </div>
        </body>
        </html>
        """

        # Format the data
        summary = report.get("summary", {})
        tools = report.get("tool_usage", {}).get("tools", [])
        files = report.get("file_operations", {}).get("files", [])
        errors = report.get("error_analysis", {})

        # Generate tool rows
        tool_rows = ""
        for tool in tools:
            error_class = "error" if tool.get("error_rate", 0) > 10 else "success"
            tool_rows += f"""
                <tr>
                    <td>{tool['tool_name']}</td>
                    <td>{tool['usage_count']}</td>
                    <td class="{error_class}">{tool.get('error_rate', 0):.1f}%</td>
                </tr>
            """

        # Generate file rows
        file_rows = ""
        for file in files:
            file_rows += f"""
                <tr>
                    <td>{file['file_path']}</td>
                    <td>{file['operations']}</td>
                    <td>{file['read_count']}</td>
                    <td>{file['write_count']}</td>
                    <td>{file['edit_count']}</td>
                </tr>
            """

        # Generate error details
        error_details = ""
        for tool, tool_errors in errors.get("errors_by_tool", {}).items():
            error_details += f"<h3>{tool} ({len(tool_errors)} errors)</h3><ul>"
            for error in tool_errors[:3]:  # Show first 3
                error_details += f"<li>{error['timestamp']}: {error.get('error_message', 'Unknown error')[:100]}...</li>"
            error_details += "</ul>"

        # Fill template
        html = html_template.format(
            session_id=report.get("session_id", "Unknown"),
            duration=summary.get("duration_minutes", 0),
            total_messages=summary.get("total_nodes", 0),
            tool_calls=summary.get("total_tool_calls", 0),
            files_touched=summary.get("files_touched", 0),
            tool_rows=tool_rows,
            file_rows=file_rows,
            error_count=errors.get("total_errors", 0),
            error_details=error_details,
        )

        # Write to file
        output_path.write_text(html)
        print(f"Report exported to {output_path}")

    def export_to_json(self, report: Dict, output_path: Path):
        """Export report to JSON format"""

        # Convert datetime objects to strings
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            return obj

        serialized = serialize(report)
        output_path.write_text(json.dumps(serialized, indent=2))
        print(f"Report exported to {output_path}")


def generate_sample_reports():
    """Generate sample reports"""
    from chat_taxonomy_parser import ChatLogParser, ChatLogStorage

    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "chat_logs",
        "user": "postgres",
        "password": "postgres",
    }

    # Parse and store data first
    parser = ChatLogParser()
    session_exports = Path("/home/opsvi/master_root/.claude/session-exports")

    if session_exports.exists():
        for jsonl_file in list(session_exports.glob("*.jsonl"))[
            :1
        ]:  # Process first file
            print(f"Parsing {jsonl_file}")
            parser.parse_jsonl_file(jsonl_file)

    if parser.sessions:
        # Store data
        storage = ChatLogStorage(db_config)
        storage.connect()
        storage.create_schema()
        storage.store_parsed_data(parser)
        storage.close()

        # Generate reports
        generator = ChatReportGenerator(db_config)

        # Generate session report
        session_id = list(parser.sessions.keys())[0]
        session_report = generator.generate_session_report(session_id)

        # Export to HTML
        html_path = Path(f"/tmp/session_report_{session_id}.html")
        generator.export_to_html(session_report, html_path)

        # Export to JSON
        json_path = Path(f"/tmp/session_report_{session_id}.json")
        generator.export_to_json(session_report, json_path)

        # Generate activity report
        activity_report = generator.generate_activity_report(days=30)
        activity_json_path = Path("/tmp/activity_report.json")
        generator.export_to_json(activity_report, activity_json_path)

        print(f"Reports generated:")
        print(f"  - HTML: {html_path}")
        print(f"  - JSON: {json_path}")
        print(f"  - Activity: {activity_json_path}")


if __name__ == "__main__":
    generate_sample_reports()
