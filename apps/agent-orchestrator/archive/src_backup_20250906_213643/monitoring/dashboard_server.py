"""
Dashboard Web Server
Serves the monitoring dashboard interface with real-time metrics
"""
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Dict, Optional

try:
    from aiohttp import WSMsgType, web
    from aiohttp.web import Application, Request, Response, WebSocketResponse
except ImportError:
    web = None
    logging.warning("aiohttp package not available - install with: pip install aiohttp")

from .metrics_collector import MetricsCollector, get_global_collector

logger = logging.getLogger(__name__)


class DashboardServer:
    """HTTP server for dashboard interface with WebSocket support"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8766,
        collector: Optional[MetricsCollector] = None,
        static_dir: Optional[str] = None,
    ):
        if web is None:
            raise ImportError(
                "aiohttp package required - install with: pip install aiohttp"
            )

        self.host = host
        self.port = port
        self.collector = collector or get_global_collector()

        # Static files directory
        if static_dir:
            self.static_dir = Path(static_dir)
        else:
            self.static_dir = Path(__file__).parent.parent.parent / "web"

        # Application setup
        self.app = web.Application()
        self._setup_routes()

        # WebSocket connections
        self.websocket_connections = set()

        logger.info("DashboardServer initialized on %s:%d", host, port)

    def _setup_routes(self) -> None:
        """Setup HTTP and WebSocket routes"""
        # Static files
        self.app.router.add_get("/", self._serve_index)
        self.app.router.add_get("/static/{filename:.*}", self._serve_static)

        # API endpoints
        self.app.router.add_get("/api/summary", self._api_summary)
        self.app.router.add_get("/api/metrics", self._api_metrics)
        self.app.router.add_get("/api/active-tasks", self._api_active_tasks)
        self.app.router.add_get("/api/active-agents", self._api_active_agents)

        # WebSocket endpoint
        self.app.router.add_get("/ws", self._websocket_handler)

        # Health check
        self.app.router.add_get("/health", self._health_check)

    async def _serve_index(self, request: Request) -> Response:
        """Serve the main dashboard page"""
        index_path = self.static_dir / "index.html"

        if not index_path.exists():
            # Create a basic dashboard if it doesn't exist
            html_content = self._create_default_dashboard()
            return Response(text=html_content, content_type="text/html")

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            return Response(text=content, content_type="text/html")
        except Exception as e:
            logger.error("Error serving index: %s", e)
            return Response(text="Error loading dashboard", status=500)

    async def _serve_static(self, request: Request) -> Response:
        """Serve static files"""
        filename = request.match_info["filename"]
        file_path = self.static_dir / filename

        # Security check
        try:
            file_path.resolve().relative_to(self.static_dir.resolve())
        except ValueError:
            return Response(text="Access denied", status=403)

        if not file_path.exists():
            return Response(text="File not found", status=404)

        try:
            content_type, _ = mimetypes.guess_type(str(file_path))
            if content_type is None:
                content_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                content = f.read()

            return Response(body=content, content_type=content_type)
        except Exception as e:
            logger.error("Error serving static file %s: %s", filename, e)
            return Response(text="Error loading file", status=500)

    async def _api_summary(self, request: Request) -> Response:
        """API endpoint for metrics summary"""
        try:
            summary = self.collector.get_summary()
            return web.json_response(summary.__dict__)
        except Exception as e:
            logger.error("Error getting summary: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _api_metrics(self, request: Request) -> Response:
        """API endpoint for recent metrics"""
        try:
            seconds = int(request.query.get("seconds", 300))
            metric_type = request.query.get("type")

            if metric_type:
                from .metrics_collector import MetricType

                try:
                    mt = MetricType(metric_type)
                    metrics = self.collector.get_metrics_by_type(mt, seconds)
                except ValueError:
                    return web.json_response(
                        {"error": f"Invalid metric type: {metric_type}"}, status=400
                    )
            else:
                metrics = self.collector.get_recent_metrics(seconds)

            return web.json_response(
                {"metrics": metrics, "time_window_seconds": seconds}
            )
        except Exception as e:
            logger.error("Error getting metrics: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _api_active_tasks(self, request: Request) -> Response:
        """API endpoint for active tasks"""
        try:
            active_tasks = self.collector.get_active_tasks()
            return web.json_response({"tasks": active_tasks})
        except Exception as e:
            logger.error("Error getting active tasks: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _api_active_agents(self, request: Request) -> Response:
        """API endpoint for active agents"""
        try:
            active_agents = self.collector.get_active_agents()
            return web.json_response({"agents": active_agents})
        except Exception as e:
            logger.error("Error getting active agents: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _websocket_handler(self, request: Request) -> WebSocketResponse:
        """Handle WebSocket connections for real-time updates"""
        ws = WebSocketResponse()
        await ws.prepare(request)

        self.websocket_connections.add(ws)
        logger.info("WebSocket client connected")

        try:
            # Send initial data
            await self._send_initial_ws_data(ws)

            # Handle messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_ws_message(ws, data)
                    except json.JSONDecodeError:
                        await ws.send_str(
                            json.dumps({"type": "error", "error": "Invalid JSON"})
                        )
                elif msg.type == WSMsgType.ERROR:
                    logger.error("WebSocket error: %s", ws.exception())

        except Exception as e:
            logger.error("WebSocket error: %s", e)
        finally:
            self.websocket_connections.discard(ws)
            logger.info("WebSocket client disconnected")

        return ws

    async def _send_initial_ws_data(self, ws: WebSocketResponse) -> None:
        """Send initial data to WebSocket client"""
        try:
            # Send summary
            summary = self.collector.get_summary()
            await ws.send_str(json.dumps({"type": "summary", "data": summary.__dict__}))

            # Send recent metrics
            metrics = self.collector.get_recent_metrics(60)
            await ws.send_str(json.dumps({"type": "metrics", "data": metrics}))

            # Send active tasks
            active_tasks = self.collector.get_active_tasks()
            await ws.send_str(
                json.dumps({"type": "active_tasks", "data": active_tasks})
            )

        except Exception as e:
            logger.error("Error sending initial WebSocket data: %s", e)

    async def _handle_ws_message(self, ws: WebSocketResponse, data: Dict) -> None:
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")

        if message_type == "get_summary":
            summary = self.collector.get_summary()
            await ws.send_str(json.dumps({"type": "summary", "data": summary.__dict__}))

        elif message_type == "get_metrics":
            seconds = data.get("seconds", 300)
            metrics = self.collector.get_recent_metrics(seconds)
            await ws.send_str(json.dumps({"type": "metrics", "data": metrics}))

        elif message_type == "ping":
            await ws.send_str(
                json.dumps({"type": "pong", "timestamp": data.get("timestamp")})
            )

    async def _health_check(self, request: Request) -> Response:
        """Health check endpoint"""
        stats = {
            "status": "healthy",
            "websocket_connections": len(self.websocket_connections),
            "collector_active": self.collector is not None,
        }
        return web.json_response(stats)

    def _create_default_dashboard(self) -> str:
        """Create a basic HTML dashboard if none exists"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Orchestrator Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
            color: #2c3e50;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-active { background-color: #27ae60; }
        .status-warning { background-color: #f39c12; }
        .status-error { background-color: #e74c3c; }
        #log {
            height: 200px;
            overflow-y: auto;
            background: #2c3e50;
            color: #ecf0f1;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Agent Orchestrator Dashboard</h1>
            <p>Real-time monitoring and metrics for multi-agent execution</p>
        </div>

        <div class="dashboard-grid">
            <div class="card">
                <h3>📊 System Overview</h3>
                <div class="metric">
                    <span>Total Tasks</span>
                    <span class="metric-value" id="total-tasks">0</span>
                </div>
                <div class="metric">
                    <span>Completed Tasks</span>
                    <span class="metric-value" id="completed-tasks">0</span>
                </div>
                <div class="metric">
                    <span>Failed Tasks</span>
                    <span class="metric-value" id="failed-tasks">0</span>
                </div>
                <div class="metric">
                    <span>Active Agents</span>
                    <span class="metric-value" id="active-agents">0</span>
                </div>
            </div>

            <div class="card">
                <h3>⚡ Performance</h3>
                <div class="metric">
                    <span>Throughput (tasks/min)</span>
                    <span class="metric-value" id="throughput">0</span>
                </div>
                <div class="metric">
                    <span>Avg Execution Time</span>
                    <span class="metric-value" id="avg-time">0s</span>
                </div>
                <div class="metric">
                    <span>Error Rate</span>
                    <span class="metric-value" id="error-rate">0%</span>
                </div>
                <div class="metric">
                    <span>Connection Status</span>
                    <span class="metric-value">
                        <span class="status-indicator status-warning" id="status"></span>
                        <span id="connection-status">Connecting...</span>
                    </span>
                </div>
            </div>

            <div class="card">
                <h3>🔄 Active Tasks</h3>
                <div id="active-tasks">No active tasks</div>
            </div>

            <div class="card">
                <h3>📝 Activity Log</h3>
                <div id="log"></div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('status').className = 'status-indicator status-active';
                log('Connected to monitoring server');
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };

            ws.onclose = function() {
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('status').className = 'status-indicator status-error';
                log('Disconnected from server, reconnecting...');
                setTimeout(connect, 3000);
            };

            ws.onerror = function(error) {
                log('WebSocket error: ' + error);
            };
        }

        function handleMessage(data) {
            if (data.type === 'summary') {
                updateSummary(data.data);
            } else if (data.type === 'metrics') {
                updateMetrics(data.data);
            } else if (data.type === 'active_tasks') {
                updateActiveTasks(data.data);
            }
        }

        function updateSummary(summary) {
            document.getElementById('total-tasks').textContent = summary.total_tasks || 0;
            document.getElementById('completed-tasks').textContent = summary.completed_tasks || 0;
            document.getElementById('failed-tasks').textContent = summary.failed_tasks || 0;
            document.getElementById('active-agents').textContent = summary.active_agents || 0;
            document.getElementById('throughput').textContent = (summary.throughput_per_minute || 0).toFixed(1);
            document.getElementById('avg-time').textContent = (summary.average_execution_time || 0).toFixed(1) + 's';
            document.getElementById('error-rate').textContent = ((summary.error_rate || 0) * 100).toFixed(1) + '%';
        }

        function updateActiveTasks(tasks) {
            const container = document.getElementById('active-tasks');
            const taskList = Object.keys(tasks);

            if (taskList.length === 0) {
                container.innerHTML = 'No active tasks';
            } else {
                container.innerHTML = taskList.map(taskId =>
                    `<div class="metric">
                        <span>${taskId}</span>
                        <span class="metric-value">${Math.floor((Date.now() / 1000) - tasks[taskId])}s</span>
                    </div>`
                ).join('');
            }
        }

        function log(message) {
            const logElement = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            logElement.innerHTML += `[${time}] ${message}\\n`;
            logElement.scrollTop = logElement.scrollHeight;
        }

        // Auto-refresh summary every 5 seconds
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'get_summary'}));
            }
        }, 5000);

        // Connect on page load
        connect();
    </script>
</body>
</html>"""

    async def start_server(self) -> None:
        """Start the dashboard server"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()

            site = web.TCPSite(runner, self.host, self.port)
            await site.start()

            logger.info(
                "Dashboard server started on http://%s:%d", self.host, self.port
            )
        except Exception as e:
            logger.error("Failed to start dashboard server: %s", e)
            raise

    async def broadcast_to_websockets(self, message: Dict) -> None:
        """Broadcast message to all WebSocket connections"""
        if not self.websocket_connections:
            return

        message_str = json.dumps(message)
        disconnected = set()

        for ws in self.websocket_connections:
            try:
                await ws.send_str(message_str)
            except Exception:
                disconnected.add(ws)

        # Remove disconnected clients
        self.websocket_connections -= disconnected
