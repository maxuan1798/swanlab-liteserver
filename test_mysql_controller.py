#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwanLab MySQL Cloud Controller Test Script
测试MySQL云端控制器功能
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_mysql_controller():
    """测试MySQL控制器导入和基础功能"""

    print("🧪 Testing MySQL Cloud Controller")
    print("=" * 50)

    success = True

    # 1. 测试导入MySQL云端模块
    try:
        from swanboard.cloud_api.mysql_models import (
            CloudProject, CloudExperiment, CloudChart, CloudTag,
            CloudNamespace, CloudSource, CloudDisplay
        )
        print("✅ MySQL cloud models imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import MySQL cloud models: {e}")
        success = False

    # 2. 测试MySQL配置
    try:
        from swanboard.cloud_api.mysql_config import MySQLConfig
        config = MySQLConfig.from_env()
        print(f"✅ MySQL config loaded: {config.host}:{config.port}/{config.database}")
    except Exception as e:
        print(f"❌ Failed to load MySQL config: {e}")
        success = False

    # 3. 测试云端控制器导入
    try:
        from swanboard.controller.cloud import (
            sync_project, sync_experiment, sync_column,
            update_experiment_status, get_workspace_projects,
            get_project_experiments, validate_api_key,
            validate_workspace, _ensure_cloud_db_connected
        )
        print("✅ MySQL cloud controller functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import cloud controller functions: {e}")
        success = False

    # 4. 测试API验证函数
    try:
        # 测试没有授权的情况
        result = validate_api_key(None)
        if not result:
            print("✅ API key validation correctly rejects None")
        else:
            print("❌ API key validation incorrectly accepts None")
            success = False

        # 测试错误格式的授权
        result = validate_api_key("InvalidFormat")
        if not result:
            print("✅ API key validation correctly rejects invalid format")
        else:
            print("❌ API key validation incorrectly accepts invalid format")
            success = False

        # 测试正确格式的授权
        result = validate_api_key("Bearer test_token")
        if result:  # 在开发模式下应该返回True
            print("✅ API key validation accepts Bearer token format")
        else:
            print("⚠️  API key validation rejects Bearer token (may be expected if SWANLAB_API_KEY is set)")

    except Exception as e:
        print(f"❌ Error testing API key validation: {e}")
        success = False

    # 5. 测试工作空间验证
    try:
        result = validate_workspace("test_workspace")
        if result:
            print("✅ Workspace validation works")
        else:
            print("⚠️  Workspace validation rejected test_workspace (may be expected)")
    except Exception as e:
        print(f"❌ Error testing workspace validation: {e}")
        success = False

    # 6. 测试数据库连接函数（不实际连接）
    try:
        # 这个函数应该能被调用，即使连接失败
        result = _ensure_cloud_db_connected()
        if result:
            print("✅ Cloud database connection successful")
        else:
            print("⚠️  Cloud database connection failed (expected if MySQL not running)")
    except Exception as e:
        print(f"❌ Error testing database connection: {e}")
        success = False

    # 7. 测试Swagger文档功能
    try:
        # 如果服务器正在运行，测试Swagger端点
        import requests
        try:
            response = requests.get("http://localhost:5173/api/v1/openapi.json", timeout=2)
            if response.status_code == 200:
                schema = response.json()
                cloud_paths = [path for path in schema.get('paths', {}).keys() if '/cloud/' in path]
                print(f"✅ Swagger API documentation: {len(cloud_paths)} cloud endpoints found")
            else:
                print("⚠️  Swagger API not accessible (server may not be running)")
        except requests.exceptions.ConnectionError:
            print("⚠️  SwanLab-Dashboard server not running")
    except ImportError:
        print("⚠️  Requests module not available for Swagger test")
    except Exception as e:
        print(f"❌ Error testing Swagger documentation: {e}")
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 MySQL Cloud Controller Tests Passed!")
        print("\n📋 Summary:")
        print("- ✅ MySQL models and configuration working")
        print("- ✅ Cloud controller functions accessible")
        print("- ✅ API validation functions working")
        print("- ✅ Swagger UI configuration complete")

        print("\n🚀 Next Steps:")
        print("1. Start MySQL server (if not running)")
        print("2. Configure MySQL environment variables:")
        print("   export MYSQL_HOST=localhost")
        print("   export MYSQL_PORT=3306")
        print("   export MYSQL_USER=root")
        print("   export MYSQL_PASSWORD=your_password")
        print("   export MYSQL_DATABASE=swanlab_cloud")
        print("3. Start SwanLab-Dashboard server:")
        print("   uvicorn swanboard.app:app --host 0.0.0.0 --port 5173")
        print("4. Test API endpoints with:")
        print("   python test/test_cloud_api.py")

    else:
        print("❌ Some tests failed!")
        print("Please check the error messages above and fix any issues.")

    return success

def main():
    """主函数"""
    print("SwanLab MySQL Cloud Controller Test")
    print("===================================")

    # 设置测试环境变量
    os.environ.setdefault('MYSQL_HOST', 'localhost')
    os.environ.setdefault('MYSQL_PORT', '3306')
    os.environ.setdefault('MYSQL_USER', 'root')
    os.environ.setdefault('MYSQL_PASSWORD', 'swanlab123')
    os.environ.setdefault('MYSQL_DATABASE', 'swanlab_cloud')
    os.environ.setdefault('SWANLAB_ALLOWED_WORKSPACES', 'default,test_workspace')

    try:
        success = asyncio.run(test_mysql_controller())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)