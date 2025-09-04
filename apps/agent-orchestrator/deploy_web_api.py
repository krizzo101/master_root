#!/usr/bin/env python3
"""
Web API Deployment Script

Simple deployment script for the Web API system.
Handles server startup with production-ready configuration.
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from async_web_server import AsyncWebServer, RequestQualityGate


class ProductionQualityGate(RequestQualityGate):
    """Production-ready quality gate with enhanced validation"""

    def __init__(self):
        self.request_counts = {}  # Simple in-memory rate limiting
        self.max_requests_per_minute = 1000

    async def validate_rate_limit(self, request):
        """Production rate limiting"""
        client_ip = request.context.get("remote_addr", "unknown")
        current_time = asyncio.get_event_loop().time()

        # Simple sliding window rate limiting
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        # Clean old requests (older than 60 seconds)
        self.request_counts[client_ip] = [
            req_time
            for req_time in self.request_counts[client_ip]
            if current_time - req_time < 60
        ]

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.max_requests_per_minute:
            return {"passed": False, "issues": ["Rate limit exceeded"]}

        # Record this request
        self.request_counts[client_ip].append(current_time)
        return {"passed": True, "issues": []}

    async def validate_input(self, request):
        """Enhanced input validation for production"""
        if request.payload:
            # Check payload size
            payload_str = str(request.payload)
            if len(payload_str) > 1024 * 1024:  # 1MB limit
                return {"passed": False, "issues": ["Payload too large (>1MB)"]}

            # Check for ExecutionPlan structure
            if (
                request.endpoint == "/api/v1/execution-plans"
                and request.request_type == "POST"
            ):
                if not isinstance(request.payload, dict):
                    return {"passed": False, "issues": ["Invalid payload format"]}

                required_fields = ["plan_id", "name", "tasks"]
                for field in required_fields:
                    if field not in request.payload:
                        return {
                            "passed": False,
                            "issues": [f"Missing required field: {field}"],
                        }

                # Validate tasks structure
                tasks = request.payload.get("tasks", [])
                if not isinstance(tasks, list) or len(tasks) == 0:
                    return {"passed": False, "issues": ["At least one task required"]}

                for i, task in enumerate(tasks):
                    if not isinstance(task, dict):
                        return {
                            "passed": False,
                            "issues": [f"Task {i} must be an object"],
                        }

                    task_required = ["task_id", "task_type", "prompt"]
                    for field in task_required:
                        if field not in task:
                            return {
                                "passed": False,
                                "issues": [f"Task {i} missing required field: {field}"],
                            }

        return {"passed": True, "issues": []}


class WebAPIDeployment:
    """Web API deployment manager"""

    def __init__(
        self, host: str, port: int, max_parallel: int = 100, log_level: str = "INFO"
    ):
        self.host = host
        self.port = port
        self.max_parallel = max_parallel
        self.log_level = log_level
        self.server = None
        self.shutdown_event = asyncio.Event()

        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

    def _setup_logging(self):
        """Setup production logging"""

        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "web_api.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )

        # Reduce aiohttp logging noise
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    async def start_server(self):
        """Start the production server"""
        self.logger.info("🚀 Starting Web API Server (Production Mode)")
        self.logger.info(f"   Host: {self.host}")
        self.logger.info(f"   Port: {self.port}")
        self.logger.info(f"   Max Parallel: {self.max_parallel}")
        self.logger.info(f"   Log Level: {self.log_level}")

        # Create server
        self.server = AsyncWebServer(
            host=self.host, port=self.port, max_parallel=self.max_parallel
        )

        # Add production quality gates
        self.server.add_quality_gate(ProductionQualityGate())

        # Start server
        await self.server.start()

        self.logger.info("✅ Server started successfully")
        self.logger.info(f"   Health check: http://{self.host}:{self.port}/health")
        self.logger.info(f"   Metrics: http://{self.host}:{self.port}/metrics")
        self.logger.info(
            f"   API docs: http://{self.host}:{self.port}/api/v1/execution-plans"
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()

    async def monitor_server(self):
        """Monitor server performance and log metrics periodically"""

        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Get current metrics
                metrics = await self.server.monitor.get_metrics_summary()

                # Log summary
                self.logger.info("📊 Server Metrics Summary:")
                self.logger.info(f"   Total Requests: {metrics['requests_total']}")
                self.logger.info(f"   Active Requests: {metrics['requests_active']}")
                self.logger.info(f"   Success Rate: {metrics['success_rate']:.2f}%")
                self.logger.info(
                    f"   Avg Response Time: {metrics['avg_response_time']:.2f}ms"
                )
                self.logger.info(f"   Uptime: {metrics['uptime_seconds']:.0f}s")

                # Check for issues
                if metrics["success_rate"] < 95.0:
                    self.logger.warning("⚠️  Success rate below 95%")

                if metrics["avg_response_time"] > 1000:
                    self.logger.warning("⚠️  Average response time above 1000ms")

                if metrics["requests_active"] > self.max_parallel * 0.8:
                    self.logger.warning("⚠️  High concurrent request load")

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")

    async def run(self):
        """Run the production server"""

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # Start server
            await self.start_server()

            # Start monitoring
            monitor_task = asyncio.create_task(self.monitor_server())

            # Wait for shutdown signal
            await self.shutdown_event.wait()

            # Cancel monitoring
            monitor_task.cancel()

            # Graceful shutdown
            self.logger.info("🛑 Shutting down server...")
            await self.server.shutdown()
            self.logger.info("✅ Server shutdown complete")

        except Exception as e:
            self.logger.error(f"❌ Server error: {e}")
            if self.server:
                await self.server.shutdown()
            raise


def main():
    """Main deployment function"""

    parser = argparse.ArgumentParser(description="Deploy Web API Server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=100,
        help="Max parallel requests (default: 100)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    parser.add_argument(
        "--check-deps", action="store_true", help="Check dependencies and exit"
    )

    args = parser.parse_args()

    # Check dependencies
    if args.check_deps:
        print("Checking dependencies...")
        try:
            import aiohttp
            import jsonschema

            print("✅ All dependencies satisfied")
            return 0
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Run: pip install -r requirements_web_server.txt")
            return 1

    # Create deployment
    deployment = WebAPIDeployment(
        host=args.host,
        port=args.port,
        max_parallel=args.max_parallel,
        log_level=args.log_level,
    )

    try:
        # Run server
        asyncio.run(deployment.run())
        return 0

    except KeyboardInterrupt:
        print("\n🛑 Deployment interrupted")
        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
