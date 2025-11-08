"""
Tenant Management Service

Business logic for tenant operations.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import secrets

from src.infrastructure.tenancy.models import (
    Tenant,
    TenantUser,
    TenantSubscription,
    TenantInvitation,
    TenantAuditLog,
)
from src.infrastructure.tenancy.context import get_current_tenant


class TenantService:
    """Tenant management service."""

    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db

    def create_tenant(
        self,
        name: str,
        slug: str,
        owner_user_id: str,
        plan: str = "free",
        domain: Optional[str] = None,
    ) -> Tenant:
        """
        Create new tenant.

        Args:
            name: Tenant name
            slug: Tenant slug (unique)
            owner_user_id: Owner user ID
            plan: Subscription plan
            domain: Custom domain

        Returns:
            Created tenant

        Example:
            ```python
            tenant = service.create_tenant(
                name="Acme Corp",
                slug="acme-corp",
                owner_user_id="usr_123",
                plan="professional"
            )
            ```
        """
        # Create tenant
        tenant = Tenant(
            id=f"ten_{secrets.token_urlsafe(8)}",
            name=name,
            slug=slug,
            domain=domain,
            plan=plan,
            is_active=True,
        )

        self.db.add(tenant)
        self.db.flush()

        # Add owner as first user
        tenant_user = TenantUser(
            id=f"tu_{secrets.token_urlsafe(8)}",
            tenant_id=tenant.id,
            user_id=owner_user_id,
            role="owner",
            is_active=True,
        )

        self.db.add(tenant_user)

        # Create initial subscription
        subscription = TenantSubscription(
            id=f"sub_{secrets.token_urlsafe(8)}",
            tenant_id=tenant.id,
            plan=plan,
            status="active",
            billing_cycle="monthly",
            starts_at=datetime.utcnow(),
        )

        self.db.add(subscription)
        self.db.commit()

        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        return self.db.query(Tenant).filter(Tenant.slug == slug).first()

    def update_tenant(self, tenant_id: str, **kwargs) -> Optional[Tenant]:
        """Update tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        tenant.updated_at = datetime.utcnow()
        self.db.commit()

        return tenant

    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant and all associated data."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        self.db.delete(tenant)
        self.db.commit()

        return True

    def invite_user(
        self,
        tenant_id: str,
        email: str,
        role: str,
        invited_by_user_id: str,
        expires_in_days: int = 7,
    ) -> TenantInvitation:
        """
        Invite user to tenant.

        Args:
            tenant_id: Tenant ID
            email: User email
            role: Role to assign
            invited_by_user_id: Inviting user ID
            expires_in_days: Expiration days

        Returns:
            Created invitation
        """
        invitation = TenantInvitation(
            id=f"inv_{secrets.token_urlsafe(8)}",
            tenant_id=tenant_id,
            email=email,
            role=role,
            invited_by=invited_by_user_id,
            token=secrets.token_urlsafe(32),
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        )

        self.db.add(invitation)
        self.db.commit()

        return invitation

    def accept_invitation(self, token: str, user_id: str) -> bool:
        """
        Accept tenant invitation.

        Args:
            token: Invitation token
            user_id: User ID accepting

        Returns:
            True if accepted
        """
        invitation = (
            self.db.query(TenantInvitation)
            .filter(
                TenantInvitation.token == token, TenantInvitation.status == "pending"
            )
            .first()
        )

        if not invitation:
            return False

        if invitation.expires_at < datetime.utcnow():
            return False

        # Create tenant user
        tenant_user = TenantUser(
            id=f"tu_{secrets.token_urlsafe(8)}",
            tenant_id=invitation.tenant_id,
            user_id=user_id,
            role=invitation.role,
            is_active=True,
            invited_by=invitation.invited_by,
            invited_at=invitation.created_at,
        )

        self.db.add(tenant_user)

        # Update invitation
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()

        self.db.commit()

        return True

    def log_activity(
        self,
        tenant_id: str,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """
        Log tenant activity.

        Args:
            tenant_id: Tenant ID
            action: Action performed
            user_id: User ID
            resource_type: Resource type
            resource_id: Resource ID
            metadata: Additional metadata
        """
        log = TenantAuditLog(
            id=f"log_{secrets.token_urlsafe(8)}",
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
        )

        self.db.add(log)
        self.db.commit()
