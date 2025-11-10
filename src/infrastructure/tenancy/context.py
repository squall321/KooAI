"""
Tenant Context Management

Manages current tenant context throughout request lifecycle.
"""

from contextvars import ContextVar
from typing import Any, Callable, Optional
from dataclasses import dataclass

# Context variable for current tenant
_current_tenant: ContextVar[Optional["TenantContext"]] = ContextVar(
    "current_tenant", default=None
)


@dataclass
class TenantContext:
    """
    Tenant context holder.

    Contains current tenant information for the request.
    """

    tenant_id: str
    tenant_slug: str
    tenant_name: str
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    permissions: Optional[list] = None

    def has_permission(self, permission: str) -> bool:
        """
        Check if current user has permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission

        Example:
            ```python
            context = get_current_tenant()
            if context.has_permission("simulations.delete"):
                # Allow deletion
                pass
            ```
        """
        if not self.permissions:
            return False
        return permission in self.permissions

    def is_admin(self) -> bool:
        """Check if current user is tenant admin."""
        return self.user_role == "admin"

    def is_owner(self) -> bool:
        """Check if current user is tenant owner."""
        return self.user_role == "owner"

    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.user_role in ("owner", "admin")


def set_current_tenant(context: Optional[TenantContext]) -> None:
    """
    Set current tenant context.

    Args:
        context: Tenant context to set

    Example:
        ```python
        context = TenantContext(
            tenant_id="ten_123",
            tenant_slug="acme-corp",
            tenant_name="Acme Corp",
            user_id="usr_456",
            user_role="admin"
        )
        set_current_tenant(context)
        ```
    """
    _current_tenant.set(context)


def get_current_tenant() -> Optional[TenantContext]:
    """
    Get current tenant context.

    Returns:
        Current tenant context or None

    Example:
        ```python
        context = get_current_tenant()
        if context:
            print(f"Current tenant: {context.tenant_name}")
        ```
    """
    return _current_tenant.get()


def clear_current_tenant() -> None:
    """
    Clear current tenant context.

    Example:
        ```python
        # After request processing
        clear_current_tenant()
        ```
    """
    _current_tenant.set(None)


def require_tenant() -> TenantContext:
    """
    Get current tenant or raise error.

    Returns:
        Current tenant context

    Raises:
        ValueError: If no tenant context is set

    Example:
        ```python
        try:
            context = require_tenant()
            # Use context
        except ValueError:
            # Handle missing tenant context
            pass
        ```
    """
    context = get_current_tenant()
    if context is None:
        raise ValueError("No tenant context available")
    return context


class TenantContextManager:
    """
    Context manager for tenant context.

    Ensures tenant context is properly set and cleared.
    """

    def __init__(self, context: TenantContext):
        """
        Initialize context manager.

        Args:
            context: Tenant context to set
        """
        self.context = context
        self.previous_context: Optional[TenantContext] = None

    def __enter__(self) -> TenantContext:
        """Enter context."""
        self.previous_context = get_current_tenant()
        set_current_tenant(self.context)
        return self.context

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context."""
        set_current_tenant(self.previous_context)


def with_tenant(context: TenantContext) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to execute function with tenant context.

    Args:
        context: Tenant context

    Example:
        ```python
        @with_tenant(TenantContext(tenant_id="ten_123", ...))
        def my_function():
            # Function runs with tenant context
            pass
        ```
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with TenantContextManager(context):
                return await func(*args, **kwargs)

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with TenantContextManager(context):
                return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
