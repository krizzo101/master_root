"""
main.py: Entry point for the FastAPI backend server.
- Loads config
- Initializes DB and Redis
- Registers API, GraphQL, WebSocket routes
- Handles graceful shutdown
"""
import logging

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.api import api_router
from backend.audit import setup_audit_logging
from backend.auth import auth_router
from backend.calendar import calendar_router
from backend.config import Settings, get_settings
from backend.database import engine
from backend.files import storage_router
from backend.graphql_app import graphql_app
from backend.models import Base
from backend.utils import rate_limit_middleware
from backend.ws import ws_router

settings: Settings = get_settings()
logger = logging.getLogger("taskmgmt")
setup_audit_logging(settings)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Powered Collaborative Task Management System", version="1.0.0")

# Middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(rate_limit_middleware)

# Static files (if needed)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(ws_router, prefix="/ws")
app.include_router(storage_router, prefix="/files")
app.include_router(calendar_router, prefix="/calendar", tags=["calendar"])

app.mount("/graphql", graphql_app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception for {request.url}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/healthz", tags=["monitor"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug
    )
