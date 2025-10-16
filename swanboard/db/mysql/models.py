#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL云端数据库模型定义
与��地SQLite模型保持结构一致，但适配MySQL数据库
"""

from peewee import (
    MySQLDatabase, Model, CharField, IntegerField, TextField,
    ForeignKeyField, DateTimeField, BooleanField,
    Check, DatabaseProxy
)

# Handle JSONField import for different peewee versions
try:
    from peewee import JSONField
except ImportError:
    # Fallback for older peewee versions that don't have JSONField
    # Use TextField instead and handle JSON serialization manually
    JSONField = TextField
from datetime import datetime
from typing import Dict, Any, Optional, List
import json


# 数据库代理，在连接时绑定实际数据库
cloud_db = DatabaseProxy()


class CloudBaseModel(Model):
    """云端数据库基础模型���"""

    class Meta:
        database = cloud_db

    @staticmethod
    def json_to_dict(json_str: str) -> dict:
        """将JSON字符串转换为字典"""
        if not json_str:
            return {}
        try:
            return json.loads(json_str) if isinstance(json_str, str) else json_str
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def dict_to_json(data: dict) -> str:
        """将字典转换为JSON字符串"""
        if data is None:
            return ""
        try:
            return json.dumps(data) if not isinstance(data, str) else data
        except (TypeError, ValueError):
            return ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        for field_name, field in self._meta.fields.items():
            value = getattr(self, field_name, None)
            if isinstance(field, DateTimeField) and value:
                result[field_name] = value.isoformat()
            elif isinstance(field, ForeignKeyField) and value:
                result[field_name] = value.id
            else:
                result[field_name] = value
        return result

    # 新增：统一将查询/模型/列表 等结果转换为 dict 列表，兼容原代码中使用的 search2list
    @classmethod
    def search2list(cls, items) -> List[Dict[str, Any]]:
        """
        将模型实例、模型列表或 dict 列表转换为 dict 列表，兼容不同 ORM/返回结构。
        - 如果 items 为 None -> 返回 []
        - 如果 items 为单个实例 -> 返回 [instance.to_dict()]
        - 如果 items 为可迭代 -> 遍历并转换每一项（支持 dict / model 有 to_dict / fallback 使用 __dict__）
        """
        if items is None:
            return []
        # 如果不是可迭代对象（例如单个模型实例），包装为列表
        try:
            iter(items)
        except TypeError:
            items = [items]
        result: List[Dict[str, Any]] = []
        for it in items:
            if it is None:
                continue
            if isinstance(it, dict):
                result.append(it)
                continue
            # 优先使用模型提供的 to_dict 方法
            if hasattr(it, "to_dict") and callable(getattr(it, "to_dict")):
                try:
                    result.append(it.to_dict())
                    continue
                except Exception:
                    pass
            # Peewee model fallback: 使用 _meta.fields 获取字段值
            try:
                fields = getattr(it, "_meta", None)
                if fields and hasattr(fields, "fields"):
                    d = {}
                    for fname in fields.fields:
                        try:
                            d[fname] = getattr(it, fname)
                        except Exception:
                            d[fname] = None
                    result.append(d)
                    continue
            except Exception:
                pass
            # 最后回退到 __dict__（去掉私有属性）
            try:
                raw = getattr(it, "__dict__", {})
                cleaned = {k: v for k, v in raw.items() if not k.startswith("_")}
                result.append(cleaned)
                continue
            except Exception:
                # 无法转换，跳过
                continue
        return result


class CloudProject(CloudBaseModel):
    """云端项目表"""

    # 默认的项目id应该是1
    DEFAULT_PROJECT_ID = 1

    id = IntegerField(primary_key=True)
    name = CharField(max_length=100, unique=True, index=True)
    description = TextField(null=True)
    workspace = CharField(max_length=100, index=True)  # 工作空间
    owner = CharField(max_length=100, index=True)  # 项目所有者
    visibility = CharField(max_length=20, default='private')  # public, private, internal

    # 统计信息
    experiment_count = IntegerField(default=0)

    # 配置信息
    settings = TextField(null=True)  # JSON格式的项目设置

    # 时间戳
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cloud_projects'
        indexes = (
            (('workspace', 'name'), True),  # 在同一工作空间内项目名唯一
        )

    def save(self, *args, **kwargs):
        """保存时自动更新时间戳"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class CloudExperiment(CloudBaseModel):
    """云端实验表"""

    # 实验运行时状态符
    RUNNING_STATUS = 0
    # 实验停止时状态符
    STOPPED_STATUS = -1
    # 实验结束时状态符
    FINISHED_STATUS = 1

    id = IntegerField(primary_key=True)
    project = ForeignKeyField(CloudProject, backref='experiments', on_delete='CASCADE')

    # 实验基本信息
    name = CharField(max_length=100, index=True)
    run_id = CharField(max_length=100, unique=True, index=True)
    description = TextField(null=True)

    # 实验状态
    status = IntegerField(default=0)  # -1: crashed, 0: running, 1: finished
    visibility = BooleanField(default=True)

    # 排序和标识
    sort_order = IntegerField()

    # 颜色主题
    light_color = CharField(max_length=20, null=True)
    dark_color = CharField(max_length=20, null=True)

    # UI状态
    pinned_opened = BooleanField(default=True)
    hidden_opened = BooleanField(default=False)

    # 扩展配置
    settings = TextField(null=True)  # JSON格式
    version = CharField(max_length=30)

    # 时间戳
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    finished_at = DateTimeField(null=True)

    class Meta:
        table_name = 'cloud_experiments'
        indexes = (
            (('project', 'name'), True),  # 同一项目内实验名唯一
            (('project', 'sort_order'), True),  # 同一项目内排序唯一
        )
        constraints = [Check('sort_order >= 0')]

    def save(self, *args, **kwargs):
        """保存时自动更新时间戳"""
        self.updated_at = datetime.now()
        if self.status != 0 and not self.finished_at:
            self.finished_at = datetime.now()
        return super().save(*args, **kwargs)


class CloudNamespace(CloudBaseModel):
    """云端命名空间表"""

    id = IntegerField(primary_key=True)
    name = CharField(max_length=100, unique=True, index=True)  # 移除experiment关联，全局唯一
    sort_order = IntegerField(null=True)
    opened = BooleanField(default=True)  # namespace是否打开显示

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cloud_namespaces'

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class CloudChart(CloudBaseModel):
    """云端图表表"""

    id = IntegerField(primary_key=True)
    experiment = ForeignKeyField(CloudExperiment, backref='charts', on_delete='CASCADE')

    key = CharField(max_length=255, index=True)  # 图表键名
    chart_type = CharField(max_length=50)  # 图表类型
    reference = CharField(max_length=20)  # 引用类型: step, time, epoch等

    config = TextField(null=True)  # JSON格式的图表配置

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cloud_charts'
        indexes = (
            (('experiment', 'key'), True),  # 同一实验内图表键唯一
        )

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class CloudTag(CloudBaseModel):
    """云端标签表"""

    id = IntegerField(primary_key=True)
    experiment = ForeignKeyField(CloudExperiment, backref='tags', on_delete='CASCADE')

    name = CharField(max_length=255, index=True)
    tag_type = CharField(max_length=50)
    folder = CharField(max_length=255, null=True)  # 文件夹路径

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cloud_tags'

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class CloudSource(CloudBaseModel):
    """云端数据源表"""

    id = IntegerField(primary_key=True)
    tag = ForeignKeyField(CloudTag, backref='sources', on_delete='CASCADE')
    chart = ForeignKeyField(CloudChart, backref='sources', on_delete='CASCADE')

    error_info = TextField(null=True)  # JSON格式的错误信息

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cloud_sources'

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class CloudDisplay(CloudBaseModel):
    """云端显示配置表"""

    id = IntegerField(primary_key=True)
    chart = ForeignKeyField(CloudChart, backref='displays', on_delete='CASCADE')
    namespace = ForeignKeyField(CloudNamespace, backref='displays', on_delete='CASCADE')

    sort_order = IntegerField(null=True)

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cloud_displays'

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class CloudRuntimeInfo(CloudBaseModel):
    """云端运行时信息表"""

    id = IntegerField(primary_key=True)
    experiment = ForeignKeyField(CloudExperiment, backref='runtime_info', on_delete='CASCADE')

    # 运行时信息字段
    requirements = TextField(null=True)  # requirements.txt内容
    metadata = TextField(null=True)      # metadata JSON内容
    config = TextField(null=True)        # config YAML内容
    conda = TextField(null=True)         # conda environment YAML内容

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'cloud_runtime_info'

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


# 所有云端模型的列表，用于批量操作
CLOUD_MODELS = [
    CloudProject,
    CloudExperiment,
    CloudNamespace,
    CloudChart,
    CloudTag,
    CloudSource,
    CloudDisplay,
    CloudRuntimeInfo
]
