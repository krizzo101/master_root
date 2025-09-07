#!/usr/bin/env python3
"""
Standalone Async Web Server Implementation
A simple, self-contained async web server based on the architecture design
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from aiohttp import web
from aiohttp.web import Request, Response, json_response

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class WebRequest:
    """Web request representation"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    method: str = "GET"
    path: str = "/"
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict] = None
    context: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class WebResponse:
    """Web response structure"""

    request_id: str
    status_code: int = 200
    data: Optional[Dict] = None
    error: Optional[str] = None
    duration_ms: float = 0


class ConnectionPool:
    """
    Connection pool management based on TokenPool pattern
    Manages resources with round-robin allocation
    """

    def __init__(self, size: int = 10):
        self.connections = [f"conn_{i}" for i in range(size)]
        self.current_index = 0
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Get next available connection"""
        async with self.lock:
            conn = self.connections[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.connections)
            return conn

    async def release(self, conn):
        """Release connection back to pool"""
        # In a real implementation, this might reset the connection state
        pass


class RequestQualityGate:
    """Quality gate for request validation"""

    async def validate(self, request: WebRequest) -> Dict[str, Any]:
        """Run all validations"""
        results = await asyncio.gather(
            self.validate_rate_limit(request),
            self.validate_auth(request),
            self.validate_input(request),
            return_exceptions=True,
        )

        all_passed = True
        all_issues = []

        for result in results:
            if isinstance(result, Exception):
                all_passed = False
                all_issues.append(str(result))
            elif not result.get("passed", True):
                all_passed = False
                all_issues.extend(result.get("issues", []))

        return {"passed": all_passed, "issues": all_issues}

    async def validate_rate_limit(self, request: WebRequest) -> Dict[str, Any]:
        """Rate limiting validation"""
        # Simple implementation - always pass
        return {"passed": True, "issues": []}

    async def validate_auth(self, request: WebRequest) -> Dict[str, Any]:
        """Authentication validation"""
        # Skip auth for public endpoints
        if request.path in ["/", "/health", "/metrics"]:
            return {"passed": True, "issues": []}

        # Check for API key
        if "X-API-Key" not in request.headers:
            return {"passed": False, "issues": ["Missing API key"]}

        return {"passed": True, "issues": []}

    async def validate_input(self, request: WebRequest) -> Dict[str, Any]:
        """Input validation"""
        if request.body:
            # Check payload size
            body_str = json.dumps(request.body)
            if len(body_str) > 100000:  # 100KB limit
                return {"passed": False, "issues": ["Payload too large"]}

        return {"passed": True, "issues": []}


class RequestOrchestrator:
    """Orchestrates request execution with parallel processing"""

    def __init__(self, max_parallel: int = 50):
        self.max_parallel = max_parallel
        self.semaphore = asyncio.Semaphore(max_parallel)
        self.connection_pool = ConnectionPool(size=10)

    async def execute(self, request: WebRequest, handler: Callable) -> WebResponse:
        """Execute request with orchestration"""
        request.start_time = time.time()

        try:
            async with self.semaphore:
                # Get connection from pool
                conn = await self.connection_pool.acquire()

                try:
                    # Execute business logic
                    result = await handler(request, conn)

                    request.end_time = time.time()
                    duration_ms = (request.end_time - request.start_time) * 1000

                    return WebResponse(
                        request_id=request.request_id,
                        status_code=200,
                        data=result,
                        duration_ms=duration_ms,
                    )

                finally:
                    await self.connection_pool.release(conn)

        except Exception as e:
            request.end_time = time.time()
            duration_ms = (request.end_time - request.start_time) * 1000

            logger.error(f"Request failed: {e}")
            return WebResponse(
                request_id=request.request_id,
                status_code=500,
                error=str(e),
                duration_ms=duration_ms,
            )


class MetricsCollector:
    """Collects and tracks server metrics"""

    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_active": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "response_times": [],
            "server_start_time": time.time(),
        }
        self.lock = asyncio.Lock()

    async def record_request_start(self):
        """Record request start"""
        async with self.lock:
            self.metrics["requests_total"] += 1
            self.metrics["requests_active"] += 1

    async def record_request_end(self, success: bool, duration_ms: float):
        """Record request completion"""
        async with self.lock:
            self.metrics["requests_active"] -= 1

            if success:
                self.metrics["requests_success"] += 1
            else:
                self.metrics["requests_failed"] += 1

            self.metrics["response_times"].append(duration_ms)

            # Keep only last 1000 response times
            if len(self.metrics["response_times"]) > 1000:
                self.metrics["response_times"] = self.metrics["response_times"][-1000:]

    async def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        async with self.lock:
            response_times = self.metrics["response_times"]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            return {
                **self.metrics,
                "avg_response_time_ms": avg_response_time,
                "success_rate": (
                    self.metrics["requests_success"]
                    / max(self.metrics["requests_total"], 1)
                )
                * 100,
                "uptime_seconds": time.time() - self.metrics["server_start_time"],
            }


class AsyncWebServer:
    """Main async web server"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = web.Application()

        # Components
        self.orchestrator = RequestOrchestrator(max_parallel=50)
        self.quality_gate = RequestQualityGate()
        self.metrics = MetricsCollector()

        # Data storage for demo
        self.data_store = {"items": {}, "users": {}}

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes"""
        # Core endpoints
        self.app.router.add_get("/", self._welcome_handler)
        self.app.router.add_get("/health", self._health_handler)
        self.app.router.add_get("/metrics", self._metrics_handler)

        # Demo API endpoints
        self.app.router.add_get("/api/items", self._list_items)
        self.app.router.add_post("/api/items", self._create_item)
        self.app.router.add_get("/api/items/{item_id}", self._get_item)

        # Async demo endpoint
        self.app.router.add_get("/api/async-demo", self._async_demo)
        self.app.router.add_post("/api/echo", self._echo_handler)

    async def start(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Server started at http://{self.host}:{self.port}")

    def _create_web_request(self, request: Request) -> WebRequest:
        """Convert aiohttp request to WebRequest"""
        return WebRequest(
            method=request.method,
            path=str(request.url.path),
            headers=dict(request.headers),
            query_params=dict(request.query),
            context={
                "remote_addr": request.remote,
                "user_agent": request.headers.get("User-Agent", ""),
            },
        )

    async def _process_request(self, request: Request, handler: Callable) -> Response:
        """Process request through quality gates and orchestrator"""
        web_request = self._create_web_request(request)

        # Parse body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                web_request.body = await request.json()
            except:
                web_request.body = None

        # Record metrics
        await self.metrics.record_request_start()

        # Quality gate validation
        validation = await self.quality_gate.validate(web_request)
        if not validation["passed"]:
            await self.metrics.record_request_end(False, 0)
            return json_response(
                {"error": "Validation failed", "issues": validation["issues"]},
                status=400,
            )

        # Execute request
        response = await self.orchestrator.execute(web_request, handler)

        # Record metrics
        await self.metrics.record_request_end(
            response.status_code < 400, response.duration_ms
        )

        # Return response
        if response.error:
            return json_response({"error": response.error}, status=response.status_code)
        else:
            return json_response(
                response.data or {"success": True}, status=response.status_code
            )

    # Route handlers

    async def _welcome_handler(self, request: Request) -> Response:
        """Welcome page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Async Web Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { font-weight: bold; color: #007bff; }
                code { background: #e9ecef; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>🚀 Async Web Server</h1>
            <p>A simple async web server implementation based on the Agent Orchestrator architecture.</p>

            <h2>Available Endpoints:</h2>

            <div class="endpoint">
                <span class="method">GET</span> <code>/health</code> - Health check
            </div>

            <div class="endpoint">
                <span class="method">GET</span> <code>/metrics</code> - Server metrics
            </div>

            <div class="endpoint">
                <span class="method">GET</span> <code>/api/async-demo</code> - Async processing demo
            </div>

            <div class="endpoint">
                <span class="method">POST</span> <code>/api/echo</code> - Echo request
            </div>

            <div class="endpoint">
                <span class="method">GET</span> <code>/api/items</code> - List items (requires X-API-Key header)
            </div>

            <div class="endpoint">
                <span class="method">POST</span> <code>/api/items</code> - Create item (requires X-API-Key header)
            </div>

            <h2>Test with curl:</h2>
            <pre>
# Health check
curl http://localhost:8000/health

# Async demo
curl http://localhost:8000/api/async-demo

# Echo test
curl -X POST http://localhost:8000/api/echo \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello!"}'

# Create item (with API key)
curl -X POST http://localhost:8000/api/items \\
  -H "X-API-Key: test-key" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Test Item", "value": 42}'
            </pre>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    async def _health_handler(self, request: Request) -> Response:
        """Health check"""
        return json_response(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "server": "AsyncWebServer",
            }
        )

    async def _metrics_handler(self, request: Request) -> Response:
        """Metrics endpoint"""
        summary = await self.metrics.get_summary()
        return json_response(summary)

    async def _async_demo(self, request: Request) -> Response:
        """Demonstrate async processing"""

        async def handler(req: WebRequest, conn: str) -> Dict:
            # Simulate parallel async operations
            async def task(name: str, delay: float) -> Dict:
                await asyncio.sleep(delay)
                return {"task": name, "delay": delay, "connection": conn}

            results = await asyncio.gather(
                task("database_query", 0.3),
                task("cache_lookup", 0.1),
                task("api_call", 0.5),
                task("calculation", 0.2),
            )

            return {
                "message": "Parallel async operations completed",
                "results": results,
                "explanation": "All 4 tasks ran in parallel using the same connection from pool",
            }

        return await self._process_request(request, handler)

    async def _echo_handler(self, request: Request) -> Response:
        """Echo request"""

        async def handler(req: WebRequest, conn: str) -> Dict:
            return {
                "echo": {
                    "method": req.method,
                    "path": req.path,
                    "headers_count": len(req.headers),
                    "query_params": req.query_params,
                    "body": req.body,
                    "connection_used": conn,
                }
            }

        return await self._process_request(request, handler)

    async def _list_items(self, request: Request) -> Response:
        """List items"""

        async def handler(req: WebRequest, conn: str) -> Dict:
            return {
                "items": list(self.data_store["items"].values()),
                "count": len(self.data_store["items"]),
            }

        return await self._process_request(request, handler)

    async def _create_item(self, request: Request) -> Response:
        """Create item"""

        async def handler(req: WebRequest, conn: str) -> Dict:
            if not req.body:
                raise ValueError("Item data required")

            item_id = f"item_{len(self.data_store['items']) + 1}"
            item = {"id": item_id, "created_at": datetime.now().isoformat(), **req.body}

            self.data_store["items"][item_id] = item
            return {"created": item}

        return await self._process_request(request, handler)

    async def _get_item(self, request: Request) -> Response:
        """Get item by ID"""
        item_id = request.match_info.get("item_id")

        async def handler(req: WebRequest, conn: str) -> Dict:
            if item_id not in self.data_store["items"]:
                raise ValueError(f"Item {item_id} not found")

            return {"item": self.data_store["items"][item_id]}

        return await self._process_request(request, handler)


async def main():
    """Main entry point"""
    import sys

    # Get port from command line
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            print(f"Invalid port: {sys.argv[1]}, using default 8000")

    print("=" * 60)
    print("🚀 STANDALONE ASYNC WEB SERVER")
    print("=" * 60)

    # Create and start server
    server = AsyncWebServer(host="0.0.0.0", port=port)
    await server.start()

    print(f"\n✅ Server running at http://localhost:{port}")
    print(f"📚 Visit http://localhost:{port}/ for documentation")
    print(f"\n🔍 Quick tests:")
    print(f"   curl http://localhost:{port}/health")
    print(f"   curl http://localhost:{port}/metrics")
    print(f"   curl http://localhost:{port}/api/async-demo")
    print(f"\n⚡ Press Ctrl+C to stop\n")

    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
            metrics = await server.metrics.get_summary()
            if metrics["requests_total"] > 0:
                print(
                    f"📊 Metrics: {metrics['requests_total']} requests, "
                    f"{metrics['success_rate']:.1f}% success, "
                    f"{metrics['avg_response_time_ms']:.2f}ms avg"
                )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
