#!/usr/bin/env python3
"""
Simple Unified Agent Monitor - Clean flexbox layout

Simplified approach with reliable layout and real-time updates.
"""

import argparse
import asyncio
import json
import logging
import re
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from aiohttp import WSMsgType, web

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None


class Colors:
    COLORS = ["\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[96m"]
    RESET = "\033[0m"
    BOLD = "\033[1m"
    ROLE_COLORS = {
        "user": "\033[96m👤\033[0m",
        "assistant": "\033[92m🤖\033[0m",
        "tool_use": "\033[94m🔧\033[0m",
        "tool_result": "\033[90m📊\033[0m",
    }
    SWARM_ICONS = ["🐝", "🐜", "🦋", "🐞", "🦗", "🕷️", "🦂", "🐛", "🦟", "🐢"]

    @classmethod
    def get_agent_color(cls, agent_id: str, color_index: int) -> str:
        return cls.COLORS[color_index % len(cls.COLORS)]

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)


class SimpleMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.active_agents = {}
        self.tool_calls = defaultdict(int)
        self.tasks = {"total": 0, "completed": 0, "failed": 0}

    def record_agent_activity(self, agent_id: str, activity_type: str = "activity"):
        current_time = time.time()
        self.active_agents[agent_id] = current_time

    def record_tool_call(self, tool_name: str):
        self.tool_calls[tool_name] += 1

    def get_active_agents_list(self, cutoff_seconds: int = 300) -> List[str]:
        current_time = time.time()
        cutoff_time = current_time - cutoff_seconds
        return [
            agent_id
            for agent_id, last_time in self.active_agents.items()
            if last_time > cutoff_time
        ]

    def get_summary(self) -> dict:
        current_time = time.time()
        runtime = current_time - self.start_time
        active_agents_list = self.get_active_agents_list()

        return {
            "total_tasks": self.tasks["total"],
            "completed_tasks": self.tasks["completed"],
            "failed_tasks": self.tasks["failed"],
            "active_agents": len(active_agents_list),
            "active_tasks": 0,
            "throughput_per_minute": 0.0,
            "error_rate": 0.0,
            "runtime_seconds": runtime,
            "top_tools": dict(
                sorted(self.tool_calls.items(), key=lambda x: x[1], reverse=True)[:8]
            ),
            "active_agents_list": active_agents_list,
        }


class SimpleUnifiedMonitor:
    def __init__(self, pattern="*", dashboard_port=8766):
        self.projects_dir = Path.home() / ".claude" / "projects"
        self.pattern = pattern
        self.dashboard_port = dashboard_port
        self.running = False

        self.agent_colors = {}
        self.agent_positions = {}
        self.swarm_groups = {}
        self.swarm_icons = {}
        self.agent_files = {}
        self.metrics = SimpleMetrics()
        self.color_index = 0

        if AIOHTTP_AVAILABLE:
            self.app = web.Application()
            self.websocket_connections = set()
            self._setup_routes()
        else:
            self.app = None

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _setup_routes(self):
        if not self.app:
            return
        self.app.router.add_get("/", self._serve_dashboard)
        self.app.router.add_get("/api/summary", self._api_summary)
        self.app.router.add_get("/ws", self._websocket_handler)

    async def _serve_dashboard(self, request):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Agent Monitor</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }

        /* Flexbox layout */
        .top-row { display: flex; gap: 20px; margin-bottom: 20px; }
        .metric-card { flex: 1; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .bottom-row { display: flex; gap: 20px; }
        .log-section { flex: 2; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .side-section { flex: 1; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }

        /* Metric styling */
        .metric { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .metric:last-child { border-bottom: none; }
        .metric-value { font-weight: bold; color: #2c3e50; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status-active { background: #27ae60; }
        .status-error { background: #e74c3c; }

        /* Log styling */
        #log { height: 500px; overflow-y: auto; background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 4px;
               font-family: 'Monaco', 'Menlo', monospace; font-size: 12px; line-height: 1.4; white-space: pre-wrap; }
        .log-entry { margin-bottom: 2px; }

        /* Lists */
        .agent-item, .tool-item { padding: 4px; margin: 2px 0; background: #f8f9fa; border-radius: 3px; font-size: 11px; }

        h3 { margin-bottom: 15px; color: #2c3e50; font-size: 16px; }
        h4 { margin-bottom: 10px; color: #666; font-size: 14px; }

        /* Update indicator */
        .update-flash { position: fixed; top: 20px; right: 20px; background: #27ae60; color: white;
                       padding: 8px 12px; border-radius: 4px; font-size: 12px; opacity: 0; transition: opacity 0.3s; }
        .update-flash.show { opacity: 1; }

        /* Responsive */
        @media (max-width: 1200px) {
            .top-row { flex-direction: column; }
            .bottom-row { flex-direction: column; }
            .log-section { order: 2; }
            .side-section { order: 1; }
        }
    </style>
</head>
<body>
    <div class="update-flash" id="update-flash">Updated</div>

    <div class="container">
        <div class="header">
            <h1>🚀 Simple Agent Monitor</h1>
            <p>Real-time monitoring with clean, responsive layout</p>
        </div>

        <div class="top-row">
            <div class="metric-card">
                <h3>📊 System Overview</h3>
                <div class="metric"><span>Active Agents</span><span class="metric-value" id="active-agents">0</span></div>
                <div class="metric"><span>Total Tasks</span><span class="metric-value" id="total-tasks">0</span></div>
                <div class="metric"><span>Completed</span><span class="metric-value" id="completed-tasks">0</span></div>
                <div class="metric"><span>Failed</span><span class="metric-value" id="failed-tasks">0</span></div>
            </div>

            <div class="metric-card">
                <h3>⚡ Performance</h3>
                <div class="metric"><span>Runtime</span><span class="metric-value" id="runtime">0s</span></div>
                <div class="metric"><span>Throughput</span><span class="metric-value" id="throughput">0/min</span></div>
                <div class="metric"><span>Error Rate</span><span class="metric-value" id="error-rate">0%</span></div>
                <div class="metric">
                    <span>Connection</span>
                    <span class="metric-value">
                        <span class="status-indicator status-error" id="status"></span>
                        <span id="connection-status">Connecting...</span>
                    </span>
                </div>
            </div>

            <div class="metric-card">
                <h3>🔧 Top Tools</h3>
                <div id="top-tools" style="max-height: 120px; overflow-y: auto;">Loading...</div>
            </div>
        </div>

        <div class="bottom-row">
            <div class="log-section">
                <h3>📝 Live Activity Stream</h3>
                <div id="log"></div>
            </div>

            <div class="side-section">
                <h3>🤖 Active Agents</h3>
                <div id="agents-list" style="max-height: 200px; overflow-y: auto;">Loading...</div>

                <h4 style="margin-top: 20px;">📈 Activity</h4>
                <div id="activity-summary">No activity yet</div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let logLines = 0;
        const maxLogLines = 150;

        function showUpdate() {
            const flash = document.getElementById('update-flash');
            flash.classList.add('show');
            setTimeout(() => flash.classList.remove('show'), 800);
        }

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('status').className = 'status-indicator status-active';
                log('🟢 Connected to monitor');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };

            ws.onclose = () => {
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('status').className = 'status-indicator status-error';
                log('🔴 Disconnected, reconnecting...');
                setTimeout(connect, 3000);
            };
        }

        function handleMessage(data) {
            if (data.type === 'summary') {
                updateSummary(data.data);
                showUpdate();
            } else if (data.type === 'log_entry') {
                log(data.message);
            }
        }

        function updateSummary(summary) {
            // Update metrics
            document.getElementById('active-agents').textContent = summary.active_agents || 0;
            document.getElementById('total-tasks').textContent = summary.total_tasks || 0;
            document.getElementById('completed-tasks').textContent = summary.completed_tasks || 0;
            document.getElementById('failed-tasks').textContent = summary.failed_tasks || 0;
            document.getElementById('runtime').textContent = Math.floor(summary.runtime_seconds || 0) + 's';
            document.getElementById('throughput').textContent = (summary.throughput_per_minute || 0).toFixed(1) + '/min';
            document.getElementById('error-rate').textContent = ((summary.error_rate || 0) * 100).toFixed(1) + '%';

            // Update agents list
            const agentsList = summary.active_agents_list || [];
            const agentsHtml = agentsList.length > 0
                ? agentsList.map(agent => `<div class="agent-item">${agent}</div>`).join('')
                : '<div style="color: #666; font-style: italic;">No active agents</div>';
            document.getElementById('agents-list').innerHTML = agentsHtml;

            // Update tools
            const topTools = summary.top_tools || {};
            const toolsHtml = Object.entries(topTools).length > 0
                ? Object.entries(topTools).map(([tool, count]) =>
                    `<div class="tool-item">${tool}: <strong>${count}</strong></div>`
                  ).join('')
                : '<div style="color: #666; font-style: italic;">No tools used yet</div>';
            document.getElementById('top-tools').innerHTML = toolsHtml;

            // Update activity summary
            const activitySummary = `${summary.active_agents || 0} agents, ${Object.keys(summary.top_tools || {}).length} tools`;
            document.getElementById('activity-summary').textContent = activitySummary;
        }

        function log(message) {
            const logEl = document.getElementById('log');
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.textContent = message;
            logEl.appendChild(logEntry);

            logLines++;
            if (logLines > maxLogLines) {
                logEl.removeChild(logEl.firstChild);
                logLines--;
            }

            logEl.scrollTop = logEl.scrollHeight;
        }

        // Keep connection alive and request updates
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'ping'}));
            }
        }, 10000);

        // Request summary updates
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'get_summary'}));
            }
        }, 2000);

        connect();
    </script>
</body>
</html>"""
        return web.Response(text=html, content_type="text/html")

    async def _api_summary(self, request):
        try:
            return web.json_response(self.metrics.get_summary())
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websocket_connections.add(ws)

        try:
            # Send initial summary
            summary = self.metrics.get_summary()
            await ws.send_str(json.dumps({"type": "summary", "data": summary}))

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get("type") == "get_summary":
                            summary = self.metrics.get_summary()
                            await ws.send_str(
                                json.dumps({"type": "summary", "data": summary})
                            )
                        elif data.get("type") == "ping":
                            await ws.send_str(json.dumps({"type": "pong"}))
                    except json.JSONDecodeError:
                        pass
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_connections.discard(ws)

        return ws

    def discover_agent_files(self) -> List[Path]:
        if not self.projects_dir.exists():
            return []

        agent_files = []
        cutoff_time = time.time() - 86400

        for project_dir in self.projects_dir.glob(self.pattern):
            if not project_dir.is_dir():
                continue
            for jsonl_file in project_dir.glob("*.jsonl"):
                try:
                    stat = jsonl_file.stat()
                    if stat.st_size > 0 and stat.st_mtime > cutoff_time:
                        agent_files.append(jsonl_file)
                except OSError:
                    continue

        return sorted(agent_files, key=lambda f: f.stat().st_mtime, reverse=True)

    def assign_colors_and_icons(self, agent_files: List[Path]):
        self.color_index = 0
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            self.agent_files[agent_id] = file_path
            color = Colors.get_agent_color(agent_id, self.color_index)
            self.agent_colors[agent_id] = color
            self.color_index += 1

    def format_log_entry(
        self, agent_id: str, entry: Dict, for_dashboard: bool = False
    ) -> Optional[str]:
        try:
            timestamp = entry.get("timestamp", "")
            if timestamp and "T" in timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except ValueError:
                    dt = datetime.fromisoformat(timestamp.split(".")[0])
                    time_str = dt.strftime("%H:%M:%S")
            else:
                time_str = "??:??:??"

            role = entry.get("role", "unknown")
            content = entry.get("content", [])

            # Record activity
            self.metrics.record_agent_activity(agent_id, role)

            # Format agent prefix
            color = self.agent_colors.get(agent_id, "")
            if for_dashboard:
                agent_prefix = f"[{agent_id}]"
                role_icon = {
                    "user": "👤",
                    "assistant": "🤖",
                    "tool_use": "🔧",
                    "tool_result": "📊",
                }.get(role, "❓")
            else:
                agent_prefix = f"{Colors.colorize(f'[{agent_id}]', color)}"
                role_icon = Colors.ROLE_COLORS.get(role, "❓")

            # Process content
            formatted_content = ""
            if isinstance(content, list):
                content_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "unknown_tool")
                            self.metrics.record_tool_call(tool_name)
                            content_parts.append(f"🔧 {tool_name}")
                        elif item.get("type") == "text":
                            text = item.get("text", "")
                            if text.strip():
                                text_clean = text.strip()[:200]
                                content_parts.append(
                                    text_clean
                                    + ("..." if len(text.strip()) > 200 else "")
                                )
                        elif item.get("type") == "tool_result":
                            content_parts.append("📊 result")
                formatted_content = " ".join(content_parts)
            elif isinstance(content, str) and content.strip():
                formatted_content = content.strip()[:200] + (
                    "..." if len(content.strip()) > 200 else ""
                )

            if not formatted_content:
                return None

            result = f"{time_str} {agent_prefix} {role_icon} {formatted_content}"
            if for_dashboard:
                result = Colors.strip_ansi(result)
            return result

        except Exception as e:
            return f"⚠️ Error: {e}"

    async def tail_file(
        self, file_path: Path, agent_id: str, output_queue: asyncio.Queue
    ):
        if agent_id not in self.agent_positions:
            try:
                with open(file_path, "rb") as f:
                    f.seek(0, 2)
                    self.agent_positions[agent_id] = f.tell()
            except (FileNotFoundError, PermissionError):
                self.agent_positions[agent_id] = 0

        position = self.agent_positions[agent_id]

        try:
            while self.running:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        f.seek(0, 2)
                        current_size = f.tell()
                        if position > current_size:
                            position = 0
                        f.seek(position)

                        for line in f:
                            if not line.strip():
                                continue
                            try:
                                entry = json.loads(line.strip())
                                terminal_line = self.format_log_entry(
                                    agent_id, entry, for_dashboard=False
                                )
                                dashboard_line = self.format_log_entry(
                                    agent_id, entry, for_dashboard=True
                                )
                                if terminal_line and dashboard_line:
                                    timestamp = entry.get("timestamp", "")
                                    await output_queue.put(
                                        (timestamp, terminal_line, dashboard_line)
                                    )
                            except json.JSONDecodeError:
                                continue

                        position = f.tell()
                        self.agent_positions[agent_id] = position

                except FileNotFoundError:
                    break
                except PermissionError:
                    break

                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

    async def output_processor(self, output_queue: asyncio.Queue):
        try:
            while self.running:
                try:
                    timestamp, terminal_msg, dashboard_msg = await asyncio.wait_for(
                        output_queue.get(), timeout=0.1
                    )
                    print(terminal_msg, flush=True)

                    if self.websocket_connections:
                        for ws in list(self.websocket_connections):
                            try:
                                await ws.send_str(
                                    json.dumps(
                                        {"type": "log_entry", "message": dashboard_msg}
                                    )
                                )
                            except Exception:
                                self.websocket_connections.discard(ws)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass

    async def broadcast_metrics(self):
        while self.running:
            try:
                if self.websocket_connections:
                    summary = self.metrics.get_summary()
                    message = json.dumps({"type": "summary", "data": summary})
                    for ws in list(self.websocket_connections):
                        try:
                            await ws.send_str(message)
                        except Exception:
                            self.websocket_connections.discard(ws)
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.error(f"Metrics broadcast error: {e}")
                await asyncio.sleep(1)

    async def start_dashboard(self):
        if not self.app:
            return
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, "localhost", self.dashboard_port)
            await site.start()
            self.logger.info(
                f"Dashboard started on http://localhost:{self.dashboard_port}"
            )
            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")

    async def run(self):
        self.running = True

        agent_files = self.discover_agent_files()
        if not agent_files:
            print("❌ No agent files found")
            return

        self.assign_colors_and_icons(agent_files)
        print(f"\n🚀 Simple Agent Monitor Started")
        print(f"📊 Monitoring {len(agent_files)} agents")
        if self.app:
            print(f"🌐 Dashboard: http://localhost:{self.dashboard_port}")
        print("=" * 80)

        output_queue = asyncio.Queue(maxsize=1000)
        tasks = []

        # File tailing
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            tasks.append(
                asyncio.create_task(self.tail_file(file_path, agent_id, output_queue))
            )

        # Output processor
        tasks.append(asyncio.create_task(self.output_processor(output_queue)))

        # Dashboard and metrics
        if self.app:
            tasks.append(asyncio.create_task(self.start_dashboard()))
        tasks.append(asyncio.create_task(self.broadcast_metrics()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            for task in tasks:
                task.cancel()

    def stop(self):
        self.running = False


async def main():
    parser = argparse.ArgumentParser(description="Simple Unified Agent Monitor")
    parser.add_argument("--pattern", default="*", help="Project directory pattern")
    parser.add_argument(
        "--dashboard-port", type=int, default=8766, help="Dashboard port"
    )
    parser.add_argument("--no-dashboard", action="store_true", help="Disable dashboard")
    args = parser.parse_args()

    monitor = SimpleUnifiedMonitor(
        pattern=args.pattern, dashboard_port=args.dashboard_port
    )

    def signal_handler(signum, frame):
        print(f"\n👋 Shutting down...")
        monitor.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await monitor.run()
    except KeyboardInterrupt:
        pass

    print("✅ Monitor stopped.")


if __name__ == "__main__":
    asyncio.run(main())
