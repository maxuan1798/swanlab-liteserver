#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目仓库 - 处理项目相关的数据操作
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BaseRepository
from ..db.mysql.models import CloudProject, CloudExperiment
from ..utils import swanlog


class ProjectRepository(BaseRepository[CloudProject]):
    """项目仓库类"""

    def __init__(self):
        super().__init__(CloudProject)

    def sync_project(self, name: str, workspace: str, description: str = None,
                    owner: str = None) -> Optional[str]:
        """
        同步项目到云端

        Args:
            name: 项目名称
            workspace: 工作空间
            description: 项目描述
            owner: 项目所有者

        Returns:
            str: 项目ID，失败返回None
        """
        if not self.ensure_connection():
            swanlog.error("Cannot sync project: database not connected")
            return None
        swanlog.info(f"Syncing project {name}")
        try:
            # 检查项目是否已存在
            existing_project = self.get_by_name_and_workspace(name, workspace)

            if existing_project:
                # 项目已存在，更新描述
                if description:
                    self.update(existing_project, description=description)
                return str(existing_project.id)

            # 创建新项目
            project_data = {
                'name': name,
                'workspace': workspace,
                'description': description or '',
                'owner': owner or os.getenv('SWANLAB_USER', 'unknown'),
                'visibility': 'private',
                'experiment_count': 0,
                'settings': '{}'
            }

            project = self.create(**project_data)
            if project:
                swanlog.info(f"Created cloud project: {name} (workspace: {workspace})")
                return str(project.id)

            return None

        except Exception as e:
            swanlog.error(f"Failed to sync project '{name}': {e}")
            return None

    def get_by_name_and_workspace(self, name: str, workspace: str) -> Optional[CloudProject]:
        """
        根据名称和工作空间获取项目

        Args:
            name: 项目名称
            workspace: 工作空间

        Returns:
            CloudProject: 项目实例，不存在返回None
        """
        if not self.ensure_connection():
            return None

        try:
            return CloudProject.get(
                (CloudProject.name == name) & (CloudProject.workspace == workspace)
            )
        except CloudProject.DoesNotExist:
            return None
        except Exception as e:
            swanlog.error(f"Failed to get project '{name}' in workspace '{workspace}': {e}")
            return None

    def get_workspace_projects(self, workspace: str) -> List[Dict[str, Any]]:
        """
        获取工作空间下的所有项目

        Args:
            workspace: 工作空间名称

        Returns:
            List[Dict]: 项目列表
        """
        if not self.ensure_connection():
            return []

        try:
            projects = CloudProject.select().where(CloudProject.workspace == workspace)
            project_list = []

            for project in projects:
                # 计算实验数量
                exp_count = CloudExperiment.select().where(CloudExperiment.project == project.id).count()

                project_dict = self.to_dict(project)
                project_dict['experiment_count'] = exp_count
                project_list.append(project_dict)

            return project_list

        except Exception as e:
            swanlog.error(f"Failed to get workspace projects: {e}")
            return []

    def increment_experiment_count(self, project_id: int) -> bool:
        """
        增加项目的实验计数

        Args:
            project_id: 项目ID

        Returns:
            bool: 更新成功返回True
        """
        project = self.get_by_id(project_id)
        if not project:
            return False

        return self.update(project, experiment_count=project.experiment_count + 1) is not None

    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目统计信息

        Args:
            project_id: 项目ID

        Returns:
            Dict: 统计信息
        """
        project = self.get_by_id(project_id)
        if not project:
            return {}

        try:
            # 统计实验数量
            exp_count = CloudExperiment.select().where(CloudExperiment.project == project_id).count()

            # 统计不同状态的实验
            running_count = CloudExperiment.select().where(
                (CloudExperiment.project == project_id) & (CloudExperiment.status == 0)
            ).count()

            finished_count = CloudExperiment.select().where(
                (CloudExperiment.project == project_id) & (CloudExperiment.status == 1)
            ).count()

            crashed_count = CloudExperiment.select().where(
                (CloudExperiment.project == project_id) & (CloudExperiment.status == -1)
            ).count()

            return {
                'project_id': project_id,
                'project_name': project.name,
                'workspace': project.workspace,
                'total_experiments': exp_count,
                'running_experiments': running_count,
                'finished_experiments': finished_count,
                'crashed_experiments': crashed_count,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None
            }

        except Exception as e:
            swanlog.error(f"Failed to get project stats: {e}")
            return {}


# 全局项目仓库实例
project_repository = ProjectRepository()
