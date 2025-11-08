"""
Authentication and Authorization Module

Provides JWT-based authentication with refresh tokens and RBAC.
"""

from .service import (
    AuthService,
    User,
    UserInDB,
    UserRole,
    Token,
    TokenData,
    TokenType,
    AuthConfig,
    has_role,
    is_admin,
    can_read,
    can_write,
    can_delete,
)

from .dependencies import (
    get_auth_service,
    get_current_user,
    get_current_active_user,
    get_optional_user,
    require_admin,
    require_user_or_admin,
)

__all__ = [
    # Service
    "AuthService",
    "User",
    "UserInDB",
    "UserRole",
    "Token",
    "TokenData",
    "TokenType",
    "AuthConfig",
    # Helpers
    "has_role",
    "is_admin",
    "can_read",
    "can_write",
    "can_delete",
    # Dependencies
    "get_auth_service",
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_admin",
    "require_user_or_admin",
]
