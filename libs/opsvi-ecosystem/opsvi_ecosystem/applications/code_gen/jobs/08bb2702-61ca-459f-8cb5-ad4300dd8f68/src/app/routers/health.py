"""
Health check endpoint for the Task Management API.
"""
from fastapi import APIRouter, status
from app.database import engine
import asyncio

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify service is running.
    """
    # Optionally: check database connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        return {"status": "unhealthy"}
