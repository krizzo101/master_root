#!/usr/bin/env python3
"""
Enhanced Unified Agent Monitor - With Real-time Output Updates

Enhanced features:
- Real-time streaming output to dashboard
- Better update frequency and responsiveness
- Enhanced WebSocket communication
- Live agent status updates
- Real-time tool usage tracking
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
    """ANSI color codes for terminal output"""

    COLORS = [
        "\033[91m",
        "\033[92m",
        "\033[93m",
        "\033[94m",
        "\033[95m",
        "\033[96m",
        "\033[31m",
        "\033[32m",
        "\033[33m",
        "\033[34m",
        "\033[35m",
        "\033[36m",
        "\033[97m",
        "\033[90m",
    ]
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

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


class EnhancedMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.active_agents = {}  # agent_id -> last_activity_time
        self.tool_calls = defaultdict(int)
        self.tasks = {"total": 0, "completed": 0, "failed": 0, "active": 0}
        self.activity_log = []
        self.throughput_history = []

    def record_agent_activity(self, agent_id: str, activity_type: str = "activity"):
        """Record agent activity with timestamp"""
        current_time = time.time()
        self.active_agents[agent_id] = current_time

        # Debug print
        print(
            f"DEBUG: Recording activity for agent {agent_id}, total active: {len(self.active_agents)}"
        )

        # Add to activity log for dashboard
        self.activity_log.append(
            {"timestamp": current_time, "agent_id": agent_id, "activity": activity_type}
        )

        # Keep only last 100 activities
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[-100:]

    def record_tool_call(self, tool_name: str):
        """Record tool usage"""
        self.tool_calls[tool_name] += 1

    def get_active_agents(self, cutoff_seconds: int = 300) -> List[str]:
        """Get list of agents active within cutoff_seconds"""
        current_time = time.time()
        cutoff_time = current_time - cutoff_seconds
        return [
            agent_id
            for agent_id, last_time in self.active_agents.items()
            if last_time > cutoff_time
        ]

    def get_summary(self) -> dict:
        """Get comprehensive metrics summary"""
        current_time = time.time()
        runtime = current_time - self.start_time
        active_agents_list = self.get_active_agents()

        # Calculate throughput
        recent_history = [
            h for h in self.throughput_history if h["timestamp"] > (current_time - 300)
        ]

        throughput = 0
        if len(recent_history) > 1:
            time_span = recent_history[-1]["timestamp"] - recent_history[0]["timestamp"]
            task_diff = recent_history[-1]["completed"] - recent_history[0]["completed"]
            if time_span > 0:
                throughput = (task_diff / time_span) * 60

        error_rate = 0
        if self.tasks["total"] > 0:
            error_rate = self.tasks["failed"] / self.tasks["total"]

        return {
            "total_tasks": self.tasks["total"],
            "completed_tasks": self.tasks["completed"],
            "failed_tasks": self.tasks["failed"],
            "active_agents": len(active_agents_list),
            "active_tasks": self.tasks["active"],
            "throughput_per_minute": throughput,
            "error_rate": error_rate,
            "runtime_seconds": runtime,
            "top_tools": dict(
                sorted(self.tool_calls.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "active_agents_list": active_agents_list,
            "recent_activity": self.activity_log[-10:],  # Last 10 activities
            "last_updated": current_time,
        }


class EnhancedUnifiedMonitor:
    def __init__(
        self,
        projects_dir: str = None,
        pattern: str = "*",
        dashboard_port: int = 8766,
        max_content_length: int = 500,
        show_tool_params: bool = True,
        enable_dashboard: bool = True,
    ):
        self.projects_dir = Path(projects_dir or Path.home() / ".claude" / "projects")
        self.pattern = pattern
        self.dashboard_port = dashboard_port
        self.max_content_length = max_content_length
        self.show_tool_params = show_tool_params
        self.enable_dashboard = enable_dashboard

        # Agent management
        self.agent_colors = {}
        self.agent_positions = {}
        self.swarm_groups = {}
        self.swarm_icons = {}
        self.agent_files = {}

        # Enhanced metrics
        self.metrics = EnhancedMetrics()
        self.running = False
        self.color_index = 0

        # Dashboard components
        if self.enable_dashboard and AIOHTTP_AVAILABLE:
            self.app = web.Application()
            self.websocket_connections = set()
            self._setup_dashboard_routes()
        else:
            self.app = None

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def discover_agent_files(self) -> List[Path]:
        """Discover active agent log files"""
        if not self.projects_dir.exists():
            self.logger.warning(f"Projects directory not found: {self.projects_dir}")
            return []

        agent_files = []
        cutoff_time = time.time() - 86400  # 24 hours

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

    def detect_swarms(self, agent_files: List[Path]) -> Dict[str, List[str]]:
        """Detect agent swarms"""
        swarms = defaultdict(list)
        project_groups = defaultdict(list)

        for file_path in agent_files:
            project_dir = file_path.parent.name
            agent_id = file_path.stem[-8:]
            project_groups[project_dir].append((agent_id, file_path))

        swarm_id = 0
        for project_dir, agents in project_groups.items():
            if len(agents) > 1:
                timestamps = []
                for agent_id, file_path in agents:
                    try:
                        timestamps.append(file_path.stat().st_ctime)
                    except OSError:
                        continue
                if timestamps:
                    timestamps.sort()
                    if timestamps[-1] - timestamps[0] <= 300:  # 5 minutes
                        swarms[f"swarm_{swarm_id}"] = [
                            agent_id for agent_id, _ in agents
                        ]
                        swarm_id += 1

        return dict(swarms)

    def assign_colors_and_icons(
        self, agent_files: List[Path], swarms: Dict[str, List[str]]
    ):
        """Assign colors and icons to agents"""
        self.agent_colors.clear()
        self.swarm_groups.clear()
        self.swarm_icons.clear()
        self.agent_files.clear()

        # Swarm mapping
        agent_to_swarm = {}
        for swarm_id, agent_list in swarms.items():
            for agent_id in agent_list:
                agent_to_swarm[agent_id] = swarm_id

        # Assign swarm icons
        for i, swarm_id in enumerate(swarms.keys()):
            self.swarm_icons[swarm_id] = Colors.SWARM_ICONS[i % len(Colors.SWARM_ICONS)]

        # Assign colors to agents
        self.color_index = 0
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            self.agent_files[agent_id] = file_path

            color = Colors.get_agent_color(agent_id, self.color_index)
            self.agent_colors[agent_id] = color
            self.color_index += 1

            if agent_id in agent_to_swarm:
                self.swarm_groups[agent_id] = agent_to_swarm[agent_id]

    def format_log_entry(
        self, agent_id: str, entry: Dict, for_dashboard: bool = False
    ) -> Optional[str]:
        """Format log entry for display"""
        try:
            # Extract timestamp
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

            # Extract content
            role = entry.get("role", "unknown")
            content = entry.get("content", [])

            # Format agent prefix
            color = self.agent_colors.get(agent_id, "")
            swarm_icon = ""
            if agent_id in self.swarm_groups:
                swarm_id = self.swarm_groups[agent_id]
                swarm_icon = self.swarm_icons.get(swarm_id, "") + " "

            if for_dashboard:
                agent_prefix = f"{swarm_icon}[{agent_id}]"
                role_icon = {
                    "user": "👤",
                    "assistant": "🤖",
                    "tool_use": "🔧",
                    "tool_result": "📊",
                }.get(role, "❓")
            else:
                agent_prefix = f"{swarm_icon}{Colors.colorize(f'[{agent_id}]', color)}"
                role_icon = Colors.ROLE_COLORS.get(role, "❓")

            # Record activity
            self.metrics.record_agent_activity(agent_id, role)

            # Process content
            formatted_content = ""
            if isinstance(content, list):
                content_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "unknown_tool")
                            self.metrics.record_tool_call(tool_name)

                            if self.show_tool_params:
                                tool_input = item.get("input", {})
                                if tool_name == "Write":
                                    file_path = tool_input.get("file_path", "")
                                    filename = (
                                        file_path.split("/")[-1]
                                        if file_path
                                        else "unnamed"
                                    )
                                    content_parts.append(f"🔧 Write → {filename}")
                                elif tool_name == "Read":
                                    file_path = tool_input.get("file_path", "")
                                    filename = (
                                        file_path.split("/")[-1]
                                        if file_path
                                        else "unnamed"
                                    )
                                    content_parts.append(f"🔧 Read → {filename}")
                                elif tool_name == "Bash":
                                    command = tool_input.get("command", "")[:50]
                                    content_parts.append(
                                        f"🔧 Bash → {command}{'...' if len(tool_input.get('command', '')) > 50 else ''}"
                                    )
                                else:
                                    content_parts.append(f"🔧 {tool_name}")
                            else:
                                content_parts.append(f"🔧 {tool_name}")

                        elif item.get("type") == "text":
                            text = item.get("text", "")
                            if text.strip():
                                text_clean = text.strip()
                                if len(text_clean) > self.max_content_length:
                                    content_parts.append(
                                        f"{text_clean[:self.max_content_length]}..."
                                    )
                                else:
                                    content_parts.append(text_clean)

                        elif item.get("type") == "tool_result":
                            result_content = item.get("content", "")
                            if (
                                isinstance(result_content, str)
                                and result_content.strip()
                            ):
                                preview = result_content.strip()[:100].replace(
                                    "\n", "\\n"
                                )
                                content_parts.append(
                                    f"📊 result: {preview}{'...' if len(result_content) > 100 else ''}"
                                )
                            else:
                                content_parts.append("📊 result")

                formatted_content = " ".join(content_parts)

            elif isinstance(content, str) and content.strip():
                content_clean = content.strip()
                if len(content_clean) > self.max_content_length:
                    formatted_content = f"{content_clean[:self.max_content_length]}..."
                else:
                    formatted_content = content_clean

            if not formatted_content:
                return None

            # Clean up formatting
            formatted_content = re.sub(r"\\s+", " ", formatted_content).strip()
            if not formatted_content:
                return None

            result = f"{time_str} {agent_prefix} {role_icon} {formatted_content}"

            # Strip ANSI for dashboard
            if for_dashboard:
                result = Colors.strip_ansi(result)

            return result

        except Exception as e:
            return f"⚠️  Error formatting entry for {agent_id}: {e}"

    async def tail_file(
        self, file_path: Path, agent_id: str, output_queue: asyncio.Queue
    ):
        """Enhanced file tailing with better activity tracking"""
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
                        lines_processed = 0

                        for line in f:
                            if not line.strip():
                                continue

                            try:
                                entry = json.loads(line.strip())

                                # Format for both terminal and dashboard
                                terminal_line = self.format_log_entry(
                                    agent_id, entry, for_dashboard=False
                                )
                                dashboard_line = self.format_log_entry(
                                    agent_id, entry, for_dashboard=True
                                )

                                if terminal_line and dashboard_line:
                                    timestamp = entry.get("timestamp", "")
                                    await output_queue.put(
                                        (
                                            timestamp,
                                            terminal_line,
                                            dashboard_line,
                                            agent_id,
                                        )
                                    )
                                    lines_processed += 1

                            except json.JSONDecodeError:
                                continue

                        position = f.tell()
                        self.agent_positions[agent_id] = position

                        # Broadcast updates if we processed lines
                        if lines_processed > 0:
                            await self._trigger_metrics_update()

                except FileNotFoundError:
                    if agent_id in self.agent_positions:
                        del self.agent_positions[agent_id]
                    break
                except PermissionError:
                    break

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            pass

    async def output_processor(self, output_queue: asyncio.Queue):
        """Enhanced output processing with real-time updates"""
        output_buffer = []
        last_flush = time.time()

        try:
            while self.running:
                try:
                    timeout = 0.05  # Faster processing
                    batch_size = 0

                    while batch_size < 3:  # Smaller batches for faster updates
                        try:
                            (
                                timestamp,
                                terminal_msg,
                                dashboard_msg,
                                agent_id,
                            ) = await asyncio.wait_for(
                                output_queue.get(), timeout=timeout
                            )
                            output_buffer.append(
                                (timestamp, terminal_msg, dashboard_msg, agent_id)
                            )
                            batch_size += 1
                            timeout = 0.01
                        except asyncio.TimeoutError:
                            break

                    current_time = time.time()
                    if output_buffer and (
                        batch_size > 0 or current_time - last_flush > 0.1
                    ):
                        output_buffer.sort(key=lambda x: x[0])

                        for (
                            timestamp,
                            terminal_msg,
                            dashboard_msg,
                            agent_id,
                        ) in output_buffer:
                            # Print to terminal
                            print(terminal_msg, flush=True)

                            # Broadcast to dashboard immediately
                            if self.websocket_connections:
                                await self._broadcast_to_dashboard(
                                    {
                                        "type": "log_entry",
                                        "timestamp": timestamp,
                                        "message": dashboard_msg,
                                        "agent_id": agent_id,
                                    }
                                )

                        output_buffer.clear()
                        last_flush = current_time
                    else:
                        await asyncio.sleep(0.01)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Output processor error: {e}")

        except Exception:
            pass

    async def _trigger_metrics_update(self):
        """Trigger immediate metrics update to dashboard"""
        if self.websocket_connections:
            summary = self.metrics.get_summary()
            await self._broadcast_to_dashboard({"type": "summary", "data": summary})

    def _setup_dashboard_routes(self):
        """Setup dashboard routes"""
        if not self.app:
            return
        self.app.router.add_get("/", self._serve_dashboard)
        self.app.router.add_get("/api/summary", self._api_summary)
        self.app.router.add_get("/ws", self._websocket_handler)
        self.app.router.add_get("/health", self._health_check)

    async def _serve_dashboard(self, request):
        """Serve enhanced dashboard HTML"""
        return web.Response(
            text=self._get_enhanced_dashboard_html(), content_type="text/html"
        )

    async def _api_summary(self, request):
        """API endpoint for metrics"""
        try:
            summary = self.metrics.get_summary()
            return web.json_response(summary)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _websocket_handler(self, request):
        """Enhanced WebSocket handler"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websocket_connections.add(ws)
        self.logger.info("Dashboard client connected")

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
                            await ws.send_str(
                                json.dumps({"type": "pong", "timestamp": time.time()})
                            )
                    except json.JSONDecodeError:
                        pass
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")

        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_connections.discard(ws)
            self.logger.info("Dashboard client disconnected")

        return ws

    async def _health_check(self, request):
        """Health check endpoint"""
        stats = {
            "status": "healthy",
            "websocket_connections": len(self.websocket_connections),
            "active_agents": len(self.agent_files),
            "metrics": self.metrics.get_summary(),
        }
        return web.json_response(stats)

    async def _broadcast_to_dashboard(self, message: dict):
        """Broadcast message to all dashboard connections"""
        if not self.websocket_connections:
            return

        message_str = json.dumps(message)
        disconnected = set()

        for ws in list(self.websocket_connections):
            try:
                await ws.send_str(message_str)
            except Exception:
                disconnected.add(ws)

        self.websocket_connections -= disconnected

    def _get_enhanced_dashboard_html(self) -> str:
        """Generate enhanced dashboard HTML with real-time updates"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Agent Monitor Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); position: relative; z-index: 1; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-value {{ font-weight: bold; color: #2c3e50; }}
        .status-indicator {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .status-active {{ background-color: #27ae60; }}
        .status-warning {{ background-color: #f39c12; }}
        .status-error {{ background-color: #e74c3c; }}
        #log {{ height: 500px; overflow-y: auto; background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 4px; font-family: 'Monaco', 'Menlo', monospace; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }}
        #agents-list {{ max-height: 200px; overflow-y: auto; }}
        .agent-item {{ padding: 5px; margin: 2px 0; background: #f8f9fa; border-radius: 4px; font-size: 12px; }}
        .update-indicator {{ position: fixed; top: 10px; right: 10px; background: #27ae60; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; opacity: 0; transition: opacity 0.3s; }}
        .update-indicator.show {{ opacity: 1; }}
        .log-entry {{ margin-bottom: 2px; word-wrap: break-word; }}
        .log-entry:hover {{ background: rgba(255,255,255,0.1); }}
    </style>
</head>
<body>
    <div class="update-indicator" id="update-indicator">Updated</div>

    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced Agent Monitor Dashboard</h1>
            <p>Real-time monitoring with live output streaming and instant updates</p>
        </div>

        <div class="dashboard-grid">
            <div class="card">
                <h3>📊 System Overview</h3>
                <div class="metric"><span>Total Tasks</span><span class="metric-value" id="total-tasks">0</span></div>
                <div class="metric"><span>Completed Tasks</span><span class="metric-value" id="completed-tasks">0</span></div>
                <div class="metric"><span>Failed Tasks</span><span class="metric-value" id="failed-tasks">0</span></div>
                <div class="metric"><span>Active Agents</span><span class="metric-value" id="active-agents">0</span></div>
                <div class="metric"><span>Active Tasks</span><span class="metric-value" id="active-tasks">0</span></div>
            </div>

            <div class="card">
                <h3>⚡ Performance</h3>
                <div class="metric"><span>Throughput (tasks/min)</span><span class="metric-value" id="throughput">0</span></div>
                <div class="metric"><span>Error Rate</span><span class="metric-value" id="error-rate">0%</span></div>
                <div class="metric"><span>Runtime</span><span class="metric-value" id="runtime">0s</span></div>
                <div class="metric">
                    <span>Connection</span>
                    <span class="metric-value">
                        <span class="status-indicator status-warning" id="status"></span>
                        <span id="connection-status">Connecting...</span>
                    </span>
                </div>
            </div>

            <div class="card">
                <h3>🔧 Top Tools & Active Agents</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <h4 style="margin: 0 0 10px 0; color: #666;">Tools</h4>
                        <div id="top-tools">Loading...</div>
                    </div>
                    <div>
                        <h4 style="margin: 0 0 10px 0; color: #666;">Agents</h4>
                        <div id="agents-list">Loading...</div>
                    </div>
                </div>
            </div>

            <div class="card" style="grid-column: span 2; min-height: 600px; z-index: 2;">
                <h3>📝 Live Activity Stream</h3>
                <div id="log" style="height: 550px; position: relative;"></div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let logLines = 0;
        const maxLogLines = 200;

        function showUpdateIndicator() {{
            const indicator = document.getElementById('update-indicator');
            indicator.classList.add('show');
            setTimeout(() => indicator.classList.remove('show'), 1000);
        }}

        function connect() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws`;
            ws = new WebSocket(wsUrl);

            ws.onopen = function() {{
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('status').className = 'status-indicator status-active';
                log('🟢 Connected to monitoring server', false);
            }};

            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                handleMessage(data);
            }};

            ws.onclose = function() {{
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('status').className = 'status-indicator status-error';
                log('🔴 Disconnected, reconnecting...', false);
                setTimeout(connect, 3000);
            }};

            ws.onerror = function(error) {{
                log('❌ WebSocket error', false);
            }};
        }}

        function handleMessage(data) {{
            if (data.type === 'summary') {{
                updateSummary(data.data);
                showUpdateIndicator();
            }} else if (data.type === 'log_entry') {{
                log(data.message, true);
            }}
        }}

        function updateSummary(summary) {{
            document.getElementById('total-tasks').textContent = summary.total_tasks || 0;
            document.getElementById('completed-tasks').textContent = summary.completed_tasks || 0;
            document.getElementById('failed-tasks').textContent = summary.failed_tasks || 0;
            document.getElementById('active-agents').textContent = summary.active_agents || 0;
            document.getElementById('active-tasks').textContent = summary.active_tasks || 0;
            document.getElementById('throughput').textContent = (summary.throughput_per_minute || 0).toFixed(1);
            document.getElementById('error-rate').textContent = ((summary.error_rate || 0) * 100).toFixed(1) + '%';
            document.getElementById('runtime').textContent = Math.floor(summary.runtime_seconds || 0) + 's';

            // Update agents list
            const agentsList = summary.active_agents_list || [];
            const agentsHtml = agentsList.length > 0
                ? agentsList.map(agent => `<div class="agent-item">${{agent}}</div>`).join('')
                : '<div style="color: #666; font-style: italic;">No active agents</div>';
            document.getElementById('agents-list').innerHTML = agentsHtml;

            // Update tools
            const topTools = summary.top_tools || {{}};
            const toolsHtml = Object.entries(topTools).length > 0
                ? Object.entries(topTools)
                    .slice(0, 8)
                    .map(([tool, count]) => `<div class="metric"><span>${{tool}}</span><span class="metric-value">${{count}}</span></div>`)
                    .join('')
                : '<div style="color: #666; font-style: italic;">No tools used yet</div>';
            document.getElementById('top-tools').innerHTML = toolsHtml;
        }}

        function log(message, isAgentLog = true) {{
            const logElement = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            const prefix = isAgentLog ? '' : `[${{time}}] `;
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.textContent = prefix + message;
            logElement.appendChild(logEntry);

            logLines++;
            if (logLines > maxLogLines) {{
                logElement.removeChild(logElement.firstChild);
                logLines--;
            }}

            logElement.scrollTop = logElement.scrollHeight;

            if (isAgentLog) {{
                showUpdateIndicator();
            }}
        }}

        // Send ping every 10 seconds to keep connection alive
        setInterval(() => {{
            if (ws && ws.readyState === WebSocket.OPEN) {{
                ws.send(JSON.stringify({{type: 'ping'}}));
            }}
        }}, 10000);

        // Request summary every 3 seconds
        setInterval(() => {{
            if (ws && ws.readyState === WebSocket.OPEN) {{
                ws.send(JSON.stringify({{type: 'get_summary'}}));
            }}
        }}, 3000);

        connect();
    </script>
</body>
</html>"""

    def print_startup_summary(
        self, agent_files: List[Path], swarms: Dict[str, List[str]]
    ):
        """Print startup summary"""
        print(f"\n🚀 {Colors.BOLD}Enhanced Agent Monitor Started{Colors.RESET}")
        print(f"📁 Projects: {self.projects_dir}")
        print(f"🔍 Pattern: {self.pattern}")
        print(f"📊 Found {len(agent_files)} active agents")

        if self.enable_dashboard and self.app:
            print(f"🌐 Dashboard: http://localhost:{self.dashboard_port}")

        if swarms:
            print(f"\n🐝 {Colors.BOLD}Detected Swarms:{Colors.RESET}")
            for swarm_id, agents in swarms.items():
                icon = self.swarm_icons.get(swarm_id, "❓")
                print(
                    f"  {icon} {swarm_id}: {len(agents)} agents ({', '.join(agents)})"
                )
        else:
            print("\n🔍 No swarms detected")

        print(
            f"\n⏱️  {Colors.DIM}Real-time monitoring active... (Ctrl+C to exit){Colors.RESET}\n"
        )
        print("=" * 100)

    async def run(self):
        """Main execution loop"""
        self.running = True

        # Setup
        agent_files = self.discover_agent_files()
        if not agent_files:
            print("❌ No agent files found")
            return

        swarms = self.detect_swarms(agent_files)
        self.assign_colors_and_icons(agent_files, swarms)
        self.print_startup_summary(agent_files, swarms)

        # Create tasks
        output_queue = asyncio.Queue(maxsize=1000)
        tasks = []

        # Dashboard
        if self.enable_dashboard and self.app:
            tasks.append(asyncio.create_task(self._start_dashboard()))

        # File tailing
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            tasks.append(
                asyncio.create_task(self.tail_file(file_path, agent_id, output_queue))
            )

        # Output processor
        tasks.append(asyncio.create_task(self.output_processor(output_queue)))

        # Metrics broadcaster
        tasks.append(asyncio.create_task(self._broadcast_metrics_loop()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            for task in tasks:
                task.cancel()

    async def _start_dashboard(self):
        """Start dashboard server"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, "localhost", self.dashboard_port)
            await site.start()
            self.logger.info(
                f"Enhanced dashboard started on http://localhost:{self.dashboard_port}"
            )

            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")

    async def _broadcast_metrics_loop(self):
        """Continuous metrics broadcasting"""
        while self.running:
            try:
                if self.websocket_connections:
                    summary = self.metrics.get_summary()
                    await self._broadcast_to_dashboard(
                        {"type": "summary", "data": summary}
                    )
                await asyncio.sleep(2)  # Every 2 seconds
            except Exception as e:
                self.logger.error(f"Metrics broadcast error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        self.running = False


def signal_handler(signum, frame, monitor):
    """Handle shutdown signals"""
    print(f"\n\n👋 {Colors.BOLD}Shutting down enhanced monitor...{Colors.RESET}")
    monitor.stop()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Unified Agent Monitor - Real-time output streaming"
    )
    parser.add_argument("--projects-dir", help="Claude projects directory")
    parser.add_argument("--pattern", default="*", help="Project directory pattern")
    parser.add_argument(
        "--dashboard-port", type=int, default=8766, help="Dashboard port"
    )
    parser.add_argument(
        "--max-length", type=int, default=500, help="Max content length"
    )
    parser.add_argument(
        "--no-tool-params", action="store_true", help="Hide tool parameters"
    )
    parser.add_argument("--no-dashboard", action="store_true", help="Disable dashboard")

    args = parser.parse_args()

    monitor = EnhancedUnifiedMonitor(
        projects_dir=args.projects_dir,
        pattern=args.pattern,
        dashboard_port=args.dashboard_port,
        max_content_length=args.max_length,
        show_tool_params=not args.no_tool_params,
        enable_dashboard=not args.no_dashboard,
    )

    def handle_signal(signum, frame):
        signal_handler(signum, frame, monitor)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        await monitor.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

    print("✅ Enhanced monitor stopped.")


if __name__ == "__main__":
    asyncio.run(main())
