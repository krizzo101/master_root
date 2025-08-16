"""
Utilities: pagination, rate limiting, common helpers
"""
import time

from fastapi import HTTPException, Request

# Simple in-memory rate limit for demo (for prod, use Redis)
RATE_LIMIT = 100  # reqs per minute
user_hits = {}


def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host
    now = int(time.time() / 60)
    key = f"{ip}:{now}"
    user_hits.setdefault(key, 0)
    user_hits[key] += 1
    if user_hits[key] > RATE_LIMIT:
        raise HTTPException(429, "Too many requests. Please slow down.")
    return call_next(request)


def paginate(items: list, page: int = 1, per_page: int = 25):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]
