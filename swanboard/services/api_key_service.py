#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Key service for SwanLab-Server platform-level API authentication
Handles API Key generation, validation, and management
"""

import uuid
import base64
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List

from ..db.mysql.api_key_models import APIKey, APIKeyUsageLog, APIKeyStatus, APIKeyScope
from ..db.mysql.auth_models import Account


class APIKeyService:
    """Service for managing platform-level API Keys"""

    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """
        Generate a new API Key pair (key_id and key_secret)
        Returns: (key_id, key_secret)
        """
        # Generate key_id (public identifier)
        key_id = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip('=')

        # Generate key_secret (private secret)
        key_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')

        return key_id, key_secret

    @staticmethod
    def hash_key_secret(key_secret: str) -> Tuple[str, str]:
        """
        Hash API Key secret for secure storage
        Returns: (hashed_secret, salt)
        """
        salt = base64.b64encode(secrets.token_bytes(16)).decode()
        key_secret_bytes = key_secret.encode('utf-8')
        salt_bytes = salt.encode('utf-8')

        # Generate bcrypt hash
        hashed_bytes = bcrypt.hashpw(key_secret_bytes, bcrypt.gensalt())
        hashed_secret = hashed_bytes.decode('utf-8')

        return hashed_secret, salt

    @staticmethod
    def verify_key_secret(key_secret: str, hashed_secret: str, salt: str) -> bool:
        """Verify API Key secret against hash and salt"""
        key_secret_bytes = key_secret.encode('utf-8')
        hashed_bytes = hashed_secret.encode('utf-8')

        # Verify secret using bcrypt
        return bcrypt.checkpw(key_secret_bytes, hashed_bytes)

    @staticmethod
    def create_api_key(
        name: str,
        description: str = None,
        scope: APIKeyScope = APIKeyScope.READ_WRITE,
        owner_id: str = None,
        expires_in_days: int = None,
        rate_limit: int = 1000
    ) -> Dict[str, str]:
        """
        Create a new platform-level API Key
        Returns: API Key information including the secret (only shown once)
        """
        # Generate API Key pair
        key_id, key_secret = APIKeyService.generate_api_key()

        # Hash the secret for storage
        hashed_secret, salt = APIKeyService.hash_key_secret(key_secret)

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        # Create API Key record
        api_key = APIKey.create(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            key_id=key_id,
            key_secret_hash=hashed_secret,
            key_secret_salt=salt,
            scope=scope.value,
            owner_id=owner_id,
            expires_at=expires_at,
            rate_limit=rate_limit,
            status=APIKeyStatus.ACTIVE.value
        )

        return {
            "id": api_key.id,
            "key_id": key_id,
            "key_secret": key_secret,  # Only returned once!
            "name": api_key.name,
            "scope": api_key.scope,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat()
        }

    @staticmethod
    def validate_api_key(key_id: str, key_secret: str) -> Optional[APIKey]:
        """
        Validate API Key credentials
        Returns: APIKey object if valid, None otherwise
        """
        try:
            # Find API Key by key_id
            api_key = APIKey.get(APIKey.key_id == key_id)

            # Check if key is valid
            if not api_key.is_valid():
                return None

            # Verify secret
            if not APIKeyService.verify_key_secret(key_secret, api_key.key_secret_hash, api_key.key_secret_salt):
                return None

            return api_key

        except APIKey.DoesNotExist:
            return None

    @staticmethod
    def get_api_key_by_id(api_key_id: str) -> Optional[APIKey]:
        """Get API Key by ID"""
        try:
            return APIKey.get(APIKey.id == api_key_id)
        except APIKey.DoesNotExist:
            return None

    @staticmethod
    def get_api_key_by_key_id(key_id: str) -> Optional[APIKey]:
        """Get API Key by key_id"""
        try:
            return APIKey.get(APIKey.key_id == key_id)
        except APIKey.DoesNotExist:
            return None

    @staticmethod
    def list_api_keys(owner_id: str = None, status: APIKeyStatus = None) -> List[APIKey]:
        """List API Keys with optional filters"""
        query = APIKey.select()

        if owner_id:
            query = query.where(APIKey.owner_id == owner_id)

        if status:
            query = query.where(APIKey.status == status.value)

        return list(query.order_by(APIKey.created_at.desc()))

    @staticmethod
    def update_api_key(
        api_key_id: str,
        name: str = None,
        description: str = None,
        scope: APIKeyScope = None,
        status: APIKeyStatus = None,
        rate_limit: int = None
    ) -> Optional[APIKey]:
        """Update API Key properties"""
        try:
            api_key = APIKey.get(APIKey.id == api_key_id)

            if name is not None:
                api_key.name = name
            if description is not None:
                api_key.description = description
            if scope is not None:
                api_key.scope = scope.value
            if status is not None:
                api_key.status = status.value
            if rate_limit is not None:
                api_key.rate_limit = rate_limit

            api_key.save()
            return api_key

        except APIKey.DoesNotExist:
            return None

    @staticmethod
    def revoke_api_key(api_key_id: str) -> bool:
        """Revoke an API Key"""
        try:
            api_key = APIKey.get(APIKey.id == api_key_id)
            api_key.status = APIKeyStatus.REVOKED.value
            api_key.save()
            return True
        except APIKey.DoesNotExist:
            return False

    @staticmethod
    def delete_api_key(api_key_id: str) -> bool:
        """Delete an API Key (permanent removal)"""
        try:
            api_key = APIKey.get(APIKey.id == api_key_id)
            api_key.delete_instance()
            return True
        except APIKey.DoesNotExist:
            return False

    @staticmethod
    def log_usage(
        api_key_id: str,
        endpoint: str,
        method: str,
        ip_address: str = None,
        user_agent: str = None,
        status_code: int = None,
        response_time: int = None
    ):
        """Log API Key usage for auditing and rate limiting"""
        APIKeyUsageLog.create(
            id=str(uuid.uuid4()),
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            response_time=response_time
        )

    @staticmethod
    def get_usage_stats(api_key_id: str, days: int = 30) -> Dict[str, any]:
        """Get usage statistics for an API Key"""
        since_date = datetime.now() - timedelta(days=days)

        # Get total usage count
        total_usage = APIKeyUsageLog.select().where(
            (APIKeyUsageLog.api_key_id == api_key_id) &
            (APIKeyUsageLog.created_at >= since_date)
        ).count()

        # Get usage by endpoint
        endpoint_stats = (
            APIKeyUsageLog
            .select(
                APIKeyUsageLog.endpoint,
                APIKeyUsageLog.method,
                APIKeyUsageLog.status_code,
                APIKeyUsageLog.response_time
            )
            .where(
                (APIKeyUsageLog.api_key_id == api_key_id) &
                (APIKeyUsageLog.created_at >= since_date)
            )
            .dicts()
        )

        return {
            "total_usage": total_usage,
            "endpoint_stats": list(endpoint_stats),
            "period_days": days
        }

    @staticmethod
    def check_rate_limit(api_key_id: str) -> bool:
        """Check if API Key is within rate limits"""
        try:
            api_key = APIKey.get(APIKey.id == api_key_id)

            # Get usage in the last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_usage = APIKeyUsageLog.select().where(
                (APIKeyUsageLog.api_key_id == api_key_id) &
                (APIKeyUsageLog.created_at >= one_hour_ago)
            ).count()

            return recent_usage < api_key.rate_limit

        except APIKey.DoesNotExist:
            return False