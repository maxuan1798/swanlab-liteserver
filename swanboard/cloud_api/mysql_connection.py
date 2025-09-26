#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL数据库连接管理模块
"""

import threading
from typing import Optional, Dict, Any
from peewee import MySQLDatabase, OperationalError, InterfaceError
from .mysql_config import MySQLConfig
from .mysql_models import cloud_db, CLOUD_MODELS
from swanboard.utils import swanlog


class MySQLConnectionManager:
    """MySQL连接管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._db: Optional[MySQLDatabase] = None
        self._config: Optional[MySQLConfig] = None
        self._connected = False
        self._lock = threading.Lock()

    def connect(self, config: MySQLConfig) -> bool:
        """
        连接到MySQL数据库

        Args:
            config: MySQL配置对象

        Returns:
            bool: 连接成功返回True，失败返回False
        """
        with self._lock:
            if self._connected and self._config == config:
                return True

            try:
                # 验证配置
                if not config.validate():
                    swanlog.error("Invalid MySQL configuration")
                    return False

                # 创建数据库连接
                self._db = MySQLDatabase(
                    config.database,
                    **config.to_peewee_config()
                )

                # 测试连接
                self._db.connect()

                # 绑定模型到数据库
                cloud_db.initialize(self._db)

                # 创建表结构
                self._create_tables()

                self._config = config
                self._connected = True
                swanlog.info(f"Successfully connected to MySQL: {config.host}:{config.port}/{config.database}")
                return True

            except (OperationalError, InterfaceError) as e:
                swanlog.error(f"Failed to connect to MySQL: {e}")
                return False
            except Exception as e:
                swanlog.error(f"Unexpected error connecting to MySQL: {e}")
                return False

    def disconnect(self):
        """断开数据库连接"""
        with self._lock:
            if self._db and self._connected:
                try:
                    self._db.close()
                    swanlog.info("MySQL connection closed")
                except Exception as e:
                    swanlog.warning(f"Error closing MySQL connection: {e}")
                finally:
                    self._connected = False
                    self._db = None
                    self._config = None

    def _create_tables(self):
        """创建数据库表结构"""
        try:
            self._db.create_tables(CLOUD_MODELS, safe=True)
            swanlog.debug("Cloud database tables created/verified")
        except Exception as e:
            swanlog.error(f"Failed to create database tables: {e}")
            raise

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self._db is not None

    def get_database(self) -> Optional[MySQLDatabase]:
        """获取数据库实例"""
        return self._db if self._connected else None

    def test_connection(self) -> bool:
        """测试数据库连接"""
        if not self._connected or not self._db:
            return False

        try:
            # 执行简单查询测试连接
            self._db.execute_sql("SELECT 1")
            return True
        except Exception as e:
            swanlog.warning(f"Database connection test failed: {e}")
            return False

    def execute_raw_sql(self, sql: str, params: Optional[tuple] = None) -> Any:
        """
        执行原生SQL查询

        Args:
            sql: SQL语句
            params: 查询参数

        Returns:
            查询结果
        """
        if not self._connected or not self._db:
            raise RuntimeError("Database not connected")

        try:
            return self._db.execute_sql(sql, params or ())
        except Exception as e:
            swanlog.error(f"Failed to execute SQL: {sql}, Error: {e}")
            raise

    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        if not self._config:
            return {}

        return {
            'host': self._config.host,
            'port': self._config.port,
            'user': self._config.user,
            'database': self._config.database,
            'connected': self._connected
        }


# 全局连接管理器实例
mysql_manager = MySQLConnectionManager()


def connect_cloud_db(config: MySQLConfig) -> bool:
    """
    连接到云端数据库

    Args:
        config: MySQL配置

    Returns:
        bool: 连接成功返回True
    """
    return mysql_manager.connect(config)


def disconnect_cloud_db():
    """断开云端数据库连接"""
    mysql_manager.disconnect()


def is_cloud_db_connected() -> bool:
    """检查云端数据库是否已连接"""
    return mysql_manager.is_connected()


def get_cloud_db() -> Optional[MySQLDatabase]:
    """获取云端数据库实例"""
    return mysql_manager.get_database()


def test_cloud_db_connection() -> bool:
    """测试云端数据库连接"""
    return mysql_manager.test_connection()