#!/usr/bin/env python3
"""
Debug version to test specific issues
"""

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
    SWARM_ICONS = ["🐝", "🐜", "🦋", "🐞", "🦗"]

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)


class SimpleMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.active_agents = set()
        self.agent_last_seen = {}
        self.tool_calls = defaultdict(int)

    def record_agent_activity(self, agent_id: str):
        self.active_agents.add(agent_id)
        self.agent_last_seen[agent_id] = time.time()
        print(f"DEBUG: Recorded activity for agent {agent_id}")

    def record_tool_call(self, tool_name: str):
        self.tool_calls[tool_name] += 1
        print(f"DEBUG: Recorded tool call: {tool_name}")

    def get_summary(self):
        current_time = time.time()
        active_cutoff = current_time - 300  # 5 minutes

        active_agents_list = [
            agent
            for agent, last_seen in self.agent_last_seen.items()
            if last_seen > active_cutoff
        ]

        summary = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_agents": len(active_agents_list),
            "active_tasks": 0,
            "throughput_per_minute": 0.0,
            "error_rate": 0.0,
            "runtime_seconds": current_time - self.start_time,
            "top_tools": dict(list(self.tool_calls.items())[:5]),
            "active_agents_list": active_agents_list,
        }

        print(
            f"DEBUG: Summary - Active agents: {len(active_agents_list)}, Tool calls: {len(self.tool_calls)}"
        )
        return summary


class DebugMonitor:
    def __init__(self, pattern="*", dashboard_port=8766):
        self.projects_dir = Path.home() / ".claude" / "projects"
        self.pattern = pattern
        self.dashboard_port = dashboard_port
        self.running = False
        self.metrics = SimpleMetrics()
        self.agent_positions = {}
        self.agent_files = {}
        self.websocket_connections = set()

        if AIOHTTP_AVAILABLE:
            self.app = web.Application()
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
<html>
<head>
    <title>Debug Monitor</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        .card { border: 1px solid #ccc; margin: 10px; padding: 15px; }
        #log { height: 200px; overflow-y: scroll; background: #f0f0f0; padding: 10px; }
    </style>
</head>
<body>
    <h1>Debug Agent Monitor</h1>
    <div class="card">
        <h3>Status</h3>
        <div>Active Agents: <span id="active-agents">0</span></div>
        <div>Runtime: <span id="runtime">0</span>s</div>
        <div>Connection: <span id="connection">Connecting...</span></div>
    </div>
    <div class="card">
        <h3>Agent List</h3>
        <div id="agents-list">Loading...</div>
    </div>
    <div class="card">
        <h3>Tools</h3>
        <div id="tools">Loading...</div>
    </div>
    <div class="card">
        <h3>Live Log</h3>
        <div id="log"></div>
    </div>

    <script>
        let ws = null;

        function connect() {
            const wsUrl = `ws://${window.location.host}/ws`;
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                document.getElementById('connection').textContent = 'Connected';
                console.log('WebSocket connected');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Received:', data);
                handleMessage(data);
            };

            ws.onclose = () => {
                document.getElementById('connection').textContent = 'Disconnected';
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(connect, 3000);
            };
        }

        function handleMessage(data) {
            if (data.type === 'summary') {
                updateSummary(data.data);
            } else if (data.type === 'log_entry') {
                log(data.message);
            }
        }

        function updateSummary(summary) {
            console.log('Updating summary:', summary);
            document.getElementById('active-agents').textContent = summary.active_agents || 0;
            document.getElementById('runtime').textContent = Math.floor(summary.runtime_seconds || 0);

            // Update agents list
            const agentsList = summary.active_agents_list || [];
            document.getElementById('agents-list').innerHTML =
                agentsList.length > 0 ? agentsList.join(', ') : 'No active agents';

            // Update tools
            const tools = summary.top_tools || {};
            const toolsHtml = Object.entries(tools)
                .map(([tool, count]) => `${tool}: ${count}`)
                .join(', ');
            document.getElementById('tools').innerHTML = toolsHtml || 'No tools used';
        }

        function log(message) {
            const logEl = document.getElementById('log');
            logEl.innerHTML += message + '\\n';
            logEl.scrollTop = logEl.scrollHeight;
        }

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
            summary = self.metrics.get_summary()
            return web.json_response(summary)
        except Exception as e:
            self.logger.error(f"API error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websocket_connections.add(ws)
        self.logger.info("WebSocket client connected")

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
                    except json.JSONDecodeError:
                        pass
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")

        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_connections.discard(ws)
            self.logger.info("WebSocket client disconnected")

        return ws

    def discover_agent_files(self):
        """Find agent log files"""
        if not self.projects_dir.exists():
            print(f"Projects directory not found: {self.projects_dir}")
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
                        print(f"DEBUG: Found agent file: {jsonl_file}")
                except OSError:
                    continue

        print(f"DEBUG: Total agent files found: {len(agent_files)}")
        return agent_files

    async def tail_file(
        self, file_path: Path, agent_id: str, output_queue: asyncio.Queue
    ):
        """Tail a single file"""
        print(f"DEBUG: Starting tail for agent {agent_id}: {file_path}")

        if agent_id not in self.agent_positions:
            try:
                with open(file_path, "rb") as f:
                    f.seek(0, 2)
                    self.agent_positions[agent_id] = f.tell()
                    print(f"DEBUG: Starting at end of file for {agent_id}")
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
                            print(f"DEBUG: File rotated for {agent_id}")
                            position = 0

                        f.seek(position)
                        new_lines = 0

                        for line in f:
                            if not line.strip():
                                continue

                            try:
                                entry = json.loads(line.strip())

                                # Record agent activity
                                self.metrics.record_agent_activity(agent_id)

                                # Check for tool calls
                                content = entry.get("content", [])
                                if isinstance(content, list):
                                    for item in content:
                                        if (
                                            isinstance(item, dict)
                                            and item.get("type") == "tool_use"
                                        ):
                                            tool_name = item.get("name", "unknown")
                                            self.metrics.record_tool_call(tool_name)

                                # Format message
                                timestamp = entry.get("timestamp", "")
                                role = entry.get("role", "unknown")
                                message = (
                                    f"[{agent_id}] {role}: {str(content)[:100]}..."
                                )

                                await output_queue.put((timestamp, message))
                                new_lines += 1

                            except json.JSONDecodeError:
                                continue

                        position = f.tell()
                        self.agent_positions[agent_id] = position

                        if new_lines > 0:
                            print(f"DEBUG: Processed {new_lines} lines for {agent_id}")

                except FileNotFoundError:
                    print(f"DEBUG: File deleted for {agent_id}")
                    break
                except PermissionError:
                    print(f"DEBUG: Permission denied for {agent_id}")
                    break

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            print(f"DEBUG: Tail cancelled for {agent_id}")

    async def output_processor(self, output_queue: asyncio.Queue):
        """Process output and broadcast"""
        while self.running:
            try:
                timestamp, message = await asyncio.wait_for(
                    output_queue.get(), timeout=0.1
                )
                print(f"TERMINAL: {message}")

                # Broadcast to dashboard
                if self.websocket_connections:
                    clean_message = Colors.strip_ansi(message)
                    for ws in list(self.websocket_connections):
                        try:
                            await ws.send_str(
                                json.dumps(
                                    {"type": "log_entry", "message": clean_message}
                                )
                            )
                        except Exception:
                            self.websocket_connections.discard(ws)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Output processor error: {e}")

    async def broadcast_metrics(self):
        """Broadcast metrics periodically"""
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

                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Metrics broadcast error: {e}")
                await asyncio.sleep(1)

    async def start_dashboard(self):
        """Start dashboard server"""
        if not self.app:
            return

        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, "localhost", self.dashboard_port)
            await site.start()
            print(f"DEBUG: Dashboard started on http://localhost:{self.dashboard_port}")

            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")

    async def run(self):
        """Main run method"""
        self.running = True

        # Discover files
        agent_files = self.discover_agent_files()
        if not agent_files:
            print("No agent files found")
            return

        print(f"Monitoring {len(agent_files)} agent files")
        if self.app:
            print(f"Dashboard: http://localhost:{self.dashboard_port}")

        # Create queue and tasks
        output_queue = asyncio.Queue(maxsize=1000)

        tasks = []

        # File tailing tasks
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            self.agent_files[agent_id] = file_path
            task = asyncio.create_task(
                self.tail_file(file_path, agent_id, output_queue)
            )
            tasks.append(task)

        # Output processor
        tasks.append(asyncio.create_task(self.output_processor(output_queue)))

        # Dashboard
        if self.app:
            tasks.append(asyncio.create_task(self.start_dashboard()))

        # Metrics broadcaster
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
    monitor = DebugMonitor(pattern="*", dashboard_port=8766)

    def signal_handler(signum, frame):
        print(f"\nShutting down debug monitor...")
        monitor.stop()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        await monitor.run()
    except KeyboardInterrupt:
        pass

    print("Debug monitor stopped.")


if __name__ == "__main__":
    asyncio.run(main())
