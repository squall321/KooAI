"""
Tests for Multi-Tenancy Models

Tests Tenant, TenantUser, TenantSubscription, TenantInvitation, and TenantAuditLog models.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock
import pytest

# Check for optional dependencies
try:
    from sqlalchemy.orm import declarative_base
    TENANCY_DEPS_AVAILABLE = True
except ImportError:
    TENANCY_DEPS_AVAILABLE = False

# Skip all tests if tenancy dependencies are not available
pytestmark = pytest.mark.skipif(
    not TENANCY_DEPS_AVAILABLE,
    reason="Tenancy dependencies (sqlalchemy) not installed"
)


class TestTenantModel:
    """Test Tenant model"""

    def test_tenant_model_exists(self):
        """Test Tenant model can be imported"""
        from src.infrastructure.tenancy.models import Tenant

        assert Tenant is not None

    def test_tenant_model_attributes(self):
        """Test Tenant model has required attributes"""
        from src.infrastructure.tenancy.models import Tenant

        # Check table name
        assert Tenant.__tablename__ == "tenants"

        # Check attributes exist
        assert hasattr(Tenant, "id")
        assert hasattr(Tenant, "name")
        assert hasattr(Tenant, "slug")
        assert hasattr(Tenant, "domain")
        assert hasattr(Tenant, "is_active")
        assert hasattr(Tenant, "plan")
        assert hasattr(Tenant, "max_users")
        assert hasattr(Tenant, "max_storage_gb")
        assert hasattr(Tenant, "created_at")

    def test_tenant_to_dict(self):
        """Test Tenant to_dict method"""
        from src.infrastructure.tenancy.models import Tenant

        tenant = Tenant(
            id="ten_123",
            name="Acme Corp",
            slug="acme-corp",
            domain="acme.example.com",
            is_active=True,
            plan="professional",
            max_users=50,
            max_storage_gb=1000,
            max_simulations=500,
            created_at=datetime.now(),
        )

        tenant_dict = tenant.to_dict()

        assert tenant_dict["id"] == "ten_123"
        assert tenant_dict["name"] == "Acme Corp"
        assert tenant_dict["slug"] == "acme-corp"
        assert tenant_dict["plan"] == "professional"

    def test_tenant_repr(self):
        """Test Tenant string representation"""
        from src.infrastructure.tenancy.models import Tenant

        tenant = Tenant(id="ten_123", name="Acme Corp", slug="acme-corp")
        repr_str = repr(tenant)

        assert "ten_123" in repr_str
        assert "Acme Corp" in repr_str


class TestTenantUserModel:
    """Test TenantUser model"""

    def test_tenant_user_model_exists(self):
        """Test TenantUser model can be imported"""
        from src.infrastructure.tenancy.models import TenantUser

        assert TenantUser is not None

    def test_tenant_user_attributes(self):
        """Test TenantUser model has required attributes"""
        from src.infrastructure.tenancy.models import TenantUser

        assert TenantUser.__tablename__ == "tenant_users"

        assert hasattr(TenantUser, "id")
        assert hasattr(TenantUser, "tenant_id")
        assert hasattr(TenantUser, "user_id")
        assert hasattr(TenantUser, "role")
        assert hasattr(TenantUser, "is_active")
        assert hasattr(TenantUser, "permissions")
        assert hasattr(TenantUser, "joined_at")

    def test_tenant_user_repr(self):
        """Test TenantUser string representation"""
        from src.infrastructure.tenancy.models import TenantUser

        tenant_user = TenantUser(
            id="tu_123", tenant_id="ten_123", user_id="usr_123", role="member"
        )
        repr_str = repr(tenant_user)

        assert "ten_123" in repr_str
        assert "usr_123" in repr_str


class TestTenantSubscriptionModel:
    """Test TenantSubscription model"""

    def test_subscription_model_exists(self):
        """Test TenantSubscription model can be imported"""
        from src.infrastructure.tenancy.models import TenantSubscription

        assert TenantSubscription is not None

    def test_subscription_attributes(self):
        """Test TenantSubscription model has required attributes"""
        from src.infrastructure.tenancy.models import TenantSubscription

        assert TenantSubscription.__tablename__ == "tenant_subscriptions"

        assert hasattr(TenantSubscription, "id")
        assert hasattr(TenantSubscription, "tenant_id")
        assert hasattr(TenantSubscription, "plan")
        assert hasattr(TenantSubscription, "status")
        assert hasattr(TenantSubscription, "billing_cycle")
        assert hasattr(TenantSubscription, "amount_cents")
        assert hasattr(TenantSubscription, "currency")
        assert hasattr(TenantSubscription, "provider")
        assert hasattr(TenantSubscription, "starts_at")
        assert hasattr(TenantSubscription, "ends_at")

    def test_subscription_repr(self):
        """Test TenantSubscription string representation"""
        from src.infrastructure.tenancy.models import TenantSubscription

        subscription = TenantSubscription(
            id="sub_123", tenant_id="ten_123", plan="professional", status="active"
        )
        repr_str = repr(subscription)

        assert "sub_123" in repr_str
        assert "professional" in repr_str


class TestTenantInvitationModel:
    """Test TenantInvitation model"""

    def test_invitation_model_exists(self):
        """Test TenantInvitation model can be imported"""
        from src.infrastructure.tenancy.models import TenantInvitation

        assert TenantInvitation is not None

    def test_invitation_attributes(self):
        """Test TenantInvitation model has required attributes"""
        from src.infrastructure.tenancy.models import TenantInvitation

        assert TenantInvitation.__tablename__ == "tenant_invitations"

        assert hasattr(TenantInvitation, "id")
        assert hasattr(TenantInvitation, "tenant_id")
        assert hasattr(TenantInvitation, "email")
        assert hasattr(TenantInvitation, "role")
        assert hasattr(TenantInvitation, "invited_by")
        assert hasattr(TenantInvitation, "token")
        assert hasattr(TenantInvitation, "status")
        assert hasattr(TenantInvitation, "expires_at")

    def test_invitation_repr(self):
        """Test TenantInvitation string representation"""
        from src.infrastructure.tenancy.models import TenantInvitation

        invitation = TenantInvitation(
            id="inv_123",
            tenant_id="ten_123",
            email="user@example.com",
            status="pending",
        )
        repr_str = repr(invitation)

        assert "inv_123" in repr_str
        assert "user@example.com" in repr_str


class TestTenantAuditLogModel:
    """Test TenantAuditLog model"""

    def test_audit_log_model_exists(self):
        """Test TenantAuditLog model can be imported"""
        from src.infrastructure.tenancy.models import TenantAuditLog

        assert TenantAuditLog is not None

    def test_audit_log_attributes(self):
        """Test TenantAuditLog model has required attributes"""
        from src.infrastructure.tenancy.models import TenantAuditLog

        assert TenantAuditLog.__tablename__ == "tenant_audit_logs"

        assert hasattr(TenantAuditLog, "id")
        assert hasattr(TenantAuditLog, "tenant_id")
        assert hasattr(TenantAuditLog, "user_id")
        assert hasattr(TenantAuditLog, "action")
        assert hasattr(TenantAuditLog, "resource_type")
        assert hasattr(TenantAuditLog, "resource_id")
        assert hasattr(TenantAuditLog, "ip_address")
        assert hasattr(TenantAuditLog, "extra_data")
        assert hasattr(TenantAuditLog, "created_at")

    def test_audit_log_repr(self):
        """Test TenantAuditLog string representation"""
        from src.infrastructure.tenancy.models import TenantAuditLog

        audit_log = TenantAuditLog(
            id="log_123", tenant_id="ten_123", action="user.created"
        )
        repr_str = repr(audit_log)

        assert "log_123" in repr_str
        assert "user.created" in repr_str


class TestModelRelationships:
    """Test model relationships"""

    def test_tenant_has_users_relationship(self):
        """Test Tenant has users relationship"""
        from src.infrastructure.tenancy.models import Tenant

        assert hasattr(Tenant, "users")

    def test_tenant_has_subscriptions_relationship(self):
        """Test Tenant has subscriptions relationship"""
        from src.infrastructure.tenancy.models import Tenant

        assert hasattr(Tenant, "subscriptions")

    def test_tenant_user_has_tenant_relationship(self):
        """Test TenantUser has tenant relationship"""
        from src.infrastructure.tenancy.models import TenantUser

        assert hasattr(TenantUser, "tenant")

    def test_subscription_has_tenant_relationship(self):
        """Test TenantSubscription has tenant relationship"""
        from src.infrastructure.tenancy.models import TenantSubscription

        assert hasattr(TenantSubscription, "tenant")
