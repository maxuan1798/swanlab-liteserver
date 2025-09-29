#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwanLab-Dashboard Swagger UI Verification Script
验证Swagger UI配置是否正确
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def verify_swagger_config():
    """验证Swagger配置"""
    print("🔍 Verifying SwanLab-Dashboard Swagger UI Configuration")
    print("=" * 60)

    try:
        # 1. 导入并检查FastAPI应用
        from swanboard.app import app
        print("✅ FastAPI app imported successfully")

        # 2. 检查OpenAPI配置
        openapi_schema = app.openapi()
        print(f"✅ OpenAPI Schema generated: {len(openapi_schema.get('paths', {}))} endpoints")

        # 3. 验证应用元数据
        print(f"✅ API Title: {app.title}")
        print(f"✅ API Version: {app.version}")
        print(f"✅ Swagger UI Path: {app.docs_url}")
        print(f"✅ ReDoc Path: {app.redoc_url}")
        print(f"✅ OpenAPI URL: {app.openapi_url}")

        # 4. 检查云端API路径
        cloud_paths = [path for path in openapi_schema['paths'].keys() if '/cloud/' in path]
        print(f"✅ Cloud API endpoints found: {len(cloud_paths)}")
        for path in cloud_paths:
            methods = list(openapi_schema['paths'][path].keys())
            print(f"   - {path} [{', '.join(methods).upper()}]")

        # 5. 验证Pydantic模型
        components = openapi_schema.get('components', {})
        schemas = components.get('schemas', {})
        model_count = len([name for name in schemas.keys() if any(keyword in name for keyword in ['Request', 'Response', 'Error', 'Health', 'Info'])])
        print(f"✅ API Models defined: {model_count}")

        # 6. 检查路由器配置
        from swanboard.router.cloud import router
        print(f"✅ Cloud router configured with tags: {router.tags}")

        print("\n" + "=" * 60)
        print("🎉 Swagger UI Configuration Verified Successfully!")
        print("\n📖 API Documentation URLs (when server is running):")
        print("   - Swagger UI: http://localhost:5173/api/docs")
        print("   - ReDoc: http://localhost:5173/api/redoc")
        print("   - OpenAPI Schema: http://localhost:5173/api/v1/openapi.json")
        print("   - Cloud Health: http://localhost:5173/api/v1/cloud/health")
        print("   - Cloud Info: http://localhost:5173/api/v1/cloud/info")

        print("\n🚀 To start the server with Swagger UI:")
        print("   uvicorn swanboard.app:app --host 0.0.0.0 --port 5173")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    success = verify_swagger_config()
    sys.exit(0 if success else 1)