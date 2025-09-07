"""
Authentication routes for Supabase integration.
Adds a lightweight email-existence check using Supabase Admin API (service role).
"""

from fastapi import APIRouter, Request, HTTPException, status, Query
from typing import Dict, Any
import logging

from ..middleware import get_current_user_from_state, get_optional_user_from_state
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


@router.get("/me")
async def get_current_user_info(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user information.
    
    Returns:
        Dict[str, Any]: User information from JWT token
    """
    current_user = get_current_user_from_state(request)
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role", "authenticated"),
        "authenticated": True,
    }


@router.post("/verify")
async def verify_token(request: Request) -> Dict[str, str]:
    """
    Verify if the provided token is valid.
    
    Returns:
        Dict[str, str]: Token verification status
    """
    current_user = get_current_user_from_state(request)
    return {
        "status": "valid",
        "user_id": current_user.get("sub"),
        "message": "Token is valid and user is authenticated"
    }


@router.get("/status")
async def auth_status(request: Request) -> Dict[str, Any]:
    """
    Get authentication status (works with or without token).
    
    Returns:
        Dict[str, Any]: Authentication status
    """
    current_user = get_optional_user_from_state(request)
    if current_user:
        return {
            "authenticated": True,
            "user_id": current_user.get("sub"),
            "email": current_user.get("email"),
            "role": current_user.get("role", "authenticated"),
        }
    else:
        return {
            "authenticated": False,
            "user_id": None,
            "email": None,
            "role": "anonymous",
        }


@router.post("/refresh")
async def refresh_info():
    """
    Placeholder endpoint for token refresh information.
    
    Note: Token refresh is handled client-side with Supabase.
    This endpoint provides information about the refresh process.
    """
    return {
        "message": "Token refresh is handled client-side with Supabase",
        "instructions": [
            "Use the Supabase client's session.refreshSession() method",
            "Handle refresh automatically with onAuthStateChange",
            "Ensure your client updates the Authorization header with new tokens"
        ],
        "documentation": "https://supabase.com/docs/reference/javascript/auth-refreshsession"
    }


@router.get("/check-email")
async def check_email(email: str = Query(..., min_length=3)) -> Dict[str, Any]:
    """
    Check if an email is registered in Supabase Auth (admin lookup).

    Returns a non-authoritative result suitable for UI hints. Always returns 200.
    """
    try:
        # Import lazily to avoid hard dependency if not used
        from supabase import create_client  # type: ignore
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        # v2 Admin API
        resp = supabase.auth.admin.get_user_by_email(email)
        # resp can be an object or dict depending on library version
        user = getattr(resp, "user", None) if resp is not None else None
        if user is None and isinstance(resp, dict):
            user = resp.get("user")

        registered = user is not None
        confirmed = None
        created_at = None
        last_sign_in_at = None
        if registered:
            confirmed = bool(getattr(user, "email_confirmed_at", None) or (user.get("email_confirmed_at") if isinstance(user, dict) else None))
            created_at = getattr(user, "created_at", None) or (user.get("created_at") if isinstance(user, dict) else None)
            last_sign_in_at = getattr(user, "last_sign_in_at", None) or (user.get("last_sign_in_at") if isinstance(user, dict) else None)
        return {
            "registered": registered,
            "confirmed": confirmed,
            "created_at": created_at,
            "last_sign_in_at": last_sign_in_at,
        }
    except Exception as e:
        logger.error(f"Email check failed: {e}")
        # Do not leak details; return safe default
        return {"registered": False}
