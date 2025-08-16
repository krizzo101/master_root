import logging

import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import tasks

logger = logging.getLogger("uvicorn.error")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"{request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Status code: {response.status_code}")
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Simple Task Management API",
        description="A simple FastAPI-powered API for managing tasks.",
        version="1.0.0",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    # Routers
    app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring purposes."""
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=True,
    )
