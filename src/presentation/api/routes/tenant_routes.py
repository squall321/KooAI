"""
Tenant Management API Routes

Endpoints for managing multi-tenant operations.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from src.infrastructure.database.session import get_db
from src.infrastructure.tenancy.service import TenantService
from src.infrastructure.tenancy.models import Tenant, TenantUser, TenantInvitation, TenantAuditLog
from src.infrastructure.tenancy.context import (
    get_current_tenant,
    require_tenant,
    TenantContext,
)
from src.infrastructure.auth.jwt_handler import get_current_user


router = APIRouter(prefix="/tenants", tags=["Tenants"])


# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================


class TenantCreateRequest(BaseModel):
    """Request to create a new tenant."""

    name: str = Field(..., min_length=1, max_length=255, description="Tenant display name")
    slug: str = Field(
        ...,
        min_length=3,
        max_length=255,
        regex=r"^[a-z0-9-]+$",
        description="Unique tenant identifier (lowercase, alphanumeric, hyphens)",
    )
    plan: str = Field(default="free", description="Subscription plan")
    domain: Optional[str] = Field(None, description="Custom domain (optional)")

    @validator("slug")
    def validate_slug(cls, v):
        """Validate slug format."""
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Slug cannot start or end with hyphen")
        if "--" in v:
            raise ValueError("Slug cannot contain consecutive hyphens")
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "plan": "professional",
                "domain": "acme.example.com",
            }
        }


class TenantUpdateRequest(BaseModel):
    """Request to update tenant details."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = None
    plan: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[int] = Field(None, ge=1)
    max_simulations: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corp (Updated)",
                "plan": "enterprise",
                "max_users": 50,
            }
        }


class TenantResponse(BaseModel):
    """Tenant details response."""

    id: str
    name: str
    slug: str
    domain: Optional[str]
    plan: str
    is_active: bool
    max_users: int
    max_storage_gb: int
    max_simulations: int
    current_users: Optional[int] = None
    current_storage_gb: Optional[float] = None
    current_simulations: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "ten_abc123",
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "domain": "acme.example.com",
                "plan": "professional",
                "is_active": True,
                "max_users": 20,
                "max_storage_gb": 100,
                "max_simulations": 1000,
                "current_users": 5,
                "current_storage_gb": 12.5,
                "current_simulations": 45,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T15:45:00Z",
            }
        }


class InviteUserRequest(BaseModel):
    """Request to invite a user to a tenant."""

    email: str = Field(..., description="User email address")
    role: str = Field(default="member", description="Role to assign")
    expires_in_days: int = Field(default=7, ge=1, le=30, description="Invitation expiration")

    class Config:
        schema_extra = {
            "example": {"email": "user@example.com", "role": "admin", "expires_in_days": 7}
        }


class InvitationResponse(BaseModel):
    """Invitation details response."""

    id: str
    tenant_id: str
    email: str
    role: str
    token: str
    status: str
    invited_by: str
    expires_at: datetime
    created_at: datetime

    class Config:
        orm_mode = True


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""

    token: str = Field(..., description="Invitation token")


class TenantUserResponse(BaseModel):
    """Tenant user details."""

    id: str
    tenant_id: str
    user_id: str
    role: str
    permissions: List[str]
    is_active: bool
    invited_by: Optional[str]
    invited_at: Optional[datetime]
    joined_at: datetime

    class Config:
        orm_mode = True


class AuditLogResponse(BaseModel):
    """Audit log entry."""

    id: str
    tenant_id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    metadata: dict
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


# ============================================================================
# Dependencies
# ============================================================================


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    """Get tenant service instance."""
    return TenantService(db)


def require_tenant_admin(
    tenant_context: TenantContext = Depends(require_tenant),
) -> TenantContext:
    """Require user to be tenant admin."""
    if not tenant_context.is_admin() and not tenant_context.is_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner privileges required",
        )
    return tenant_context


def require_tenant_owner(
    tenant_context: TenantContext = Depends(require_tenant),
) -> TenantContext:
    """Require user to be tenant owner."""
    if not tenant_context.is_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Owner privileges required"
        )
    return tenant_context


# ============================================================================
# Tenant CRUD Endpoints
# ============================================================================


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: TenantCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
):
    """
    Create a new tenant.

    The current user will be assigned as the tenant owner.

    **Required permissions**: Authenticated user

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/tenants" \\
      -H "Authorization: Bearer <token>" \\
      -H "Content-Type: application/json" \\
      -d '{
        "name": "Acme Corp",
        "slug": "acme-corp",
        "plan": "professional"
      }'
    ```
    """
    # Check if slug already exists
    existing = service.get_tenant_by_slug(request.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{request.slug}' already exists",
        )

    # Check if domain already exists
    if request.domain:
        existing_domain = (
            service.db.query(Tenant).filter(Tenant.domain == request.domain).first()
        )
        if existing_domain:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Domain '{request.domain}' is already in use",
            )

    # Create tenant
    tenant = service.create_tenant(
        name=request.name,
        slug=request.slug,
        owner_user_id=current_user["user_id"],
        plan=request.plan,
        domain=request.domain,
    )

    # Log activity
    service.log_activity(
        tenant_id=tenant.id,
        action="tenant.created",
        user_id=current_user["user_id"],
        resource_type="tenant",
        resource_id=tenant.id,
        metadata={"plan": request.plan, "slug": request.slug},
    )

    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant),
):
    """
    Get tenant details.

    **Required permissions**: Tenant member

    **Example**:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/tenants/ten_abc123" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp"
    ```
    """
    # Verify user has access to this tenant
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other tenant's details",
        )

    tenant = service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    return tenant


@router.get("/", response_model=List[TenantResponse])
async def list_my_tenants(
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
):
    """
    List all tenants the current user belongs to.

    **Required permissions**: Authenticated user

    **Example**:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/tenants" \\
      -H "Authorization: Bearer <token>"
    ```
    """
    # Get all tenant memberships for this user
    tenant_users = (
        service.db.query(TenantUser)
        .filter(TenantUser.user_id == current_user["user_id"])
        .filter(TenantUser.is_active == True)
        .all()
    )

    tenant_ids = [tu.tenant_id for tu in tenant_users]

    if not tenant_ids:
        return []

    tenants = service.db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()

    return tenants


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    request: TenantUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant_admin),
):
    """
    Update tenant details.

    **Required permissions**: Tenant admin or owner

    **Example**:
    ```bash
    curl -X PUT "http://localhost:8000/api/v1/tenants/ten_abc123" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp" \\
      -H "Content-Type: application/json" \\
      -d '{
        "name": "Acme Corporation (Updated)",
        "max_users": 50
      }'
    ```
    """
    # Verify access
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update other tenant"
        )

    # Update only provided fields
    update_data = request.dict(exclude_unset=True)

    tenant = service.update_tenant(tenant_id, **update_data)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    # Log activity
    service.log_activity(
        tenant_id=tenant_id,
        action="tenant.updated",
        user_id=current_user["user_id"],
        resource_type="tenant",
        resource_id=tenant_id,
        metadata=update_data,
    )

    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant_owner),
):
    """
    Delete a tenant and all associated data.

    **Required permissions**: Tenant owner only

    **Warning**: This action is irreversible and will delete all tenant data.

    **Example**:
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/tenants/ten_abc123" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp"
    ```
    """
    # Verify access
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete other tenant"
        )

    success = service.delete_tenant(tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    # Note: Activity log is automatically deleted via cascade
    return None


# ============================================================================
# User Invitation Endpoints
# ============================================================================


@router.post("/{tenant_id}/invitations", response_model=InvitationResponse)
async def invite_user(
    tenant_id: str,
    request: InviteUserRequest,
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant_admin),
):
    """
    Invite a user to join the tenant.

    **Required permissions**: Tenant admin or owner

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/tenants/ten_abc123/invitations" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp" \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "newuser@example.com",
        "role": "member",
        "expires_in_days": 7
      }'
    ```
    """
    # Verify access
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot invite to other tenant"
        )

    # Check if user is already a member
    existing = (
        service.db.query(TenantUser)
        .join(Tenant)
        .filter(TenantUser.tenant_id == tenant_id)
        .filter(TenantUser.email == request.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this tenant",
        )

    invitation = service.invite_user(
        tenant_id=tenant_id,
        email=request.email,
        role=request.role,
        invited_by_user_id=current_user["user_id"],
        expires_in_days=request.expires_in_days,
    )

    # Log activity
    service.log_activity(
        tenant_id=tenant_id,
        action="user.invited",
        user_id=current_user["user_id"],
        resource_type="invitation",
        resource_id=invitation.id,
        metadata={"email": request.email, "role": request.role},
    )

    return invitation


@router.post("/invitations/accept", response_model=dict)
async def accept_invitation(
    request: AcceptInvitationRequest,
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
):
    """
    Accept a tenant invitation.

    **Required permissions**: Authenticated user

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/tenants/invitations/accept" \\
      -H "Authorization: Bearer <token>" \\
      -H "Content-Type: application/json" \\
      -d '{
        "token": "invitation_token_here"
      }'
    ```
    """
    success = service.accept_invitation(request.token, current_user["user_id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token",
        )

    return {"message": "Invitation accepted successfully"}


@router.get("/{tenant_id}/invitations", response_model=List[InvitationResponse])
async def list_invitations(
    tenant_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant_admin),
):
    """
    List tenant invitations.

    **Required permissions**: Tenant admin or owner

    **Example**:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/tenants/ten_abc123/invitations?status=pending" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp"
    ```
    """
    # Verify access
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other tenant's invitations",
        )

    query = service.db.query(TenantInvitation).filter(
        TenantInvitation.tenant_id == tenant_id
    )

    if status_filter:
        query = query.filter(TenantInvitation.status == status_filter)

    invitations = query.order_by(TenantInvitation.created_at.desc()).all()

    return invitations


# ============================================================================
# Tenant Users Endpoints
# ============================================================================


@router.get("/{tenant_id}/users", response_model=List[TenantUserResponse])
async def list_tenant_users(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant),
):
    """
    List all users in the tenant.

    **Required permissions**: Tenant member

    **Example**:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/tenants/ten_abc123/users" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp"
    ```
    """
    # Verify access
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other tenant's users"
        )

    users = (
        service.db.query(TenantUser)
        .filter(TenantUser.tenant_id == tenant_id)
        .filter(TenantUser.is_active == True)
        .order_by(TenantUser.joined_at.desc())
        .all()
    )

    return users


@router.delete("/{tenant_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_tenant(
    tenant_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant_admin),
):
    """
    Remove a user from the tenant.

    **Required permissions**: Tenant admin or owner

    **Example**:
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/tenants/ten_abc123/users/usr_xyz789" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp"
    ```
    """
    # Verify access
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify other tenant"
        )

    # Cannot remove self
    if user_id == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from tenant",
        )

    # Find user
    tenant_user = (
        service.db.query(TenantUser)
        .filter(TenantUser.tenant_id == tenant_id)
        .filter(TenantUser.user_id == user_id)
        .first()
    )

    if not tenant_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found in tenant"
        )

    # Cannot remove owner
    if tenant_user.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove tenant owner",
        )

    # Soft delete
    tenant_user.is_active = False
    service.db.commit()

    # Log activity
    service.log_activity(
        tenant_id=tenant_id,
        action="user.removed",
        user_id=current_user["user_id"],
        resource_type="tenant_user",
        resource_id=tenant_user.id,
        metadata={"removed_user_id": user_id},
    )

    return None


# ============================================================================
# Audit Log Endpoints
# ============================================================================


@router.get("/{tenant_id}/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    tenant_id: str,
    action_filter: Optional[str] = Query(None, description="Filter by action"),
    user_id_filter: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: TenantService = Depends(get_tenant_service),
    tenant_context: TenantContext = Depends(require_tenant_admin),
):
    """
    Get tenant audit logs.

    **Required permissions**: Tenant admin or owner

    **Example**:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/tenants/ten_abc123/audit?limit=50&action=user.invited" \\
      -H "Authorization: Bearer <token>" \\
      -H "X-Tenant-ID: acme-corp"
    ```
    """
    # Verify access
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other tenant's logs"
        )

    query = service.db.query(TenantAuditLog).filter(TenantAuditLog.tenant_id == tenant_id)

    if action_filter:
        query = query.filter(TenantAuditLog.action == action_filter)

    if user_id_filter:
        query = query.filter(TenantAuditLog.user_id == user_id_filter)

    logs = (
        query.order_by(TenantAuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return logs
