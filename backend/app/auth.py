"""
Authentication module for Supabase JWT verification using GoTrue JWKS.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import httpx
from jose import jwt, jwk, JWTError
from jose.utils import base64url_decode
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# HTTP Bearer token scheme
security = HTTPBearer()

# Cache for JWKS keys
_jwks_cache: Optional[Dict[str, Any]] = None
_cache_expiry: Optional[datetime] = None


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(httpx.RequestError)
)
async def fetch_jwks() -> Dict[str, Any]:
    """
    Fetch JWKS keys from Supabase GoTrue endpoint with retry logic.
    
    Returns:
        Dict[str, Any]: JWKS response
        
    Raises:
        AuthenticationError: If JWKS fetch fails
    """
    global _jwks_cache, _cache_expiry
    
    # Check cache (valid for 1 hour)
    now = datetime.now(timezone.utc)
    if _jwks_cache and _cache_expiry and now < _cache_expiry:
        return _jwks_cache
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.jwt_jwks_url,
                timeout=10.0
            )
            response.raise_for_status()
            
            jwks_data = response.json()
            
            # Cache the result for 1 hour
            _jwks_cache = jwks_data
            _cache_expiry = now.replace(hour=now.hour + 1) if now.hour < 23 else now.replace(day=now.day + 1, hour=0)
            
            logger.info("JWKS keys fetched and cached successfully")
            return jwks_data
            
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch JWKS keys: {e}")
        raise AuthenticationError("Unable to verify token")
    except Exception as e:
        logger.error(f"Unexpected error fetching JWKS: {e}")
        raise AuthenticationError("Authentication service unavailable")


def get_signing_key(token: str, jwks: Dict[str, Any]) -> str:
    """
    Get the signing key for JWT verification.
    
    Args:
        token: JWT token
        jwks: JWKS response
        
    Returns:
        str: Signing key
        
    Raises:
        AuthenticationError: If signing key not found
    """
    try:
        # Get unverified header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise AuthenticationError("Token missing key ID")
        
        # Find the key in JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PEM format
                rsa_key = jwk.construct(key)
                return rsa_key.to_pem().decode("utf-8")
        
        raise AuthenticationError("Signing key not found")
        
    except JWTError as e:
        logger.error(f"JWT header error: {e}")
        raise AuthenticationError("Invalid token format")


async def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token using Supabase JWKS or JWT secret.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict[str, Any]: Decoded token payload
        
    Raises:
        AuthenticationError: If token verification fails
    """
    try:
        # Get unverified header to check algorithm
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get("alg", "RS256")
        
        if algorithm == "HS256":
            # For HS256, use JWT secret from settings
            if not settings.jwt_secret:
                logger.error("JWT secret not configured for HS256 algorithm")
                raise AuthenticationError("JWT configuration error")
            
            try:
                payload = jwt.decode(
                    token,
                    key=settings.jwt_secret,
                    algorithms=["HS256"],
                    audience=settings.jwt_audience,
                    options={
                        "verify_signature": True,
                        "verify_aud": True,
                        "verify_exp": True,
                        "verify_iat": True,
                        "verify_nbf": True,
                    }
                )
                logger.info("JWT token verified successfully with HS256")
            except JWTError as e:
                logger.error(f"JWT verification failed with HS256: {e}")
                raise AuthenticationError("Invalid or expired token")
        else:
            # For RS256, use JWKS
            jwks = await fetch_jwks()
            signing_key = get_signing_key(token, jwks)
            
            # Verify and decode token with RS256
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=settings.jwt_audience,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                }
            )
        
        # Validate required claims
        if not payload.get("sub"):
            raise AuthenticationError("Token missing user ID")
        
        return payload
        
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise AuthenticationError("Invalid or expired token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise AuthenticationError("Authentication failed")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Dict[str, Any]: User information from JWT payload
        
    Raises:
        AuthenticationError: If authentication fails
    """
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Missing authentication token")
    
    payload = await verify_token(credentials.credentials)
    
    # Extract user information
    user_info = {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "aud": payload.get("aud"),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
    }
    
    return user_info


async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    FastAPI dependency to get current user ID.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        str: User ID
    """
    return current_user["user_id"]


def require_roles(*required_roles: str):
    """
    Decorator factory for role-based access control.
    
    Args:
        *required_roles: Required roles for access
        
    Returns:
        Dependency function that checks user roles
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "")
        
        if required_roles and user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_roles}"
            )
        
        return current_user
    
    return role_checker


# Optional authentication (returns None if no token)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        
    Returns:
        Optional[Dict[str, Any]]: User info if authenticated, None otherwise
    """
    if not credentials or not credentials.credentials:
        return None
    
    try:
        return await verify_token(credentials.credentials)
    except AuthenticationError:
        return None
