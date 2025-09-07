#!/usr/bin/env python3
"""
Agent Collaboration Server
FastAPI-based REST and WebSocket server for real-time agent collaboration
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from agent_collaboration_api import (
    AgentInfo,
    AgentStatus,
    CollaborationAPI,
    HelpRequestMessage,
    Message,
    MessageType,
    Priority,
    TaskHandoffMessage,
    WorkspaceUpdate,
)
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agent Collaboration API",
    description="Real-time communication system for multi-agent collaboration",
    version="1.0.0",
)

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize collaboration system
collaboration_api = CollaborationAPI(workspace_dir=Path("./collaboration_workspace"))


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        collaboration_api.websocket_connections[agent_id] = websocket
        logger.info(f"WebSocket connected for agent: {agent_id}")

    def disconnect(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        if agent_id in collaboration_api.websocket_connections:
            del collaboration_api.websocket_connections[agent_id]
        logger.info(f"WebSocket disconnected for agent: {agent_id}")

    async def send_personal_message(self, message: str, agent_id: str):
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str, exclude_agent: str = None):
        for agent_id, websocket in self.active_connections.items():
            if agent_id != exclude_agent:
                await websocket.send_text(message)


manager = ConnectionManager()


# Pydantic models for API requests/responses
class AgentRegistrationRequest(BaseModel):
    agent_id: str
    agent_type: str
    capabilities: List[str]
    workspace_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SendMessageRequest(BaseModel):
    message_type: str
    from_agent: str
    to_agent: Optional[str] = None
    content: Dict[str, Any]
    priority: str = "normal"
    workspace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    expires_at: Optional[str] = None


class TaskHandoffRequest(BaseModel):
    task_id: str
    task_type: str
    task_description: str
    from_agent: str
    to_agent: str
    context: Dict[str, Any] = {}
    dependencies: List[str] = []
    deadline: Optional[str] = None
    resources: Dict[str, Any] = {}


class HelpRequest(BaseModel):
    request_id: str
    requesting_agent: str
    help_type: str
    description: str
    context: Dict[str, Any] = {}
    urgency: str = "normal"
    skills_needed: List[str] = []


class WorkspaceArtifactRequest(BaseModel):
    workspace_id: str
    artifact_type: str
    name: str
    content: Dict[str, Any]
    author: str
    description: str = ""


class AgentStatusUpdate(BaseModel):
    status: str
    metadata: Dict[str, Any] = {}


# REST API Endpoints


@app.post("/api/v1/agents/register")
async def register_agent(request: AgentRegistrationRequest):
    """Register a new agent in the collaboration system"""
    try:
        agent_info = AgentInfo(
            agent_id=request.agent_id,
            agent_type=request.agent_type,
            capabilities=request.capabilities,
            status=AgentStatus.ONLINE,
            last_seen=datetime.now().isoformat(),
            workspace_id=request.workspace_id,
            metadata=request.metadata,
        )

        result = await collaboration_api.register_agent(agent_info)
        return result

    except Exception as e:
        logger.error(f"Agent registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents/active")
async def get_active_agents():
    """Get list of all active collaborating agents"""
    try:
        agents = await collaboration_api.get_active_agents()
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Get active agents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agents/{agent_id}/status")
async def update_agent_status(agent_id: str, request: AgentStatusUpdate):
    """Update agent status and metadata"""
    try:
        status = AgentStatus(request.status)
        result = await collaboration_api.update_agent_status(
            agent_id, status, request.metadata
        )
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")
    except Exception as e:
        logger.error(f"Update agent status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/messages/send")
async def send_message(request: SendMessageRequest):
    """Send message to agent(s)"""
    try:
        message = Message(
            message_id="",  # Will be generated automatically
            message_type=MessageType(request.message_type),
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            content=request.content,
            priority=Priority(request.priority),
            workspace_id=request.workspace_id,
            correlation_id=request.correlation_id,
            expires_at=request.expires_at,
        )

        result = await collaboration_api.send_message(message)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents/{agent_id}/messages")
async def get_messages(agent_id: str, max_messages: int = 10):
    """Get messages for a specific agent"""
    try:
        messages = await collaboration_api.get_messages(agent_id, max_messages)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/coordination/task-handoff")
async def request_task_handoff(request: TaskHandoffRequest):
    """Request task handoff between agents"""
    try:
        handoff_data = TaskHandoffMessage(
            task_id=request.task_id,
            task_type=request.task_type,
            task_description=request.task_description,
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            context=request.context,
            dependencies=request.dependencies,
            deadline=request.deadline,
            resources=request.resources,
        )

        message = Message(
            message_id="",
            message_type=MessageType.TASK_HANDOFF,
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            content=handoff_data.__dict__,
            priority=Priority.HIGH,
        )

        result = await collaboration_api.send_message(message)
        return result

    except Exception as e:
        logger.error(f"Task handoff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/coordination/help-request")
async def request_help(request: HelpRequest):
    """Broadcast help request to available agents"""
    try:
        help_data = HelpRequestMessage(
            request_id=request.request_id,
            requesting_agent=request.requesting_agent,
            help_type=request.help_type,
            description=request.description,
            context=request.context,
            urgency=Priority(request.urgency),
            skills_needed=request.skills_needed,
        )

        message = Message(
            message_id="",
            message_type=MessageType.HELP_REQUEST,
            from_agent=request.requesting_agent,
            to_agent=None,  # Broadcast
            content=help_data.__dict__,
            priority=Priority(request.urgency),
        )

        result = await collaboration_api.send_message(message)
        return result

    except Exception as e:
        logger.error(f"Help request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/workspace/share")
async def share_workspace_artifact(request: WorkspaceArtifactRequest):
    """Share workspace artifact with collaborating agents"""
    try:
        artifact_data = {
            "type": request.artifact_type,
            "name": request.name,
            "content": request.content,
            "author": request.author,
            "description": request.description,
            "created_at": datetime.now().isoformat(),
        }

        result = await collaboration_api.share_workspace_artifact(
            request.workspace_id, artifact_data
        )
        return result

    except Exception as e:
        logger.error(f"Share artifact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workspace/{workspace_id}/status")
async def get_workspace_status(workspace_id: str):
    """Get shared workspace status"""
    try:
        status = await collaboration_api.get_workspace_status(workspace_id)
        return status
    except Exception as e:
        logger.error(f"Get workspace status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time collaboration
@app.websocket("/ws/collaboration/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """Real-time collaboration WebSocket endpoint"""
    await manager.connect(websocket, agent_id)

    try:
        # Send welcome message
        welcome_msg = {
            "type": "connection_established",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Real-time collaboration established for agent {agent_id}",
        }
        await websocket.send_text(json.dumps(welcome_msg))

        # Handle incoming WebSocket messages
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)

                # Process different types of WebSocket messages
                if message_data.get("type") == "heartbeat":
                    # Update agent status
                    await collaboration_api.update_agent_status(
                        agent_id,
                        AgentStatus.ONLINE,
                        {"last_heartbeat": datetime.now().isoformat()},
                    )

                    # Send heartbeat response
                    response = {
                        "type": "heartbeat_ack",
                        "timestamp": datetime.now().isoformat(),
                    }
                    await websocket.send_text(json.dumps(response))

                elif message_data.get("type") == "message":
                    # Handle direct message sending via WebSocket
                    content = message_data.get("content", {})
                    message = Message(
                        message_id="",
                        message_type=MessageType(message_data.get("message_type")),
                        from_agent=agent_id,
                        to_agent=message_data.get("to_agent"),
                        content=content,
                        priority=Priority(message_data.get("priority", "normal")),
                    )

                    await collaboration_api.send_message(message)

                else:
                    logger.warning(
                        f"Unknown WebSocket message type: {message_data.get('type')}"
                    )

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {agent_id}: {data}")
            except Exception as e:
                logger.error(f"WebSocket message processing error: {e}")

    except WebSocketDisconnect:
        manager.disconnect(agent_id)
        # Update agent status to offline
        try:
            await collaboration_api.update_agent_status(agent_id, AgentStatus.OFFLINE)
        except:
            pass  # Agent might not be registered


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_agents": len(collaboration_api.agents),
        "active_websockets": len(manager.active_connections),
    }


# API documentation endpoints
@app.get("/api/v1/schema/message-types")
async def get_message_types():
    """Get available message types"""
    return {
        "message_types": [mt.value for mt in MessageType],
        "priorities": [p.value for p in Priority],
        "agent_statuses": [status.value for status in AgentStatus],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent Collaboration Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    uvicorn.run(
        "collaboration_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
