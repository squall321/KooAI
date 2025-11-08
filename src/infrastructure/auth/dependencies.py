"""
Authentication Dependencies for FastAPI

Provides dependency injection for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .service import AuthService, User, UserRole, TokenData

# Security scheme
security = HTTPBearer()


def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    return AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials
        auth_service: Authentication service

    Returns:
        Current user

    Raises:
        HTTPException: If credentials are invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        token_data: TokenData = auth_service.decode_access_token(token)

        # In real application, fetch user from database
        # For now, create user from token data
        user = User(
            user_id=token_data.user_id,
            email=token_data.email,
            username=token_data.email.split("@")[0],
            role=token_data.role,
            is_active=True,
            created_at=None,  # Would come from DB
        )

        return user

    except Exception:
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Current user if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


# Role-based dependencies
async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require admin role.

    Args:
        current_user: Current active user

    Returns:
        Current user if admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_user_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require user or admin role (write access).

    Args:
        current_user: Current active user

    Returns:
        Current user if user or admin

    Raises:
        HTTPException: If user is readonly
    """
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write privileges required",
        )
    return current_user


# Optional authentication (for rate limiting differentiation)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Useful for endpoints that have different rate limits for authenticated users.

    Args:
        credentials: Optional HTTP Authorization credentials
        auth_service: Authentication service

    Returns:
        Current user if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        token_data: TokenData = auth_service.decode_access_token(token)

        user = User(
            user_id=token_data.user_id,
            email=token_data.email,
            username=token_data.email.split("@")[0],
            role=token_data.role,
            is_active=True,
            created_at=None,
        )

        return user if user.is_active else None

    except Exception:
        return None
