"""
Middleware for logging and CORS in the Task Management API.
"""
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging details of incoming requests and responses.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"Incoming {request.method} request to {request.url.path}")
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # ms
        logger.info(
            f"Completed {request.method} {request.url.path} in {process_time:.2f}ms with status {response.status_code}"
        )
        return response


def setup_middleware(app: FastAPI) -> None:
    """
    Configure middleware for the FastAPI app (CORS and logging).
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict as needed!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
