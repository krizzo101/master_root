#!/usr/bin/env python3
"""
Simple Async Web Server Demo
Demonstrates the async web server with various endpoints and request handling
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.async_web_server import APIRequest, AsyncWebServer, RequestQualityGate

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class DemoQualityGate(RequestQualityGate):
    """Demo quality gate with custom validation rules"""

    def __init__(self):
        self.request_counts = {}
        self.blocked_ips = set()

    async def validate_rate_limit(self, request: APIRequest) -> Dict[str, Any]:
        """Simple rate limiting - max 10 requests per minute per IP"""
        remote_addr = request.context.get("remote_addr", "unknown")

        # Clean up old entries (simple time window)
        current_minute = datetime.now().strftime("%Y-%m-%d %H:%M")
        key = f"{remote_addr}:{current_minute}"

        # Count requests
        self.request_counts[key] = self.request_counts.get(key, 0) + 1

        if self.request_counts[key] > 100:  # 100 requests per minute limit
            return {
                "passed": False,
                "issues": [f"Rate limit exceeded for {remote_addr}"],
            }

        return {"passed": True, "issues": []}

    async def validate_authentication(self, request: APIRequest) -> Dict[str, Any]:
        """Demo authentication check"""
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")

        # Skip auth for health and metrics endpoints
        if request.endpoint in ["/health", "/metrics", "/"]:
            return {"passed": True, "issues": []}

        # Demo: Accept any non-empty API key
        if not api_key:
            return {
                "passed": False,
                "issues": ["Missing API key. Include X-API-Key header"],
            }

        return {"passed": True, "issues": []}

    async def validate_input(self, request: APIRequest) -> Dict[str, Any]:
        """Validate input data"""
        if request.payload:
            # Check for SQL injection patterns (very basic)
            payload_str = json.dumps(request.payload).lower()
            dangerous_patterns = ["drop table", "delete from", "; --", "' or '"]

            for pattern in dangerous_patterns:
                if pattern in payload_str:
                    return {
                        "passed": False,
                        "issues": [f"Potentially dangerous input detected: {pattern}"],
                    }

            # Check payload size
            if len(payload_str) > 50000:  # 50KB limit
                return {"passed": False, "issues": ["Payload too large (max 50KB)"]}

        return {"passed": True, "issues": []}


class DemoWebServer(AsyncWebServer):
    """Extended web server with demo endpoints"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        super().__init__(host, port, max_parallel=50)

        # Demo data storage
        self.demo_database = {"users": {}, "tasks": {}, "messages": []}

        # Add more routes
        self._setup_demo_routes()

    def _setup_demo_routes(self):
        """Setup additional demo routes"""
        # User endpoints
        self.app.router.add_post("/api/users", self._create_user)
        self.app.router.add_get("/api/users/{user_id}", self._get_user)
        self.app.router.add_get("/api/users", self._list_users)

        # Task endpoints
        self.app.router.add_post("/api/tasks", self._create_task)
        self.app.router.add_get("/api/tasks", self._list_tasks)
        self.app.router.add_put("/api/tasks/{task_id}/complete", self._complete_task)

        # Echo endpoint for testing
        self.app.router.add_post("/api/echo", self._echo_handler)

        # Async simulation endpoint
        self.app.router.add_get("/api/async-demo", self._async_demo)

        # Welcome page
        self.app.router.add_get("/", self._welcome_handler)

    async def _welcome_handler(self, request):
        """Welcome page with API documentation"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Async Web Server Demo</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { font-weight: bold; color: #007bff; }
                code { background: #e9ecef; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>🚀 Async Web Server Demo</h1>
            <p>Welcome to the async web server demo based on the Agent Orchestrator architecture!</p>

            <h2>Available Endpoints:</h2>

            <div class="endpoint">
                <span class="method">GET</span> <code>/health</code> - Health check
            </div>

            <div class="endpoint">
                <span class="method">GET</span> <code>/metrics</code> - Server metrics
            </div>

            <div class="endpoint">
                <span class="method">POST</span> <code>/api/echo</code> - Echo your request
            </div>

            <div class="endpoint">
                <span class="method">GET</span> <code>/api/async-demo</code> - Async processing demo
            </div>

            <div class="endpoint">
                <span class="method">POST</span> <code>/api/users</code> - Create user (requires X-API-Key header)
            </div>

            <div class="endpoint">
                <span class="method">GET</span> <code>/api/users</code> - List users (requires X-API-Key header)
            </div>

            <div class="endpoint">
                <span class="method">POST</span> <code>/api/tasks</code> - Create task (requires X-API-Key header)
            </div>

            <div class="endpoint">
                <span class="method">GET</span> <code>/api/tasks</code> - List tasks (requires X-API-Key header)
            </div>

            <h2>Testing with curl:</h2>
            <pre>
# Health check
curl http://localhost:8000/health

# Echo test
curl -X POST http://localhost:8000/api/echo \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello, async world!"}'

# Create user (with API key)
curl -X POST http://localhost:8000/api/users \\
  -H "X-API-Key: demo-key-123" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "John Doe", "email": "john@example.com"}'
            </pre>
        </body>
        </html>
        """
        return self.app.response_class(text=html_content, content_type="text/html")

    async def _echo_handler(self, request):
        """Echo request back"""
        api_request = await self._create_api_request(request, "echo")

        response_data = {
            "echo": {
                "method": api_request.request_type,
                "endpoint": api_request.endpoint,
                "headers_count": len(api_request.headers),
                "payload": api_request.payload,
                "query_params": api_request.query_params,
                "timestamp": datetime.now().isoformat(),
            }
        }

        return self.app.json_response(response_data)

    async def _async_demo(self, request):
        """Demonstrate async processing with parallel tasks"""
        start_time = asyncio.get_event_loop().time()

        # Simulate parallel async operations
        async def fake_db_query(name: str, delay: float) -> Dict:
            await asyncio.sleep(delay)
            return {"operation": name, "duration": delay, "status": "completed"}

        # Run multiple operations in parallel
        results = await asyncio.gather(
            fake_db_query("user_lookup", 0.5),
            fake_db_query("permission_check", 0.3),
            fake_db_query("data_fetch", 0.7),
            fake_db_query("cache_warm", 0.2),
        )

        total_time = asyncio.get_event_loop().time() - start_time

        return self.app.json_response(
            {
                "message": "Async operations completed",
                "parallel_operations": results,
                "total_time_seconds": round(total_time, 3),
                "explanation": "All 4 operations ran in parallel, taking only as long as the slowest one (0.7s)",
            }
        )

    async def _create_user(self, request):
        """Create a new user"""
        api_request = await self._create_api_request(request, "create_user")

        if not api_request.payload:
            return self.app.json_response({"error": "User data required"}, status=400)

        user_id = f"user_{len(self.demo_database['users']) + 1}"
        user_data = {
            "id": user_id,
            "created_at": datetime.now().isoformat(),
            **api_request.payload,
        }

        self.demo_database["users"][user_id] = user_data

        return self.app.json_response({"success": True, "user": user_data})

    async def _get_user(self, request):
        """Get user by ID"""
        user_id = request.match_info.get("user_id")

        if user_id not in self.demo_database["users"]:
            return self.app.json_response({"error": "User not found"}, status=404)

        return self.app.json_response({"user": self.demo_database["users"][user_id]})

    async def _list_users(self, request):
        """List all users"""
        return self.app.json_response(
            {
                "users": list(self.demo_database["users"].values()),
                "count": len(self.demo_database["users"]),
            }
        )

    async def _create_task(self, request):
        """Create a new task"""
        api_request = await self._create_api_request(request, "create_task")

        if not api_request.payload:
            return self.app.json_response({"error": "Task data required"}, status=400)

        task_id = f"task_{len(self.demo_database['tasks']) + 1}"
        task_data = {
            "id": task_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            **api_request.payload,
        }

        self.demo_database["tasks"][task_id] = task_data

        return self.app.json_response({"success": True, "task": task_data})

    async def _list_tasks(self, request):
        """List all tasks"""
        status_filter = request.query.get("status")

        tasks = list(self.demo_database["tasks"].values())

        if status_filter:
            tasks = [t for t in tasks if t.get("status") == status_filter]

        return self.app.json_response(
            {"tasks": tasks, "count": len(tasks), "filter": status_filter}
        )

    async def _complete_task(self, request):
        """Mark task as completed"""
        task_id = request.match_info.get("task_id")

        if task_id not in self.demo_database["tasks"]:
            return self.app.json_response({"error": "Task not found"}, status=404)

        self.demo_database["tasks"][task_id]["status"] = "completed"
        self.demo_database["tasks"][task_id][
            "completed_at"
        ] = datetime.now().isoformat()

        return self.app.json_response(
            {"success": True, "task": self.demo_database["tasks"][task_id]}
        )


async def main():
    """Main demo runner"""

    print("=" * 60)
    print("🚀 ASYNC WEB SERVER DEMO")
    print("=" * 60)

    # Get port from command line or use default
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default 8000")

    # Create and configure server
    server = DemoWebServer(host="0.0.0.0", port=port)

    # Add demo quality gate
    demo_gate = DemoQualityGate()
    server.add_quality_gate(demo_gate)

    # Start server
    await server.start()

    print(f"\n✅ Server is running at http://localhost:{port}")
    print(f"\n📚 Visit http://localhost:{port}/ for API documentation")
    print(f"\n🔍 Quick test commands:")
    print(f"   curl http://localhost:{port}/health")
    print(f"   curl http://localhost:{port}/metrics")
    print(f"   curl http://localhost:{port}/api/async-demo")
    print(f"\n⚡ Press Ctrl+C to stop the server\n")

    try:
        # Keep server running
        while True:
            await asyncio.sleep(60)

            # Print metrics every minute
            metrics = await server.monitor.get_metrics_summary()
            if metrics["requests_total"] > 0:
                print(f"\n📊 Metrics Update:")
                print(f"   Total requests: {metrics['requests_total']}")
                print(f"   Active requests: {metrics['requests_active']}")
                print(f"   Success rate: {metrics['success_rate']:.1f}%")
                print(f"   Avg response time: {metrics['avg_response_time']:.2f}ms")

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        await server.shutdown()
        print("✅ Server stopped successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
