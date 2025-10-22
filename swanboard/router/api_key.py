#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Key management router for SwanLab-Server
Provides endpoints for creating, listing, and managing platform-level API Keys
"""

from fastapi import APIRouter, Request, Depends
from typing import Dict, Any, List

from ..controller.api_key import (
    create_api_key,
    list_api_keys,
    get_api_key,
    update_api_key,
    revoke_api_key
)
from ..dependencies.auth import validate_api_key_dependency
from ..db.mysql import Account

# ================================== Pydantic Models for API Documentation ==================================

from pydantic import BaseModel, Field
from typing import Optional

class APIKeyCreateRequest(BaseModel):
    """API Key创建请求模型"""
    name: str = Field(..., description="API Key名称", example="My API Key")
    description: Optional[str] = Field(None, description="API Key描述", example="API Key for SwanLab integration")
    scope: str = Field("read_write", description="权限范围: read_only, read_write, admin", example="read_write")
    expires_in_days: Optional[int] = Field(None, description="过期天数（默认永不过期）", example=365)
    rate_limit: int = Field(1000, description="速率限制（请求/小时）", example=1000)

class APIKeyResponse(BaseModel):
    """API Key响应模型"""
    id: str = Field(..., description="API Key ID")
    key_id: str = Field(..., description="API Key公共标识符")
    name: str = Field(..., description="API Key名称")
    description: Optional[str] = Field(None, description="API Key描述")
    scope: str = Field(..., description="权限范围")
    status: str = Field(..., description="状态: active, inactive, revoked")
    rate_limit: int = Field(..., description="速率限制（请求/小时）")
    expires_at: Optional[str] = Field(None, description="过期时间")
    last_used_at: Optional[str] = Field(None, description="最后使用时间")
    usage_count: int = Field(..., description="使用次数")
    created_at: str = Field(..., description="创建时间")

class APIKeyCreateResponse(BaseModel):
    """API Key创建响应模型"""
    api_key: Dict[str, Any] = Field(..., description="API Key信息")
    warning: str = Field(..., description="安全警告")

class APIKeyListResponse(BaseModel):
    """API Key列表响应模型"""
    api_keys: List[APIKeyResponse] = Field(..., description="API Key列表")
    total: int = Field(..., description="总数")

class APIKeyUpdateRequest(BaseModel):
    """API Key更新请求模型"""
    name: Optional[str] = Field(None, description="API Key名称", example="Updated API Key Name")
    description: Optional[str] = Field(None, description="API Key描述", example="Updated description")
    scope: Optional[str] = Field(None, description="权限范围: read_only, read_write, admin", example="read_only")
    status: Optional[str] = Field(None, description="状态: active, inactive, revoked", example="inactive")
    rate_limit: Optional[int] = Field(None, description="速率限制（请求/小时）", example=500)

class APIKeyDetailResponse(BaseModel):
    """API Key详情响应模型"""
    api_key: APIKeyResponse = Field(..., description="API Key详细信息")
    usage_stats: Dict[str, Any] = Field(..., description="使用统计")

class APIKeyRevokeResponse(BaseModel):
    """API Key撤销响应模型"""
    message: str = Field(..., description="撤销消息")
    api_key_id: str = Field(..., description="API Key ID")

# ================================== 路由器初始化 ==================================

router = APIRouter(
    tags=["API Keys"],
    responses={
        401: {"description": "认证失败"},
        403: {"description": "权限不足"},
        404: {"description": "API Key不存在"},
        500: {"description": "服务器内部错误"}
    }
)

# ================================== API Key 管理路由 ==================================

@router.post(
    "/api-keys",
    response_model=APIKeyCreateResponse,
    summary="创建平台级 API Key",
    description="创建新的平台级 API Key，用于程序化访问 SwanLab-Server API"
)
async def create_api_key_route(
    request: Request,
    account: Account = Depends(validate_api_key_dependency)
):
    """
    ## 创建平台级 API Key

    此端点允许用户创建新的平台级 API Key，用于程序化访问 SwanLab-Server API。

    ### 功能特性
    - 生成安全的 API Key 对（key_id 和 key_secret）
    - 支持权限范围控制（read_only, read_write, admin）
    - 可配置过期时间和速率限制
    - 密钥仅显示一次，请妥善保存

    ### 使用场景
    - 为第三方应用提供 API 访问
    - 自动化脚本和 CI/CD 流程
    - 集成到其他系统中

    ### 认证
    需要在 Authorization header 中提供有效的 JWT 令牌
    """
    return await create_api_key(request, account)


@router.get(
    "/api-keys",
    response_model=APIKeyListResponse,
    summary="列出用户的所有 API Keys",
    description="获取当前用户创建的所有平台级 API Keys"
)
async def list_api_keys_route(
    request: Request,
    account: Account = Depends(validate_api_key_dependency)
):
    """
    ## 列出用户的所有 API Keys

    此端点返回当前用户创建的所有平台级 API Keys。

    ### 返回信息
    - API Key 基本信息（不包含密钥）
    - 权限范围和状态
    - 使用统计和最后使用时间

    ### 认证
    需要在 Authorization header 中提供有效的 JWT 令牌
    """
    return await list_api_keys(request, account)


@router.get(
    "/api-keys/{api_key_id}",
    response_model=APIKeyDetailResponse,
    summary="获取 API Key 详细信息",
    description="获取特定 API Key 的详细信息和使用统计"
)
async def get_api_key_route(
    api_key_id: str,
    account: Account = Depends(validate_api_key_dependency)
):
    """
    ## 获取 API Key 详细信息

    此端点返回指定 API Key 的详细信息和使用统计。

    ### 返回信息
    - API Key 完整信息（不包含密钥）
    - 最近使用统计
    - 端点访问记录

    ### 认证
    需要在 Authorization header 中提供有效的 JWT 令牌
    """
    return await get_api_key(api_key_id, account)


@router.patch(
    "/api-keys/{api_key_id}",
    response_model=APIKeyResponse,
    summary="更新 API Key 属性",
    description="更新 API Key 的名称、描述、权限范围、状态或速率限制"
)
async def update_api_key_route(
    api_key_id: str,
    request: Request,
    account: Account = Depends(validate_api_key_dependency)
):
    """
    ## 更新 API Key 属性

    此端点允许更新 API Key 的各种属性。

    ### 可更新属性
    - 名称和描述
    - 权限范围（read_only, read_write, admin）
    - 状态（active, inactive, revoked）
    - 速率限制

    ### 认证
    需要在 Authorization header 中提供有效的 JWT 令牌
    """
    return await update_api_key(api_key_id, request, account)


@router.delete(
    "/api-keys/{api_key_id}",
    response_model=APIKeyRevokeResponse,
    summary="撤销 API Key",
    description="撤销指定的 API Key，使其无法再访问 API"
)
async def revoke_api_key_route(
    api_key_id: str,
    account: Account = Depends(validate_api_key_dependency)
):
    """
    ## 撤销 API Key

    此端点永久撤销指定的 API Key，使其无法再访问 SwanLab-Server API。

    ### 注意事项
    - 撤销操作不可逆
    - 已撤销的 API Key 无法恢复
    - 建议在密钥泄露或不再需要时使用

    ### 认证
    需要在 Authorization header 中提供有效的 JWT 令牌
    """
    return await revoke_api_key(api_key_id, account)
