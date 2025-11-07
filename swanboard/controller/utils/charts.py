#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2024-03-09 21:43:59
@File: swanlab/server/controller/utils/charts.py
@IDE: vscode
@Description:
    图表相关函数 - 云端版本
"""
import logging
from ...db import CloudChart
from ...db.mysql import CloudChart as Chart, CloudDisplay as Display, CloudNamespace as Namespace, CloudExperiment as Experiment
from typing import List, Tuple, Union, Optional

logger = logging.getLogger(__name__)


def get_exp_charts(id: int) -> Tuple[List[dict], List[dict]]:
    """
    获取单实验图表数据

    Parameters
    ----------
    id : int
        实验id

    Returns
    -------
    Tuple[List[dict], List[dict]]
        (图表列表, 命名空间列表)
    """
    charts: List[Chart] = Chart.filter(Chart.experiment == id)
    chart_list = CloudChart.search2list(charts)
    # 获取每个图表对应的数据源
    for index, chart in enumerate(charts):
        sources = []
        error = {}
        # source->experiment_id
        source_map = {}
        for source in Chart.search2list(chart.sources):
            sources.append(source["tag_id"]["name"])
            source_map[source["tag_id"]["name"]] = id
            if source["error"]:
                error[source["tag_id"]["name"]] = Chart.json_to_dict(source["error"])
        chart_list[index]["error"] = error
        chart_list[index]["source"] = sources
        chart_list[index]["multi"] = False
        chart_list[index]["source_map"] = source_map

    # 当前实验下的命名空间
    namespaces = Namespace.filter(Namespace.experiment_id == id)
    namespace_list = Namespace.search2list(namespaces)
    # 获取每个命名空间对应的 display
    # display 含有 chart 与 namespace 的对应关系
    for index, namespace in enumerate(namespaces):
        displays = []
        for display in Namespace.search2list(namespace.displays):
            displays.append(display["chart_id"]["id"])
        namespace_list[index]["charts"] = displays
    return get_pinned_and_hidden(chart_list, namespace_list, experiment_id=id)


def get_proj_charts(id: int) -> Tuple[List[dict], List[dict]]:
    """
    获取多实验对比图表数据

    Parameters
    ----------
    id : int
        项目id

    Returns
    -------
    Tuple[List[dict], List[dict]]
        (图表列表, 命名空间列表)
    """
    # 支持的图表类型
    allow_types = ["default", "line", "image", "audio"]

    # 先查询属于该 project 的 experiment id 列表（避免直接使用不存在的 Chart.project_id）
    experiments = Experiment.filter(Experiment.project == id)
    exp_ids = [exp.id for exp in experiments] if experiments else []

    if not exp_ids:
        # 没有 experiment，直接返回空结构
        return get_pinned_and_hidden([], [], project_id=id)

    # 根据 experiment_id 列表查询 chart（注意模型字段名为 chart_type、experiment/exeriment_id）
    try:
        multi_charts = Chart.filter(Chart.experiment.in_(exp_ids), Chart.chart_type.in_(allow_types))
    except Exception as e:
        # 兜底：如果 ORM 不支持 in_ 或 filter 的组合，回退到遍历过滤
        logger.warning(f"Failed to query charts with in_ filter for project {id}: {e}, falling back to manual filtering")
        all_charts = Chart.filter() if hasattr(Chart, "filter") else []
        multi_charts = [c for c in all_charts if getattr(c, "experiment", None) and getattr(getattr(c, "experiment"), "project", None) and getattr(getattr(c, "experiment"), "project").id == id and getattr(c, "chart_type", None) in allow_types]

    # 获取图表配置
    charts = []
    # source -> experiment_id（复用原逻辑）
    for _chart in multi_charts:
        sources, error = [], {}
        source_map = {}

        # 处理不同 ORM 返回值的兼容：优先使用 ORM 关联对象列表，否则尝试访问属性
        for source in _chart.sources:
            try:
                # source -> tag -> experiment
                tag = getattr(source, "tag", None) or getattr(source, "tag_id", None) or {}
                exp_obj = getattr(tag, "experiment", None) or getattr(tag, "experiment_id", None)
                name = getattr(tag, "name", None) or (tag.get("name") if isinstance(tag, dict) else None)
                exp_name = getattr(exp_obj, "name", None) if exp_obj else None
                exp_id = getattr(exp_obj, "id", None) if exp_obj else exp_obj if isinstance(exp_obj, int) else None
                if exp_name:
                    sources.append(exp_name)
                    source_map[exp_name] = exp_id
                # error 信息字段兼容
                err = getattr(source, "error_info", None) or getattr(source, "error", None)
                if err:
                    error[exp_name or str(exp_id)] = Chart.json_to_dict(err) if hasattr(Chart, "json_to_dict") else {}
            except Exception:
                continue
        # 将 chart 转为 dict/序列化表现（保留原行为）
        try:
            t = _chart.__dict__()
        except Exception:
            # 回退：尝试用 model 的 to_dict 或 __dict__
            t = _chart.to_dict() if hasattr(_chart, "to_dict") else dict(getattr(_chart, "__dict__", {}))
        charts.append({**t, "error": error, "source": sources, "multi": True, "source_map": source_map})

    # 获取所有 namespace（namespace 不再与 project 直接关联，需按 displays 中的 chart 过滤）
    namespaces = Namespace.filter() if hasattr(Namespace, "filter") else []
    namespace_list = Namespace.search2list(namespaces) if hasattr(Namespace, "search2list") else []

    # 预加载 experiment_id -> project_id 映射，避免循环中的 N+1 查询
    exp_to_proj_map = {exp.id: getattr(exp.project, "id", None) for exp in experiments}

    def _chart_belongs_to_project(chart_repr: dict, project_id: int) -> bool:
        """
        尝试从 display 返回的 chart 表示中判断 chart 是否属于指定 project。
        支持多种结构：chart_repr 中的 'experiment' 可能为 id、dict 或嵌套包含 project 信息。
        使用预加载的映射避免数据库查询。
        """
        if not isinstance(chart_repr, dict):
            return False
        # 可能的键名
        exp_field = chart_repr.get("experiment") or chart_repr.get("experiment_id")
        # 如果是 dict，查看其中的 project 或 project_id
        if isinstance(exp_field, dict):
            proj = exp_field.get("project") or exp_field.get("project_id")
            if isinstance(proj, dict):
                return proj.get("id") == project_id
            return proj == project_id
        # 如果是 int，使用预加载的映射
        if isinstance(exp_field, int):
            proj_id = exp_to_proj_map.get(exp_field)
            return proj_id == project_id
        return False

    # 通过 namespace -> displays -> chart 来筛选出属于该 project 的 namespace 中的 charts
    for index, namespace in enumerate(namespaces):
        displays = []
        namespace_displays = Display.search2list(namespace.displays)
        for display in namespace_displays:
            chart_repr = display.get("chart_id") if isinstance(display, dict) else None
            if not chart_repr:
                continue
            # 兼容旧键名 'type' 与 新键名 'chart_type'
            ctype = chart_repr.get("type") or chart_repr.get("chart_type")
            if ctype not in allow_types:
                continue
            # 判断该 chart 是否属于当前 project
            belongs = _chart_belongs_to_project(chart_repr, id)
            if belongs:
                displays.append(chart_repr.get("id"))
        if len(displays) > 0:
            namespace_list[index]["charts"] = displays

    # 过滤 namespace 中没有 charts 的项
    namespace_list = [namespace for namespace in namespace_list if "charts" in namespace and len(namespace["charts"]) > 0]

    return get_pinned_and_hidden(charts, namespace_list, project_id=id)


def get_pinned_and_hidden(
    chart_list: List[dict],
    namespace_list: List[dict],
    project_id: Optional[int] = None,
    experiment_id: Optional[int] = None
) -> Tuple[List[dict], List[dict]]:
    """
    获取置顶图表与隐藏图表

    Parameters
    ----------
    chart_list : List[dict]
        图表列表
    namespace_list : List[dict]
        命名空间列表
    project_id : int, optional
        项目ID，用于查询项目的 pinned_opened 和 hidden_opened
    experiment_id : int, optional
        实验ID，用于查询实验的 pinned_opened 和 hidden_opened
    """
    # 如果没有图表，返回空列表
    if not len(chart_list):
        return chart_list, namespace_list

    # 获取pinned和hidden的开启/关闭状态
    pinned_opened = 1  # 默认值
    hidden_opened = 0  # 默认值

    # 从数据库查询 experiment 或 project 的状态
    from ...db.mysql import CloudProject as Project

    if experiment_id:
        try:
            exp = Experiment.get_by_id(experiment_id)
            if exp:
                pinned_opened = getattr(exp, 'pinned_opened', 1)
                hidden_opened = getattr(exp, 'hidden_opened', 0)
        except Exception as e:
            logger.debug(f"Failed to fetch experiment {experiment_id} for pinned/hidden status: {e}")
    elif project_id:
        try:
            proj = Project.get_by_id(project_id)
            if proj:
                pinned_opened = getattr(proj, 'pinned_opened', 1)
                hidden_opened = getattr(proj, 'hidden_opened', 0)
        except Exception as e:
            logger.debug(f"Failed to fetch project {project_id} for pinned/hidden status: {e}")

    # 如果无法从参数获取，尝试从 chart_list 推断
    if not experiment_id and not project_id and len(chart_list) > 0:
        first_chart = chart_list[0]
        # 尝试从 chart 中获取 experiment 或 project 的 ID
        exp_id = first_chart.get("experiment") or first_chart.get("experiment_id")
        proj_id = first_chart.get("project") or first_chart.get("project_id")

        if exp_id and isinstance(exp_id, int):
            try:
                exp = Experiment.get_by_id(exp_id)
                if exp:
                    pinned_opened = getattr(exp, 'pinned_opened', 1)
                    hidden_opened = getattr(exp, 'hidden_opened', 0)
                    experiment_id = exp_id
            except Exception as e:
                logger.debug(f"Failed to infer experiment {exp_id} from chart_list: {e}")
        elif proj_id and isinstance(proj_id, int):
            try:
                proj = Project.get_by_id(proj_id)
                if proj:
                    pinned_opened = getattr(proj, 'pinned_opened', 1)
                    hidden_opened = getattr(proj, 'hidden_opened', 0)
                    project_id = proj_id
            except Exception as e:
                logger.debug(f"Failed to infer project {proj_id} from chart_list: {e}")

    # 遍历chart_list，动态生成pinned与hidden的namespace，这两个namespace的id分别为-1与-2
    pinned_namespace = {
        "id": -1,
        "name": "pinned",
        "charts": [],
        "opened": pinned_opened,
        "experiment_id": experiment_id,
        "project_id": project_id,
    }
    hidden_namespace = {
        "id": -2,
        "name": "hidden",
        "charts": [],
        "opened": hidden_opened,
        "experiment_id": experiment_id,
        "project_id": project_id,
    }
    for chart in chart_list:
        # 如果chart的status为1，则将其加入pinned的namespace，如果是-1加入hidden的namespace
        # 如果是0，则不加入任何namespace
        # 首先将chart对象加入pinned或hidden的namespace，后续会滤除为id
        chart_status = chart.get("status", 0)
        if chart_status == 1:
            pinned_namespace["charts"].append(chart)
        elif chart_status == -1:
            hidden_namespace["charts"].append(chart)
        if chart_status != 0:
            chart_id = chart.get("id")
            if chart_id is not None:
                del_chart_from_namespace(namespace_list, chart_id)
    # 滤除namespace中的空charts的namespace
    namespace_list = [namespace for namespace in namespace_list if len(namespace.get("charts", [])) != 0]

    # 如果没有任何 namespace，创建一个默认的 namespace 包含所有 status=0 的图表
    if len(namespace_list) == 0:
        default_charts = [chart for chart in chart_list if chart.get("status", 0) == 0]
        if len(default_charts) > 0:
            default_namespace = {
                "id": 1,
                "name": "default",
                "charts": [chart.get("id") for chart in default_charts],
                "sort": 0,
                "opened": 1,
                "experiment_id": experiment_id,
                "project_id": project_id,
            }
            namespace_list.append(default_namespace)

    # 如果pinned_namespace中有charts，则加入namespace_list的首位
    if len(pinned_namespace["charts"]) > 0:
        # namespaces的charts字段根据每个元素的sort排序，小的在前
        pinned_namespace["charts"].sort(key=lambda x: x.get("sort", 0))
        pinned_namespace = {**pinned_namespace, "charts": [chart.get("id") for chart in pinned_namespace["charts"]]}
        namespace_list.insert(0, pinned_namespace)
    # 如果hidden_namespace中有charts，则加入namespace_list的末位
    if len(hidden_namespace["charts"]) > 0:
        # namespaces的charts字段根据每个元素的sort排序，小的在前
        hidden_namespace["charts"].sort(key=lambda x: x.get("sort", 0))
        hidden_namespace = {**hidden_namespace, "charts": [chart.get("id") for chart in hidden_namespace["charts"]]}
        namespace_list.append(hidden_namespace)
    return chart_list, namespace_list


def del_chart_from_namespace(namespace_list: List[dict], chart_id: int) -> List[dict]:
    """
    从命名空间中删除图表
    """
    for namespace in namespace_list:
        if chart_id in namespace["charts"]:
            namespace["charts"].remove(chart_id)
    return namespace_list
