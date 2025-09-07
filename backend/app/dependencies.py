"""
FastAPI dependencies for common functionality.
Provides clean dependency injection for authentication and other services.
"""

from typing import Dict, Any
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .middleware import get_current_user_from_state, get_current_user_id_from_state
from .db import get_db


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from middleware.
    
    Args:
        request: HTTP request with user state set by middleware
        
    Returns:
        Dict[str, Any]: User information from JWT token
        
    Raises:
        HTTPException: If user is not authenticated
    """
    return get_current_user_from_state(request)


def get_current_user_id(request: Request) -> str:
    """
    Dependency to get current authenticated user ID.
    
    Args:
        request: HTTP request with user state set by middleware
        
    Returns:
        str: User ID (sub claim from JWT)
        
    Raises:
        HTTPException: If user is not authenticated
    """
    return get_current_user_id_from_state(request)


def get_user_with_db(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> tuple[str, AsyncSession]:
    """
    Dependency to get authenticated user ID and database session together.
    
    Args:
        user_id: Current user ID from auth dependency
        db: Database session dependency
        
    Returns:
        tuple[str, AsyncSession]: User ID and database session
    """
    return user_id, db


class AuthenticatedUser:
    """
    Dependency class for authenticated user context.
    Provides clean access to user information and database.
    """
    
    def __init__(self, request: Request, db: AsyncSession = Depends(get_db)):
        self.user = get_current_user_from_state(request)
        self.user_id = self.user.get("sub")
        self.email = self.user.get("email")
        self.role = self.user.get("role", "authenticated")
        self.db = db
    
    def require_role(self, *required_roles: str) -> None:
        """
        Require specific roles for access.
        
        Args:
            *required_roles: Required role names
            
        Raises:
            HTTPException: If user doesn't have required roles
        """
        if required_roles and self.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )


def get_authenticated_user(
    request: Request, 
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedUser:
    """
    Dependency to get authenticated user context with database access.
    
    Args:
        request: HTTP request
        db: Database session
        
    Returns:
        AuthenticatedUser: User context with database access
    """
    return AuthenticatedUser(request, db)
