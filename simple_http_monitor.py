#!/usr/bin/env python3
"""
Simple HTTP-based monitor (no WebSockets)
"""

import json
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse


class MonitorData:
    def __init__(self):
        self.counter = 0
        self.last_update = time.time()
        self.projects_dir = Path.home() / ".claude" / "projects"
        self.orchestrator_dir = Path("apps/agent-orchestrator/outputs")

    def get_data(self):
        self.counter += 1
        files_found = self._count_files()
        orchestrator_files = self._count_orchestrator_files()
        active_sessions = self._get_active_sessions()
        recent_activity = self._get_recent_activity()

        return {
            "counter": self.counter,
            "timestamp": time.strftime("%H:%M:%S"),
            "files_found": files_found,
            "orchestrator_files": orchestrator_files,
            "total_files": files_found + orchestrator_files,
            "active_sessions": len(active_sessions),
            "recent_activity": recent_activity,
            "last_update": self.last_update,
            "projects_dir": str(self.projects_dir),
            "orchestrator_dir": str(self.orchestrator_dir),
            "session_details": active_sessions[:5],  # Top 5 sessions
        }

    def _count_files(self):
        if not self.projects_dir.exists():
            return 0

        count = 0
        cutoff_time = time.time() - 86400

        for project_dir in self.projects_dir.glob("*"):
            if not project_dir.is_dir():
                continue
            for jsonl_file in project_dir.glob("*.jsonl"):
                try:
                    stat = jsonl_file.stat()
                    if stat.st_size > 0 and stat.st_mtime > cutoff_time:
                        count += 1
                except OSError:
                    continue
        return count

    def _count_orchestrator_files(self):
        if not self.orchestrator_dir.exists():
            return 0

        count = 0
        cutoff_time = time.time() - 86400

        for file_path in self.orchestrator_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".json", ".log", ".jsonl"]:
                try:
                    stat = file_path.stat()
                    if stat.st_size > 0 and stat.st_mtime > cutoff_time:
                        count += 1
                except OSError:
                    continue
        return count


# Global data store
monitor_data = MonitorData()


class MonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.serve_dashboard()
        elif path == "/api/data":
            self.serve_api()
        else:
            self.send_error(404)

    def serve_dashboard(self):
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Agent Activity Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #333;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(45deg, #00ff88, #00aaff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(0,255,136,0.3);
            margin-bottom: 10px;
        }

        .header .subtitle {
            color: #888;
            font-size: 1.1em;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: rgba(0,0,0,0.4);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid #333;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: #00ff88;
            box-shadow: 0 8px 32px rgba(0,255,136,0.2);
            transform: translateY(-2px);
        }

        .card h3 {
            color: #00ff88;
            font-size: 1.4em;
            margin-bottom: 20px;
            text-align: center;
            text-shadow: 0 0 10px rgba(0,255,136,0.3);
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 15px 0;
            padding: 10px 0;
            border-bottom: 1px solid #333;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            color: #aaa;
            font-size: 0.95em;
        }

        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #00aaff;
            text-shadow: 0 0 8px rgba(0,170,255,0.4);
        }

        .big-metric {
            text-align: center;
            margin: 20px 0;
        }

        .big-metric .value {
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(45deg, #ff6b6b, #ffa500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(255,107,107,0.3);
            display: block;
        }

        .big-metric .label {
            color: #888;
            font-size: 0.9em;
            margin-top: 10px;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #00ff88;
            box-shadow: 0 0 10px #00ff88;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 10px #00ff88; }
            50% { box-shadow: 0 0 20px #00ff88, 0 0 30px #00ff88; }
            100% { box-shadow: 0 0 10px #00ff88; }
        }

        .auto-refresh {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }

        .connection-status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Agent Swarm Monitor</h1>
        <div class="subtitle">Real-time activity tracking across all agents</div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>🎯 Activity Overview</h3>
            <div class="connection-status">
                <span class="status-indicator"></span>
                <span>Live Updates Active</span>
            </div>
            <div class="big-metric">
                <span id="counter" class="value">Loading...</span>
                <div class="label">Update Cycles</div>
            </div>
            <div class="auto-refresh">Refreshes every 3 seconds</div>
        </div>

        <div class="card">
            <h3>📁 File Activity</h3>
            <div class="metric">
                <span class="metric-label">Claude Projects</span>
                <span id="files" class="metric-value">Loading...</span>
            </div>
            <div class="metric">
                <span class="metric-label">Orchestrator Output</span>
                <span id="orchestrator" class="metric-value">Loading...</span>
            </div>
            <div class="big-metric" style="margin-top: 25px;">
                <span id="total" class="value" style="font-size: 2.5em;">Loading...</span>
                <div class="label">Total Active Files</div>
            </div>
        </div>

        <div class="card">
            <h3>⏰ System Status</h3>
            <div class="metric">
                <span class="metric-label">Last Update</span>
                <span id="timestamp" class="metric-value">Loading...</span>
            </div>
            <div class="metric">
                <span class="metric-label">Monitor Status</span>
                <span class="metric-value">🟢 Online</span>
            </div>
            <div class="metric">
                <span class="metric-label">Data Sources</span>
                <span class="metric-value">2 Active</span>
            </div>
        </div>
    </div>

    <script>
        function updateData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('counter').textContent = data.counter;
                    document.getElementById('files').textContent = data.files_found;
                    document.getElementById('orchestrator').textContent = data.orchestrator_files;
                    document.getElementById('total').textContent = data.total_files;
                    document.getElementById('timestamp').textContent = data.timestamp;
                    console.log('Updated:', data);
                })
                .catch(error => {
                    console.error('Update failed:', error);
                    document.getElementById('counter').textContent = 'ERROR';
                });
        }

        // Update immediately
        updateData();

        // Auto-refresh every 3 seconds
        setInterval(updateData, 3000);
    </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_api(self):
        data = monitor_data.get_data()
        print(
            f"📡 API called - Counter: {data['counter']}, Claude: {data['files_found']}, Orchestrator: {data['orchestrator_files']}, Total: {data['total_files']}"
        )

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def start_server():
    server = HTTPServer(("localhost", 8765), MonitorHandler)
    print("🌐 HTTP Monitor running on http://localhost:8765")
    print("📂 Projects directory:", monitor_data.projects_dir)
    print("🔍 Initial file count:", monitor_data._count_files())

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")


if __name__ == "__main__":
    start_server()
