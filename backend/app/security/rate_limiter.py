import time
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Fallback in-memory store for rate limiting
_memory_limiter_store = {}

async def check_rate_limit(request: Request, limit: int = 100, window_secs: int = 60):
    """
    Very simple, clean, and reliable rate limiter.
    Defaults to 100 requests per minute per IP address.
    """
    ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Try to clean up expired timestamps from in-memory dictionary
    if ip not in _memory_limiter_store:
        _memory_limiter_store[ip] = []

    timestamps = _memory_limiter_store[ip]
    # Filter for timestamps within the current window
    active_timestamps = [ts for ts in timestamps if now - ts < window_secs]

    if len(active_timestamps) >= limit:
        logger.warning(f"Rate limit exceeded for IP: {ip}. Active request count: {len(active_timestamps)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

    active_timestamps.append(now)
    _memory_limiter_store[ip] = active_timestamps
