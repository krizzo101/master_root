"""
Base API framework for OPSVI Core.

Provides FastAPI-based REST API framework with authentication, rate limiting, and documentation.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

logger = get_logger(__name__)


class APIError(ComponentError):
    """Raised when API operations fail."""

    pass


class RateLimitExceeded(APIError):
    """Raised when rate limit is exceeded."""

    pass


class APIConfig(BaseModel):
    """Configuration for API server."""

    title: str = Field(default="OPSVI Core API", description="API title")
    version: str = Field(default="1.0.0", description="API version")
    description: str = Field(default="OPSVI Core REST API", description="API description")
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: List[str] = Field(default=["*"], description="CORS origins")
    rate_limit_rpm: int = Field(default=100, description="Rate limit requests per minute")
    enable_docs: bool = Field(default=True, description="Enable API documentation")


class RateLimiter(BaseComponent):
    """Rate limiting implementation."""

    def __init__(self, requests_per_minute: int = 100):
        super().__init__()
        self.requests_per_minute = requests_per_minute
        self._requests: Dict[str, List[datetime]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed based on rate limit."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)

        # Get client requests
        client_requests = self._requests.get(client_id, [])
        
        # Remove old requests outside the window
        client_requests = [req for req in client_requests if req > window_start]
        
        # Check if under limit
        if len(client_requests) >= self.requests_per_minute:
            return False
        
        # Add current request
        client_requests.append(now)
        self._requests[client_id] = client_requests
        
        return True

    def get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Use IP address as client ID (can be enhanced with API keys)
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        client_id = self.rate_limiter.get_client_id(request)
        
        if not self.rate_limiter.is_allowed(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        
        response = await call_next(request)
        return response


class APIAuthenticator(BaseComponent, ABC):
    """Abstract API authentication interface."""

    @abstractmethod
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate the request and return user info."""
        pass

    @abstractmethod
    async def authorize(self, user_info: Dict[str, Any], resource: str, action: str) -> bool:
        """Authorize user access to resource."""
        pass


class JWTAuthenticator(APIAuthenticator):
    """JWT-based authentication."""

    def __init__(self, secret_key: str):
        super().__init__()
        self.secret_key = secret_key
        self.security = HTTPBearer()

    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate using JWT token."""
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            # TODO: Implement JWT validation
            # For now, return a mock user
            return {"user_id": "test_user", "roles": ["user"]}
        except Exception as e:
            logger.error("Authentication failed: %s", str(e))
            return None

    async def authorize(self, user_info: Dict[str, Any], resource: str, action: str) -> bool:
        """Authorize user access."""
        # TODO: Implement proper authorization logic
        return True


class APIEndpoint(BaseComponent):
    """Base class for API endpoints."""

    def __init__(self, path: str, methods: List[str]):
        super().__init__()
        self.path = path
        self.methods = methods
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, method: str, handler: Callable) -> None:
        """Register a handler for a specific HTTP method."""
        self.handlers[method.upper()] = handler

    async def handle_request(self, request: Request) -> Any:
        """Handle incoming request."""
        method = request.method.upper()
        handler = self.handlers.get(method)
        
        if not handler:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=f"Method {method} not allowed",
            )
        
        return await handler(request)


class APIServer(BaseComponent):
    """Main API server implementation."""

    def __init__(self, config: APIConfig):
        super().__init__()
        self.config = config
        self.app = FastAPI(
            title=config.title,
            version=config.version,
            description=config.description,
            docs_url="/docs" if config.enable_docs else None,
            redoc_url="/redoc" if config.enable_docs else None,
        )
        self.rate_limiter = RateLimiter(config.rate_limit_rpm)
        self.authenticator = JWTAuthenticator("secret_key")  # TODO: Use proper secret
        self.endpoints: Dict[str, APIEndpoint] = {}

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup middleware."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Rate limiting middleware
        self.app.add_middleware(RateLimitMiddleware, rate_limiter=self.rate_limiter)

    def _setup_routes(self) -> None:
        """Setup default routes."""
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.utcnow()}

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "OPSVI Core API", "version": self.config.version}

    def add_endpoint(self, endpoint: APIEndpoint) -> None:
        """Add an endpoint to the API."""
        self.endpoints[endpoint.path] = endpoint
        
        # Register with FastAPI
        for method in endpoint.methods:
            if method.upper() == "GET":
                self.app.get(endpoint.path)(endpoint.handle_request)
            elif method.upper() == "POST":
                self.app.post(endpoint.path)(endpoint.handle_request)
            elif method.upper() == "PUT":
                self.app.put(endpoint.path)(endpoint.handle_request)
            elif method.upper() == "DELETE":
                self.app.delete(endpoint.path)(endpoint.handle_request)

    async def start(self) -> None:
        """Start the API server."""
        import uvicorn
        
        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="debug" if self.config.debug else "info",
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def _start(self) -> None:
        """Start the API server."""
        logger.info("Starting API server on %s:%d", self.config.host, self.config.port)
        await self.start()

    async def _stop(self) -> None:
        """Stop the API server."""
        logger.info("Stopping API server")
