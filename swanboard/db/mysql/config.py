#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL配置管理类
支持从环境变量和配置文件加载MySQL连接信息
"""

import os
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class MySQLConfig:
    """MySQL数据库配置类"""

    host: str = 'localhost'
    port: int = 3306
    user: str = 'root'
    password: str = ''
    database: str = 'swanlab_cloud'
    charset: str = 'utf8mb4'
    autocommit: bool = True

    # 连接池配置
    max_connections: int = 20
    stale_timeout: int = 300
    timeout: int = 20

    @classmethod
    def from_env(cls) -> 'MySQLConfig':
        """从环境变量加载配置"""
        return cls(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'swanlab_cloud'),
            charset=os.getenv('MYSQL_CHARSET', 'utf8mb4'),
            autocommit=os.getenv('MYSQL_AUTOCOMMIT', 'true').lower() == 'true',
            max_connections=int(os.getenv('MYSQL_MAX_CONNECTIONS', '20')),
            stale_timeout=int(os.getenv('MYSQL_STALE_TIMEOUT', '300')),
            timeout=int(os.getenv('MYSQL_TIMEOUT', '20'))
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'MySQLConfig':
        """从字典加载配置"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__dataclass_fields__})

    def to_peewee_config(self) -> Dict[str, Any]:
        """转换为Peewee数据库配置"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'autocommit': self.autocommit,
            'max_connections': self.max_connections,
            'stale_timeout': self.stale_timeout,
            'timeout': self.timeout
        }

    def get_connection_string(self) -> str:
        """获取MySQL连接字符串"""
        return f"mysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def validate(self) -> bool:
        """验证配置是否有效"""
        required_fields = ['host', 'user', 'database']
        return all(getattr(self, field) for field in required_fields)