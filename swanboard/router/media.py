#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2024-01-29 14:14:02
@File: swanlab\server\router\static.py
@IDE: vscode
@Description:
    多媒体相关接口路由
    暂时只有一个，用于获取媒体数据，这媒体包括音频、视频、图片、文字等，返回的接口是统一的
    返回的数据格式也不再是JSON，而是二进制数据，这样可以减少数据传输的大小
    我们约定前端通过一个相对路径获取媒体数据，这个路径相对于当前watch的文件夹
"""

from ..settings import get_media_dir, get_minio_config
from ..utils.minio_client import get_minio_client
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from ..db.mysql import CloudExperiment as Experiment, CloudTag as Tag
import os

from ..repositories import (
    experiment_repository, tag_repository
)

# 响应模块
from ..module.resp import (
    SUCCESS_200, DATA_ERROR_500, BAD_REQUEST_400,
    NOT_FOUND_404, CONFLICT_409, UNAUTHORIZED_401
)

router = APIRouter()

# 初始化 MinIO 客户端（如果启用）
minio_config = get_minio_config()
minio_client = get_minio_client(minio_config) if minio_config.get("enabled") else None


# ---------------------------------- 音频相关 ----------------------------------


@router.get("/{path:path}")
def _(path: str, tag: str, experiment_id: str):
    """获取媒体文件
    通过参数拼接为本地路径或从 MinIO 获取，返回二进制数据
    tag需要进行url编码

    优先级：MinIO (如果启用) > 本地文件系统
    """
    print(f"path: {path}")
    print(f"experiment_id: {experiment_id}")
    print(f"tag: {tag}")
    # 获取实验信息
    experiment = experiment_repository.get_by_id(experiment_id)
    if not experiment:
        return NOT_FOUND_404(f"Experiment with id {experiment_id} not found")
    run_id = experiment.run_id
    print(f"run_id: {run_id}")
    tag_folder = tag_repository.get_experiment_tag_folder(experiment_id, tag)
    if not tag_folder:
        return NOT_FOUND_404(f"Tag {tag} not found in experiment {experiment_id}")
    print(f"tag_folder: {tag_folder}")
    # 如果启用了 MinIO，尝试从 MinIO 获取文件
    if minio_client:
        # MinIO 对象键格式: run_id/column_id/filename
        # path 已经包含了 filename，tag_folder 就是 column_id
        object_key = f"{run_id}/{tag_folder}/{path}"
        print(f"object_key: {object_key}")
        file_data = minio_client.download_file(object_key)
        if file_data:
            # 从 MinIO 获取成功，返回流式响应
            import mimetypes
            content_type, _ = mimetypes.guess_type(path)
            return StreamingResponse(
                file_data,
                media_type=content_type or "application/octet-stream",
                headers={"Cache-Control": "max-age=31536000"}
            )

    # 如果 MinIO 未启用或文件不存在，从本地文件系统获取
    media_path = os.path.join(get_media_dir(run_id, tag_folder), path)

    # 检查本地文件是否存在
    if not os.path.exists(media_path):
        raise HTTPException(status_code=404, detail="Media file not found")

    return FileResponse(media_path)
