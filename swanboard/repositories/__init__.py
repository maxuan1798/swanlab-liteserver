#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Repository pattern implementation for SwanLab Dashboard
Provides unified data access layer for cloud operations
"""
import logging

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from ..db.mysql.connection import MySQLConnectionManager as ConnectionManager, mysql_manager as connection_manager
from .base import BaseRepository
from .project import ProjectRepository, project_repository
from .experiment import ExperimentRepository, experiment_repository
from .chart import (
    ChartRepository, NamespaceRepository, TagRepository,
    chart_repository, namespace_repository, tag_repository
)
from .clickhouse import ClickHouseRepository, clickhouse_repository

__all__ = [
    # Classes
    'ConnectionManager',
    'BaseRepository',
    'ProjectRepository',
    'ExperimentRepository',
    'ChartRepository',
    'NamespaceRepository',
    'TagRepository',
    'ClickHouseRepository',

    # Global instances
    'connection_manager',
    'project_repository',
    'experiment_repository',
    'chart_repository',
    'namespace_repository',
    'tag_repository',
    'clickhouse_repository'
]
