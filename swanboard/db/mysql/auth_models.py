#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authentication-related database models for SwanLab-Server
"""

from peewee import (
    CharField, IntegerField, TextField,
    ForeignKeyField, DateTimeField, BooleanField
)
from datetime import datetime
import enum

from .models import CloudBaseModel, cloud_db


class AccountStatus(enum.Enum):
    """Account status enumeration"""
    ACTIVE = 'active'
    PENDING = 'pending'
    BANNED = 'banned'


class Tenant(CloudBaseModel):
    """
    Tenant model for multi-tenancy support
    Each tenant represents a workspace or organization
    """
    id = CharField(max_length=36, primary_key=True)
    name = CharField(max_length=100, null=False, index=True)
    description = TextField(null=True)

    # Owner information
    owner_id = CharField(max_length=36, null=True)

    # Settings
    settings = TextField(null=True)  # JSON format

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'tenants'

    def save(self, *args, **kwargs):
        """Auto-update timestamp on save"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class Account(CloudBaseModel):
    """
    Account model for user authentication
    Supports both password-based and OAuth authentication
    """
    id = CharField(max_length=36, primary_key=True)
    email = CharField(max_length=255, unique=True, null=False, index=True)

    # Password authentication
    password = CharField(max_length=255, null=True)  # Hashed password
    password_salt = CharField(max_length=255, null=True)

    # Profile
    name = CharField(max_length=100, null=False)
    avatar = CharField(max_length=500, null=True)

    # Status
    status = CharField(max_length=20, default=AccountStatus.ACTIVE.value)

    # Current active tenant
    current_tenant_id = CharField(max_length=36, null=True, index=True)

    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    last_login_at = DateTimeField(null=True)
    last_active_at = DateTimeField(null=True)

    class Meta:
        table_name = 'accounts'

    def save(self, *args, **kwargs):
        """Auto-update timestamp on save"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    def is_active(self) -> bool:
        """Check if account is active"""
        return self.status == AccountStatus.ACTIVE.value

    def is_banned(self) -> bool:
        """Check if account is banned"""
        return self.status == AccountStatus.BANNED.value


class TenantAccountJoin(CloudBaseModel):
    """
    Junction table for many-to-many relationship between tenants and accounts
    Represents user membership in tenants/workspaces
    """
    id = CharField(max_length=36, primary_key=True)
    tenant_id = CharField(max_length=36, null=False, index=True)
    account_id = CharField(max_length=36, null=False, index=True)

    # Role in this tenant
    role = CharField(max_length=20, default='member')  # owner, admin, member, viewer

    # Is this the current active tenant for this account
    current = BooleanField(default=False)

    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'tenant_account_joins'
        indexes = (
            (('tenant_id', 'account_id'), True),  # Unique together
        )

    def save(self, *args, **kwargs):
        """Auto-update timestamp on save"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class AccountIntegrate(CloudBaseModel):
    """
    OAuth integration model for third-party authentication
    Links external OAuth accounts (GitHub, Google, etc.) to SwanLab accounts
    """
    id = CharField(max_length=36, primary_key=True)
    account_id = CharField(max_length=36, null=False, index=True)

    # OAuth provider information
    provider = CharField(max_length=20, null=False, index=True)  # github, google, etc.
    open_id = CharField(max_length=255, null=False)  # Provider's user ID

    # OAuth tokens (encrypted/hashed in production)
    access_token = TextField(null=True)
    refresh_token = TextField(null=True)
    token_expires_at = DateTimeField(null=True)

    # Profile data from provider
    provider_username = CharField(max_length=100, null=True)
    provider_email = CharField(max_length=255, null=True)
    provider_data = TextField(null=True)  # JSON format for additional data

    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'account_integrates'
        indexes = (
            (('provider', 'open_id'), True),  # Unique combination
        )

    def save(self, *args, **kwargs):
        """Auto-update timestamp on save"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class RefreshToken(CloudBaseModel):
    """
    Refresh token model for JWT token management
    Stores refresh tokens for token rotation
    """
    id = CharField(max_length=36, primary_key=True)
    account_id = CharField(max_length=36, null=False, index=True)

    # Token information
    token = CharField(max_length=500, unique=True, null=False)

    # Metadata
    ip_address = CharField(max_length=50, null=True)
    user_agent = CharField(max_length=500, null=True)

    # Status
    is_revoked = BooleanField(default=False)

    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    expires_at = DateTimeField(null=False)

    class Meta:
        table_name = 'refresh_tokens'

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)"""
        return not self.is_revoked and not self.is_expired()


# All authentication models for batch operations
AUTH_MODELS = [
    Tenant,
    Account,
    TenantAccountJoin,
    AccountIntegrate,
    RefreshToken,
]