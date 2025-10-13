#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端同步管理器
提供本地数据与MySQL云端数据库的同步功能，以及 MinIO 文件存储服务
"""

import threading
from typing import Optional, Dict, Any, List, Tuple
from swankit.callback.models import ColumnInfo

from ..repositories import (
    connection_manager, project_repository, experiment_repository, chart_repository
)
from ..db.mysql.models import CloudRuntimeInfo
from swanboard.utils import swanlog

# MinIO / boto3 支持
import os
from io import BytesIO
try:
    import boto3
    from botocore.config import Config as BotocoreConfig
    from botocore.exceptions import ClientError
    _BOTO3_AVAILABLE = True
except Exception:
    _BOTO3_AVAILABLE = False


class ServerMinIOClient:
    """服务端 MinIO 客户端，提供完整的文件存储功能"""

    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket_name: str = "swanlab-media",
        region: str = "us-east-1",
    ):
        """
        初始化服务端 MinIO 客户端

        :param endpoint: MinIO 服务地址
        :param access_key: MinIO 访问密钥
        :param secret_key: MinIO 密钥
        :param bucket_name: 存储桶名称
        :param region: 区域名称
        """
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = bucket_name or os.getenv("MINIO_BUCKET", "swanlab-media")
        self.region = region

        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化 boto3 客户端"""
        if not _BOTO3_AVAILABLE:
            swanlog.warning("boto3 not available, MinIO client disabled")
            return

        if not self.endpoint or not self.access_key or not self.secret_key:
            swanlog.warning("MinIO configuration incomplete, client disabled")
            return

        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=BotocoreConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
            )
            self._ensure_bucket_exists()
            swanlog.info(f"MinIO client initialized: endpoint={self.endpoint}, bucket={self.bucket_name}")
        except Exception as e:
            swanlog.error(f"Failed to initialize MinIO client: {e}")
            self.client = None

    def _ensure_bucket_exists(self):
        """确保存储桶存在，如果不存在则创建"""
        if not self.client:
            return

        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            swanlog.debug(f"Bucket '{self.bucket_name}' already exists")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    swanlog.info(f"Created bucket '{self.bucket_name}'")
                except Exception as create_error:
                    swanlog.error(f"Failed to create bucket '{self.bucket_name}': {create_error}")
            else:
                swanlog.error(f"Error checking bucket: {e}")

    def is_available(self) -> bool:
        """检查 MinIO 客户端是否可用"""
        return self.client is not None

    def upload_file(self, file_data: bytes, object_key: str, content_type: str = None) -> bool:
        """
        上传文件到 MinIO

        :param file_data: 文件的二进制数据
        :param object_key: 对象存储的键（路径）
        :param content_type: 文件的 MIME 类型
        :return: 上传是否成功
        """
        if not self.client:
            swanlog.warning("MinIO client not available, skipping upload")
            return False

        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                CacheControl="max-age=31536000",
                **extra_args
            )
            swanlog.debug(f"Uploaded file to MinIO: {object_key}")
            return True
        except Exception as e:
            swanlog.error(f"Failed to upload file to MinIO: {e}")
            return False

    def upload_files(self, files: List[tuple]) -> int:
        """
        批量上传文件到 MinIO

        :param files: 文件列表，每个元素为 (file_data, object_key, content_type) 元组
        :return: 成功上传的文件数量
        """
        success_count = 0
        for file_info in files:
            file_data, object_key = file_info[0], file_info[1]
            content_type = file_info[2] if len(file_info) > 2 else None
            if self.upload_file(file_data, object_key, content_type):
                success_count += 1
        return success_count

    def download_file(self, object_key: str) -> Optional[BytesIO]:
        """
        从 MinIO 下载文件

        :param object_key: 对象存储的键（路径）
        :return: 文件的二进制数据流，如果失败则返回 None
        """
        if not self.client:
            swanlog.warning("MinIO client not available, cannot download")
            return None

        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            file_data = BytesIO(response["Body"].read())
            swanlog.debug(f"Downloaded file from MinIO: {object_key}")
            return file_data
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                swanlog.warning(f"File not found in MinIO: {object_key}")
            else:
                swanlog.error(f"Failed to download file from MinIO: {e}")
            return None
        except Exception as e:
            swanlog.error(f"Failed to download file from MinIO: {e}")
            return None

    def file_exists(self, object_key: str) -> bool:
        """
        检查文件是否存在于 MinIO

        :param object_key: 对象存储的键（路径）
        :return: 文件是否存在
        """
        if not self.client:
            return False

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    def delete_file(self, object_key: str) -> bool:
        """
        从 MinIO 删除文件

        :param object_key: 对象存储的键（路径）
        :return: 删除是否成功
        """
        if not self.client:
            return False

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            swanlog.debug(f"Deleted file from MinIO: {object_key}")
            return True
        except Exception as e:
            swanlog.error(f"Failed to delete file from MinIO: {e}")
            return False

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        """
        生成预签名 URL 用于临时访问文件

        :param object_key: 对象存储的键（路径）
        :param expiration: URL 过期时间（秒），默认 1 小时
        :return: 预签名 URL，如果失败则返回 None
        """
        if not self.client:
            return None

        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            swanlog.error(f"Failed to generate presigned URL: {e}")
            return None

    def get_config(self) -> Dict[str, Any]:
        """返回 MinIO 配置信息（不包含敏感密钥）"""
        return {
            'enabled': self.is_available(),
            'endpoint': self.endpoint,
            'bucket': self.bucket_name,
            'region': self.region,
        }


class CloudSyncManager:
    """云端同步管理器"""

    def __init__(self, workspace: str, user: str):
        """
        初始化同步管理器

        Args:
            workspace: 工作空间名称
            user: 用户名
        """
        self.workspace = workspace
        self.user = user
        self._lock = threading.Lock()

        # 缓存当前项目和实验ID
        self._current_project_id: Optional[str] = None
        self._current_experiment_id: Optional[str] = None

        # 初始化 MinIO 客户端
        self.minio_client = ServerMinIOClient()
        swanlog.info(f"MinIO Workspace: {self.workspace}")

    # MinIO 代理方法 - 供 HTTP API 调用
    def get_minio_config(self) -> Dict[str, Any]:
        """返回服务器端 MinIO 配置信息（不包含敏感密钥）"""
        return self.minio_client.get_config()

    def upload_media_bytes(self, object_key: str, file_bytes: bytes, content_type: Optional[str] = None) -> bool:
        """将给定字节内容上传到服务器配置的 MinIO 存储"""
        return self.minio_client.upload_file(file_bytes, object_key, content_type)

    def upload_media_stream(self, object_key: str, stream, content_type: Optional[str] = None) -> bool:
        """支持流式上传"""
        try:
            data = stream.read()
            return self.upload_media_bytes(object_key, data, content_type)
        except Exception as e:
            swanlog.error(f"upload_media_stream failed: {e}")
            return False

    def download_media_bytes(self, object_key: str) -> Optional[BytesIO]:
        """从服务器 MinIO 下载对象并返回 BytesIO"""
        return self.minio_client.download_file(object_key)

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        """生成 presigned URL 供客户端下载"""
        return self.minio_client.generate_presigned_url(object_key, expiration)

    def delete_media_file(self, object_key: str) -> bool:
        """删除媒体文件"""
        return self.minio_client.delete_file(object_key)

    def file_exists(self, object_key: str) -> bool:
        """检查文件是否存在"""
        return self.minio_client.file_exists(object_key)

    def sync_project(self, name: str, description: str = None) -> Optional[str]:
        """
        同步项目到云端

        Args:
            name: 项目名称
            description: 项目描述

        Returns:
            str: 云端项目ID，失败返回None
        """
        swanlog.info("Cloud database sync")
        if not connection_manager.ensure_connected():
            swanlog.warning("Cloud database not connected, skipping project sync")
            return None

        with self._lock:
            try:
                swanlog.info(f"Syncing project {name}")
                project_id = project_repository.sync_project(
                    name=name,
                    workspace=self.workspace,
                    description=description,
                    owner=self.user
                )

                if project_id:
                    self._current_project_id = project_id
                    swanlog.debug(f"Project '{name}' synced to cloud with ID: {project_id}")

                return project_id

            except Exception as e:
                swanlog.error(f"Failed to sync project '{name}' to cloud: {e}")
                return None

    def sync_experiment(self, run_id: str, name: str, description: str = None,
                       colors: Tuple[str, str] = None, sort_order: int = None) -> Optional[str]:
        """
        同步实验到云端

        Args:
            run_id: 运行ID
            name: 实验名称
            description: 实验描述
            colors: 颜色主题 (light, dark)
            sort_order: 排序序号

        Returns:
            str: 云端实验ID，失败返回None
        """
        if not connection_manager.ensure_connected() or not self._current_project_id:
            swanlog.warning("Cloud database not connected or no project, skipping experiment sync")
            return None

        with self._lock:
            try:
                experiment_id = experiment_repository.sync_experiment(
                    run_id=run_id,
                    name=name,
                    project_id=int(self._current_project_id),
                    description=description,
                    colors=colors,
                    sort_order=sort_order
                )

                if experiment_id:
                    self._current_experiment_id = experiment_id
                    swanlog.debug(f"Experiment '{name}' (run_id: {run_id}) synced to cloud with ID: {experiment_id}")

                return experiment_id

            except Exception as e:
                swanlog.error(f"Failed to sync experiment '{name}' to cloud: {e}")
                return None

    def sync_runtime_info(self, requirements: str = None, metadata: str = None,
                         config: str = None, conda: str = None) -> Optional[str]:
        """
        同步实验运行时信息到云端

        Args:
            requirements: requirements.txt内容
            metadata: metadata JSON内容
            config: config YAML内容
            conda: conda environment YAML内容

        Returns:
            str: 云端运行时信息ID，失败返回None
        """
        if not connection_manager.ensure_connected() or not self._current_experiment_id:
            swanlog.warning("Cloud database not connected or no experiment, skipping runtime info sync")
            return None

        with self._lock:
            try:
                # 检查是否已存在运行时信息
                existing = CloudRuntimeInfo.select().where(
                    CloudRuntimeInfo.experiment == int(self._current_experiment_id)
                ).first()

                if existing:
                    # 更新现有记录
                    if requirements is not None:
                        existing.requirements = requirements
                    if metadata is not None:
                        existing.metadata = metadata
                    if config is not None:
                        existing.config = config
                    if conda is not None:
                        existing.conda = conda

                    existing.save()
                    runtime_id = str(existing.id)
                    swanlog.debug(f"Runtime info updated for experiment ID: {self._current_experiment_id}")
                else:
                    # 创建新记录
                    runtime_info = CloudRuntimeInfo.create(
                        experiment=int(self._current_experiment_id),
                        requirements=requirements,
                        metadata=metadata,
                        config=config,
                        conda=conda
                    )
                    runtime_id = str(runtime_info.id)
                    swanlog.debug(f"Runtime info created for experiment ID: {self._current_experiment_id}")

                return runtime_id

            except Exception as e:
                swanlog.error(f"Failed to sync runtime info to cloud: {e}")
                return None

    def sync_column(self, column_info: ColumnInfo) -> Optional[str]:
        """
        同步列信息到云端

        Args:
            column_info: 列信息对象

        Returns:
            str: 云端列ID，失败返回None
        """
        if not connection_manager.ensure_connected() or not self._current_experiment_id:
            swanlog.warning("Cloud database not connected or no experiment, skipping column sync")
            return None

        # 只同步自定义指标
        if column_info.cls != "CUSTOM":
            return None

        with self._lock:
            try:
                chart_type = column_info.chart_type.value.chart_type

                # 处理错误信息
                error_info = None
                if column_info.error is not None:
                    error_info = {
                        "data_class": column_info.error.got,
                        "expected": column_info.error.expected,
                    }

                chart_id = chart_repository.sync_column(
                    key=column_info.key,
                    experiment_id=int(self._current_experiment_id),
                    chart_type=chart_type,
                    reference=column_info.chart_reference.lower(),
                    section_name=column_info.section_name,
                    section_sort=column_info.section_sort,
                    kid=column_info.kid,
                    error_info=error_info
                )

                if chart_id:
                    swanlog.debug(f"Column '{column_info.key}' synced to cloud with chart ID: {chart_id}")

                return chart_id

            except Exception as e:
                swanlog.error(f"Failed to sync column '{column_info.key}' to cloud: {e}")
                return None

    def sync_experiment_status(self, status: int, error: str = None) -> bool:
        """
        同步实验状态到云端

        Args:
            status: 实验状态 (-1: crashed, 0: running, 1: finished)
            error: 错误信息

        Returns:
            bool: 同步成功返回True
        """
        if not connection_manager.ensure_connected() or not self._current_experiment_id:
            swanlog.warning("Cloud database not connected or no experiment, skipping status sync")
            return False

        with self._lock:
            try:
                success = experiment_repository.update_status(
                    experiment_id=int(self._current_experiment_id),
                    status=status,
                    error=error
                )

                if success:
                    swanlog.debug(f"Experiment status {status} synced to cloud")

                return success

            except Exception as e:
                swanlog.error(f"Failed to sync experiment status to cloud: {e}")
                return False

    def get_project_experiments(self, project_name: str) -> List[Dict[str, Any]]:
        """
        获取项目的所有实验

        Args:
            project_name: 项目名称

        Returns:
            List[Dict]: 实验列表
        """
        if not connection_manager.ensure_connected():
            return []

        try:
            project = project_repository.get_by_name_and_workspace(project_name, self.workspace)
            if not project:
                swanlog.warning(f"Project '{project_name}' not found in cloud")
                return []

            return experiment_repository.get_project_experiments(project.id)

        except Exception as e:
            swanlog.error(f"Failed to get project experiments: {e}")
            return []

    def get_experiment_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实验详情

        Args:
            run_id: 运行ID

        Returns:
            Dict: 实验详情，失败返回None
        """
        if not connection_manager.ensure_connected():
            return None

        try:
            return experiment_repository.get_experiment_details(run_id)

        except Exception as e:
            swanlog.error(f"Failed to get experiment details: {e}")
            return None

    def get_experiment_runtime_info(self, experiment_id: int = None) -> Optional[Dict[str, Any]]:
        """
        获取实验运行时信息

        Args:
            experiment_id: 实验ID，如果不提供则使用当前实验

        Returns:
            Dict: 运行时信息，失败返回None
        """
        if not connection_manager.ensure_connected():
            return None

        exp_id = experiment_id or (int(self._current_experiment_id) if self._current_experiment_id else None)
        if not exp_id:
            swanlog.warning("No experiment ID provided for runtime info query")
            return None

        try:
            runtime_info = CloudRuntimeInfo.select().where(
                CloudRuntimeInfo.experiment == exp_id
            ).first()

            if runtime_info:
                return runtime_info.to_dict()
            else:
                return None

        except Exception as e:
            swanlog.error(f"Failed to get runtime info: {e}")
            return None

    def cleanup(self):
        """清理资源"""
        with self._lock:
            self._current_project_id = None
            self._current_experiment_id = None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取同步统计信息

        Returns:
            Dict: 统计信息
        """
        if not connection_manager.ensure_connected():
            return {'connected': False}

        try:
            # 获取工作空间项目统计
            workspace_projects = project_repository.get_workspace_projects(self.workspace)
            project_count = len(workspace_projects)

            experiment_count = 0
            current_project_name = None
            current_experiment_name = None

            if self._current_project_id:
                current_project = project_repository.get_by_id(int(self._current_project_id))
                if current_project:
                    current_project_name = current_project.name
                    project_experiments = experiment_repository.get_project_experiments(current_project.id)
                    experiment_count = len(project_experiments)

            if self._current_experiment_id:
                current_experiment = experiment_repository.get_by_id(int(self._current_experiment_id))
                if current_experiment:
                    current_experiment_name = current_experiment.name

            return {
                'connected': True,
                'workspace': self.workspace,
                'user': self.user,
                'projects': project_count,
                'experiments': experiment_count,
                'current_project': current_project_name,
                'current_experiment': current_experiment_name
            }

        except Exception as e:
            swanlog.error(f"Failed to get sync stats: {e}")
            return {'connected': False, 'error': str(e)}

    # 便捷方法，保持与原版本的兼容性
    def get_current_project(self):
        """获取当前项目实例"""
        if self._current_project_id:
            return project_repository.get_by_id(int(self._current_project_id))
        return None

    def get_current_experiment(self):
        """获取当前实验实例"""
        if self._current_experiment_id:
            return experiment_repository.get_by_id(int(self._current_experiment_id))
        return None
