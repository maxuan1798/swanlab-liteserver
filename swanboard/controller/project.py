#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@DATE: 2024-01-19 22:09:09
@File: swanboard/controller/project.py
@IDE: vscode
@Description:
    项目相关 API 的处理函数 - 云端版本
    使用 CloudSyncManager 和 Repository 模式
"""

import os
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, Header

# 使用CloudSyncManager和repositories处理业务逻辑
from ..cloud_api import CloudSyncManager
from ..repositories import (
    connection_manager, project_repository, experiment_repository, chart_repository
)

from ..db.mysql import (
    CloudProject as Project,
    CloudExperiment as Experiment
)

# 响应模块
from ..module.resp import (
    SUCCESS_200, DATA_ERROR_500, BAD_REQUEST_400,
    NOT_FOUND_404, CONFLICT_409, UNAUTHORIZED_401
)

# 工具函数
from ..utils import swanlog, check_desc_format, COLOR_LIST

# 默认项目 id
DEFAULT_PROJECT_ID = Project.DEFAULT_PROJECT_ID
# 实验运行状态
RUNNING_STATUS = Experiment.RUNNING_STATUS


# ================================== 项目信息获取 ==================================

def get_project_info(
    project_id: int = DEFAULT_PROJECT_ID,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取项目信息

    GET /api/v1/projects/{project_id}

    Returns:
        项目信息和实验列表
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        print("get_project_info", project_id)
        # 获取项目信息
        project = project_repository.get_by_id(project_id)
        if not project:
            return NOT_FOUND_404(f"Project with id {project_id} not found")
        swanlog.info(f"Project with id {project_id} found")
        # 获取项目下的所有实验
        experiments = experiment_repository.get_project_experiments(project_id)
        swanlog.info(f"Found {len(experiments)} experiments")
        # 构建响应数据
        project_data = project_repository.to_dict(project)
        if not project_data:
            return DATA_ERROR_500("Failed to convert project to dict")
        project_data["experiments"] = experiments or []
        project_data["colors"] = COLOR_LIST

        # 处理实验数据格式
        if experiments:
            for experiment in experiments:
                if isinstance(experiment, dict) and "id" in experiment:
                    experiment["experiment_id"] = experiment["id"]
                    # 移除不需要的字段
                    experiment.pop("project_id", None)

        return SUCCESS_200(project_data)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        swanlog.error(f"Get project info error: {e}")
        swanlog.error(f"Full traceback: {error_details}")
        return DATA_ERROR_500(f"Failed to get project info: {e}")


def get_project_summary(
    project_id: int = DEFAULT_PROJECT_ID,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取项目下所有实验的总结信息

    GET /api/v1/projects/{project_id}/summary

    Returns:
        项目总结信息
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 验证项目存在
        project = project_repository.get_by_id(project_id)
        if not project:
            return NOT_FOUND_404(f"Project with id {project_id} not found")

        # 获取项目统计信息
        stats = project_repository.get_project_stats(project_id)

        # 获取项目下的实验列表
        experiments = experiment_repository.get_project_experiments(project_id)

        # 获取所有实验的图表信息
        all_charts = []
        tag_names = set()

        for experiment in experiments:
            exp_charts = chart_repository.get_experiment_charts(experiment["id"])
            for chart in exp_charts:
                all_charts.append(chart)
                tag_names.add(chart["key"])

        # 构建总结数据
        summaries = {}
        for experiment in experiments:
            exp_name = experiment["name"]
            exp_summary = {}

            # 获取每个实验的最新指标数据
            exp_charts = chart_repository.get_experiment_charts(experiment["id"])
            for chart in exp_charts:
                # 这里简化处理，实际可能需要从数据文件中读取最新值
                exp_summary[chart["key"]] = f"Latest value for {chart['key']}"

            summaries[exp_name] = exp_summary

        return SUCCESS_200({
            "tags": list(tag_names),
            "summaries": summaries,
            "stats": stats
        })

    except Exception as e:
        swanlog.error(f"Get project summary error: {e}")
        return DATA_ERROR_500(f"Failed to get project summary: {e}")


# ================================== 项目信息修改 ==================================

def update_project_info(
    project_id: int,
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    修改项目信息

    PUT /api/v1/projects/{project_id}

    Body:
    {
        "name": "new_project_name",
        "description": "new project description"
    }

    Returns:
        更新后的项目信息
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = request.json()

        # 验证项目存在
        project = project_repository.get_by_id(project_id)
        if not project:
            return NOT_FOUND_404(f"Project with id {project_id} not found")

        # 验证和格式化数据
        updates = {}
        if "name" in body:
            updates["name"] = body["name"]

        if "description" in body:
            updates["description"] = check_desc_format(body["description"], False)

        # 更新项目信息
        updated_project = project_repository.update(project, **updates)
        if not updated_project:
            return DATA_ERROR_500("Failed to update project")

        swanlog.info(f"Updated project {project_id}: {updates}")

        return SUCCESS_200({
            "updates": updates,
            "project": project_repository.to_dict(updated_project)
        })

    except Exception as e:
        swanlog.error(f"Update project info error: {e}")
        return DATA_ERROR_500(f"Failed to update project info: {e}")


# ================================== 项目删除 ==================================

def delete_project(
    project_id: int,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    删除项目

    DELETE /api/v1/projects/{project_id}

    Returns:
        删除结果
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 验证项目存在
        project = project_repository.get_by_id(project_id)
        if not project:
            return NOT_FOUND_404(f"Project with id {project_id} not found")

        # 检查是否有正在运行的实验
        running_experiments = experiment_repository.get_experiments_by_status(
            status=RUNNING_STATUS,  # running
            project_id=project_id
        )

        if running_experiments:
            return CONFLICT_409("Can't delete project since there are experiments running")

        # 获取所有实验用于清理
        experiments = experiment_repository.get_project_experiments(project_id)

        # 删除项目（这会级联删除相关的实验、图表等）
        success = project_repository.delete(project)
        if not success:
            return DATA_ERROR_500("Failed to delete project from database")

        swanlog.info(f"Deleted project {project_id} with {len(experiments)} experiments")

        return SUCCESS_200({
            "deleted_project_id": str(project_id),
            "deleted_experiments_count": len(experiments)
        })

    except Exception as e:
        swanlog.error(f"Delete project error: {e}")
        return DATA_ERROR_500(f"Failed to delete project: {e}")


# ================================== 项目图表 ==================================

def get_project_charts(
    project_id: int,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取多实验对比图表数据

    GET /api/v1/projects/{project_id}/charts

    Returns:
        项目图表数据
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 验证项目存在
        project = project_repository.get_by_id(project_id)
        if not project:
            return NOT_FOUND_404(f"Project with id {project_id} not found")

        # 获取项目下所有实验
        experiments = experiment_repository.get_project_experiments(project_id)

        # 获取所有图表数据
        all_charts = []
        all_namespaces = []

        for experiment in experiments:
            exp_id = experiment["id"]

            # 获取实验的图表
            exp_charts = chart_repository.get_experiment_charts(exp_id)
            for chart in exp_charts:
                # 添加实验信息到图表
                chart["experiment"] = experiment
                all_charts.append(chart)

            # 获取实验的命名空间
            from ..repositories import namespace_repository
            exp_namespaces = namespace_repository.get_experiment_namespaces(exp_id)
            for namespace in exp_namespaces:
                namespace["experiment"] = experiment
                all_namespaces.append(namespace)

        # 按命名空间和图表键进行分组
        grouped_charts = {}
        for chart in all_charts:
            key = chart["key"]
            if key not in grouped_charts:
                grouped_charts[key] = []
            grouped_charts[key].append(chart)

        return SUCCESS_200({
            "charts": list(grouped_charts.values()),
            "namespaces": all_namespaces,
            "experiments": experiments
        })

    except Exception as e:
        swanlog.error(f"Get project charts error: {e}")
        return DATA_ERROR_500(f"Failed to get project charts: {e}")


# ================================== 工作空间项目列表 ==================================

async def get_workspace_projects(
    workspace: str,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    获取工作空间下的所有项目

    GET /api/v1/workspaces/{workspace}/projects

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

        # 获取工作空间下的项目
        project_list = project_repository.get_workspace_projects(workspace)

        return SUCCESS_200({
            "workspace": workspace,
            "projects": project_list,
            "total": len(project_list)
        })

    except Exception as e:
        swanlog.error(f"Get workspace projects error: {e}")
        return DATA_ERROR_500(f"Failed to get workspace projects: {e}")


# ================================== 创建项目 ==================================

def create_project(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    创建新项目

    POST /api/v1/projects

    Body:
    {
        "name": "project_name",
        "workspace": "workspace_name",
        "description": "project description"
    }

    Returns:
        创建的项目信息
    """
    # 验证API密钥
    if not connection_manager.validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = request.json()

        # 必需字段验证
        required_fields = ['name', 'workspace']
        for field in required_fields:
            if field not in body:
                return BAD_REQUEST_400(f"Missing required field: {field}")

        project_name = body['name']
        workspace = body['workspace']
        description = body.get('description', '')

        swanlog.info(f"Creating project: {project_name} in workspace: {workspace}")

        # 验证工作空间
        if not connection_manager.validate_workspace(workspace):
            return UNAUTHORIZED_401(f"Workspace '{workspace}' not allowed")

        # 创建CloudSyncManager实例
        sync_manager = CloudSyncManager(
            workspace=workspace,
            user=os.getenv('SWANLAB_USER', 'unknown')
        )

        # 使用CloudSyncManager创建项目
        project_id = sync_manager.sync_project(
            name=project_name,
            description=description
        )

        if not project_id:
            return DATA_ERROR_500("Failed to create project")

        # 获取创建的项目信息
        project = project_repository.get_by_name_and_workspace(project_name, workspace)
        if not project:
            return DATA_ERROR_500("Project created but cannot retrieve project")

        swanlog.info(f"Successfully created project: {project_name} (ID: {project_id})")

        return SUCCESS_200({
            "id": project_id,
            "project_id": project_id,
            "name": project.name,
            "description": project.description,
            "workspace": workspace,
            "created": True
        })

    except Exception as e:
        swanlog.error(f"Create project error: {e}")
        return DATA_ERROR_500(f"Failed to create project: {e}")
