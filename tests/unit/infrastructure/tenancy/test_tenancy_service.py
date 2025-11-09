"""
Tests for Tenant Management Service

Tests TenantService business logic.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import pytest

# Check for optional dependencies
try:
    from sqlalchemy.orm import Session
    TENANCY_DEPS_AVAILABLE = True
except ImportError:
    TENANCY_DEPS_AVAILABLE = False

# Skip all tests if tenancy dependencies are not available
pytestmark = pytest.mark.skipif(
    not TENANCY_DEPS_AVAILABLE,
    reason="Tenancy dependencies (sqlalchemy) not installed"
)


class TestTenantService:
    """Test TenantService class"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.flush = Mock()
        db.delete = Mock()
        return db

    @pytest.fixture
    def tenant_service(self, mock_db):
        """Create TenantService instance"""
        from src.infrastructure.tenancy.service import TenantService

        return TenantService(mock_db)

    def test_tenant_service_creation(self, mock_db):
        """Test TenantService can be created"""
        from src.infrastructure.tenancy.service import TenantService

        service = TenantService(mock_db)
        assert service is not None
        assert service.db == mock_db

    def test_create_tenant_basic(self, tenant_service, mock_db):
        """Test creating a basic tenant"""
        tenant = tenant_service.create_tenant(
            name="Acme Corp", slug="acme-corp", owner_user_id="usr_123"
        )

        # Verify tenant was created
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_create_tenant_with_plan(self, tenant_service, mock_db):
        """Test creating tenant with specific plan"""
        tenant = tenant_service.create_tenant(
            name="Acme Corp",
            slug="acme-corp",
            owner_user_id="usr_123",
            plan="professional",
        )

        # Verify plan was set
        assert mock_db.add.called

    def test_create_tenant_with_domain(self, tenant_service, mock_db):
        """Test creating tenant with custom domain"""
        tenant = tenant_service.create_tenant(
            name="Acme Corp",
            slug="acme-corp",
            owner_user_id="usr_123",
            domain="acme.example.com",
        )

        assert mock_db.add.called

    def test_get_tenant_by_id(self, tenant_service, mock_db):
        """Test getting tenant by ID"""
        from src.infrastructure.tenancy.models import Tenant

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_result = Mock(spec=Tenant)

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_result

        result = tenant_service.get_tenant("ten_123")

        mock_db.query.assert_called_once()
        assert result == mock_result

    def test_get_tenant_by_slug(self, tenant_service, mock_db):
        """Test getting tenant by slug"""
        from src.infrastructure.tenancy.models import Tenant

        mock_query = Mock()
        mock_filter = Mock()
        mock_result = Mock(spec=Tenant)

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_result

        result = tenant_service.get_tenant_by_slug("acme-corp")

        mock_db.query.assert_called_once()
        assert result == mock_result

    def test_get_tenant_not_found(self, tenant_service, mock_db):
        """Test getting nonexistent tenant returns None"""
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = tenant_service.get_tenant("nonexistent")

        assert result is None

    def test_update_tenant(self, tenant_service, mock_db):
        """Test updating tenant"""
        from src.infrastructure.tenancy.models import Tenant

        # Mock existing tenant
        mock_tenant = Mock(spec=Tenant)
        mock_tenant.name = "Old Name"

        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_tenant

        result = tenant_service.update_tenant("ten_123", name="New Name")

        assert mock_db.commit.called
        assert result == mock_tenant

    def test_update_tenant_not_found(self, tenant_service, mock_db):
        """Test updating nonexistent tenant returns None"""
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = tenant_service.update_tenant("nonexistent", name="New Name")

        assert result is None
        assert not mock_db.commit.called

    def test_delete_tenant(self, tenant_service, mock_db):
        """Test deleting tenant"""
        from src.infrastructure.tenancy.models import Tenant

        mock_tenant = Mock(spec=Tenant)

        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_tenant

        result = tenant_service.delete_tenant("ten_123")

        assert result is True
        assert mock_db.delete.called
        assert mock_db.commit.called

    def test_delete_tenant_not_found(self, tenant_service, mock_db):
        """Test deleting nonexistent tenant returns False"""
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = tenant_service.delete_tenant("nonexistent")

        assert result is False
        assert not mock_db.delete.called

    def test_invite_user(self, tenant_service, mock_db):
        """Test inviting user to tenant"""
        invitation = tenant_service.invite_user(
            tenant_id="ten_123",
            email="user@example.com",
            role="member",
            invited_by_user_id="admin_123",
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    def test_invite_user_custom_expiration(self, tenant_service, mock_db):
        """Test inviting user with custom expiration"""
        invitation = tenant_service.invite_user(
            tenant_id="ten_123",
            email="user@example.com",
            role="member",
            invited_by_user_id="admin_123",
            expires_in_days=14,
        )

        assert mock_db.add.called

    def test_accept_invitation_success(self, tenant_service, mock_db):
        """Test accepting valid invitation"""
        from src.infrastructure.tenancy.models import TenantInvitation

        # Mock invitation
        mock_invitation = Mock(spec=TenantInvitation)
        mock_invitation.token = "valid_token"
        mock_invitation.status = "pending"
        mock_invitation.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_invitation.tenant_id = "ten_123"
        mock_invitation.role = "member"
        mock_invitation.invited_by = "admin_123"
        mock_invitation.created_at = datetime.utcnow()

        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_invitation

        result = tenant_service.accept_invitation("valid_token", "usr_123")

        assert result is True
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_accept_invitation_expired(self, tenant_service, mock_db):
        """Test accepting expired invitation"""
        from src.infrastructure.tenancy.models import TenantInvitation

        # Mock expired invitation
        mock_invitation = Mock(spec=TenantInvitation)
        mock_invitation.token = "expired_token"
        mock_invitation.status = "pending"
        mock_invitation.expires_at = datetime.utcnow() - timedelta(days=1)

        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_invitation

        result = tenant_service.accept_invitation("expired_token", "usr_123")

        assert result is False

    def test_accept_invitation_not_found(self, tenant_service, mock_db):
        """Test accepting nonexistent invitation"""
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = tenant_service.accept_invitation("nonexistent_token", "usr_123")

        assert result is False

    def test_log_activity_basic(self, tenant_service, mock_db):
        """Test logging basic activity"""
        tenant_service.log_activity(
            tenant_id="ten_123", action="user.created", user_id="usr_123"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    def test_log_activity_with_resource(self, tenant_service, mock_db):
        """Test logging activity with resource"""
        tenant_service.log_activity(
            tenant_id="ten_123",
            action="file.uploaded",
            user_id="usr_123",
            resource_type="simulation_file",
            resource_id="file_456",
        )

        assert mock_db.add.called

    def test_log_activity_with_metadata(self, tenant_service, mock_db):
        """Test logging activity with metadata"""
        tenant_service.log_activity(
            tenant_id="ten_123",
            action="settings.updated",
            user_id="admin_123",
            metadata={"setting": "max_users", "old_value": 5, "new_value": 10},
        )

        assert mock_db.add.called
