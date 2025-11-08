"""
Multi-Tenancy Infrastructure

Provides comprehensive multi-tenant support with:
- Tenant isolation at database level
- Multiple identification strategies (header, subdomain, domain, path, JWT)
- Automatic query filtering
- Tenant context management
- User invitation system
- Audit logging

Usage:
    # 1. Add middleware to FastAPI app
    from src.infrastructure.tenancy.middleware import TenantMiddleware
    from src.infrastructure.tenancy.middleware import (
        HeaderStrategy,
        SubdomainStrategy,
    )

    app.add_middleware(
        TenantMiddleware,
        strategies=[
            HeaderStrategy(),
            SubdomainStrategy(base_domain="kooai.com"),
        ],
        require_tenant=False,
        excluded_paths=["/health", "/docs"],
    )

    # 2. Include tenant routes
    from src.presentation.api.routes.tenant_routes import router as tenant_router
    app.include_router(tenant_router, prefix="/api/v1")

    # 3. Use tenant context in your code
    from src.infrastructure.tenancy.context import get_current_tenant, require_tenant

    @app.get("/my-endpoint")
    async def my_endpoint():
        tenant = get_current_tenant()
        if tenant:
            print(f"Current tenant: {tenant.tenant_id}")

    # 4. Use tenant-scoped models
    from src.infrastructure.tenancy.isolation import TenantScoped

    class Simulation(Base, TenantScoped):
        __tablename__ = "simulations"
        # ... fields

    # Auto-filtered queries
    simulations = Simulation.for_tenant(db).all()

    # 5. Use repository pattern
    from src.infrastructure.tenancy.isolation import TenantRepository

    class SimulationRepository(TenantRepository[Simulation]):
        pass

    repo = SimulationRepository(db, Simulation)
    simulations = repo.find_all()  # Auto-filtered by tenant

Examples:
    # Header-based identification
    curl -H "X-Tenant-ID: acme-corp" http://localhost:8000/api/v1/simulations

    # Subdomain-based identification
    curl http://acme.kooai.com/api/v1/simulations

    # Custom domain
    curl http://acme.example.com/api/v1/simulations

    # Path-based identification
    curl http://localhost:8000/tenants/acme-corp/api/v1/simulations
"""

from .models import (
    Tenant,
    TenantUser,
    TenantSubscription,
    TenantInvitation,
    TenantAuditLog,
)

from .context import (
    TenantContext,
    get_current_tenant,
    set_current_tenant,
    require_tenant,
    clear_current_tenant,
    TenantContextManager,
    with_tenant,
)

from .middleware import (
    TenantIdentificationStrategy,
    HeaderStrategy,
    SubdomainStrategy,
    DomainStrategy,
    PathStrategy,
    JWTStrategy,
    MultiStrategyResolver,
    TenantMiddleware,
)

from .isolation import (
    TenantIsolatedQuery,
    TenantScoped,
    enable_tenant_isolation,
    check_tenant_access,
    TenantRepository,
)

from .service import TenantService

__all__ = [
    # Models
    "Tenant",
    "TenantUser",
    "TenantSubscription",
    "TenantInvitation",
    "TenantAuditLog",
    # Context
    "TenantContext",
    "get_current_tenant",
    "set_current_tenant",
    "require_tenant",
    "clear_current_tenant",
    "TenantContextManager",
    "with_tenant",
    # Middleware
    "TenantIdentificationStrategy",
    "HeaderStrategy",
    "SubdomainStrategy",
    "DomainStrategy",
    "PathStrategy",
    "JWTStrategy",
    "MultiStrategyResolver",
    "TenantMiddleware",
    # Isolation
    "TenantIsolatedQuery",
    "TenantScoped",
    "enable_tenant_isolation",
    "check_tenant_access",
    "TenantRepository",
    # Service
    "TenantService",
]
