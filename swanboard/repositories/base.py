#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础仓库类 - 提供通用的数据访问方法
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic
from datetime import datetime

from ..db.mysql.models import CloudBaseModel
from ..db.mysql.connection import mysql_manager as connection_manager
from ..utils import swanlog

T = TypeVar('T', bound=CloudBaseModel)


class BaseRepository(Generic[T], ABC):
    """基础仓库类"""

    def __init__(self, model_class: Type[T]):
        """
        初始化仓库

        Args:
            model_class: 数据模型类
        """
        self.model_class = model_class
        self.connection_manager = connection_manager

    def ensure_connection(self) -> bool:
        """确保数据库连接"""
        return self.connection_manager.ensure_connected()

    def is_available(self) -> bool:
        """检查仓库是否可用"""
        return self.connection_manager.is_connected()

    def create(self, **data) -> Optional[T]:
        """
        创建新记录

        Args:
            **data: 创建数据

        Returns:
            T: 创建的模型实例，失败返回None
        """
        if not self.ensure_connection():
            swanlog.error(f"Cannot create {self.model_class.__name__}: database not connected")
            return None

        try:
            instance = self.model_class.create(**data)
            swanlog.debug(f"Created {self.model_class.__name__} with ID: {instance.id}")
            return instance
        except Exception as e:
            swanlog.error(f"Failed to create {self.model_class.__name__}: {e}")
            return None

    def get_by_id(self, id: int) -> Optional[T]:
        """
        根据ID获取记录

        Args:
            id: 记录ID

        Returns:
            T: 模型实例，不存在返回None
        """
        if not self.ensure_connection():
            return None

        try:
            return self.model_class.get_by_id(id)
        except self.model_class.DoesNotExist:
            return None
        except Exception as e:
            swanlog.error(f"Failed to get {self.model_class.__name__} by ID {id}: {e}")
            return None

    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **conditions) -> tuple[Optional[T], bool]:
        """
        获取或创建记录

        Args:
            defaults: 创建时的默认值
            **conditions: 查询条件

        Returns:
            tuple: (实例, 是否新创建)
        """
        if not self.ensure_connection():
            return None, False

        try:
            instance, created = self.model_class.get_or_create(defaults=defaults, **conditions)
            return instance, created
        except Exception as e:
            swanlog.error(f"Failed to get_or_create {self.model_class.__name__}: {e}")
            return None, False

    def update(self, instance: T, **data) -> Optional[T]:
        """
        更新记录

        Args:
            instance: 要更新的实例
            **data: 更新数据

        Returns:
            T: 更新后的实例
        """
        if not self.ensure_connection():
            return None

        try:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            # 自动更新时间戳
            if hasattr(instance, 'updated_at'):
                instance.updated_at = datetime.now()

            instance.save()
            swanlog.debug(f"Updated {self.model_class.__name__} ID: {instance.id}")
            return instance
        except Exception as e:
            swanlog.error(f"Failed to update {self.model_class.__name__}: {e}")
            return None

    def delete(self, instance: T) -> bool:
        """
        删除记录

        Args:
            instance: 要删除的实例

        Returns:
            bool: 删除成功返回True
        """
        if not self.ensure_connection():
            return False

        try:
            instance.delete_instance()
            swanlog.debug(f"Deleted {self.model_class.__name__} ID: {instance.id}")
            return True
        except Exception as e:
            swanlog.error(f"Failed to delete {self.model_class.__name__}: {e}")
            return False

    def list_all(self) -> List[T]:
        """
        获取所有记录

        Returns:
            List[T]: 记录列表
        """
        if not self.ensure_connection():
            return []

        try:
            return list(self.model_class.select())
        except Exception as e:
            swanlog.error(f"Failed to list all {self.model_class.__name__}: {e}")
            return []

    def count(self, **conditions) -> int:
        """
        统计记录数量

        Args:
            **conditions: 查询条件

        Returns:
            int: 记录数量
        """
        if not self.ensure_connection():
            return 0

        try:
            query = self.model_class.select()
            for key, value in conditions.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
            return query.count()
        except Exception as e:
            swanlog.error(f"Failed to count {self.model_class.__name__}: {e}")
            return 0

    def to_dict(self, instance: T) -> Dict[str, Any]:
        """
        将模型实例转换为字典

        Args:
            instance: 模型实例

        Returns:
            Dict: 字典表示
        """
        if hasattr(instance, 'to_dict'):
            return instance.to_dict()

        # 手动构建字典
        result = {}
        for field_name, field in instance._meta.fields.items():
            value = getattr(instance, field_name, None)
            if isinstance(value, datetime) and value:
                result[field_name] = value.isoformat()
            elif hasattr(value, 'id'):  # 外键
                result[field_name] = value.id
            else:
                result[field_name] = value
        return result

    def json_to_dict(self, json_str: str) -> dict:
        """将JSON字符串转换为字典"""
        return CloudBaseModel.json_to_dict(json_str)

    def dict_to_json(self, data: dict) -> str:
        """将字典转换为JSON字符串"""
        return CloudBaseModel.dict_to_json(data)
