from swankit.callback import SwanKitCallback
from swankit.callback.models import ColumnInfo
from .db.models import *
from .db import add_multi_chart, connect, NotExistedError, ExistedError, ChartTypeError
from typing import Tuple, Optional
from swanboard.utils import swanlog
import time


class SwanBoardCallback(SwanKitCallback):
    """
    SwanBoardCallback类，swanlab本体与数据库的连接回调函数
    """

    def __init__(self, db_config: Optional[dict] = None):
        super(SwanBoardCallback, self).__init__()
        self.exp: Optional[Experiment] = None
        self.db_config = db_config

    def __str__(self) -> str:
        return "SwanBoardCallback"

    def on_init(self, proj_name: str, *args, **kwargs):
        # 连接MySQL数据库，如果数据库不存在会自动创建
        # 可以通过构造函数传入db_config参数，或通过环境变量或配置文件设置MySQL连接参数
        import os
        if self.db_config:
            db_config = {
                'database': self.db_config.get('database', 'swanlab'),
                'user': self.db_config.get('user', 'root'),
                'password': self.db_config.get('password', ''),
                'host': self.db_config.get('host', 'localhost'),
                'port': self.db_config.get('port', 3306),
                'autocreate': self.db_config.get('autocreate', True)
            }
        else:
            db_config = {
                'database': os.getenv('MYSQL_DATABASE', 'swanlab'),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', '3306')),
                'autocreate': True
            }
        connect(**db_config)
        # 初始化项目数据库
        Project.init(proj_name)

    def before_init_experiment(
        self,
        run_id: str,
        exp_name: str,
        description: str,
        num: int,
        colors: Tuple[str, str],
        *args,
        **kwargs,
    ):
        original_exp_name = exp_name
        print("Before init experiment:", original_exp_name)
        # ---------------------------------- 实验名称校验 ----------------------------------
        # 这个循环的目的是如果创建失败则等零点五秒重新生成后缀重新创建，直到创建成功

        def find_next_available_name(base_name: str) -> str:
            """找到下一个可用的实验名称"""
            # 首先尝试原始名称
            if not Experiment.filter(Experiment.name == base_name).exists():
                return base_name

            # 获取所有以base_name开头的实验名称
            existing_names = [exp.name for exp in Experiment.filter(Experiment.name.startswith(base_name))]

            # 提取所有数字后缀
            max_suffix = 0
            for name in existing_names:
                if name == base_name:
                    max_suffix = max(max_suffix, 1)
                elif name.startswith(base_name + "-"):
                    suffix_part = name[len(base_name) + 1:]
                    if suffix_part.isdigit():
                        max_suffix = max(max_suffix, int(suffix_part) + 1)

            return f"{base_name}-{max_suffix}"

        while True:
            try:
                # 获得数据库实例
                self.exp = Experiment.create(
                    name=exp_name,
                    run_id=run_id,
                    description=description,
                    num=num,
                    colors=colors,
                )
                break
            except ExistedError:
                swanlog.debug(f"Experiment {exp_name} has existed, try another name...")
                exp_name = find_next_available_name(original_exp_name)
                time.sleep(0.2)

    def on_log(self, *args, **kwargs):
        # 每一次log的时候检查一下数据库中的实验状态
        # 如果实验状态不为0，说明实验已经结束，不允许再次调用log方法
        # 这意味着每次log都会进行查询，比较消耗性能，后续考虑采用多进程共享内存的方式进行优化
        swanlog.debug(f"Check experiment and state...")
        try:
            exp = Experiment.get(id=self.exp.id)
        except NotExistedError:
            raise KeyboardInterrupt("The experiment has been deleted by the user")
        # 此时self.__state == 0，说明是前端主动停止的
        if exp.status != 0:
            raise KeyboardInterrupt("The experiment has been stopped by the user")

    def on_column_create(self, column_info: ColumnInfo, *args, **kwargs):

        if column_info.cls != "CUSTOM":
            return  # 屏蔽系统生成的指标
        chart_type = column_info.chart_type.value.chart_type
        # 创建Chart
        chart = Chart.create(
            column_info.key,
            experiment_id=self.exp,
            type=chart_type,
            reference=column_info.chart_reference.lower(),
        )
        # 创建命名空间，如果命名空间已经存在，会抛出ExistedError异常，捕获不处理即可
        # 需要指定sort，default命名空间的sort为0，其他命名空间的sort为None，表示默认添加到最后
        namespace = column_info.section_name
        try:
            n = Namespace.create(name=namespace, experiment_id=self.exp.id, sort=column_info.section_sort)
            swanlog.debug(f"Namespace {namespace} created, id: {n.id}")
        except ExistedError:
            n: Namespace = Namespace.get(name=namespace, experiment_id=self.exp.id)
            swanlog.debug(f"Namespace {namespace} exists, id: {n.id}")
        # 创建display，这个必然是成功的，因为display是唯一的，直接添加到最后一条即可
        Display.create(chart_id=chart.id, namespace_id=n.id)
        tag: Tag = Tag.create(
            experiment_id=self.exp.id,
            name=column_info.key,
            type=chart_type,
            folder=column_info.kid,
        )
        # 添加一条source记录
        error = None
        if column_info.error is not None:
            error = {
                "data_class": column_info.error.got,
                "excepted": column_info.error.expected,
            }
        Source.create(tag_id=tag.id, chart_id=chart.id, error=error)
        # 新建多实验对比图表数据
        try:
            add_multi_chart(tag_id=tag.id, chart_id=chart.id)
        except ChartTypeError:
            swanlog.debug("In the multi-experiment chart, the current type of tag is not as expected.")

    def on_stop(self, error: str = None, *args, **kwargs):
        # 更新数据库中的实验状态
        self.exp.update_status(-1 if error is not None else 1)
