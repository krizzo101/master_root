"""Main FastAPI application for URL shortener service."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cachetools import TTLCache
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, HttpUrl, validator

from .base62 import decode, encode, extract_id_from_code, generate_short_code
from .config import settings
from .config.logging_config import setup_logging
from .database import DatabaseError, URLDatabase

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize database
db = URLDatabase(settings.database_url)

# Initialize cache
url_cache = (
    TTLCache(maxsize=1000, ttl=settings.cache_ttl) if settings.enable_cache else None
)


# Pydantic models
class URLRequest(BaseModel):
    """Request model for URL shortening."""

    url: HttpUrl
    custom_code: Optional[str] = Field(
        None, min_length=4, max_length=20, regex="^[a-zA-Z0-9]+$"
    )
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)

    @validator("url")
    def validate_url_length(cls, v):
        """Validate URL length."""
        if len(str(v)) > settings.max_url_length:
            raise ValueError(f"URL exceeds maximum length of {settings.max_url_length}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/very/long/url/that/needs/shortening",
                "custom_code": "mycode",
                "expires_in_days": 30,
            }
        }


class URLResponse(BaseModel):
    """Response model for URL shortening."""

    short_url: str
    original_url: str
    short_code: str
    expires_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "short_url": "http://localhost:8000/abc123",
                "original_url": "https://example.com/very/long/url",
                "short_code": "abc123",
                "expires_at": "2024-12-31T23:59:59",
            }
        }


class URLStats(BaseModel):
    """URL statistics model."""

    original_url: str
    short_code: str
    created_at: datetime
    click_count: int
    is_active: bool
    expires_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    status_code: int

    class Config:
        schema_extra = {"example": {"detail": "URL not found", "status_code": 404}}


# Dependency for API key validation
async def validate_api_key(request: Request) -> bool:
    """Validate API key if enabled."""
    if not settings.enable_api_key:
        return True

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return True


# Cleanup task for expired URLs
async def cleanup_expired_urls():
    """Background task to cleanup expired URLs."""
    while True:
        try:
            if settings.enable_auto_cleanup:
                cleaned = db.cleanup_expired()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired URLs")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        await asyncio.sleep(settings.cleanup_interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Start background tasks
    cleanup_task = asyncio.create_task(cleanup_expired_urls())

    yield

    # Shutdown
    logger.info("Shutting down application")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A production-ready URL shortener service",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database operation failed", "status_code": 500},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "status_code": 400},
    )


# Routes
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.post(
    "/shorten",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def shorten_url(
    request: URLRequest, api_key_valid: bool = Depends(validate_api_key)
) -> URLResponse:
    """
    Create a shortened URL.

    - **url**: The original URL to shorten (required)
    - **custom_code**: Optional custom short code
    - **expires_in_days**: Optional expiration in days
    """
    try:
        original_url = str(request.url)

        # Handle custom code
        if request.custom_code:
            short_code = request.custom_code
            # Check if custom code already exists
            existing = db.get_url_by_code(short_code)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Custom code '{short_code}' already exists",
                )
        else:
            # Generate new short code
            # Try to find a unique code
            for attempt in range(10):
                # Use current timestamp + attempt for uniqueness
                import time

                url_id = int(time.time() * 1000) + attempt
                short_code = generate_short_code(url_id, settings.min_code_length)

                # Check if code already exists
                if not db.get_url_by_code(short_code):
                    break
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to generate unique short code",
                )

        # Calculate expiration
        expires_at = None
        if request.expires_in_days or settings.default_expiry_days:
            days = request.expires_in_days or settings.default_expiry_days
            expires_at = datetime.now() + timedelta(days=days)

        # Insert into database
        url_id = db.insert_url(original_url, short_code, expires_at)

        # Clear cache for this code if exists
        if url_cache and short_code in url_cache:
            del url_cache[short_code]

        # Build response
        short_url = f"{settings.base_url}/{short_code}"

        logger.info(f"Created short URL: {short_url} -> {original_url}")

        return URLResponse(
            short_url=short_url,
            original_url=original_url,
            short_code=short_code,
            expires_at=expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create short URL",
        )


@app.get(
    "/{code}",
    response_class=RedirectResponse,
    responses={404: {"model": ErrorResponse}, 410: {"model": ErrorResponse}},
)
async def redirect_url(code: str):
    """
    Redirect to the original URL using the short code.

    - **code**: The short code to resolve
    """
    try:
        # Check cache first
        if url_cache and code in url_cache:
            original_url = url_cache[code]
            logger.debug(f"Cache hit for code: {code}")
        else:
            # Lookup in database
            url_data = db.get_url_by_code(code)

            if not url_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
                )

            # Check if expired
            if url_data.get("expires_at"):
                expires_at = datetime.fromisoformat(url_data["expires_at"])
                if expires_at < datetime.now():
                    raise HTTPException(
                        status_code=status.HTTP_410_GONE, detail="Short URL has expired"
                    )

            original_url = url_data["original_url"]

            # Update cache
            if url_cache:
                url_cache[code] = original_url

        # Increment click count asynchronously
        asyncio.create_task(asyncio.to_thread(db.increment_click_count, code))

        logger.info(f"Redirecting {code} to {original_url}")
        return RedirectResponse(
            url=original_url, status_code=status.HTTP_301_MOVED_PERMANENTLY
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error redirecting URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to redirect",
        )


@app.get(
    "/api/stats/{code}",
    response_model=URLStats,
    responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def get_url_stats(
    code: str, api_key_valid: bool = Depends(validate_api_key)
) -> URLStats:
    """
    Get statistics for a shortened URL.

    - **code**: The short code to get stats for
    """
    try:
        url_data = db.get_url_by_code(code)

        if not url_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
            )

        return URLStats(
            original_url=url_data["original_url"],
            short_code=url_data["short_code"],
            created_at=datetime.fromisoformat(url_data["created_at"]),
            click_count=url_data["click_count"],
            is_active=bool(url_data["is_active"]),
            expires_at=datetime.fromisoformat(url_data["expires_at"])
            if url_data.get("expires_at")
            else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics",
        )


@app.get("/api/health", include_in_schema=False)
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connectivity
        stats = db.get_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "total_urls": stats.get("total_urls", 0),
            "active_urls": stats.get("active_urls", 0),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"},
        )


@app.delete(
    "/api/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def delete_url(code: str, api_key_valid: bool = Depends(validate_api_key)):
    """
    Delete (deactivate) a shortened URL.

    - **code**: The short code to delete
    """
    try:
        success = db.deactivate_url(code)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
            )

        # Clear from cache
        if url_cache and code in url_cache:
            del url_cache[code]

        logger.info(f"Deleted short URL: {code}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete URL",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
