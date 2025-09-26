#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@DATE: 2024-11-26 16:50:00
@File: swanboard/router/cloud.py
@IDE: vscode
@Description:
    云端API路由 - 支持EnhancedSwanBoardCallback的HTTP通信
"""

from fastapi import APIRouter, Request, Header
from typing import Optional

from ..controller.cloud import (
    sync_project,
    sync_experiment,
    sync_column,
    update_experiment_status,
    get_workspace_projects,
    get_project_experiments
)

router = APIRouter()


# ================================== 项目相关路由 ==================================

@router.post("/projects")
async def create_or_sync_project(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    同步项目到云端

    支持EnhancedSwanBoardCallback的项目同步功能

    Body:
    {
        "name": "project_name",
        "workspace": "workspace_name",
        "description": "project description"
    }

    Returns:
        项目ID和相关信息
    """
    return await sync_project(request, authorization)


# ================================== 实验相关路由 ==================================

@router.post("/experiments")
async def create_or_sync_experiment(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    同步实验到云端

    支持EnhancedSwanBoardCallback的实验同步功能

    Body:
    {
        "run_id": "run_20241126_001",
        "name": "experiment_name",
        "description": "experiment description",
        "colors": ["#FF6B6B", "#4ECDC4"],
        "project_id": "1",
        "workspace": "workspace_name"
    }

    Returns:
        实验ID和相关信息
    """
    return await sync_experiment(request, authorization)


@router.put("/experiments/{experiment_id}/status")
async def update_experiment_status_route(
    experiment_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    更新实验状态

    支持EnhancedSwanBoardCallback的状态同步功能

    Body:
    {
        "status": 1  // -1: crashed, 0: running, 1: finished
    }

    Returns:
        更新结果
    """
    return await update_experiment_status(experiment_id, request, authorization)


# ================================== 列/指标相关路由 ==================================

@router.post("/columns")
async def create_or_sync_column(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    同步列/指标到云端

    支持EnhancedSwanBoardCallback的指标同步功能

    Body:
    {
        "key": "loss",
        "experiment_id": "1",
        "chart_type": "line",
        "reference": "step",
        "section_name": "default",
        "section_sort": 0,
        "kid": "loss_folder",
        "error": {
            "data_class": "str",
            "expected": "float"
        }
    }

    Returns:
        列ID和相关信息
    """
    return await sync_column(request, authorization)


# ================================== 查询相关路由 ==================================

@router.get("/workspaces/{workspace}/projects")
async def list_workspace_projects(
    workspace: str,
    authorization: Optional[str] = Header(None)
):
    """
    获取工作空间下的所有项目

    Returns:
        项目列表
    """
    return await get_workspace_projects(workspace, authorization)


@router.get("/projects/{project_id}/experiments")
async def list_project_experiments(
    project_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    获取项目下的所有实验

    Returns:
        实验列表
    """
    return await get_project_experiments(project_id, authorization)


# ================================== 健康检查 ==================================

@router.get("/health")
async def health_check():
    """
    云端API健康检查

    Returns:
        服务状态
    """
    from ..utils import get_swanlog_dir
    from ..db import connect
    import os

    try:
        # 检查数据库连接
        db_path = get_swanlog_dir()
        db_available = os.path.exists(db_path)

        if db_available:
            connect(autocreate=False, path=db_path)

        return {
            "status": "healthy",
            "timestamp": "2024-11-26T16:50:00Z",
            "database": {
                "available": db_available,
                "path": db_path
            },
            "api_version": "v1"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-11-26T16:50:00Z"
        }


# ================================== API信息 ==================================

@router.get("/info")
async def api_info():
    """
    获取云端API信息

    Returns:
        API版本和功能信息
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
            "columns": {
                "POST /columns": "Sync column/metric to cloud"
            },
            "utils": {
                "GET /health": "Health check",
                "GET /info": "API information"
            }
        },
        "authentication": {
            "type": "Bearer Token",
            "header": "Authorization",
            "format": "Bearer {token}",
            "env_var": "SWANLAB_API_KEY"
        }
    }