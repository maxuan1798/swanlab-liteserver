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
    # API Key格式通常是 "key_id:key_secret"
    if ":" in auth_value:
        key_id, key_secret = auth_value.split(":", 1)
        api_key = APIKeyService.validate_api_key(key_id, key_secret)

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


# 创建依赖实例，便于在路由中使用
api_key_auth = Depends(validate_api_key_dependency)
platform_api_key_auth = Depends(validate_platform_api_key_dependency)
