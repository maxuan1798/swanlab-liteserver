from ..module.resp import SUCCESS_200, NOT_FOUND_404, PARAMS_ERROR_422
from .db import NotExistedError

from .db import (
    Namespace,
    Experiment,
    Project,
)
from ..repositories import namespace_repository


def get_namespaces(page: int = 1, size: int = 20, keyword: str = None):
    """分页查询namespace列表

    Parameters
    ----------
    page : int, optional
        页码，从1开始，默认为1
    size : int, optional
        每页大小，默认为20
    keyword : str, optional
        搜索关键词，用于模糊匹配namespace名称

    Returns
    -------
    dict
        包含namespace列表和分页信息的响应
    """
    try:
        # 使用 repository 获取数据
        namespace_list, total = namespace_repository.get_all(page=page, size=size, keyword=keyword)

        return SUCCESS_200({
            "namespaces": namespace_list,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "pages": (total + size - 1) // size if total > 0 else 0
            }
        })

    except Exception as e:
        return PARAMS_ERROR_422(str(e))


def create_namespace(name: str, sort_order: int = None):
    """创建新的namespace

    Parameters
    ----------
    name : str
        namespace名称
    sort_order : int, optional
        排序顺序，如果不提供则自动设置为最大值+1

    Returns
    -------
    dict
        创建的namespace信息
    """
    try:
        # 使用 repository 创建命名空间
        namespace = namespace_repository.create_namespace(name=name, sort_order=sort_order)

        if not namespace:
            return PARAMS_ERROR_422("Namespace with name '{}' already exists.".format(name))

        return SUCCESS_200(namespace_repository.to_dict(namespace))

    except Exception as e:
        return PARAMS_ERROR_422(str(e))


# 修改namespace可见性
def change_namespace_opened(namespace_id: int, opened: int, experiment_id: int, project_id: int):
    """修改namespace的打开/关闭状态

    Parameters
    ----------
    namespace_id : int
        namespace的id，特别的，-1表示pinned，-2表示hidden
    opened : int
        在一个实验下，该namespace是否可见，true -> 1 , false -> 0
    experiment_id : int
        实验id，修改pinned/hidden的namespace的开启关闭状态时需要
    project_id : int
        项目id，修改pinned/hidden的namespace的开启关闭状态时需要
    Returns
    -------
    _type_:dict
        当前namespace信息
    """
    if namespace_id in [-1, -2]:
        if experiment_id is not None:
            exp_or_proj = Experiment.get_by_id(experiment_id)
        else:
            exp_or_proj = Project.get_by_id(project_id)
        # 如果实验或者项目不存在，则返回404
        if exp_or_proj is None:
            return NOT_FOUND_404("Experiment or project with id {} does not exist.".format(experiment_id))
        if namespace_id == -1:
            exp_or_proj.pinned_opened = 1 if opened else 0
        else:
            exp_or_proj.hidden_opened = 1 if opened else 0
        exp_or_proj.save()
        return SUCCESS_200(None)
    # 正常的namespace
    try:
        namespace: Namespace = Namespace.get_by_id(namespace_id)
    except NotExistedError:
        return NOT_FOUND_404("Namespace with id {} does not exist.".format(namespace_id))
    namespace.opened = 1 if opened else 0
    namespace.save()
    return SUCCESS_200(None)
