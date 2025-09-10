#!/usr/bin/env python3
"""
Live Orchestrator Management API
Allows real-time task injection and dependency management
"""

import asyncio
import json
import signal
import sys
from datetime import datetime
from pathlib import Path

from aiohttp import web

# import aiohttp_cors  # Not available

# Find running orchestrator by process ID or shared memory
ORCHESTRATOR_STATE_FILE = "outputs/analysis/current_orchestrator_state.json"


class OrchestratorAPI:
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Setup API endpoints for live management"""
        self.app.router.add_get("/status", self.get_status)
        self.app.router.add_post("/inject_tasks", self.inject_tasks)
        self.app.router.add_post("/update_dependencies", self.update_dependencies)
        self.app.router.add_post("/trigger_continue", self.trigger_continue)

        # CORS headers (simple version)
        async def add_cors_headers(request, handler):
            response = await handler(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response

        self.app.middlewares.append(add_cors_headers)

    async def get_status(self, request):
        """Get current orchestrator status"""
        try:
            # Find latest analysis directory
            analysis_dirs = list(Path("outputs/analysis/").glob("system_analysis_*"))
            if not analysis_dirs:
                return web.json_response({"error": "No analysis found"}, status=404)

            latest_dir = sorted(analysis_dirs)[-1]

            # Read task status
            task_files = list((latest_dir / "tasks").glob("*.json"))
            status = {
                "analysis_dir": str(latest_dir),
                "total_tasks": len(task_files),
                "completed_tasks": len(task_files),
                "timestamp": datetime.now().isoformat(),
                "task_files": [f.name for f in task_files],
            }

            return web.json_response(status)

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def inject_tasks(self, request):
        """Inject new tasks into running orchestrator"""
        try:
            data = await request.json()

            # Write injection request to file system
            injection_file = f"outputs/analysis/task_injection_{datetime.now().strftime('%H%M%S')}.json"
            with open(injection_file, "w") as f:
                json.dump(data, f, indent=2)

            return web.json_response(
                {
                    "status": "injection_queued",
                    "file": injection_file,
                    "message": "Tasks queued for injection",
                }
            )

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def update_dependencies(self, request):
        """Update task dependencies dynamically"""
        try:
            data = await request.json()

            # Write dependency update to file system
            update_file = f"outputs/analysis/dependency_update_{datetime.now().strftime('%H%M%S')}.json"
            with open(update_file, "w") as f:
                json.dump(
                    {"timestamp": datetime.now().isoformat(), "updates": data},
                    f,
                    indent=2,
                )

            return web.json_response(
                {
                    "status": "dependencies_updated",
                    "file": update_file,
                    "message": "Dependencies updated, orchestrator will reload",
                }
            )

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def trigger_continue(self, request):
        """Force orchestrator to continue with available completed tasks"""
        try:
            data = await request.json()

            # Create continue signal
            continue_file = f"outputs/analysis/continue_signal_{datetime.now().strftime('%H%M%S')}.json"
            with open(continue_file, "w") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "action": "force_continue",
                        "override_dependencies": data.get("override_dependencies", []),
                    },
                    f,
                    indent=2,
                )

            return web.json_response(
                {
                    "status": "continue_triggered",
                    "file": continue_file,
                    "message": "Orchestrator signaled to continue",
                }
            )

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)


async def start_api_server():
    """Start the management API server"""
    api = OrchestratorAPI()

    runner = web.AppRunner(api.app)
    await runner.setup()

    site = web.TCPSite(runner, "localhost", 8888)
    await site.start()

    print("🌐 Orchestrator Management API started on http://localhost:8888")
    print("📊 Status: GET /status")
    print("🔄 Inject tasks: POST /inject_tasks")
    print("📝 Update deps: POST /update_dependencies")
    print("▶️  Force continue: POST /trigger_continue")

    # Keep server running
    try:
        await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        print("\n🛑 API server shutting down...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(start_api_server())
    except KeyboardInterrupt:
        print("👋 API server stopped")
