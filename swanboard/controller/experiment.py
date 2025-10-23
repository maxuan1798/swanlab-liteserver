#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@DATE: 2024-01-20 21:21:45
@File: swanboard/controller/experiment.py
@IDE: vscode
@Description:
    实验相关 API 的处理函数 - 云端版本
    使用 CloudSyncManager 和Repository 模式
"""

import os
import ujson
import yaml
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, Depends
from typing import Union
from ..db.mysql.api_key_models import APIKey

# 使用CloudSyncManager和repositories处理业务逻辑
from ..cloud_api import CloudSyncManager
from ..repositories import (
    connection_manager, project_repository, experiment_repository, chart_repository, clickhouse_repository
)

# 认证依赖
from ..dependencies.auth import validate_api_key_dependency, validate_platform_api_key_dependency
from ..db.mysql import Account

from ..db.mysql import (
    CloudProject as Project,
    CloudExperiment as Experiment
)
from ..db.mysql.models import CloudRuntimeInfo

# 响应模块
from ..module.resp import (
    SUCCESS_200, DATA_ERROR_500, BAD_REQUEST_400,
    NOT_FOUND_404, CONFLICT_409, UNAUTHORIZED_401
)

# 工具函数
from ..utils import swanlog, check_desc_format, COLOR_LIST
from .utils.tag import lttb

# 图表工具函数（兼容原有的图表数据结构）
def get_exp_charts_compatible(experiment_id: int):
    """
    获取实验图表数据，兼容原有的数据结构
    云端版本简化实现
    """
    try:
        # 获取实验的图表信息
        charts = chart_repository.get_experiment_charts(experiment_id)

        # 转换为兼容的格式
        chart_list = []
        for chart in charts:
            chart_item = {
                "id": chart.get("id"),
                "key": chart.get("key", ""),
                "name": chart.get("key", ""),
                "type": chart.get("chart_type", "line"),
                "reference": chart.get("reference", "step"),
                "sort": chart.get("sort", 0),
                "status": chart.get("status", 0),
                "experiment_id": experiment_id,
                "project_id": None,
                "error": {},
                "source": [chart.get("key", "")],
                "multi": False,
                "source_map": {chart.get("key", ""): experiment_id}
            }
            chart_list.append(chart_item)

        # 简化的命名空间数据
        namespace_list = [
            {
                "id": 1,
                "name": "default",
                "charts": [chart["id"] for chart in chart_list],
                "opened": True,
                "experiment_id": experiment_id,
                "project_id": None,
            }
        ]

        return chart_list, namespace_list
    except Exception as e:
        swanlog.error(f"Failed to get experiment charts: {e}")
        return [], []

# 默认项目 id
DEFAULT_PROJECT_ID = Project.DEFAULT_PROJECT_ID
# 实验运行状态
RUNNING_STATUS = Experiment.RUNNING_STATUS


# ================================== 实验信息获取 ==================================

def get_experiment_info(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获取实验信息

    GET /api/v1/experiments/{experiment_id}

    Returns:
        ���验信息和相关数据
    """
    # JWT认证已通过依赖注入处理

    try:
        # 获取实验信息
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        swanlog.info(f"Experiment with id {experiment_id} found")

        # 构建响应数据
        experiment_data = experiment_repository.to_dict(experiment)
        if not experiment_data:
            return DATA_ERROR_500("Failed to convert experiment to dict")

        # 移除不需要的字段
        experiment_data.pop("project_id", None)

        # 从云端运行时信息获取 config 和 system
        try:
            # 从 CloudRuntimeInfo 表中获取运行时信息
            runtime_info = CloudRuntimeInfo.select().where(
                CloudRuntimeInfo.experiment == experiment_id
            ).first()

            if runtime_info:
                # 从云端运行时信息加载 config
                if runtime_info.config:
                    try:
                        experiment_data["config"] = yaml.load(runtime_info.config, Loader=yaml.FullLoader)
                    except Exception as e:
                        swanlog.warning(f"Failed to parse config from cloud runtime info: {e}")
                        experiment_data["config"] = {}
                else:
                    experiment_data["config"] = {}

                # 从云端运行时信息加载 system (metadata)
                if runtime_info.metadata:
                    try:
                        experiment_data["system"] = ujson.loads(runtime_info.metadata)
                    except Exception as e:
                        swanlog.warning(f"Failed to parse metadata from cloud runtime info: {e}")
                        experiment_data["system"] = {}
                else:
                    experiment_data["system"] = {}

                swanlog.debug(f"Loaded config and system from cloud runtime info for experiment {experiment_id}")
            else:
                # 如果云端没有运行时信息，设置为空
                experiment_data["config"] = {}
                experiment_data["system"] = {}
                swanlog.info(f"No runtime info found in cloud for experiment {experiment_id}")

        except Exception as e:
            swanlog.warning(f"Failed to get runtime info from cloud: {e}")
            # 云端获取失败时，设置为空
            experiment_data["config"] = {}
            experiment_data["system"] = {}

        return SUCCESS_200(experiment_data)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        swanlog.error(f"Get experiment info error: {e}")
        swanlog.error(f"Full traceback: {error_details}")
        return DATA_ERROR_500(f"Failed to get experiment info: {e}")


def get_tag_data(
    experiment_id: int,
    tag: str,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获取标签数据（从 ClickHouse 获取）

    GET /api/v1/experiments/{experiment_id}/tag/{tag}

    Returns:
        标签相关的数据信息
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 获取实验的 run_id（使用实验目录名作为 run_id）
        # 注意：这里假设 experiment 对象有 run_dir 或类似属性
        # 你可能需要根据实际的数据模型调整
        run_id = getattr(experiment, 'run_dir', None) or getattr(experiment, 'run_id', None)
        if not run_id:
            # 如果实验对象没有 run_id，尝试从数据库或其他地方获取
            # 这里使用一个后备方案
            swanlog.warning(f"Experiment {experiment_id} has no run_id, using experiment_id as fallback")
            run_id = str(experiment_id)

        # 从 ClickHouse 获取列信息
        column = clickhouse_repository.get_column_by_run_and_key(run_id, tag)
        if not column:
            return NOT_FOUND_404(f"Tag '{tag}' not found for experiment {experiment_id}")

        column_id = column['column_id']

        # 获取指标数据
        tag_data = clickhouse_repository.get_metric_data(run_id, column_id)

        # 如果数据为空，返回空列���
        if len(tag_data) == 0:
            return SUCCESS_200(data={
                "sum": 0,
                "max": None,
                "min": None,
                "list": [],
                "experiment_id": experiment_id
            })

        # 根据 index 升序排序（已经在查询中按 step 排序）
        # tag_data 的最后一个数据增加一个字段 _last = True
        tag_data[-1]["_last"] = True

        # 获取最大值和最小值
        summary = clickhouse_repository.get_metric_summary(run_id, column_id)
        max_value = summary.get('max', None)
        min_value = summary.get('min', None)

        # 应用 LTTB 降采样
        sampled_data = lttb(tag_data)

        return SUCCESS_200(
            data={
                "sum": len(tag_data),
                "max": max_value,
                "min": min_value,
                "list": sampled_data,
                # 标注此数据隶属于哪个实验
                "experiment_id": experiment_id,
            }
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        swanlog.error(f"Get tag data error: {e}")
        swanlog.error(f"Full traceback: {error_details}")
        return DATA_ERROR_500(f"Failed to get tag data: {e}")


def get_experiment_status(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获取实验状态以及实验图表配���，用于实时更新实验状态

    GET /api/v1/experiments/{experiment_id}/status

    Returns:
        实验状态和图表配置信息
    """
    # JWT认证已通过依赖注入处理

    try:
        # 获取实验信息
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 获取实验的图表信息（使用兼容格式）
        chart_list, namespace_list = get_exp_charts_compatible(experiment_id)

        return SUCCESS_200({
            "status": experiment.status,
            "update_time": experiment.updated_at.isoformat() if experiment.updated_at else None,
            "finish_time": experiment.finished_at.isoformat() if experiment.finished_at else None,
            "charts": {
                "charts": chart_list,
                "namespaces": namespace_list,
            },
        })

    except Exception as e:
        swanlog.error(f"Get experiment status error: {e}")
        return DATA_ERROR_500(f"Failed to get experiment status: {e}")


def get_experiment_summary(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获取实验的总结数据——每个标签的最新数据

    GET /api/v1/experiments/{experiment_id}/summary

    Returns:
        实验总结信息
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 获取实验的图表信息
        charts = chart_repository.get_experiment_charts(experiment_id)

        # 构建总结数据
        summaries = []
        for chart in charts:
            # 云端版本中，总结数据从数据���中获取
            summaries.append({
                "key": chart["key"],
                "value": f"Latest value for {chart['key']}"  # 这里可以扩展为实际的最新值
            })

        return SUCCESS_200({"summaries": summaries})

    except Exception as e:
        swanlog.error(f"Get experiment summary error: {e}")
        return DATA_ERROR_500(f"Failed to get experiment summary: {e}")


def get_experiment_charts(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获���实验图表信息

    GET /api/v1/experiments/{experiment_id}/charts

    Returns:
        实验图表数据
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 获取实验的图表信息（使用兼容格式）
        chart_list, namespace_list = get_exp_charts_compatible(experiment_id)

        return SUCCESS_200({
            "charts": chart_list,
            "namespaces": namespace_list,
        })

    except Exception as e:
        swanlog.error(f"Get experiment charts error: {e}")
        return DATA_ERROR_500(f"Failed to get experiment charts: {e}")



def get_recent_logs(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获取实验最近日志（从 ClickHouse 获取）

    GET /api/v1/experiments/{experiment_id}/recent_log

    Returns:
        实验日志信息
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 获取 run_id
        run_id = getattr(experiment, 'run_dir', None) or getattr(experiment, 'run_id', None)
        if not run_id:
            swanlog.warning(f"Experiment {experiment_id} has no run_id, using experiment_id as fallback")
            run_id = str(experiment_id)

        # 从 ClickHouse 获取最近的日志日期
        recent_dates = clickhouse_repository.get_recent_log_dates(run_id)

        # 获取最近的日志内容
        logs = clickhouse_repository.get_logs(run_id, limit=100)

        # 格式化日志消息
        log_messages = [log.get('message', '') for log in logs]

        return SUCCESS_200({
            "recent": recent_dates if recent_dates else [],
            "logs": log_messages if log_messages else ["No logs available"]
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        swanlog.error(f"Get recent logs error: {e}")
        swanlog.error(f"Full traceback: {error_details}")
        return DATA_ERROR_500(f"Failed to get recent logs: {e}")


def get_experiment_requirements(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获取实验依赖（优先从云端运行时信息获取）

    GET /api/v1/experiments/{experiment_id}/requirements

    Returns:
        实验依赖信息
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 从云端运行时信息获取数据
        try:
            runtime_info = CloudRuntimeInfo.select().where(
                CloudRuntimeInfo.experiment == experiment_id
            ).first()

            if runtime_info:
                # 解析 requirements 文件内容
                requirements_content = runtime_info.requirements or ''
                if requirements_content:
                    # 如果是文件内容，按行分割
                    if '\n' in requirements_content:
                        requirements_lines = requirements_content.strip().split('\n')
                    else:
                        # 单行内容
                        requirements_lines = [requirements_content]
                else:
                    requirements_lines = ["# No requirements information available"]

                # 解析 metadata 获取系统信息
                system_info = {}
                if runtime_info.metadata:
                    try:
                        system_info = ujson.loads(runtime_info.metadata)
                    except Exception as e:
                        swanlog.warning(f"Failed to parse metadata: {e}")

                # 解析 conda 环境信息
                conda_content = runtime_info.conda or ''

                return SUCCESS_200({
                    "requirements": requirements_lines,
                    "python_version": system_info.get('python_version'),
                    "platform": system_info.get('platform'),
                    "cuda_version": system_info.get('cuda_version'),
                    "conda": conda_content,
                    "metadata": runtime_info.metadata,
                    "config": runtime_info.config
                })
            else:
                swanlog.info(f"No cloud runtime info found for experiment {experiment_id}")
                return SUCCESS_200({
                    "requirements": ["# No requirements information available"],
                    "python_version": None,
                    "platform": None,
                    "cuda_version": None,
                    "conda": "",
                    "metadata": None,
                    "config": None
                })

        except Exception as e:
            swanlog.warning(f"Failed to get runtime info from cloud database: {e}")
            return SUCCESS_200({
                "requirements": ["# Error loading requirements information"],
                "python_version": None,
                "platform": None,
                "cuda_version": None,
                "conda": "",
                "metadata": None,
                "config": None
            })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        swanlog.error(f"Get experiment requirements error: {e}")
        swanlog.error(f"Full traceback: {error_details}")
        return DATA_ERROR_500(f"Failed to get experiment requirements: {e}")


# 为了兼容性，添加拼写错误的函数名
def get_experimet_charts(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    获取实验图表信息 (兼容拼写错误的函数名)

    这是 get_experiment_charts 的别名
    """
    return get_experiment_charts(experiment_id, _)


def get_experiment_logs_by_names(
    project_name: str,
    experiment_name: str,
    workspace: str = None,
    auth: Union[Account, APIKey] = Depends(validate_platform_api_key_dependency)
) -> Dict[str, Any]:
    """
    根据项目名称和实验名称获取实验日志

    GET /api/v1/experiments/logs
    Query Parameters:
        project_name: 项目名称
        experiment_name: 实验名称
        workspace: 工作空间（可选）

    Returns:
        实验日志信息
    """
    # JWT认证已通过依赖注入处理

    try:
        print(f"Fetching logs for project '{project_name}', experiment '{experiment_name}', workspace '{workspace}'")
        # 首先根据项目名称和实验名称找到实验
        experiment = experiment_repository.get_by_project_and_experiment_name(
            project_name=project_name,
            experiment_name=experiment_name,
            workspace=workspace
        )
        print(f'Fetched logs for project {project_name} and experiment {experiment_name}')
        if not experiment:
            return NOT_FOUND_404(f"Experiment '{experiment_name}' not found in project '{project_name}'")

        # 使用现有的 get_recent_logs 函数获取日志
        return get_recent_logs(experiment.id)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        swanlog.error(f"Get experiment logs by names error: {e}")
        swanlog.error(f"Full traceback: {error_details}")
        return DATA_ERROR_500(f"Failed to get experiment logs: {e}")


# ================================== 实验信息修改 ==================================

def update_experiment_info(
    experiment_id: int,
    request: Request,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    修改实验信息

    PUT /api/v1/experiments/{experiment_id}

    Body:
    {
        "name": "new_experiment_name",
        "description": "new experiment description"
    }

    Returns:
        更新后的实验信息
    """
    # JWT认证已通过依赖注入处理

    try:
        body = request.json()

        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 验证和格式化数据
        updates = {}
        if "name" in body:
            updates["name"] = body["name"].strip()

        if "description" in body:
            updates["description"] = check_desc_format(body["description"], False)

        # 更新实验信息
        updated_experiment = experiment_repository.update(experiment, **updates)
        if not updated_experiment:
            return DATA_ERROR_500("Failed to update experiment")

        swanlog.info(f"Updated experiment {experiment_id}: {updates}")

        return SUCCESS_200({
            "updates": updates,
            "experiment": experiment_repository.to_dict(updated_experiment)
        })

    except Exception as e:
        swanlog.error(f"Update experiment info error: {e}")
        return DATA_ERROR_500(f"Failed to update experiment info: {e}")


def update_experiment_status(
    experiment_id: int,
    request: Request,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    更新实验状态

    PUT /api/v1/experiments/{experiment_id}/status

    Body:
    {
        "status": 1,  // -1: crashed, 0: running, 1: finished
        "error": "error message"  // 可选，实验出错时的错误信息
    }

    Returns:
        更新结果
    """
    # JWT认证已通过依赖注入处理

    try:
        body = request.json()

        if 'status' not in body:
            return BAD_REQUEST_400("Missing required field: status")

        status = int(body['status'])
        error = body.get('error')

        # 验证状态值
        if status not in [-1, 0, 1]:
            return BAD_REQUEST_400("Invalid status value. Must be -1, 0, or 1")

        # 使用experiment_repository直接更新状态
        success = experiment_repository.update_status(
            experiment_id=experiment_id,
            status=status,
            error=error
        )

        if not success:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found or update failed")

        # 获取更新后的实验信息
        experiment = experiment_repository.get_by_id(experiment_id)
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


# ================================== 实验删除 ==================================

def delete_experiment(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    删除实验

    DELETE /api/v1/experiments/{experiment_id}

    Returns:
        删除结果
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # ���查实验是否正在运行
        if experiment.status == RUNNING_STATUS:
            return CONFLICT_409("Can't delete experiment since it is running")

        # 获取相关的图表信息用于清理
        charts = chart_repository.get_experiment_charts(experiment_id)

        # 删除实验（这会级联删除相关的图表、标签等）
        success = experiment_repository.delete(experiment)
        if not success:
            return DATA_ERROR_500("Failed to delete experiment from database")

        swanlog.info(f"Deleted experiment {experiment_id} with {len(charts)} charts")

        return SUCCESS_200({
            "deleted_experiment_id": str(experiment_id),
            "deleted_charts_count": len(charts)
        })

    except Exception as e:
        swanlog.error(f"Delete experiment error: {e}")
        return DATA_ERROR_500(f"Failed to delete experiment: {e}")


# ================================== 实验控制 ==================================

def stop_experiment(
    experiment_id: int,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    停止实验

    PUT /api/v1/experiments/{experiment_id}/stop

    Returns:
        停止实验后的状态信息
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 更新实验状态为停止
        from datetime import datetime
        updated_experiment = experiment_repository.update(
            experiment,
            status=-1,  # 停止状态
            finished_at=datetime.now()
        )

        if not updated_experiment:
            return DATA_ERROR_500("Failed to stop experiment")

        return SUCCESS_200({
            "id": experiment_id,
            "status": -1,
            "finished_at": updated_experiment.finished_at.isoformat() if updated_experiment.finished_at else None,
        })

    except Exception as e:
        swanlog.error(f"Stop experiment error: {e}")
        return DATA_ERROR_500(f"Failed to stop experiment: {e}")


def change_experiment_visibility(
    experiment_id: int,
    show: bool,
    _: None = Depends(validate_api_key_dependency)
) -> Dict[str, Any]:
    """
    修改实验是否可见

    PUT /api/v1/experiments/{experiment_id}/visibility

    Body:
    {
        "show": true  // 在多实验对比图表中，该实验是否可见
    }

    Returns:
        当前实验信息
    """
    # JWT认证已通过依赖注入处理

    try:
        # 验证实验存在
        experiment = experiment_repository.get_by_id(experiment_id)
        if not experiment:
            return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")

        # 更新可见性
        updated_experiment = experiment_repository.update(
            experiment,
            show=1 if show else 0
        )

        if not updated_experiment:
            return DATA_ERROR_500("Failed to update experiment visibility")

        return SUCCESS_200({
            "experiment": experiment_repository.to_dict(updated_experiment)
        })

    except Exception as e:
        swanlog.error(f"Change experiment visibility error: {e}")
        return DATA_ERROR_500(f"Failed to change experiment visibility: {e}")
