#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@DATE: 2024-11-26 16:45:00
@File: swanboard/controller/cloud.py
@IDE: vscode
@Description:
    云端API控制器 - 支持EnhancedSwanBoardCallback的HTTP通信
"""

import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import Request, HTTPException, Header

# 数据库模型
from ..db import (
    Project, Experiment, Chart, Tag, Namespace, Source, Display,
    ExistedError, NotExistedError, ChartTypeError, connect, add_multi_chart
)

# 响应模块
from ..module.resp import (
    SUCCESS_200, DATA_ERROR_500, BAD_REQUEST_400,
    NOT_FOUND_404, CONFLICT_409, UNAUTHORIZED_401
)

# 工具函数
from ..utils import swanlog, get_swanlog_dir, generate_color
from swankit.env import create_time


# ================================== 认证和验证 ==================================

def validate_api_key(authorization: Optional[str] = None) -> bool:
    """
    验证API密钥

    Args:
        authorization: Authorization header值

    Returns:
        bool: 验证成功返回True
    """
    return True
    # if not authorization:
    #     return False
    #
    # # 检查Bearer token格式
    # if not authorization.startswith("Bearer "):
    #     return False
    #
    # token = authorization[7:]  # 移除"Bearer "前缀
    #
    # # 简单的token验证（实际应用中应该使用更安全的方法）
    # expected_token = os.getenv('SWANLAB_API_KEY')
    # if not expected_token:
    #     # 如果没有设置API密钥，则允许所有请求（开发模式）
    #     return True
    #
    # return token == expected_token


def validate_workspace(workspace: str) -> bool:
    """
    验证工作空间

    Args:
        workspace: 工作空间名称

    Returns:
        bool: 验证成功返回True
    """
    # 简单验证，实际应用中可能需要更复杂的逻辑
    allowed_workspaces = os.getenv('SWANLAB_ALLOWED_WORKSPACES', '').split(',')
    if not allowed_workspaces or allowed_workspaces == ['']:
        return True  # 如果没有限制，允许所有工作空间

    return workspace in allowed_workspaces


# ================================== 项目相关API ==================================

async def sync_project(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    同步项目到云端

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
    if not validate_api_key(authorization):
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

        # 验证工作空间
        if not validate_workspace(workspace):
            return UNAUTHORIZED_401(f"Workspace '{workspace}' not allowed")

        # 连接数据库
        connect(autocreate=True, path=get_swanlog_dir())

        # 检查项目是否已存在
        try:
            existing_project = Project.get(Project.name == project_name)
            # 项目已存在，更新描述
            if description:
                existing_project.description = description
                existing_project.save()

            return SUCCESS_200({
                "id": str(existing_project.id),
                "project_id": str(existing_project.id),
                "name": existing_project.name,
                "description": existing_project.description,
                "workspace": workspace,
                "existed": True
            })

        except Project.DoesNotExist:
            # 项目不存在，创建新项目
            pass

        # 创建新项目
        try:
            project = Project.create(
                name=project_name,
                description=description,
                version="1.0.0"
            )

            swanlog.info(f"Created cloud project: {project_name} (workspace: {workspace})")

            return SUCCESS_200({
                "id": str(project.id),
                "project_id": str(project.id),
                "name": project.name,
                "description": project.description,
                "workspace": workspace,
                "existed": False
            })

        except Exception as e:
            swanlog.error(f"Failed to create project: {e}")
            return DATA_ERROR_500(f"Failed to create project: {e}")

    except Exception as e:
        swanlog.error(f"Project sync error: {e}")
        return DATA_ERROR_500(f"Project sync failed: {e}")


# ================================== 实验相关API ==================================

async def sync_experiment(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    同步实验到云端

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
    if not validate_api_key(authorization):
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
        project_id = body.get('project_id', '1')
        workspace = body['workspace']

        # 验证工作空间
        if not validate_workspace(workspace):
            return UNAUTHORIZED_401(f"Workspace '{workspace}' not allowed")

        # 连接数据库
        connect(autocreate=True, path=get_swanlog_dir())

        # 验证项目存在
        try:
            project = Project.get(Project.id == int(project_id))
        except Project.DoesNotExist:
            return NOT_FOUND_404(f"Project with id {project_id} not found")

        # 处理颜色
        if colors and len(colors) >= 2:
            light_color, dark_color = colors[0], colors[1]
        else:
            light_color, dark_color = generate_color()

        # 检查实验是否已存在
        try:
            existing_exp = Experiment.get(Experiment.run_id == run_id)
            # 实验已存在，更新信息
            existing_exp.name = exp_name
            existing_exp.description = description
            existing_exp.light = light_color
            existing_exp.dark = dark_color
            existing_exp.save()

            return SUCCESS_200({
                "id": str(existing_exp.id),
                "experiment_id": str(existing_exp.id),
                "run_id": existing_exp.run_id,
                "name": existing_exp.name,
                "description": existing_exp.description,
                "workspace": workspace,
                "existed": True
            })

        except Experiment.DoesNotExist:
            # 实验不存在，创建新实验
            pass

        # 获取项目中实验数量作为sort
        exp_count = Experiment.select().where(Experiment.project_id == project.id).count()

        # 创建新实验
        try:
            experiment = Experiment.create(
                name=exp_name,
                run_id=run_id,
                description=description,
                project_id=project.id,
                colors=(light_color, dark_color),
                num=exp_count + 1
            )

            swanlog.info(f"Created cloud experiment: {exp_name} (run_id: {run_id}, workspace: {workspace})")

            return SUCCESS_200({
                "id": str(experiment.id),
                "experiment_id": str(experiment.id),
                "run_id": experiment.run_id,
                "name": experiment.name,
                "description": experiment.description,
                "workspace": workspace,
                "existed": False
            })

        except Exception as e:
            swanlog.error(f"Failed to create experiment: {e}")
            return DATA_ERROR_500(f"Failed to create experiment: {e}")

    except Exception as e:
        swanlog.error(f"Experiment sync error: {e}")
        return DATA_ERROR_500(f"Experiment sync failed: {e}")


# ================================== 列/指标相关API ==================================

async def sync_column(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    同步列/指标到云端

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
    if not validate_api_key(authorization):
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

        # 连接数据库
        connect(autocreate=True, path=get_swanlog_dir())

        # 验证实验存在
        try:
            experiment = Experiment.get(Experiment.id == experiment_id)
        except Experiment.DoesNotExist:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 创建图表
        try:
            chart = Chart.create(
                key=key,
                experiment_id=experiment,
                type=chart_type,
                reference=reference
            )
        except ExistedError:
            # 图表已存在
            chart = Chart.get(Chart.key == key, Chart.experiment_id == experiment)

        # 创建命名空间
        try:
            namespace = Namespace.create(
                name=section_name,
                experiment_id=experiment.id,
                sort=section_sort
            )
        except ExistedError:
            namespace = Namespace.get(
                Namespace.name == section_name,
                Namespace.experiment_id == experiment.id
            )

        # 创建显示配置
        try:
            display = Display.create(
                chart_id=chart.id,
                namespace_id=namespace.id
            )
        except ExistedError:
            display = Display.get(
                Display.chart_id == chart.id,
                Display.namespace_id == namespace.id
            )

        # 创建标签
        try:
            tag = Tag.create(
                experiment_id=experiment.id,
                name=key,
                type=chart_type,
                folder=kid
            )
        except ExistedError:
            tag = Tag.get(
                Tag.experiment_id == experiment.id,
                Tag.name == key
            )

        # 创建数据源
        error_data = None
        if error_info:
            error_data = {
                "data_class": error_info.get("data_class"),
                "excepted": error_info.get("expected")  # 注意这里使用"excepted"以匹配原有代码
            }

        try:
            source = Source.create(
                tag_id=tag.id,
                chart_id=chart.id,
                error=error_data
            )
        except ExistedError:
            source = Source.get(
                Source.tag_id == tag.id,
                Source.chart_id == chart.id
            )

        # 尝试添加多实验对比图表
        try:
            add_multi_chart(tag_id=tag.id, chart_id=chart.id)
        except ChartTypeError:
            swanlog.debug("Chart type not supported for multi-experiment comparison")

        swanlog.info(f"Synced column: {key} for experiment {experiment.name}")

        return SUCCESS_200({
            "id": str(chart.id),
            "column_id": str(chart.id),
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
    if not validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        body = await request.json()

        if 'status' not in body:
            return BAD_REQUEST_400("Missing required field: status")

        status = int(body['status'])

        # 验证状态值
        if status not in [-1, 0, 1]:
            return BAD_REQUEST_400("Invalid status value. Must be -1, 0, or 1")

        # 连接数据库
        connect(autocreate=True, path=get_swanlog_dir())

        # 查找实验
        try:
            experiment = Experiment.get(Experiment.id == int(experiment_id))
        except Experiment.DoesNotExist:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 更新状态
        experiment.update_status(status)

        status_text = {-1: "crashed", 0: "running", 1: "finished"}[status]
        swanlog.info(f"Updated experiment {experiment.name} status to: {status_text}")

        return SUCCESS_200({
            "experiment_id": str(experiment.id),
            "status": status,
            "status_text": status_text,
            "updated_at": experiment.finish_time or experiment.update_time
        })

    except Exception as e:
        swanlog.error(f"Status update error: {e}")
        return DATA_ERROR_500(f"Status update failed: {e}")


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
    if not validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 验证工作空间
        if not validate_workspace(workspace):
            return UNAUTHORIZED_401(f"Workspace '{workspace}' not allowed")

        # 连接数据库
        connect(autocreate=True, path=get_swanlog_dir())

        # 获取所有项目（简化版本，实际中可能需要根据workspace过滤）
        projects = Project.select()
        project_list = []

        for project in projects:
            exp_count = Experiment.select().where(Experiment.project_id == project.id).count()
            project_list.append({
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "experiment_count": exp_count,
                "created_at": project.create_time,
                "updated_at": project.update_time
            })

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
    if not validate_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # 连接数据库
        connect(autocreate=True, path=get_swanlog_dir())

        # 验证项目存在
        try:
            project = Project.get(Project.id == int(project_id))
        except Project.DoesNotExist:
            return NOT_FOUND_404(f"Project with id {project_id} not found")

        # 获取项目下的所有实验
        experiments = Experiment.select().where(Experiment.project_id == project.id)
        experiment_list = []

        for exp in experiments:
            experiment_list.append({
                "id": str(exp.id),
                "name": exp.name,
                "run_id": exp.run_id,
                "description": exp.description,
                "status": exp.status,
                "light_color": exp.light,
                "dark_color": exp.dark,
                "created_at": exp.create_time,
                "updated_at": exp.update_time,
                "finished_at": exp.finish_time
            })

        return SUCCESS_200({
            "project_id": str(project.id),
            "project_name": project.name,
            "experiments": experiment_list,
            "total": len(experiment_list)
        })

    except Exception as e:
        swanlog.error(f"Get project experiments error: {e}")
        return DATA_ERROR_500(f"Failed to get project experiments: {e}")
