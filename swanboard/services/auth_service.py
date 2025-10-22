#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authentication service for SwanLab-Server
Handles password hashing, JWT token generation, and authentication logic
"""

import uuid
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict

import bcrypt
from jose import JWTError, jwt
import redis

from ..db.mysql import Account, AccountStatus, RefreshToken
from ..config.auth_config import AuthConfig

# Redis client for refresh token storage (optional, can also use database)
redis_client: Optional[redis.Redis] = None


class AuthService:
    """Authentication service for user management and JWT tokens"""

    @staticmethod
    def initialize_redis(redis_url: str):
        """Initialize Redis client for token storage"""
        global redis_client
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}")
            redis_client = None

    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """
        Hash password with salt
        Returns: (hashed_password, salt)

        Note: Client sends MD5 hashed passwords, so password length is always 32 bytes
        """
        salt = base64.b64encode(secrets.token_bytes(16)).decode()

        # Use bcrypt directly to avoid passlib compatibility issues
        # Client sends MD5 hashes (32 bytes), well within bcrypt's 72-byte limit
        password_bytes = password.encode('utf-8')

        # Generate bcrypt hash
        hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        hashed = hashed_bytes.decode('utf-8')

        return hashed, salt

    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash and salt"""
        # Use bcrypt directly to avoid passlib compatibility issues
        # Client sends MD5 hashes (32 bytes), well within bcrypt's 72-byte limit
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')

        # Verify password using bcrypt
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def create_access_token(
        account_id: str,
        tenant_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        """
        if expires_delta is None:
            expires_delta = timedelta(seconds=AuthConfig.JWT_ACCESS_TOKEN_EXPIRES)

        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": account_id,
            "tenant_id": tenant_id,
            "exp": expire,
            "type": "access"
        }

        encoded_jwt = jwt.encode(
            to_encode,
            AuthConfig.JWT_SECRET_KEY,
            algorithm=AuthConfig.JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        account_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create and store refresh token
        """
        token_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(seconds=AuthConfig.JWT_REFRESH_TOKEN_EXPIRES)

        # Create token payload
        to_encode = {
            "sub": account_id,
            "jti": token_id,
            "exp": expires_at,
            "type": "refresh"
        }

        token = jwt.encode(
            to_encode,
            AuthConfig.JWT_SECRET_KEY,
            algorithm=AuthConfig.JWT_ALGORITHM
        )

        # Store in database
        try:
            RefreshToken.create(
                id=token_id,
                account_id=account_id,
                token=token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
        except Exception as e:
            print(f"Error storing refresh token: {e}")

        # Optionally store in Redis for faster lookup
        if redis_client:
            try:
                redis_client.setex(
                    f"refresh_token:{token}",
                    AuthConfig.JWT_REFRESH_TOKEN_EXPIRES,
                    account_id
                )
            except Exception as e:
                print(f"Error storing token in Redis: {e}")

        return token

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
        """
        Verify JWT token and return payload
        """
        try:
            payload = jwt.decode(
                token,
                AuthConfig.JWT_SECRET_KEY,
                algorithms=[AuthConfig.JWT_ALGORITHM]
            )
            print("printing payload:", payload)
            if payload.get("type") != token_type:
                return None

            return payload
        except JWTError:
            return None

    @staticmethod
    def authenticate(email: str, password: str) -> Account:
        """
        Authenticate user with email and password
        Raises ValueError if authentication fails
        """
        # Find account by email
        try:
            account = Account.get(Account.email == email)
        except Account.DoesNotExist:
            raise ValueError("Invalid email or password")

        # Check account status
        if account.status == AccountStatus.BANNED.value:
            raise ValueError("Account has been banned")

        if account.status == AccountStatus.PENDING.value:
            raise ValueError("Account is pending activation")

        # Verify password
        if not account.password or not account.password_salt:
            raise ValueError("Password authentication not available for this account")

        if not AuthService.verify_password(password, account.password, account.password_salt):
            raise ValueError("Invalid email or password")

        return account

    @staticmethod
    def login(
        account: Account,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate token pair for logged-in user
        """
        # Update last login time
        account.last_login_at = datetime.now()
        account.last_active_at = datetime.now()
        account.save()

        # Create tokens
        access_token = AuthService.create_access_token(
            account.id,
            account.current_tenant_id
        )
        refresh_token = AuthService.create_refresh_token(
            account.id,
            ip_address,
            user_agent
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": AuthConfig.JWT_ACCESS_TOKEN_EXPIRES
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token
        """
        # Verify refresh token
        payload = AuthService.verify_token(refresh_token, "refresh")
        if not payload:
            raise ValueError("Invalid refresh token")

        account_id = payload.get("sub")
        token_id = payload.get("jti")

        # Check if token exists and is valid in database
        try:
            db_token = RefreshToken.get(RefreshToken.id == token_id)
            if not db_token.is_valid():
                raise ValueError("Refresh token has expired or been revoked")
        except RefreshToken.DoesNotExist:
            raise ValueError("Refresh token not found")

        # Get account
        try:
            account = Account.get(Account.id == account_id)
        except Account.DoesNotExist:
            raise ValueError("Account not found")

        # Check account status
        if not account.is_active():
            raise ValueError("Account is not active")

        # Create new access token
        access_token = AuthService.create_access_token(
            account.id,
            account.current_tenant_id
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": AuthConfig.JWT_ACCESS_TOKEN_EXPIRES
        }

    @staticmethod
    def revoke_refresh_token(token: str):
        """Revoke a refresh token"""
        payload = AuthService.verify_token(token, "refresh")
        if payload:
            token_id = payload.get("jti")
            try:
                db_token = RefreshToken.get(RefreshToken.id == token_id)
                db_token.is_revoked = True
                db_token.save()

                # Remove from Redis if present
                if redis_client:
                    redis_client.delete(f"refresh_token:{token}")
            except RefreshToken.DoesNotExist:
                pass

    @staticmethod
    def register_account(
        email: str,
        password: str,
        name: str,
        create_default_tenant: bool = True
    ) -> Account:
        """
        Register a new account
        """
        # Check if email already exists
        if Account.select().where(Account.email == email).exists():
            raise ValueError("Email already registered")

        # Hash password
        hashed_password, salt = AuthService.hash_password(password)

        # Create account
        account_id = str(uuid.uuid4())
        account = Account.create(
            id=account_id,
            email=email,
            password=hashed_password,
            password_salt=salt,
            name=name,
            status=AccountStatus.ACTIVE.value
        )

        # Create default tenant if requested
        if create_default_tenant:
            from ..db.mysql import Tenant, TenantAccountJoin

            tenant_id = str(uuid.uuid4())
            tenant = Tenant.create(
                id=tenant_id,
                name=f"{name}'s Workspace",
                owner_id=account_id
            )

            # Create tenant-account relationship
            TenantAccountJoin.create(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                account_id=account_id,
                role='owner',
                current=True
            )

            # Set as current tenant
            account.current_tenant_id = tenant_id
            account.save()

        return account

    @staticmethod
    def get_account_by_id(account_id: str) -> Optional[Account]:
        """Get account by ID"""
        try:
            return Account.get(Account.id == account_id)
        except Account.DoesNotExist:
            return None

    @staticmethod
    def get_account_by_email(email: str) -> Optional[Account]:
        """Get account by email"""
        try:
            return Account.get(Account.email == email)
        except Account.DoesNotExist:
            return None
