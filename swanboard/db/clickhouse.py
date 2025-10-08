#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ClickHouse 数据库连接管理
"""

import os
import threading
from typing import List, Dict, Any, Optional
from clickhouse_driver import Client
from ..utils import swanlog


class ClickHouseManager:
    """ClickHouse 连接管理器（使用线程本地存储）"""

    def __init__(self):
        # 使用线程本地存储，每个线程有独立的连接
        self._local = threading.local()

        # 从环境变量读取配置
        self.host = os.getenv('CLICKHOUSE_HOST', 'localhost')
        self.port = int(os.getenv('CLICKHOUSE_PORT', '9000'))
        self.user = os.getenv('CLICKHOUSE_USER', 'default')
        self.password = os.getenv('CLICKHOUSE_PASS', 'password123')
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'app')
        self._initialized = False

    def _get_client(self) -> Optional[Client]:
        """获取当前线程的客户端连接"""
        if not hasattr(self._local, 'client'):
            self._local.client = None
        return self._local.client

    def _set_client(self, client: Optional[Client]):
        """设置当前线程的客户端连接"""
        self._local.client = client

    def connect(self) -> bool:
        """连接到 ClickHouse（为当前线程创建连接）"""
        try:
            client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            # 测试连接
            client.execute('SELECT 1')
            self._set_client(client)

            if not self._initialized:
                swanlog.info(f"Connected to ClickHouse at {self.host}:{self.port}")
                self._initialized = True

            return True
        except Exception as e:
            swanlog.error(f"Failed to connect to ClickHouse: {e}")
            self._set_client(None)
            return False

    def is_connected(self) -> bool:
        """检查当前线程是否已连接"""
        client = self._get_client()
        return client is not None

    def ensure_connected(self) -> bool:
        """确保当前线程有可用连接"""
        if self.is_connected():
            return True
        return self.connect()

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """
        执行查询（自动管理连接）

        Args:
            query: SQL 查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        # 为每次查询创建新连接（最安全的方式）
        try:
            client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            result = client.execute(query, params or {})
            client.disconnect()
            return result
        except Exception as e:
            swanlog.error(f"Failed to execute ClickHouse query: {e}")
            swanlog.debug(f"Query: {query}")
            if params:
                swanlog.debug(f"Params: {params}")
            return []

    def disconnect(self):
        """断开当前线程的连接"""
        client = self._get_client()
        if client:
            try:
                client.disconnect()
            except:
                pass
            self._set_client(None)


# 全局 ClickHouse 管理器实例
clickhouse_manager = ClickHouseManager()
