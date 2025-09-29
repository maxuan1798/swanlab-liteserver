"""
Enhanced SwanBoard Callback with HTTP-based Cloud API Support

Environment Variables for Configuration:
- SWANLAB_CLOUD_SYNC: Set to 'true' to enable HTTP-based cloud sync
- SWANLAB_API_HOST: Cloud API base URL (default: http://localhost:5173/api/v1/cloud)
- SWANLAB_API_KEY: API key for cloud authentication
- SWANLAB_WORKSPACE: Cloud workspace name
- SWANLAB_CLOUD_TIMEOUT: HTTP request timeout in seconds (default: 30)

Usage:
1. Local only (default): Works as before with local SQLite database
2. Local + HTTP Cloud sync: Set SWANLAB_CLOUD_SYNC=true and provide API credentials
"""

import os
import requests
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

from swankit.callback import SwanKitCallback
from swankit.callback.models import ColumnInfo
from .db.models import *
from .db import add_multi_chart, connect, NotExistedError, ExistedError, ChartTypeError
from .callback import SwanBoardCallback
from .utils import swanlog, get_swanlog_dir


class EnhancedSwanBoardCallback(SwanBoardCallback):
    """
    增强版 SwanBoardCallback，支持本地SQLite数据库和HTTP云端API同步
    """

    def __init__(self, enable_cloud: bool = False, cloud_config: Optional[Dict[str, Any]] = None):
        """
        初始化增强版回调

        :param enable_cloud: 是否启用HTTP云端API功能
        :param cloud_config: 云端配置，包含API端点、认证信息等
        """
        super().__init__()

        # 从环境变量检查是否启用云端同步
        self.enable_cloud = enable_cloud or os.getenv('SWANLAB_CLOUD_SYNC', 'false').lower() == 'true'
        self.cloud_config = cloud_config or {}

        # 默认云端配置
        self.cloud_api_base = self.cloud_config.get('api_base') or os.getenv('SWANLAB_API_HOST', 'http://localhost:5173/api/v1/cloud')
        self.cloud_api_key = self.cloud_config.get('api_key') or os.getenv('SWANLAB_API_KEY')
        self.cloud_workspace = self.cloud_config.get('workspace') or os.getenv('SWANLAB_WORKSPACE', 'default')
        self.cloud_timeout = self.cloud_config.get('timeout') or int(os.getenv('SWANLAB_CLOUD_TIMEOUT', '30'))

        # HTTP session for cloud requests
        self.session = None
        if self.enable_cloud:
            self.session = requests.Session()
            self.session.headers.update({
                'Content-Type': 'application/json'
            })

            # 添加认证头（如果有API密钥）
            if self.cloud_api_key:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.cloud_api_key}'
                })

            swanlog.info(f"HTTP cloud sync enabled - API: {self.cloud_api_base}, Workspace: {self.cloud_workspace}")

    def _send_cloud_request(self, endpoint: str, data: Dict[str, Any], method: str = 'POST') -> Optional[Dict]:
        """
        发送请求到云端API

        :param endpoint: API端点
        :param data: 请求数据
        :param method: HTTP方法
        :return: 响应数据或None（如果失败）
        """
        if not self.enable_cloud or not self.session:
            return None

        try:
            url = f"{self.cloud_api_base.rstrip('/')}/{endpoint.lstrip('/')}"
            swanlog.info(f"HTTP cloud sync request - URL: {url}")
            # 添加时间戳
            data['timestamp'] = datetime.now().isoformat()

            if method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.cloud_timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=self.cloud_timeout)
            elif method.upper() == 'GET':
                response = self.session.get(url, params=data, timeout=self.cloud_timeout)
            else:
                swanlog.warning(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()

            # 解析响应
            if response.content:
                response_data = response.json()
                swanlog.info(f"HTTP cloud sync response - response_data: {response_data}")
                # 检查API响应格式
                if response_data.get('code') == 0:
                    return response_data.get('data', {})
                else:
                    swanlog.warning(f"Cloud API error: {response_data.get('message', 'Unknown error')}")
                    return None
            else:
                return {}

        except requests.exceptions.Timeout:
            swanlog.warning(f"Cloud request timeout for endpoint: {endpoint}")
        except requests.exceptions.ConnectionError:
            swanlog.warning(f"Cloud connection error for endpoint: {endpoint}. Is SwanLab-Dashboard running?")
        except requests.exceptions.HTTPError as e:
            swanlog.warning(f"Cloud HTTP error for endpoint {endpoint}: {e}")
            if e.response.status_code == 401:
                swanlog.warning("Cloud API authentication failed. Check your API key.")
            elif e.response.status_code == 403:
                swanlog.warning("Cloud API access forbidden. Check workspace permissions.")
        except Exception as e:
            swanlog.warning(f"Unexpected cloud request error for endpoint {endpoint}: {e}")

        return None

    def _sync_project_to_cloud(self, proj_name: str) -> Optional[str]:
        """
        同步项目到云端

        :param proj_name: 项目名称
        :return: 云端项目ID
        """
        data = {
            'name': proj_name,
            'workspace': self.cloud_workspace,
            'description': f'Project {proj_name} synced from local SwanLab'
        }

        response = self._send_cloud_request('projects', data)
        if response:
            project_id = response.get('id') or response.get('project_id')
            if project_id:
                swanlog.debug(f"Project '{proj_name}' synced to cloud with ID: {project_id}")
                return str(project_id)

        return None

    def _sync_experiment_to_cloud(self, run_id: str, exp_name: str, description: str,
                                colors: Tuple[str, str], project_id: str = None) -> Optional[str]:
        """
        同步实验到云端

        :param run_id: 运行ID
        :param exp_name: 实验名称
        :param description: 实验描述
        :param colors: 实验颜色
        :param project_id: 项目ID
        :return: 云端实验ID
        """
        data = {
            'run_id': run_id,
            'name': exp_name,
            'description': description,
            'colors': list(colors) if colors else None,
            'project_id': project_id or '1',  # 默认项目ID
            'workspace': self.cloud_workspace
        }

        response = self._send_cloud_request('experiments', data)
        if response:
            experiment_id = response.get('id') or response.get('experiment_id')
            if experiment_id:
                swanlog.debug(f"Experiment '{exp_name}' (run_id: {run_id}) synced to cloud with ID: {experiment_id}")
                return str(experiment_id)

        return None

    def _sync_column_to_cloud(self, column_info: ColumnInfo, experiment_id: str = None) -> Optional[str]:
        """
        同步列信息到云端

        :param column_info: 列信息
        :param experiment_id: 实验ID
        :return: 云端列ID
        """
        if column_info.cls != "CUSTOM":
            return None  # 屏蔽系统生成的指标

        chart_type = column_info.chart_type.value.chart_type

        data = {
            'key': column_info.key,
            'experiment_id': experiment_id,
            'chart_type': chart_type,
            'reference': column_info.chart_reference.lower(),
            'section_name': column_info.section_name,
            'section_sort': column_info.section_sort,
            'kid': column_info.kid
        }

        if column_info.error is not None:
            data['error'] = {
                'data_class': column_info.error.got,
                'expected': column_info.error.expected,
            }

        response = self._send_cloud_request('columns', data)
        if response:
            column_id = response.get('id') or response.get('column_id')
            if column_id:
                swanlog.debug(f"Column '{column_info.key}' synced to cloud with ID: {column_id}")
                return str(column_id)

        return None

    def _sync_experiment_status_to_cloud(self, experiment_id: str, status: int):
        """
        同步实验状态到云端

        :param experiment_id: 实验ID
        :param status: 实验状态
        """
        data = {'status': status}

        response = self._send_cloud_request(f'experiments/{experiment_id}/status', data, method='PUT')
        if response:
            swanlog.debug(f"Experiment status {status} synced to cloud")
        else:
            swanlog.warning(f"Failed to sync experiment status {status} to cloud")

    def get_cloud_sync_stats(self) -> Dict[str, Any]:
        """
        获取云端同步统计信息

        :return: 统计信息字典
        """
        if not self.enable_cloud:
            return {'enabled': False, 'reason': 'Cloud sync disabled'}

        if not self.session:
            return {'enabled': False, 'reason': 'No HTTP session'}

        # 尝试健康检查
        try:
            response = self.session.get(f"{self.cloud_api_base}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                return {
                    'enabled': True,
                    'api_base': self.cloud_api_base,
                    'workspace': self.cloud_workspace,
                    'has_api_key': bool(self.cloud_api_key),
                    'health': health_data
                }
            else:
                return {
                    'enabled': False,
                    'reason': f'Health check failed: HTTP {response.status_code}'
                }
        except Exception as e:
            return {
                'enabled': False,
                'reason': f'Health check error: {e}'
            }

    def on_init(self, proj_name: str, *args, **kwargs):
        # 执行原有的本地逻辑
        super().on_init(proj_name, *args, **kwargs)

        # 如果启用云端，同步项目到云端HTTP API
        if self.enable_cloud:
            cloud_project_id = self._sync_project_to_cloud(proj_name)
            if cloud_project_id:
                # 存储云端项目ID以供后续使用
                self.cloud_project_id = cloud_project_id
            else:
                swanlog.warning(f"Failed to sync project {proj_name} to cloud HTTP API")

    def before_init_experiment(self, run_id: str, exp_name: str, description: str,
                             num: int, colors: Tuple[str, str], *args, **kwargs):
        # 执行原有的本地逻辑
        super().before_init_experiment(run_id, exp_name, description, num, colors, *args, **kwargs)

        # 如果启用云端，同步实验到云端HTTP API
        if self.enable_cloud:
            project_id = getattr(self, 'cloud_project_id', '1')
            cloud_experiment_id = self._sync_experiment_to_cloud(
                run_id, exp_name, description, colors, project_id
            )
            if cloud_experiment_id:
                # 存储云端实验ID以供后续使用
                self.cloud_experiment_id = cloud_experiment_id
            else:
                swanlog.warning(f"Failed to sync experiment {exp_name} to cloud HTTP API")

    def on_column_create(self, column_info: ColumnInfo, *args, **kwargs):
        # 执行原有的本地逻辑
        super().on_column_create(column_info, *args, **kwargs)

        # 如果启用云端，同步列信息到云端HTTP API
        if self.enable_cloud and hasattr(self, 'cloud_experiment_id'):
            cloud_column_id = self._sync_column_to_cloud(column_info, self.cloud_experiment_id)
            if cloud_column_id:
                swanlog.debug(f"Column {column_info.key} synced to cloud HTTP API with ID: {cloud_column_id}")
            else:
                # 这里不显示警告，因为系统生成的指标会被过滤掉
                swanlog.debug(f"Column {column_info.key} not synced to cloud (may be system-generated)")

    def on_stop(self, error: str = None, *args, **kwargs):
        # 执行原有的本地逻辑
        super().on_stop(error, *args, **kwargs)

        # 如果启用云端，同步实验状态到云端HTTP API
        if self.enable_cloud and hasattr(self, 'cloud_experiment_id'):
            status = -1 if error is not None else 1
            self._sync_experiment_status_to_cloud(self.cloud_experiment_id, status)

    def __del__(self):
        """析构函数，关闭HTTP session"""
        if hasattr(self, 'session') and self.session:
            self.session.close()


# 为了向后兼容，保留原有的配置方式
def create_enhanced_callback_with_http_cloud(
    api_base: str = None,
    api_key: str = None,
    workspace: str = None,
    timeout: int = 30
) -> EnhancedSwanBoardCallback:
    """
    创建支持HTTP云端同步的增强回调

    :param api_base: API基础URL
    :param api_key: API密钥
    :param workspace: 工作空间名称
    :param timeout: 请求超时时间
    :return: 配置好的回调实例
    """
    cloud_config = {}
    if api_base:
        cloud_config['api_base'] = api_base
    if api_key:
        cloud_config['api_key'] = api_key
    if workspace:
        cloud_config['workspace'] = workspace
    if timeout:
        cloud_config['timeout'] = timeout

    return EnhancedSwanBoardCallback(
        enable_cloud=True,
        cloud_config=cloud_config
    )
