"""
Tests for Authentication Service

Tests JWT-based authentication, password hashing, and RBAC.
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch
import pytest

if TYPE_CHECKING:
    from src.infrastructure.auth.service import AuthService, User

# Check for optional dependencies
try:
    from jose import JWTError
    import passlib
    AUTH_DEPS_AVAILABLE = True
except ImportError:
    AUTH_DEPS_AVAILABLE = False
    # Create a mock JWTError for testing if jose is not installed
    class MockJWTError(Exception):
        pass
    JWTError = MockJWTError

# Skip all tests if auth dependencies are not available
pytestmark = pytest.mark.skipif(
    not AUTH_DEPS_AVAILABLE,
    reason="Auth dependencies (jose, passlib) not installed"
)


class TestUserRole:
    """Test UserRole enum"""

    def test_user_role_values(self) -> None:
        """Test UserRole enum values"""
        from src.infrastructure.auth.service import UserRole

        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.READONLY.value == "readonly"


class TestTokenType:
    """Test TokenType enum"""

    def test_token_type_values(self) -> None:
        """Test TokenType enum values"""
        from src.infrastructure.auth.service import TokenType

        assert TokenType.ACCESS.value == "access"
        assert TokenType.REFRESH.value == "refresh"


class TestUserModels:
    """Test User models"""

    def test_user_model_creation(self) -> None:
        """Test User model can be created"""
        from src.infrastructure.auth.service import User, UserRole

        user = User(
            user_id="usr_123",
            email="user@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(),
        )

        assert user.user_id == "usr_123"
        assert user.email == "user@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True

    def test_user_in_db_model(self) -> None:
        """Test UserInDB model includes password hash"""
        from src.infrastructure.auth.service import UserInDB, UserRole

        user = UserInDB(
            user_id="usr_123",
            email="user@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(),
            hashed_password="$2b$12$hashed",
        )

        assert user.hashed_password == "$2b$12$hashed"


class TestAuthConfig:
    """Test AuthConfig"""

    def test_auth_config_defaults(self) -> None:
        """Test AuthConfig default values"""
        from src.infrastructure.auth.service import AuthConfig

        config = AuthConfig()

        assert config.ALGORITHM == "HS256"
        assert config.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert config.REFRESH_TOKEN_EXPIRE_DAYS == 7


class TestAuthService:
    """Test AuthService class"""

    @pytest.fixture
    def auth_service(self) -> "AuthService":
        """Create AuthService instance"""
        from src.infrastructure.auth.service import AuthService, AuthConfig

        config = AuthConfig()
        config.SECRET_KEY = "test-secret-key"
        config.REFRESH_SECRET_KEY = "test-refresh-secret-key"

        return AuthService(config)

    def test_auth_service_creation(self, auth_service: "AuthService") -> None:
        """Test AuthService can be created"""
        assert auth_service is not None

    def test_hash_password(self, auth_service: "AuthService") -> None:
        """Test password hashing"""
        password = "my_secret_password"
        hashed = auth_service.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_success(self, auth_service: "AuthService") -> None:
        """Test password verification succeeds with correct password"""
        password = "my_secret_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_failure(self, auth_service: "AuthService") -> None:
        """Test password verification fails with wrong password"""
        password = "my_secret_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_create_access_token(self, auth_service: "AuthService") -> None:
        """Test creating access token"""
        from src.infrastructure.auth.service import UserRole

        token = auth_service.create_access_token(
            user_id="usr_123", email="user@example.com", role=UserRole.USER
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, auth_service: "AuthService") -> None:
        """Test creating refresh token"""
        from src.infrastructure.auth.service import UserRole

        token = auth_service.create_refresh_token(
            user_id="usr_123", email="user@example.com", role=UserRole.USER
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_tokens(self, auth_service: "AuthService") -> None:
        """Test creating both tokens"""
        from src.infrastructure.auth.service import UserRole

        tokens = auth_service.create_tokens(
            user_id="usr_123", email="user@example.com", role=UserRole.USER
        )

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0

    def test_decode_access_token_success(self, auth_service: "AuthService") -> None:
        """Test decoding valid access token"""
        from src.infrastructure.auth.service import UserRole, TokenType

        token = auth_service.create_access_token(
            user_id="usr_123", email="user@example.com", role=UserRole.USER
        )

        token_data = auth_service.decode_access_token(token)

        assert token_data.user_id == "usr_123"
        assert token_data.email == "user@example.com"
        assert token_data.role == UserRole.USER
        assert token_data.token_type == TokenType.ACCESS

    def test_decode_access_token_invalid(self, auth_service: "AuthService") -> None:
        """Test decoding invalid token raises error"""
        with pytest.raises(JWTError):
            auth_service.decode_access_token("invalid.token.here")

    def test_decode_refresh_token_success(self, auth_service: "AuthService") -> None:
        """Test decoding valid refresh token"""
        from src.infrastructure.auth.service import UserRole, TokenType

        token = auth_service.create_refresh_token(
            user_id="usr_123", email="user@example.com", role=UserRole.ADMIN
        )

        token_data = auth_service.decode_refresh_token(token)

        assert token_data.user_id == "usr_123"
        assert token_data.token_type == TokenType.REFRESH

    def test_decode_refresh_token_invalid(self, auth_service: "AuthService") -> None:
        """Test decoding invalid refresh token raises error"""
        with pytest.raises(JWTError):
            auth_service.decode_refresh_token("invalid.token.here")

    def test_refresh_access_token(self, auth_service: "AuthService") -> None:
        """Test refreshing access token"""
        from src.infrastructure.auth.service import UserRole

        # Create original tokens
        original_tokens = auth_service.create_tokens(
            user_id="usr_123", email="user@example.com", role=UserRole.USER
        )

        # Refresh using refresh token
        new_tokens = auth_service.refresh_access_token(original_tokens.refresh_token)

        assert new_tokens.access_token != original_tokens.access_token
        assert new_tokens.refresh_token != original_tokens.refresh_token

    def test_authenticate_user_success(self, auth_service: "AuthService") -> None:
        """Test successful user authentication"""
        from src.infrastructure.auth.service import UserInDB, UserRole

        password = "test_password"
        hashed = auth_service.hash_password(password)

        user = UserInDB(
            user_id="usr_123",
            email="user@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(),
            hashed_password=hashed,
        )

        assert auth_service.authenticate_user(user, password) is True

    def test_authenticate_user_wrong_password(self, auth_service: "AuthService") -> None:
        """Test authentication fails with wrong password"""
        from src.infrastructure.auth.service import UserInDB, UserRole

        password = "test_password"
        hashed = auth_service.hash_password(password)

        user = UserInDB(
            user_id="usr_123",
            email="user@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(),
            hashed_password=hashed,
        )

        assert auth_service.authenticate_user(user, "wrong_password") is False

    def test_authenticate_user_inactive(self, auth_service: "AuthService") -> None:
        """Test authentication fails for inactive user"""
        from src.infrastructure.auth.service import UserInDB, UserRole

        password = "test_password"
        hashed = auth_service.hash_password(password)

        user = UserInDB(
            user_id="usr_123",
            email="user@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=False,
            created_at=datetime.now(),
            hashed_password=hashed,
        )

        assert auth_service.authenticate_user(user, password) is False

    def test_token_expiration(self, auth_service: "AuthService") -> None:
        """Test token with custom expiration"""
        from src.infrastructure.auth.service import UserRole

        # Create token that expires in 1 second
        token = auth_service.create_access_token(
            user_id="usr_123",
            email="user@example.com",
            role=UserRole.USER,
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        # Should raise error when decoding expired token
        with pytest.raises(JWTError):
            auth_service.decode_access_token(token)


class TestRBACHelpers:
    """Test RBAC helper functions"""

    @pytest.fixture
    def admin_user(self) -> "User":
        """Create admin user"""
        from src.infrastructure.auth.service import User, UserRole

        return User(
            user_id="admin_123",
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.now(),
        )

    @pytest.fixture
    def regular_user(self) -> "User":
        """Create regular user"""
        from src.infrastructure.auth.service import User, UserRole

        return User(
            user_id="usr_123",
            email="user@example.com",
            username="user",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(),
        )

    @pytest.fixture
    def readonly_user(self) -> "User":
        """Create readonly user"""
        from src.infrastructure.auth.service import User, UserRole

        return User(
            user_id="readonly_123",
            email="readonly@example.com",
            username="readonly",
            role=UserRole.READONLY,
            is_active=True,
            created_at=datetime.now(),
        )

    def test_has_role(self, admin_user: "User", regular_user: "User") -> None:
        """Test has_role function"""
        from src.infrastructure.auth.service import has_role, UserRole

        assert has_role(admin_user, [UserRole.ADMIN]) is True
        assert has_role(admin_user, [UserRole.USER]) is False
        assert has_role(regular_user, [UserRole.ADMIN, UserRole.USER]) is True

    def test_is_admin(self, admin_user: "User", regular_user: "User") -> None:
        """Test is_admin function"""
        from src.infrastructure.auth.service import is_admin

        assert is_admin(admin_user) is True
        assert is_admin(regular_user) is False

    def test_can_read(self, admin_user: "User", regular_user: "User", readonly_user: "User") -> None:
        """Test can_read function"""
        from src.infrastructure.auth.service import can_read

        assert can_read(admin_user) is True
        assert can_read(regular_user) is True
        assert can_read(readonly_user) is True

    def test_can_write(self, admin_user: "User", regular_user: "User", readonly_user: "User") -> None:
        """Test can_write function"""
        from src.infrastructure.auth.service import can_write

        assert can_write(admin_user) is True
        assert can_write(regular_user) is True
        assert can_write(readonly_user) is False

    def test_can_delete(self, admin_user: "User", regular_user: "User", readonly_user: "User") -> None:
        """Test can_delete function"""
        from src.infrastructure.auth.service import can_delete

        assert can_delete(admin_user) is True
        assert can_delete(regular_user) is False
        assert can_delete(readonly_user) is False
