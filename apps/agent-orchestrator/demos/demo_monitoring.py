#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard for Agent Orchestrator Demo

This module provides comprehensive real-time monitoring capabilities including:
- Live progress tracking with visual indicators
- Task status monitoring with detailed information
- Performance metrics collection and display
- Resource usage monitoring
- Interactive dashboard with web interface
"""

import asyncio
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import websockets

logger = logging.getLogger(__name__)


@dataclass
class TaskStatus:
    """Represents the current status of a task"""

    task_id: str
    task_type: str
    status: str  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress_percent: float = 0.0
    current_step: str = "Initializing"
    error_message: Optional[str] = None
    result_summary: Optional[str] = None


@dataclass
class WorkflowMetrics:
    """Comprehensive workflow metrics"""

    workflow_id: str
    workflow_name: str
    start_time: float
    total_tasks: int
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    overall_progress: float = 0.0
    estimated_completion_time: Optional[float] = None
    average_task_duration: float = 0.0
    success_rate: float = 0.0
    resource_usage: Dict = None

    def __post_init__(self):
        if self.resource_usage is None:
            self.resource_usage = {}


class RealTimeMonitor:
    """Real-time monitoring system for orchestrator workflows"""

    def __init__(self, workflow_id: str, workflow_name: str):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.start_time = time.time()

        # State tracking
        self.tasks: Dict[str, TaskStatus] = {}
        self.metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            start_time=self.start_time,
            total_tasks=0,
        )

        # Monitoring configuration
        self.update_interval = 1.0  # seconds
        self.monitoring_active = False
        self.update_callbacks: List[Callable] = []
        self.task_completion_times: List[float] = []

        # Thread-safe update lock
        self.update_lock = threading.Lock()

        # Dashboard state
        self.dashboard_data = {
            "workflow": asdict(self.metrics),
            "tasks": {},
            "live_log": [],
            "charts_data": {
                "progress_timeline": [],
                "task_duration_histogram": [],
                "resource_usage": [],
            },
        }

    def initialize_workflow(self, total_tasks: int):
        """Initialize workflow monitoring with total task count"""
        with self.update_lock:
            self.metrics.total_tasks = total_tasks
            self.metrics.pending_tasks = total_tasks
            self._log_event(
                "workflow_initialized", f"Workflow initialized with {total_tasks} tasks"
            )

    def register_task(self, task_id: str, task_type: str):
        """Register a new task for monitoring"""
        with self.update_lock:
            self.tasks[task_id] = TaskStatus(
                task_id=task_id, task_type=task_type, status="pending"
            )
            self._log_event(
                "task_registered", f"Task {task_id} ({task_type}) registered"
            )

    def update_task_status(self, task_id: str, status: str, **kwargs):
        """Update task status with optional additional information"""
        with self.update_lock:
            if task_id not in self.tasks:
                self.register_task(task_id, kwargs.get("task_type", "unknown"))

            task = self.tasks[task_id]
            old_status = task.status
            task.status = status

            # Update timestamps
            if status == "running" and old_status == "pending":
                task.start_time = time.time()
                self.metrics.running_tasks += 1
                self.metrics.pending_tasks -= 1

            elif status in ["completed", "failed"] and old_status == "running":
                task.end_time = time.time()
                self.metrics.running_tasks -= 1

                if status == "completed":
                    self.metrics.completed_tasks += 1
                    if task.start_time:
                        duration = task.end_time - task.start_time
                        self.task_completion_times.append(duration)
                else:
                    self.metrics.failed_tasks += 1

            # Update optional fields
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            # Update overall metrics
            self._update_overall_metrics()

            # Log the update
            self._log_event(
                "task_status_update", f"Task {task_id}: {old_status} → {status}"
            )

            # Notify callbacks
            self._notify_callbacks()

    def update_task_progress(
        self, task_id: str, progress_percent: float, current_step: str = None
    ):
        """Update task progress information"""
        with self.update_lock:
            if task_id in self.tasks:
                self.tasks[task_id].progress_percent = progress_percent
                if current_step:
                    self.tasks[task_id].current_step = current_step

                self._log_event(
                    "task_progress",
                    f"Task {task_id}: {progress_percent:.1f}% - {current_step}",
                )
                self._notify_callbacks()

    def _update_overall_metrics(self):
        """Update overall workflow metrics"""
        total = self.metrics.total_tasks
        if total > 0:
            self.metrics.overall_progress = (self.metrics.completed_tasks / total) * 100
            self.metrics.success_rate = (
                self.metrics.completed_tasks
                / max(1, self.metrics.completed_tasks + self.metrics.failed_tasks)
            ) * 100

        # Calculate average task duration
        if self.task_completion_times:
            self.metrics.average_task_duration = sum(self.task_completion_times) / len(
                self.task_completion_times
            )

            # Estimate completion time
            remaining_tasks = (
                self.metrics.total_tasks
                - self.metrics.completed_tasks
                - self.metrics.failed_tasks
            )
            if remaining_tasks > 0:
                estimated_remaining_time = (
                    remaining_tasks * self.metrics.average_task_duration
                )
                self.metrics.estimated_completion_time = (
                    time.time() + estimated_remaining_time
                )

    def _log_event(self, event_type: str, message: str):
        """Log an event to the live log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
        }

        self.dashboard_data["live_log"].append(log_entry)

        # Keep only last 100 log entries
        if len(self.dashboard_data["live_log"]) > 100:
            self.dashboard_data["live_log"] = self.dashboard_data["live_log"][-100:]

    def _notify_callbacks(self):
        """Notify all registered callbacks of updates"""
        for callback in self.update_callbacks:
            try:
                callback(self.get_current_state())
            except Exception as e:
                logger.error(f"Error in monitor callback: {e}")

    def register_callback(self, callback: Callable):
        """Register a callback for real-time updates"""
        self.update_callbacks.append(callback)

    def get_current_state(self) -> Dict:
        """Get current complete monitoring state"""
        with self.update_lock:
            return {
                "workflow": asdict(self.metrics),
                "tasks": {
                    task_id: asdict(task) for task_id, task in self.tasks.items()
                },
                "live_log": self.dashboard_data["live_log"][-20:],  # Last 20 entries
                "summary": {
                    "elapsed_time": time.time() - self.start_time,
                    "tasks_per_minute": (
                        self.metrics.completed_tasks
                        / max((time.time() - self.start_time) / 60, 0.1)
                    ),
                    "eta_minutes": (
                        (self.metrics.estimated_completion_time - time.time()) / 60
                        if self.metrics.estimated_completion_time
                        else None
                    ),
                },
            }

    def generate_progress_report(self) -> str:
        """Generate a formatted progress report"""
        state = self.get_current_state()
        workflow = state["workflow"]
        summary = state["summary"]

        # Progress bar
        progress = workflow["overall_progress"]
        bar_length = 50
        filled_length = int(bar_length * progress / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          ORCHESTRATOR LIVE MONITORING                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ Workflow: {workflow['workflow_name']:<60} ║
║ Progress: {progress:5.1f}% |{bar}| ║
║                                                                               ║
║ 📊 Task Status:                                                               ║
║    ✅ Completed: {workflow['completed_tasks']:>3}    ⏳ Running: {workflow['running_tasks']:>3}    ❌ Failed: {workflow['failed_tasks']:>3}    ⏸️  Pending: {workflow['pending_tasks']:>3} ║
║                                                                               ║
║ ⏱️  Timing:                                                                    ║
║    Elapsed: {summary['elapsed_time']/60:>6.1f} min    Rate: {summary['tasks_per_minute']:>5.1f} tasks/min               ║
║    ETA: {summary['eta_minutes']:>9.1f} min    Avg/Task: {workflow['average_task_duration']:>6.1f} sec                 ║
║                                                                               ║
║ 🎯 Success Rate: {workflow['success_rate']:>5.1f}%                                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

        # Add recent activity
        if state["live_log"]:
            report += "\n📋 Recent Activity:\n"
            for entry in state["live_log"][-5:]:
                timestamp = datetime.fromisoformat(entry["timestamp"]).strftime(
                    "%H:%M:%S"
                )
                report += f"   {timestamp} | {entry['message']}\n"

        return report

    def start_live_monitoring(self, update_interval: float = 1.0):
        """Start live monitoring with console updates"""
        self.update_interval = update_interval
        self.monitoring_active = True

        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Clear screen and show report
                    print("\033[2J\033[H")  # Clear screen and move cursor to top
                    print(self.generate_progress_report())
                    time.sleep(self.update_interval)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(1)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def stop_monitoring(self):
        """Stop live monitoring"""
        self.monitoring_active = False

    def save_final_report(self, output_path: Path):
        """Save comprehensive final report"""
        final_state = self.get_current_state()

        # Enhanced final report
        report = {
            "workflow_summary": final_state["workflow"],
            "task_details": final_state["tasks"],
            "execution_timeline": self.dashboard_data["live_log"],
            "performance_analysis": {
                "total_execution_time": time.time() - self.start_time,
                "task_completion_times": self.task_completion_times,
                "average_task_duration": final_state["workflow"][
                    "average_task_duration"
                ],
                "throughput_tasks_per_minute": final_state["summary"][
                    "tasks_per_minute"
                ],
                "success_rate": final_state["workflow"]["success_rate"],
            },
            "monitoring_metadata": {
                "monitoring_start": datetime.fromtimestamp(self.start_time).isoformat(),
                "monitoring_end": datetime.now().isoformat(),
                "total_log_entries": len(self.dashboard_data["live_log"]),
                "update_callbacks_registered": len(self.update_callbacks),
            },
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        logger.info(f"Final monitoring report saved to: {output_path}")


class WebDashboard:
    """Web-based dashboard for real-time monitoring"""

    def __init__(self, monitor: RealTimeMonitor, port: int = 8765):
        self.monitor = monitor
        self.port = port
        self.connected_clients = set()
        self.server = None

    async def register_client(self, websocket, path):
        """Register a new websocket client"""
        self.connected_clients.add(websocket)
        try:
            # Send initial state
            await websocket.send(
                json.dumps(
                    {"type": "initial_state", "data": self.monitor.get_current_state()}
                )
            )

            # Keep connection alive
            await websocket.wait_closed()
        finally:
            self.connected_clients.discard(websocket)

    async def broadcast_update(self, update_data: Dict):
        """Broadcast update to all connected clients"""
        if self.connected_clients:
            message = json.dumps({"type": "update", "data": update_data})

            # Send to all connected clients
            disconnected = set()
            for client in self.connected_clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)

            # Remove disconnected clients
            self.connected_clients -= disconnected

    def start_server(self):
        """Start the websocket server"""

        def server_callback(state):
            """Callback to broadcast updates"""
            if self.connected_clients:
                asyncio.create_task(self.broadcast_update(state))

        self.monitor.register_callback(server_callback)

        async def server_main():
            self.server = await websockets.serve(
                self.register_client, "localhost", self.port
            )
            logger.info(f"Dashboard server started on ws://localhost:{self.port}")
            await self.server.wait_closed()

        return asyncio.create_task(server_main())

    def get_dashboard_html(self) -> str:
        """Generate HTML dashboard page"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Orchestrator - Live Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .progress-bar {{ width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: #3498db; transition: width 0.3s ease; }}
        .task-list {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        .task-item {{ padding: 10px; border-bottom: 1px solid #ecf0f1; display: flex; justify-content: space-between; align-items: center; }}
        .status-badge {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }}
        .status-completed {{ background: #27ae60; }}
        .status-running {{ background: #3498db; }}
        .status-failed {{ background: #e74c3c; }}
        .status-pending {{ background: #95a5a6; }}
        .live-log {{ background: white; border-radius: 8px; padding: 20px; height: 300px; overflow-y: auto; }}
        .log-entry {{ padding: 5px 0; border-bottom: 1px solid #ecf0f1; font-family: monospace; font-size: 12px; }}
        #connectionStatus {{ position: fixed; top: 10px; right: 10px; padding: 5px 10px; border-radius: 4px; color: white; }}
        .connected {{ background: #27ae60; }}
        .disconnected {{ background: #e74c3c; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div id="connectionStatus" class="disconnected">Connecting...</div>

        <div class="header">
            <h1>🤖 Agent Orchestrator Dashboard</h1>
            <p id="workflowName">Loading...</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Overall Progress</h3>
                <div class="progress-bar">
                    <div id="overallProgress" class="progress-fill" style="width: 0%"></div>
                </div>
                <p id="progressText">0%</p>
            </div>

            <div class="metric-card">
                <h3>Task Status</h3>
                <p>✅ Completed: <span id="completedTasks">0</span></p>
                <p>⏳ Running: <span id="runningTasks">0</span></p>
                <p>❌ Failed: <span id="failedTasks">0</span></p>
                <p>⏸️ Pending: <span id="pendingTasks">0</span></p>
            </div>

            <div class="metric-card">
                <h3>Performance</h3>
                <p>Elapsed: <span id="elapsedTime">0</span> min</p>
                <p>Rate: <span id="taskRate">0</span> tasks/min</p>
                <p>ETA: <span id="eta">calculating...</span></p>
            </div>

            <div class="metric-card">
                <h3>Success Rate</h3>
                <p><span id="successRate">0</span>%</p>
                <p>Avg Duration: <span id="avgDuration">0</span>s</p>
            </div>
        </div>

        <div class="task-list">
            <h3>Tasks</h3>
            <div id="tasksList">Loading tasks...</div>
        </div>

        <div class="live-log">
            <h3>Live Activity Log</h3>
            <div id="logEntries"></div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:{self.port}');
        const connectionStatus = document.getElementById('connectionStatus');

        ws.onopen = function() {{
            connectionStatus.textContent = 'Connected';
            connectionStatus.className = 'connected';
        }};

        ws.onclose = function() {{
            connectionStatus.textContent = 'Disconnected';
            connectionStatus.className = 'disconnected';
        }};

        ws.onmessage = function(event) {{
            const message = JSON.parse(event.data);
            if (message.type === 'initial_state' || message.type === 'update') {{
                updateDashboard(message.data);
            }}
        }};

        function updateDashboard(data) {{
            const workflow = data.workflow;
            const tasks = data.tasks;
            const summary = data.summary;

            // Update workflow info
            document.getElementById('workflowName').textContent = workflow.workflow_name;

            // Update progress
            const progress = workflow.overall_progress;
            document.getElementById('overallProgress').style.width = progress + '%';
            document.getElementById('progressText').textContent = progress.toFixed(1) + '%';

            // Update task counts
            document.getElementById('completedTasks').textContent = workflow.completed_tasks;
            document.getElementById('runningTasks').textContent = workflow.running_tasks;
            document.getElementById('failedTasks').textContent = workflow.failed_tasks;
            document.getElementById('pendingTasks').textContent = workflow.pending_tasks;

            // Update performance metrics
            document.getElementById('elapsedTime').textContent = (summary.elapsed_time / 60).toFixed(1);
            document.getElementById('taskRate').textContent = summary.tasks_per_minute.toFixed(1);
            document.getElementById('eta').textContent = summary.eta_minutes ? summary.eta_minutes.toFixed(1) + ' min' : 'calculating...';
            document.getElementById('successRate').textContent = workflow.success_rate.toFixed(1);
            document.getElementById('avgDuration').textContent = workflow.average_task_duration.toFixed(1);

            // Update tasks list
            const tasksList = document.getElementById('tasksList');
            tasksList.innerHTML = '';
            for (const [taskId, task] of Object.entries(tasks)) {{
                const taskItem = document.createElement('div');
                taskItem.className = 'task-item';
                taskItem.innerHTML = `
                    <div>
                        <strong>${{task.task_id}}</strong> (${{{task.task_type}}})
                        <br><small>${{task.current_step}}</small>
                    </div>
                    <span class="status-badge status-${{task.status}}">${{task.status.toUpperCase()}}</span>
                `;
                tasksList.appendChild(taskItem);
            }}

            // Update live log
            const logEntries = document.getElementById('logEntries');
            logEntries.innerHTML = '';
            data.live_log.forEach(entry => {{
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                const timestamp = new Date(entry.timestamp).toLocaleTimeString();
                logEntry.innerHTML = `<strong>${{timestamp}}</strong> ${{entry.message}}`;
                logEntries.appendChild(logEntry);
            }});
            logEntries.scrollTop = logEntries.scrollHeight;
        }}
    </script>
</body>
</html>
        """


# Demo helper function
def create_demo_monitor(workflow_name: str) -> RealTimeMonitor:
    """Create a demo monitor with sample configuration"""
    workflow_id = f"demo_{int(time.time())}"
    monitor = RealTimeMonitor(workflow_id, workflow_name)

    # Configure for demo
    monitor.update_interval = 0.5  # Fast updates for demo

    return monitor


if __name__ == "__main__":
    # Demo the monitoring system
    monitor = create_demo_monitor("Real-time Monitoring Demo")

    # Start live monitoring
    monitor.start_live_monitoring(1.0)

    try:
        # Simulate workflow
        monitor.initialize_workflow(5)

        # Simulate tasks
        tasks = ["task_1", "task_2", "task_3", "task_4", "task_5"]
        for i, task_id in enumerate(tasks):
            monitor.register_task(task_id, f"demo_type_{i+1}")

        # Simulate execution
        for task_id in tasks:
            monitor.update_task_status(task_id, "running")
            time.sleep(2)

            # Simulate progress updates
            for progress in [25, 50, 75, 100]:
                monitor.update_task_progress(task_id, progress, f"Step {progress//25}")
                time.sleep(0.5)

            monitor.update_task_status(task_id, "completed")

        print("\n✅ Demo completed! Press Ctrl+C to exit...")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\n🛑 Monitoring stopped.")
