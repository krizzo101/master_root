#!/usr/bin/env python3
"""
Simple startup script for the async web server
"""

import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from async_web_server import AsyncWebServer, RequestQualityGate


class CustomQualityGate(RequestQualityGate):
    """Custom quality gate with enhanced validation"""

    async def validate_rate_limit(self, request):
        # Simple rate limiting example
        return {"passed": True, "issues": []}

    async def validate_input(self, request):
        # Basic input validation
        if request.context.get("body"):
            # Check for potentially large payloads
            body = request.context["body"]
            if isinstance(body, dict) and len(str(body)) > 10000:
                return {"passed": False, "issues": ["Payload too large"]}
        return {"passed": True, "issues": []}


async def main():
    """Main server startup"""

    # Parse command line arguments
    host = "0.0.0.0"
    port = 8000
    max_parallel = 20

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    if len(sys.argv) > 2:
        host = sys.argv[2]

    print(f"Starting async web server on {host}:{port}")
    print(f"Max parallel requests: {max_parallel}")

    # Initialize server
    server = AsyncWebServer(host=host, port=port, max_parallel=max_parallel)

    # Add custom quality gate
    server.add_quality_gate(CustomQualityGate())

    # Start server
    await server.start()

    print("\nServer is running. Press Ctrl+C to stop.")
    print(f"Test endpoints:")
    print(f"  - Health: http://{host}:{port}/health")
    print(f"  - Metrics: http://{host}:{port}/metrics")
    print(f"  - Any path: http://{host}:{port}/your/path/here")

    # Keep running
    try:
        while True:
            await asyncio.sleep(300)  # Check metrics every 5 minutes
            metrics = await server.monitor.get_metrics()
            if metrics["requests_started"] > 0:
                print(f"\n📊 Server metrics: {metrics}")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        await server.shutdown()
        print("Server stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer interrupted.")
