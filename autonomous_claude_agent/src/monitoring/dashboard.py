"""
Web dashboard for monitoring the autonomous agent with WebSocket support.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

from ..utils.logger import get_logger
from .metrics_exporter import MetricsExporter
from .alert_manager import AlertManager, AlertSeverity
from .health_checker import HealthChecker

logger = get_logger(__name__)


class DashboardConfig(BaseModel):
    """Dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    update_interval: float = 1.0
    history_size: int = 1000
    enable_cors: bool = True


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new connection."""
        await websocket.accept()
        async with self.lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a connection."""
        async with self.lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.add(connection)
        
        # Remove disconnected clients
        if disconnected:
            async with self.lock:
                self.active_connections -= disconnected


class MonitoringDashboard:
    """Real-time monitoring dashboard."""
    
    def __init__(self,
                 metrics_exporter: MetricsExporter,
                 alert_manager: AlertManager,
                 health_checker: HealthChecker,
                 config: Optional[DashboardConfig] = None):
        self.metrics_exporter = metrics_exporter
        self.alert_manager = alert_manager
        self.health_checker = health_checker
        self.config = config or DashboardConfig()
        
        self.app = FastAPI(title="Autonomous Agent Monitor")
        self.connection_manager = ConnectionManager()
        
        # Data storage
        self.metrics_history: List[Dict[str, Any]] = []
        self.system_stats: Dict[str, Any] = {}
        self.agent_states: Dict[str, Any] = {}
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_websockets()
        
        # Background tasks
        self.update_task: Optional[asyncio.Task] = None
    
    def _setup_middleware(self):
        """Set up FastAPI middleware."""
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
    
    def _setup_routes(self):
        """Set up HTTP routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve the dashboard HTML."""
            return self._generate_dashboard_html()
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get current metrics."""
            metrics = await self.metrics_exporter.get_all_metrics()
            return JSONResponse(content=metrics)
        
        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get active alerts."""
            alerts = self.alert_manager.get_active_alerts()
            return JSONResponse(content=[
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata
                }
                for alert in alerts
            ])
        
        @self.app.get("/api/health")
        async def get_health():
            """Get system health status."""
            health = await self.health_checker.check_all()
            return JSONResponse(content={
                "status": health.status.value,
                "components": {
                    name: {
                        "status": comp.status.value,
                        "message": comp.message,
                        "last_check": comp.last_check.isoformat() if comp.last_check else None,
                        "metadata": comp.metadata
                    }
                    for name, comp in health.components.items()
                },
                "timestamp": health.timestamp.isoformat()
            })
        
        @self.app.get("/api/history")
        async def get_history(limit: int = 100):
            """Get metrics history."""
            return JSONResponse(content=self.metrics_history[-limit:])
        
        @self.app.get("/api/agents")
        async def get_agents():
            """Get agent states."""
            return JSONResponse(content=self.agent_states)
        
        @self.app.post("/api/alerts/acknowledge/{alert_id}")
        async def acknowledge_alert(alert_id: str):
            """Acknowledge an alert."""
            success = self.alert_manager.acknowledge_alert(alert_id)
            if not success:
                raise HTTPException(status_code=404, detail="Alert not found")
            return {"status": "acknowledged"}
    
    def _setup_websockets(self):
        """Set up WebSocket endpoints."""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self.connection_manager.connect(websocket)
            
            try:
                # Send initial data
                await websocket.send_json({
                    "type": "initial",
                    "data": {
                        "metrics": await self.metrics_exporter.get_all_metrics(),
                        "health": await self._get_health_data(),
                        "alerts": self._get_alerts_data(),
                        "agents": self.agent_states
                    }
                })
                
                # Keep connection alive
                while True:
                    # Wait for any message (ping/pong)
                    data = await websocket.receive_text()
                    if data == "ping":
                        await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                await self.connection_manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await self.connection_manager.disconnect(websocket)
    
    async def _update_loop(self):
        """Background task to broadcast updates."""
        while True:
            try:
                # Collect current data
                metrics = await self.metrics_exporter.get_all_metrics()
                health = await self._get_health_data()
                alerts = self._get_alerts_data()
                
                # Update history
                self.metrics_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": metrics
                })
                
                # Trim history
                if len(self.metrics_history) > self.config.history_size:
                    self.metrics_history = self.metrics_history[-self.config.history_size:]
                
                # Broadcast update
                await self.connection_manager.broadcast({
                    "type": "update",
                    "data": {
                        "metrics": metrics,
                        "health": health,
                        "alerts": alerts,
                        "agents": self.agent_states,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
                await asyncio.sleep(self.config.update_interval)
                
            except Exception as e:
                logger.error(f"Update loop error: {e}")
                await asyncio.sleep(5)
    
    async def _get_health_data(self) -> Dict[str, Any]:
        """Get formatted health data."""
        health = await self.health_checker.check_all()
        return {
            "status": health.status.value,
            "components": {
                name: {
                    "status": comp.status.value,
                    "message": comp.message
                }
                for name, comp in health.components.items()
            }
        }
    
    def _get_alerts_data(self) -> List[Dict[str, Any]]:
        """Get formatted alerts data."""
        return [
            {
                "id": alert.id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in self.alert_manager.get_active_alerts()
        ]
    
    def update_agent_state(self, agent_id: str, state: Dict[str, Any]):
        """Update agent state information."""
        self.agent_states[agent_id] = {
            **state,
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def start(self):
        """Start the dashboard server."""
        # Start update loop
        self.update_task = asyncio.create_task(self._update_loop())
        
        # Start server
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def stop(self):
        """Stop the dashboard server."""
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    def _generate_dashboard_html(self) -> str:
        """Generate the dashboard HTML page."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Agent Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0f1419;
            color: #e6edf3;
        }
        .container { padding: 20px; max-width: 1400px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #30363d;
        }
        h1 { font-size: 28px; font-weight: 600; }
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 6px;
            background: #161b22;
            border: 1px solid #30363d;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.connected { background: #3fb950; }
        .status-dot.disconnected { background: #f85149; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .card-title { font-size: 16px; font-weight: 600; }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
        }
        .metric:last-child { border-bottom: none; }
        .metric-name { color: #8b949e; }
        .metric-value { font-weight: 600; font-family: monospace; }
        .alert {
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .alert.critical { background: #f8514920; border: 1px solid #f85149; }
        .alert.warning { background: #f0883e20; border: 1px solid #f0883e; }
        .alert.info { background: #58a6ff20; border: 1px solid #58a6ff; }
        .health-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .health-status.healthy { background: #3fb95020; color: #3fb950; }
        .health-status.degraded { background: #f0883e20; color: #f0883e; }
        .health-status.unhealthy { background: #f8514920; color: #f85149; }
        .chart-container {
            height: 200px;
            margin-top: 15px;
            position: relative;
        }
        canvas { width: 100% !important; height: 100% !important; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Autonomous Agent Monitor</h1>
            <div class="status-indicator">
                <span class="status-dot" id="connectionStatus"></span>
                <span id="connectionText">Connecting...</span>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">System Metrics</span>
                    <span id="lastUpdate"></span>
                </div>
                <div id="metricsContainer"></div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Health Status</span>
                    <span id="overallHealth" class="health-status"></span>
                </div>
                <div id="healthContainer"></div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Active Alerts</span>
                    <span id="alertCount"></span>
                </div>
                <div id="alertsContainer"></div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Agent Activity</span>
                </div>
                <div class="chart-container">
                    <canvas id="activityChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="card-title">Performance Metrics</span>
            </div>
            <div class="chart-container" style="height: 300px;">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        let ws;
        let activityChart, performanceChart;
        const maxDataPoints = 50;
        const performanceData = {
            labels: [],
            datasets: [{
                label: 'CPU Usage',
                data: [],
                borderColor: '#3fb950',
                tension: 0.3
            }, {
                label: 'Memory Usage',
                data: [],
                borderColor: '#58a6ff',
                tension: 0.3
            }]
        };
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                updateConnectionStatus(true);
                console.log('WebSocket connected');
            };
            
            ws.onclose = () => {
                updateConnectionStatus(false);
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                handleMessage(message);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            // Ping to keep connection alive
            setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                }
            }, 30000);
        }
        
        function updateConnectionStatus(connected) {
            const dot = document.getElementById('connectionStatus');
            const text = document.getElementById('connectionText');
            if (connected) {
                dot.className = 'status-dot connected';
                text.textContent = 'Connected';
            } else {
                dot.className = 'status-dot disconnected';
                text.textContent = 'Disconnected';
            }
        }
        
        function handleMessage(message) {
            if (message.type === 'initial' || message.type === 'update') {
                updateMetrics(message.data.metrics);
                updateHealth(message.data.health);
                updateAlerts(message.data.alerts);
                updateCharts(message.data);
                updateTimestamp();
            }
        }
        
        function updateMetrics(metrics) {
            const container = document.getElementById('metricsContainer');
            container.innerHTML = Object.entries(metrics).map(([key, value]) => `
                <div class="metric">
                    <span class="metric-name">${key}</span>
                    <span class="metric-value">${formatValue(value)}</span>
                </div>
            `).join('');
        }
        
        function updateHealth(health) {
            const overall = document.getElementById('overallHealth');
            overall.className = `health-status ${health.status.toLowerCase()}`;
            overall.textContent = health.status;
            
            const container = document.getElementById('healthContainer');
            container.innerHTML = Object.entries(health.components).map(([name, comp]) => `
                <div class="metric">
                    <span class="metric-name">${name}</span>
                    <span class="health-status ${comp.status.toLowerCase()}">${comp.status}</span>
                </div>
            `).join('');
        }
        
        function updateAlerts(alerts) {
            const count = document.getElementById('alertCount');
            count.textContent = `${alerts.length} active`;
            
            const container = document.getElementById('alertsContainer');
            if (alerts.length === 0) {
                container.innerHTML = '<p style="color: #8b949e; text-align: center;">No active alerts</p>';
            } else {
                container.innerHTML = alerts.slice(0, 5).map(alert => `
                    <div class="alert ${alert.severity.toLowerCase()}">
                        <div>
                            <strong>${alert.title}</strong><br>
                            <small>${alert.message}</small>
                        </div>
                    </div>
                `).join('');
            }
        }
        
        function updateCharts(data) {
            // Update performance chart
            if (data.metrics) {
                const now = new Date().toLocaleTimeString();
                performanceData.labels.push(now);
                performanceData.datasets[0].data.push(data.metrics.cpu_usage || 0);
                performanceData.datasets[1].data.push(data.metrics.memory_usage || 0);
                
                // Limit data points
                if (performanceData.labels.length > maxDataPoints) {
                    performanceData.labels.shift();
                    performanceData.datasets.forEach(d => d.data.shift());
                }
                
                if (performanceChart) {
                    performanceChart.update('none');
                }
            }
        }
        
        function updateTimestamp() {
            const elem = document.getElementById('lastUpdate');
            elem.textContent = new Date().toLocaleTimeString();
        }
        
        function formatValue(value) {
            if (typeof value === 'number') {
                return value.toFixed(2);
            }
            return value;
        }
        
        function initCharts() {
            // Activity chart
            const activityCtx = document.getElementById('activityChart').getContext('2d');
            activityChart = new Chart(activityCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Active', 'Idle', 'Error'],
                    datasets: [{
                        data: [65, 30, 5],
                        backgroundColor: ['#3fb950', '#58a6ff', '#f85149']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#e6edf3' }
                        }
                    }
                }
            });
            
            // Performance chart
            const performanceCtx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(performanceCtx, {
                type: 'line',
                data: performanceData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { color: '#8b949e' },
                            grid: { color: '#21262d' }
                        },
                        x: {
                            ticks: { color: '#8b949e' },
                            grid: { color: '#21262d' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#e6edf3' }
                        }
                    }
                }
            });
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initCharts();
            connectWebSocket();
        });
    </script>
</body>
</html>
        '''


class DashboardServer:
    """Standalone dashboard server."""
    
    def __init__(self,
                 dashboard: MonitoringDashboard,
                 config: Optional[DashboardConfig] = None):
        self.dashboard = dashboard
        self.config = config or DashboardConfig()
    
    async def start(self):
        """Start the dashboard server."""
        logger.info(f"Starting dashboard server on {self.config.host}:{self.config.port}")
        await self.dashboard.start()
    
    async def stop(self):
        """Stop the dashboard server."""
        logger.info("Stopping dashboard server")
        await self.dashboard.stop()


# Example usage
if __name__ == "__main__":
    async def main():
        # Create components
        metrics_exporter = MetricsExporter()
        alert_manager = AlertManager()
        health_checker = HealthChecker()
        
        # Create dashboard
        dashboard = MonitoringDashboard(
            metrics_exporter=metrics_exporter,
            alert_manager=alert_manager,
            health_checker=health_checker
        )
        
        # Start server
        server = DashboardServer(dashboard)
        await server.start()
    
    asyncio.run(main())