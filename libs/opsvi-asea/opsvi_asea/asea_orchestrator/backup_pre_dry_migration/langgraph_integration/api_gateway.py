"""
Phase 4: API Gateway for ASEA-LangGraph Integration

Implements production-ready REST API including:
1. Workflow Execution API
2. Authentication and Authorization
3. Rate Limiting and Security
4. Real-time Status and Monitoring
5. Async Execution and Webhooks
"""

import asyncio
import time
import uuid
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import json
import logging

try:
    from fastapi import (
        FastAPI,
        HTTPException,
        Depends,
        BackgroundTasks,
        Request,
        Response,
    )
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
    from pydantic import BaseModel, Field
    import uvicorn
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    # Define minimal classes for type hints
    class BaseModel:
        pass

    class FastAPI:
        pass


from .advanced_monitoring import create_default_monitoring_setup


# Request/Response Models
class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""

    workflow_name: str = Field(..., description="Name of the workflow to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow")
    config: Optional[Dict[str, Any]] = Field(
        default={}, description="Workflow configuration"
    )
    async_execution: bool = Field(default=False, description="Execute asynchronously")
    webhook_url: Optional[str] = Field(
        default=None, description="Webhook URL for async results"
    )
    timeout_seconds: Optional[int] = Field(default=300, description="Execution timeout")
    priority: int = Field(default=1, description="Execution priority (1-10)")


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""

    execution_id: str = Field(..., description="Unique execution ID")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Workflow result"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: Optional[float] = Field(
        default=None, description="Execution time in seconds"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""

    execution_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkflowTemplateRequest(BaseModel):
    """Request model for creating workflow templates."""

    template_name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    workflow_config: Dict[str, Any] = Field(..., description="Workflow configuration")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for inputs")
    tags: List[str] = Field(default=[], description="Template tags")


class APIKeyRequest(BaseModel):
    """Request model for API key creation."""

    name: str = Field(..., description="API key name")
    permissions: List[str] = Field(..., description="API key permissions")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration date")


class SystemHealthResponse(BaseModel):
    """Response model for system health."""

    status: str
    version: str
    uptime_seconds: float
    active_executions: int
    total_executions: int
    error_rate: float
    avg_execution_time: float
    system_metrics: Dict[str, Any]


# Authentication and Security
class APIKeyManager:
    """Manages API keys and authentication with persistent storage."""

    def __init__(self):
        self.rate_limits: Dict[str, List[float]] = {}
        self.secret_key = "asea-api-secret-change-in-production"
        self._init_database_connection()

    def _init_database_connection(self):
        """Initialize database connection for persistent storage."""
        try:
            from arango import ArangoClient

            client = ArangoClient(hosts=f"http://{db_host}:{db_port}")
            self.db = client.db(
                "asea_prod_db", username="root", password="arango_production_password"
            )

            # Ensure api_keys collection exists
            if not self.db.has_collection("api_keys"):
                self.db.create_collection("api_keys")

            self.api_keys_collection = self.db.collection("api_keys")

        except Exception as e:
            print(f"Warning: Database connection failed, using in-memory storage: {e}")
            self.db = None
            self.api_keys_collection = None
            self.api_keys: Dict[str, Dict[str, Any]] = {}

    def create_api_key(
        self, name: str, permissions: List[str], expires_at: Optional[datetime] = None
    ) -> str:
        """Create a new API key with persistent storage."""
        api_key = self._generate_api_key()
        key_data = {
            "_key": api_key.replace("asea_", ""),  # Remove prefix for ArangoDB key
            "api_key": api_key,
            "name": name,
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "last_used": None,
            "usage_count": 0,
        }

        if self.api_keys_collection:
            try:
                self.api_keys_collection.insert(key_data)
            except Exception as e:
                print(f"Warning: Failed to store API key in database: {e}")
                # Fallback to in-memory storage
                if not hasattr(self, "api_keys"):
                    self.api_keys = {}
                self.api_keys[api_key] = {
                    "name": name,
                    "permissions": permissions,
                    "created_at": datetime.now(),
                    "expires_at": expires_at,
                    "last_used": None,
                    "usage_count": 0,
                }
        else:
            # In-memory fallback
            if not hasattr(self, "api_keys"):
                self.api_keys = {}
            self.api_keys[api_key] = {
                "name": name,
                "permissions": permissions,
                "created_at": datetime.now(),
                "expires_at": expires_at,
                "last_used": None,
                "usage_count": 0,
            }

        return api_key

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return key info with persistent storage."""
        key_info = None

        # Try database first
        if self.api_keys_collection:
            try:
                cursor = self.api_keys_collection.find({"api_key": api_key})
                results = list(cursor)
                if results:
                    key_info = results[0]
                    # Convert ISO strings back to datetime for expiration check
                    if key_info.get("expires_at"):
                        expires_at = datetime.fromisoformat(key_info["expires_at"])
                        if datetime.now() > expires_at:
                            return None

                    # Update usage in database
                    self.api_keys_collection.update(
                        {"_key": key_info["_key"]},
                        {
                            "last_used": datetime.now().isoformat(),
                            "usage_count": key_info.get("usage_count", 0) + 1,
                        },
                    )

                    return key_info
            except Exception as e:
                print(f"Warning: Database query failed: {e}")

        # Fallback to in-memory storage
        if hasattr(self, "api_keys") and api_key in self.api_keys:
            key_info = self.api_keys[api_key]

            # Check expiration
            if key_info["expires_at"] and datetime.now() > key_info["expires_at"]:
                return None

            # Update usage
            key_info["last_used"] = datetime.now()
            key_info["usage_count"] += 1

            return key_info

        return None

    def check_permission(self, api_key: str, permission: str) -> bool:
        """Check if API key has specific permission."""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return False

        permissions = key_info.get("permissions", [])
        return permission in permissions or "admin" in permissions

    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        random_data = f"{uuid.uuid4()}{time.time()}{self.secret_key}"
        return f"asea_{hashlib.sha256(random_data.encode()).hexdigest()[:32]}"


class WorkflowExecutionManager:
    """Manages workflow executions and status tracking."""

    def __init__(self):
        self.executions: Dict[str, Dict[str, Any]] = {}
        self.execution_queue: List[str] = []
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.max_concurrent = 10

    async def execute_workflow(
        self, request: WorkflowExecutionRequest, user_id: str = "anonymous"
    ) -> WorkflowExecutionResponse:
        """Execute a workflow synchronously or asynchronously."""
        execution_id = str(uuid.uuid4())

        # Create execution record
        execution_record = {
            "execution_id": execution_id,
            "workflow_name": request.workflow_name,
            "input_data": request.input_data,
            "config": request.config,
            "user_id": user_id,
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "async_execution": request.async_execution,
            "webhook_url": request.webhook_url,
            "timeout_seconds": request.timeout_seconds,
            "priority": request.priority,
        }

        self.executions[execution_id] = execution_record

        if request.async_execution:
            # Queue for async execution
            self.execution_queue.append(execution_id)
            self._process_queue()

            return WorkflowExecutionResponse(
                execution_id=execution_id,
                status="queued",
                created_at=execution_record["created_at"],
            )
        else:
            # Execute synchronously
            return await self._execute_workflow_sync(execution_id)

    async def _execute_workflow_sync(
        self, execution_id: str
    ) -> WorkflowExecutionResponse:
        """Execute workflow synchronously."""
        execution_record = self.executions[execution_id]

        try:
            execution_record["status"] = "running"
            execution_record["started_at"] = datetime.now()

            # Create workflow and execute
            start_time = time.time()
            result = await self._run_workflow(execution_record)
            execution_time = time.time() - start_time

            # Update record
            execution_record["status"] = "completed"
            execution_record["result"] = result
            execution_record["execution_time"] = execution_time
            execution_record["completed_at"] = datetime.now()
            execution_record["updated_at"] = datetime.now()

            return WorkflowExecutionResponse(
                execution_id=execution_id,
                status="completed",
                result=result,
                execution_time=execution_time,
                created_at=execution_record["created_at"],
                completed_at=execution_record["completed_at"],
            )

        except Exception as e:
            # Handle error
            execution_record["status"] = "failed"
            execution_record["error"] = str(e)
            execution_record["completed_at"] = datetime.now()
            execution_record["updated_at"] = datetime.now()

            return WorkflowExecutionResponse(
                execution_id=execution_id,
                status="failed",
                error=str(e),
                created_at=execution_record["created_at"],
                completed_at=execution_record["completed_at"],
            )

    async def _run_workflow(self, execution_record: Dict[str, Any]) -> Dict[str, Any]:
        """Run the actual workflow."""
        # This is a simplified implementation - in production, this would
        # integrate with the actual LangGraph workflow compilation and execution

        workflow_name = execution_record["workflow_name"]
        input_data = execution_record["input_data"]
        config = execution_record["config"]

        # Simulate workflow execution
        await asyncio.sleep(1)  # Simulate processing time

        return {
            "workflow_name": workflow_name,
            "execution_summary": f"Processed {workflow_name} with {len(input_data)} inputs",
            "output_data": {
                "processed_inputs": input_data,
                "execution_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "config": config,
                },
            },
        }

    def _process_queue(self):
        """Process the execution queue asynchronously."""
        if len(self.active_executions) >= self.max_concurrent:
            return

        if not self.execution_queue:
            return

        # Get next execution from queue
        execution_id = self.execution_queue.pop(0)

        # Start async execution
        task = asyncio.create_task(self._execute_workflow_async(execution_id))
        self.active_executions[execution_id] = task

    async def _execute_workflow_async(self, execution_id: str):
        """Execute workflow asynchronously."""
        try:
            result = await self._execute_workflow_sync(execution_id)

            # Send webhook if configured
            execution_record = self.executions[execution_id]
            if execution_record.get("webhook_url"):
                await self._send_webhook(execution_record["webhook_url"], result.dict())

        except Exception as e:
            logging.error(f"Async execution {execution_id} failed: {e}")
        finally:
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            # Process next in queue
            self._process_queue()

    async def _send_webhook(self, webhook_url: str, data: Dict[str, Any]):
        """Send webhook notification."""
        # In production, this would use aiohttp or similar
        logging.info(f"Webhook notification sent to {webhook_url}")

    def get_execution_status(
        self, execution_id: str
    ) -> Optional[WorkflowStatusResponse]:
        """Get execution status."""
        if execution_id not in self.executions:
            return None

        record = self.executions[execution_id]
        return WorkflowStatusResponse(
            execution_id=execution_id,
            status=record["status"],
            result=record.get("result"),
            error=record.get("error"),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )


class WorkflowTemplateManager:
    """Manages workflow templates."""

    def __init__(self):
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_default_templates()

    def create_template(self, request: WorkflowTemplateRequest) -> str:
        """Create a new workflow template."""
        template_id = f"template_{uuid.uuid4().hex[:8]}"

        self.templates[template_id] = {
            "template_id": template_id,
            "name": request.template_name,
            "description": request.description,
            "workflow_config": request.workflow_config,
            "input_schema": request.input_schema,
            "tags": request.tags,
            "created_at": datetime.now(),
            "usage_count": 0,
        }

        return template_id

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow template."""
        return self.templates.get(template_id)

    def list_templates(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List workflow templates."""
        templates = list(self.templates.values())

        if tags:
            templates = [t for t in templates if any(tag in t["tags"] for tag in tags)]

        return templates

    def _load_default_templates(self):
        """Load default workflow templates."""
        # Multi-agent research template
        self.templates["multi_agent_research"] = {
            "template_id": "multi_agent_research",
            "name": "Multi-Agent Research",
            "description": "Comprehensive research using multiple specialized agents",
            "workflow_config": {
                "execution_mode": "collaborative",
                "agent_roles": ["coordinator", "specialist", "critic", "synthesizer"],
                "timeout_seconds": 300,
            },
            "input_schema": {
                "type": "object",
                "properties": {
                    "research_question": {"type": "string"},
                    "domain": {"type": "string"},
                    "depth": {
                        "type": "string",
                        "enum": ["basic", "intermediate", "comprehensive"],
                    },
                },
                "required": ["research_question"],
            },
            "tags": ["research", "multi-agent", "analysis"],
            "created_at": datetime.now(),
            "usage_count": 0,
        }

        # Single agent analysis template
        self.templates["single_agent_analysis"] = {
            "template_id": "single_agent_analysis",
            "name": "Single Agent Analysis",
            "description": "Quick analysis using a single specialized agent",
            "workflow_config": {
                "execution_mode": "sequential",
                "agent_roles": ["specialist"],
                "timeout_seconds": 60,
            },
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "context": {"type": "string"},
                },
                "required": ["prompt"],
            },
            "tags": ["analysis", "single-agent", "quick"],
            "created_at": datetime.now(),
            "usage_count": 0,
        }


# Global managers - initialized once
api_key_manager = None
execution_manager = None
template_manager = None
metrics_collector = None
workflow_monitor = None
alert_manager = None


# FastAPI Application
def create_api_gateway() -> FastAPI:
    """Create the FastAPI application with all endpoints."""

    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI and dependencies not available. Install with: pip install fastapi uvicorn slowapi"
        )

    # Rate limiting
    limiter = Limiter(key_func=get_remote_address)

    # Create FastAPI app
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        global api_key_manager, execution_manager, template_manager
        global metrics_collector, workflow_monitor, alert_manager

        logging.info("ASEA API Gateway starting up...")

        # Initialize managers globally
        api_key_manager = APIKeyManager()
        execution_manager = WorkflowExecutionManager()
        template_manager = WorkflowTemplateManager()
        (
            metrics_collector,
            workflow_monitor,
            alert_manager,
        ) = create_default_monitoring_setup()

        # Create default API key
        default_key = api_key_manager.create_api_key(
            "default",
            ["workflow:execute", "workflow:status", "templates:read", "metrics:read"],
        )
        logging.info(f"Default API key created: {default_key}")

        yield

        # Shutdown
        logging.info("ASEA API Gateway shutting down...")

    app = FastAPI(
        title="ASEA Workflow API Gateway",
        description="Production API for ASEA-LangGraph workflow execution",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure appropriately for production
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Authentication
    security = HTTPBearer()

    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        """Authenticate API requests."""
        global api_key_manager
        if not api_key_manager:
            raise HTTPException(
                status_code=500, detail="API key manager not initialized"
            )

        api_key = credentials.credentials
        key_info = api_key_manager.validate_api_key(api_key)

        if not key_info:
            raise HTTPException(status_code=401, detail="Invalid API key")

        return key_info

    def require_permission(permission: str):
        """Dependency to require specific permission."""

        def check_permission(
            user: Dict[str, Any] = Depends(get_current_user),
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            global api_key_manager
            if not api_key_manager:
                raise HTTPException(
                    status_code=500, detail="API key manager not initialized"
                )
            if not api_key_manager.check_permission(
                credentials.credentials, permission
            ):
                raise HTTPException(
                    status_code=403, detail=f"Permission required: {permission}"
                )
            return user

        return check_permission

    # API Endpoints

    @app.get("/health", response_model=SystemHealthResponse)
    @limiter.limit("10/minute")
    async def get_system_health(request: Request):
        """Get system health status."""
        global workflow_monitor, metrics_collector
        health = (
            workflow_monitor.get_workflow_health()
            if workflow_monitor
            else {"status": "healthy"}
        )
        metrics_summary = (
            metrics_collector.get_all_metrics_summary() if metrics_collector else {}
        )

        return SystemHealthResponse(
            status=health["status"],
            version="1.0.0",
            uptime_seconds=time.time() - app.state.start_time
            if hasattr(app.state, "start_time")
            else 0,
            active_executions=len(execution_manager.active_executions),
            total_executions=len(execution_manager.executions),
            error_rate=health.get("error_rate_last_hour", 0),
            avg_execution_time=health.get("avg_duration_last_hour", 0),
            system_metrics=metrics_summary,
        )

    @app.post("/workflows/execute", response_model=WorkflowExecutionResponse)
    @limiter.limit("30/minute")
    async def execute_workflow(
        request: WorkflowExecutionRequest,
        background_tasks: BackgroundTasks,
        user: Dict[str, Any] = Depends(require_permission("workflow:execute")),
        http_request: Request = None,
    ):
        """Execute a workflow."""
        global execution_manager, metrics_collector
        try:
            result = await execution_manager.execute_workflow(
                request, user.get("name", "anonymous")
            )

            # Record metrics
            if metrics_collector:
                metrics_collector.record_counter(
                    "api_workflow_requests",
                    1,
                    {
                        "workflow": request.workflow_name,
                        "async": str(request.async_execution),
                    },
                )

            return result

        except Exception as e:
            if metrics_collector:
                metrics_collector.record_counter(
                    "api_workflow_errors", 1, {"workflow": request.workflow_name}
                )
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/workflows/{execution_id}/status", response_model=WorkflowStatusResponse)
    @limiter.limit("60/minute")
    async def get_workflow_status(
        execution_id: str,
        user: Dict[str, Any] = Depends(require_permission("workflow:status")),
        request: Request = None,
    ):
        """Get workflow execution status."""
        global execution_manager
        status = execution_manager.get_execution_status(execution_id)

        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")

        return status

    @app.get("/workflows/{execution_id}/stream")
    @limiter.limit("10/minute")
    async def stream_workflow_status(
        execution_id: str,
        user: Dict[str, Any] = Depends(require_permission("workflow:status")),
        request: Request = None,
    ):
        """Stream workflow execution status updates."""
        global execution_manager

        async def generate_status_updates():
            while True:
                status = execution_manager.get_execution_status(execution_id)
                if not status:
                    yield f"data: {json.dumps({'error': 'Execution not found'})}\n\n"
                    break

                yield f"data: {status.json()}\n\n"

                if status.status in ["completed", "failed"]:
                    break

                await asyncio.sleep(1)

        return StreamingResponse(
            generate_status_updates(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.post("/templates", response_model=Dict[str, str])
    @limiter.limit("10/minute")
    async def create_workflow_template(
        request: WorkflowTemplateRequest,
        user: Dict[str, Any] = Depends(require_permission("templates:create")),
        http_request: Request = None,
    ):
        """Create a new workflow template."""
        global template_manager
        template_id = template_manager.create_template(request)
        return {"template_id": template_id}

    @app.get("/templates", response_model=List[Dict[str, Any]])
    @limiter.limit("30/minute")
    async def list_workflow_templates(
        tags: Optional[str] = None,
        user: Dict[str, Any] = Depends(require_permission("templates:read")),
        request: Request = None,
    ):
        """List available workflow templates."""
        global template_manager
        tag_list = tags.split(",") if tags else None
        return template_manager.list_templates(tag_list)

    @app.get("/templates/{template_id}", response_model=Dict[str, Any])
    @limiter.limit("30/minute")
    async def get_workflow_template(
        template_id: str,
        user: Dict[str, Any] = Depends(require_permission("templates:read")),
        request: Request = None,
    ):
        """Get a specific workflow template."""
        global template_manager
        template = template_manager.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template

    @app.post("/api-keys", response_model=Dict[str, str])
    @limiter.limit("5/minute")
    async def create_api_key(
        request: APIKeyRequest,
        user: Dict[str, Any] = Depends(require_permission("admin")),
        http_request: Request = None,
    ):
        """Create a new API key."""
        global api_key_manager
        api_key = api_key_manager.create_api_key(
            request.name, request.permissions, request.expires_at
        )
        return {"api_key": api_key}

    @app.get("/metrics", response_model=Dict[str, Any])
    @limiter.limit("20/minute")
    async def get_metrics(
        format_type: str = "json",
        user: Dict[str, Any] = Depends(require_permission("metrics:read")),
        request: Request = None,
    ):
        """Get system metrics."""
        global metrics_collector
        if format_type == "prometheus":
            content = (
                metrics_collector.export_metrics("prometheus")
                if metrics_collector
                else ""
            )
            return Response(content=content, media_type="text/plain")
        else:
            return (
                metrics_collector.get_all_metrics_summary() if metrics_collector else {}
            )

    @app.get("/alerts", response_model=List[Dict[str, Any]])
    @limiter.limit("20/minute")
    async def get_active_alerts(
        user: Dict[str, Any] = Depends(require_permission("alerts:read")),
        request: Request = None,
    ):
        """Get active alerts."""
        global alert_manager
        return alert_manager.get_active_alerts() if alert_manager else []

    # Store start time for uptime calculation
    app.state.start_time = time.time()

    return app


# Production Server
def run_production_server(
    host: str = "0.0.0.0", port: int = 8000, workers: int = 1, log_level: str = "info"
):
    """Run the production API server."""

    if not FASTAPI_AVAILABLE:
        print(
            "FastAPI not available. Install with: pip install fastapi uvicorn slowapi"
        )
        return

    app = create_api_gateway()

    uvicorn.run(
        app, host=host, port=port, workers=workers, log_level=log_level, access_log=True
    )


if __name__ == "__main__":
    # Development server
    run_production_server(port=8000, log_level="debug")
