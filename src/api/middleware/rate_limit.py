"""Rate limiting middleware."""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.

    Implements sliding window rate limiting per IP address.
    """

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute per IP
            requests_per_hour: Max requests per hour per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Store request timestamps per IP
        self.minute_requests = defaultdict(list)
        self.hour_requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        """Process request and enforce rate limits."""
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        # Check rate limits
        now = datetime.utcnow()

        # Clean old entries
        self._clean_old_entries(client_ip, now)

        # Check minute limit
        if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip} (minute)")
            return self._rate_limit_response("Too many requests per minute")

        # Check hour limit
        if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
            logger.warning(f"Rate limit exceeded for {client_ip} (hour)")
            return self._rate_limit_response("Too many requests per hour")

        # Record request
        self.minute_requests[client_ip].append(now)
        self.hour_requests[client_ip].append(now)

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Minute-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Minute-Remaining"] = str(
            self.requests_per_minute - len(self.minute_requests[client_ip])
        )
        response.headers["X-RateLimit-Hour-Limit"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Hour-Remaining"] = str(
            self.requests_per_hour - len(self.hour_requests[client_ip])
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _clean_old_entries(self, client_ip: str, now: datetime):
        """Remove expired entries from request history."""
        # Clean minute requests (keep last minute)
        minute_ago = now - timedelta(minutes=1)
        self.minute_requests[client_ip] = [
            ts for ts in self.minute_requests[client_ip]
            if ts > minute_ago
        ]

        # Clean hour requests (keep last hour)
        hour_ago = now - timedelta(hours=1)
        self.hour_requests[client_ip] = [
            ts for ts in self.hour_requests[client_ip]
            if ts > hour_ago
        ]

        # Clean up empty entries
        if not self.minute_requests[client_ip]:
            del self.minute_requests[client_ip]
        if not self.hour_requests[client_ip]:
            del self.hour_requests[client_ip]

    def _rate_limit_response(self, detail: str):
        """Return rate limit exceeded response."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "detail": detail
            },
            headers={
                "Retry-After": "60"
            }
        )
