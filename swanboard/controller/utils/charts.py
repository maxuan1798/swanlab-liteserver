#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2024-03-09 21:43:59
@File: swanlab/server/controller/utils/charts.py
@IDE: vscode
@Description:
    图表相关函数 - 云端版本
"""
from ...db import CloudChart
from ...db.mysql import CloudChart as Chart, CloudDisplay as Display, CloudNamespace as Namespace, CloudExperiment as Experiment
from typing import List, Union


def get_exp_charts(id: int):
    """
    获取单实验图表数据

    Parameters
    ----------
    id : int
        实验id
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
    return get_pinned_and_hidden(chart_list, namespace_list)


def get_proj_charts(id: int):
    """
    获取多实验对比图表数据

    Parameters
    ----------
    id : int
        项目id
    """
    # 支持的图表类型
    allow_types = ["default", "line", "image", "audio"]

    # 先查询属于该 project 的 experiment id 列表（避免直接使用不存在的 Chart.project_id）
    experiments = Experiment.filter(Experiment.project == id)
    exp_ids = [exp.id for exp in experiments] if experiments else []

    if not exp_ids:
        # 没有 experiment，直接返回空结构
        return get_pinned_and_hidden([], [])

    # 根据 experiment_id 列表查询 chart（注意模型字段名为 chart_type、experiment/exeriment_id）
    try:
        multi_charts = Chart.filter(Chart.experiment.in_(exp_ids), Chart.chart_type.in_(allow_types))
    except Exception:
        # 兜底：如果 ORM 不支持 in_ 或 filter 的组合，回退到遍历过滤
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
            print("chart source:", source)
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

    def _chart_belongs_to_project(chart_repr: dict, project_id: int) -> bool:
        """
        尝试从 display 返回的 chart 表示中判断 chart 是否属于指定 project。
        支持多种结构：chart_repr 中的 'experiment' 可能为 id、dict 或嵌套包含 project 信息。
        回退到 DB 查询 Experiment 时也会尝试确定关系。
        """
        if not isinstance(chart_repr, dict):
            return False
        # 可能的键名
        exp_field = chart_repr.get("experiment") or chart_repr.get("experiment_id") or chart_repr.get("experiment_id")
        # 如果是 dict，查看其中的 project 或 project_id
        if isinstance(exp_field, dict):
            proj = exp_field.get("project") or exp_field.get("project_id")
            if isinstance(proj, dict):
                return proj.get("id") == project_id
            return proj == project_id
        # 如果是 int，直接用 DB 判断
        if isinstance(exp_field, int):
            exps = Experiment.filter(Experiment.id == exp_field)
            if exps:
                return getattr(exps[0].project, "id", None) == project_id
        return False

    # 通过 namespace -> displays -> chart 来筛选出属于该 project 的 namespace 中的 charts
    for index, namespace in enumerate(namespaces):
        displays = []
        for display in Display.search2list(namespace.displays):
            chart_repr = display.get("chart_id") if isinstance(display, dict) else None
            if not chart_repr:
                continue
            # 兼容旧键名 'type' 与 新键名 'chart_type'
            ctype = chart_repr.get("type") or chart_repr.get("chart_type")
            if ctype not in allow_types:
                continue
            # 判断该 chart 是否属于当前 project
            if _chart_belongs_to_project(chart_repr, id):
                displays.append(chart_repr.get("id"))
        if len(displays) > 0:
            namespace_list[index]["charts"] = displays

    # 过滤 namespace 中没有 charts 的项
    namespace_list = [namespace for namespace in namespace_list if "charts" in namespace and len(namespace["charts"]) > 0]

    return get_pinned_and_hidden(charts, namespace_list)


def get_pinned_and_hidden(chart_list: List[dict], namespace_list: List[dict]) -> Union[List[dict], List[dict]]:
    """
    获取置顶图表与隐藏图表
    """
    if not len(chart_list) or not len(namespace_list):
        return chart_list, namespace_list
    # 获取pinned和hidden的开启/关闭状态，通过chart_list的第一个元素的experiment_id或者project_id获取
    first_chart = chart_list[0]
    if first_chart["experiment_id"] is not None:
        exp_or_proj = first_chart["experiment_id"]
    else:
        exp_or_proj = first_chart["project_id"]
    pinned_opened, hidden_opened = exp_or_proj["pinned_opened"], exp_or_proj["hidden_opened"]

    # 遍历chart_list，动态生成pinned与hidden的namespace，这两个namespace的id分别为-1与-2
    pinned_namespace = {
        "id": -1,
        "name": "pinned",
        "charts": [],
        "opened": pinned_opened,
        "experiment_id": first_chart["experiment_id"],
        "project_id": first_chart["project_id"],
    }
    hidden_namespace = {
        "id": -2,
        "name": "hidden",
        "charts": [],
        "opened": hidden_opened,
        "experiment_id": first_chart["experiment_id"],
        "project_id": first_chart["project_id"],
    }
    for chart in chart_list:
        # 如果chart的status为1，则将其加入pinned的namespace，如果是-1加入hidden的namespace
        # 如果是0，则不加入任何namespace
        # 首先将chart对象加入pinned或hidden的namespace，后续会滤除为id
        if chart["status"] == 1:
            pinned_namespace["charts"].append(chart)
        elif chart["status"] == -1:
            hidden_namespace["charts"].append(chart)
        if chart["status"] != 0:
            del_chart_from_namespace(namespace_list, chart["id"])
    # 滤除namespace中的空charts的namespace
    namespace_list = [namespace for namespace in namespace_list if len(namespace["charts"]) != 0]
    # 如果pinned_namespace中有charts，则加入namespace_list的首位
    if len(pinned_namespace["charts"]) > 0:
        # namespaces的charts字段根据每个元素的sort排序，小的在前
        pinned_namespace["charts"].sort(key=lambda x: x["sort"])
        pinned_namespace = {**pinned_namespace, "charts": [chart["id"] for chart in pinned_namespace["charts"]]}
        namespace_list.insert(0, pinned_namespace)
    # 如果hidden_namespace中有charts，则加入namespace_list的末位
    if len(hidden_namespace["charts"]) > 0:
        # namespaces的charts字段根据每个元素的sort排序，小的在前
        hidden_namespace["charts"].sort(key=lambda x: x["sort"])
        hidden_namespace = {**hidden_namespace, "charts": [chart["id"] for chart in hidden_namespace["charts"]]}
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
