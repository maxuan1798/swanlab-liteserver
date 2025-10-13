"""
MinIO 客户端工具，用于从 MinIO 获取媒体文件
"""

import os
from io import BytesIO
from typing import Optional, List, Dict, Any

import boto3
from botocore.config import Config as BotocoreConfig
from botocore.exceptions import ClientError

# 尝试导入 swanlog，如果不存在则使用标准 logging
try:
    from swanboard.utils import swanlog
except ImportError:
    import logging as swanlog


class MinIOClient:
    """MinIO 客户端，用于对象存储的完整功能"""

    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket_name: str = "swanlab-media",
        region: str = "us-east-1",
    ):
        """
        初始化 MinIO 客户端

        :param endpoint: MinIO 服务地址
        :param access_key: MinIO 访问密钥
        :param secret_key: MinIO 密钥
        :param bucket_name: 存储桶名称
        :param region: 区域名称
        """
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "http://localhost:9100")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = bucket_name or os.getenv("MINIO_BUCKET", "swanlab-media")
        self.region = region

        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化 boto3 客户端"""
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


# 全局 MinIO 客户端实例
_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """获取全局 MinIO 客户端实例"""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client


def init_minio_client(endpoint: str = None, access_key: str = None,
                     secret_key: str = None, bucket_name: str = None) -> MinIOClient:
    """初始化全局 MinIO 客户端实例"""
    global _minio_client
    _minio_client = MinIOClient(endpoint, access_key, secret_key, bucket_name)
    return _minio_client
