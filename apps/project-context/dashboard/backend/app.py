#!/usr/bin/env python3
"""
Real-Time Orchestrator Monitoring Dashboard Backend
FastAPI application with WebSocket support for live updates
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add paths for orchestrator integration
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from monitoring_service import MonitoringService
from websocket_handler import WebSocketManager
from database_integration import dashboard_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Orchestrator Monitoring Dashboard",
    description="Real-time monitoring for PracticalOrchestrator execution",
    version="1.0.0",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
monitoring_service = MonitoringService()
websocket_manager = WebSocketManager()


# Data models
class SystemStatus(BaseModel):
    overall_progress: float
    current_phase: Optional[str]
    elapsed_minutes: float
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_tasks: int


class TaskDetail(BaseModel):
    task_id: str
    task_type: str
    status: str
    session_id: Optional[str]
    phase_id: Optional[str]
    start_time: Optional[float]
    end_time: Optional[float]
    duration: Optional[float]
    files_created: List[str]
    files_modified: List[str]
    metrics: Dict
    error: Optional[str]


class PerformanceMetrics(BaseModel):
    parallel_utilization: float
    tasks_per_hour: float
    average_task_duration: float
    success_rate: float
    fastest_task: Optional[Dict]
    slowest_task: Optional[Dict]


# API Endpoints


@app.get("/")
async def serve_dashboard():
    """Serve the main dashboard HTML"""
    return FileResponse("frontend/index.html")


@app.get("/api/status")
async def get_system_status() -> SystemStatus:
    """Get current system status overview"""
    try:
        status = await monitoring_service.get_system_status()
        return SystemStatus(**status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def get_all_tasks() -> List[TaskDetail]:
    """Get detailed information for all tasks"""
    try:
        tasks = await monitoring_service.get_all_tasks()
        return [TaskDetail(**task) for task in tasks]
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}")
async def get_task_detail(task_id: str) -> TaskDetail:
    """Get detailed information for a specific task"""
    try:
        task = await monitoring_service.get_task_detail(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskDetail(**task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance")
async def get_performance_metrics() -> PerformanceMetrics:
    """Get performance metrics and analytics"""
    try:
        metrics = await monitoring_service.get_performance_metrics()
        return PerformanceMetrics(**metrics)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/{task_id}")
async def get_task_logs(task_id: str, lines: int = 100):
    """Get recent log entries for a specific task"""
    try:
        logs = await monitoring_service.get_task_logs(task_id, lines)
        return {"task_id": task_id, "logs": logs}
    except Exception as e:
        logger.error(f"Error getting logs for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quality-report")
async def get_quality_report():
    """Get the latest quality report"""
    try:
        report = await monitoring_service.get_quality_report()
        return report
    except Exception as e:
        logger.error(f"Error getting quality report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "monitoring_active": monitoring_service.is_active(),
    }


# Enhanced WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint for real-time dashboard updates with improved error handling"""
    client_id = None
    try:
        # Enhanced connection with client ID tracking
        client_id = await websocket_manager.connect(websocket)
        if not client_id:
            logger.warning("WebSocket connection rejected")
            return

        logger.info(f"WebSocket client {client_id} connected successfully")

        while True:
            try:
                # Wait for client messages with timeout to prevent hanging
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                # Enhanced message handling through the manager
                await websocket_manager.handle_client_message(websocket, message)

            except asyncio.TimeoutError:
                # Send periodic heartbeat to check connection health
                try:
                    await websocket.send_json(
                        {
                            "type": "heartbeat_check",
                            "timestamp": time.time(),
                            "client_id": client_id,
                        }
                    )
                except Exception:
                    logger.info(
                        f"Client {client_id} connection lost during heartbeat check"
                    )
                    break

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received from client {client_id}: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "client_id": client_id,
                    }
                )

            except Exception as e:
                logger.error(
                    f"WebSocket message handling error for client {client_id}: {e}"
                )
                break

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected gracefully")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        if client_id:
            await websocket_manager.disconnect(client_id)
        else:
            # Fallback for backward compatibility
            await websocket_manager.disconnect(websocket=websocket)


# Background task for periodic updates
@app.on_event("startup")
async def startup_event():
    """Initialize enhanced background monitoring on startup"""
    logger.info("Starting Enhanced Orchestrator Monitoring Dashboard")
    
    # Initialize database connections
    await dashboard_db.initialize()

    # Initialize WebSocket manager statistics
    websocket_manager.initialize_stats()

    # Start background monitoring services
    monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())
    websocket_task = asyncio.create_task(websocket_manager.start_broadcast_loop())

    # Store tasks for graceful shutdown
    app.state.background_tasks = {
        "monitoring": monitoring_task,
        "websocket": websocket_task,
    }

    # Mount static files (with error handling)
    try:
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")

    logger.info("Enhanced Dashboard backend ready with WebSocket real-time updates")


@app.on_event("shutdown")
async def shutdown_event():
    """Enhanced cleanup on shutdown with graceful task termination"""
    logger.info("Shutting down Enhanced Monitoring Dashboard")

    try:
        # Stop services gracefully
        await monitoring_service.stop_monitoring()
        await websocket_manager.stop_broadcast()

        # Cancel background tasks if they exist
        if hasattr(app.state, "background_tasks"):
            for task_name, task in app.state.background_tasks.items():
                if not task.done():
                    logger.info(f"Cancelling {task_name} task")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info(f"{task_name} task cancelled successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Dashboard shutdown complete")


# New comprehensive analytics endpoints
@app.get("/api/analytics")
async def get_task_analytics():
    """Get comprehensive task analytics and insights"""
    try:
        analytics = await monitoring_service.get_task_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live-data")
async def get_live_monitoring_data():
    """Get comprehensive live monitoring data for dashboard"""
    try:
        data = await monitoring_service.get_live_monitoring_data()
        return data
    except Exception as e:
        logger.error(f"Error getting live data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/directories")
async def get_output_directories():
    """Get list of monitored output directories"""
    try:
        directories = [
            {
                "path": str(d),
                "name": d.name,
                "exists": d.exists(),
                "task_count": len(list((d / "tasks").glob("*.json")))
                if (d / "tasks").exists()
                else 0,
            }
            for d in monitoring_service.output_dirs
        ]
        return {"directories": directories, "total": len(directories)}
    except Exception as e:
        logger.error(f"Error getting directories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/websocket-stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    try:
        stats = websocket_manager.get_connection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Database endpoints
@app.get("/api/database-status")
async def get_database_status():
    """Get database connection status"""
    try:
        status = await dashboard_db.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/project-stats")
async def get_project_stats():
    """Get project statistics from database"""
    try:
        stats = await dashboard_db.get_project_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search-context")
async def search_context(q: str, limit: int = 10):
    """Search context items in database"""
    try:
        results = await dashboard_db.search_context(q, limit)
        return results
    except Exception as e:
        logger.error(f"Error searching context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Development endpoint for testing
@app.get("/api/simulate-progress")
async def simulate_progress():
    """Simulate progress updates for development/testing"""
    if app.debug:
        await monitoring_service.simulate_task_progress()
        return {"message": "Progress simulation triggered"}
    else:
        raise HTTPException(status_code=403, detail="Only available in debug mode")


if __name__ == "__main__":
    # Run the server
    uvicorn.run("app:app", host="0.0.0.0", port=8004, reload=True, log_level="info")
