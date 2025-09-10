#!/usr/bin/env python3
"""
Unified Agent Monitor - Consolidated monitoring solution

Combines the best features from all existing monitoring tools:
- Detailed log tailing (from swarm_log_tailer_detailed.py)  
- Web dashboard (from dashboard_server.py)
- Real-time metrics (from realtime_monitor.py)
- Collaboration tracking (from chat-monitor)

Single tool to replace all others with comprehensive monitoring capabilities.
"""

import argparse
import asyncio
import json
import logging
import mimetypes
import os
import re
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from aiohttp import WSMsgType, web
    from aiohttp.web import Application, Request, Response, WebSocketResponse
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None


# Color management for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    COLORS = [
        "\033[91m",  # Red
        "\033[92m",  # Green
        "\033[93m",  # Yellow
        "\033[94m",  # Blue
        "\033[95m",  # Magenta
        "\033[96m",  # Cyan
        "\033[31m",  # Dark Red
        "\033[32m",  # Dark Green
        "\033[33m",  # Dark Yellow
        "\033[34m",  # Dark Blue
        "\033[35m",  # Dark Magenta
        "\033[36m",  # Dark Cyan
        "\033[97m",  # White
        "\033[90m",  # Gray
    ]

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Role indicators
    ROLE_COLORS = {
        "user": "\033[96m👤\033[0m",  # Cyan user
        "assistant": "\033[92m🤖\033[0m",  # Green assistant
        "tool": "\033[93m⚡\033[0m",  # Yellow tool
        "tool_use": "\033[94m🔧\033[0m",  # Blue tool use
        "tool_result": "\033[90m📊\033[0m",  # Gray tool result
    }

    # Swarm icons
    SWARM_ICONS = ["🐝", "🐜", "🦋", "🐞", "🦗", "🕷️", "🦂", "🐛", "🦟", "🐢"]

    @classmethod
    def get_agent_color(cls, agent_id: str, color_index: int) -> str:
        """Get consistent color for agent"""
        return cls.COLORS[color_index % len(cls.COLORS)]

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text"""
        return f"{color}{text}{cls.RESET}"


class MetricsCollector:
    """Collect and aggregate metrics from agent activity"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'active_agents': 0,
            'tool_calls': defaultdict(int),
            'agent_activity': defaultdict(list),
            'collaboration_events': [],
            'throughput_history': [],
        }
        self.active_agents = set()
        self.active_tasks = {}
        
    def record_agent_activity(self, agent_id: str, activity_type: str, details: dict = None):
        """Record agent activity for metrics"""
        self.active_agents.add(agent_id)
        self.metrics['agent_activity'][agent_id].append({
            'timestamp': time.time(),
            'type': activity_type,
            'details': details or {}
        })
        
    def record_tool_call(self, tool_name: str):
        """Record tool usage"""
        self.metrics['tool_calls'][tool_name] += 1
        
    def record_task(self, task_id: str, status: str):
        """Record task completion/failure"""
        if status == 'started':
            self.active_tasks[task_id] = time.time()
            self.metrics['total_tasks'] += 1
        elif status == 'completed':
            self.active_tasks.pop(task_id, None)
            self.metrics['completed_tasks'] += 1
        elif status == 'failed':
            self.active_tasks.pop(task_id, None) 
            self.metrics['failed_tasks'] += 1
            
        # Update throughput
        current_time = time.time()
        self.metrics['throughput_history'].append({
            'timestamp': current_time,
            'completed': self.metrics['completed_tasks'],
            'failed': self.metrics['failed_tasks']
        })
        
        # Keep only last hour of throughput data
        cutoff = current_time - 3600
        self.metrics['throughput_history'] = [
            h for h in self.metrics['throughput_history'] 
            if h['timestamp'] > cutoff
        ]
    
    def get_summary(self) -> dict:
        """Get current metrics summary"""
        current_time = time.time()
        runtime = current_time - self.start_time
        
        # Calculate throughput (tasks per minute)
        recent_history = [
            h for h in self.metrics['throughput_history']
            if h['timestamp'] > (current_time - 300)  # Last 5 minutes
        ]
        
        throughput = 0
        if len(recent_history) > 1:
            time_span = recent_history[-1]['timestamp'] - recent_history[0]['timestamp']
            task_diff = recent_history[-1]['completed'] - recent_history[0]['completed']
            if time_span > 0:
                throughput = (task_diff / time_span) * 60  # per minute
        
        # Calculate error rate
        total_completed = self.metrics['completed_tasks'] + self.metrics['failed_tasks']
        error_rate = self.metrics['failed_tasks'] / max(total_completed, 1)
        
        return {
            'total_tasks': self.metrics['total_tasks'],
            'completed_tasks': self.metrics['completed_tasks'],
            'failed_tasks': self.metrics['failed_tasks'],
            'active_agents': len(self.active_agents),
            'active_tasks': len(self.active_tasks),
            'throughput_per_minute': throughput,
            'error_rate': error_rate,
            'runtime_seconds': runtime,
            'top_tools': dict(sorted(self.metrics['tool_calls'].items(), 
                                   key=lambda x: x[1], reverse=True)[:10])
        }


class UnifiedAgentMonitor:
    """Unified monitoring solution combining log tailing, dashboard, and metrics"""
    
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
        self.agent_colors: Dict[str, str] = {}
        self.agent_positions: Dict[str, int] = {}
        self.swarm_groups: Dict[str, str] = {}
        self.swarm_icons: Dict[str, str] = {}
        self.agent_files: Dict[str, Path] = {}
        
        # Metrics and state
        self.metrics = MetricsCollector()
        self.running = False
        self.color_index = 0
        
        # Dashboard components
        if self.enable_dashboard and AIOHTTP_AVAILABLE:
            self.app = web.Application()
            self.websocket_connections = set()
            self._setup_dashboard_routes()
        else:
            self.app = None
            if self.enable_dashboard:
                print("⚠️  Dashboard disabled: aiohttp not available (pip install aiohttp)")
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def discover_agent_files(self) -> List[Path]:
        """Discover active agent log files"""
        if not self.projects_dir.exists():
            self.logger.warning(f"Projects directory not found: {self.projects_dir}")
            return []

        agent_files = []
        cutoff_time = time.time() - 86400  # 24 hours ago

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
        """Detect agent swarms based on directory grouping and timing"""
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
                        swarm_name = f"swarm_{swarm_id}"
                        swarms[swarm_name] = [agent_id for agent_id, _ in agents]
                        swarm_id += 1

        return dict(swarms)

    def assign_colors_and_icons(self, agent_files: List[Path], swarms: Dict[str, List[str]]):
        """Assign colors and icons to agents"""
        self.agent_colors.clear()
        self.swarm_groups.clear()
        self.swarm_icons.clear()
        self.agent_files.clear()

        # Create reverse swarm mapping
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

    def format_log_entry(self, agent_id: str, entry: Dict) -> Optional[str]:
        """Format a log entry with detailed content extraction"""
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

            # Extract role and content
            role = entry.get("role", entry.get("type", "unknown"))
            content = entry.get("content", entry.get("message", {}))

            if isinstance(content, dict) and "content" in content:
                content = content["content"]

            role_icon = Colors.ROLE_COLORS.get(role, "❓")
            
            # Get agent prefix with swarm icon
            color = self.agent_colors.get(agent_id, "")
            swarm_icon = ""
            if agent_id in self.swarm_groups:
                swarm_id = self.swarm_groups[agent_id]
                swarm_icon = self.swarm_icons.get(swarm_id, "") + " "
            agent_prefix = f"{swarm_icon}{Colors.colorize(f'[{agent_id}]', color)}"

            if not content and not entry.get("tool_calls") and not entry.get("tool_results"):
                return None

            formatted_content = ""

            if isinstance(content, list):
                content_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            tool_name = item.get("name", "unknown_tool")
                            tool_input = item.get("input", {})
                            
                            # Record tool usage for metrics
                            self.metrics.record_tool_call(tool_name)
                            
                            # Format with parameters if enabled
                            if self.show_tool_params:
                                formatted_tool = self._format_tool_with_params(tool_name, tool_input)
                            else:
                                formatted_tool = f"🔧 {tool_name}"
                            content_parts.append(formatted_tool)
                            
                        elif item.get("type") == "text":
                            text = item.get("text", "")
                            if text.strip():
                                text_clean = text.strip()
                                if len(text_clean) > self.max_content_length:
                                    sentences = re.split(r'[.!?]\s+', text_clean[:self.max_content_length])
                                    if len(sentences) > 1:
                                        text_preview = '. '.join(sentences[:-1]) + '.'
                                    else:
                                        text_preview = text_clean[:self.max_content_length]
                                    content_parts.append(f"{text_preview}...")
                                else:
                                    content_parts.append(text_clean)
                        elif item.get("type") == "tool_result":
                            result_content = item.get("content", "")
                            if isinstance(result_content, str) and result_content.strip():
                                result_preview = result_content.strip()[:200].replace("\n", "\\n")
                                content_parts.append(f"📊 tool_result: {result_preview}{'...' if len(result_content) > 200 else ''}")
                            else:
                                content_parts.append("📊 tool_result")

                formatted_content = " ".join(content_parts)

            elif isinstance(content, str) and content.strip():
                content_clean = content.strip()
                if len(content_clean) > self.max_content_length:
                    truncated = content_clean[:self.max_content_length]
                    last_space = truncated.rfind(' ')
                    if last_space > self.max_content_length * 0.8:
                        truncated = truncated[:last_space]
                    formatted_content = truncated + "..."
                else:
                    formatted_content = content_clean

            # Record agent activity for metrics
            self.metrics.record_agent_activity(agent_id, role, {"content_length": len(formatted_content)})

            if not formatted_content:
                return None

            formatted_content = re.sub(r'\s+', ' ', formatted_content).strip()
            
            if not formatted_content:
                return None

            return f"{time_str} {agent_prefix} {role_icon} {formatted_content}"

        except Exception as e:
            return f"⚠️  Error formatting entry for {agent_id}: {e}"

    def _format_tool_with_params(self, tool_name: str, tool_input: dict) -> str:
        """Format tool call with detailed parameters"""
        if tool_name == "Write":
            file_path = tool_input.get("file_path", "")
            content = tool_input.get("content", "")
            filename = file_path.split("/")[-1] if file_path else "unnamed"
            content_preview = content[:100].replace("\n", "\\n") if content else ""
            return f"🔧 Write → {filename} ({len(content)} chars) | {content_preview}{'...' if len(content) > 100 else ''}"
            
        elif tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            filename = file_path.split("/")[-1] if file_path else "unnamed"
            return f"🔧 Read → {filename}"
            
        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            return f"🔧 Bash → {command[:100]}{'...' if len(command) > 100 else ''}"
            
        elif tool_name == "Task":
            subagent_type = tool_input.get("subagent_type", "")
            description = tool_input.get("description", "")
            return f"🔧 Task → {subagent_type} | {description[:50]}{'...' if len(description) > 50 else ''}"
            
        else:
            return f"🔧 {tool_name}"

    async def tail_file(self, file_path: Path, agent_id: str, output_queue: asyncio.Queue):
        """Tail a single agent log file"""
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
                            self.logger.info(f"🔄 {agent_id}: File rotated/truncated, resetting position")
                            position = 0

                        f.seek(position)

                        for line in f:
                            if not line.strip():
                                continue

                            try:
                                entry = json.loads(line.strip())
                                formatted_line = self.format_log_entry(agent_id, entry)
                                if formatted_line:
                                    timestamp = entry.get("timestamp", "")
                                    await output_queue.put((timestamp, formatted_line))
                            except json.JSONDecodeError:
                                continue

                        position = f.tell()
                        self.agent_positions[agent_id] = position

                except FileNotFoundError:
                    if agent_id in self.agent_positions:
                        del self.agent_positions[agent_id]
                    self.logger.info(f"🗑️  {agent_id}: File deleted, stopping monitoring")
                    break
                except PermissionError:
                    self.logger.warning(f"⚠️  Permission denied reading {file_path}")
                    break

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            pass

    async def output_processor(self, output_queue: asyncio.Queue):
        """Process and display output in chronological order"""
        output_buffer = []
        last_flush = time.time()

        try:
            while self.running:
                try:
                    timeout = 0.1
                    batch_size = 0

                    while batch_size < 5:
                        try:
                            timestamp, message = await asyncio.wait_for(
                                output_queue.get(), timeout=timeout
                            )
                            output_buffer.append((timestamp, message))
                            batch_size += 1
                            timeout = 0.01
                        except asyncio.TimeoutError:
                            break

                    current_time = time.time()
                    if output_buffer and (batch_size > 0 or current_time - last_flush > 0.3):
                        output_buffer.sort(key=lambda x: x[0])
                        
                        for timestamp, message in output_buffer:
                            print(message, flush=True)
                            # Broadcast to dashboard if enabled
                            if self.app and self.websocket_connections:
                                await self._broadcast_to_dashboard({
                                    "type": "log_entry",
                                    "timestamp": timestamp,
                                    "message": message
                                })

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

        # Flush remaining messages
        if output_buffer:
            output_buffer.sort(key=lambda x: x[0])
            for timestamp, message in output_buffer:
                print(message, flush=True)

    def _setup_dashboard_routes(self):
        """Setup dashboard HTTP and WebSocket routes"""
        if not self.app:
            return
            
        self.app.router.add_get("/", self._serve_dashboard)
        self.app.router.add_get("/api/summary", self._api_summary)
        self.app.router.add_get("/api/metrics", self._api_metrics)
        self.app.router.add_get("/ws", self._websocket_handler)
        self.app.router.add_get("/health", self._health_check)

    async def _serve_dashboard(self, request: Request) -> Response:
        """Serve the dashboard HTML"""
        return Response(text=self._get_dashboard_html(), content_type="text/html")

    async def _api_summary(self, request: Request) -> Response:
        """API endpoint for metrics summary"""
        try:
            summary = self.metrics.get_summary()
            return web.json_response(summary)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _api_metrics(self, request: Request) -> Response:
        """API endpoint for metrics"""
        try:
            summary = self.metrics.get_summary()
            return web.json_response(summary)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _websocket_handler(self, request: Request) -> WebSocketResponse:
        """Handle WebSocket connections for real-time updates"""
        ws = WebSocketResponse()
        await ws.prepare(request)

        self.websocket_connections.add(ws)
        self.logger.info("Dashboard client connected")

        try:
            # Send initial data
            summary = self.metrics.get_summary()
            await ws.send_str(json.dumps({"type": "summary", "data": summary}))

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get("type") == "ping":
                            await ws.send_str(json.dumps({"type": "pong"}))
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

    async def _health_check(self, request: Request) -> Response:
        """Health check endpoint"""
        stats = {
            "status": "healthy",
            "websocket_connections": len(self.websocket_connections),
            "active_agents": len(self.agent_files),
            "metrics": self.metrics.get_summary()
        }
        return web.json_response(stats)

    async def _broadcast_to_dashboard(self, message: dict):
        """Broadcast message to all dashboard connections"""
        if not self.websocket_connections:
            return
            
        message_str = json.dumps(message)
        disconnected = set()
        
        for ws in self.websocket_connections:
            try:
                await ws.send_str(message_str)
            except Exception:
                disconnected.add(ws)
        
        self.websocket_connections -= disconnected

    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Agent Monitor Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background-color: #f5f5f5;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .dashboard-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-value {{ font-weight: bold; color: #2c3e50; }}
        .status-indicator {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .status-active {{ background-color: #27ae60; }}
        .status-warning {{ background-color: #f39c12; }}
        .status-error {{ background-color: #e74c3c; }}
        #log {{ height: 300px; overflow-y: auto; background: #2c3e50; color: #ecf0f1; padding: 10px; 
               border-radius: 4px; font-family: 'Monaco', 'Menlo', monospace; font-size: 12px; }}
        #agents-list {{ max-height: 200px; overflow-y: auto; }}
        .agent-item {{ padding: 5px; margin: 2px 0; background: #f8f9fa; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Unified Agent Monitor Dashboard</h1>
            <p>Real-time monitoring with log tailing, metrics, and collaboration tracking</p>
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
                    <span>Connection Status</span>
                    <span class="metric-value">
                        <span class="status-indicator status-warning" id="status"></span>
                        <span id="connection-status">Connecting...</span>
                    </span>
                </div>
            </div>

            <div class="card">
                <h3>🤖 Active Agents</h3>
                <div id="agents-list">No active agents</div>
            </div>

            <div class="card">
                <h3>🔧 Top Tools</h3>
                <div id="top-tools">Loading...</div>
            </div>

            <div class="card">
                <h3>📝 Live Activity Log</h3>
                <div id="log"></div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;

        function connect() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws`;
            ws = new WebSocket(wsUrl);

            ws.onopen = function() {{
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('status').className = 'status-indicator status-active';
                log('Connected to monitoring server');
            }};

            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                handleMessage(data);
            }};

            ws.onclose = function() {{
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('status').className = 'status-indicator status-error';
                log('Disconnected from server, reconnecting...');
                setTimeout(connect, 3000);
            }};

            ws.onerror = function(error) {{
                log('WebSocket error: ' + error);
            }};
        }}

        function handleMessage(data) {{
            if (data.type === 'summary') {{
                updateSummary(data.data);
            }} else if (data.type === 'log_entry') {{
                log(data.message);
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
            
            // Update top tools
            const topTools = summary.top_tools || {{}};
            const toolsHtml = Object.entries(topTools)
                .slice(0, 5)
                .map(([tool, count]) => `<div class="metric"><span>${{tool}}</span><span class="metric-value">${{count}}</span></div>`)
                .join('');
            document.getElementById('top-tools').innerHTML = toolsHtml || 'No tools used yet';
        }}

        function log(message) {{
            const logElement = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            const displayMessage = message.includes('[') ? message : `[${{time}}] ${{message}}`;
            logElement.innerHTML += displayMessage + '\\n';
            logElement.scrollTop = logElement.scrollHeight;
            
            // Keep only last 100 lines
            const lines = logElement.innerHTML.split('\\n');
            if (lines.length > 100) {{
                logElement.innerHTML = lines.slice(-100).join('\\n');
            }}
        }}

        // Auto-refresh summary every 5 seconds
        setInterval(() => {{
            if (ws && ws.readyState === WebSocket.OPEN) {{
                ws.send(JSON.stringify({{type: 'get_summary'}}));
            }}
        }}, 5000);

        // Connect on page load
        connect();
    </script>
</body>
</html>"""

    def print_startup_summary(self, agent_files: List[Path], swarms: Dict[str, List[str]]):
        """Print startup summary"""
        print(f"\n🚀 {Colors.BOLD}Unified Agent Monitor Started{Colors.RESET}")
        print(f"📁 Projects: {self.projects_dir}")
        print(f"🔍 Pattern: {self.pattern}")
        print(f"📊 Found {len(agent_files)} active agents")
        
        if self.enable_dashboard and self.app:
            print(f"🌐 Dashboard: http://localhost:{self.dashboard_port}")
        
        if swarms:
            print(f"\n🐝 {Colors.BOLD}Detected Swarms:{Colors.RESET}")
            for swarm_id, agents in swarms.items():
                icon = self.swarm_icons.get(swarm_id, "❓")
                print(f"  {icon} {swarm_id}: {len(agents)} agents ({', '.join(agents)})")
        else:
            print("\n🔍 No swarms detected (agents working independently)")

        print(f"\n⏱️  {Colors.DIM}Monitoring logs in real-time... (Ctrl+C to exit){Colors.RESET}\n")
        print("=" * 100)

    async def run(self):
        """Main execution loop"""
        self.running = True

        # Discover and setup
        agent_files = self.discover_agent_files()
        if not agent_files:
            print("❌ No active agent files found. Try adjusting the pattern or checking the projects directory.")
            return

        swarms = self.detect_swarms(agent_files)
        self.assign_colors_and_icons(agent_files, swarms)
        self.print_startup_summary(agent_files, swarms)

        # Start dashboard server if enabled
        dashboard_task = None
        if self.enable_dashboard and self.app:
            dashboard_task = asyncio.create_task(self._start_dashboard())

        # Create output queue
        output_queue = asyncio.Queue(maxsize=1000)

        # Start file tailing tasks
        tail_tasks = []
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            task = asyncio.create_task(self.tail_file(file_path, agent_id, output_queue))
            tail_tasks.append(task)

        # Start output processor
        output_task = asyncio.create_task(self.output_processor(output_queue))
        
        # Start metrics broadcaster
        metrics_task = asyncio.create_task(self._broadcast_metrics())

        try:
            tasks = [output_task, metrics_task] + tail_tasks
            if dashboard_task:
                tasks.append(dashboard_task)
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            for task in tail_tasks + [output_task, metrics_task]:
                task.cancel()
            if dashboard_task:
                dashboard_task.cancel()

    async def _start_dashboard(self):
        """Start the dashboard web server"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', self.dashboard_port)
            await site.start()
            self.logger.info(f"Dashboard started on http://localhost:{self.dashboard_port}")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")

    async def _broadcast_metrics(self):
        """Periodically broadcast metrics to dashboard"""
        while self.running:
            try:
                if self.websocket_connections:
                    summary = self.metrics.get_summary()
                    await self._broadcast_to_dashboard({
                        "type": "summary", 
                        "data": summary
                    })
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Metrics broadcast error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        """Stop the monitor"""
        self.running = False


def signal_handler(signum, frame, monitor):
    """Handle Ctrl+C gracefully"""
    print(f"\n\n👋 {Colors.BOLD}Shutting down unified monitor...{Colors.RESET}")
    monitor.stop()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified Agent Monitor - Log tailing, metrics, and dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Monitor with dashboard
  %(prog)s --pattern "*agent-orchestrator*"  # Custom pattern
  %(prog)s --no-dashboard                     # Terminal only
  %(prog)s --max-length 1000                 # Longer content previews
  %(prog)s --dashboard-port 8080             # Custom dashboard port
        """,
    )

    parser.add_argument("--projects-dir", help="Claude projects directory (default: ~/.claude/projects)")
    parser.add_argument("--pattern", default="*", help="Project directory pattern (default: *)")
    parser.add_argument("--dashboard-port", type=int, default=8766, help="Dashboard port (default: 8766)")
    parser.add_argument("--max-length", type=int, default=500, help="Max content length (default: 500)")
    parser.add_argument("--no-tool-params", action="store_true", help="Hide tool parameters")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable web dashboard")

    args = parser.parse_args()

    # Create monitor
    monitor = UnifiedAgentMonitor(
        projects_dir=args.projects_dir,
        pattern=args.pattern,
        dashboard_port=args.dashboard_port,
        max_content_length=args.max_length,
        show_tool_params=not args.no_tool_params,
        enable_dashboard=not args.no_dashboard,
    )

    # Setup signal handler
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

    print("✅ Unified monitor stopped.")


if __name__ == "__main__":
    asyncio.run(main())