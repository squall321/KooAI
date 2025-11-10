"""
Authentication API Routes

Endpoints for user authentication and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.infrastructure.auth.service import AuthService, User, UserRole, Token, UserInDB
from src.infrastructure.auth.dependencies import (
    get_auth_service,
    get_current_user,
    get_current_active_user,
    require_admin,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request."""

    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.USER


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request."""

    old_password: str
    new_password: str


class UserResponse(BaseModel):
    """User response (without password)."""

    user_id: str
    email: str
    username: str
    role: UserRole
    is_active: bool


# Temporary in-memory user storage (replace with database)
_users_db: dict[str, UserInDB] = {}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Create a new user account",
)
async def register(
    request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
) -> "UserResponse":
    """
    ## Register New User

    Create a new user account with email and password.

    ### Request Body
    - **email**: User email address
    - **username**: Username
    - **password**: Password (min 8 characters)
    - **role**: User role (default: user)

    ### Returns
    - User information (without password)

    ### Errors
    - **400**: User already exists
    - **422**: Validation error

    ### Example
    ```json
    {
        "email": "user@example.com",
        "username": "john",
        "password": "securepassword123",
        "role": "user"
    }
    ```
    """
    # Check if user exists
    if request.email in _users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password
    hashed_password = auth_service.hash_password(request.password)

    # Create user
    import uuid
    from datetime import datetime

    user = UserInDB(
        user_id=str(uuid.uuid4()),
        email=request.email,
        username=request.username,
        role=request.role,
        is_active=True,
        created_at=datetime.utcnow(),
        hashed_password=hashed_password,
    )

    # Store user (in real app, save to database)
    _users_db[request.email] = user

    # Return user without password
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Authenticate and receive access & refresh tokens",
)
async def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> Token:
    """
    ## User Login

    Authenticate with email and password to receive JWT tokens.

    ### Request Body
    - **email**: User email
    - **password**: User password

    ### Returns
    - **access_token**: JWT access token (30 min expiry)
    - **refresh_token**: JWT refresh token (7 days expiry)
    - **token_type**: "bearer"
    - **expires_in**: Access token expiration in seconds

    ### Errors
    - **401**: Invalid credentials
    - **400**: Inactive user

    ### Example
    ```json
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    ```

    ### Response
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer",
        "expires_in": 1800
    }
    ```
    """
    # Get user from database
    user = _users_db.get(request.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Authenticate
    if not auth_service.authenticate_user(user, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    tokens = auth_service.create_tokens(user.user_id, user.email, user.role)

    return tokens


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh Access Token",
    description="Get new access token using refresh token",
)
async def refresh(request: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)) -> Token:
    """
    ## Refresh Access Token

    Get a new access token using a valid refresh token.

    ### Request Body
    - **refresh_token**: Valid refresh token

    ### Returns
    - New access and refresh tokens

    ### Errors
    - **401**: Invalid or expired refresh token

    ### Example
    ```json
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    ```
    """
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token)
        return tokens
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get information about the currently authenticated user",
)
async def get_me(current_user: User = Depends(get_current_active_user)) -> "UserResponse":
    """
    ## Get Current User

    Retrieve information about the currently authenticated user.

    ### Headers
    - **Authorization**: Bearer {access_token}

    ### Returns
    - Current user information

    ### Errors
    - **401**: Invalid or missing token
    - **400**: Inactive user

    ### Example
    ```bash
    curl -H "Authorization: Bearer eyJ0eXAi..." http://localhost:8000/api/v1/auth/me
    ```
    """
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change Password",
    description="Change user password",
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    ## Change Password

    Change the current user's password.

    ### Request Body
    - **old_password**: Current password
    - **new_password**: New password (min 8 characters)

    ### Errors
    - **401**: Invalid old password
    - **422**: Validation error

    ### Example
    ```json
    {
        "old_password": "oldpassword123",
        "new_password": "newsecurepassword456"
    }
    ```
    """
    # Get user from database
    user = _users_db.get(current_user.email)

    if user is None or not auth_service.verify_password(request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    # Update password
    user.hashed_password = auth_service.hash_password(request.new_password)
    _users_db[current_user.email] = user


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List Users (Admin)",
    description="List all users (admin only)",
)
async def list_users(current_user: User = Depends(require_admin)) -> list["UserResponse"]:
    """
    ## List All Users (Admin Only)

    Retrieve a list of all registered users.

    ### Permissions
    - Requires admin role

    ### Returns
    - List of all users

    ### Errors
    - **403**: Insufficient privileges
    - **401**: Invalid or missing token

    ### Example
    ```bash
    curl -H "Authorization: Bearer {admin_token}" http://localhost:8000/api/v1/auth/users
    ```
    """
    users = [
        UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
        )
        for user in _users_db.values()
    ]
    return users
