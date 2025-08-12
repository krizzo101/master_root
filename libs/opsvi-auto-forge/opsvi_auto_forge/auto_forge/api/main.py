"""Main FastAPI application for the autonomous software factory."""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from opsvi_auto_forge.config.settings import settings
from .routes import health, runs, tasks, projects, websockets, debug, decisions
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.application.orchestrator.registry import TaskRegistryManager
from opsvi_auto_forge.infrastructure.monitoring.logging_config import (
    configure_logging,
    get_logger,
    log_request_start,
    log_request_end,
    log_error,
    generate_correlation_id,
    set_correlation_id,
    get_correlation_id,
)

# Configure structured logging
configure_logging(
    log_level=settings.log_level,
    log_format="json",
    enable_console=True,
    enable_file=True,
    enable_debug_log=True,
)

logger = get_logger("api.main")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of currently active HTTP requests",
    ["method", "endpoint"],
)


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Auto Forge API server")

    # Initialize Neo4j client
    try:
        neo4j_client = Neo4jClient()
        await neo4j_client.connect()
        logger.info("✅ Neo4j client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Neo4j client: {e}")
        raise

    # Initialize task registry
    try:
        task_registry = TaskRegistryManager(neo4j_client=neo4j_client)
        await task_registry.initialize()
        logger.info("✅ Task registry initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize task registry: {e}")
        raise

    # Initialize Neo4j schema
    try:
        schema_initialized = await neo4j_client.initialize_schema()
        if schema_initialized:
            logger.info("✅ Neo4j schema initialized successfully")
        else:
            logger.warning("⚠️ Neo4j schema initialization failed, but continuing")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Neo4j schema: {e}, but continuing")

    logger.info("✅ Auto Forge API server started successfully")

    yield

    logger.info("🛑 Shutting down Auto Forge API server")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Autonomous Software Factory API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Enhanced logging middleware
@app.middleware("http")
async def enhanced_logging_middleware(request: Request, call_next):
    """Enhanced middleware for comprehensive request/response logging."""
    start_time = time.time()

    # Generate correlation ID for this request
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)

    # Extract request details
    method = request.method
    url = str(request.url)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Log request start
    log_request_start(
        request_id=correlation_id,
        method=method,
        url=url,
        client_ip=client_ip,
        user_agent=user_agent,
        headers=dict(request.headers),
        query_params=dict(request.query_params),
    )

    logger.debug(
        "HTTP request details",
        correlation_id=correlation_id,
        method=method,
        url=url,
        client_ip=client_ip,
        user_agent=user_agent,
        content_length=request.headers.get("content-length"),
        content_type=request.headers.get("content-type"),
    )

    # Track active requests
    ACTIVE_REQUESTS.labels(method=method, endpoint=request.url.path).inc()

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time
        duration_ms = duration * 1000

        # Log response
        log_request_end(
            request_id=correlation_id,
            method=method,
            url=url,
            status_code=response.status_code,
            duration_ms=duration_ms,
            response_size=len(response.body) if hasattr(response, "body") else 0,
        )

        logger.debug(
            "HTTP response details",
            correlation_id=correlation_id,
            status_code=response.status_code,
            duration_ms=duration_ms,
            response_headers=dict(response.headers),
        )

        # Update metrics
        REQUEST_COUNT.labels(
            method=method, endpoint=request.url.path, status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(method=method, endpoint=request.url.path).observe(
            duration
        )

        return response

    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = duration * 1000

        # Log error
        log_error(
            f"HTTP request failed: {e}",
            error=e,
            correlation_id=correlation_id,
            method=method,
            url=url,
            duration_ms=duration_ms,
        )

        logger.error(
            "HTTP request exception",
            correlation_id=correlation_id,
            method=method,
            url=url,
            exception=str(e),
            exception_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )

        # Update metrics
        REQUEST_COUNT.labels(method=method, endpoint=request.url.path, status=500).inc()

        REQUEST_LATENCY.labels(method=method, endpoint=request.url.path).observe(
            duration
        )

        raise
    finally:
        # Decrease active requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=request.url.path).dec()


# Enhanced request body logging middleware
class LogRequestBodyMiddleware(BaseHTTPMiddleware):
    """Middleware to log request body for debugging."""

    async def dispatch(self, request: Request, call_next):
        # Log request body for debugging (only for specific endpoints)
        debug_endpoints = ["/runs/start", "/projects/", "/tasks/"]

        if any(endpoint in request.url.path for endpoint in debug_endpoints):
            try:
                body = await request.body()
                if body:
                    logger.debug(
                        "Request body",
                        correlation_id=get_correlation_id(),
                        endpoint=request.url.path,
                        body_size=len(body),
                        body_preview=(
                            body[:500].decode("utf-8", errors="ignore") + "..."
                            if len(body) > 500
                            else body.decode("utf-8", errors="ignore")
                        ),
                    )
            except Exception as e:
                logger.warning(
                    "Failed to log request body",
                    correlation_id=get_correlation_id(),
                    endpoint=request.url.path,
                    error=str(e),
                )

        response = await call_next(request)
        return response


app.add_middleware(LogRequestBodyMiddleware)


# Exception handlers with enhanced logging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with enhanced logging."""
    correlation_id = get_correlation_id()

    logger.error(
        "Request validation error",
        correlation_id=correlation_id,
        method=request.method,
        url=str(request.url),
        validation_errors=exc.errors(),
        exc_info=True,
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "correlation_id": correlation_id,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with enhanced logging."""
    correlation_id = get_correlation_id()

    logger.error(
        "Unhandled exception",
        correlation_id=correlation_id,
        method=request.method,
        url=str(request.url),
        exception=str(exc),
        exception_type=type(exc).__name__,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "correlation_id": correlation_id},
    )


# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(websockets.router, prefix="/ws", tags=["websockets"])
app.include_router(debug.router, prefix="/debug", tags=["debug"])
app.include_router(decisions.router, prefix="/decisions", tags=["decisions"])

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with enhanced logging."""
    correlation_id = get_correlation_id()

    logger.info("Root endpoint accessed", correlation_id=correlation_id)

    return {
        "message": "Auto Forge API",
        "version": settings.app_version,
        "status": "running",
        "correlation_id": correlation_id,
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with enhanced logging."""
    correlation_id = get_correlation_id()

    logger.debug("Health check requested", correlation_id=correlation_id)

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
    }
