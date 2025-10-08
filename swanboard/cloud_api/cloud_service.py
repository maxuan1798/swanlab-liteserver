#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端同步管理器
提供本地数据与MySQL云端数据库的同步功能
"""

import threading
from typing import Optional, Dict, Any, List, Tuple
from swankit.callback.models import ColumnInfo

from ..repositories import (
    connection_manager, project_repository, experiment_repository, chart_repository
)
from ..db.mysql.models import CloudRuntimeInfo
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

        # 缓存当前项目和实验ID
        self._current_project_id: Optional[str] = None
        self._current_experiment_id: Optional[str] = None

    def is_available(self) -> bool:
        """检查云端同步是否可用"""
        return connection_manager.is_connected()

    def sync_project(self, name: str, description: str = None) -> Optional[str]:
        """
        同步项目到云端

        Args:
            name: 项目名称
            description: 项目描述

        Returns:
            str: 云端项目ID，失败返回None
        """
        swanlog.info("Cloud database sync")
        if not connection_manager.ensure_connected():
            swanlog.warning("Cloud database not connected, skipping project sync")
            return None

        with self._lock:
            try:
                swanlog.info(f"Syncing project {name}")
                project_id = project_repository.sync_project(
                    name=name,
                    workspace=self.workspace,
                    description=description,
                    owner=self.user
                )

                if project_id:
                    self._current_project_id = project_id
                    swanlog.debug(f"Project '{name}' synced to cloud with ID: {project_id}")

                return project_id

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
        if not connection_manager.ensure_connected() or not self._current_project_id:
            swanlog.warning("Cloud database not connected or no project, skipping experiment sync")
            return None

        with self._lock:
            try:
                experiment_id = experiment_repository.sync_experiment(
                    run_id=run_id,
                    name=name,
                    project_id=int(self._current_project_id),
                    description=description,
                    colors=colors,
                    sort_order=sort_order
                )

                if experiment_id:
                    self._current_experiment_id = experiment_id
                    swanlog.debug(f"Experiment '{name}' (run_id: {run_id}) synced to cloud with ID: {experiment_id}")

                return experiment_id

            except Exception as e:
                swanlog.error(f"Failed to sync experiment '{name}' to cloud: {e}")
                return None

    def sync_runtime_info(self, requirements: str = None, metadata: str = None,
                         config: str = None, conda: str = None) -> Optional[str]:
        """
        同步实验运行时信息到云端

        Args:
            requirements: requirements.txt内容
            metadata: metadata JSON内容
            config: config YAML内容
            conda: conda environment YAML内容

        Returns:
            str: 云端运行时信息ID，失败返回None
        """
        if not connection_manager.ensure_connected() or not self._current_experiment_id:
            swanlog.warning("Cloud database not connected or no experiment, skipping runtime info sync")
            return None

        with self._lock:
            try:
                # 检查是否已存在运行时信息
                existing = CloudRuntimeInfo.select().where(
                    CloudRuntimeInfo.experiment == int(self._current_experiment_id)
                ).first()

                if existing:
                    # 更新现有记录
                    if requirements is not None:
                        existing.requirements = requirements
                    if metadata is not None:
                        existing.metadata = metadata
                    if config is not None:
                        existing.config = config
                    if conda is not None:
                        existing.conda = conda

                    existing.save()
                    runtime_id = str(existing.id)
                    swanlog.debug(f"Runtime info updated for experiment ID: {self._current_experiment_id}")
                else:
                    # 创建新记录
                    runtime_info = CloudRuntimeInfo.create(
                        experiment=int(self._current_experiment_id),
                        requirements=requirements,
                        metadata=metadata,
                        config=config,
                        conda=conda
                    )
                    runtime_id = str(runtime_info.id)
                    swanlog.debug(f"Runtime info created for experiment ID: {self._current_experiment_id}")

                return runtime_id

            except Exception as e:
                swanlog.error(f"Failed to sync runtime info to cloud: {e}")
                return None

    def sync_column(self, column_info: ColumnInfo) -> Optional[str]:
        """
        同步列信息到云端

        Args:
            column_info: 列信息对象

        Returns:
            str: 云端列ID，失败返回None
        """
        if not connection_manager.ensure_connected() or not self._current_experiment_id:
            swanlog.warning("Cloud database not connected or no experiment, skipping column sync")
            return None

        # 只同步自定义指标
        if column_info.cls != "CUSTOM":
            return None

        with self._lock:
            try:
                chart_type = column_info.chart_type.value.chart_type

                # 处理错误信息
                error_info = None
                if column_info.error is not None:
                    error_info = {
                        "data_class": column_info.error.got,
                        "expected": column_info.error.expected,
                    }

                chart_id = chart_repository.sync_column(
                    key=column_info.key,
                    experiment_id=int(self._current_experiment_id),
                    chart_type=chart_type,
                    reference=column_info.chart_reference.lower(),
                    section_name=column_info.section_name,
                    section_sort=column_info.section_sort,
                    kid=column_info.kid,
                    error_info=error_info
                )

                if chart_id:
                    swanlog.debug(f"Column '{column_info.key}' synced to cloud with chart ID: {chart_id}")

                return chart_id

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
        if not connection_manager.ensure_connected() or not self._current_experiment_id:
            swanlog.warning("Cloud database not connected or no experiment, skipping status sync")
            return False

        with self._lock:
            try:
                success = experiment_repository.update_status(
                    experiment_id=int(self._current_experiment_id),
                    status=status,
                    error=error
                )

                if success:
                    swanlog.debug(f"Experiment status {status} synced to cloud")

                return success

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
        if not connection_manager.ensure_connected():
            return []

        try:
            project = project_repository.get_by_name_and_workspace(project_name, self.workspace)
            if not project:
                swanlog.warning(f"Project '{project_name}' not found in cloud")
                return []

            return experiment_repository.get_project_experiments(project.id)

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
        if not connection_manager.ensure_connected():
            return None

        try:
            return experiment_repository.get_experiment_details(run_id)

        except Exception as e:
            swanlog.error(f"Failed to get experiment details: {e}")
            return None

    def get_experiment_runtime_info(self, experiment_id: int = None) -> Optional[Dict[str, Any]]:
        """
        获取实验运行时信息

        Args:
            experiment_id: 实验ID，如果不提供则使用当前实验

        Returns:
            Dict: 运行时信息，失败返回None
        """
        if not connection_manager.ensure_connected():
            return None

        exp_id = experiment_id or (int(self._current_experiment_id) if self._current_experiment_id else None)
        if not exp_id:
            swanlog.warning("No experiment ID provided for runtime info query")
            return None

        try:
            runtime_info = CloudRuntimeInfo.select().where(
                CloudRuntimeInfo.experiment == exp_id
            ).first()

            if runtime_info:
                return runtime_info.to_dict()
            else:
                return None

        except Exception as e:
            swanlog.error(f"Failed to get runtime info: {e}")
            return None

    def cleanup(self):
        """清理资源"""
        with self._lock:
            self._current_project_id = None
            self._current_experiment_id = None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取同步统计信息

        Returns:
            Dict: 统计信息
        """
        if not connection_manager.ensure_connected():
            return {'connected': False}

        try:
            # 获取工作空间项目统计
            workspace_projects = project_repository.get_workspace_projects(self.workspace)
            project_count = len(workspace_projects)

            experiment_count = 0
            current_project_name = None
            current_experiment_name = None

            if self._current_project_id:
                current_project = project_repository.get_by_id(int(self._current_project_id))
                if current_project:
                    current_project_name = current_project.name
                    project_experiments = experiment_repository.get_project_experiments(current_project.id)
                    experiment_count = len(project_experiments)

            if self._current_experiment_id:
                current_experiment = experiment_repository.get_by_id(int(self._current_experiment_id))
                if current_experiment:
                    current_experiment_name = current_experiment.name

            return {
                'connected': True,
                'workspace': self.workspace,
                'user': self.user,
                'projects': project_count,
                'experiments': experiment_count,
                'current_project': current_project_name,
                'current_experiment': current_experiment_name
            }

        except Exception as e:
            swanlog.error(f"Failed to get sync stats: {e}")
            return {'connected': False, 'error': str(e)}

    # 便捷方法，保持与原版本的兼容性
    def get_current_project(self):
        """获取当前项目实例"""
        if self._current_project_id:
            return project_repository.get_by_id(int(self._current_project_id))
        return None

    def get_current_experiment(self):
        """获取当前实验实例"""
        if self._current_experiment_id:
            return experiment_repository.get_by_id(int(self._current_experiment_id))
        return None
