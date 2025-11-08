"""
Multi-Tenancy Models

Database models for multi-tenant support.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Tenant(Base):
    """
    Tenant model.

    Represents an organization/tenant in the system.
    """

    __tablename__ = "tenants"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_trial = Column(Boolean, default=False, nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)

    # Plan and limits
    plan = Column(String(50), default="free", nullable=False)
    max_users = Column(Integer, default=5, nullable=False)
    max_storage_gb = Column(Integer, default=10, nullable=False)
    max_simulations = Column(Integer, default=100, nullable=False)

    # Settings
    settings = Column(JSON, default=dict, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    subscriptions = relationship("TenantSubscription", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation."""
        return f"<Tenant(id={self.id}, name={self.name}, slug={self.slug})>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "domain": self.domain,
            "is_active": self.is_active,
            "is_trial": self.is_trial,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "plan": self.plan,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "max_simulations": self.max_simulations,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TenantUser(Base):
    """
    Tenant-User association.

    Links users to tenants with roles.
    """

    __tablename__ = "tenant_users"

    id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)

    # Role within tenant
    role = Column(String(50), default="member", nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    invited_by = Column(String(50), nullable=True)
    invited_at = Column(DateTime, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Permissions
    permissions = Column(JSON, default=list, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        """String representation."""
        return f"<TenantUser(tenant_id={self.tenant_id}, user_id={self.user_id}, role={self.role})>"


class TenantSubscription(Base):
    """
    Tenant subscription.

    Tracks billing and subscription status.
    """

    __tablename__ = "tenant_subscriptions"

    id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Subscription details
    plan = Column(String(50), nullable=False)
    status = Column(String(50), default="active", nullable=False)

    # Billing
    billing_cycle = Column(String(20), default="monthly", nullable=False)
    amount_cents = Column(Integer, default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Payment provider
    provider = Column(String(50), nullable=True)  # stripe, paypal, etc.
    provider_subscription_id = Column(String(255), nullable=True, unique=True, index=True)

    # Dates
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="subscriptions")

    def __repr__(self):
        """String representation."""
        return f"<TenantSubscription(id={self.id}, tenant_id={self.tenant_id}, plan={self.plan}, status={self.status})>"


class TenantInvitation(Base):
    """
    Tenant invitation.

    Manages invitations to join a tenant.
    """

    __tablename__ = "tenant_invitations"

    id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), default="member", nullable=False)
    invited_by = Column(String(50), nullable=False)

    # Token
    token = Column(String(255), unique=True, nullable=False, index=True)

    # Status
    status = Column(String(50), default="pending", nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """String representation."""
        return f"<TenantInvitation(id={self.id}, tenant_id={self.tenant_id}, email={self.email}, status={self.status})>"


class TenantAuditLog(Base):
    """
    Tenant audit log.

    Tracks all tenant-level activities.
    """

    __tablename__ = "tenant_audit_logs"

    id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Activity details
    user_id = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(50), nullable=True, index=True)

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    metadata = Column(JSON, default=dict, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        """String representation."""
        return f"<TenantAuditLog(id={self.id}, tenant_id={self.tenant_id}, action={self.action})>"
