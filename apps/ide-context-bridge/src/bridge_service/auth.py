#!/usr/bin/env python3
"""
Authentication and authorization for IDE Context Bridge.

Provides API key verification, rate limiting, and security utilities.
"""

import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication related error."""

    pass


class RateLimitExceeded(Exception):
    """Rate limit exceeded error."""

    pass


class APIKeyAuth:
    """API Key authentication manager."""

    def __init__(self, allowed_keys: List[str], header_name: str = "X-API-Key"):
        self.allowed_keys = set(allowed_keys)
        self.header_name = header_name
        self.key_usage = {}  # Track key usage statistics

    def verify_key(self, api_key: str) -> bool:
        """Verify API key."""
        if not api_key:
            return False

        # Hash the key for security (optional)
        key_valid = api_key in self.allowed_keys

        if key_valid:
            # Track usage
            if api_key not in self.key_usage:
                self.key_usage[api_key] = {
                    "first_used": datetime.now(),
                    "last_used": datetime.now(),
                    "usage_count": 0,
                }

            self.key_usage[api_key]["last_used"] = datetime.now()
            self.key_usage[api_key]["usage_count"] += 1

        return key_valid

    def add_key(self, api_key: str):
        """Add new API key."""
        self.allowed_keys.add(api_key)
        logger.info(f"Added new API key: {api_key[:8]}...")

    def remove_key(self, api_key: str):
        """Remove API key."""
        self.allowed_keys.discard(api_key)
        if api_key in self.key_usage:
            del self.key_usage[api_key]
        logger.info(f"Removed API key: {api_key[:8]}...")

    def get_key_stats(self) -> Dict[str, Any]:
        """Get API key usage statistics."""
        return {
            "total_keys": len(self.allowed_keys),
            "active_keys": len(self.key_usage),
            "usage_stats": {
                key[:8] + "...": stats for key, stats in self.key_usage.items()
            },
        }


class RateLimiter:
    """Rate limiting implementation."""

    def __init__(self, rate_limit: str = "100/minute"):
        """
        Initialize rate limiter.

        Args:
            rate_limit: Format like "100/minute", "50/hour", "1000/day"
        """
        self.limits = self._parse_rate_limit(rate_limit)
        self.requests = {}  # client_id -> list of timestamps

    def _parse_rate_limit(self, rate_limit: str) -> Dict[str, int]:
        """Parse rate limit string."""
        parts = rate_limit.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid rate limit format: {rate_limit}")

        count = int(parts[0])
        period = parts[1].lower()

        period_seconds = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}

        if period not in period_seconds:
            raise ValueError(f"Invalid period: {period}")

        return {"count": count, "period": period, "seconds": period_seconds[period]}

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit."""
        now = time.time()
        window_start = now - self.limits["seconds"]

        # Initialize client tracking
        if client_id not in self.requests:
            self.requests[client_id] = []

        # Clean old requests
        self.requests[client_id] = [
            timestamp
            for timestamp in self.requests[client_id]
            if timestamp > window_start
        ]

        # Check limit
        if len(self.requests[client_id]) >= self.limits["count"]:
            return False

        # Record this request
        self.requests[client_id].append(now)
        return True

    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit stats for client."""
        now = time.time()
        window_start = now - self.limits["seconds"]

        if client_id not in self.requests:
            return {
                "requests_in_window": 0,
                "limit": self.limits["count"],
                "period": self.limits["period"],
                "remaining": self.limits["count"],
            }

        # Count requests in current window
        recent_requests = [
            timestamp
            for timestamp in self.requests[client_id]
            if timestamp > window_start
        ]

        return {
            "requests_in_window": len(recent_requests),
            "limit": self.limits["count"],
            "period": self.limits["period"],
            "remaining": max(0, self.limits["count"] - len(recent_requests)),
        }

    def cleanup_old_data(self):
        """Clean up old request data."""
        now = time.time()
        cutoff = now - self.limits["seconds"] * 2  # Keep extra data for safety

        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                timestamp
                for timestamp in self.requests[client_id]
                if timestamp > cutoff
            ]

            # Remove empty entries
            if not self.requests[client_id]:
                del self.requests[client_id]


class JWTAuth:
    """JWT token authentication."""

    def __init__(self, secret_key: str, expire_hours: int = 24):
        self.secret_key = secret_key
        self.expire_hours = expire_hours
        self.algorithm = "HS256"

    def create_token(self, user_id: str, session_id: str, **kwargs) -> str:
        """Create JWT token."""
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.expire_hours),
            **kwargs,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")


class AuthManager:
    """Main authentication manager."""

    def __init__(self, config):
        self.config = config
        self.require_auth = config.security.require_auth
        self.api_key_auth = None
        self.rate_limiter = None
        self.jwt_auth = None

        # Initialize authentication methods
        if self.require_auth:
            self.api_key_auth = APIKeyAuth(
                allowed_keys=config.security.allowed_api_keys,
                header_name=config.security.api_key_header,
            )

        # Initialize rate limiter
        if config.security.rate_limit:
            self.rate_limiter = RateLimiter(config.security.rate_limit)

        # Initialize JWT auth if secret is provided
        if config.security.jwt_secret:
            self.jwt_auth = JWTAuth(
                secret_key=config.security.jwt_secret,
                expire_hours=config.security.jwt_expire_hours,
            )

    def authenticate_request(
        self,
        request: Request,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Authenticate incoming request."""
        client_id = self._get_client_id(request)

        # Check rate limit first
        if self.rate_limiter and not self.rate_limiter.check_rate_limit(client_id):
            raise RateLimitExceeded(f"Rate limit exceeded for client {client_id}")

        # Skip authentication if not required
        if not self.require_auth:
            return {"client_id": client_id, "authenticated": False}

        # Try API key authentication
        if api_key and self.api_key_auth and self.api_key_auth.verify_key(api_key):
            return {
                "client_id": client_id,
                "authenticated": True,
                "auth_type": "api_key",
                "api_key": api_key[:8] + "...",
            }

        # Try JWT token authentication
        if token and self.jwt_auth:
            try:
                payload = self.jwt_auth.verify_token(token)
                return {
                    "client_id": client_id,
                    "authenticated": True,
                    "auth_type": "jwt",
                    "user_id": payload.get("user_id"),
                    "session_id": payload.get("session_id"),
                }
            except AuthenticationError:
                pass

        # Authentication failed
        raise AuthenticationError("Authentication required")

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Use X-Forwarded-For if available (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Use direct client IP
        client_host = getattr(request.client, "host", "unknown")
        return client_host

    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        stats = {
            "require_auth": self.require_auth,
            "rate_limiter_enabled": self.rate_limiter is not None,
            "jwt_auth_enabled": self.jwt_auth is not None,
        }

        if self.api_key_auth:
            stats["api_key_stats"] = self.api_key_auth.get_key_stats()

        return stats


# Global auth manager instance
auth_manager: Optional[AuthManager] = None


def initialize_auth(config) -> AuthManager:
    """Initialize global auth manager."""
    global auth_manager
    auth_manager = AuthManager(config)
    return auth_manager


def get_auth_manager() -> Optional[AuthManager]:
    """Get global auth manager."""
    return auth_manager


# FastAPI dependency functions
def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """FastAPI dependency to verify API key or JWT token."""
    if not auth_manager:
        # No auth configured, allow request
        return {"authenticated": False}

    try:
        # Extract JWT token from Authorization header
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]  # Remove "Bearer " prefix

        # Authenticate request
        auth_info = auth_manager.authenticate_request(
            request=request, api_key=x_api_key, token=token
        )

        return auth_info

    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")


def require_authentication(func):
    """Decorator to require authentication for a function."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if auth_info is in kwargs (from FastAPI dependency)
        auth_info = kwargs.get("auth_info") or kwargs.get("api_key")

        if not auth_info or not auth_info.get("authenticated", False):
            raise HTTPException(status_code=401, detail="Authentication required")

        return await func(*args, **kwargs)

    return wrapper


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def generate_session_id() -> str:
    """Generate a unique session ID."""
    timestamp = str(int(time.time()))
    random_part = secrets.token_urlsafe(16)
    return f"sess_{timestamp}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_hashed_key(api_key: str, hashed_key: str) -> bool:
    """Verify API key against hash."""
    return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key


# Utility functions for security
def is_safe_path(path: str) -> bool:
    """Check if file path is safe (no directory traversal)."""
    # Prevent directory traversal attacks
    if ".." in path or path.startswith("/"):
        return False
    return True


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input."""
    if not text:
        return ""

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", "\x00"]
    for char in dangerous_chars:
        text = text.replace(char, "")

    return text.strip()


if __name__ == "__main__":
    # Test authentication functionality
    print("Testing IDE Context Bridge Authentication...")

    # Generate test API key
    api_key = generate_api_key()
    print(f"Generated API Key: {api_key}")

    # Test hashing
    hashed = hash_api_key(api_key)
    print(f"Hashed Key: {hashed}")
    print(f"Verification: {verify_hashed_key(api_key, hashed)}")

    # Generate session ID
    session_id = generate_session_id()
    print(f"Generated Session ID: {session_id}")

    # Test rate limiter
    rate_limiter = RateLimiter("5/minute")
    client = "test_client"

    print(f"\nTesting rate limiter (5/minute):")
    for i in range(7):
        allowed = rate_limiter.check_rate_limit(client)
        stats = rate_limiter.get_client_stats(client)
        print(
            f"Request {i+1}: {'ALLOWED' if allowed else 'BLOCKED'} - {stats['remaining']} remaining"
        )

    print("\nAuthentication test completed!")
