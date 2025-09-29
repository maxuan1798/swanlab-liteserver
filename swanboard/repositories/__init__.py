#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Repository pattern implementation for SwanLab Dashboard
Provides unified data access layer for cloud operations
"""

from ..db.mysql.connection import MySQLConnectionManager as ConnectionManager, mysql_manager as connection_manager
from .base import BaseRepository
from .project import ProjectRepository, project_repository
from .experiment import ExperimentRepository, experiment_repository
from .chart import (
    ChartRepository, NamespaceRepository, TagRepository,
    chart_repository, namespace_repository, tag_repository
)

__all__ = [
    # Classes
    'ConnectionManager',
    'BaseRepository',
    'ProjectRepository',
    'ExperimentRepository',
    'ChartRepository',
    'NamespaceRepository',
    'TagRepository',

    # Global instances
    'connection_manager',
    'project_repository',
    'experiment_repository',
    'chart_repository',
    'namespace_repository',
    'tag_repository'
]
