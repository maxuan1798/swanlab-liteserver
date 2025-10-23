#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API认证依赖模块
提供统一的JWT令牌验证和平台级API Key验证依赖函数
"""

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Union
import os

from ..services.auth_service import AuthService
from ..services.api_key_service import APIKeyService
from ..db.mysql import Account
from ..db.mysql.api_key_models import APIKey

security = HTTPBearer()


def validate_api_key_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Account:
    """
    FastAPI依赖函数 - 验证JWT令牌

    此依赖函数可以用于任何需要JWT令牌验证的路由
    使用与登录认证相同的JWT令牌验证逻辑

    Args:
        credentials: HTTPAuthorizationCredentials from HTTPBearer

    Returns:
        Account: 验证成功的用户账户对象

    Raises:
        HTTPException: 认证失败时抛出401或403错误
    """
    # 如果没有提供Authorization头
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    token = credentials.credentials
    print("Received token:", token)
    # 验证JWT令牌
    payload = AuthService.verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取账户
    account_id = payload.get("sub")
    account = AuthService.get_account_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=401,
            detail="Account not found",
        )

    if not account.is_active():
        raise HTTPException(
            status_code=403,
            detail="Account is not active",
        )

    return account


def validate_platform_api_key_dependency(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Union[Account, APIKey]:
    """
    FastAPI依赖函数 - 验证JWT令牌或平台级API Key

    此依赖函数支持两种认证方式：
    1. JWT令牌（用户认证）
    2. 平台级API Key（程序化访问）

    Args:
        request: FastAPI Request object
        credentials: HTTPAuthorizationCredentials from HTTPBearer

    Returns:
        Union[Account, APIKey]: 验证成功的用户账户对象或API Key对象

    Raises:
        HTTPException: 认证失败时抛出401或403错误

    Parameters
    ----------
    request
    credentials
    x_api_key
    """

    auth_value = None

    # 方式1: Authorization Bearer
    if credentials:
        auth_value = credentials.credentials

    # 方式2: X-API-Key Header
    elif x_api_key:
        auth_value = x_api_key

    if not auth_value:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header or X-API-Key"
        )

    # 首先尝试JWT令牌验证
    payload = AuthService.verify_token(auth_value, "access")
    if payload:
        # JWT令牌验证成功
        account_id = payload.get("sub")
        account = AuthService.get_account_by_id(account_id)

        if not account:
            raise HTTPException(
                status_code=401,
                detail="Account not found",
            )

        if not account.is_active():
            raise HTTPException(
                status_code=403,
                detail="Account is not active",
            )

        return account

    # 如果不是JWT令牌，尝试API Key验证
    # 支持两种格式: "key_id:key_secret" 和单字符串格式
    api_key = None

    if ":" in auth_value:
        # Legacy format: key_id:key_secret
        key_id, key_secret = auth_value.split(":", 1)
        api_key = APIKeyService.validate_api_key(key_id, key_secret)
    else:
        # Single-string format: treat the entire string as key_secret and find matching API key
        all_api_keys = APIKey.select()
        for candidate_key in all_api_keys:
            if APIKeyService.verify_key_secret(auth_value, candidate_key.key_secret_hash, candidate_key.key_secret_salt):
                api_key = candidate_key
                break

    if api_key:
        # 检查速率限制
        if not APIKeyService.check_rate_limit(api_key.id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )

        # 记录使用情况
        APIKeyService.log_usage(
            api_key_id=api_key.id,
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        # 更新API Key的使用统计
        api_key.update_usage(request.client.host if request.client else None)

        return api_key

    # 两种认证方式都失败
    raise HTTPException(
        status_code=401,
        detail="Invalid or expired token/API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


def validate_x_api_key_only_dependency(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key")
) -> APIKey:
    """
    FastAPI依赖函数 - 仅验证平台级API Key（通过X-API-Key header）

    此依赖函数仅支持 X-API-Key header 认证，不接受 JWT token
    专门用于 Cloud API 端点的认证

    Args:
        request: FastAPI Request object
        x_api_key: API Key from X-API-Key header (single string format)

    Returns:
        APIKey: 验证成功的 API Key 对象

    Raises:
        HTTPException: 认证失败时抛出401或403错误
    """
    print("Received X-API-Key:", x_api_key)
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "X-API-Key"}
        )

    # Handle both single-string API keys and legacy key_id:key_secret format
    if ":" in x_api_key:
        # Legacy format: key_id:key_secret
        key_id, key_secret = x_api_key.split(":", 1)
        api_key = APIKeyService.validate_api_key(key_id, key_secret)
    else:
        # Single-string format: treat the entire string as key_secret and find matching API key
        # This assumes the API key is stored with a known key_id or we need to search for it
        api_key = None

        # Try to find API key by treating the single string as key_secret
        # This is a simplified approach - in production you might want a more robust lookup
        all_api_keys = APIKey.select()
        for candidate_key in all_api_keys:
            if APIKeyService.verify_key_secret(x_api_key, candidate_key.key_secret_hash, candidate_key.key_secret_salt):
                api_key = candidate_key
                break

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "X-API-Key"}
        )

    # 检查速率限制
    if not APIKeyService.check_rate_limit(api_key.id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    # 记录使用情况
    APIKeyService.log_usage(
        api_key_id=api_key.id,
        endpoint=str(request.url.path),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # 更新API Key的使用统计
    api_key.update_usage(request.client.host if request.client else None)

    return api_key


# 创建依赖实例，便于在路由中使用
api_key_auth = Depends(validate_api_key_dependency)
platform_api_key_auth = Depends(validate_platform_api_key_dependency)
x_api_key_only_auth = Depends(validate_x_api_key_only_dependency)
