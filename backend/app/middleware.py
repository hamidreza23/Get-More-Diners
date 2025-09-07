"""
Authentication middleware for Supabase JWT verification.
Automatically extracts and verifies JWT tokens, setting user context in request state.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .auth import verify_token, AuthenticationError

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically verify Supabase JWT tokens and set user context.
    
    For each request:
    1. Extracts Authorization: Bearer <token> header
    2. Verifies JWT using Supabase JWKS (with caching)
    3. Sets request.state.user_id and request.state.user for authenticated requests
    4. Allows unauthenticated requests to pass through (routes can check auth state)
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        exclude_paths: Optional[list] = None,
        require_auth_paths: Optional[list] = None
    ):
        """
        Initialize auth middleware.
        
        Args:
            app: ASGI application
            exclude_paths: Paths to skip authentication entirely
            require_auth_paths: Paths that require authentication (return 401 if not authenticated)
        """
        super().__init__(app)
        
        # Default paths that don't need authentication
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/health/detailed",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/docs",
            "/api/v1/redoc",
            "/api/v1/openapi.json"
        ]
        
        # Paths that require authentication (will return 401 if not authenticated)
        self.require_auth_paths = require_auth_paths or [
            "/api/v1/restaurants",
            "/api/v1/campaigns",
            "/api/v1/diners",
            "/api/v1/ai",
            "/api/v1/me"
        ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process each request through the authentication middleware.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            Response: HTTP response
        """
        # Initialize user state
        request.state.user_id = None
        request.state.user = None
        request.state.authenticated = False
        
        # Debug logging
        logger.info(f"AuthMiddleware processing: {request.method} {request.url.path}")
        
        # Allow CORS preflight to pass through unchallenged
        if request.method.upper() == "OPTIONS":
            logger.info(f"Skipping auth for OPTIONS request: {request.url.path}")
            return await call_next(request)

        # Skip auth for excluded paths
        if self._should_exclude_path(request.url.path):
            logger.info(f"Skipping auth for excluded path: {request.url.path}")
            return await call_next(request)
        
        # Check if this path requires authentication
        if not self._requires_authentication(request.url.path):
            logger.info(f"Path does not require authentication: {request.url.path}")
            return await call_next(request)
        
        # Extract token from Authorization header
        token = self._extract_token(request)
        
        # If no token provided, return 401 (we already checked this path requires auth)
        if not token:
            return self._create_auth_error_response(
                "Missing authentication token",
                status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify token
        try:
            logger.info(f"Attempting to verify token: {token[:50]}...")
            user_payload = await verify_token(token)
            user_id = user_payload.get("sub")
            
            # Check if user is deleted (simplified for now)
            # In production, you would check the deleted_users table here
            # For now, we'll skip this check to avoid database access in middleware
            
            # Set user context in request state
            request.state.user_id = user_id
            request.state.user = user_payload
            request.state.authenticated = True
            
            logger.info(f"Successfully authenticated user: {request.state.user_id}")
            
        except AuthenticationError as e:
            # Check if this path requires authentication
            if self._requires_authentication(request.url.path):
                return self._create_auth_error_response(
                    e.detail,
                    e.status_code
                )
            
            # For optional auth paths, log the error but continue
            logger.warning(f"Authentication failed for optional auth path: {e.detail}")
        
        except Exception as e:
            logger.error(f"Unexpected auth middleware error: {e}")
            
            # Check if this path requires authentication
            if self._requires_authentication(request.url.path):
                return self._create_auth_error_response(
                    "Authentication service error",
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Continue to next middleware/route handler
        return await call_next(request)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            request: HTTP request
            
        Returns:
            Optional[str]: JWT token if found, None otherwise
        """
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return None
        
        # Check for Bearer token format
        if not authorization.startswith("Bearer "):
            logger.warning(f"Invalid authorization header format: {authorization[:20]}...")
            return None
        
        # Extract token (remove "Bearer " prefix)
        token = authorization[7:].strip()
        
        if not token:
            logger.warning("Empty token in Authorization header")
            return None
        
        return token
    
    def _should_exclude_path(self, path: str) -> bool:
        """
        Check if path should be excluded from authentication.
        
        Args:
            path: Request path
            
        Returns:
            bool: True if path should be excluded
        """
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    def _requires_authentication(self, path: str) -> bool:
        """
        Check if path requires authentication.
        
        Args:
            path: Request path
            
        Returns:
            bool: True if authentication is required
        """
        for auth_path in self.require_auth_paths:
            if path.startswith(auth_path):
                return True
        return False
    
    def _create_auth_error_response(self, detail: str, status_code: int) -> JSONResponse:
        """
        Create standardized authentication error response.
        
        Args:
            detail: Error detail message
            status_code: HTTP status code
            
        Returns:
            JSONResponse: Error response
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "type": "authentication_error",
                "authenticated": False
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user_from_state(request: Request) -> Dict[str, Any]:
    """
    Get current user from request state (set by middleware).
    
    Args:
        request: HTTP request with user state
        
    Returns:
        Dict[str, Any]: User information
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not getattr(request.state, "authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication state",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def get_current_user_id_from_state(request: Request) -> str:
    """
    Get current user ID from request state (set by middleware).
    
    Args:
        request: HTTP request with user state
        
    Returns:
        str: User ID
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = get_current_user_from_state(request)
    user_id = user.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_id


def get_optional_user_from_state(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user from request state if authenticated, None otherwise.
    
    Args:
        request: HTTP request
        
    Returns:
        Optional[Dict[str, Any]]: User information if authenticated, None otherwise
    """
    if not getattr(request.state, "authenticated", False):
        return None
    
    return getattr(request.state, "user", None)


def require_auth(request: Request) -> None:
    """
    Decorator helper to require authentication for a route.
    
    Args:
        request: HTTP request
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not getattr(request.state, "authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this endpoint",
            headers={"WWW-Authenticate": "Bearer"}
        )


def require_roles(request: Request, *required_roles: str) -> Dict[str, Any]:
    """
    Require specific roles for a route.
    
    Args:
        request: HTTP request
        *required_roles: Required role names
        
    Returns:
        Dict[str, Any]: User information
        
    Raises:
        HTTPException: If user doesn't have required roles
    """
    user = get_current_user_from_state(request)
    user_role = user.get("role", "")
    
    if required_roles and user_role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {required_roles}"
        )
    
    return user


class OptionalAuthMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware that only sets auth context without enforcing authentication.
    Useful for routes that want to check auth state but don't require it.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with optional authentication."""
        # Initialize user state
        request.state.user_id = None
        request.state.user = None
        request.state.authenticated = False
        
        # Extract and verify token if present
        authorization = request.headers.get("Authorization")
        
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:].strip()
            
            if token:
                try:
                    user_payload = await verify_token(token)
                    request.state.user_id = user_payload.get("sub")
                    request.state.user = user_payload
                    request.state.authenticated = True
                except Exception as e:
                    # Log but don't fail the request
                    logger.debug(f"Optional auth failed: {e}")
        
        return await call_next(request)
