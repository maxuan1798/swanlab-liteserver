from fastapi import APIRouter, Query
from ..module.resp import PARAMS_ERROR_422

from ..controller.namespace import (
    # 修改namespace开启关闭状态
    change_namespace_opened,
    # 查询namespace列表
    get_namespaces,
    # 创建namespace
    create_namespace,
)
from fastapi import Request
from urllib.parse import quote

router = APIRouter()


@router.get("/")
async def _(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页大小，最大100"),
    keyword: str = Query(None, description="搜索关键词")
):
    """分页查询namespace列表

    Parameters
    ----------
    page : int
        页码，从1开始
    size : int
        每页大小，最大100
    keyword : str, optional
        搜索关键词，用于模糊匹配namespace名称

    Returns
    -------
    dict
        包含namespace列表和分页信息
    """
    return get_namespaces(page, size, keyword)


@router.post("/")
async def _(request: Request):
    """创建新的namespace

    Parameters
    ----------
    request : Request
        请求体，包含以下字段：
        - name: str, namespace名称
        - sort_order: int, optional, 排序顺序

    Returns
    -------
    dict
        创建的namespace信息
    """
    data = await request.json()
    name = data.get("name")
    sort_order = data.get("sort_order")

    if not name:
        return PARAMS_ERROR_422("Request parameter 'name' is required")

    return create_namespace(name, sort_order)


# 修改namespace可见性
@router.patch("/{namespace_id}/opened")
async def _(namespace_id: int, request: Request):
    """修��namespace可见性

    Parameters
    ----------
    experiment_id : int
        实验id
    request : Request
        请求体，包含 opened 字段
    Returns
    -------
    experiment : dict
        当前实验信息
    """

    data = await request.json()
    opened = data.get("opened")
    experiment_id = data.get("experiment_id")
    project_id = data.get("project_id")

    if opened is None:
        return PARAMS_ERROR_422("Request parameter 'opened'")
    if experiment_id is None and project_id is None:
        return PARAMS_ERROR_422("Request parameter 'experiment_id' or 'project_id'")
    return change_namespace_opened(namespace_id, opened, experiment_id, project_id)
