#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端同步管理器
提供本地数据与MySQL云端数据库的同步功能
"""

import threading
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from swankit.callback.models import ColumnInfo

from .mysql_models import (
    CloudProject, CloudExperiment, CloudChart, CloudTag,
    CloudNamespace, CloudSource, CloudDisplay, CloudBaseModel
)
from .mysql_connection import mysql_manager, is_cloud_db_connected
from swanboard.utils import swanlog


class CloudSyncManager:
    """云端同步管理器"""

    def __init__(self, workspace: str, user: str):
        """
        初始化同步管理器

        Args:
            workspace: 工作空间名称
            user: 用户名
        """
        self.workspace = workspace
        self.user = user
        self._lock = threading.Lock()

        # 缓存当前项目和实验
        self._current_project: Optional[CloudProject] = None
        self._current_experiment: Optional[CloudExperiment] = None

    def is_available(self) -> bool:
        """检查云端同步是否可用"""
        return is_cloud_db_connected()

    def sync_project(self, name: str, description: str = None) -> Optional[str]:
        """
        同步项目到云端

        Args:
            name: 项目名称
            description: 项目描述

        Returns:
            str: 云端项目ID，失败返回None
        """
        if not self.is_available():
            swanlog.warning("Cloud database not connected, skipping project sync")
            return None

        with self._lock:
            try:
                # 尝试获取现有项目
                project, created = CloudProject.get_or_create(
                    workspace=self.workspace,
                    name=name,
                    defaults={
                        'description': description or '',
                        'owner': self.user,
                        'visibility': 'private',
                        'experiment_count': 0,
                        'settings': '{}'
                    }
                )

                if not created and description:
                    # 更新项目描述
                    project.description = description
                    project.save()

                self._current_project = project
                swanlog.debug(f"Project '{name}' synced to cloud with ID: {project.id}")
                return str(project.id)

            except Exception as e:
                swanlog.error(f"Failed to sync project '{name}' to cloud: {e}")
                return None

    def sync_experiment(self, run_id: str, name: str, description: str = None,
                       colors: Tuple[str, str] = None, sort_order: int = None) -> Optional[str]:
        """
        同步实验到云端

        Args:
            run_id: 运行ID
            name: 实验名称
            description: 实验描述
            colors: 颜色主题 (light, dark)
            sort_order: 排序序号

        Returns:
            str: 云端实验ID，失败返回None
        """
        if not self.is_available() or not self._current_project:
            swanlog.warning("Cloud database not connected or no project, skipping experiment sync")
            return None

        with self._lock:
            try:
                light_color, dark_color = colors if colors else (None, None)

                # 如果没有提供sort_order，使用项目的实验计数
                if sort_order is None:
                    sort_order = self._current_project.experiment_count + 1

                # 尝试获取现有实验
                experiment, created = CloudExperiment.get_or_create(
                    project=self._current_project,
                    run_id=run_id,
                    defaults={
                        'name': name,
                        'description': description or '',
                        'status': 0,  # running
                        'visibility': True,
                        'sort_order': sort_order,
                        'light_color': light_color,
                        'dark_color': dark_color,
                        'pinned_opened': True,
                        'hidden_opened': False,
                        'settings': '{}',
                        'version': '1.0.0'
                    }
                )

                if created:
                    # 更新项目的实验计数
                    self._current_project.experiment_count += 1
                    self._current_project.save()
                else:
                    # 更新实验信息
                    experiment.name = name
                    experiment.description = description or ''
                    if colors:
                        experiment.light_color = light_color
                        experiment.dark_color = dark_color
                    experiment.save()

                self._current_experiment = experiment
                swanlog.debug(f"Experiment '{name}' (run_id: {run_id}) synced to cloud with ID: {experiment.id}")
                return str(experiment.id)

            except Exception as e:
                swanlog.error(f"Failed to sync experiment '{name}' to cloud: {e}")
                return None

    def sync_column(self, column_info: ColumnInfo) -> Optional[str]:
        """
        同步列信息到云端

        Args:
            column_info: 列信息对象

        Returns:
            str: 云端列ID，失败返回None
        """
        if not self.is_available() or not self._current_experiment:
            swanlog.warning("Cloud database not connected or no experiment, skipping column sync")
            return None

        # 只同步自定义指标
        if column_info.cls != "CUSTOM":
            return None

        with self._lock:
            try:
                chart_type = column_info.chart_type.value.chart_type

                # 创建或获取命名空间
                namespace, _ = CloudNamespace.get_or_create(
                    experiment=self._current_experiment,
                    name=column_info.section_name,
                    defaults={
                        'sort_order': column_info.section_sort
                    }
                )

                # 创建图表
                chart, created = CloudChart.get_or_create(
                    experiment=self._current_experiment,
                    key=column_info.key,
                    defaults={
                        'chart_type': chart_type,
                        'reference': column_info.chart_reference.lower(),
                        'config': '{}'
                    }
                )

                # 创建标签
                tag, _ = CloudTag.get_or_create(
                    experiment=self._current_experiment,
                    name=column_info.key,
                    defaults={
                        'tag_type': chart_type,
                        'folder': column_info.kid
                    }
                )

                # 创建数据源
                error_info = None
                if column_info.error is not None:
                    error_info = CloudBaseModel.dict_to_json({
                        "data_class": column_info.error.got,
                        "expected": column_info.error.expected,
                    })

                source, _ = CloudSource.get_or_create(
                    tag=tag,
                    chart=chart,
                    defaults={
                        'error_info': error_info
                    }
                )

                # 创建显示配置
                display, _ = CloudDisplay.get_or_create(
                    chart=chart,
                    namespace=namespace,
                    defaults={
                        'sort_order': None
                    }
                )

                swanlog.debug(f"Column '{column_info.key}' synced to cloud with chart ID: {chart.id}")
                return str(chart.id)

            except Exception as e:
                swanlog.error(f"Failed to sync column '{column_info.key}' to cloud: {e}")
                return None

    def sync_experiment_status(self, status: int, error: str = None) -> bool:
        """
        同步实验状态到云端

        Args:
            status: 实验状态 (-1: crashed, 0: running, 1: finished)
            error: 错误信息

        Returns:
            bool: 同步成功返回True
        """
        if not self.is_available() or not self._current_experiment:
            swanlog.warning("Cloud database not connected or no experiment, skipping status sync")
            return False

        with self._lock:
            try:
                self._current_experiment.status = status
                if status != 0:  # 实验结束
                    self._current_experiment.finished_at = datetime.now()

                # 如果有错误信息，可以存储在settings中
                if error:
                    settings = CloudBaseModel.json_to_dict(self._current_experiment.settings)
                    settings['error'] = error
                    self._current_experiment.settings = CloudBaseModel.dict_to_json(settings)

                self._current_experiment.save()
                swanlog.debug(f"Experiment status {status} synced to cloud")
                return True

            except Exception as e:
                swanlog.error(f"Failed to sync experiment status to cloud: {e}")
                return False

    def get_project_experiments(self, project_name: str) -> List[Dict[str, Any]]:
        """
        获取项目的所有实验

        Args:
            project_name: 项目名称

        Returns:
            List[Dict]: 实验列表
        """
        if not self.is_available():
            return []

        try:
            project = CloudProject.get(
                CloudProject.workspace == self.workspace,
                CloudProject.name == project_name
            )

            experiments = []
            for exp in project.experiments:
                experiments.append(exp.to_dict())

            return experiments

        except CloudProject.DoesNotExist:
            swanlog.warning(f"Project '{project_name}' not found in cloud")
            return []
        except Exception as e:
            swanlog.error(f"Failed to get project experiments: {e}")
            return []

    def get_experiment_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实验详情

        Args:
            run_id: 运行ID

        Returns:
            Dict: 实验详情，失败返回None
        """
        if not self.is_available():
            return None

        try:
            experiment = CloudExperiment.get(CloudExperiment.run_id == run_id)

            # 构建完整的实验信息
            details = experiment.to_dict()
            details['project'] = experiment.project.to_dict()
            details['charts'] = [chart.to_dict() for chart in experiment.charts]
            details['namespaces'] = [ns.to_dict() for ns in experiment.namespaces]

            return details

        except CloudExperiment.DoesNotExist:
            swanlog.warning(f"Experiment with run_id '{run_id}' not found in cloud")
            return None
        except Exception as e:
            swanlog.error(f"Failed to get experiment details: {e}")
            return None

    def cleanup(self):
        """清理资源"""
        with self._lock:
            self._current_project = None
            self._current_experiment = None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取同步统计信息

        Returns:
            Dict: 统计信息
        """
        if not self.is_available():
            return {'connected': False}

        try:
            project_count = CloudProject.select().where(
                CloudProject.workspace == self.workspace
            ).count()

            experiment_count = 0
            if self._current_project:
                experiment_count = CloudExperiment.select().where(
                    CloudExperiment.project == self._current_project
                ).count()

            return {
                'connected': True,
                'workspace': self.workspace,
                'user': self.user,
                'projects': project_count,
                'experiments': experiment_count,
                'current_project': self._current_project.name if self._current_project else None,
                'current_experiment': self._current_experiment.name if self._current_experiment else None
            }

        except Exception as e:
            swanlog.error(f"Failed to get sync stats: {e}")
            return {'connected': False, 'error': str(e)}