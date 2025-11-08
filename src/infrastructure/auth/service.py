"""
Authentication and Authorization Module

JWT-based authentication with refresh tokens and role-based access control.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class TokenType(str, Enum):
    """Token types."""

    ACCESS = "access"
    REFRESH = "refresh"


class User(BaseModel):
    """User model."""

    user_id: str
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool = True
    created_at: datetime


class UserInDB(User):
    """User model with password hash."""

    hashed_password: str


class Token(BaseModel):
    """Access token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""

    user_id: str
    email: str
    role: UserRole
    token_type: TokenType


class AuthConfig:
    """Authentication configuration."""

    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    REFRESH_SECRET_KEY: str = "your-refresh-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class AuthService:
    """
    Authentication service.

    Handles user authentication, token generation, and password hashing.
    """

    def __init__(self, config: Optional[AuthConfig] = None):
        """Initialize auth service."""
        self.config = config or AuthConfig()

    # Password hashing
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    # Token generation
    def create_access_token(
        self, user_id: str, email: str, role: UserRole, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User ID
            email: User email
            role: User role
            expires_delta: Custom expiration time

        Returns:
            JWT access token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "type": TokenType.ACCESS.value,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, user_id: str, email: str, role: UserRole) -> str:
        """
        Create JWT refresh token.

        Args:
            user_id: User ID
            email: User email
            role: User role

        Returns:
            JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "type": TokenType.REFRESH.value,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(
            to_encode, self.config.REFRESH_SECRET_KEY, algorithm=self.config.ALGORITHM
        )
        return encoded_jwt

    def create_tokens(self, user_id: str, email: str, role: UserRole) -> Token:
        """
        Create both access and refresh tokens.

        Args:
            user_id: User ID
            email: User email
            role: User role

        Returns:
            Token object with both tokens
        """
        access_token = self.create_access_token(user_id, email, role)
        refresh_token = self.create_refresh_token(user_id, email, role)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # Token validation
    def decode_access_token(self, token: str) -> TokenData:
        """
        Decode and validate access token.

        Args:
            token: JWT access token

        Returns:
            Token payload data

        Raises:
            JWTError: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.ALGORITHM])

            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            token_type: str = payload.get("type")

            if user_id is None or token_type != TokenType.ACCESS.value:
                raise JWTError("Invalid token")

            return TokenData(
                user_id=user_id, email=email, role=UserRole(role), token_type=TokenType.ACCESS
            )
        except JWTError as e:
            raise JWTError(f"Could not validate credentials: {e}")

    def decode_refresh_token(self, token: str) -> TokenData:
        """
        Decode and validate refresh token.

        Args:
            token: JWT refresh token

        Returns:
            Token payload data

        Raises:
            JWTError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token, self.config.REFRESH_SECRET_KEY, algorithms=[self.config.ALGORITHM]
            )

            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            token_type: str = payload.get("type")

            if user_id is None or token_type != TokenType.REFRESH.value:
                raise JWTError("Invalid refresh token")

            return TokenData(
                user_id=user_id, email=email, role=UserRole(role), token_type=TokenType.REFRESH
            )
        except JWTError as e:
            raise JWTError(f"Could not validate refresh token: {e}")

    def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair

        Raises:
            JWTError: If refresh token is invalid
        """
        token_data = self.decode_refresh_token(refresh_token)

        # Create new tokens
        return self.create_tokens(token_data.user_id, token_data.email, token_data.role)

    # User authentication
    def authenticate_user(self, user: UserInDB, password: str) -> bool:
        """
        Authenticate user with password.

        Args:
            user: User from database
            password: Plain text password

        Returns:
            True if authentication successful
        """
        if not user.is_active:
            return False

        return self.verify_password(password, user.hashed_password)


# Role-based access control helpers
def has_role(user: User, required_roles: List[UserRole]) -> bool:
    """
    Check if user has required role.

    Args:
        user: User object
        required_roles: List of allowed roles

    Returns:
        True if user has one of the required roles
    """
    return user.role in required_roles


def is_admin(user: User) -> bool:
    """Check if user is admin."""
    return user.role == UserRole.ADMIN


def can_read(user: User) -> bool:
    """Check if user can read (all roles)."""
    return user.is_active


def can_write(user: User) -> bool:
    """Check if user can write (admin and user roles)."""
    return user.role in [UserRole.ADMIN, UserRole.USER]


def can_delete(user: User) -> bool:
    """Check if user can delete (admin only)."""
    return user.role == UserRole.ADMIN
