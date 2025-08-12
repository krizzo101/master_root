"""Rate limiting middleware for the code generation API."""

import time
import hashlib
from typing import Dict, Tuple
from collections import defaultdict, deque
from fastapi import Request, HTTPException
import logging

from config import config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter with IP-based tracking."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # Store request timestamps per IP
        self._requests: Dict[str, deque] = defaultdict(lambda: deque())

        # Track blocked IPs with expiry
        self._blocked_ips: Dict[str, float] = {}

        # Cleanup interval
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP address with hash for privacy)."""
        # Get real IP from headers (for reverse proxy setups)
        real_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "").strip()
            or request.client.host
            if request.client
            else "unknown"
        )

        # Hash IP for privacy while maintaining uniqueness
        return hashlib.sha256(real_ip.encode()).hexdigest()[:16]

    def _cleanup_old_requests(self) -> None:
        """Remove old request records and expired blocks."""
        now = time.time()

        # Only cleanup periodically
        if now - self._last_cleanup < self._cleanup_interval:
            return

        cutoff_time = now - self.window_seconds

        # Clean old requests
        for client_id in list(self._requests.keys()):
            client_requests = self._requests[client_id]

            # Remove old requests
            while client_requests and client_requests[0] < cutoff_time:
                client_requests.popleft()

            # Remove empty queues
            if not client_requests:
                del self._requests[client_id]

        # Clean expired blocks
        for client_id in list(self._blocked_ips.keys()):
            if self._blocked_ips[client_id] < now:
                del self._blocked_ips[client_id]

        self._last_cleanup = now

    def is_allowed(self, request: Request) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed under rate limits.

        Returns:
            (allowed, info) - allowed is bool, info contains rate limit details
        """
        now = time.time()
        client_id = self._get_client_id(request)

        # Cleanup old data
        self._cleanup_old_requests()

        # Check if IP is currently blocked
        if client_id in self._blocked_ips:
            remaining_block = self._blocked_ips[client_id] - now
            if remaining_block > 0:
                return False, {
                    "blocked_until": self._blocked_ips[client_id],
                    "remaining_seconds": int(remaining_block),
                    "reason": "IP temporarily blocked due to rate limit violations",
                }
            else:
                # Block expired
                del self._blocked_ips[client_id]

        # Get client's request history
        client_requests = self._requests[client_id]

        # Remove requests outside the window
        cutoff_time = now - self.window_seconds
        while client_requests and client_requests[0] < cutoff_time:
            client_requests.popleft()

        # Check if under limit
        current_count = len(client_requests)

        info = {
            "limit": self.max_requests,
            "window_seconds": self.window_seconds,
            "current_count": current_count,
            "remaining": max(0, self.max_requests - current_count),
            "reset_at": now + self.window_seconds if client_requests else now,
        }

        if current_count >= self.max_requests:
            # Rate limit exceeded - block IP for a period
            block_duration = min(self.window_seconds * 2, 3600)  # Max 1 hour
            self._blocked_ips[client_id] = now + block_duration

            logger.warning(
                f"Rate limit exceeded for client {client_id[:8]}... - blocked for {block_duration}s"
            )

            info.update(
                {
                    "blocked_until": self._blocked_ips[client_id],
                    "block_duration": block_duration,
                    "reason": "Rate limit exceeded",
                }
            )

            return False, info

        # Allow request and record it
        client_requests.append(now)
        info["current_count"] += 1
        info["remaining"] -= 1

        return True, info

    def get_status(self) -> Dict[str, any]:
        """Get rate limiter status."""
        self._cleanup_old_requests()

        return {
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "active_clients": len(self._requests),
            "blocked_clients": len(self._blocked_ips),
            "total_tracked_requests": sum(
                len(reqs) for reqs in self._requests.values()
            ),
        }


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=config.rate_limit_requests, window_seconds=config.rate_limit_window
)


async def rate_limit_middleware(request: Request) -> None:
    """FastAPI middleware for rate limiting."""
    # Skip rate limiting for health/metrics endpoints
    if (
        request.url.path in ["/health", "/metrics", "/info"]
        or request.url.path.startswith("/status")
        or request.url.path == "/favicon.ico"
    ):
        return

    # Check rate limit
    allowed, info = rate_limiter.is_allowed(request)

    if not allowed:
        logger.warning(f"Rate limit exceeded for {request.url.path}")
        raise HTTPException(
            status_code=429,
            detail={"error": "Rate limit exceeded", "info": info},
            headers={
                "Retry-After": str(
                    int(info.get("remaining_seconds", info.get("block_duration", 60)))
                )
            },
        )

    # Add rate limit headers to response (will be added by middleware)
    request.state.rate_limit_info = info
