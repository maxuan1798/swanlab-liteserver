# SwanLab Cloud API 使用指南

本指南介绍如何使用SwanLab-Dashboard的云端API来支持EnhancedSwanBoardCallback的HTTP通信功能。

## 概述

SwanLab Cloud API提供了一套完整的HTTP接口，支持：
- 项目和实验的云端同步
- 指标和图表数据的云端存储
- 实验状态的实时更新
- 多工作空间和用户管理

## API架构

```
┌─────────────────────┐     HTTP API     ┌─────────────────────┐
│ EnhancedSwanBoard   │ ────────────────▶ │ SwanLab-Dashboard   │
│ Callback            │                   │ Cloud API           │
│ (enable_cloud=True) │ ◀──────────────── │ (/api/v1/cloud/*)   │
└─────────────────────┘                   └─────────────────────┘
                                                    │
                                                    ▼
                                          ┌─────────────────────┐
                                          │ Local SQLite        │
                                          │ Database            │
                                          └─────────────────────┘
```

## 快速开始

### 1. 启动SwanLab-Dashboard服务

```bash
cd SwanLab-Server
python -m uvicorn swanboard.app:app --host 0.0.0.0 --port 5173
```

### 2. 配置环境变量

```bash
# API认证密钥（可选，开发环境可以不设置）
export SWANLAB_API_KEY="your_secure_api_key"

# 允许的工作空间（可选，不设置表示允许所有）
export SWANLAB_ALLOWED_WORKSPACES="workspace1,workspace2,default"
```

### 3. 使用EnhancedSwanBoardCallback

```python
from swanboard.enhanced_callback import EnhancedSwanBoardCallback

# 启用云端HTTP同步
callback = EnhancedSwanBoardCallback(
    enable_cloud=True,
    cloud_config={
        'api_base': 'http://localhost:5173/api/v1/cloud',
        'api_key': 'your_api_key',  # 可选
        'workspace': 'my_workspace',
        'timeout': 30
    }
)

# SwanLab会自动使用这个回调进行云端同步
```

## API端点详情

### 基础端点

#### GET /api/v1/cloud/health
健康检查端点
```json
{
    "status": "healthy",
    "timestamp": "2024-11-26T16:50:00Z",
    "database": {
        "available": true,
        "path": "/path/to/swanlog"
    },
    "api_version": "v1"
}
```

#### GET /api/v1/cloud/info
获取API信息
```json
{
    "name": "SwanLab Cloud API",
    "version": "1.0.0",
    "description": "HTTP API for EnhancedSwanBoardCallback cloud sync",
    "endpoints": { ... },
    "authentication": { ... }
}
```

### 项目管理

#### POST /api/v1/cloud/projects
同步项目到云端

**请求头:**
```
Authorization: Bearer your_api_key
Content-Type: application/json
```

**请求体:**
```json
{
    "name": "my_project",
    "workspace": "my_workspace",
    "description": "Project description"
}
```

**响应:**
```json
{
    "success": true,
    "data": {
        "id": "1",
        "project_id": "1",
        "name": "my_project",
        "description": "Project description",
        "workspace": "my_workspace",
        "existed": false
    },
    "message": "Success",
    "time": 0.02
}
```

#### GET /api/v1/cloud/workspaces/{workspace}/projects
获取工作空间下的所有项目

**响应:**
```json
{
    "success": true,
    "data": {
        "workspace": "my_workspace",
        "projects": [
            {
                "id": "1",
                "name": "project1",
                "description": "Description",
                "experiment_count": 5,
                "created_at": "2024-11-26 16:30:00",
                "updated_at": "2024-11-26 16:45:00"
            }
        ],
        "total": 1
    }
}
```

### 实验管理

#### POST /api/v1/cloud/experiments
同步实验到云端

**请求体:**
```json
{
    "run_id": "run_20241126_001",
    "name": "my_experiment",
    "description": "Experiment description",
    "colors": ["#FF6B6B", "#4ECDC4"],
    "project_id": "1",
    "workspace": "my_workspace"
}
```

**响应:**
```json
{
    "success": true,
    "data": {
        "id": "1",
        "experiment_id": "1",
        "run_id": "run_20241126_001",
        "name": "my_experiment",
        "description": "Experiment description",
        "workspace": "my_workspace",
        "existed": false
    }
}
```

#### PUT /api/v1/cloud/experiments/{experiment_id}/status
更新实验状态

**请求体:**
```json
{
    "status": 1  // -1: crashed, 0: running, 1: finished
}
```

**响应:**
```json
{
    "success": true,
    "data": {
        "experiment_id": "1",
        "status": 1,
        "status_text": "finished",
        "updated_at": "2024-11-26 16:45:00"
    }
}
```

#### GET /api/v1/cloud/projects/{project_id}/experiments
获取项目下的所有实验

**响应:**
```json
{
    "success": true,
    "data": {
        "project_id": "1",
        "project_name": "my_project",
        "experiments": [
            {
                "id": "1",
                "name": "experiment1",
                "run_id": "run_001",
                "description": "Description",
                "status": 1,
                "light_color": "#FF6B6B",
                "dark_color": "#4ECDC4",
                "created_at": "2024-11-26 16:30:00",
                "updated_at": "2024-11-26 16:45:00",
                "finished_at": "2024-11-26 16:45:00"
            }
        ],
        "total": 1
    }
}
```

### 指标管理

#### POST /api/v1/cloud/columns
同步指标/列到云端

**请求体:**
```json
{
    "key": "loss",
    "experiment_id": "1",
    "chart_type": "line",
    "reference": "step",
    "section_name": "metrics",
    "section_sort": 0,
    "kid": "loss_folder",
    "error": {
        "data_class": "str",
        "expected": "float"
    }
}
```

**响应:**
```json
{
    "success": true,
    "data": {
        "id": "1",
        "column_id": "1",
        "key": "loss",
        "chart_type": "line",
        "experiment_id": "1"
    }
}
```

## 认证和安全

### API密钥认证

API使用Bearer Token认证：

```bash
curl -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"name":"test","workspace":"default"}' \
     http://localhost:5173/api/v1/cloud/projects
```

### 环境变量配置

```bash
# API密钥（如果未设置，开发模式下允许所有请求）
export SWANLAB_API_KEY="your_secure_api_key_here"

# 允许的工作空间（如果未设置，允许所有工作空间）
export SWANLAB_ALLOWED_WORKSPACES="prod,dev,test"
```

### 安全建议

1. **生产环境**: 务必设置`SWANLAB_API_KEY`
2. **工作空间限制**: 使用`SWANLAB_ALLOWED_WORKSPACES`限制访问
3. **HTTPS**: 生产环境使用HTTPS
4. **防火墙**: 限制API访问IP范围

## 错误处理

### 常见HTTP状态码

- `200`: 成功
- `400`: 请求参数错误
- `401`: 认证失败
- `404`: 资源不存在
- `409`: 冲突（如运行中的实验不能删除）
- `500`: 服务器内部错误

### 错误响应格式

```json
{
    "success": false,
    "message": "Error description",
    "code": 400,
    "time": 0.01
}
```

## 完整示例

### Python示例

```python
import requests
import json

class SwanLabCloudClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    def sync_project(self, name, workspace, description=""):
        """同步项目"""
        data = {
            "name": name,
            "workspace": workspace,
            "description": description
        }
        response = requests.post(
            f"{self.base_url}/projects",
            headers=self.headers,
            json=data
        )
        return response.json()

    def sync_experiment(self, project_id, run_id, name, **kwargs):
        """同步实验"""
        data = {
            "project_id": project_id,
            "run_id": run_id,
            "name": name,
            "workspace": kwargs.get("workspace", "default"),
            **kwargs
        }
        response = requests.post(
            f"{self.base_url}/experiments",
            headers=self.headers,
            json=data
        )
        return response.json()

# 使用示例
client = SwanLabCloudClient(
    base_url="http://localhost:5173/api/v1/cloud",
    api_key="your_api_key"
)

# 创建项目
project = client.sync_project(
    name="my_ml_project",
    workspace="research",
    description="Machine learning experiments"
)

print(f"Project ID: {project['data']['id']}")

# 创建实验
experiment = client.sync_experiment(
    project_id=project['data']['id'],
    run_id="run_001",
    name="baseline_model",
    description="Baseline model training",
    colors=["#3498DB", "#2ECC71"]
)

print(f"Experiment ID: {experiment['data']['id']}")
```

### curl示例

```bash
#!/bin/bash

API_BASE="http://localhost:5173/api/v1/cloud"
API_KEY="your_api_key"

# 创建项目
PROJECT_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "curl_project",
    "workspace": "test",
    "description": "Project created with curl"
  }' \
  "$API_BASE/projects")

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.data.id')
echo "Created project with ID: $PROJECT_ID"

# 创建实验
EXPERIMENT_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"run_id\": \"curl_run_$(date +%s)\",
    \"name\": \"curl_experiment\",
    \"description\": \"Experiment created with curl\",
    \"project_id\": \"$PROJECT_ID\",
    \"workspace\": \"test\",
    \"colors\": [\"#FF6B6B\", \"#4ECDC4\"]
  }" \
  "$API_BASE/experiments")

EXPERIMENT_ID=$(echo $EXPERIMENT_RESPONSE | jq -r '.data.id')
echo "Created experiment with ID: $EXPERIMENT_ID"

# 更新实验状态为完成
STATUS_RESPONSE=$(curl -s -X PUT \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": 1}' \
  "$API_BASE/experiments/$EXPERIMENT_ID/status")

echo "Updated experiment status: $(echo $STATUS_RESPONSE | jq -r '.data.status_text')"
```

## 测试和调试

### 运行测试

```bash
cd SwanLab-Server
python test/test_cloud_api.py
```

### 健康检查

```bash
curl http://localhost:5173/api/v1/cloud/health
```

### 查看API信息

```bash
curl http://localhost:5173/api/v1/cloud/info
```

### 调试日志

查看SwanLab-Dashboard服务日志获取详细的请求处理信息。

## 常见问题

### Q: API密钥验证失败？
A: 确保设置了正确的环境变量`SWANLAB_API_KEY`，或者在开发环境下不设置此变量。

### Q: 工作空间访问被拒绝？
A: 检查`SWANLAB_ALLOWED_WORKSPACES`环境变量，确保包含您使用的工作空间名称。

### Q: 数据库连接错误？
A: 确保SwanLab-Dashboard服务有权限访问数据存储目录，检查`get_swanlog_dir()`返回的路径。

### Q: 端口冲突？
A: 修改启动命令中的端口号，同时更新客户端的`api_base`配置。

### Q: 如何在生产环境部署？
A: 使用反向代理（如Nginx），配置HTTPS，设置环境变量，限制访问IP等。

## 版本信息

- API版本: v1.0.0
- 兼容SwanLab版本: 1.0+
- Python版本要求: 3.7+

## 更多资源

- [SwanLab官方文档](https://docs.swanlab.cn)
- [FastAPI文档](https://fastapi.tiangolo.com)
- [HTTP状态码参考](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
