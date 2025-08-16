"""
REST API Server for Pattern Engine Service
FastAPI-based API with WebSocket support for real-time pattern updates
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
import logging
from contextlib import asynccontextmanager

from pattern_engine_core import DistributedPatternEngine, Pattern, PatternType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global pattern engine instance
engine: Optional[DistributedPatternEngine] = None
websocket_clients: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global engine
    
    # Startup
    logger.info("Starting Pattern Engine API Server")
    engine = DistributedPatternEngine(
        node_id=os.getenv("NODE_ID", "api_server"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    await engine.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Pattern Engine API Server")
    await engine.shutdown()


app = FastAPI(
    title="Pattern Engine Service",
    description="Distributed Pattern Recognition and Learning API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class InteractionRequest(BaseModel):
    """Request model for observing interactions"""
    task: Optional[str] = None
    tool_used: Optional[str] = None
    error: Optional[str] = None
    recovery_action: Optional[str] = None
    execution_time: Optional[float] = None
    method: Optional[str] = None
    success: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PatternRequest(BaseModel):
    """Request model for creating patterns"""
    type: str
    description: str
    trigger_conditions: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ContextRequest(BaseModel):
    """Request model for pattern matching"""
    context: Dict[str, Any]
    threshold: float = Field(default=0.3, ge=0.0, le=1.0)


class PatternUpdateRequest(BaseModel):
    """Request model for updating pattern outcomes"""
    pattern_id: str
    success: bool
    execution_time: float = 0.0


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "node_id": engine.node_id if engine else "not_initialized",
        "patterns": len(engine.patterns) if engine else 0,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/observe")
async def observe_interaction(request: InteractionRequest, background_tasks: BackgroundTasks):
    """Observe an interaction and extract patterns"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    interaction = request.dict(exclude_none=True)
    interaction['timestamp'] = datetime.now().isoformat()
    
    result = await engine.observe_interaction(interaction)
    
    # Broadcast to WebSocket clients
    background_tasks.add_task(broadcast_update, {
        "type": "observation",
        "data": result
    })
    
    return result


@app.post("/patterns")
async def create_pattern(request: PatternRequest):
    """Manually create a new pattern"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        pattern_type = PatternType(request.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid pattern type: {request.type}")
    
    pattern = Pattern(
        id=f"manual_{datetime.now().timestamp()}",
        type=pattern_type,
        description=request.description,
        trigger_conditions=request.trigger_conditions,
        actions=request.actions,
        confidence=request.confidence,
        source_node=engine.node_id
    )
    
    success = await engine.register_pattern(pattern)
    
    if success:
        return {"status": "created", "pattern_id": pattern.id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create pattern")


@app.get("/patterns")
async def list_patterns(pattern_type: Optional[str] = None):
    """List all patterns or filter by type"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    if pattern_type:
        try:
            ptype = PatternType(pattern_type)
            patterns = [p.to_dict() for p in engine.patterns.values() if p.type == ptype]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid pattern type: {pattern_type}")
    else:
        patterns = [p.to_dict() for p in engine.patterns.values()]
    
    return {
        "total": len(patterns),
        "patterns": patterns
    }


@app.get("/patterns/{pattern_id}")
async def get_pattern(pattern_id: str):
    """Get details of a specific pattern"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    pattern = engine.patterns.get(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    return pattern.to_dict()


@app.post("/match")
async def match_patterns(request: ContextRequest):
    """Find patterns matching the given context"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    matches = await engine.find_matching_patterns(request.context, request.threshold)
    
    return {
        "matches": [
            {
                "pattern_id": pattern_id,
                "score": score,
                "pattern": engine.patterns[pattern_id].to_dict()
            }
            for pattern_id, score in matches
        ]
    }


@app.post("/recommend")
async def get_recommendations(request: ContextRequest):
    """Get action recommendations based on patterns"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    recommendations = await engine.get_recommendations(request.context)
    
    return {
        "recommendations": recommendations
    }


@app.post("/patterns/update")
async def update_pattern_outcome(request: PatternUpdateRequest):
    """Update pattern statistics based on execution outcome"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    if request.pattern_id not in engine.patterns:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # Update pattern stats
    pattern = engine.patterns[request.pattern_id]
    stats = engine.pattern_stats[request.pattern_id]
    
    if request.success:
        stats['successes'] += 1
    else:
        stats['failures'] += 1
    
    stats['total_time'] += request.execution_time
    
    # Update pattern metrics
    pattern.last_used = datetime.now()
    pattern.success_rate = stats['successes'] / (stats['successes'] + stats['failures'])
    pattern.avg_execution_time = stats['total_time'] / (stats['successes'] + stats['failures'])
    
    return {"status": "updated", "pattern_id": request.pattern_id}


@app.get("/statistics")
async def get_statistics():
    """Get pattern engine statistics"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return engine.get_statistics()


@app.delete("/patterns/{pattern_id}")
async def delete_pattern(pattern_id: str):
    """Delete a pattern"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    if pattern_id not in engine.patterns:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    del engine.patterns[pattern_id]
    
    # Remove from index
    for pattern_set in engine.pattern_index.values():
        pattern_set.discard(pattern_id)
    
    return {"status": "deleted", "pattern_id": pattern_id}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time pattern updates"""
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        # Send initial statistics
        await websocket.send_json({
            "type": "connected",
            "data": engine.get_statistics() if engine else {}
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "stats":
                await websocket.send_json({
                    "type": "statistics",
                    "data": engine.get_statistics() if engine else {}
                })
                
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)


async def broadcast_update(message: Dict[str, Any]):
    """Broadcast updates to all WebSocket clients"""
    disconnected = []
    
    for client in websocket_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)
    
    # Clean up disconnected clients
    for client in disconnected:
        if client in websocket_clients:
            websocket_clients.remove(client)


# Batch operations endpoint
@app.post("/batch/observe")
async def batch_observe(interactions: List[InteractionRequest]):
    """Observe multiple interactions in batch"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    results = []
    for interaction_req in interactions:
        interaction = interaction_req.dict(exclude_none=True)
        interaction['timestamp'] = datetime.now().isoformat()
        result = await engine.observe_interaction(interaction)
        results.append(result)
    
    return {
        "processed": len(results),
        "results": results
    }


# Federation endpoints
@app.get("/federation/status")
async def federation_status():
    """Get federation status"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return {
        "node_id": engine.node_id,
        "redis_connected": engine.redis_client is not None,
        "federation_channel": engine.federation_channel,
        "discovery_channel": engine.discovery_channel,
        "local_patterns": sum(1 for p in engine.patterns.values() if p.source_node == engine.node_id),
        "federated_patterns": sum(1 for p in engine.patterns.values() if p.source_node != engine.node_id)
    }


@app.post("/federation/sync")
async def sync_patterns():
    """Force sync with distributed patterns"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    if not engine.redis_client:
        raise HTTPException(status_code=503, detail="Redis not connected")
    
    await engine._sync_distributed_patterns()
    
    return {
        "status": "synced",
        "total_patterns": len(engine.patterns)
    }


import os
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )