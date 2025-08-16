"""API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/v1")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
