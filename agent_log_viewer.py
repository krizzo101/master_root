#!/usr/bin/env python3
"""
Brand New Agent Log Viewer - Live tail of agent activity
"""

import asyncio
import json
import re
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse


class AgentLogData:
    def __init__(self):
        self.projects_dir = Path.home() / ".claude" / "projects"
        self.orchestrator_dir = Path("apps/agent-orchestrator/outputs")
        self.live_logs = []
        self.max_logs = 500

    def get_agent_files(self):
        """Get all recent agent files"""
        files = []
        cutoff_time = time.time() - 86400  # 24 hours

        # Claude projects
        if self.projects_dir.exists():
            for project_dir in self.projects_dir.glob("*"):
                if project_dir.is_dir():
                    for jsonl_file in project_dir.glob("*.jsonl"):
                        try:
                            stat = jsonl_file.stat()
                            if stat.st_size > 0 and stat.st_mtime > cutoff_time:
                                files.append(
                                    {
                                        "path": jsonl_file,
                                        "agent_id": jsonl_file.stem[-8:],
                                        "project": project_dir.name,
                                        "type": "claude",
                                        "size": stat.st_size,
                                        "modified": stat.st_mtime,
                                    }
                                )
                        except OSError:
                            continue

        # Orchestrator outputs
        if self.orchestrator_dir.exists():
            for log_file in self.orchestrator_dir.rglob("*.log"):
                try:
                    stat = log_file.stat()
                    if stat.st_size > 0 and stat.st_mtime > cutoff_time:
                        files.append(
                            {
                                "path": log_file,
                                "agent_id": log_file.stem,
                                "project": log_file.parent.name,
                                "type": "orchestrator",
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                            }
                        )
                except OSError:
                    continue

        # Sort by most recent
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    def tail_file(self, file_path, lines=50):
        """Get last N lines from file"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception:
            return []

    def parse_claude_log(self, line, agent_id, project):
        """Parse Claude JSONL log entry"""
        try:
            entry = json.loads(line.strip())
            timestamp = entry.get("timestamp", "")
            role = entry.get("role", "unknown")
            content = entry.get("content", [])

            # Extract meaningful content
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "unknown")
                            return {
                                "timestamp": timestamp,
                                "agent_id": agent_id,
                                "project": project,
                                "type": "tool_use",
                                "role": role,
                                "message": f"🔧 {tool_name}",
                                "details": str(item.get("input", ""))[:100],
                            }
                        elif item.get("type") == "text":
                            text = item.get("text", "")[:200]
                            return {
                                "timestamp": timestamp,
                                "agent_id": agent_id,
                                "project": project,
                                "type": "text",
                                "role": role,
                                "message": text,
                                "details": "",
                            }

            return {
                "timestamp": timestamp,
                "agent_id": agent_id,
                "project": project,
                "type": "activity",
                "role": role,
                "message": f"{role} activity",
                "details": str(content)[:100] if content else "",
            }
        except json.JSONDecodeError:
            return None

    def get_live_activity(self):
        """Get recent activity from all agents"""
        activity = []
        files = self.get_agent_files()

        for file_info in files[:20]:  # Top 20 most recent files
            lines = self.tail_file(file_info["path"], 10)  # Last 10 lines each

            for line in lines:
                if not line.strip():
                    continue

                if file_info["type"] == "claude":
                    parsed = self.parse_claude_log(
                        line, file_info["agent_id"], file_info["project"]
                    )
                    if parsed:
                        activity.append(parsed)
                else:
                    # Simple orchestrator log parsing
                    activity.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "agent_id": file_info["agent_id"],
                            "project": file_info["project"],
                            "type": "orchestrator",
                            "role": "system",
                            "message": line.strip()[:200],
                            "details": "",
                        }
                    )

        # Sort by timestamp
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity[:100]  # Return top 100 most recent


# Global data store
log_data = AgentLogData()


class LogViewerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.serve_dashboard()
        elif path == "/api/logs":
            self.serve_logs_api()
        elif path == "/api/agents":
            self.serve_agents_api()
        else:
            self.send_error(404)

    def serve_dashboard(self):
        html = """<!DOCTYPE html>
<html>
<head>
    <title>🔍 Live Agent Activity Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            background: #0a0a0a;
            color: #00ff00;
            height: 100vh;
            overflow: hidden;
        }

        .header {
            background: #1a1a1a;
            padding: 15px 20px;
            border-bottom: 2px solid #00ff00;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 1.5em;
            text-shadow: 0 0 10px #00ff00;
        }

        .stats {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
        }

        .stat {
            color: #00aaff;
        }

        .main-content {
            height: calc(100vh - 80px);
            display: flex;
        }

        .sidebar {
            width: 300px;
            background: #111;
            border-right: 1px solid #333;
            overflow-y: auto;
        }

        .log-area {
            flex: 1;
            background: #000;
            overflow-y: auto;
            padding: 10px;
            font-size: 13px;
            line-height: 1.4;
        }

        .agent-item {
            padding: 10px;
            border-bottom: 1px solid #222;
            cursor: pointer;
            transition: all 0.2s;
        }

        .agent-item:hover {
            background: #222;
            border-left: 3px solid #00ff00;
        }

        .agent-item.active {
            background: #1a1a2e;
            border-left: 3px solid #00ff00;
        }

        .agent-name {
            font-weight: bold;
            color: #00ff00;
        }

        .agent-project {
            color: #888;
            font-size: 0.8em;
        }

        .agent-stats {
            color: #00aaff;
            font-size: 0.8em;
            margin-top: 5px;
        }

        .log-entry {
            margin-bottom: 8px;
            padding: 8px;
            border-left: 3px solid;
            background: rgba(255,255,255,0.02);
            border-radius: 0 4px 4px 0;
        }

        .log-tool { border-left-color: #ff6b6b; }
        .log-text { border-left-color: #4ecdc4; }
        .log-activity { border-left-color: #ffe66d; }
        .log-orchestrator { border-left-color: #95e1d3; }

        .log-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            font-size: 0.85em;
        }

        .log-time {
            color: #888;
        }

        .log-agent {
            color: #00aaff;
        }

        .log-message {
            color: #00ff00;
            word-wrap: break-word;
        }

        .log-details {
            color: #666;
            font-size: 0.8em;
            margin-top: 4px;
            font-style: italic;
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff00;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.3; }
            100% { opacity: 1; }
        }

        .controls {
            padding: 10px;
            background: #1a1a1a;
            border-bottom: 1px solid #333;
            text-align: center;
        }

        .btn {
            background: #333;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 5px 15px;
            margin: 0 5px;
            cursor: pointer;
            border-radius: 3px;
            font-family: inherit;
            font-size: 0.9em;
        }

        .btn:hover {
            background: #00ff00;
            color: #000;
        }

        .auto-scroll {
            background: #00ff00;
            color: #000;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Live Agent Activity Monitor</h1>
        <div class="stats">
            <div class="stat">Active Agents: <span id="agent-count">0</span></div>
            <div class="stat">Total Logs: <span id="log-count">0</span></div>
            <div class="stat">Status: <span class="status-indicator"></span> Live</div>
        </div>
    </div>

    <div class="main-content">
        <div class="sidebar">
            <div class="controls">
                <button class="btn auto-scroll" id="auto-scroll-btn" onclick="toggleAutoScroll()">Auto-Scroll ON</button>
                <button class="btn" onclick="clearLogs()">Clear</button>
            </div>
            <div id="agent-list">Loading agents...</div>
        </div>

        <div class="log-area" id="log-area">
            <div style="text-align: center; color: #666; margin-top: 100px;">
                🚀 Loading agent activity...<br>
                <small>Real-time log streaming will begin shortly</small>
            </div>
        </div>
    </div>

    <script>
        let autoScroll = true;
        let selectedAgent = 'all';

        function formatTime(timestamp) {
            if (!timestamp) return 'Unknown';
            try {
                const date = new Date(timestamp);
                return date.toLocaleTimeString();
            } catch {
                return timestamp.slice(-8) || 'Unknown';
            }
        }

        function formatAgentId(agentId) {
            if (!agentId) return 'Unknown';
            return agentId.length > 8 ? '...' + agentId.slice(-8) : agentId;
        }

        function updateAgentList(agents) {
            const container = document.getElementById('agent-list');
            if (!agents.length) {
                container.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No active agents</div>';
                return;
            }

            const html = agents.map(agent => `
                <div class="agent-item" onclick="selectAgent('${agent.agent_id}')">
                    <div class="agent-name">${formatAgentId(agent.agent_id)}</div>
                    <div class="agent-project">${agent.project}</div>
                    <div class="agent-stats">${agent.type} • ${(agent.size/1024).toFixed(0)}KB</div>
                </div>
            `).join('');

            container.innerHTML = `
                <div class="agent-item ${selectedAgent === 'all' ? 'active' : ''}" onclick="selectAgent('all')">
                    <div class="agent-name">🌐 ALL AGENTS</div>
                    <div class="agent-project">Live feed from all sources</div>
                </div>
                ${html}
            `;

            document.getElementById('agent-count').textContent = agents.length;
        }

        function updateLogs(logs) {
            const container = document.getElementById('log-area');

            if (!logs.length) {
                container.innerHTML = '<div style="text-align: center; color: #666; margin-top: 100px;">📭 No recent activity</div>';
                return;
            }

            const filteredLogs = selectedAgent === 'all' ? logs : logs.filter(log => log.agent_id === selectedAgent);

            const html = filteredLogs.map(log => `
                <div class="log-entry log-${log.type}">
                    <div class="log-header">
                        <span class="log-time">${formatTime(log.timestamp)}</span>
                        <span class="log-agent">${formatAgentId(log.agent_id)} (${log.project})</span>
                    </div>
                    <div class="log-message">${log.message}</div>
                    ${log.details ? `<div class="log-details">${log.details}</div>` : ''}
                </div>
            `).join('');

            container.innerHTML = html;
            document.getElementById('log-count').textContent = filteredLogs.length;

            if (autoScroll) {
                container.scrollTop = container.scrollHeight;
            }
        }

        function selectAgent(agentId) {
            selectedAgent = agentId;
            document.querySelectorAll('.agent-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.closest('.agent-item').classList.add('active');
            loadData(); // Refresh logs for selected agent
        }

        function toggleAutoScroll() {
            autoScroll = !autoScroll;
            const btn = document.getElementById('auto-scroll-btn');
            if (autoScroll) {
                btn.textContent = 'Auto-Scroll ON';
                btn.classList.add('auto-scroll');
            } else {
                btn.textContent = 'Auto-Scroll OFF';
                btn.classList.remove('auto-scroll');
            }
        }

        function clearLogs() {
            document.getElementById('log-area').innerHTML = '<div style="text-align: center; color: #666; margin-top: 100px;">🧹 Logs cleared</div>';
        }

        async function loadData() {
            try {
                // Load agents
                const agentsResponse = await fetch('/api/agents');
                const agentsData = await agentsResponse.json();
                updateAgentList(agentsData.agents || []);

                // Load logs
                const logsResponse = await fetch('/api/logs');
                const logsData = await logsResponse.json();
                updateLogs(logsData.logs || []);

            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('log-area').innerHTML =
                    '<div style="text-align: center; color: #ff6b6b; margin-top: 100px;">❌ Error loading logs</div>';
            }
        }

        // Load data immediately
        loadData();

        // Auto-refresh every 2 seconds
        setInterval(loadData, 2000);
    </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_logs_api(self):
        activity = log_data.get_live_activity()
        data = {"logs": activity, "count": len(activity)}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def serve_agents_api(self):
        agents = log_data.get_agent_files()
        data = {"agents": agents[:50], "count": len(agents)}  # Top 50 agents

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def start_server():
    server = HTTPServer(("localhost", 8769), LogViewerHandler)
    print("🔍 Live Agent Log Viewer running on http://localhost:8769")
    print(f"📁 Monitoring {log_data.projects_dir}")
    print(f"📁 Monitoring {log_data.orchestrator_dir}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Log viewer stopped")


if __name__ == "__main__":
    start_server()
