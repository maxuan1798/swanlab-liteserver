#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OAuth service for third-party authentication (GitHub, Google, etc.)
"""

import uuid
from typing import Optional, Tuple, Dict
from datetime import datetime

import httpx

from ..db.mysql import Account, AccountIntegrate, Tenant, TenantAccountJoin, AccountStatus
from ..config.auth_config import AuthConfig


class GitHubOAuth:
    """GitHub OAuth authentication handler"""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        self.client_id = client_id or AuthConfig.GITHUB_CLIENT_ID
        self.client_secret = client_secret or AuthConfig.GITHUB_CLIENT_SECRET
        self.redirect_uri = redirect_uri or AuthConfig.GITHUB_REDIRECT_URI

        # GitHub OAuth URLs
        self.auth_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        self.user_url = "https://api.github.com/user"
        self.email_url = "https://api.github.com/user/emails"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate GitHub OAuth authorization URL
        Args:
            state: CSRF protection state parameter
        Returns:
            Authorization URL
        """
        if not state:
            state = str(uuid.uuid4())

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.auth_url}?{query_string}"

    def get_access_token(self, code: str) -> str:
        """
        Exchange authorization code for access token
        Args:
            code: Authorization code from GitHub
        Returns:
            Access token
        """
        response = httpx.post(
            self.token_url,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
            headers={"Accept": "application/json"},
        )

        response.raise_for_status()
        data = response.json()

        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("Failed to get access token from GitHub")

        return access_token

    def get_user_info(self, token: str) -> Dict:
        """
        Get user information from GitHub
        Args:
            token: GitHub access token
        Returns:
            User information dictionary
        """
        headers = {"Authorization": f"token {token}"}

        # Get user profile
        user_response = httpx.get(self.user_url, headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()

        # Get user emails
        email_response = httpx.get(self.email_url, headers=headers)
        email_response.raise_for_status()
        emails_data = email_response.json()

        # Find primary email
        primary_email = next(
            (email for email in emails_data if email.get("primary")),
            {}
        )

        return {
            "id": str(user_data["id"]),
            "username": user_data.get("login"),
            "name": user_data.get("name") or user_data.get("login"),
            "email": primary_email.get("email") or f"{user_data['id']}@github.com",
            "avatar": user_data.get("avatar_url"),
            "bio": user_data.get("bio"),
        }

    def authenticate(self, code: str) -> Tuple[Account, bool]:
        """
        Authenticate user with GitHub OAuth code
        Args:
            code: Authorization code from GitHub
        Returns:
            Tuple of (Account, is_new_user)
        """
        # Get access token
        access_token = self.get_access_token(code)

        # Get user info
        user_info = self.get_user_info(access_token)

        # Check if GitHub account is already linked
        try:
            integrate = AccountIntegrate.get(
                (AccountIntegrate.provider == "github") &
                (AccountIntegrate.open_id == user_info["id"])
            )

            # Update integration info
            integrate.provider_username = user_info["username"]
            integrate.provider_email = user_info["email"]
            integrate.access_token = access_token
            integrate.save()

            # Get associated account
            account = Account.get(Account.id == integrate.account_id)
            account.last_login_at = datetime.now()
            account.save()

            return account, False

        except AccountIntegrate.DoesNotExist:
            pass

        # Check if email is already registered
        try:
            account = Account.get(Account.email == user_info["email"])

            # Link GitHub account to existing account
            AccountIntegrate.create(
                id=str(uuid.uuid4()),
                account_id=account.id,
                provider="github",
                open_id=user_info["id"],
                provider_username=user_info["username"],
                provider_email=user_info["email"],
                access_token=access_token,
            )

            account.last_login_at = datetime.now()
            account.save()

            return account, False

        except Account.DoesNotExist:
            pass

        # Create new account
        account_id = str(uuid.uuid4())
        account = Account.create(
            id=account_id,
            email=user_info["email"],
            name=user_info["name"],
            avatar=user_info.get("avatar"),
            status=AccountStatus.ACTIVE.value,
        )

        # Create GitHub integration
        AccountIntegrate.create(
            id=str(uuid.uuid4()),
            account_id=account_id,
            provider="github",
            open_id=user_info["id"],
            provider_username=user_info["username"],
            provider_email=user_info["email"],
            access_token=access_token,
        )

        # Create default tenant
        tenant_id = str(uuid.uuid4())
        tenant = Tenant.create(
            id=tenant_id,
            name=f"{user_info['name']}'s Workspace",
            owner_id=account_id,
        )

        # Create tenant-account relationship
        TenantAccountJoin.create(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            account_id=account_id,
            role="owner",
            current=True,
        )

        # Set as current tenant
        account.current_tenant_id = tenant_id
        account.save()

        return account, True


class GoogleOAuth:
    """Google OAuth authentication handler (placeholder for future implementation)"""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        self.client_id = client_id or AuthConfig.GOOGLE_CLIENT_ID
        self.client_secret = client_secret or AuthConfig.GOOGLE_CLIENT_SECRET
        self.redirect_uri = redirect_uri or AuthConfig.GOOGLE_REDIRECT_URI

        # Google OAuth URLs
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        if not state:
            state = str(uuid.uuid4())

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.auth_url}?{query_string}"

    # TODO: Implement Google OAuth methods similar to GitHubOAuth
