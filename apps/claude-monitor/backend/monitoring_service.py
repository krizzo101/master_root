#!/usr/bin/env python3
"""
Comprehensive monitoring backend service for Claude processes.
Provides FastAPI endpoints and WebSocket for real-time monitoring.
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import docker
import psutil
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "/home/opsvi/master_root/chat_logs.db"

app = FastAPI(
    title="Claude Monitoring Service",
    description="Real-time monitoring for Claude processes and system resources",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    load_average: List[float]
    timestamp: str


class TokenUsage(BaseModel):
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    sessions_count: int
    avg_tokens_per_session: float
    timestamp: str  # Store as ISO string instead of datetime


class DockerContainer(BaseModel):
    id: str
    name: str
    status: str
    image: str
    cpu_percent: float
    memory_usage: int
    memory_limit: int
    memory_percent: float
    created: str


class DashboardData(BaseModel):
    system_metrics: SystemMetrics
    token_usage: TokenUsage
    tool_usage: dict
    docker_containers: List[DockerContainer]
    active_sessions: int
    recent_tool_calls: int


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connection established. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket connection closed. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                dead_connections.append(connection)

        # Remove dead connections
        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()


# Database operations
def get_db_connection():
    """Create database connection with error handling."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


def get_token_usage() -> TokenUsage:
    """Query token usage from nodes table."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Query for token usage from raw_json field
            cursor.execute(
                """
                SELECT
                    COUNT(*) as sessions_count,
                    SUM(
                        CASE
                            WHEN json_extract(raw_json, '$.input_tokens') IS NOT NULL
                            THEN CAST(json_extract(raw_json, '$.input_tokens') AS INTEGER)
                            ELSE 0
                        END
                    ) as total_input_tokens,
                    SUM(
                        CASE
                            WHEN json_extract(raw_json, '$.output_tokens') IS NOT NULL
                            THEN CAST(json_extract(raw_json, '$.output_tokens') AS INTEGER)
                            ELSE 0
                        END
                    ) as total_output_tokens
                FROM nodes
                WHERE raw_json IS NOT NULL
                    AND datetime(timestamp) >= datetime('now', '-7 days')
            """
            )

            result = cursor.fetchone()
            if result and result["sessions_count"] > 0:
                total_input = result["total_input_tokens"] or 0
                total_output = result["total_output_tokens"] or 0
                sessions = result["sessions_count"]

                # Rough cost calculation (OpenAI-style pricing)
                total_cost = (total_input * 0.01 / 1000) + (total_output * 0.03 / 1000)
                avg_tokens = (
                    (total_input + total_output) / sessions if sessions > 0 else 0
                )

                return TokenUsage(
                    total_input_tokens=total_input,
                    total_output_tokens=total_output,
                    total_cost=round(total_cost, 4),
                    sessions_count=sessions,
                    avg_tokens_per_session=round(avg_tokens, 2),
                    timestamp=datetime.now().isoformat(),
                )

    except sqlite3.Error as e:
        logger.error(f"Token usage query error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in get_token_usage: {e}")

    # Return default values on error
    return TokenUsage(
        total_input_tokens=0,
        total_output_tokens=0,
        total_cost=0.0,
        sessions_count=0,
        avg_tokens_per_session=0.0,
        timestamp=datetime.now().isoformat(),
    )


def get_active_sessions() -> int:
    """Get count of active sessions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM sessions
                WHERE datetime(created_at) >= datetime('now', '-1 hour')
            """
            )
            result = cursor.fetchone()
            return result["count"] if result else 0
    except sqlite3.Error as e:
        logger.error(f"Active sessions query error: {e}")
        return 0


def get_recent_tool_calls() -> int:
    """Get count of recent tool calls."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM tool_calls
                WHERE datetime(timestamp) >= datetime('now', '-1 hour')
            """
            )
            result = cursor.fetchone()
            return result["count"] if result else 0
    except sqlite3.Error as e:
        logger.error(f"Recent tool calls query error: {e}")
        return 0


# System monitoring
def get_system_metrics() -> SystemMetrics:
    """Get current system resource metrics."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage
        disk = psutil.disk_usage("/")

        # Load average
        load_avg = (
            list(psutil.getloadavg())
            if hasattr(psutil, "getloadavg")
            else [0.0, 0.0, 0.0]
        )

        return SystemMetrics(
            cpu_percent=round(cpu_percent, 2),
            memory_percent=round(memory.percent, 2),
            memory_used=memory.used,
            memory_total=memory.total,
            disk_percent=round(disk.percent, 2),
            disk_used=disk.used,
            disk_total=disk.total,
            load_average=load_avg,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


# Docker monitoring
def get_docker_containers() -> List[DockerContainer]:
    """Get Docker containers with Claude processes."""
    containers = []
    try:
        client = docker.from_env()

        # Get all running containers
        for container in client.containers.list():
            try:
                # Get container stats
                stats = container.stats(stream=False)

                # Calculate CPU percentage with robust error handling
                cpu_percent = 0.0
                try:
                    cpu_usage = stats.get("cpu_stats", {}).get("cpu_usage", {})
                    precpu_usage = stats.get("precpu_stats", {}).get("cpu_usage", {})

                    if cpu_usage.get("total_usage") and precpu_usage.get("total_usage"):
                        cpu_delta = (
                            cpu_usage["total_usage"] - precpu_usage["total_usage"]
                        )
                        system_cpu = stats.get("cpu_stats", {}).get(
                            "system_cpu_usage", 0
                        )
                        presystem_cpu = stats.get("precpu_stats", {}).get(
                            "system_cpu_usage", 0
                        )
                        system_delta = system_cpu - presystem_cpu

                        if system_delta > 0 and cpu_usage.get("percpu_usage"):
                            cpu_percent = (
                                (cpu_delta / system_delta)
                                * len(cpu_usage["percpu_usage"])
                                * 100.0
                            )
                except (KeyError, TypeError, ZeroDivisionError):
                    cpu_percent = 0.0

                # Memory usage with robust error handling
                memory_usage = 0
                memory_limit = 1
                memory_percent = 0.0
                try:
                    memory_stats = stats.get("memory_stats", {})
                    memory_usage = memory_stats.get("usage", 0)
                    memory_limit = memory_stats.get("limit", 1)
                    if memory_limit > 0:
                        memory_percent = (memory_usage / memory_limit) * 100.0
                except (KeyError, TypeError, ZeroDivisionError):
                    memory_usage = 0
                    memory_limit = 1
                    memory_percent = 0.0

                # Check if this might be a Claude-related container
                is_claude_related = any(
                    keyword in container.name.lower()
                    or keyword in str(container.image).lower()
                    for keyword in ["claude", "ai", "llm", "chat", "assistant"]
                )

                container_info = DockerContainer(
                    id=container.id[:12],
                    name=container.name,
                    status=container.status,
                    image=str(container.image.tags[0])
                    if container.image.tags
                    else container.image.id[:12],
                    cpu_percent=round(cpu_percent, 2),
                    memory_usage=memory_usage,
                    memory_limit=memory_limit,
                    memory_percent=round(memory_percent, 2),
                    created=container.attrs["Created"],
                )

                # Prioritize Claude-related containers or include all if none found
                if is_claude_related or len(containers) < 10:
                    containers.append(container_info)

            except Exception as e:
                logger.warning(f"Error processing container {container.name}: {e}")
                continue

    except docker.errors.DockerException as e:
        logger.error(f"Docker connection error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in get_docker_containers: {e}")

    return containers


# API Endpoints
@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Get current dashboard data."""
    try:
        system_metrics = get_system_metrics()
        token_usage = get_token_usage()
        tool_usage_data = await get_tool_usage()  # Get tool usage data
        docker_containers = get_docker_containers()
        active_sessions = get_active_sessions()
        recent_tool_calls = get_recent_tool_calls()

        return DashboardData(
            system_metrics=system_metrics,
            token_usage=token_usage,
            tool_usage=tool_usage_data,
            docker_containers=docker_containers,
            active_sessions=active_sessions,
            recent_tool_calls=recent_tool_calls,
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@app.get("/api/tokens", response_model=TokenUsage)
async def get_tokens():
    """Get token usage statistics."""
    return get_token_usage()


@app.get("/api/tools")
async def get_tool_usage():
    """Get tool usage statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get top tools by usage count
            cursor.execute(
                """
                SELECT
                    tool_name,
                    COUNT(*) as usage_count,
                    COUNT(DISTINCT node_uuid) as unique_sessions,
                    datetime(MIN(timestamp)) as first_used,
                    datetime(MAX(timestamp)) as last_used
                FROM tool_calls
                WHERE datetime(timestamp) >= datetime('now', '-7 days')
                GROUP BY tool_name
                ORDER BY usage_count DESC
                LIMIT 20
            """
            )

            tools = [dict(row) for row in cursor.fetchall()]

            # Get total tool usage stats
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_calls,
                    COUNT(DISTINCT tool_name) as unique_tools,
                    COUNT(DISTINCT node_uuid) as sessions_with_tools
                FROM tool_calls
                WHERE datetime(timestamp) >= datetime('now', '-7 days')
            """
            )

            stats = dict(cursor.fetchone())

            return {
                "summary": stats,
                "top_tools": tools,
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Error fetching tool usage: {e}")
        return {"error": str(e)}


@app.get("/api/sessions")
async def get_session_analytics():
    """Get session analytics and statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get recent session summary
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_sessions,
                    COUNT(DISTINCT cwd) as unique_directories,
                    COUNT(DISTINCT git_branch) as unique_branches,
                    datetime(MIN(created_at)) as first_session,
                    datetime(MAX(created_at)) as latest_session
                FROM sessions
                WHERE datetime(created_at) >= datetime('now', '-7 days')
            """
            )

            session_stats = dict(cursor.fetchone())

            # Get most active sessions (by node count)
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.cwd,
                    s.git_branch,
                    COUNT(n.uuid) as node_count,
                    datetime(s.created_at) as created_at,
                    datetime(MAX(n.timestamp)) as last_activity
                FROM sessions s
                LEFT JOIN nodes n ON s.session_id = n.session_id
                WHERE datetime(s.created_at) >= datetime('now', '-7 days')
                GROUP BY s.session_id
                ORDER BY node_count DESC
                LIMIT 10
            """
            )

            active_sessions = [dict(row) for row in cursor.fetchall()]

            return {
                "summary": session_stats,
                "most_active_sessions": active_sessions,
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Error fetching session analytics: {e}")
        return {"error": str(e)}


@app.get("/api/docker", response_model=List[DockerContainer])
async def get_docker():
    """Get Docker container status."""
    return get_docker_containers()


@app.get("/api/system", response_model=SystemMetrics)
async def get_system():
    """Get system resource metrics."""
    return get_system_metrics()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any message from client (keepalive)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            except asyncio.TimeoutError:
                pass  # No message received, continue with update

            # Send updated data
            try:
                dashboard_data = await get_dashboard()
                await websocket.send_json(
                    {"type": "dashboard_update", "data": dashboard_data.dict()}
                )
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
                break

            # Wait before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


# Background task for broadcasting updates
async def broadcast_updates():
    """Background task to broadcast updates to all connected clients."""
    while True:
        try:
            if manager.active_connections:
                dashboard_data = await get_dashboard()
                await manager.broadcast(
                    {"type": "dashboard_update", "data": dashboard_data.dict()}
                )
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

        await asyncio.sleep(10)  # Broadcast every 10 seconds


@app.on_event("startup")
async def startup_event():
    """Start background tasks."""
    # Verify database exists
    if not Path(DB_PATH).exists():
        logger.warning(f"Database not found at {DB_PATH}")

    # Start background broadcast task
    asyncio.create_task(broadcast_updates())
    logger.info("Monitoring service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Monitoring service shutting down")


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "monitoring_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
