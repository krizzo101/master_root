"""
Agent management endpoints for the ACCF Research Agent.

This module provides endpoints for managing and monitoring agents.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...core.orchestrator import AgentOrchestrator
from ..app import get_orchestrator

router = APIRouter()


@router.get("/")
async def list_agents(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """List all available agents."""

    try:
        agent_status = orchestrator.get_agent_status()
        return {
            "total_agents": agent_status["total_agents"],
            "agents": agent_status["agents"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/{agent_name}")
async def get_agent_details(
    agent_name: str, orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """Get details for a specific agent."""

    try:
        agent_status = orchestrator.get_agent_status()

        if agent_name not in agent_status["agents"]:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_name}' not found"
            )

        return {"name": agent_name, "details": agent_status["agents"][agent_name]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent details: {str(e)}"
        )


@router.get("/{agent_name}/capabilities")
async def get_agent_capabilities(
    agent_name: str, orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """Get capabilities for a specific agent."""

    try:
        agent = orchestrator.agents.get(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_name}' not found"
            )

        return {"agent_name": agent_name, "capabilities": agent.get_capabilities()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent capabilities: {str(e)}"
        )


@router.post("/{agent_name}/test")
async def test_agent(
    agent_name: str,
    test_data: Dict[str, Any],
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Test a specific agent with sample data."""

    try:
        agent = orchestrator.agents.get(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_name}' not found"
            )

        # Create a test task
        from ...agents import Task

        test_task = Task(
            id="test-task",
            type=test_data.get("task_type", "test"),
            parameters=test_data.get("parameters", {}),
        )

        # Execute test task
        result = await agent.execute(test_task)

        return {
            "agent_name": agent_name,
            "test_result": {
                "status": result.status,
                "data": result.data,
                "error_message": result.error_message,
                "execution_time": result.execution_time,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent test failed: {str(e)}")


@router.get("/status/overview")
async def get_agents_overview(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Get an overview of all agents status."""

    try:
        agent_status = orchestrator.get_agent_status()

        # Calculate summary statistics
        total_agents = agent_status["total_agents"]
        initialized_agents = sum(
            1
            for agent_info in agent_status["agents"].values()
            if agent_info["initialized"]
        )

        return {
            "total_agents": total_agents,
            "initialized_agents": initialized_agents,
            "health_percentage": (
                (initialized_agents / total_agents * 100) if total_agents > 0 else 0
            ),
            "agents": agent_status["agents"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get agents overview: {str(e)}"
        )
