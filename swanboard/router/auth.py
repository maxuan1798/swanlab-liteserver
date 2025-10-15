#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authentication routes for SwanLab-Server
Handles user login, registration, token refresh, and user info
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..services.auth_service import AuthService
from ..db.mysql import Account


router = APIRouter()
security = HTTPBearer()


# ================================ Request/Response Models ================================


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request model"""
    email: EmailStr
    password: str
    name: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class AccountResponse(BaseModel):
    """Account response model"""
    id: str
    email: str
    name: str
    avatar: Optional[str]
    status: str
    current_tenant_id: Optional[str]
    created_at: str
    last_login_at: Optional[str]


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


# ================================ Dependency Functions ================================


async def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Account:
    """
    Dependency to get current authenticated account from JWT token
    """
    token = credentials.credentials

    # Verify token
    payload = AuthService.verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get account
    account_id = payload.get("sub")
    account = AuthService.get_account_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found",
        )

    if not account.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    return account


# ================================ Auth Routes ================================


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, http_request: Request):
    """
    Register a new account

    Creates a new account with email and password, and automatically
    creates a default workspace for the user.

    Returns JWT access and refresh tokens.
    """
    try:
        # Register account
        account = AuthService.register_account(
            email=request.email,
            password=request.password,
            name=request.name,
            create_default_tenant=True
        )

        # Generate tokens
        tokens = AuthService.login(
            account,
            ip_address=http_request.client.host,
            user_agent=http_request.headers.get("user-agent")
        )

        return TokenResponse(**tokens)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request):
    """
    Login with email and password

    Authenticates user credentials and returns JWT access and refresh tokens.

    Parameters
    ----------
    request : LoginRequest
        Login credentials (email and password)

    Returns
    -------
    TokenResponse
        JWT tokens and expiration info
    """
    try:
        # Authenticate user
        account = AuthService.authenticate(request.email, request.password)

        # Generate tokens
        tokens = AuthService.login(
            account,
            ip_address=http_request.client.host,
            user_agent=http_request.headers.get("user-agent")
        )

        return TokenResponse(**tokens)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token

    Uses a valid refresh token to generate a new access token.

    Parameters
    ----------
    request : RefreshTokenRequest
        Refresh token

    Returns
    -------
    TokenResponse
        New access token
    """
    try:
        tokens = AuthService.refresh_access_token(request.refresh_token)
        return TokenResponse(**tokens)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshTokenRequest
):
    """
    Logout user

    Revokes the refresh token to prevent further token refreshes.

    Parameters
    ----------
    request : RefreshTokenRequest
        Refresh token to revoke

    Returns
    -------
    MessageResponse
        Success message
    """
    try:
        AuthService.revoke_refresh_token(request.refresh_token)
        return MessageResponse(message="Logged out successfully")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=AccountResponse)
async def get_current_user(account: Account = Depends(get_current_account)):
    """
    Get current authenticated user information

    Returns the profile information of the currently logged-in user.

    Returns
    -------
    AccountResponse
        Current user's account information
    """
    return AccountResponse(
        id=account.id,
        email=account.email,
        name=account.name,
        avatar=account.avatar,
        status=account.status,
        current_tenant_id=account.current_tenant_id,
        created_at=account.created_at.isoformat() if account.created_at else None,
        last_login_at=account.last_login_at.isoformat() if account.last_login_at else None,
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint

    Simple endpoint to check if the authentication service is running.
    """
    return {"status": "healthy", "service": "authentication"}
