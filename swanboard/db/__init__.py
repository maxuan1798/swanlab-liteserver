#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2024-01-16 10:52:10
@File: swanboard\db\__init__.py
@IDE: vscode
@Description:
    数据库模块 - 云端版本
    仅包含 MySQL 和 ClickHouse 支持，SQLite 已移除
"""

# MySQL 云端数据库
from .mysql import (
    CloudProject,
    CloudExperiment,
    CloudChart,
    CloudTag,
    CloudNamespace,
    CloudSource,
    CloudDisplay,
    CloudBaseModel,
    CLOUD_MODELS,
    connect_cloud_db,
    is_cloud_db_connected,
    mysql_manager,
    MySQLConnectionManager,
    MySQLConfig,
)

# ClickHouse 数据库
from .clickhouse import ClickHouseManager, clickhouse_manager

__all__ = [
    # MySQL Models
    'CloudProject',
    'CloudExperiment',
    'CloudChart',
    'CloudTag',
    'CloudNamespace',
    'CloudSource',
    'CloudDisplay',
    'CloudBaseModel',
    'CLOUD_MODELS',

    # MySQL Connection
    'connect_cloud_db',
    'is_cloud_db_connected',
    'mysql_manager',
    'MySQLConnectionManager',
    'MySQLConfig',

    # ClickHouse
    'ClickHouseManager',
    'clickhouse_manager',
]