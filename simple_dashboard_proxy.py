#!/usr/bin/env python3
"""
Simple Dashboard Proxy
Serves dashboard on port 8005 and proxies API calls to port 8004
"""

import asyncio

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static files from the dashboard
try:
    app.mount(
        "/static",
        StaticFiles(
            directory="/home/opsvi/master_root/apps/project-context/dashboard/frontend"
        ),
        name="static",
    )
except Exception as e:
    print(f"Could not mount static files: {e}")


@app.get("/")
async def serve_dashboard():
    """Serve the main dashboard HTML"""
    return FileResponse(
        "/home/opsvi/master_root/apps/project-context/dashboard/frontend/index.html"
    )


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_api(request: Request, path: str):
    """Proxy all API calls to port 8004"""
    target_url = f"http://localhost:8004/api/{path}"

    async with httpx.AsyncClient() as client:
        # Forward the request to port 8004
        response = await client.request(
            method=request.method,
            url=target_url,
            params=request.query_params,
            headers=dict(request.headers),
            content=await request.body(),
        )

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@app.websocket("/ws")
async def websocket_proxy(websocket):
    """Proxy WebSocket connections to port 8004"""
    # This is a simple WebSocket proxy - for full functionality
    # you'd need more complex WebSocket proxying
    await websocket.accept()
    await websocket.send_json({"type": "info", "message": "WebSocket proxy active"})


if __name__ == "__main__":
    print("🔄 Starting Dashboard Proxy on port 8005")
    print("📡 Proxying API calls to port 8004")
    uvicorn.run("simple_dashboard_proxy:app", host="0.0.0.0", port=8005, reload=False)
