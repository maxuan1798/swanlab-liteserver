#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SwanLab MySQL云端同步使用示例

这个示例展示了如何使用EnhancedSwanBoardCallback进行MySQL云端同步
"""

import os
import sys
import time
from typing import Dict, Any

# 添加swanboard到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from swanboard.enhanced_callback import EnhancedSwanBoardCallback
from swanboard.cloud_api import MySQLConfig


def setup_environment():
    """设置环境变量示例"""
    # 启用云端同步
    os.environ['SWANLAB_CLOUD_SYNC'] = 'true'

    # MySQL数据库配置
    os.environ['MYSQL_HOST'] = 'localhost'
    os.environ['MYSQL_PORT'] = '3306'
    os.environ['MYSQL_USER'] = 'swanlab_user'
    os.environ['MYSQL_PASSWORD'] = 'your_password'
    os.environ['MYSQL_DATABASE'] = 'swanlab_cloud'

    # 工作空间配置
    os.environ['SWANLAB_WORKSPACE'] = 'example_workspace'
    os.environ['SWANLAB_USER'] = 'example_user'


def example_with_env_config():
    """使用环境变量配置的示例"""
    print("=== 使用环境变量配置 ===")

    # 设置环境变量
    setup_environment()

    # 创建增强回调（会自动从环境变量读取配置）
    callback = EnhancedSwanBoardCallback(enable_cloud=True)

    # 模拟SwanLab工作流程
    try:
        # 1. 初始化项目
        print("初始化项目...")
        callback.on_init("example_project")

        # 2. 创建实验
        print("创建实验...")
        callback.before_init_experiment(
            run_id="run_20241126_001",
            exp_name="example_experiment",
            description="这是一个示例实验",
            num=1,
            colors=("#FF6B6B", "#4ECDC4")
        )

        # 3. 模拟创建一些指标
        print("创建指标...")
        # 这里需要真实的ColumnInfo对象，实际使用中由SwanKit提供
        # callback.on_column_create(column_info)

        # 4. 模拟实验结束
        print("实验结束...")
        callback.on_stop(error=None)  # 成功结束

        # 5. 获取同步统计信息
        stats = callback.get_cloud_sync_stats()
        print(f"同步统计信息: {stats}")

    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        callback.on_stop(error=str(e))  # 错误结束


def example_with_manual_config():
    """使用手动配置的示例"""
    print("\n=== 使用手动配置 ===")

    # 手动创建MySQL配置
    mysql_config = MySQLConfig(
        host='localhost',
        port=3306,
        user='swanlab_user',
        password='your_password',
        database='swanlab_cloud',
        charset='utf8mb4',
        max_connections=10
    )

    # 验证配置
    if not mysql_config.validate():
        print("MySQL配置验证失败!")
        return

    print(f"MySQL连接字符串: {mysql_config.get_connection_string()}")

    # 创建增强回调
    callback = EnhancedSwanBoardCallback(
        enable_cloud=True,
        mysql_config=mysql_config
    )

    # 设置工作空间信息（通过环境变量）
    os.environ['SWANLAB_WORKSPACE'] = 'manual_workspace'
    os.environ['SWANLAB_USER'] = 'manual_user'

    try:
        # 模拟工作流程
        callback.on_init("manual_project")

        callback.before_init_experiment(
            run_id="manual_run_001",
            exp_name="manual_experiment",
            description="手动配置的示例实验",
            num=1,
            colors=("#9B59B6", "#E74C3C")
        )

        callback.on_stop(error=None)

        # 获取统计信息
        stats = callback.get_cloud_sync_stats()
        print(f"手动配置同步统计: {stats}")

    except Exception as e:
        print(f"手动配置执行错误: {e}")


def example_cloud_sync_manager():
    """直接使用CloudSyncManager的示例"""
    print("\n=== 直接使用CloudSyncManager ===")

    from swanboard.cloud_api import CloudSyncManager
    from swanboard.cloud_api.mysql_connection import connect_cloud_db

    # 配置数据库连接
    mysql_config = MySQLConfig.from_env()

    if not connect_cloud_db(mysql_config):
        print("无法连接到MySQL数据库")
        return

    # 创建同步管理器
    sync_manager = CloudSyncManager(
        workspace='direct_workspace',
        user='direct_user'
    )

    try:
        # 1. 同步项目
        project_id = sync_manager.sync_project(
            name='direct_project',
            description='直接使用CloudSyncManager创建的项目'
        )
        print(f"项目同步完成，ID: {project_id}")

        # 2. 同步实验
        experiment_id = sync_manager.sync_experiment(
            run_id='direct_run_001',
            name='direct_experiment',
            description='直接同步的实验',
            colors=('#3498DB', '#2ECC71'),
            sort_order=1
        )
        print(f"实验同步完成，ID: {experiment_id}")

        # 3. 更新实验状态
        success = sync_manager.sync_experiment_status(status=1)  # 成功完成
        print(f"状态同步: {'成功' if success else '失败'}")

        # 4. 获取项目实验列表
        experiments = sync_manager.get_project_experiments('direct_project')
        print(f"项目实验列表: {len(experiments)} 个实验")

        # 5. 获取实验详情
        details = sync_manager.get_experiment_details('direct_run_001')
        if details:
            print(f"实验详情: {details['name']}, 状态: {details['status']}")

        # 6. 获取统计信息
        stats = sync_manager.get_stats()
        print(f"CloudSyncManager统计: {stats}")

    except Exception as e:
        print(f"CloudSyncManager示例错误: {e}")
    finally:
        sync_manager.cleanup()


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")

    # 故意使用错误的配置
    bad_config = MySQLConfig(
        host='nonexistent-host',
        user='wrong_user',
        password='wrong_password',
        database='nonexistent_db'
    )

    # 这应该会失败，但不会抛出异常
    callback = EnhancedSwanBoardCallback(
        enable_cloud=True,
        mysql_config=bad_config
    )

    # 检查云端同步是否可用
    stats = callback.get_cloud_sync_stats()
    if not stats.get('enabled', False):
        print("云端同步未启用（预期结果，因为使用了错误配置）")

    # 即使云端同步失败，本地功能仍然正常工作
    try:
        callback.on_init("local_only_project")
        callback.before_init_experiment(
            run_id="local_run_001",
            exp_name="local_experiment",
            description="只在本地运行的实验",
            num=1,
            colors=("#95A5A6", "#34495E")
        )
        callback.on_stop(error=None)
        print("本地功能正常工作，云端同步失败但不影响本地操作")
    except Exception as e:
        print(f"本地操作也失败了: {e}")


def demonstrate_cli_usage():
    """演示CLI工具使用"""
    print("\n=== CLI工具使用示例 ===")

    print("可用的CLI命令:")
    print("1. 测试连接:")
    print("   python -m swanboard.cloud_api.cli test-connection -h localhost -u root")

    print("2. 初始化数据库:")
    print("   python -m swanboard.cloud_api.cli init-db -h localhost -u root")

    print("3. 查看统计:")
    print("   python -m swanboard.cloud_api.cli stats -w my_workspace")

    print("4. 列出项目:")
    print("   python -m swanboard.cloud_api.cli list-projects -w my_workspace")

    print("5. 环境变量示例:")
    print("   python -m swanboard.cloud_api.cli env-example")


def main():
    """主函数"""
    print("SwanLab MySQL云端同步示例")
    print("=" * 50)

    try:
        # 1. 环境变量配置示例
        example_with_env_config()

        # 2. 手动配置示例
        example_with_manual_config()

        # 3. 直接使用CloudSyncManager
        example_cloud_sync_manager()

        # 4. 错误处理示例
        example_error_handling()

        # 5. CLI工具演示
        demonstrate_cli_usage()

    except KeyboardInterrupt:
        print("\n用户中断执行")
    except Exception as e:
        print(f"\n执行示例时发生错误: {e}")
    finally:
        print("\n示例执行完成")


if __name__ == '__main__':
    main()