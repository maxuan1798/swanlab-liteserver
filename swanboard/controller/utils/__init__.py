#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2024-03-09 21:41:37
@File: swanlab/server/controller/utils/__init__.py
@IDE: vscode
@Description:
    共享工具函数
"""
from .charts import get_exp_charts, get_proj_charts
from .tag import read_tag_data, get_tag_files, LOGS_CONFIGS, lttb
from typing import List


def clear_field(target: List[dict], field: str) -> List[dict]:
    """遍历字典列表清除某个字段

    Parameters
    ----------
    target : List[dict]
        需要处理的列表
    field : str
        需要删除的字段

    Returns
    -------
    List[dict]
        处理后的字典列表
    """

    for item in target:
        item.pop(field)

    return target


def normalize_experiment_fields(data: dict) -> dict:
    """
    标准化实验数据字段，处理前后端字段名不一致的问题

    将数据库字段映射为前端期望的字段名：
    - created_at -> create_time
    - finished_at -> finish_time
    - light_color -> light
    - dark_color -> dark

    Parameters
    ----------
    data : dict
        实验数据字典

    Returns
    -------
    dict
        标准化后的数据字典
    """
    # 时间字段兼容
    if "create_time" not in data and "created_at" in data:
        data["create_time"] = data["created_at"]
    if "finish_time" not in data and "finished_at" in data:
        data["finish_time"] = data["finished_at"]

    # 颜色字段兼容
    if "light" not in data and "light_color" in data:
        data["light"] = data["light_color"]
    if "dark" not in data and "dark_color" in data:
        data["dark"] = data["dark_color"]

    return data
