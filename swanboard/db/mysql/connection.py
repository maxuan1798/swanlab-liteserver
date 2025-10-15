#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL数据库连接管理模块
"""

import os
import threading
from typing import Optional, Dict, Any
from peewee import MySQLDatabase, OperationalError, InterfaceError, logger
from .config import MySQLConfig
from .models import cloud_db, CLOUD_MODELS
from swanboard.utils import swanlog
import logging

# Import AUTH_MODELS for table creation
try:
    from .auth_models import AUTH_MODELS
    _has_auth_models = True
except ImportError:
    AUTH_MODELS = []
    _has_auth_models = False

class MySQLConnectionManager:
    """MySQL连接管理器"""

    _instance = None
    # 使用可重入锁，避免同一线程重复获取导致死锁
    _lock = threading.RLock()

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
        # 实例级别也使用可重入锁
        self._lock = threading.RLock()

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

                # 启用 Peewee SQL 日志
                logging.basicConfig(level=logging.DEBUG)
                logger.setLevel(logging.DEBUG)

                # 准备 peewee kwargs，移除重复的 'database' 字段以避免重复传参
                peewee_kwargs = config.to_peewee_config()
                peewee_kwargs.pop('database', None)

                # 仅保留 MySQLDatabase 常用且被支持的参数
                allowed_keys = {'host', 'port', 'user', 'password', 'charset', 'autocommit'}
                filtered_kwargs = {k: v for k, v in peewee_kwargs.items() if k in allowed_keys}

                # 创建数据库连接：通过关键字参数传入，确保不会重复传递 database 或非支持参数
                self._db = MySQLDatabase(config.database, **filtered_kwargs)

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
            # Create cloud models tables
            self._db.create_tables(CLOUD_MODELS, safe=True)
            swanlog.debug("Cloud database tables created/verified")

            # Create authentication models tables if available
            if _has_auth_models and AUTH_MODELS:
                self._db.create_tables(AUTH_MODELS, safe=True)
                swanlog.debug("Authentication tables created/verified")
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

    def ensure_connected(self) -> bool:
        """
        确保云端MySQL数据库已连接

        Returns:
            bool: 连接成功返回True
        """
        swanlog.info("Ensuring MySQL is connected")
        if self.is_connected():
            return True
        swanlog.info("MySQL is not connected")
        with self._lock:
            # 双重检查锁定
            if self.is_connected():
                return True

            try:
                config = MySQLConfig.from_env()
                success = self.connect(config)
                if success:
                    swanlog.info("Cloud database connection established")
                else:
                    swanlog.error("Failed to establish cloud database connection")
                return success
            except Exception as e:
                swanlog.error(f"Failed to connect to cloud database: {e}")
                return False


    def validate_workspace(self, workspace: str) -> bool:
        """
        验证工作空间

        Args:
            workspace: 工作空间名称

        Returns:
            bool: 验证成功返回True
        """
        allowed_workspaces = os.getenv('SWANLAB_ALLOWED_WORKSPACES', '').split(',')
        if not allowed_workspaces or allowed_workspaces == ['']:
            return True  # 如果没有限制，允许所有工作空间

        return workspace in allowed_workspaces

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
