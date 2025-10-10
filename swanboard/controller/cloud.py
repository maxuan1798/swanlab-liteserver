#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@DATE: 2024-11-26 16:45:00
@File: swanboard/controller/cloud.py
@IDE: vscode
@Description:
    云端API控制器 - 使用CloudSyncManager统一处理逻辑
    支持EnhancedSwanBoardCallback的HTTP通信
"""

import os
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Header

# 使用CloudSyncManager处理业务逻辑
from ..cloud_api import CloudSyncManager
from ..repositories import connection_manager

# 响应模块
from ..module.resp import (
    SUCCESS_200, DATA_ERROR_500, BAD_REQUEST_400,
    NOT_FOUND_404, UNAUTHORIZED_401
)

# 工具函数
from ..utils import swanlog


# ================================== 项目相关API ==================================

async def sync_project(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    同步项目到云端数据库

    POST /api/v1/cloud/projects

    Body:
    {
        "name": "project_name",
        "workspace": "workspace_name",
        "description": "project description"
    }

    Returns:
        项目ID和相关信息
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = await request.json()

        # 必需字段验证
        required_fields = ['name', 'workspace']
        for field in required_fields:
            if field not in body:
                return BAD_REQUEST_400(f"Missing required field: {field}")

        project_name = body['name']
        workspace = body['workspace']
        description = body.get('description', '')

        swanlog.info(f"project name: {project_name}")
        swanlog.info(f"workspace: {workspace}")

        # 验证工作空间
        if not connection_manager.validate_workspace(workspace):
            return UNAUTHORIZED_401(f"Workspace '{workspace}' not allowed")

        swanlog.info("Validated workspace successfully")

        # 创建CloudSyncManager实例
        sync_manager = CloudSyncManager(
            workspace=workspace,
            user=os.getenv('SWANLAB_USER', 'unknown')
        )

        # 使用CloudSyncManager同步项目
        project_id = sync_manager.sync_project(
            name=project_name,
            description=description
        )

        if not project_id:
            return DATA_ERROR_500("Failed to sync project")

        # 获取项目信息以构建响应
        from ..repositories import project_repository
        project = project_repository.get_by_name_and_workspace(project_name, workspace)
        if not project:
            return DATA_ERROR_500("Project sync succeeded but cannot retrieve project")

        return SUCCESS_200({
            "id": project_id,
            "project_id": project_id,
            "name": project.name,
            "description": project.description,
            "workspace": workspace,
            "existed": True  # CloudSyncManager会处理存在性逻辑
        })

    except Exception as e:
        swanlog.error(f"Project sync error: {e}")
        return DATA_ERROR_500(f"Project sync failed: {e}")



# ================================== 实验相关API ==================================

async def sync_experiment(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    同步实验到云端数据库

    POST /api/v1/cloud/experiments

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
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = await request.json()

        # 必需字段验证
        required_fields = ['run_id', 'name', 'workspace']
        for field in required_fields:
            if field not in body:
                return BAD_REQUEST_400(f"Missing required field: {field}")

        run_id = body['run_id']
        exp_name = body['name']
        description = body.get('description', '')
        colors = body.get('colors', [])
        workspace = body['workspace']

        # 验证工作空间
        if not connection_manager.validate_workspace(workspace):
            return UNAUTHORIZED_401(f"Workspace '{workspace}' not allowed")

        # 处理颜色
        colors_tuple = None
        if colors and len(colors) >= 2:
            colors_tuple = (colors[0], colors[1])

        # 创建CloudSyncManager实例
        sync_manager = CloudSyncManager(
            workspace=workspace,
            user=os.getenv('SWANLAB_USER', 'unknown')
        )

        # 首先需要有一个项目上下文，如果提供了project_id，先设置项目
        project_id = body.get('project_id')
        if project_id:
            # 验证项目存在并设置为当前项目
            from ..repositories import project_repository
            project = project_repository.get_by_id(int(project_id))
            if not project:
                return NOT_FOUND_404(f"Project with id {project_id} not found")
            sync_manager._current_project_id = str(project.id)

        # 使用CloudSyncManager同步实验
        experiment_id = sync_manager.sync_experiment(
            run_id=run_id,
            name=exp_name,
            description=description,
            colors=colors_tuple
        )

        if not experiment_id:
            return DATA_ERROR_500("Failed to sync experiment")

        # 获取实验信息以构建响应
        from ..repositories import experiment_repository
        experiment = experiment_repository.get_by_run_id(run_id)
        if not experiment:
            return DATA_ERROR_500("Experiment sync succeeded but cannot retrieve experiment")

        return SUCCESS_200({
            "id": experiment_id,
            "experiment_id": experiment_id,
            "run_id": experiment.run_id,
            "name": experiment.name,
            "description": experiment.description,
            "workspace": workspace,
            "existed": True  # CloudSyncManager会处理存在性逻辑
        })

    except Exception as e:
        swanlog.error(f"Experiment sync error: {e}")
        return DATA_ERROR_500(f"Experiment sync failed: {e}")


# ================================== 列/指标相关API ==================================

async def sync_column(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    同步列/指标到云端数据库

    POST /api/v1/cloud/columns

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
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = await request.json()

        # 必需字段验证
        required_fields = ['key', 'experiment_id', 'chart_type', 'section_name']
        for field in required_fields:
            if field not in body:
                return BAD_REQUEST_400(f"Missing required field: {field}")

        key = body['key']
        experiment_id = int(body['experiment_id'])
        chart_type = body['chart_type']
        reference = body.get('reference', 'step')
        section_name = body['section_name']
        section_sort = body.get('section_sort', 0)
        kid = body.get('kid', '')
        error_info = body.get('error')

        # 验证实验存在
        from ..repositories import experiment_repository
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 使用chart_repository直接同步列
        from ..repositories import chart_repository
        chart_id = chart_repository.sync_column(
            key=key,
            experiment_id=experiment_id,
            chart_type=chart_type,
            reference=reference,
            section_name=section_name,
            section_sort=section_sort,
            kid=kid,
            error_info=error_info
        )

        if not chart_id:
            return DATA_ERROR_500("Failed to sync column")

        swanlog.info(f"Synced column: {key} for experiment {experiment.name}")

        return SUCCESS_200({
            "id": chart_id,
            "column_id": chart_id,
            "key": key,
            "chart_type": chart_type,
            "experiment_id": str(experiment_id)
        })

    except Exception as e:
        swanlog.error(f"Column sync error: {e}")
        return DATA_ERROR_500(f"Column sync failed: {e}")


# ================================== 实验状态API ==================================

async def update_experiment_status(
    experiment_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    更新实验状态

    PUT /api/v1/cloud/experiments/{experiment_id}/status

    Body:
    {
        "status": 1  // -1: crashed, 0: running, 1: finished
    }

    Returns:
        更新结果
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = await request.json()

        if 'status' not in body:
            return BAD_REQUEST_400("Missing required field: status")

        status = int(body['status'])
        error = body.get('error')

        # 验证状态值
        if status not in [-1, 0, 1]:
            return BAD_REQUEST_400("Invalid status value. Must be -1, 0, or 1")

        # 使用experiment_repository直接更新状态
        from ..repositories import experiment_repository
        success = experiment_repository.update_status(
            experiment_id=int(experiment_id),
            status=status,
            error=error
        )

        if not success:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found or update failed")

        # 获取更新后的实验信息
        experiment = experiment_repository.get_by_id(int(experiment_id))
        status_text = {-1: "crashed", 0: "running", 1: "finished"}[status]

        return SUCCESS_200({
            "experiment_id": str(experiment_id),
            "status": status,
            "status_text": status_text,
            "updated_at": experiment.updated_at.isoformat() if experiment and experiment.updated_at else None
        })

    except Exception as e:
        swanlog.error(f"Status update error: {e}")
        return DATA_ERROR_500(f"Status update failed: {e}")


# ================================== 运行时信息API ==================================

async def sync_runtime_info(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    同步实验运行时信息到云端数据库

    POST /api/v1/cloud/runtime-info

    Body:
    {
        "experiment_id": "1",
        "requirements": "numpy==1.21.0\npandas==1.3.0",
        "metadata": "{\"python_version\": \"3.8.10\"}",
        "config": "epochs: 100\nlearning_rate: 0.001",
        "conda": "name: myenv\ndependencies:\n  - python=3.8"
    }

    Returns:
        运行时信息ID和相关信息
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = await request.json()
        print("sync_runtime_info body:", body)
        # 必需字段验证
        required_fields = ['experiment_id']
        for field in required_fields:
            if field not in body:
                return BAD_REQUEST_400(f"Missing required field: {field}")

        experiment_id = int(body['experiment_id'])
        requirements = body.get('requirements')
        metadata = body.get('metadata')
        config = body.get('config')
        conda = body.get('conda')

        # 验证实验存在
        from ..repositories import experiment_repository
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 获取实验的工作空间信息（通过项目获取）
        from ..repositories import project_repository
        project = project_repository.get_by_id(experiment.project_id)
        if not project:
            return DATA_ERROR_500("Project not found for experiment")

        # 创建CloudSyncManager实例
        sync_manager = CloudSyncManager(
            workspace=project.workspace,
            user=os.getenv('SWANLAB_USER', 'unknown')
        )

        # 设置当前实验上下文
        sync_manager._current_project_id = str(project.id)
        sync_manager._current_experiment_id = str(experiment.id)

        # 使用CloudSyncManager同步运行时信息
        runtime_id = sync_manager.sync_runtime_info(
            requirements=requirements,
            metadata=metadata,
            config=config,
            conda=conda
        )

        if not runtime_id:
            return DATA_ERROR_500("Failed to sync runtime info")

        swanlog.info(f"Synced runtime info for experiment {experiment.name}")

        return SUCCESS_200({
            "id": runtime_id,
            "runtime_info_id": runtime_id,
            "experiment_id": str(experiment_id),
            "synced_fields": {
                "requirements": requirements is not None,
                "metadata": metadata is not None,
                "config": config is not None,
                "conda": conda is not None
            }
        })

    except Exception as e:
        swanlog.error(f"Runtime info sync error: {e}")
        return DATA_ERROR_500(f"Runtime info sync failed: {e}")


async def get_runtime_info(
    experiment_id: str,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取实验运行时信息

    GET /api/v1/cloud/experiments/{experiment_id}/runtime-info

    Returns:
        运行时信息详情
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 验证实验存在
        from ..repositories import experiment_repository
        experiment = experiment_repository.get_by_id(int(experiment_id))
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 获取实验的工作空间信息
        from ..repositories import project_repository
        project = project_repository.get_by_id(experiment.project_id)
        if not project:
            return DATA_ERROR_500("Project not found for experiment")

        # 创建CloudSyncManager实例
        sync_manager = CloudSyncManager(
            workspace=project.workspace,
            user=os.getenv('SWANLAB_USER', 'unknown')
        )

        # 获取运行时信息
        runtime_info = sync_manager.get_experiment_runtime_info(int(experiment_id))

        if not runtime_info:
            return NOT_FOUND_404(f"Runtime info not found for experiment {experiment_id}")

        return SUCCESS_200({
            "experiment_id": str(experiment_id),
            "experiment_name": experiment.name,
            "runtime_info": runtime_info
        })

    except Exception as e:
        swanlog.error(f"Get runtime info error: {e}")
        return DATA_ERROR_500(f"Failed to get runtime info: {e}")


# ================================== 查询API ==================================

async def get_workspace_projects(
    workspace: str,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取工作空间下的所有项目

    GET /api/v1/cloud/workspaces/{workspace}/projects

    Returns:
        项目列表
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 验证工作空间
        if not connection_manager.validate_workspace(workspace):
            return UNAUTHORIZED_401(f"Workspace '{workspace}' not allowed")

        # 使用project_repository获取项目列表
        from ..repositories import project_repository
        project_list = project_repository.get_workspace_projects(workspace)

        return SUCCESS_200({
            "workspace": workspace,
            "projects": project_list,
            "total": len(project_list)
        })

    except Exception as e:
        swanlog.error(f"Get workspace projects error: {e}")
        return DATA_ERROR_500(f"Failed to get workspace projects: {e}")


async def get_project_experiments(
    project_id: str,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取项目下的所有实验

    GET /api/v1/cloud/projects/{project_id}/experiments

    Returns:
        实验列表
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 验证项目存在
        from ..repositories import project_repository, experiment_repository
        project = project_repository.get_by_id(int(project_id))
        if not project:
            return NOT_FOUND_404(f"Project with id {project_id} not found")

        # 获取项目下的所有实验
        experiment_list = experiment_repository.get_project_experiments(int(project_id))

        return SUCCESS_200({
            "project_id": str(project.id),
            "project_name": project.name,
            "experiments": experiment_list,
            "total": len(experiment_list)
        })

    except Exception as e:
        swanlog.error(f"Get project experiments error: {e}")
        return DATA_ERROR_500(f"Failed to get project experiments: {e}")


async def get_workspaces(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取所有工作空间列表

    GET /api/v1/cloud/workspaces

    Returns:
        工作空间列表
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 使用 NamespaceRepository 获取所有工作空间
        from ..repositories import namespace_repository

        workspace_list = namespace_repository.get_all_workspaces()

        return SUCCESS_200({
            "workspaces": workspace_list,
            "total": len(workspace_list)
        })

    except Exception as e:
        swanlog.error(f"Get workspaces error: {e}")
        return DATA_ERROR_500(f"Failed to get workspaces: {e}")
