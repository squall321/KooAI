"""
Tenant Isolation Middleware

Automatically identifies and sets tenant context for each request.
"""

import re
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.infrastructure.tenancy.context import (
    TenantContext,
    set_current_tenant,
    clear_current_tenant,
)


class TenantIdentificationStrategy:
    """Base class for tenant identification strategies."""

    async def identify(self, request: Request) -> Optional[str]:
        """
        Identify tenant from request.

        Args:
            request: HTTP request

        Returns:
            Tenant ID or None
        """
        raise NotImplementedError


class HeaderStrategy(TenantIdentificationStrategy):
    """
    Identify tenant from HTTP header.

    Example:
        X-Tenant-ID: ten_123
    """

    def __init__(self, header_name: str = "X-Tenant-ID"):
        """
        Initialize header strategy.

        Args:
            header_name: Header name to check
        """
        self.header_name = header_name

    async def identify(self, request: Request) -> Optional[str]:
        """Identify tenant from header."""
        return request.headers.get(self.header_name)


class SubdomainStrategy(TenantIdentificationStrategy):
    """
    Identify tenant from subdomain.

    Example:
        acme.kooai.com -> tenant slug: "acme"
    """

    def __init__(self, base_domain: str = "kooai.com"):
        """
        Initialize subdomain strategy.

        Args:
            base_domain: Base domain to extract subdomain from
        """
        self.base_domain = base_domain

    async def identify(self, request: Request) -> Optional[str]:
        """Identify tenant from subdomain."""
        host = request.headers.get("host", "")

        # Remove port if present
        host = host.split(":")[0]

        # Extract subdomain
        if host.endswith(f".{self.base_domain}"):
            subdomain = host.replace(f".{self.base_domain}", "")
            return subdomain

        return None


class DomainStrategy(TenantIdentificationStrategy):
    """
    Identify tenant from custom domain.

    Example:
        acme.com -> lookup tenant by domain
    """

    def __init__(self, db_lookup: Callable):
        """
        Initialize domain strategy.

        Args:
            db_lookup: Function to lookup tenant by domain
        """
        self.db_lookup = db_lookup

    async def identify(self, request: Request) -> Optional[str]:
        """Identify tenant from custom domain."""
        host = request.headers.get("host", "")
        host = host.split(":")[0]

        # Lookup tenant by domain
        tenant = await self.db_lookup(domain=host)
        if tenant:
            return tenant.slug

        return None


class PathStrategy(TenantIdentificationStrategy):
    """
    Identify tenant from URL path.

    Example:
        /tenants/acme-corp/... -> tenant slug: "acme-corp"
    """

    def __init__(self, pattern: str = r"^/tenants/([^/]+)"):
        """
        Initialize path strategy.

        Args:
            pattern: Regex pattern to extract tenant from path
        """
        self.pattern = re.compile(pattern)

    async def identify(self, request: Request) -> Optional[str]:
        """Identify tenant from path."""
        path = request.url.path
        match = self.pattern.match(path)

        if match:
            return match.group(1)

        return None


class JWTStrategy(TenantIdentificationStrategy):
    """
    Identify tenant from JWT token claims.

    Example:
        JWT payload: {"tenant_id": "ten_123"}
    """

    def __init__(self, claim_name: str = "tenant_id"):
        """
        Initialize JWT strategy.

        Args:
            claim_name: JWT claim name containing tenant ID
        """
        self.claim_name = claim_name

    async def identify(self, request: Request) -> Optional[str]:
        """Identify tenant from JWT."""
        # Get JWT from authorization header
        auth_header = request.headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")

        # Decode JWT (simplified - use proper JWT library in production)
        try:
            import jwt

            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get(self.claim_name)
        except Exception:
            return None


class MultiStrategyResolver:
    """
    Try multiple strategies in order.

    Falls back to next strategy if current one returns None.
    """

    def __init__(self, strategies: list[TenantIdentificationStrategy]):
        """
        Initialize multi-strategy resolver.

        Args:
            strategies: List of strategies to try in order
        """
        self.strategies = strategies

    async def identify(self, request: Request) -> Optional[str]:
        """Try strategies in order."""
        for strategy in self.strategies:
            tenant_identifier = await strategy.identify(request)
            if tenant_identifier:
                return tenant_identifier

        return None


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Tenant isolation middleware.

    Automatically identifies tenant and sets context for each request.
    """

    def __init__(
        self,
        app: ASGIApp,
        strategies: Optional[list[TenantIdentificationStrategy]] = None,
        require_tenant: bool = False,
        excluded_paths: Optional[list[str]] = None,
    ):
        """
        Initialize tenant middleware.

        Args:
            app: ASGI application
            strategies: Tenant identification strategies
            require_tenant: Require tenant for all requests
            excluded_paths: Paths that don't require tenant

        Example:
            ```python
            app.add_middleware(
                TenantMiddleware,
                strategies=[
                    HeaderStrategy(),
                    SubdomainStrategy(base_domain="kooai.com"),
                    PathStrategy(),
                ],
                require_tenant=True,
                excluded_paths=["/health", "/docs", "/openapi.json"]
            )
            ```
        """
        super().__init__(app)

        if strategies is None:
            # Default strategies
            strategies = [
                HeaderStrategy(),
                PathStrategy(),
            ]

        self.resolver = MultiStrategyResolver(strategies)
        self.require_tenant = require_tenant
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
        ]

    def is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from tenant requirement."""
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return True
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with tenant context.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response

        Raises:
            HTTPException: If tenant required but not found
        """
        # Clear any existing tenant context
        clear_current_tenant()

        # Skip tenant resolution for excluded paths
        if self.is_excluded_path(request.url.path):
            response = await call_next(request)
            return response

        # Identify tenant
        tenant_identifier = await self.resolver.identify(request)

        if not tenant_identifier and self.require_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant identification required",
            )

        if tenant_identifier:
            # Load tenant from database (simplified - use actual DB in production)
            tenant_context = await self.load_tenant_context(
                tenant_identifier, request
            )

            if not tenant_context:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant '{tenant_identifier}' not found",
                )

            # Set tenant context
            set_current_tenant(tenant_context)

            # Add tenant info to request state
            request.state.tenant = tenant_context

        try:
            # Process request
            response = await call_next(request)

            # Add tenant header to response
            if tenant_identifier:
                response.headers["X-Tenant-ID"] = tenant_context.tenant_id

            return response

        finally:
            # Clear tenant context
            clear_current_tenant()

    async def load_tenant_context(
        self, identifier: str, request: Request
    ) -> Optional[TenantContext]:
        """
        Load tenant context from database.

        Args:
            identifier: Tenant identifier (ID or slug)
            request: HTTP request

        Returns:
            Tenant context or None
        """
        # Simplified - use actual database query in production
        # This would lookup tenant from database by ID or slug

        # Extract user info from JWT if available
        user_id = None
        user_role = None
        permissions = []

        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                import jwt

                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
                user_role = payload.get("role")
                permissions = payload.get("permissions", [])
            except Exception:
                pass

        # Create context (in production, load from database)
        context = TenantContext(
            tenant_id=f"ten_{identifier}",
            tenant_slug=identifier,
            tenant_name=f"Tenant {identifier}",
            user_id=user_id,
            user_role=user_role or "member",
            permissions=permissions,
        )

        return context
