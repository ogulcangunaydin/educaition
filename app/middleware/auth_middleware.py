import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.token_service import (
    TokenBlacklistedError,
    TokenExpiredError,
    TokenInvalidError,
    verify_access_token,
)

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {
        "/api/authenticate",
        "/api/refresh",
        "/api/password-requirements",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
    }

    PUBLIC_PREFIXES = (
        "/api/players/",  # Game players (handled by participant tokens)
        "/api/dissonance_test_participants/",  # Test participants (handled by participant tokens)
        "/api/program-suggestion/students/",  # Students (handled by participant tokens)
    )

    def __init__(self, app: Callable, exclude_paths: set[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or set()

    def _is_public_path(self, path: str) -> bool:
        if path in self.PUBLIC_PATHS or path in self.exclude_paths:
            return True

        return bool(path.startswith(self.PUBLIC_PREFIXES))

    def _extract_token(self, request: Request) -> str | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if self._is_public_path(path):
            return await call_next(request)

        token = self._extract_token(request)

        if token:
            try:
                payload = verify_access_token(token)
                request.state.user_id = payload.user_id
                request.state.username = payload.sub
                request.state.token_jti = payload.jti
            except TokenExpiredError:
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Token has expired",
                        "error_code": "token_expired",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except TokenBlacklistedError:
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Token has been revoked",
                        "error_code": "token_blacklisted",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except TokenInvalidError as e:
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": f"Invalid token: {e.message}",
                        "error_code": "token_invalid",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except Exception as e:
                logger.error(f"Unexpected auth error: {e}")
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Authentication failed",
                        "error_code": "auth_error",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Continue to the route handler (FastAPI's Depends will handle actual auth)
        return await call_next(request)
