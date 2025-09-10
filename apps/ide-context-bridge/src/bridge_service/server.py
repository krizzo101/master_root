#!/usr/bin/env python3
"""
IDE Context Bridge Server

Main server that handles WebSocket and HTTP requests for IDE integration.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import verify_api_key
from .config import BridgeConfig
from .context_manager import ContextManager
from .metrics import MetricsCollector
from .models import (
    BridgeResponse,
    HealthResponse,
    IDEContextMessage,
    SearchRequest,
    SuggestionRequest,
)
from .suggestion_engine import SuggestionEngine
from .websocket_handler import ConnectionManager, WebSocketHandler

logger = logging.getLogger(__name__)


class BridgeServer:
    """
    Main server class for the IDE Context Bridge.

    Handles:
    - WebSocket connections for real-time communication
    - HTTP REST API for request-response operations
    - Context management and persistence
    - Intelligent suggestion generation
    """

    def __init__(self, config: BridgeConfig):
        """Initialize the bridge server with configuration."""
        self.config = config
        self.app = FastAPI(
            title="IDE Context Bridge API",
            description="Bridge between IDEs and unified context system",
            version="1.0.0",
        )

        # Core components
        self.connection_manager = ConnectionManager()
        self.context_manager: Optional[ContextManager] = None
        self.suggestion_engine: Optional[SuggestionEngine] = None
        self.websocket_handler: Optional[WebSocketHandler] = None
        self.metrics = MetricsCollector()
        self.redis_client: Optional[redis.Redis] = None

        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            process_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )

            # Record metrics
            self.metrics.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=process_time,
            )

            return response

    def _setup_routes(self):
        """Setup API routes."""

        # Health check
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now(),
                version="1.0.0",
                active_connections=len(self.connection_manager.active_connections),
                active_sessions=len(self.active_sessions),
            )

        # Metrics endpoint
        @self.app.get("/metrics")
        async def get_metrics():
            """Prometheus metrics endpoint."""
            return self.metrics.get_prometheus_metrics()

        # Context management
        @self.app.post("/api/v1/context")
        async def update_context(
            context_msg: IDEContextMessage,
            background_tasks: BackgroundTasks,
            api_key: str = Depends(verify_api_key),
        ):
            """Update IDE context via HTTP."""
            try:
                # Process context update in background
                background_tasks.add_task(self._process_context_update, context_msg)

                return BridgeResponse(
                    type="context_ack",
                    timestamp=datetime.now(),
                    session_id=context_msg.session_id,
                    data={"status": "accepted"},
                )

            except Exception as e:
                logger.error(f"Context update failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Search endpoint
        @self.app.post("/api/v1/search")
        async def search_context(
            search_req: SearchRequest, api_key: str = Depends(verify_api_key)
        ):
            """Search context items."""
            try:
                if not self.suggestion_engine:
                    raise HTTPException(
                        status_code=503, detail="Suggestion engine not available"
                    )

                start_time = datetime.now()
                results = await self.suggestion_engine.search_context(
                    query=search_req.query,
                    search_type=search_req.type,
                    filters=search_req.filters,
                    max_results=search_req.max_results or 10,
                )

                response_time = (datetime.now() - start_time).total_seconds()

                return BridgeResponse(
                    type="search_results",
                    timestamp=datetime.now(),
                    request_id=search_req.request_id,
                    session_id=search_req.session_id,
                    data={
                        "search_results": results,
                        "metrics": {
                            "response_time_ms": int(response_time * 1000),
                            "result_count": len(results),
                        },
                    },
                )

            except Exception as e:
                logger.error(f"Search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Suggestions endpoint
        @self.app.post("/api/v1/suggestions")
        async def get_suggestions(
            suggestion_req: SuggestionRequest, api_key: str = Depends(verify_api_key)
        ):
            """Get intelligent code suggestions."""
            try:
                if not self.suggestion_engine:
                    raise HTTPException(
                        status_code=503, detail="Suggestion engine not available"
                    )

                start_time = datetime.now()
                suggestions = await self.suggestion_engine.generate_suggestions(
                    session_id=suggestion_req.session_id,
                    file_path=suggestion_req.file_path,
                    cursor_position=suggestion_req.cursor_position,
                    context=suggestion_req.context,
                    suggestion_types=suggestion_req.types,
                )

                response_time = (datetime.now() - start_time).total_seconds()

                return BridgeResponse(
                    type="suggestions",
                    timestamp=datetime.now(),
                    request_id=suggestion_req.request_id,
                    session_id=suggestion_req.session_id,
                    data={
                        "suggestions": suggestions,
                        "metrics": {
                            "response_time_ms": int(response_time * 1000),
                            "suggestion_count": len(suggestions),
                        },
                    },
                )

            except Exception as e:
                logger.error(f"Suggestion generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # WebSocket endpoint
        @self.app.websocket("/ide-bridge")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            if not self.websocket_handler:
                await websocket.close(code=1013, reason="Service unavailable")
                return

            await self.websocket_handler.handle_connection(websocket)

    async def initialize(self):
        """Initialize all service components."""
        try:
            logger.info("Initializing IDE Context Bridge Service...")

            # Initialize Redis connection
            if self.config.redis_url:
                self.redis_client = redis.from_url(
                    self.config.redis_url, decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Redis connection established")

            # Initialize core components
            self.context_manager = ContextManager(
                postgres_url=self.config.postgres_url, redis_client=self.redis_client
            )
            await self.context_manager.initialize()

            self.suggestion_engine = SuggestionEngine(
                context_manager=self.context_manager,
                embedding_service_url=self.config.embedding_service_url,
                config=self.config,
            )
            await self.suggestion_engine.initialize()

            self.websocket_handler = WebSocketHandler(
                connection_manager=self.connection_manager,
                context_manager=self.context_manager,
                suggestion_engine=self.suggestion_engine,
            )

            logger.info("IDE Context Bridge Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize service: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources on shutdown."""
        logger.info("Shutting down IDE Context Bridge Service...")

        # Close all WebSocket connections
        await self.connection_manager.disconnect_all()

        # Cleanup components
        if self.suggestion_engine:
            await self.suggestion_engine.cleanup()

        if self.context_manager:
            await self.context_manager.cleanup()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Service shutdown complete")

    async def _process_context_update(self, context_msg: IDEContextMessage):
        """Process context update in background."""
        try:
            if not self.context_manager:
                logger.error("Context manager not available")
                return

            # Update context
            await self.context_manager.update_context(
                session_id=context_msg.session_id, context_data=context_msg.dict()
            )

            # Update session tracking
            self.active_sessions[context_msg.session_id] = {
                "last_update": datetime.now(),
                "editor_id": context_msg.editor_id,
                "active_file": context_msg.active_file.path
                if context_msg.active_file
                else None,
            }

            # Broadcast to WebSocket connections if needed
            if context_msg.session_id in self.connection_manager.active_connections:
                await self.connection_manager.send_to_session(
                    session_id=context_msg.session_id,
                    message={
                        "type": "context_updated",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        except Exception as e:
            logger.error(f"Failed to process context update: {e}")

    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the server."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level=self.config.log_level.lower(),
            access_log=True,
        )


async def create_bridge_server(config: BridgeConfig) -> BridgeServer:
    """Factory function to create and initialize bridge server."""
    server = BridgeServer(config)
    await server.initialize()
    return server


if __name__ == "__main__":
    import argparse

    from .config import load_config

    parser = argparse.ArgumentParser(description="IDE Context Bridge Server")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def run_server():
        server = await create_bridge_server(config)

        try:
            server.run(host=args.host, port=args.port)
        finally:
            await server.cleanup()

    asyncio.run(run_server())
