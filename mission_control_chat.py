#!/usr/bin/env python3
"""
Mission Control Chat Interface
Comprehensive multi-agent chat with orchestrator status and system monitoring
Designed for accessibility (red/green colorblind friendly) with symbol-based indicators
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

import psutil


class MissionControlData:
    def __init__(self):
        self.projects_dir = Path.home() / ".claude" / "projects"
        self.orchestrator_dir = Path("apps/agent-orchestrator/outputs")

        # Mock orchestrator status (would be real data in production)
        self.orchestrator_status = {
            "current_phase": "EXECUTION",
            "phase_progress": 0.65,
            "total_phases": 4,
            "active_agents": 8,
            "total_agents": 12,
            "tasks_completed": 23,
            "tasks_failed": 2,
            "tasks_in_progress": 5,
            "tokens_used": 145230,
            "tokens_remaining": 854770,
            "time_elapsed": 1847,  # seconds
            "estimated_remaining": 892,
            "retries_attempted": 3,
            "deliverables_generated": 7,
        }

        # Agent types and their symbols
        self.agent_types = {
            "claude": {"symbol": "◆", "name": "Claude"},
            "openai": {"symbol": "●", "name": "OpenAI"},
            "orchestrator": {"symbol": "■", "name": "System"},
            "specialist": {"symbol": "▲", "name": "Specialist"},
        }

        # Mock chat messages
        self.chat_messages = []
        self.last_message_id = 0

    def get_system_metrics(self):
        """Get real system metrics"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "memory_available_gb": round(memory.available / 1024**3, 1),
            "disk_free_gb": round(disk.free / 1024**3, 1),
            "load_average": psutil.getloadavg()[0]
            if hasattr(psutil, "getloadavg")
            else 0,
            "containers": self.get_docker_stats(),
        }

    def get_docker_stats(self):
        """Get Docker container stats via CLI"""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            containers = []
            lines = result.stdout.strip().split("\n")[1:]  # Skip header

            for line in lines[:10]:  # Top 10 containers
                parts = line.split("\t")
                if len(parts) >= 4:
                    name = parts[0]
                    cpu_str = parts[1].replace("%", "")
                    mem_usage = parts[2].split(" / ")[0]
                    mem_perc = parts[3].replace("%", "")

                    containers.append(
                        {
                            "name": name[:15] + "..." if len(name) > 15 else name,
                            "cpu_percent": float(cpu_str) if cpu_str != "--" else 0,
                            "memory_usage": mem_usage,
                            "memory_percent": float(mem_perc)
                            if mem_perc != "--"
                            else 0,
                        }
                    )

            return containers
        except Exception:
            return []

    def get_service_status(self):
        """Check status of various services"""
        services = {
            "knowledge_base": {"status": "healthy", "symbol": "▲", "uptime": "47h 23m"},
            "chat_log_db": {"status": "healthy", "symbol": "▲", "uptime": "47h 23m"},
            "orchestrator": {"status": "active", "symbol": "●", "uptime": "2h 15m"},
            "embedding_service": {
                "status": "degraded",
                "symbol": "◆",
                "uptime": "12h 8m",
            },
            "vector_search": {"status": "healthy", "symbol": "▲", "uptime": "47h 23m"},
            "monitoring": {"status": "healthy", "symbol": "▲", "uptime": "1h 45m"},
        }
        return services

    def get_chat_log_stats(self):
        """Get statistics about chat logs"""
        try:
            total_files = 0
            total_size = 0
            agent_distribution = {
                "claude": 0,
                "openai": 0,
                "system": 0,
                "specialist": 0,
            }

            if self.projects_dir.exists():
                for project_dir in self.projects_dir.glob("*"):
                    if project_dir.is_dir():
                        for jsonl_file in project_dir.glob("*.jsonl"):
                            try:
                                stat = jsonl_file.stat()
                                total_files += 1
                                total_size += stat.st_size
                                # Mock agent type detection
                                agent_type = random.choice(
                                    ["claude", "openai", "system", "specialist"]
                                )
                                agent_distribution[agent_type] += 1
                            except OSError:
                                continue

            return {
                "total_files": total_files,
                "total_size_mb": round(total_size / 1024 / 1024, 1),
                "agent_distribution": agent_distribution,
                "avg_file_size_kb": round(
                    (total_size / total_files / 1024) if total_files > 0 else 0, 1
                ),
            }
        except Exception:
            return {
                "total_files": 0,
                "total_size_mb": 0,
                "agent_distribution": {},
                "avg_file_size_kb": 0,
            }

    def add_chat_message(self, agent_type, agent_id, message):
        """Add a new chat message"""
        self.last_message_id += 1
        self.chat_messages.append(
            {
                "id": self.last_message_id,
                "timestamp": datetime.now().isoformat(),
                "agent_type": agent_type,
                "agent_id": agent_id,
                "message": message,
                "symbol": self.agent_types.get(agent_type, {}).get("symbol", "○"),
            }
        )

        # Keep only last 100 messages
        if len(self.chat_messages) > 100:
            self.chat_messages = self.chat_messages[-100:]

    def simulate_activity(self):
        """Simulate some agent activity for demo"""
        # Add some mock messages
        messages = [
            (
                "claude",
                "claude-001",
                "Task analysis complete. Identified 3 optimization opportunities.",
            ),
            (
                "openai",
                "gpt-4-turbo",
                "Processing user requirements... Estimated completion: 2 minutes.",
            ),
            (
                "orchestrator",
                "sys-coord",
                "Phase 2/4 started: Implementation. Allocating resources to 8 agents.",
            ),
            (
                "specialist",
                "perf-opt",
                "Memory usage optimized. Reduced footprint by 23%.",
            ),
            (
                "claude",
                "claude-002",
                "Generated deliverable: system_architecture_v2.md",
            ),
        ]

        # Randomly add messages
        if random.random() < 0.3:  # 30% chance
            agent_type, agent_id, message = random.choice(messages)
            self.add_chat_message(agent_type, agent_id, message)

        # Update orchestrator progress
        self.orchestrator_status["phase_progress"] = min(
            1.0,
            self.orchestrator_status["phase_progress"] + random.uniform(0.001, 0.01),
        )
        self.orchestrator_status["tokens_used"] += random.randint(10, 100)
        self.orchestrator_status["time_elapsed"] += random.randint(1, 5)

        if random.random() < 0.1:  # 10% chance
            self.orchestrator_status["tasks_completed"] += 1


# Global data store
mission_control = MissionControlData()


class MissionControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.serve_dashboard()
        elif path == "/api/status":
            self.serve_status_api()
        elif path == "/api/chat":
            self.serve_chat_api()
        else:
            self.send_error(404)

    def serve_dashboard(self):
        html = """<!DOCTYPE html>
<html>
<head>
    <title>🚀 Mission Control - Multi-Agent Command Center</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            height: 100vh;
            overflow: hidden;
        }

        .mission-header {
            background: linear-gradient(90deg, #1a1a2e, #16213e, #0f3460);
            padding: 12px 20px;
            border-bottom: 2px solid #00aaff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,170,255,0.2);
        }

        .mission-title {
            font-size: 1.3em;
            font-weight: bold;
            text-shadow: 0 0 10px #00aaff;
        }

        .mission-time {
            font-size: 0.9em;
            opacity: 0.8;
        }

        .main-grid {
            height: calc(100vh - 60px);
            display: grid;
            grid-template-columns: 2fr 1fr;
            grid-template-rows: 1fr 200px;
            gap: 2px;
        }

        .chat-panel {
            background: #111;
            display: flex;
            flex-direction: column;
            border: 1px solid #333;
        }

        .chat-header {
            background: #1a1a1a;
            padding: 10px 15px;
            border-bottom: 1px solid #333;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .active-agents {
            font-size: 0.8em;
            opacity: 0.7;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            line-height: 1.4;
        }

        .message {
            margin-bottom: 12px;
            padding: 8px 12px;
            border-left: 3px solid #333;
            background: rgba(255,255,255,0.02);
            border-radius: 0 6px 6px 0;
            position: relative;
        }

        .message-claude { border-left-color: #00aaff; }
        .message-openai { border-left-color: #ff6b6b; }
        .message-orchestrator { border-left-color: #ffd93d; }
        .message-specialist { border-left-color: #6bcf7f; }

        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            font-size: 0.85em;
        }

        .agent-info {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .agent-symbol {
            font-size: 1.2em;
            font-weight: bold;
        }

        .message-time {
            opacity: 0.5;
            font-size: 0.8em;
        }

        .message-content {
            font-size: 0.95em;
        }

        .status-panel {
            background: #0f0f0f;
            border: 1px solid #333;
            display: flex;
            flex-direction: column;
        }

        .orchestrator-status {
            background: #1a1a1a;
            padding: 15px;
            border-bottom: 1px solid #333;
        }

        .status-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #00aaff;
            font-size: 1.1em;
        }

        .status-row {
            display: flex;
            justify-content: space-between;
            margin: 6px 0;
            font-size: 0.9em;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .phase-progress {
            width: 100%;
            height: 12px;
            background: #333;
            border-radius: 6px;
            overflow: hidden;
            margin: 8px 0;
            position: relative;
        }

        .phase-fill {
            height: 100%;
            background: repeating-linear-gradient(
                90deg,
                #00aaff,
                #00aaff 10px,
                #0088cc 10px,
                #0088cc 20px
            );
            transition: width 0.3s ease;
        }

        .services-grid {
            padding: 15px;
            flex: 1;
            overflow-y: auto;
        }

        .service-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid #222;
            font-size: 0.85em;
        }

        .service-item:last-child {
            border-bottom: none;
        }

        .service-status {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .metrics-panel {
            background: #0f0f0f;
            border: 1px solid #333;
            padding: 15px;
            grid-column: 1 / -1;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            height: 100%;
        }

        .metric-card {
            background: #1a1a1a;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #333;
        }

        .metric-title {
            font-size: 0.9em;
            margin-bottom: 8px;
            opacity: 0.8;
        }

        .metric-value {
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 4px;
        }

        .metric-bar {
            width: 100%;
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
        }

        .metric-fill {
            height: 100%;
            transition: width 0.3s ease;
        }

        .metric-fill-low { background: #6bcf7f; }
        .metric-fill-med { background: #ffd93d; }
        .metric-fill-high { background: #ff6b6b; }

        .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }

        .chat-input {
            border-top: 1px solid #333;
            padding: 10px;
            background: #1a1a1a;
        }

        .input-box {
            width: 100%;
            background: #333;
            border: 1px solid #555;
            color: #fff;
            padding: 8px 12px;
            border-radius: 4px;
            font-family: inherit;
            font-size: 0.9em;
        }

        .input-box:focus {
            outline: none;
            border-color: #00aaff;
            box-shadow: 0 0 5px rgba(0,170,255,0.3);
        }

        .symbol-legend {
            position: fixed;
            top: 70px;
            right: 10px;
            background: rgba(0,0,0,0.9);
            border: 1px solid #333;
            border-radius: 4px;
            padding: 8px;
            font-size: 0.7em;
            opacity: 0.7;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 4px;
            margin: 2px 0;
        }
    </style>
</head>
<body>
    <div class="mission-header">
        <div class="mission-title">🚀 MISSION CONTROL - Multi-Agent Command Center</div>
        <div class="mission-time" id="mission-time">Loading...</div>
    </div>

    <div class="symbol-legend">
        <div class="legend-item"><span>◆</span> Claude</div>
        <div class="legend-item"><span>●</span> OpenAI</div>
        <div class="legend-item"><span>■</span> System</div>
        <div class="legend-item"><span>▲</span> Specialist</div>
        <div class="legend-item"><span>▲</span> Healthy</div>
        <div class="legend-item"><span>◆</span> Degraded</div>
        <div class="legend-item"><span>▼</span> Critical</div>
    </div>

    <div class="main-grid">
        <div class="chat-panel">
            <div class="chat-header">
                <span>💬 Agent Communication Stream</span>
                <span class="active-agents" id="active-agents">8 agents online</span>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div style="text-align: center; padding: 40px; opacity: 0.5;">
                    Waiting for agent communications...
                </div>
            </div>
            <div class="chat-input">
                <input type="text" class="input-box" placeholder="Send message to all agents..." id="message-input">
            </div>
        </div>

        <div class="status-panel">
            <div class="orchestrator-status">
                <div class="status-title">🎯 Orchestrator Status</div>
                <div class="status-row">
                    <span>Phase:</span>
                    <span id="current-phase">EXECUTION (2/4)</span>
                </div>
                <div class="phase-progress">
                    <div class="phase-fill" id="phase-fill" style="width: 65%"></div>
                </div>
                <div class="status-row">
                    <span>Active Agents:</span>
                    <span id="active-count">8/12</span>
                </div>
                <div class="status-row">
                    <span>Tasks:</span>
                    <span id="task-status">●●●●● ◆◆ ○○○</span>
                </div>
                <div class="status-row">
                    <span>Tokens:</span>
                    <span id="token-usage">145K/1M (14%)</span>
                </div>
                <div class="status-row">
                    <span>Runtime:</span>
                    <span id="runtime">30m 47s</span>
                </div>
                <div class="status-row">
                    <span>Deliverables:</span>
                    <span id="deliverables">7 generated</span>
                </div>
            </div>

            <div class="services-grid">
                <div class="status-title">⚙️ Service Health</div>
                <div id="services-list">Loading...</div>
            </div>
        </div>

        <div class="metrics-panel">
            <div class="metrics-grid" id="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">CPU Usage</div>
                    <div class="metric-value" id="cpu-value">0%</div>
                    <div class="metric-bar">
                        <div class="metric-fill metric-fill-low" id="cpu-bar"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Memory Usage</div>
                    <div class="metric-value" id="memory-value">0%</div>
                    <div class="metric-bar">
                        <div class="metric-fill metric-fill-low" id="memory-bar"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">🐳 Containers</div>
                    <div class="metric-value" id="containers-count">0</div>
                    <div id="containers-list" style="font-size: 0.7em; margin-top: 5px; max-height: 100px; overflow-y: auto;"></div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Agent Distribution</div>
                    <div class="metric-value" id="agent-dist">◆●■▲</div>
                    <div style="font-size: 0.8em; opacity: 0.7;" id="agent-counts">0/0/0/0</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function formatTime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            if (hours > 0) {
                return `${hours}h ${minutes}m ${secs}s`;
            } else {
                return `${minutes}m ${secs}s`;
            }
        }

        function formatTokens(used, total) {
            const usedK = Math.floor(used / 1000);
            const totalK = Math.floor(total / 1000);
            const percent = Math.floor((used / total) * 100);
            return `${usedK}K/${totalK}K (${percent}%)`;
        }

        function renderTaskStatus(completed, failed, inProgress) {
            let symbols = '';
            // Completed tasks (solid circles)
            symbols += '●'.repeat(Math.min(completed, 10));
            // Failed tasks (diamonds)
            symbols += '◆'.repeat(Math.min(failed, 5));
            // In progress (triangles)
            symbols += '▲'.repeat(Math.min(inProgress, 5));
            return symbols || '○○○';
        }

        function updateChat(messages) {
            const container = document.getElementById('chat-messages');

            if (!messages.length) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; opacity: 0.5;">Waiting for agent communications...</div>';
                return;
            }

            const html = messages.map(msg => `
                <div class="message message-${msg.agent_type}">
                    <div class="message-header">
                        <div class="agent-info">
                            <span class="agent-symbol">${msg.symbol}</span>
                            <span>${msg.agent_id}</span>
                        </div>
                        <span class="message-time">${new Date(msg.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div class="message-content">${msg.message}</div>
                </div>
            `).join('');

            container.innerHTML = html;
            container.scrollTop = container.scrollHeight;
        }

        function updateMetrics(data) {
            const metrics = data.system_metrics;

            // CPU
            document.getElementById('cpu-value').textContent = metrics.cpu_usage.toFixed(1) + '%';
            document.getElementById('cpu-bar').style.width = metrics.cpu_usage + '%';
            document.getElementById('cpu-bar').className = 'metric-fill ' +
                (metrics.cpu_usage > 80 ? 'metric-fill-high' :
                 metrics.cpu_usage > 60 ? 'metric-fill-med' : 'metric-fill-low');

            // Memory
            document.getElementById('memory-value').textContent = metrics.memory_usage.toFixed(1) + '%';
            document.getElementById('memory-bar').style.width = metrics.memory_usage + '%';
            document.getElementById('memory-bar').className = 'metric-fill ' +
                (metrics.memory_usage > 85 ? 'metric-fill-high' :
                 metrics.memory_usage > 70 ? 'metric-fill-med' : 'metric-fill-low');

            // Containers
            const containers = metrics.containers || [];
            document.getElementById('containers-count').textContent = containers.length;
            const containerHtml = containers.map(c =>
                `<div style="margin: 2px 0; opacity: ${c.cpu_percent > 5 ? '1' : '0.6'};">
                    <div style="font-weight: bold;">${c.name}</div>
                    <div>CPU: ${c.cpu_percent}% | Mem: ${c.memory_usage}</div>
                </div>`
            ).join('');
            document.getElementById('containers-list').innerHTML = containerHtml || 'No containers';

            // Agent distribution
            const dist = data.chat_stats.agent_distribution;
            document.getElementById('agent-dist').textContent = '◆●■▲';
            document.getElementById('agent-counts').textContent =
                `${dist.claude}/${dist.openai}/${dist.system}/${dist.specialist}`;
        }

        function updateServices(services) {
            const container = document.getElementById('services-list');
            const html = Object.entries(services).map(([name, info]) => `
                <div class="service-item">
                    <span>${name.replace('_', ' ')}</span>
                    <div class="service-status">
                        <span class="${info.status === 'healthy' ? 'pulse' : ''}">${info.symbol}</span>
                        <span style="font-size: 0.8em; opacity: 0.7;">${info.uptime}</span>
                    </div>
                </div>
            `).join('');
            container.innerHTML = html;
        }

        function updateOrchestrator(status) {
            // Phase
            document.getElementById('current-phase').textContent =
                `${status.current_phase} (${Math.ceil(status.phase_progress * status.total_phases)}/${status.total_phases})`;

            // Progress bar
            document.getElementById('phase-fill').style.width = (status.phase_progress * 100) + '%';

            // Active agents
            document.getElementById('active-count').textContent = `${status.active_agents}/${status.total_agents}`;

            // Task status with symbols
            document.getElementById('task-status').textContent =
                renderTaskStatus(status.tasks_completed, status.tasks_failed, status.tasks_in_progress);

            // Tokens
            document.getElementById('token-usage').textContent =
                formatTokens(status.tokens_used, status.tokens_used + status.tokens_remaining);

            // Runtime
            document.getElementById('runtime').textContent = formatTime(status.time_elapsed);

            // Deliverables
            document.getElementById('deliverables').textContent = `${status.deliverables_generated} generated`;
        }

        async function loadData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                updateOrchestrator(data.orchestrator_status);
                updateServices(data.services);
                updateMetrics(data);

                const chatResponse = await fetch('/api/chat');
                const chatData = await chatResponse.json();
                updateChat(chatData.messages || []);

                document.getElementById('active-agents').textContent = `${data.orchestrator_status.active_agents} agents online`;

            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        // Update mission time
        function updateMissionTime() {
            document.getElementById('mission-time').textContent =
                `Mission Time: ${new Date().toLocaleTimeString()} - ${new Date().toLocaleDateString()}`;
        }

        // Message input handling
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const message = this.value.trim();
                if (message) {
                    // In a real implementation, this would send to the backend
                    console.log('User message:', message);
                    this.value = '';
                }
            }
        });

        // Initialize
        updateMissionTime();
        setInterval(updateMissionTime, 1000);

        loadData();
        setInterval(loadData, 2000); // Update every 2 seconds
    </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_status_api(self):
        # Simulate activity
        mission_control.simulate_activity()

        data = {
            "orchestrator_status": mission_control.orchestrator_status,
            "system_metrics": mission_control.get_system_metrics(),
            "services": mission_control.get_service_status(),
            "chat_stats": mission_control.get_chat_log_stats(),
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def serve_chat_api(self):
        data = {
            "messages": mission_control.chat_messages[-50:],  # Last 50 messages
            "count": len(mission_control.chat_messages),
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def start_server():
    server = HTTPServer(("localhost", 8770), MissionControlHandler)
    print("🚀 Mission Control Chat Interface running on http://localhost:8770")
    print("🎯 Multi-agent command center with orchestrator monitoring")
    print("♿ Accessibility: Red/green colorblind friendly with symbols")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Mission Control shutting down...")


if __name__ == "__main__":
    start_server()
