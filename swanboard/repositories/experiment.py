#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实验仓库 - 处理实验相关的数据操作
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .base import BaseRepository
from ..db.mysql.models import CloudExperiment, CloudProject
from ..utils import swanlog, generate_color


class ExperimentRepository(BaseRepository[CloudExperiment]):
    """实验仓库类"""

    def __init__(self):
        super().__init__(CloudExperiment)

    def sync_experiment(self, run_id: str, name: str, project_id: int,
                       description: str = None, colors: Tuple[str, str] = None,
                       sort_order: int = None) -> Optional[str]:
        """
        同步实验到云端

        Args:
            run_id: 运行ID
            name: 实验名称
            project_id: 项目ID
            description: 实验描述
            colors: 颜色主题 (light, dark)
            sort_order: 排序序号

        Returns:
            str: 实验ID，失败返回None
        """
        if not self.ensure_connection():
            swanlog.error("Cannot sync experiment: database not connected")
            return None

        try:
            # 验证项目存在
            project = CloudProject.get_by_id(project_id)
            if not project:
                swanlog.error(f"Project with id {project_id} not found")
                return None

            # 处理颜色
            if colors and len(colors) >= 2:
                light_color, dark_color = colors[0], colors[1]
            else:
                light_color, dark_color = generate_color()

            # 检查实验是否已存在
            existing_exp = self.get_by_run_id(run_id)

            if existing_exp:
                # 实验已存在，更新信息
                update_data = {
                    'name': name,
                    'description': description or '',
                    'light_color': light_color,
                    'dark_color': dark_color
                }
                self.update(existing_exp, **update_data)
                return str(existing_exp.id)

            # 获取项目中实验数量作为sort_order
            if sort_order is None:
                sort_order = self.count(project=project_id) + 1

            # 创建新实验
            experiment_data = {
                'name': name,
                'run_id': run_id,
                'description': description or '',
                'project': project,
                'light_color': light_color,
                'dark_color': dark_color,
                'sort_order': sort_order,
                'status': 0,  # running
                'visibility': True,
                'pinned_opened': True,
                'hidden_opened': False,
                'settings': '{}',
                'version': '1.0.0'
            }

            experiment = self.create(**experiment_data)
            if experiment:
                swanlog.info(f"Created cloud experiment: {name} (run_id: {run_id})")
                return str(experiment.id)

            return None

        except Exception as e:
            swanlog.error(f"Failed to sync experiment '{name}': {e}")
            return None

    def get_by_run_id(self, run_id: str) -> Optional[CloudExperiment]:
        """
        根据运行ID获取实验

        Args:
            run_id: 运行ID

        Returns:
            CloudExperiment: 实验实例，不存在返回None
        """
        if not self.ensure_connection():
            return None

        try:
            return CloudExperiment.get(CloudExperiment.run_id == run_id)
        except CloudExperiment.DoesNotExist:
            return None
        except Exception as e:
            swanlog.error(f"Failed to get experiment by run_id '{run_id}': {e}")
            return None

    def get_project_experiments(self, project_id: int) -> List[Dict[str, Any]]:
        """
        获取项目下的所有实验

        Args:
            project_id: 项目ID

        Returns:
            List[Dict]: 实验列表
        """
        if not self.ensure_connection():
            return []

        try:
            experiments = CloudExperiment.select().where(
                CloudExperiment.project == project_id
            ).order_by(CloudExperiment.sort_order)

            experiment_list = []
            for exp in experiments:
                exp_dict = self.to_dict(exp)
                experiment_list.append(exp_dict)

            return experiment_list

        except Exception as e:
            swanlog.error(f"Failed to get project experiments: {e}")
            return []

    def update_status(self, experiment_id: int, status: int, error: str = None) -> bool:
        """
        更新实验状态

        Args:
            experiment_id: 实验ID
            status: 状态值 (-1: crashed, 0: running, 1: finished)
            error: 错误信息

        Returns:
            bool: 更新成功返回True
        """
        if status not in [-1, 0, 1]:
            swanlog.error("Invalid status value. Must be -1, 0, or 1")
            return False

        experiment = self.get_by_id(experiment_id)
        if not experiment:
            swanlog.error(f"Experiment with id {experiment_id} not found")
            return False

        try:
            update_data = {'status': status}

            # 如果不是运行状态，设置完成时间
            if status != 0:
                update_data['finished_at'] = datetime.now()

            # 如果有错误信息，存储在settings中
            if error:
                settings = self.json_to_dict(experiment.settings)
                settings['error'] = error
                update_data['settings'] = self.dict_to_json(settings)

            result = self.update(experiment, **update_data)
            if result:
                status_text = {-1: "crashed", 0: "running", 1: "finished"}[status]
                swanlog.info(f"Updated experiment {experiment.name} status to: {status_text}")
                return True

            return False

        except Exception as e:
            swanlog.error(f"Failed to update experiment status: {e}")
            return False

    def get_experiment_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实验详情

        Args:
            run_id: 运行ID

        Returns:
            Dict: 实验详情，失败返回None
        """
        experiment = self.get_by_run_id(run_id)
        if not experiment:
            return None

        try:
            # 构建完整的实验信息
            details = self.to_dict(experiment)
            details['project'] = experiment.project.to_dict() if experiment.project else None
            details['charts'] = [chart.to_dict() for chart in experiment.charts]
            details['namespaces'] = [ns.to_dict() for ns in experiment.namespaces]

            return details

        except Exception as e:
            swanlog.error(f"Failed to get experiment details: {e}")
            return None

    def get_experiments_by_status(self, status: int, project_id: int = None) -> List[Dict[str, Any]]:
        """
        根据状态获取实验列表

        Args:
            status: 实验状态
            project_id: 项目ID（可选）

        Returns:
            List[Dict]: 实验列表
        """
        if not self.ensure_connection():
            return []

        try:
            query = CloudExperiment.select().where(CloudExperiment.status == status)

            if project_id is not None:
                query = query.where(CloudExperiment.project == project_id)

            experiments = []
            for exp in query.order_by(CloudExperiment.updated_at.desc()):
                experiments.append(self.to_dict(exp))

            return experiments

        except Exception as e:
            swanlog.error(f"Failed to get experiments by status: {e}")
            return []

    def get_by_project_and_experiment_name(self, project_name: str, experiment_name: str, workspace: str = None) -> Optional[CloudExperiment]:
        """
        根据项目名称和实验名称获取实验

        Args:
            project_name: 项目名称
            experiment_name: 实验名称
            workspace: 工作空间（可选）

        Returns:
            CloudExperiment: 实验实例，不存在返回None
        """
        if not self.ensure_connection():
            return None

        try:
            # 首先找到项目
            from .project import project_repository
            project = project_repository.get_by_name_and_workspace(project_name, workspace)
            if not project:
                swanlog.warning(f"Project '{project_name}' not found in workspace '{workspace}'")
                return None

            # 然后找到实验
            query = CloudExperiment.select().where(
                (CloudExperiment.project == project.id) &
                (CloudExperiment.name == experiment_name)
            )

            return query.first()

        except CloudExperiment.DoesNotExist:
            swanlog.warning(f"Experiment '{experiment_name}' not found in project '{project_name}'")
            return None
        except Exception as e:
            swanlog.error(f"Failed to get experiment by project and experiment name: {e}")
            return None


# 全局实验仓库实例
experiment_repository = ExperimentRepository()
