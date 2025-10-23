#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@DATE: 2024-11-26 16:50:00
@File: swanboard/router/cloud.py
@IDE: vscode
@Description:
    云端API路由 - 支持EnhancedSwanBoardCallback的HTTP通信
"""

from fastapi import APIRouter, Request, Header, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import os
import io

from ..controller.cloud import (
    sync_project,
    sync_experiment,
    sync_column,
    update_experiment_status,
    sync_runtime_info,
    get_runtime_info,
    get_workspace_projects,
    get_project_experiments,
    get_workspaces
)
from ..dependencies.auth import validate_x_api_key_only_dependency
from ..db.mysql.api_key_models import APIKey

from swanboard.cloud_api.cloud_service import CloudSyncManager
from swanboard.utils import swanlog

# ================================== Pydantic Models for API Documentation ==================================

class ProjectSyncRequest(BaseModel):
    """项目同步请求模型"""
    name: str = Field(..., description="项目名称", example="my-ml-project")
    workspace: str = Field(..., description="工作空间名称", example="default")
    description: Optional[str] = Field(None, description="项目描述", example="A machine learning project for image classification")

class ProjectSyncResponse(BaseModel):
    """项目同步响应模型"""
    success: bool = Field(..., description="是否成功")
    project_id: str = Field(..., description="项目ID", example="1")
    name: str = Field(..., description="项目名称")
    workspace: str = Field(..., description="工作空间名称")
    message: Optional[str] = Field(None, description="消息")

class ExperimentSyncRequest(BaseModel):
    """实验同步请求模型"""
    run_id: str = Field(..., description="运行ID", example="run_20241126_001")
    name: str = Field(..., description="实验名称", example="baseline-model")
    description: Optional[str] = Field(None, description="实验描述", example="Baseline model with default parameters")
    colors: Optional[List[str]] = Field(None, description="实验颜色", example=["#FF6B6B", "#4ECDC4"])
    project_id: str = Field(..., description="项目ID", example="1")
    workspace: str = Field(..., description="工作空间名称", example="default")

class ExperimentSyncResponse(BaseModel):
    """实验同步响应模型"""
    success: bool = Field(..., description="是否成功")
    experiment_id: str = Field(..., description="实验ID", example="1")
    run_id: str = Field(..., description="运行ID")
    name: str = Field(..., description="实验名称")
    message: Optional[str] = Field(None, description="消息")

class ExperimentStatusRequest(BaseModel):
    """实验状态更新请求模型"""
    status: int = Field(..., description="实验状态: -1=崩溃, 0=运行中, 1=已完成", example=1)

class ColumnSyncRequest(BaseModel):
    """列/指标同步请求模型"""
    key: str = Field(..., description="指标键名", example="loss")
    experiment_id: str = Field(..., description="实验ID", example="1")
    chart_type: str = Field(..., description="图表类型", example="line")
    reference: str = Field(..., description="参考轴", example="step")
    section_name: Optional[str] = Field("default", description="章节名称")
    section_sort: Optional[int] = Field(0, description="章节排序")
    kid: Optional[str] = Field(None, description="子键ID", example="loss_folder")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态", example="healthy")
    timestamp: str = Field(..., description="时间戳")
    database: Dict[str, Any] = Field(..., description="数据库状态")
    api_version: str = Field(..., description="API版本", example="v1")

class APIInfo(BaseModel):
    """API信息模型"""
    name: str = Field(..., description="API名称", example="SwanLab Cloud API")
    version: str = Field(..., description="API版本", example="1.0.0")
    description: str = Field(..., description="API描述")
    endpoints: Dict[str, Dict[str, str]] = Field(..., description="端点信息")
    authentication: Dict[str, str] = Field(..., description="认证信息")

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误信息")
    code: Optional[int] = Field(None, description="错误代码")

class RuntimeInfoSyncRequest(BaseModel):
    """运行时信息同步请求模型"""
    experiment_id: str = Field(..., description="实验ID", example="1")
    requirements: Optional[str] = Field(None, description="requirements.txt内容", example="numpy==1.21.0\npandas==1.3.0")
    metadata: Optional[str] = Field(None, description="metadata JSON内容", example='{"python_version": "3.8.10"}')
    config: Optional[str] = Field(None, description="config YAML内容", example="epochs: 100\nlearning_rate: 0.001")
    conda: Optional[str] = Field(None, description="conda environment YAML内容", example="name: myenv\ndependencies:\n  - python=3.8")

class RuntimeInfoSyncResponse(BaseModel):
    """运行时信息同步响应模型"""
    success: bool = Field(..., description="是否成功")
    runtime_info_id: str = Field(..., description="运行时信息ID", example="1")
    experiment_id: str = Field(..., description="实验ID", example="1")
    synced_fields: Dict[str, bool] = Field(..., description="已同步的字段")

# ================================== 路由器初始化 ==================================

router = APIRouter(
    tags=["Cloud API"],
    responses={
        401: {"model": ErrorResponse, "description": "认证失败"},
        403: {"model": ErrorResponse, "description": "权限不足"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)

# Singleton CloudSyncManager for the router. Workspace & user come from env.
_cloud_workspace = os.getenv('SWANLAB_WORKSPACE', 'default')
_cloud_user = os.getenv('SWANLAB_CLOUD_USER', 'system')
_manager = CloudSyncManager(workspace=_cloud_workspace, user=_cloud_user)

# API key check dependency (使用集中化的依赖)


# ================================== 项目相关路由 ==================================

@router.post(
    "/projects",
    response_model=ProjectSyncResponse,
    summary="同步项目到云端",
    description="创建或同步机器学习项目到云端存储，支持EnhancedSwanBoardCallback的项目同步功能",
    responses={
        200: {"model": ProjectSyncResponse, "description": "项目同步成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
    }
)
async def create_or_sync_project(
    project_data: ProjectSyncRequest,
    request: Request,
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """
    ## 同步项目到云端

    此端点允许EnhancedSwanBoardCallback将机器学习项目信息同步到云端存储。

    ### 功能特性
    - 自动创建新项目或更新现有项目
    - 支持工作空间组织
    - 项目描述和元数据存储

    ### 使用场景
    - 训练开始时创建项目记录
    - 更新项目描述和配置
    - 组织管理机器学习项目

    ### 认证
    需要在 X-API-Key header 中提供有效的 API 密钥（格式：key_id:key_secret）
    """
    return await sync_project(request, auth)


# ================================== 实验相关路由 ==================================

@router.post(
    "/experiments",
    response_model=ExperimentSyncResponse,
    summary="同步实验到云端",
    description="创建或同步机器学习实验到云端存储，支持EnhancedSwanBoardCallback的实验同步功能",
    responses={
        200: {"model": ExperimentSyncResponse, "description": "实验同步成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
    }
)
async def create_or_sync_experiment(
    experiment_data: ExperimentSyncRequest,
    request: Request,
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """
    ## 同步实验到云端

    此端点允许EnhancedSwanBoardCallback将机器学习实验信息同步到云端存储。

    ### 功能特性
    - 自动创建新实验或更新现有实验
    - 支持实验元数据和配置
    - 实验状态追踪和可视化颜色设置

    ### 使用场景
    - 训练开始时创建实验记录
    - 更新实验配置和描述
    - 关联实验到特定项目

    ### 认证
    需要在 X-API-Key header 中提供有效的 API 密钥（格式：key_id:key_secret）
    """
    return await sync_experiment(request, auth)


@router.put(
    "/experiments/{experiment_id}/status",
    summary="更新实验状态",
    description="更新机器学习实验的运行状态，支持EnhancedSwanBoardCallback的状态同步功能",
    responses={
        200: {"description": "实验状态更新成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        404: {"model": ErrorResponse, "description": "实验不存在"},
    }
)
async def update_experiment_status_route(
    experiment_id: str,
    status_data: ExperimentStatusRequest,
    request: Request,
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """
    ## 更新实验状态

    此端点允许EnhancedSwanBoardCallback更新实验的运行状态。

    ### 状态说明
    - `-1`: 实验崩溃/失败
    - `0`: 实验正在运行
    - `1`: 实验已完成

    ### 使用场景
    - 训练开始时设置为运行状态
    - 训练完成时标记为完成
    - 训练出错时标记为失败

    ### 认证
    需要在 X-API-Key header 中提供有效的 API 密钥（格式：key_id:key_secret）
    """
    return await update_experiment_status(experiment_id, request, auth)


# ================================== 运行时信息相关路由 ==================================

@router.post(
    "/runtime-info",
    response_model=RuntimeInfoSyncResponse,
    summary="同步运行时信息到云端",
    description="同步机器学习实验的运行时信息到云端存储，包括requirements、metadata、config和conda环境",
    responses={
        200: {"model": RuntimeInfoSyncResponse, "description": "运行时信息同步成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        404: {"model": ErrorResponse, "description": "实验不存在"},
    }
)
async def sync_runtime_info_route(
    runtime_data: RuntimeInfoSyncRequest,
    request: Request,
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """
    ## 同步运行时信息到云端

    此端点允许EnhancedSwanBoardCallback将实验运行时信息同步到云端存储。

    ### 功能特性
    - 同步requirements.txt内容
    - 同步metadata JSON信息
    - 同步config YAML配置
    - 同步conda环境配置

    ### 使用场景
    - 训练开始时记录环境信息
    - 更新实验配置文件
    - 保存依赖包版本信息

    ### 认证
    需要在 X-API-Key header 中提供有效的 API 密钥（格式：key_id:key_secret）
    """
    return await sync_runtime_info(request, auth)


@router.get(
    "/experiments/{experiment_id}/runtime-info",
    summary="获取实验运行时信息",
    description="获取指定实验的运行时信息，包括requirements、metadata、config和conda环境",
    responses={
        200: {"description": "运行时信息获取成功"},
        404: {"model": ErrorResponse, "description": "实验或运行时信息不存在"},
    }
)
async def get_runtime_info_route(
    experiment_id: str,
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """
    ## 获取实验运行时信息

    此端点允许获取指定实验的完整运行时信息。

    ### 返回信息
    - requirements.txt内容
    - metadata JSON信息
    - config YAML配置
    - conda环境配置

    ### 使用场景
    - 查看实验环境配置
    - 复现实验环境
    - 分析依赖包版本

    ### 认证
    需要在 X-API-Key header 中提供有效的 API 密钥（格式：key_id:key_secret）
    """
    return await get_runtime_info(experiment_id, auth)


# ================================== 列/指标相关路由 ==================================

@router.post(
    "/columns",
    summary="同步指标列到云端",
    description="创建或同步机器学习实验指标列到云端存储，支持EnhancedSwanBoardCallback的指标同步功能",
    responses={
        200: {"description": "指标列同步成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
    }
)
async def create_or_sync_column(
    column_data: ColumnSyncRequest,
    request: Request,
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """
    ## 同步指标列到云端

    此端点允许EnhancedSwanBoardCallback将实验指标列信息同步到云端存储。

    ### 功能特性
    - 自动创建新指标列或更新现有列
    - 支持多种图表类型（line, scatter, bar等）
    - 指标分组和章节管理
    - 错误信息记录和追踪

    ### 使用场景
    - 首次记录指标时创建列定义
    - 更新指标的可视化设置
    - 记录数据类型错误和异常

    ### 认证
    需要在 X-API-Key header 中提供有效的 API 密钥（格式：key_id:key_secret）
    """
    return await sync_column(request, auth)


# ================================== 查询相关路由 ==================================

@router.get("/workspaces")
async def list_workspaces():
    """
    获取所有工作空间列表

    Returns:
        工作空间列表
    """
    return get_workspaces()


@router.get("/workspaces/{workspace}/projects")
async def list_workspace_projects(
    workspace: str
):
    """
    获取工作空间下的所有项目

    Returns:
        项目列表
    """
    return get_workspace_projects(workspace)


@router.get("/projects/{project_id}/experiments")
async def list_project_experiments(
    project_id: str
):
    """
    获取项目下的所有实验

    Returns:
        实验列表
    """
    return get_project_experiments(project_id)


# ================================== 健康检查 ==================================

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="云端API健康检查",
    description="检查SwanLab Cloud API服务的健康状态，包括数据库连接状态",
    tags=["Health Check"]
)
async def health_check():
    """
    ## 云端API健康检查

    检查SwanLab Cloud API服务的整体健康状态。

    ### 检查项目
    - API服务状态
    - MySQL 数据库连接状态
    - ClickHouse 数据库连接状态

    ### 返回状态
    - `healthy`: 所有服务正常运行
    - `unhealthy`: 存在服务异常

    ### 无需认证
    此端点不需要API密钥，可用于监控和健康检查
    """
    from ..db.mysql import mysql_manager
    from ..db.clickhouse import clickhouse_manager
    from datetime import datetime

    try:
        # 检查 MySQL 连接
        mysql_connected = mysql_manager.is_connected()

        # 检查 ClickHouse 连接
        clickhouse_connected = clickhouse_manager.is_connected()

        # 判断整体健康状态
        overall_status = "healthy" if (mysql_connected and clickhouse_connected) else "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "database": {
                "mysql": {
                    "available": mysql_connected,
                    "host": mysql_manager.host if hasattr(mysql_manager, 'host') else "unknown"
                },
                "clickhouse": {
                    "available": clickhouse_connected,
                    "host": clickhouse_manager.host if hasattr(clickhouse_manager, 'host') else "unknown"
                }
            },
            "api_version": "v1"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ================================== API信息 ==================================

@router.get(
    "/info",
    response_model=APIInfo,
    summary="获取云端API信息",
    description="获取SwanLab Cloud API的版本信息、端点列表和认证说明",
    tags=["API Information"]
)
async def api_info():
    """
    ## 获取云端API信息

    提供SwanLab Cloud API的完整信息，包括版本、端点和认证方式。

    ### 包含信息
    - API名称和版本
    - 可用端点列表
    - 认证方式说明
    - 环境变量配置指南

    ### 无需认证
    此端点不需要API密钥，可用于API发现和文档
    """
    return {
        "name": "SwanLab Cloud API",
        "version": "1.0.0",
        "description": "HTTP API for EnhancedSwanBoardCallback cloud sync",
        "endpoints": {
            "projects": {
                "POST /projects": "Sync project to cloud",
                "GET /workspaces/{workspace}/projects": "List workspace projects"
            },
            "experiments": {
                "POST /experiments": "Sync experiment to cloud",
                "PUT /experiments/{id}/status": "Update experiment status",
                "GET /projects/{id}/experiments": "List project experiments"
            },
            "runtime_info": {
                "POST /runtime-info": "Sync runtime info to cloud",
                "GET /experiments/{id}/runtime-info": "Get experiment runtime info"
            },
            "columns": {
                "POST /columns": "Sync column/metric to cloud"
            },
            "utils": {
                "GET /health": "Health check",
                "GET /info": "API information"
            }
        },
        "authentication": {
            "type": "X-API-Key",
            "header": "X-API-Key",
            "format": "key_id:key_secret",
            "example": "sk_abc123:secret_xyz789",
            "env_var": "SWANLAB_API_KEY",
            "note": "Create API keys from the web dashboard: Settings > API Keys"
        }
    }

# ================================== MinIO 相关路由 ==================================

# Singleton CloudSyncManager for the router. Workspace & user come from env.
_cloud_workspace = os.getenv('SWANLAB_WORKSPACE', 'default')
_cloud_user = os.getenv('SWANLAB_CLOUD_USER', 'system')
_manager = CloudSyncManager(workspace=_cloud_workspace, user=_cloud_user)

@router.get(
    path='/minio/config',
    summary="获取MinIO配置",
    description="返回服务器端MinIO配置（不包含密钥）",
    tags=["MinIO"])
async def minio_config():
    """Return server-side MinIO configuration (no secrets)."""
    try:
        cfg = _manager.get_minio_config()
        return JSONResponse(content={"code": 0, "message": "success", "data": cfg})
    except Exception as e:
        swanlog.error(f"minio_config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/minio/upload')
async def minio_upload(
    request: Request,
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """Upload a file (multipart) and proxy it to server MinIO implementation.

    Expects multipart form with fields:
      - object_key: destination key in bucket
      - file: file to upload
    """
    try:
        form = await request.form()
        object_key = form.get('object_key')
        upload = form.get('file')

        if not object_key:
            raise HTTPException(status_code=400, detail='Missing object_key')
        if not upload:
            raise HTTPException(status_code=400, detail='Missing file')

        # `upload` is an UploadFile-like object at runtime; read bytes
        body = await upload.read()
        content_type = getattr(upload, 'content_type', None)
        ok = _manager.upload_media_bytes(object_key=object_key, file_bytes=body, content_type=content_type)
        if ok:
            return JSONResponse(content={"code": 0, "message": "uploaded", "data": {"object_key": object_key}})
        else:
            raise HTTPException(status_code=500, detail='Upload failed on server')
    except HTTPException:
        raise
    except Exception as e:
        swanlog.error(f"minio_upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/minio/download')
async def minio_download(
    object_key: str = Query(...),
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """Download object bytes proxied from server MinIO. Returns raw bytes."""
    try:
        bio = _manager.download_media_bytes(object_key)
        if not bio:
            raise HTTPException(status_code=404, detail='Object not found')
        # Attempt to guess content-type is not done here; return octet-stream
        return StreamingResponse(io.BytesIO(bio.getvalue()), media_type='application/octet-stream')
    except HTTPException:
        raise
    except Exception as e:
        swanlog.error(f"minio_download error for key {object_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/minio/presign')
async def minio_presign(
    object_key: str = Query(...),
    expiration: int = Query(3600),
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """Return a presigned URL for the given object (if supported by server).

    Response: {"code":0, "message":"success", "data": {"url": "..."}}
    """
    try:
        url = _manager.generate_presigned_url(object_key, expiration)
        if not url:
            raise HTTPException(status_code=404, detail='Presign not available')
        return JSONResponse(content={"code": 0, "message": "success", "data": {"url": url}})
    except HTTPException:
        raise
    except Exception as e:
        swanlog.error(f"minio_presign error for key {object_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/minio/delete')
async def minio_delete(
    object_key: str = Query(...),
    auth: APIKey = Depends(validate_x_api_key_only_dependency)
):
    """Delete object from server MinIO.

    Response: {"code":0, "message":"success", "data": {"deleted": true}}
    """
    try:
        ok = _manager.delete_media_file(object_key)
        if ok:
            return JSONResponse(content={"code": 0, "message": "deleted", "data": {"deleted": True, "object_key": object_key}})
        else:
            raise HTTPException(status_code=404, detail='Object not found or delete failed')
    except HTTPException:
        raise
    except Exception as e:
        swanlog.error(f"minio_delete error for key {object_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
