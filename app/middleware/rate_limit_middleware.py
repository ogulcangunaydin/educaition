import logging
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    AUTH_PATHS = {
        "/api/authenticate",
        "/api/refresh",
    }

    def __init__(
        self,
        app: Callable,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        auth_requests_per_minute: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.auth_requests_per_minute = auth_requests_per_minute

        self._requests: dict[str, list[tuple[float, str]]] = defaultdict(list)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")

        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_old_requests(self, current_time: float) -> None:
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        one_hour_ago = current_time - 3600
        for ip in list(self._requests.keys()):
            self._requests[ip] = [
                (ts, path) for ts, path in self._requests[ip] if ts > one_hour_ago
            ]
            if not self._requests[ip]:
                del self._requests[ip]

        self._last_cleanup = current_time

    def _is_rate_limited(self, client_ip: str, path: str) -> tuple[bool, str | None]:
        current_time = time.time()
        one_minute_ago = current_time - 60
        one_hour_ago = current_time - 3600
        client_requests = self._requests[client_ip]

        requests_last_minute = sum(
            1 for ts, _ in client_requests if ts > one_minute_ago
        )
        requests_last_hour = sum(1 for ts, _ in client_requests if ts > one_hour_ago)

        if path in self.AUTH_PATHS:
            auth_requests_last_minute = sum(
                1
                for ts, p in client_requests
                if ts > one_minute_ago and p in self.AUTH_PATHS
            )
            if auth_requests_last_minute >= self.auth_requests_per_minute:
                return True, "Too many authentication attempts. Please try again later."

        if requests_last_minute >= self.requests_per_minute:
            return (
                True,
                f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
            )

        if requests_last_hour >= self.requests_per_hour:
            return (
                True,
                f"Rate limit exceeded. Maximum {self.requests_per_hour} requests per hour.",
            )

        return False, None

    def _record_request(self, client_ip: str, path: str) -> None:
        current_time = time.time()
        self._requests[client_ip].append((current_time, path))
        self._cleanup_old_requests(current_time)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        path = request.url.path

        is_limited, message = self._is_rate_limited(client_ip, path)

        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": message,
                    "error_code": "rate_limit_exceeded",
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                },
            )

        self._record_request(client_ip, path)
        response = await call_next(request)
        return response
