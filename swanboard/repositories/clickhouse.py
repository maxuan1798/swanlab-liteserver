#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ClickHouse Repository - 用于查询时序数据
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..db.clickhouse import clickhouse_manager
from ..utils import swanlog


class ClickHouseRepository:
    """ClickHouse 数据查询仓库"""

    def __init__(self):
        self.manager = clickhouse_manager

    def get_column_by_run_and_key(self, run_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        根据 run_id 和 key 获取列信息

        Args:
            run_id: 运行 ID
            key: 列的 key（tag）

        Returns:
            列信息字典，如果不存在返回 None
        """
        query = """
        SELECT
            run_id,
            column_id,
            key,
            name,
            cls,
            typ,
            chart_type
        FROM column
        WHERE run_id = %(run_id)s AND key = %(key)s
        LIMIT 1
        """

        try:
            result = self.manager.execute(query, {'run_id': run_id, 'key': key})
            if result:
                row = result[0]
                return {
                    'run_id': row[0],
                    'column_id': row[1],
                    'key': row[2],
                    'name': row[3],
                    'cls': row[4],
                    'typ': row[5],
                    'chart_type': row[6]
                }
            return None
        except Exception as e:
            swanlog.error(f"Failed to get column: {e}")
            return None

    def get_metric_data(
        self,
        run_id: str,
        column_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取指标数据

        Args:
            run_id: 运行 ID
            column_id: 列 ID
            limit: 限制返回的数据条数

        Returns:
            指标数据列表，每个元素包含 step 和 value
        """
        query = """
        SELECT
            step,
            epoch,
            value,
            metric_data
        FROM metric
        WHERE run_id = %(run_id)s AND column_id = %(column_id)s
        ORDER BY step ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            result = self.manager.execute(query, {
                'run_id': run_id,
                'column_id': column_id
            })

            data_list = []
            for row in result:
                step, epoch, value, metric_data = row
                # 根据数据类型构建返回数据
                if value is not None:
                    # 标量数据
                    data_list.append({
                        'index': step,
                        'step': step,
                        'epoch': epoch,
                        'data': value
                    })
                elif metric_data:
                    # 媒体数据
                    data_list.append({
                        'index': step,
                        'step': step,
                        'epoch': epoch,
                        'data': metric_data  # 媒体数据的文件名列表
                    })

            return data_list
        except Exception as e:
            swanlog.error(f"Failed to get metric data: {e}")
            return []

    def get_metric_summary(
        self,
        run_id: str,
        column_id: str
    ) -> Dict[str, Any]:
        """
        获取指标的汇总信息（最大值、最小值、总数）

        Args:
            run_id: 运行 ID
            column_id: 列 ID

        Returns:
            包含 max、min、count 的字典
        """
        query = """
        SELECT
            MAX(value) as max_value,
            MIN(value) as min_value,
            COUNT(*) as count
        FROM metric
        WHERE run_id = %(run_id)s
          AND column_id = %(column_id)s
          AND value IS NOT NULL
        """

        try:
            result = self.manager.execute(query, {
                'run_id': run_id,
                'column_id': column_id
            })

            if result:
                row = result[0]
                return {
                    'max': row[0],
                    'min': row[1],
                    'count': row[2]
                }
            return {'max': None, 'min': None, 'count': 0}
        except Exception as e:
            swanlog.error(f"Failed to get metric summary: {e}")
            return {'max': None, 'min': None, 'count': 0}

    def get_logs(
        self,
        run_id: str,
        limit: int = 100,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取日志数据

        Args:
            run_id: 运行 ID
            limit: 限制返回的日志条数
            level: 日志级别过滤（可选）

        Returns:
            日志列表
        """
        query = """
        SELECT
            timestamp,
            level,
            epoch,
            message,
            contents
        FROM log
        WHERE run_id = %(run_id)s
        """

        if level:
            query += " AND level = %(level)s"

        query += " ORDER BY timestamp DESC"
        query += f" LIMIT {limit}"

        params = {'run_id': run_id}
        if level:
            params['level'] = level

        try:
            result = self.manager.execute(query, params)

            logs = []
            for row in result:
                timestamp, log_level, epoch, message, contents = row
                logs.append({
                    'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
                    'level': log_level,
                    'epoch': epoch,
                    'message': message,
                    'contents': contents if contents else []
                })

            return logs
        except Exception as e:
            swanlog.error(f"Failed to get logs: {e}")
            return []

    def get_recent_log_dates(self, run_id: str) -> List[str]:
        """
        获取最近有日志的日期列表

        Args:
            run_id: 运行 ID

        Returns:
            日期列表（格式：YYYY-MM-DD）
        """
        query = """
        SELECT DISTINCT toDate(timestamp) as log_date
        FROM log
        WHERE run_id = %(run_id)s
        ORDER BY log_date DESC
        LIMIT 10
        """

        try:
            result = self.manager.execute(query, {'run_id': run_id})
            dates = [str(row[0]) for row in result]
            return dates
        except Exception as e:
            swanlog.error(f"Failed to get recent log dates: {e}")
            return []

    def get_runtime_info(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        获取运行时信息

        Args:
            run_id: 运行 ID

        Returns:
            运行时信息字典
        """
        query = """
        SELECT
            python_version,
            platform,
            cuda_version,
            requirements,
            metadata,
            config,
            conda
        FROM runtime
        WHERE run_id = %(run_id)s
        ORDER BY timestamp DESC
        LIMIT 1
        """

        try:
            result = self.manager.execute(query, {'run_id': run_id})

            if result:
                row = result[0]
                return {
                    'python_version': row[0],
                    'platform': row[1],
                    'cuda_version': row[2],
                    'requirements': row[3],
                    'metadata': row[4],
                    'config': row[5],
                    'conda': row[6]
                }
            return None
        except Exception as e:
            swanlog.error(f"Failed to get runtime info: {e}")
            return None


# 全局 ClickHouse repository 实例
clickhouse_repository = ClickHouseRepository()