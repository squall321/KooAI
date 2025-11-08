# Multi-Tenancy Integration Guide

Complete guide for integrating multi-tenancy support into KooAI.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Setup](#database-setup)
4. [Application Integration](#application-integration)
5. [Testing Multi-Tenancy](#testing-multi-tenancy)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

## Overview

The multi-tenancy system provides:

- **Tenant Isolation**: Complete data separation between tenants at the database level
- **Multiple Identification Strategies**: Support for headers, subdomains, custom domains, paths, and JWT
- **Automatic Query Filtering**: All database queries are automatically scoped to the current tenant
- **User Management**: Invite users, manage roles, and track permissions
- **Audit Logging**: Comprehensive activity tracking for compliance
- **Subscription Management**: Track plans, limits, and billing

## Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                  HTTP Request                        │
└────────────────────┬────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │ TenantMiddleware    │
          │ - Identify tenant   │
          │ - Set context       │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Request Handler    │
          │  (API Routes)       │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │ TenantRepository    │
          │ - Auto-filtering    │
          │ - Access validation │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │     Database        │
          │  (Tenant-scoped)    │
          └─────────────────────┘
```

### Identification Strategies

1. **Header-based**: `X-Tenant-ID: acme-corp`
2. **Subdomain**: `acme.kooai.com`
3. **Custom Domain**: `acme.example.com`
4. **Path-based**: `/tenants/acme-corp/api/v1/...`
5. **JWT Token**: `{ "tenant_id": "ten_abc123" }`

## Database Setup

### Step 1: Run Migration

```bash
# Apply the multi-tenancy migration
alembic upgrade head

# Verify tables were created
psql -U postgres -d kooai -c "\dt tenant*"
```

Expected tables:
- `tenants`
- `tenant_users`
- `tenant_subscriptions`
- `tenant_invitations`
- `tenant_audit_logs`

### Step 2: Add tenant_id to Existing Tables (Optional)

If you want existing resources (simulations, analyses, etc.) to be tenant-scoped:

```sql
-- Example: Add tenant_id to simulations table
ALTER TABLE simulations ADD COLUMN tenant_id VARCHAR(50);
ALTER TABLE simulations ADD CONSTRAINT fk_simulations_tenant_id
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX ix_simulations_tenant_id ON simulations(tenant_id);

-- Repeat for other tables as needed
ALTER TABLE analyses ADD COLUMN tenant_id VARCHAR(50);
ALTER TABLE datasets ADD COLUMN tenant_id VARCHAR(50);
```

### Step 3: Create Initial Tenant (Optional)

```sql
-- Create a default tenant for testing
INSERT INTO tenants (id, name, slug, plan, is_active, created_at, updated_at)
VALUES ('ten_default', 'Default Tenant', 'default', 'free', true, NOW(), NOW());

-- Create owner user for the tenant
INSERT INTO tenant_users (id, tenant_id, user_id, role, is_active, joined_at, updated_at)
VALUES ('tu_default', 'ten_default', 'usr_admin', 'owner', true, NOW(), NOW());
```

## Application Integration

### Step 1: Update main.py

Add tenant middleware and routes to your FastAPI application:

```python
# src/presentation/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import tenant components
from src.infrastructure.tenancy.middleware import (
    TenantMiddleware,
    HeaderStrategy,
    SubdomainStrategy,
    DomainStrategy,
    PathStrategy,
)
from src.presentation.api.routes.tenant_routes import router as tenant_router

# Create FastAPI app
app = FastAPI(title="KooAI API")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware
app.add_middleware(
    TenantMiddleware,
    strategies=[
        HeaderStrategy(),  # X-Tenant-ID header
        SubdomainStrategy(base_domain="kooai.com"),  # subdomain.kooai.com
        PathStrategy(),  # /tenants/{slug}/...
    ],
    require_tenant=False,  # Set to True to require tenant for all requests
    excluded_paths=[
        "/health",
        "/docs",
        "/openapi.json",
        "/api/v1/tenants",  # Allow tenant creation without context
    ],
)

# Include tenant routes
app.include_router(tenant_router, prefix="/api/v1")

# ... rest of your routes
```

### Step 2: Update Models to be Tenant-Scoped

Make your existing models tenant-aware:

```python
# src/domain/models/simulation.py

from sqlalchemy import Column, String, ForeignKey
from src.infrastructure.tenancy.isolation import TenantScoped

class Simulation(Base, TenantScoped):
    __tablename__ = "simulations"

    id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    # ... other fields
```

### Step 3: Use Tenant-Aware Repositories

Update your services to use tenant-scoped queries:

```python
# src/application/services/simulation_service.py

from src.infrastructure.tenancy.isolation import TenantRepository
from src.infrastructure.tenancy.context import get_current_tenant

class SimulationRepository(TenantRepository[Simulation]):
    """Auto-filtered by tenant."""
    pass

class SimulationService:
    def __init__(self, db: Session):
        self.repo = SimulationRepository(db, Simulation)

    def get_all_simulations(self):
        # Automatically filtered by current tenant
        return self.repo.find_all()

    def create_simulation(self, name: str, **kwargs):
        # Automatically sets tenant_id from context
        return self.repo.create(name=name, **kwargs)
```

### Step 4: Protect Routes with Tenant Context

Require tenant context in your API routes:

```python
# src/presentation/api/routes/simulation_routes.py

from fastapi import APIRouter, Depends
from src.infrastructure.tenancy.context import require_tenant, TenantContext

router = APIRouter(prefix="/simulations", tags=["simulations"])

@router.get("/")
async def list_simulations(
    tenant_context: TenantContext = Depends(require_tenant),
    db: Session = Depends(get_db),
):
    """List simulations for current tenant."""
    service = SimulationService(db)
    simulations = service.get_all_simulations()  # Auto-filtered
    return simulations

@router.post("/")
async def create_simulation(
    request: SimulationCreateRequest,
    tenant_context: TenantContext = Depends(require_tenant),
    db: Session = Depends(get_db),
):
    """Create simulation for current tenant."""
    service = SimulationService(db)
    simulation = service.create_simulation(**request.dict())  # Auto-sets tenant_id
    return simulation
```

## Testing Multi-Tenancy

### Manual Testing

#### 1. Create Tenants

```bash
# Create first tenant
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "plan": "professional"
  }'

# Create second tenant
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget Inc",
    "slug": "widget-inc",
    "plan": "enterprise"
  }'
```

#### 2. Test Tenant Isolation

```bash
# Create simulation for Acme Corp (using header)
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: acme-corp" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Simulation 1"
  }'

# Create simulation for Widget Inc
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: widget-inc" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget Simulation 1"
  }'

# List simulations for Acme Corp (should only see Acme's data)
curl -X GET http://localhost:8000/api/v1/simulations \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: acme-corp"

# List simulations for Widget Inc (should only see Widget's data)
curl -X GET http://localhost:8000/api/v1/simulations \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: widget-inc"
```

#### 3. Test Subdomain Strategy

```bash
# Add DNS entries or use /etc/hosts
echo "127.0.0.1 acme.localhost" | sudo tee -a /etc/hosts
echo "127.0.0.1 widget.localhost" | sudo tee -a /etc/hosts

# Access via subdomain
curl http://acme.localhost:8000/api/v1/simulations \
  -H "Authorization: Bearer <token>"

curl http://widget.localhost:8000/api/v1/simulations \
  -H "Authorization: Bearer <token>"
```

### Automated Testing

```python
# tests/integration/test_multi_tenancy.py

import pytest
from fastapi.testclient import TestClient
from src.presentation.api.main import app
from src.infrastructure.tenancy.models import Tenant
from src.infrastructure.tenancy.service import TenantService

class TestMultiTenancy:

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def tenants(self, db):
        """Create two test tenants."""
        service = TenantService(db)

        tenant1 = service.create_tenant(
            name="Tenant 1",
            slug="tenant-1",
            owner_user_id="usr_001",
        )

        tenant2 = service.create_tenant(
            name="Tenant 2",
            slug="tenant-2",
            owner_user_id="usr_002",
        )

        return tenant1, tenant2

    def test_tenant_isolation(self, client, tenants):
        """Test that tenants can't access each other's data."""
        tenant1, tenant2 = tenants

        # Create simulation for tenant1
        response = client.post(
            "/api/v1/simulations",
            headers={"X-Tenant-ID": tenant1.slug},
            json={"name": "Sim 1"},
        )
        assert response.status_code == 201
        sim1_id = response.json()["id"]

        # Try to access from tenant2 (should not see it)
        response = client.get(
            f"/api/v1/simulations/{sim1_id}",
            headers={"X-Tenant-ID": tenant2.slug},
        )
        assert response.status_code == 404

        # Access from tenant1 (should work)
        response = client.get(
            f"/api/v1/simulations/{sim1_id}",
            headers={"X-Tenant-ID": tenant1.slug},
        )
        assert response.status_code == 200

    def test_subdomain_identification(self, client, tenants):
        """Test subdomain-based tenant identification."""
        tenant1, tenant2 = tenants

        # Access via subdomain
        response = client.get(
            "/api/v1/simulations",
            headers={"Host": f"{tenant1.slug}.kooai.com"},
        )
        assert response.status_code == 200
```

## Production Deployment

### Environment Variables

```bash
# .env.production

# Tenant configuration
TENANT_REQUIRE_CONTEXT=true  # Require tenant for all requests
TENANT_BASE_DOMAIN=kooai.com  # Base domain for subdomain strategy
TENANT_EXCLUDED_PATHS=/health,/docs,/metrics  # Paths that don't require tenant

# Database
DATABASE_URL=postgresql://user:pass@localhost/kooai
```

### Nginx Configuration (Subdomain Support)

```nginx
# /etc/nginx/sites-available/kooai

server {
    listen 80;
    server_name *.kooai.com kooai.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Custom Domain Support

For custom domains (e.g., `acme.example.com`):

1. **Update Tenant**: Set the `domain` field

```bash
curl -X PUT http://localhost:8000/api/v1/tenants/ten_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: acme-corp" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "acme.example.com"
  }'
```

2. **DNS Configuration**: Point domain to your server

```
acme.example.com    A    1.2.3.4
```

3. **SSL Certificate**: Generate SSL cert for custom domain

```bash
certbot --nginx -d acme.example.com
```

### Monitoring

Add tenant information to logs:

```python
# src/infrastructure/logging/structured_logger.py

import logging
from src.infrastructure.tenancy.context import get_current_tenant

def get_logger(name: str):
    logger = logging.getLogger(name)

    # Add tenant context to all logs
    class TenantContextFilter(logging.Filter):
        def filter(self, record):
            tenant = get_current_tenant()
            record.tenant_id = tenant.tenant_id if tenant else "none"
            record.tenant_slug = tenant.tenant_slug if tenant else "none"
            return True

    logger.addFilter(TenantContextFilter())
    return logger
```

## Troubleshooting

### Issue: "No tenant context available"

**Cause**: Tenant middleware didn't identify a tenant

**Solutions**:
1. Check that you're passing the tenant identifier (header, subdomain, etc.)
2. Verify the slug/ID exists in the database
3. Check excluded_paths configuration

```python
# Debug: Print tenant context
from src.infrastructure.tenancy.context import get_current_tenant

@app.get("/debug/tenant")
async def debug_tenant():
    tenant = get_current_tenant()
    if tenant:
        return {
            "tenant_id": tenant.tenant_id,
            "tenant_slug": tenant.tenant_slug,
            "user_role": tenant.user_role,
        }
    return {"error": "No tenant context"}
```

### Issue: Cross-tenant data access

**Cause**: Not using tenant-scoped queries

**Solution**: Always use `TenantRepository` or `.for_tenant()` methods

```python
# Bad - not tenant-scoped
simulations = db.query(Simulation).all()  # Shows ALL tenants' data!

# Good - tenant-scoped
simulations = Simulation.for_tenant(db).all()  # Only current tenant

# Better - use repository
repo = SimulationRepository(db, Simulation)
simulations = repo.find_all()  # Auto-filtered
```

### Issue: Migration failures

**Cause**: Tables already exist or foreign key constraints

**Solution**:
1. Check current migration state: `alembic current`
2. Reset if needed: `alembic downgrade base && alembic upgrade head`
3. For existing databases, manually add tenant_id columns before running migration

### Performance Optimization

For large-scale deployments:

1. **Add Composite Indexes**:
```sql
CREATE INDEX idx_simulations_tenant_created ON simulations(tenant_id, created_at DESC);
CREATE INDEX idx_analyses_tenant_status ON analyses(tenant_id, status);
```

2. **Enable Query Caching**:
```python
# Cache tenant lookups
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_tenant_by_slug(slug: str):
    return db.query(Tenant).filter(Tenant.slug == slug).first()
```

3. **Database Connection Pooling**:
```python
# Increase pool size for multi-tenant workload
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)
```

## Security Best Practices

1. **Always validate tenant access** before allowing operations
2. **Log all cross-tenant attempts** for security monitoring
3. **Use row-level security** in PostgreSQL for additional protection
4. **Implement rate limiting per tenant** to prevent abuse
5. **Regular audit log reviews** for compliance

## Next Steps

- [ ] Enable multi-tenancy in main.py
- [ ] Run database migration
- [ ] Update existing models with TenantScoped mixin
- [ ] Test tenant isolation
- [ ] Configure monitoring and alerts
- [ ] Document tenant onboarding process
- [ ] Set up billing integration (Stripe)

## Support

For issues or questions:
- Check logs: `docker-compose logs -f api`
- Review audit logs: `GET /api/v1/tenants/{tenant_id}/audit`
- Open issue: https://github.com/yourusername/kooai/issues
