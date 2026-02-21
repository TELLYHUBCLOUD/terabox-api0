import time
from collections import defaultdict
from fastapi import Request, HTTPException
from app.core.config import settings
from app.utils.logger import log


class RateLimiter:
    """Simple in-memory rate limiter — IP based"""

    def __init__(self):
        self._requests: dict = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        window = settings.RATE_LIMIT_WINDOW
        limit = settings.RATE_LIMIT_REQUESTS

        # Purani requests clean karo
        self._requests[ip] = [
            t for t in self._requests[ip]
            if now - t < window
        ]

        if len(self._requests[ip]) >= limit:
            log.warning(f"Rate limit hit: {ip} ({len(self._requests[ip])} reqs)")
            return False

        self._requests[ip].append(now)
        return True

    def get_remaining(self, ip: str) -> int:
        now = time.time()
        window = settings.RATE_LIMIT_WINDOW
        recent = [t for t in self._requests.get(ip, []) if now - t < window]
        return max(0, settings.RATE_LIMIT_REQUESTS - len(recent))


rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware"""
    ip = request.client.host

    # Health check pe rate limit mat lagao
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    if not rate_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Max {settings.RATE_LIMIT_REQUESTS} requests per {settings.RATE_LIMIT_WINDOW}s",
                "retry_after": settings.RATE_LIMIT_WINDOW,
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(rate_limiter.get_remaining(ip))
    return response
