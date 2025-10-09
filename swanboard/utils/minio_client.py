"""
MinIO 客户端工具，用于从 MinIO 获取媒体文件
"""

import os
from io import BytesIO
from typing import Optional

import boto3
from botocore.config import Config as BotocoreConfig
from botocore.exceptions import ClientError


class MinIOClient:
    """MinIO 客户端，用于从对象存储获取媒体文件"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
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
        self.endpoint = endpoint
        self.bucket_name = bucket_name

        # 初始化 boto3 客户端
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=BotocoreConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def download_file(self, object_key: str) -> Optional[BytesIO]:
        """
        从 MinIO 下载文件

        :param object_key: 对象存储的键（路径）
        :return: 文件的二进制数据流，如果失败则返回 None
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            file_data = BytesIO(response["Body"].read())
            return file_data
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code != "NoSuchKey":
                print(f"Error downloading from MinIO: {e}")
            return None
        except Exception as e:
            print(f"Error downloading from MinIO: {e}")
            return None

    def file_exists(self, object_key: str) -> bool:
        """
        检查文件是否存在于 MinIO

        :param object_key: 对象存储的键（路径）
        :return: 文件是否存在
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        """
        生成预签名 URL 用于临时访问文件

        :param object_key: 对象存储的键（路径）
        :param expiration: URL 过期时间（秒），默认 1 小时
        :return: 预签名 URL，如果失败则返回 None
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket_name, "Key": object_key}, ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None


# 全局 MinIO 客户端实例
_minio_client: Optional[MinIOClient] = None


def get_minio_client(config: dict = None) -> Optional[MinIOClient]:
    """
    获取 MinIO 客户端单例

    :param config: MinIO 配置字典
    :return: MinIO 客户端实例，如果未启用则返回 None
    """
    global _minio_client

    # 如果已经初始化且配置未改变，直接返回
    if _minio_client is not None and config is None:
        return _minio_client

    # 如果提供了配置，重新初始化
    if config and config.get("enabled", False):
        try:
            _minio_client = MinIOClient(
                endpoint=config["endpoint"],
                access_key=config["access_key"],
                secret_key=config["secret_key"],
                bucket_name=config["bucket"],
                region=config.get("region", "us-east-1"),
            )
            return _minio_client
        except Exception as e:
            print(f"Failed to initialize MinIO client: {e}")
            return None

    # 如果未启用 MinIO，返回 None
    return None