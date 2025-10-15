#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OAuth authentication routes for SwanLab-Server
Handles GitHub and other OAuth providers
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import uuid

from ..services.oauth_service import GitHubOAuth
from ..services.auth_service import AuthService


router = APIRouter()


# ================================ Request/Response Models ================================


class OAuthCallbackResponse(BaseModel):
    """OAuth callback response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    is_new_user: bool
    account_id: str


class OAuthAuthorizationResponse(BaseModel):
    """OAuth authorization response"""
    authorization_url: str
    state: str


# ================================ GitHub OAuth Routes ================================


@router.get("/github/authorize", response_model=OAuthAuthorizationResponse)
async def github_authorize(request: Request):
    """
    Initiate GitHub OAuth flow

    Generates GitHub OAuth authorization URL and state token for CSRF protection.
    Redirect the user to the returned authorization_url.

    Returns
    -------
    OAuthAuthorizationResponse
        Authorization URL and state token
    """
    # Generate state token for CSRF protection
    state = str(uuid.uuid4())

    # Store state in session (in production, use Redis or database)
    # For now, we'll trust the callback to validate

    # Initialize GitHub OAuth
    github_oauth = GitHubOAuth()

    # Generate authorization URL
    authorization_url = github_oauth.get_authorization_url(state)

    return OAuthAuthorizationResponse(
        authorization_url=authorization_url,
        state=state
    )


@router.get("/github/callback")
async def github_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    request: Request = None
):
    """
    GitHub OAuth callback handler

    Handles the callback from GitHub after user authorization.
    Exchanges the authorization code for tokens and creates/updates user account.

    Parameters
    ----------
    code : str
        Authorization code from GitHub
    state : str
        State token for CSRF validation
    error : str, optional
        Error message if authorization failed

    Returns
    -------
    OAuthCallbackResponse
        JWT tokens and user information
    """
    # Check for errors
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub OAuth error: {error}"
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required"
        )

    # TODO: Validate state token for CSRF protection
    # In production, retrieve and validate the state from session/Redis

    try:
        # Initialize GitHub OAuth
        github_oauth = GitHubOAuth()

        # Authenticate with GitHub
        account, is_new_user = github_oauth.authenticate(code)

        # Generate JWT tokens
        tokens = AuthService.login(
            account,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )

        return OAuthCallbackResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            is_new_user=is_new_user,
            account_id=account.id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub authentication failed: {str(e)}"
        )


@router.get("/github")
async def github_login_redirect():
    """
    Convenience endpoint that directly redirects to GitHub authorization

    Alternative to /github/authorize that immediately redirects instead of
    returning JSON.
    """
    github_oauth = GitHubOAuth()
    state = str(uuid.uuid4())
    authorization_url = github_oauth.get_authorization_url(state)

    return RedirectResponse(url=authorization_url)


# ================================ Google OAuth Routes (Placeholder) ================================


@router.get("/google/authorize")
async def google_authorize():
    """
    Initiate Google OAuth flow (placeholder)

    TODO: Implement Google OAuth similar to GitHub
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth is not yet implemented"
    )


@router.get("/google/callback")
async def google_callback():
    """
    Google OAuth callback handler (placeholder)

    TODO: Implement Google OAuth callback
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth is not yet implemented"
    )
