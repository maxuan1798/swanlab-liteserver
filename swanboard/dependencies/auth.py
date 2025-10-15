#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API认证依赖模块
提供统一的JWT令牌验证依赖函数
"""

from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

from ..services.auth_service import AuthService
from ..db.mysql import Account

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


# 创建依赖实例，便于在路由中使用
api_key_auth = Depends(validate_api_key_dependency)