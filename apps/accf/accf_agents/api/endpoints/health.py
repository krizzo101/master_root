"""
Health check endpoints for the ACCF Research Agent.

This module provides health check and status endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import psutil
import time

from ...core.orchestrator import AgentOrchestrator
from ..app import get_orchestrator

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "ACCF Research Agent",
    }


@router.get("/detailed")
async def detailed_health_check(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Detailed health check with system metrics."""

    try:
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        # Agent status
        agent_status = orchestrator.get_agent_status()

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "ACCF Research Agent",
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "memory_total": memory.total,
            },
            "agents": agent_status,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/ready")
async def readiness_check(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Readiness check to ensure the service is ready to handle requests."""

    try:
        agent_status = orchestrator.get_agent_status()

        # Check if at least one agent is available
        if agent_status["total_agents"] == 0:
            raise HTTPException(status_code=503, detail="No agents available")

        return {
            "status": "ready",
            "timestamp": time.time(),
            "agents_available": agent_status["total_agents"],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")
