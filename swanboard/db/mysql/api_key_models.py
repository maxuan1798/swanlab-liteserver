#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Key models for SwanLab-Server platform-level API authentication
"""

from peewee import (
    CharField, IntegerField, TextField,
    ForeignKeyField, DateTimeField, BooleanField
)
from datetime import datetime, timedelta
import enum
import uuid
import secrets

from .models import CloudBaseModel, cloud_db


class APIKeyStatus(enum.Enum):
    """API Key status enumeration"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    REVOKED = 'revoked'


class APIKeyScope(enum.Enum):
    """API Key scope enumeration"""
    READ_ONLY = 'read_only'
    READ_WRITE = 'read_write'
    ADMIN = 'admin'


class APIKey(CloudBaseModel):
    """
    Platform-level API Key model for SwanLab-Server
    Provides programmatic access to the platform without user authentication
    """
    id = CharField(max_length=36, primary_key=True)

    # API Key information
    name = CharField(max_length=100, null=False, index=True)
    description = TextField(null=True)

    # Key values (hashed for storage)
    key_id = CharField(max_length=32, unique=True, null=False, index=True)  # Public identifier
    key_secret_hash = CharField(max_length=255, null=False)  # Hashed secret
    key_secret_salt = CharField(max_length=255, null=False)  # Salt for hashing

    # Scope and permissions
    scope = CharField(max_length=20, default=APIKeyScope.READ_WRITE.value)
    permissions = TextField(null=True)  # JSON format for fine-grained permissions

    # Status
    status = CharField(max_length=20, default=APIKeyStatus.ACTIVE.value)

    # Owner information (optional - can be system-level keys)
    owner_id = CharField(max_length=36, null=True, index=True)  # Account ID if user-owned

    # Rate limiting
    rate_limit = IntegerField(default=1000)  # Requests per hour

    # Expiration
    expires_at = DateTimeField(null=True)

    # Last used
    last_used_at = DateTimeField(null=True)
    last_used_ip = CharField(max_length=50, null=True)

    # Usage statistics
    usage_count = IntegerField(default=0)

    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'api_keys'

    def save(self, *args, **kwargs):
        """Auto-update timestamp on save"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    def is_active(self) -> bool:
        """Check if API key is active"""
        return self.status == APIKeyStatus.ACTIVE.value

    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)"""
        return self.is_active() and not self.is_expired()

    def can_access(self, required_scope: APIKeyScope) -> bool:
        """Check if API key has required scope"""
        current_scope = APIKeyScope(self.scope)

        # Scope hierarchy: READ_ONLY < READ_WRITE < ADMIN
        scope_hierarchy = {
            APIKeyScope.READ_ONLY: 1,
            APIKeyScope.READ_WRITE: 2,
            APIKeyScope.ADMIN: 3
        }

        return scope_hierarchy[current_scope] >= scope_hierarchy[required_scope]

    def update_usage(self, ip_address: str = None):
        """Update usage statistics"""
        self.last_used_at = datetime.now()
        if ip_address:
            self.last_used_ip = ip_address
        self.usage_count += 1
        self.save()


class APIKeyUsageLog(CloudBaseModel):
    """
    API Key usage log for auditing and rate limiting
    """
    id = CharField(max_length=36, primary_key=True)
    api_key_id = CharField(max_length=36, null=False, index=True)

    # Request information
    endpoint = CharField(max_length=255, null=False)
    method = CharField(max_length=10, null=False)
    ip_address = CharField(max_length=50, null=True)
    user_agent = CharField(max_length=500, null=True)

    # Response information
    status_code = IntegerField(null=True)
    response_time = IntegerField(null=True)  # in milliseconds

    # Timestamps
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'api_key_usage_logs'
        indexes = (
            (('api_key_id', 'created_at'), False),  # For usage analytics
        )


# All API Key models for batch operations
API_KEY_MODELS = [
    APIKey,
    APIKeyUsageLog,
]