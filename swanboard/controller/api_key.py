#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Key management controller for SwanLab-Server
Provides endpoints for creating, listing, and managing platform-level API Keys
"""

from typing import Dict, Any, List, Optional
from fastapi import Request, HTTPException, Depends

from ..services.api_key_service import APIKeyService
from ..db.mysql.api_key_models import APIKey, APIKeyStatus, APIKeyScope
from ..db.mysql.auth_models import Account

# 认证依赖
from ..dependencies.auth import validate_api_key_dependency

# 响应模块
from ..module.resp import (
    SUCCESS_200, DATA_ERROR_500, BAD_REQUEST_400,
    NOT_FOUND_404, UNAUTHORIZED_401
)

# 工具函数
from ..utils import swanlog


# ================================== API Key 管理API ==================================

async def create_api_key(request: Request, account: Account = Depends(validate_api_key_dependency)) -> Dict[str, Any]:
    """
    创建新的平台级 API Key

    POST /api/v1/api-keys

    Body:
    {
        "name": "My API Key",
        "description": "API Key for SwanLab integration",
        "scope": "read_write",  # read_only, read_write, admin
        "expires_in_days": 365,  # 可选，默认永不过期
        "rate_limit": 1000  # 可选，默认1000请求/小时
    }

    Returns:
        API Key信息，包括key_secret（仅显示一次）
    """
    try:
        body = await request.json()

        # 必需字段验证
        required_fields = ['name']
        for field in required_fields:
            if field not in body:
                return BAD_REQUEST_400(f"Missing required field: {field}")

        name = body['name']
        description = body.get('description')
        scope_str = body.get('scope', 'read_write')
        expires_in_days = body.get('expires_in_days')
        rate_limit = body.get('rate_limit', 1000)

        # 验证scope
        try:
            scope = APIKeyScope(scope_str)
        except ValueError:
            return BAD_REQUEST_400(f"Invalid scope: {scope_str}. Must be one of: read_only, read_write, admin")

        # 创建API Key
        api_key_info = APIKeyService.create_api_key(
            name=name,
            description=description,
            scope=scope,
            owner_id=account.id,
            expires_in_days=expires_in_days,
            rate_limit=rate_limit
        )

        swanlog.info(f"Created API Key: {api_key_info['key_id']} for user: {account.email}")

        return SUCCESS_200({
            "api_key": api_key_info,
            "warning": "Store the key_secret securely as it will only be shown once!"
        })

    except Exception as e:
        swanlog.error(f"API Key creation error: {e}")
        return DATA_ERROR_500(f"API Key creation failed: {e}")


async def list_api_keys(request: Request, account: Account = Depends(validate_api_key_dependency)) -> Dict[str, Any]:
    """
    列出用户的所有 API Keys

    GET /api/v1/api-keys

    Returns:
        API Key列表（不包含key_secret）
    """
    try:
        # 获取用户的API Keys
        api_keys = APIKeyService.list_api_keys(owner_id=account.id)

        # 转换为响应格式
        api_keys_list = []
        for api_key in api_keys:
            api_keys_list.append({
                "id": api_key.id,
                "key_id": api_key.key_id,
                "name": api_key.name,
                "description": api_key.description,
                "scope": api_key.scope,
                "status": api_key.status,
                "rate_limit": api_key.rate_limit,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                "usage_count": api_key.usage_count,
                "created_at": api_key.created_at.isoformat()
            })

        return SUCCESS_200({
            "api_keys": api_keys_list,
            "total": len(api_keys_list)
        })

    except Exception as e:
        swanlog.error(f"List API Keys error: {e}")
        return DATA_ERROR_500(f"Failed to list API Keys: {e}")


async def get_api_key(api_key_id: str, account: Account = Depends(validate_api_key_dependency)) -> Dict[str, Any]:
    """
    获取特定 API Key 的详细信息

    GET /api/v1/api-keys/{api_key_id}

    Returns:
        API Key详细信息（不包含key_secret）
    """
    try:
        # 获取API Key
        api_key = APIKeyService.get_api_key_by_id(api_key_id)

        if not api_key:
            return NOT_FOUND_404(f"API Key with id {api_key_id} not found")

        # 检查权限
        if api_key.owner_id != account.id:
            return UNAUTHORIZED_401("You don't have permission to access this API Key")

        # 获取使用统计
        usage_stats = APIKeyService.get_usage_stats(api_key_id)

        return SUCCESS_200({
            "api_key": {
                "id": api_key.id,
                "key_id": api_key.key_id,
                "name": api_key.name,
                "description": api_key.description,
                "scope": api_key.scope,
                "status": api_key.status,
                "rate_limit": api_key.rate_limit,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                "usage_count": api_key.usage_count,
                "created_at": api_key.created_at.isoformat()
            },
            "usage_stats": usage_stats
        })

    except Exception as e:
        swanlog.error(f"Get API Key error: {e}")
        return DATA_ERROR_500(f"Failed to get API Key: {e}")


async def update_api_key(api_key_id: str, request: Request, account: Account = Depends(validate_api_key_dependency)) -> Dict[str, Any]:
    """
    更新 API Key 属性

    PATCH /api/v1/api-keys/{api_key_id}

    Body:
    {
        "name": "Updated Name",
        "description": "Updated description",
        "scope": "read_only",
        "status": "inactive",
        "rate_limit": 500
    }

    Returns:
        更新后的API Key信息
    """
    try:
        body = await request.json()

        # 获取API Key
        api_key = APIKeyService.get_api_key_by_id(api_key_id)

        if not api_key:
            return NOT_FOUND_404(f"API Key with id {api_key_id} not found")

        # 检查权限
        if api_key.owner_id != account.id:
            return UNAUTHORIZED_401("You don't have permission to update this API Key")

        # 解析更新字段
        name = body.get('name')
        description = body.get('description')
        scope_str = body.get('scope')
        status_str = body.get('status')
        rate_limit = body.get('rate_limit')

        # 验证scope
        scope = None
        if scope_str:
            try:
                scope = APIKeyScope(scope_str)
            except ValueError:
                return BAD_REQUEST_400(f"Invalid scope: {scope_str}. Must be one of: read_only, read_write, admin")

        # 验证status
        status = None
        if status_str:
            try:
                status = APIKeyStatus(status_str)
            except ValueError:
                return BAD_REQUEST_400(f"Invalid status: {status_str}. Must be one of: active, inactive, revoked")

        # 更新API Key
        updated_api_key = APIKeyService.update_api_key(
            api_key_id=api_key_id,
            name=name,
            description=description,
            scope=scope,
            status=status,
            rate_limit=rate_limit
        )

        if not updated_api_key:
            return DATA_ERROR_500("Failed to update API Key")

        return SUCCESS_200({
            "api_key": {
                "id": updated_api_key.id,
                "key_id": updated_api_key.key_id,
                "name": updated_api_key.name,
                "description": updated_api_key.description,
                "scope": updated_api_key.scope,
                "status": updated_api_key.status,
                "rate_limit": updated_api_key.rate_limit,
                "expires_at": updated_api_key.expires_at.isoformat() if updated_api_key.expires_at else None,
                "last_used_at": updated_api_key.last_used_at.isoformat() if updated_api_key.last_used_at else None,
                "usage_count": updated_api_key.usage_count,
                "created_at": updated_api_key.created_at.isoformat()
            }
        })

    except Exception as e:
        swanlog.error(f"Update API Key error: {e}")
        return DATA_ERROR_500(f"Failed to update API Key: {e}")


async def revoke_api_key(api_key_id: str, account: Account = Depends(validate_api_key_dependency)) -> Dict[str, Any]:
    """
    撤销 API Key

    DELETE /api/v1/api-keys/{api_key_id}

    Returns:
        撤销结果
    """
    try:
        # 获取API Key
        api_key = APIKeyService.get_api_key_by_id(api_key_id)

        if not api_key:
            return NOT_FOUND_404(f"API Key with id {api_key_id} not found")

        # 检查权限
        if api_key.owner_id != account.id:
            return UNAUTHORIZED_401("You don't have permission to revoke this API Key")

        # 撤销API Key
        success = APIKeyService.revoke_api_key(api_key_id)

        if not success:
            return DATA_ERROR_500("Failed to revoke API Key")

        swanlog.info(f"Revoked API Key: {api_key.key_id} for user: {account.email}")

        return SUCCESS_200({
            "message": "API Key revoked successfully",
            "api_key_id": api_key_id
        })

    except Exception as e:
        swanlog.error(f"Revoke API Key error: {e}")
        return DATA_ERROR_500(f"Failed to revoke API Key: {e}")