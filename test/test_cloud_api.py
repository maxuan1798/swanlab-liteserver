#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SwanLab云端API测试文件

测试EnhancedSwanBoardCallback与SwanLab-Dashboard的HTTP通信
"""

import os
import sys
import requests
import time
from typing import Dict, Any

# 添加swanboard到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 测试配置
API_BASE_URL = "http://localhost:5173/api/v1/cloud"
API_KEY = "test_api_key_12345"  # 测试用API密钥

# 设置环境变量
os.environ['SWANLAB_API_KEY'] = API_KEY
os.environ['SWANLAB_ALLOWED_WORKSPACES'] = 'test_workspace,default'


class CloudApiTester:
    """云端API测试器"""

    def __init__(self, base_url: str = API_BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def test_health_check(self) -> bool:
        """测试健康检查端点"""
        print("🔍 Testing health check...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def test_api_info(self) -> bool:
        """测试API信息端点"""
        print("📋 Testing API info...")
        try:
            response = self.session.get(f"{self.base_url}/info")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Info: {data.get('name')} v{data.get('version')}")
                return True
            else:
                print(f"❌ API info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API info error: {e}")
            return False

    def test_project_sync(self) -> Dict[str, Any]:
        """测试项目同步"""
        print("📁 Testing project sync...")

        project_data = {
            "name": "test_project_api",
            "workspace": "test_workspace",
            "description": "Test project created via API"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/projects",
                json=project_data
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    project_info = data.get('data', {})
                    project_id = project_info.get('id')
                    existed = project_info.get('existed', False)

                    status = "updated" if existed else "created"
                    print(f"✅ Project {status}: ID={project_id}, Name={project_info.get('name')}")

                    return project_info
                else:
                    print(f"❌ Project sync failed: {data.get('message')}")
                    return {}
            else:
                print(f"❌ Project sync HTTP error: {response.status_code}")
                print(f"Response: {response.text}")
                return {}

        except Exception as e:
            print(f"❌ Project sync error: {e}")
            return {}

    def test_experiment_sync(self, project_id: str) -> Dict[str, Any]:
        """测试实验同步"""
        print("🧪 Testing experiment sync...")

        experiment_data = {
            "run_id": f"test_run_{int(time.time())}",
            "name": "test_experiment_api",
            "description": "Test experiment created via API",
            "colors": ["#FF6B6B", "#4ECDC4"],
            "project_id": project_id,
            "workspace": "test_workspace"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/experiments",
                json=experiment_data
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    exp_info = data.get('data', {})
                    exp_id = exp_info.get('id')
                    existed = exp_info.get('existed', False)

                    status = "updated" if existed else "created"
                    print(f"✅ Experiment {status}: ID={exp_id}, Run ID={exp_info.get('run_id')}")

                    return exp_info
                else:
                    print(f"❌ Experiment sync failed: {data.get('message')}")
                    return {}
            else:
                print(f"❌ Experiment sync HTTP error: {response.status_code}")
                print(f"Response: {response.text}")
                return {}

        except Exception as e:
            print(f"❌ Experiment sync error: {e}")
            return {}

    def test_column_sync(self, experiment_id: str) -> bool:
        """测试列同步"""
        print("📊 Testing column sync...")

        column_data = {
            "key": "test_loss",
            "experiment_id": experiment_id,
            "chart_type": "line",
            "reference": "step",
            "section_name": "metrics",
            "section_sort": 0,
            "kid": "test_loss_folder"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/columns",
                json=column_data
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    column_info = data.get('data', {})
                    column_id = column_info.get('id')
                    print(f"✅ Column created: ID={column_id}, Key={column_info.get('key')}")
                    return True
                else:
                    print(f"❌ Column sync failed: {data.get('message')}")
                    return False
            else:
                print(f"❌ Column sync HTTP error: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Column sync error: {e}")
            return False

    def test_status_update(self, experiment_id: str) -> bool:
        """测试状态更新"""
        print("🔄 Testing status update...")

        status_data = {"status": 1}  # finished

        try:
            response = self.session.put(
                f"{self.base_url}/experiments/{experiment_id}/status",
                json=status_data
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status_info = data.get('data', {})
                    status_text = status_info.get('status_text')
                    print(f"✅ Status updated: {status_text}")
                    return True
                else:
                    print(f"❌ Status update failed: {data.get('message')}")
                    return False
            else:
                print(f"❌ Status update HTTP error: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Status update error: {e}")
            return False

    def test_query_apis(self, project_id: str) -> bool:
        """测试查询API"""
        print("🔍 Testing query APIs...")

        success = True

        # 测试工作空间项目列表
        try:
            response = self.session.get(f"{self.base_url}/workspaces/test_workspace/projects")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    projects = data.get('data', {}).get('projects', [])
                    print(f"✅ Workspace projects: {len(projects)} found")
                else:
                    print(f"❌ Workspace query failed: {data.get('message')}")
                    success = False
            else:
                print(f"❌ Workspace query HTTP error: {response.status_code}")
                success = False
        except Exception as e:
            print(f"❌ Workspace query error: {e}")
            success = False

        # 测试项目实验列表
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}/experiments")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    experiments = data.get('data', {}).get('experiments', [])
                    print(f"✅ Project experiments: {len(experiments)} found")
                else:
                    print(f"❌ Project query failed: {data.get('message')}")
                    success = False
            else:
                print(f"❌ Project query HTTP error: {response.status_code}")
                success = False
        except Exception as e:
            print(f"❌ Project query error: {e}")
            success = False

        return success

    def test_authentication(self) -> bool:
        """测试认证"""
        print("🔐 Testing authentication...")

        # 测试无认证的请求
        try:
            response = requests.post(f"{self.base_url}/projects", json={
                "name": "test_project",
                "workspace": "test_workspace"
            })

            if response.status_code == 401:
                print("✅ Authentication required (expected 401)")
            else:
                print(f"❌ Authentication test failed: expected 401, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            return False

        # 测试错误的API密钥
        try:
            bad_headers = {
                'Authorization': 'Bearer wrong_key',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                f"{self.base_url}/projects",
                json={"name": "test", "workspace": "test"},
                headers=bad_headers
            )

            if response.status_code == 401:
                print("✅ Bad API key rejected (expected 401)")
                return True
            else:
                print(f"❌ Bad key test failed: expected 401, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Bad key test error: {e}")
            return False

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 Starting SwanLab Cloud API Tests")
        print("=" * 50)

        all_passed = True

        # 基础测试
        if not self.test_health_check():
            all_passed = False

        if not self.test_api_info():
            all_passed = False

        if not self.test_authentication():
            all_passed = False

        # 功能测试
        project_info = self.test_project_sync()
        if not project_info:
            all_passed = False
            print("❌ Skipping remaining tests due to project sync failure")
            return all_passed

        project_id = project_info.get('id')

        experiment_info = self.test_experiment_sync(project_id)
        if not experiment_info:
            all_passed = False
            print("❌ Skipping remaining tests due to experiment sync failure")
            return all_passed

        experiment_id = experiment_info.get('id')

        if not self.test_column_sync(experiment_id):
            all_passed = False

        if not self.test_status_update(experiment_id):
            all_passed = False

        if not self.test_query_apis(project_id):
            all_passed = False

        # 测试结果
        print("=" * 50)
        if all_passed:
            print("🎉 All tests passed!")
        else:
            print("❌ Some tests failed!")

        return all_passed


def test_enhanced_callback_integration():
    """测试EnhancedSwanBoardCallback与API的集成"""
    print("\n🔗 Testing EnhancedSwanBoardCallback Integration")
    print("-" * 50)

    try:
        from swanboard.enhanced_callback import EnhancedSwanBoardCallback

        # 设置环境变量以使用HTTP API
        os.environ['SWANLAB_CLOUD_SYNC'] = 'true'
        os.environ['SWANLAB_API_HOST'] = API_BASE_URL
        os.environ['SWANLAB_API_KEY'] = API_KEY
        os.environ['SWANLAB_WORKSPACE'] = 'test_workspace'

        # 创建增强回调（使用HTTP模式）
        callback = EnhancedSwanBoardCallback(
            enable_cloud=True,
            cloud_config={
                'api_base': API_BASE_URL,
                'api_key': API_KEY,
                'workspace': 'test_workspace',
                'timeout': 30
            }
        )

        print("✅ EnhancedSwanBoardCallback created successfully")

        # 检查云端同步状态
        stats = callback.get_cloud_sync_stats()
        if stats.get('enabled'):
            print(f"✅ Cloud sync enabled: {stats.get('api_base')}")
        else:
            print(f"⚠️  Cloud sync disabled: {stats.get('reason')}")

        # 测试项目初始化
        callback.on_init("integration_test_project")
        print("✅ Project initialization completed")

        # 测试实验初始化
        callback.before_init_experiment(
            run_id=f"integration_run_{int(time.time())}",
            exp_name="integration_test_experiment",
            description="Integration test experiment",
            num=1,
            colors=("#9B59B6", "#E74C3C")
        )
        print("✅ Experiment initialization completed")

        # 测试实验结束
        callback.on_stop(error=None)
        print("✅ Experiment completion handled")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("SwanLab Cloud API Test Suite")
    print("============================")

    # 检查是否有SwanLab-Dashboard服务运行
    try:
        response = requests.get("http://localhost:5173/api/v1/cloud/health", timeout=5)
        if response.status_code != 200:
            print("⚠️  SwanLab-Dashboard服务未运行，请先启动服务")
            print("   命令: cd SwanLab-Server && python -m uvicorn swanboard.app:app --host 0.0.0.0 --port 5173")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  无法连接到SwanLab-Dashboard服务 (http://localhost:5173)")
        print("   请确保服务正在运行:")
        print("   cd SwanLab-Server && python -m uvicorn swanboard.app:app --host 0.0.0.0 --port 5173")
        return False
    except Exception as e:
        print(f"⚠️  服务检查失败: {e}")
        return False

    # 运行API测试
    tester = CloudApiTester()
    api_success = tester.run_all_tests()

    # 运行集成测试
    integration_success = test_enhanced_callback_integration()

    # 总结
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   API Tests: {'✅ PASSED' if api_success else '❌ FAILED'}")
    print(f"   Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")

    overall_success = api_success and integration_success
    print(f"\n   Overall Result: {'🎉 ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")

    return overall_success


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
