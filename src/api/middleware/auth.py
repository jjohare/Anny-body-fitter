"""Authentication middleware."""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging
import jwt
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protecting API endpoints."""

    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next):
        """Process request and validate authentication."""
        path = request.url.path

        # Allow public endpoints
        if path in self.PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # For development: allow unauthenticated access
        # Remove this in production!
        if os.getenv("DISABLE_AUTH", "false").lower() == "true":
            logger.warning("Authentication disabled - development mode only!")
            request.state.user = {"id": "dev_user", "username": "developer"}
            return await call_next(request)

        # Validate authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized_response("Missing authorization header")

        try:
            token = auth_header.replace("Bearer ", "")
            payload = decode_access_token(token)
            request.state.user = payload
        except HTTPException as e:
            return self._unauthorized_response(str(e.detail))
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return self._unauthorized_response("Invalid authentication")

        return await call_next(request)

    def _unauthorized_response(self, detail: str):
        """Return unauthorized response."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Unauthorized", "detail": detail},
            headers={"WWW-Authenticate": "Bearer"}
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data to encode
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT access token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(request: Request) -> dict:
    """
    Dependency to get current authenticated user.

    Args:
        request: FastAPI request object

    Returns:
        User information from token

    Raises:
        HTTPException: If user not authenticated
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return request.state.user


# Utility function for login endpoint (to be used in auth routes)
async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user credentials.

    This is a placeholder - implement with your actual user database.

    Args:
        username: Username
        password: Password

    Returns:
        User dict if authenticated, None otherwise
    """
    # TODO: Implement actual user authentication
    # For now, accept any credentials in development
    if os.getenv("DISABLE_AUTH", "false").lower() == "true":
        return {
            "id": "dev_user",
            "username": username,
            "email": f"{username}@example.com"
        }

    return None
