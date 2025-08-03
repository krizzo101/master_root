"""
Health Check API Endpoints

Provides health monitoring and system status endpoints for the ACCF Research Agent.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import time
import logging
from datetime import datetime

from capabilities.core.monitoring import get_monitoring, get_health_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    Comprehensive health check endpoint

    Returns:
        JSON response with system health status
    """
    try:
        start_time = time.time()

        # Get monitoring instances
        metrics, health_checker, performance_monitor, agent_metrics = get_monitoring()

        # Perform health check
        health_status = await health_checker.perform_health_check()

        # Record metrics
        duration = time.time() - start_time
        metrics.put_metric("health_check_duration", duration, "Seconds")
        metrics.put_metric("health_check_count", 1, "Count")

        # Determine HTTP status
        if health_status["status"] == "healthy":
            status_code = 200
        else:
            status_code = 503

        response_data = {
            "status": health_status["status"],
            "timestamp": health_status["timestamp"].isoformat(),
            "version": health_status.get("version", "1.0.0"),
            "duration": duration,
            "checks": health_status["checks"],
            "uptime": get_uptime(),
            "system_info": get_system_info(),
        }

        return JSONResponse(content=response_data, status_code=status_code)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        metrics.put_metric("health_check_failed", 1, "Count")

        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration

    Returns:
        JSON response indicating if the service is ready to receive traffic
    """
    try:
        # Perform basic health check
        health_status = await get_health_status()

        # Check if all critical services are healthy
        checks = health_status.get("checks", {})
        critical_services = ["neo4j", "openai"]

        all_ready = all(
            checks.get(service, {}).get("status") == "healthy"
            for service in critical_services
        )

        if all_ready:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready - critical dependencies unhealthy",
            )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration

    Returns:
        JSON response indicating if the service is alive
    """
    try:
        # Simple liveness check - just verify the process is running
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "pid": get_pid(),
        }

    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Liveness check failed: {str(e)}")


@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus-compatible metrics endpoint

    Returns:
        Text response with metrics in Prometheus format
    """
    try:
        metrics, _, _, _ = get_monitoring()

        # Record system metrics
        metrics.record_system_metrics()

        # Return basic metrics in Prometheus format
        # In a full implementation, this would collect and format all metrics
        prometheus_metrics = [
            "# HELP accf_research_agent_health_status Overall health status",
            "# TYPE accf_research_agent_health_status gauge",
            "accf_research_agent_health_status 1",
            "",
            "# HELP accf_research_agent_uptime_seconds Service uptime in seconds",
            "# TYPE accf_research_agent_uptime_seconds gauge",
            f"accf_research_agent_uptime_seconds {get_uptime_seconds()}",
            "",
            "# HELP accf_research_agent_version_info Version information",
            "# TYPE accf_research_agent_version_info gauge",
            'accf_research_agent_version_info{version="1.0.0"} 1',
        ]

        return "\n".join(prometheus_metrics)

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Metrics collection failed: {str(e)}"
        )


@router.get("/status")
async def detailed_status():
    """
    Detailed system status endpoint

    Returns:
        JSON response with comprehensive system status
    """
    try:
        metrics, health_checker, performance_monitor, agent_metrics = get_monitoring()

        # Get health status
        health_status = await health_checker.perform_health_check()

        # Get performance alerts
        alerts = performance_monitor.check_performance_alerts()

        # Compile detailed status
        status_data = {
            "health": health_status,
            "performance": {
                "alerts": alerts,
                "thresholds": performance_monitor.performance_thresholds,
            },
            "system": {
                "uptime": get_uptime(),
                "uptime_seconds": get_uptime_seconds(),
                "system_info": get_system_info(),
                "process_info": get_process_info(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        return status_data

    except Exception as e:
        logger.error(f"Detailed status failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Status collection failed: {str(e)}"
        )


def get_uptime() -> str:
    """Get system uptime as formatted string"""
    try:
        import psutil

        uptime_seconds = time.time() - psutil.boot_time()

        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    except Exception:
        return "unknown"


def get_uptime_seconds() -> float:
    """Get system uptime in seconds"""
    try:
        import psutil

        return time.time() - psutil.boot_time()
    except Exception:
        return 0.0


def get_system_info() -> Dict[str, Any]:
    """Get basic system information"""
    try:
        import psutil

        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_total": psutil.disk_usage("/").total,
            "platform": psutil.sys.platform,
            "python_version": psutil.sys.version,
        }
    except Exception:
        return {}


def get_process_info() -> Dict[str, Any]:
    """Get current process information"""
    try:
        import psutil

        process = psutil.Process()

        return {
            "pid": process.pid,
            "memory_usage": process.memory_info().rss,
            "cpu_percent": process.cpu_percent(),
            "create_time": process.create_time(),
            "num_threads": process.num_threads(),
        }
    except Exception:
        return {}


def get_pid() -> int:
    """Get current process ID"""
    try:
        import os

        return os.getpid()
    except Exception:
        return 0
