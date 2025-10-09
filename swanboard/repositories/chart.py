#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表仓库 - 处理图表、列、标签等相关的数据操作
"""

import json
from typing import Optional, List, Dict, Any

from .base import BaseRepository
from ..db.mysql.models import (
    CloudChart, CloudTag, CloudNamespace, CloudSource, CloudDisplay, CloudExperiment
)
from ..utils import swanlog


class ChartRepository(BaseRepository[CloudChart]):
    """图表仓库类"""

    def __init__(self):
        super().__init__(CloudChart)

    def sync_column(self, key: str, experiment_id: int, chart_type: str,
                   reference: str = 'step', section_name: str = 'default',
                   section_sort: int = 0, kid: str = '', error_info: dict = None) -> Optional[str]:
        """
        同步列/指标到云端

        Args:
            key: 指标键名
            experiment_id: 实验ID
            chart_type: 图表类型
            reference: 引用类型
            section_name: 分组名称
            section_sort: 分组排序
            kid: 文件夹路径
            error_info: 错误信息

        Returns:
            str: 图表ID，失败返回None
        """
        if not self.ensure_connection():
            swanlog.error("Cannot sync column: database not connected")
            return None

        try:
            # 验证实验存在
            experiment = CloudExperiment.get_by_id(experiment_id)
            if not experiment:
                swanlog.error(f"Experiment with id {experiment_id} not found")
                return None

            # 创建或获取图表
            chart, chart_created = CloudChart.get_or_create(
                experiment=experiment,
                key=key,
                defaults={
                    'chart_type': chart_type,
                    'reference': reference,
                    'config': '{}'
                }
            )

            if not chart_created:
                # 图表已存在，更新信息
                chart.chart_type = chart_type
                chart.reference = reference
                chart.save()

            # 创建或获取命名空间
            namespace, _ = CloudNamespace.get_or_create(
                name=section_name,
                defaults={'sort_order': section_sort}
            )

            # 创建或获取显示配置
            display, _ = CloudDisplay.get_or_create(
                chart=chart,
                namespace=namespace,
                defaults={'sort_order': None}
            )

            # 创建或获取标签
            tag, _ = CloudTag.get_or_create(
                experiment=experiment,
                name=key,
                defaults={
                    'tag_type': chart_type,
                    'folder': kid
                }
            )

            # 创建或获取数据源
            error_data = None
            if error_info:
                error_data = json.dumps({
                    "data_class": error_info.get("data_class"),
                    "expected": error_info.get("expected")
                })

            source, _ = CloudSource.get_or_create(
                tag=tag,
                chart=chart,
                defaults={'error_info': error_data}
            )

            swanlog.info(f"Synced column: {key} for experiment {experiment.name}")
            return str(chart.id)

        except Exception as e:
            swanlog.error(f"Failed to sync column '{key}': {e}")
            return None

    def get_experiment_charts(self, experiment_id: int) -> List[Dict[str, Any]]:
        """
        获取实验的所有图表

        Args:
            experiment_id: 实验ID

        Returns:
            List[Dict]: 图表列表
        """
        if not self.ensure_connection():
            return []

        try:
            charts = CloudChart.select().where(CloudChart.experiment == experiment_id)
            chart_list = []

            for chart in charts:
                chart_dict = self.to_dict(chart)

                # 添加相关信息
                chart_dict['sources'] = []
                for source in chart.sources:
                    source_dict = source.to_dict()
                    source_dict['tag'] = source.tag.to_dict() if source.tag else None
                    chart_dict['sources'].append(source_dict)

                chart_dict['displays'] = []
                for display in chart.displays:
                    display_dict = display.to_dict()
                    display_dict['namespace'] = display.namespace.to_dict() if display.namespace else None
                    chart_dict['displays'].append(display_dict)

                chart_list.append(chart_dict)

            return chart_list

        except Exception as e:
            swanlog.error(f"Failed to get experiment charts: {e}")
            return []

    def get_chart_by_key(self, experiment_id: int, key: str) -> Optional[CloudChart]:
        """
        根据键名获取图表

        Args:
            experiment_id: 实验ID
            key: 图表键名

        Returns:
            CloudChart: 图表实例，不存在返回None
        """
        if not self.ensure_connection():
            return None

        try:
            return CloudChart.get(
                (CloudChart.experiment == experiment_id) & (CloudChart.key == key)
            )
        except CloudChart.DoesNotExist:
            return None
        except Exception as e:
            swanlog.error(f"Failed to get chart by key '{key}': {e}")
            return None

    def update_chart_config(self, chart_id: int, config: Dict[str, Any]) -> bool:
        """
        更新图表配置

        Args:
            chart_id: 图表ID
            config: 配置数据

        Returns:
            bool: 更新成功返回True
        """
        chart = self.get_by_id(chart_id)
        if not chart:
            return False

        try:
            config_json = self.dict_to_json(config)
            return self.update(chart, config=config_json) is not None
        except Exception as e:
            swanlog.error(f"Failed to update chart config: {e}")
            return False


class NamespaceRepository(BaseRepository[CloudNamespace]):
    """命名空间仓库类 (workspace)"""

    def __init__(self):
        super().__init__(CloudNamespace)

    def get_all(self, page: int = 1, size: int = 20, keyword: Optional[str] = None) -> tuple[List[Dict[str, Any]], int]:
        """
        分页查询所有命名空间

        Args:
            page: 页码，从1开始
            size: 每页大小
            keyword: 搜索关键词

        Returns:
            tuple: (命名空间列表, 总数)
        """
        if not self.ensure_connection():
            return [], 0

        try:
            query = CloudNamespace.select()

            # 添加关键词搜索
            if keyword:
                query = query.where(CloudNamespace.name.contains(keyword))

            # 计算总数
            total = query.count()

            # 分页查询
            offset = (page - 1) * size
            namespaces = query.order_by(CloudNamespace.sort_order).offset(offset).limit(size)

            namespace_list = [self.to_dict(ns) for ns in namespaces]
            return namespace_list, total

        except Exception as e:
            swanlog.error(f"Failed to get all namespaces: {e}")
            return [], 0

    def get_by_name(self, name: str) -> Optional[CloudNamespace]:
        """
        根据名称获取命名空间

        Args:
            name: 命名空间名称

        Returns:
            CloudNamespace: 命名空间实例，不存在返回None
        """
        if not self.ensure_connection():
            return None

        try:
            return CloudNamespace.get(CloudNamespace.name == name)
        except CloudNamespace.DoesNotExist:
            return None
        except Exception as e:
            swanlog.error(f"Failed to get namespace by name '{name}': {e}")
            return None

    def create_namespace(self, name: str, sort_order: Optional[int] = None) -> Optional[CloudNamespace]:
        """
        创建新的命名空间

        Args:
            name: 命名空间名称
            sort_order: 排序顺序，如果不提供则自动设置为最大值+1

        Returns:
            CloudNamespace: 创建的命名空间实例，失败返回None
        """
        if not self.ensure_connection():
            return None

        try:
            # 检查是否已存在同名命名空间
            existing = self.get_by_name(name)
            if existing:
                swanlog.warning(f"Namespace with name '{name}' already exists")
                return None

            # 如果没有提供sort_order，则设置为最大值+1
            if sort_order is None:
                max_order = CloudNamespace.select().aggregate(CloudNamespace.sort_order.max())
                sort_order = (max_order or 0) + 1

            # 创建命名空间
            namespace = self.create(name=name, sort_order=sort_order)
            if namespace:
                swanlog.info(f"Created namespace: {name} with sort_order: {sort_order}")
            return namespace

        except Exception as e:
            swanlog.error(f"Failed to create namespace '{name}': {e}")
            return None

    def update_opened(self, namespace_id: int, opened: bool) -> bool:
        """
        更新命名空间的开启/关闭状态

        Args:
            namespace_id: 命名空间ID
            opened: 是否开启

        Returns:
            bool: 更新成功返回True
        """
        namespace = self.get_by_id(namespace_id)
        if not namespace:
            swanlog.error(f"Namespace with id {namespace_id} not found")
            return False

        try:
            return self.update(namespace, opened=opened) is not None
        except Exception as e:
            swanlog.error(f"Failed to update namespace opened status: {e}")
            return False

    def get_all_workspaces(self) -> List[Dict[str, Any]]:
        """
        获取所有工作空间（命名空间）列表

        Returns:
            List[Dict]: 工作空间列表，每个包含 name 和 project_count
        """
        if not self.ensure_connection():
            return []

        try:
            # 获取所有命名空间
            namespaces = CloudNamespace.select().order_by(CloudNamespace.sort_order)

            workspace_list = []
            for ns in namespaces:
                workspace_list.append({
                    'name': ns.name,
                    'id': ns.id,
                    'sort_order': ns.sort_order,
                    'opened': ns.opened,
                    'created_at': ns.created_at.isoformat() if ns.created_at else None
                })

            return workspace_list

        except Exception as e:
            swanlog.error(f"Failed to get all workspaces: {e}")
            return []


class TagRepository(BaseRepository[CloudTag]):
    """标签仓库类"""

    def __init__(self):
        super().__init__(CloudTag)

    def get_experiment_tag_folder(self, experiment_id: int, tag_name: str) -> Optional[str]:
        """
        根据实验ID和标签名获取标签文件夹路径

        Args:
            experiment_id: 实验ID
            tag_name: 标签名称

        Returns:
            str: 标签文件夹路径，不存在返回None
        """
        if not self.ensure_connection():
            return None

        try:
            tag = CloudTag.get(
                (CloudTag.experiment == experiment_id) & (CloudTag.name == tag_name)
            )
            return tag.folder if tag else None
        except CloudTag.DoesNotExist:
            return None
        except Exception as e:
            swanlog.error(f"Failed to get tag folder for experiment {experiment_id}, tag '{tag_name}': {e}")
            return None

    def get_experiment_tags(self, experiment_id: int) -> List[Dict[str, Any]]:
        """
        获取实验的所有标签

        Args:
            experiment_id: 实验ID

        Returns:
            List[Dict]: 标签列表
        """
        if not self.ensure_connection():
            return []

        try:
            tags = CloudTag.select().where(CloudTag.experiment == experiment_id)
            return [self.to_dict(tag) for tag in tags]

        except Exception as e:
            swanlog.error(f"Failed to get experiment tags: {e}")
            return []


# 全局仓库实例
chart_repository = ChartRepository()
namespace_repository = NamespaceRepository()
tag_repository = TagRepository()
