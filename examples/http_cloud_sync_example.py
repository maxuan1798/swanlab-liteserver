#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SwanLab HTTP云端同步使用示例

这个示例展示了如何使用EnhancedSwanBoardCallback进行HTTP云端同步
"""

import os
import sys
import time

# 添加swanboard到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from swanboard.enhanced_callback import EnhancedSwanBoardCallback


def setup_environment():
    """设置环境变量示例"""
    # 启用云端同步
    os.environ['SWANLAB_CLOUD_SYNC'] = 'true'

    # HTTP API配置
    os.environ['SWANLAB_API_HOST'] = 'http://localhost:5173/api/v1/cloud'
    os.environ['SWANLAB_API_KEY'] = 'your_api_key'  # 可选，开发环境可不设置
    os.environ['SWANLAB_WORKSPACE'] = 'example_workspace'
    os.environ['SWANLAB_CLOUD_TIMEOUT'] = '30'


def example_with_env_config():
    """使用环境变量配置的示例"""
    print("=== 使用环境变量配置 ===")

    # 设置环境变量
    setup_environment()

    # 创建增强回调（会自动从环境变量读取配置）
    callback = EnhancedSwanBoardCallback(enable_cloud=True)

    # 检查云端同步状态
    stats = callback.get_cloud_sync_stats()
    print(f"Cloud sync stats: {stats}")

    # 模拟SwanLab工作流程
    try:
        # 1. 初始化项目
        print("初始化项目...")
        callback.on_init("example_project")

        # 2. 创建实验
        print("创建实验...")
        callback.before_init_experiment(
            run_id=f"run_{int(time.time())}",
            exp_name="example_experiment",
            description="这是一个示例实验",
            num=1,
            colors=("#FF6B6B", "#4ECDC4")
        )

        # 3. 模拟实验结束
        print("实验结束...")
        callback.on_stop(error=None)  # 成功结束

        print("✅ 所有操作完成！")

    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        callback.on_stop(error=str(e))  # 错误结束


def example_with_manual_config():
    """使用手动配置的示例"""
    print("\n=== 使用手动配置 ===")

    # 手动创建云端配置
    cloud_config = {
        'api_base': 'http://localhost:5173/api/v1/cloud',
        'api_key': 'your_api_key',  # 可选
        'workspace': 'manual_workspace',
        'timeout': 30
    }

    # 创建增强回调
    callback = EnhancedSwanBoardCallback(
        enable_cloud=True,
        cloud_config=cloud_config
    )

    # 检查云端同步状态
    stats = callback.get_cloud_sync_stats()
    print(f"Manual config stats: {stats}")

    try:
        # 模拟工作流程
        callback.on_init("manual_project")

        callback.before_init_experiment(
            run_id=f"manual_run_{int(time.time())}",
            exp_name="manual_experiment",
            description="手动配置的示例实验",
            num=1,
            colors=("#9B59B6", "#E74C3C")
        )

        callback.on_stop(error=None)

        print("✅ 手动配置示例完成！")

    except Exception as e:
        print(f"手动配置执行错误: {e}")


def example_without_cloud():
    """不启用云端同步的示例"""
    print("\n=== 不启用云端同步 ===")

    # 创建标准回调（不启用云端）
    callback = EnhancedSwanBoardCallback(enable_cloud=False)

    # 检查云端同步状态
    stats = callback.get_cloud_sync_stats()
    print(f"No cloud sync stats: {stats}")

    try:
        # 模拟工作流程（只在本地运行）
        callback.on_init("local_only_project")

        callback.before_init_experiment(
            run_id=f"local_run_{int(time.time())}",
            exp_name="local_experiment",
            description="只在本地运行的实验",
            num=1,
            colors=("#95A5A6", "#34495E")
        )

        callback.on_stop(error=None)

        print("✅ 本地模式完成！")

    except Exception as e:
        print(f"本地模式执行错误: {e}")


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")

    # 故意使用错误的配置
    bad_config = {
        'api_base': 'http://nonexistent-host:9999/api/v1/cloud',
        'api_key': 'wrong_key',
        'workspace': 'test_workspace',
        'timeout': 5
    }

    # 这应该会失败，但不会抛出异常
    callback = EnhancedSwanBoardCallback(
        enable_cloud=True,
        cloud_config=bad_config
    )

    # 检查云端同步是否可用
    stats = callback.get_cloud_sync_stats()
    if not stats.get('enabled', False):
        print("云端同步未启用（预期结果，因为使用了错误配置）")
        print(f"原因: {stats.get('reason')}")

    # 即使云端同步失败，本地功能仍然正常工作
    try:
        callback.on_init("error_handling_project")
        callback.before_init_experiment(
            run_id=f"error_run_{int(time.time())}",
            exp_name="error_experiment",
            description="错误处理示例实验",
            num=1,
            colors=("#E74C3C", "#C0392B")
        )
        callback.on_stop(error=None)
        print("✅ 本地功能正常工作，云端同步失败但不影响本地操作")
    except Exception as e:
        print(f"本地操作也失败了: {e}")


def demonstrate_helper_function():
    """演示辅助函数的使用"""
    print("\n=== 使用辅助函数 ===")

    from swanboard.enhanced_callback import create_enhanced_callback_with_http_cloud

    # 使用辅助函数创建回调
    callback = create_enhanced_callback_with_http_cloud(
        api_base='http://localhost:5173/api/v1/cloud',
        api_key='test_key',
        workspace='helper_workspace',
        timeout=30
    )

    stats = callback.get_cloud_sync_stats()
    print(f"Helper function stats: {stats}")

    try:
        callback.on_init("helper_project")
        callback.before_init_experiment(
            run_id=f"helper_run_{int(time.time())}",
            exp_name="helper_experiment",
            description="辅助函数创建的实验",
            num=1,
            colors=("#3498DB", "#2980B9")
        )
        callback.on_stop(error=None)
        print("✅ 辅助函数示例完成！")
    except Exception as e:
        print(f"辅助函数执行错误: {e}")


def main():
    """主函数"""
    print("SwanLab HTTP云端同步示例")
    print("=" * 50)

    # 检查SwanLab-Dashboard是否运行
    import requests
    try:
        response = requests.get("http://localhost:5173/api/v1/cloud/health", timeout=3)
        if response.status_code == 200:
            print("✅ SwanLab-Dashboard服务正在运行")
        else:
            print("⚠️  SwanLab-Dashboard服务响应异常")
    except requests.exceptions.ConnectionError:
        print("⚠️  SwanLab-Dashboard服务未运行")
        print("请先启动服务: python -m uvicorn swanboard.app:app --host 0.0.0.0 --port 5173")
        print("继续运行示例（仅演示本地功能）...")

    try:
        # 1. 环境变量配置示例
        example_with_env_config()

        # 2. 手动配置示例
        example_with_manual_config()

        # 3. 不启用云端同步
        example_without_cloud()

        # 4. 错误处理示例
        example_error_handling()

        # 5. 辅助函数示例
        demonstrate_helper_function()

    except KeyboardInterrupt:
        print("\n用户中断执行")
    except Exception as e:
        print(f"\n执行示例时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n示例执行完成")


if __name__ == '__main__':
    main()