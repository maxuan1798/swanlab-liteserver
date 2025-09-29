#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwanLab-Dashboard Swagger UI Test Script
测试Swagger UI文档生成和API端点可用性
"""

import uvicorn
import asyncio
import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from swanboard.app import app

def test_swagger_endpoints():
    """测试Swagger相关端点"""
    base_url = "http://localhost:8001"

    # 等待服务启动
    time.sleep(3)

    print("🧪 Testing Swagger UI endpoints...")

    # 1. 测试OpenAPI JSON schema
    try:
        with urlopen(f"{base_url}/api/v1/openapi.json") as response:
            if response.status == 200:
                schema = json.loads(response.read())
                print(f"✅ OpenAPI Schema: {len(schema.get('paths', {}))} endpoints found")

                # 验证云端API路径
                cloud_paths = [path for path in schema['paths'].keys() if '/cloud/' in path]
                print(f"✅ Cloud API endpoints: {len(cloud_paths)} found")
                for path in cloud_paths:
                    print(f"   - {path}")
            else:
                print(f"❌ OpenAPI Schema failed: {response.status}")
    except Exception as e:
        print(f"❌ OpenAPI Schema error: {e}")

    # 2. 测试Swagger UI页面
    try:
        with urlopen(f"{base_url}/api/docs") as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                if "swagger-ui" in content.lower():
                    print("✅ Swagger UI page loaded successfully")
                else:
                    print("⚠️  Swagger UI page loaded but content unclear")
            else:
                print(f"❌ Swagger UI failed: {response.status}")
    except Exception as e:
        print(f"❌ Swagger UI error: {e}")

    # 3. 测试ReDoc页面
    try:
        with urlopen(f"{base_url}/api/redoc") as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                if "redoc" in content.lower():
                    print("✅ ReDoc page loaded successfully")
                else:
                    print("⚠️  ReDoc page loaded but content unclear")
            else:
                print(f"❌ ReDoc failed: {response.status}")
    except Exception as e:
        print(f"❌ ReDoc error: {e}")

    # 4. 测试云端API健康检查
    try:
        with urlopen(f"{base_url}/api/v1/cloud/health") as response:
            if response.status == 200:
                health = json.loads(response.read())
                print(f"✅ Cloud API Health: {health.get('status', 'unknown')}")
            else:
                print(f"❌ Cloud API Health failed: {response.status}")
    except Exception as e:
        print(f"❌ Cloud API Health error: {e}")

    # 5. 测试API信息端点
    try:
        with urlopen(f"{base_url}/api/v1/cloud/info") as response:
            if response.status == 200:
                info = json.loads(response.read())
                print(f"✅ Cloud API Info: {info.get('name', 'unknown')} v{info.get('version', 'unknown')}")
            else:
                print(f"❌ Cloud API Info failed: {response.status}")
    except Exception as e:
        print(f"❌ Cloud API Info error: {e}")

async def main():
    """主测试函数"""
    print("🚀 Starting SwanLab-Dashboard Swagger UI Test")
    print("=" * 60)

    # 启动FastAPI服务器
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8001,
        log_level="warning"  # 减少日志输出
    )
    server = uvicorn.Server(config)

    # 在后台启动服务器
    server_task = asyncio.create_task(server.serve())

    try:
        # 运行测试（在新线程中执行，避免阻塞服务器）
        test_thread = threading.Thread(target=test_swagger_endpoints)
        test_thread.start()
        test_thread.join()

        print("\n" + "=" * 60)
        print("📊 Swagger UI Test Results:")
        print("- Swagger UI: http://localhost:8001/api/docs")
        print("- ReDoc: http://localhost:8001/api/redoc")
        print("- OpenAPI Schema: http://localhost:8001/api/v1/openapi.json")
        print("- Cloud API Health: http://localhost:8001/api/v1/cloud/health")
        print("- Cloud API Info: http://localhost:8001/api/v1/cloud/info")

        print("\n🎉 Test completed! Check the URLs above to explore the API documentation.")
        print("Press Ctrl+C to stop the server...")

        # 保持服务器运行，让用户可以访问Swagger UI
        await server_task

    except KeyboardInterrupt:
        print("\n\n👋 Stopping server...")
        server.should_exit = True
        await server_task
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        server.should_exit = True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")