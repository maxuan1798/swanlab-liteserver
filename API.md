# SwanLab-Dashboard API Documentation

本文档描述了 SwanLab-Dashboard 前后端交互的 REST API 接口协议。

## 目录

- [基础信息](#基础信息)
  - [通用响应结构](#通用响应结构)
  - [响应状态码](#响应状态码)
- [1. Project API](#1-project-api)
  - [1.1 获取项目信息](#11-获取项目信息)
  - [1.2 获取项目总结信息](#12-获取项目总结信息)
  - [1.3 修改项目信息](#13-修改项目信息)
  - [1.4 删除项目](#14-删除项目)
  - [1.5 获取多实验对比图表](#15-获取多实验对比图表)
- [2. Experiment API](#2-experiment-api)
  - [2.1 获取实验信息](#21-获取实验信息)
  - [2.2 获取 Tag 数据](#22-获取-tag-数据)
  - [2.3 获取实验状态](#23-获取实验状态)
  - [2.4 获取实验总结](#24-获取实验总结)
  - [2.5 获取实验日志](#25-获取实验日志)
  - [2.6 获取实验图表配置](#26-获取实验图表配置)
  - [2.7 修改实验信息](#27-修改实验信息)
  - [2.8 删除实验](#28-删除实验)
  - [2.9 停止实验](#29-停止实验)
  - [2.10 获取实验依赖](#210-获取实验依赖)
  - [2.11 修改实验可见性](#211-修改实验可见性)
  - [2.12 根据名称获取实验日志](#212-根据名称获取实验日志)
- [3. Chart API](#3-chart-api)
  - [3.1 修改图表状态](#31-修改图表状态)
- [4. Namespace API](#4-namespace-api)
  - [4.1 修改命名空间展开状态](#41-修改命名空间展开状态)
  - [4.2 分页查询命名空间列表](#42-分页查询命名空间列表)
  - [4.3 创建命名空间](#43-创建命名空间)
- [5. Media API](#5-media-api)
  - [5.1 获取媒体文件](#51-获取媒体文件)
- [6. 数据库结构](#6-数据库结构)
  - [6.1 Project 表（项目表）](#61-project-表项目表)
  - [6.2 Experiment 表（实验表）](#62-experiment-表实验表)
  - [6.3 Tag 表（指标标签表）](#63-tag-表指标标签表)
  - [6.4 Chart 表（图表表）](#64-chart-表图表表)
  - [6.5 Namespace 表（命名空间表）](#65-namespace-表命名空间表)
  - [6.6 Source 表（图表-标签关联表）](#66-source-表图表-标签关联表)
  - [6.7 Display 表（命名空间-图表关联表）](#67-display-表命名空间-图表关联表)
  - [6.8 数据库关系图](#68-数据库关系图)
  - [6.9 生成 Mock 数据的完整示例](#69-生成-mock-数据的完整示例)
- [7. 数据存储结构](#7-数据存储结构)
  - [7.1 文件系统结构](#71-文件系统结构)
  - [7.2 Tag 数据格式](#72-tag-数据格式)
  - [7.3 Summary 文件格式](#73-summary-文件格式)
- [8. 前端调用示例](#8-前端调用示例)
  - [8.1 获取项目实验列表](#81-获取项目实验列表)
  - [8.2 获取实验 Tag 数据](#82-获取实验-tag-数据)
  - [8.3 更新实验信息](#83-更新实验信息)
  - [8.4 修改图表状态](#84-修改图表状态)
  - [8.5 修改命名空间展开状态](#85-修改命名空间展开状态)
  - [8.6 获取媒体文件](#86-获取媒体文件)
- [9. 注意事项](#9-注意事项)

---

## 基础信息

- **Base URL**: `/api/v1`
- **响应格式**: JSON
- **字符编码**: UTF-8

## 通用响应结构

所有 API 响应都遵循以下 JSON 结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 响应状态码

| HTTP 状态码 | code | 说明 |
|-----------|------|------|
| 200 | 0 | 请求成功 |
| 404 | 3404 | 资源不存在 |
| 409 | 3409 | 操作冲突（如删除运行中的实验） |
| 422 | 3422 | 请求参数错误 |
| 500 | 3500 | 数据格式错误 |
| 500 | 3555 | 未知服务器错误 |

---

## 1. Project API

项目相关接口，用于管理项目和实验列表。

### 1.1 获取项目信息

获取项目基本信息及其下所有实验列表。

**接口地址**: `GET /api/v1/project`

**请求参数**: 无

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "SwanLab Project",
    "description": "项目描述",
    "logdir": "/path/to/swanlog",
    "colors": ["#1f77b4", "#ff7f0e", ...],
    "experiments": [
      {
        "id": 1,
        "experiment_id": 1,
        "name": "experiment-1",
        "run_id": "exp-abc123def456",
        "description": "实验描述",
        "status": 0,
        "num": 100,
        "colors": ["#1f77b4", "#aec7e8"],
        "create_time": "2024-01-01 12:00:00",
        "update_time": "2024-01-01 13:00:00",
        "finish_time": null,
        "show": 1,
        "pinned_opened": 1,
        "hidden_opened": 0,
        "config": {
          "learning_rate": 0.001,
          "batch_size": 32
        }
      }
    ]
  }
}
```

**字段说明**:

- `logdir`: swanlog 目录的绝对路径
- `colors`: 可用的颜色列表
- `experiments`: 实验列表
  - `status`: 实验状态，0-运行中，1-已完成，-1-失败/错误，2-已停止
  - `show`: 是否在多实验对比中显示，1-显示，0-隐藏（**重要**：前端依赖此字段进行图表过滤，默认应为 1）
  - `pinned_opened`: 置顶区域是否展开
  - `hidden_opened`: 隐藏区域是否展开
  - `config`: 实验配置（如果存在 config.yaml）

**注意事项**:
- `show` 字段必须存在且为整数（0 或 1），如果缺失，前端会默认设置为 1（可见）
- `experiment_id` 和 `id` 应该一致，用于前端引用

---

### 1.2 获取项目总结信息

获取项目下所有实验的最新指标值总结。

**接口地址**: `GET /api/v1/project/summaries`

**请求参数**: 无

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "tags": ["loss", "accuracy", "learning_rate"],
    "summaries": {
      "experiment-1": {
        "loss": 0.123,
        "accuracy": 0.95,
        "learning_rate": 0.001
      },
      "experiment-2": {
        "loss": 0.089,
        "accuracy": 0.97,
        "learning_rate": 0.001
      }
    }
  }
}
```

**字段说明**:

- `tags`: 所有唯一的 tag 名称列表（按创建顺序）
- `summaries`: 以实验名称为键的字典，值为该实验各 tag 的最新值

---

### 1.3 修改项目信息

更新项目的名称和描述。

**接口地址**: `PATCH /api/v1/project/update`

**请求参数**:

```json
{
  "name": "新项目名称",
  "description": "新的项目描述"
}
```

**查询参数**:

- `project_id` (可选): 项目 ID，默认为默认项目

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "updates": {
      "name": "新项目名称",
      "description": "新的项目描述"
    }
  }
}
```

---

### 1.4 删除项目

删除项目及其下所有实验（包括文件系统和数据库记录）。

**接口地址**: `DELETE /api/v1/project`

**请求参数**: 无

**查询参数**:

- `project_id` (可选): 项目 ID，默认为默认项目

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

**错误响应**:

```json
{
  "code": 3409,
  "message": "Can't delete project since there is experiment running"
}
```

---

### 1.5 获取多实验对比图表

获取项目级别的多实验对比图表数据。

**接口地址**: `GET /api/v1/project/{project_id}/charts`

**路径参数**:

- `project_id`: 项目 ID

**请求参数**: 无

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "charts": [
      {
        "id": 10,
        "experiment": 5,
        "key": "epoch",
        "chart_type": "line",
        "reference": "step",
        "config": "{}",
        "error": {},
        "source": ["horse-8"],
        "multi": true,
        "source_map": {
          "horse-8": 5
        },
        "created_at": "2025-10-30T08:47:36",
        "updated_at": "2025-10-30T08:47:36"
      }
    ],
    "namespaces": [
      {
        "id": 1,
        "name": "default",
        "charts": [10, 9, 12, 11],
        "sort": 0,
        "opened": 1,
        "experiment_id": null,
        "project_id": 2
      }
    ]
  }
}
```

**字段说明**:

- `charts`: 图表列表
  - `id`: 图表唯一 ID
  - `experiment`: 关联的实验 ID（整数）
  - `key`: 图表关键字（指标名称，如 "loss"、"epoch"）
  - `chart_type`: 图表类型（"line"、"default"、"image"、"audio" 等）
  - `reference`: 参考轴，通常为 "step" 或 "time"
  - `error`: 错误信息对象，键为实验名称，值为错误详情
  - `source`: **数据源数组**，包含实验名称列表（如 `["horse-8", "ox-3"]`）
  - `multi`: 布尔值，是否为多实验对比图表
  - `source_map`: 实验名称到实验 ID 的映射（如 `{"horse-8": 5}`）
  - `config`: 图表配置（JSON 字符串）
- `namespaces`: 命名空间（图表分组）
  - `id`: 命名空间 ID（正整数为普通命名空间）
  - `name`: 命名空间名称（如 "default"）
  - `charts`: 该命名空间下的图表 ID 列表（**整数数组**，如 `[10, 9, 12, 11]`）
  - `sort`: 排序顺序
  - `opened`: 是否展开，1-展开，0-折叠
  - `experiment_id`: 关联的实验 ID（实验级命名空间时有值，项目级为 null）
  - `project_id`: 关联的项目 ID（项目级命名空间时有值，实验级为 null）

**重要说明**:

1. **`source` 字段格式变化**：
   - ✅ 新格式（当前实现）：`"source": ["horse-8", "ox-3"]` （实验名称数组）
   - ❌ 旧格式（文档示例）：`"sources": [{"id": 1, "tag": {...}}]` （对象数组）
   - 前端通过 `chart.source` 数组中的实验名称在 `projectStore.showMap` 中查找可见性

2. **字段名兼容性**：
   - `key` vs `name`：后端返回 `key`，前端会规范化为 `name`
   - `chart_type` vs `type`：后端返回 `chart_type`，前端会规范化为 `type`

3. **namespace.charts 数据类型**：
   - 必须是整数数组 `[10, 9, 12, 11]`，不是对象数组
   - 前端通过 `charts.value.find(c => c.id === chart_id)` 查找对应的 chart 对象

---

## 2. Experiment API

实验相关接口，用于管理单个实验的详细信息。

### 2.1 获取实验信息

获取指定实验的详细信息。

**接口地址**: `GET /api/v1/experiment/{experiment_id}`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "experiment-1",
    "run_id": "exp-abc123def456",
    "description": "实验描述",
    "status": 0,
    "num": 100,
    "colors": ["#1f77b4", "#aec7e8"],
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 13:00:00",
    "finish_time": null,
    "show": 1,
    "pinned_opened": 1,
    "hidden_opened": 0,
    "config": {
      "learning_rate": 0.001,
      "batch_size": 32
    },
    "system": {
      "python_version": "3.9.0",
      "platform": "Linux",
      "hostname": "server-01"
    }
  }
}
```

**字段说明**:

- `config`: 实验配置（来自 config.yaml）
- `system`: 系统元信息（来自 swanlab-metadata.json）

---

### 2.2 获取 Tag 数据

获取指定实验的某个 tag 的时序数据。

**接口地址**: `GET /api/v1/experiment/{experiment_id}/tag/{tag}`

**路径参数**:

- `experiment_id`: 实验 ID
- `tag`: Tag 名称（需要 URL 编码，支持 `/` 等特殊字符）

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "sum": 1000,
    "max": 1.234,
    "min": 0.001,
    "experiment_id": 1,
    "list": [
      {
        "index": 0,
        "data": 0.5,
        "create_time": 1704096000.123
      },
      {
        "index": 1,
        "data": 0.45,
        "create_time": 1704096001.456
      },
      {
        "index": 999,
        "data": 0.001,
        "_last": true,
        "create_time": 1704096999.789
      }
    ]
  }
}
```

**字段说明**:

- `sum`: 数据点总数
- `max`: 最大值
- `min`: 最小值
- `list`: 数据点列表（可能经过降采样处理）
  - `index`: 步数/索引
  - `data`: 数据值
  - `create_time`: 创建时间戳
  - `_last`: 仅最后一个数据点包含此字段，值为 true

---

### 2.3 获取实验状态

获取实验的实时状态和图表配置（用于轮询更新）。

**接口地址**: `GET /api/v1/experiment/{experiment_id}/status`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": 0,
    "update_time": "2024-01-01 13:30:00",
    "finish_time": null,
    "charts": {
      "charts": [
        {
          "id": 1,
          "name": "loss",
          "type": "default",
          "reference": "step",
          "status": 0,
          "error": null
        }
      ],
      "namespaces": [
        {
          "id": 1,
          "name": "default",
          "sort": 0,
          "opened": 1,
          "charts": [1]
        }
      ]
    }
  }
}
```

---

### 2.4 获取实验总结

获取实验下所有 tag 的最新值。

**接口地址**: `GET /api/v1/experiment/{experiment_id}/summary`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "summaries": [
      {
        "key": "loss",
        "value": 0.123
      },
      {
        "key": "accuracy",
        "value": 0.95
      }
    ]
  }
}
```

**字段说明**:

- `summaries`: 按 tag 排序（创建顺序）的最新值列表

---

### 2.5 获取实验日志

获取实验的控制台输出日志。

**接口地址**: `GET /api/v1/experiment/{experiment_id}/recent_log`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "recent": ["2024-01-01", "2024-01-01"],
    "logs": [
      "2024-01-01 12:00:00 Training started...",
      "2024-01-01 12:00:01 Epoch 1/10",
      "2024-01-01 12:00:02 Loss: 0.5"
    ],
    "error": [
      "Traceback (most recent call last):",
      "  File \"train.py\", line 10, in <module>",
      "    raise ValueError(\"error message\")"
    ]
  }
}
```

**字段说明**:

- `recent`: 日志时间范围 [开始日期, 结束日期]
- `logs`: 日志内容列表（每行一个元素）
- `error`: 错误日志（如果存在 error.log 文件）

---

### 2.6 获取实验图表配置

获取实验的所有图表和命名空间配置。

**接口地址**: `GET /api/v1/experiment/{experiment_id}/chart`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "charts": [
      {
        "id": 1,
        "name": "loss",
        "type": "default",
        "reference": "step",
        "status": 0,
        "error": null,
        "sources": [
          {
            "id": 1,
            "tag_id": 1,
            "chart_id": 1
          }
        ]
      }
    ],
    "namespaces": [
      {
        "id": -1,
        "name": "pinned",
        "sort": -1,
        "opened": 1,
        "charts": []
      },
      {
        "id": 1,
        "name": "default",
        "sort": 0,
        "opened": 1,
        "charts": [1]
      }
    ]
  }
}
```

---

### 2.7 修改实验信息

更新实验的名称和描述。

**接口地址**: `PATCH /api/v1/experiment/{experiment_id}`

**路径参数**:

- `experiment_id`: 实验 ID

**请求参数**:

```json
{
  "name": "新实验名称",
  "description": "新的实验描述"
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "name": "新实验名称",
    "description": "新的实验描述"
  }
}
```

---

### 2.8 删除实验

删除指定实验（包括文件系统和数据库记录）。

**接口地址**: `DELETE /api/v1/experiment/{experiment_id}`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "experiment_id": 1
  }
}
```

**注意**: 不能删除正在运行的实验（status = 0）。

---

### 2.9 停止实验

停止正在运行的实验。

**接口地址**: `GET /api/v1/experiment/{experiment_id}/stop`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "status": 2,
    "finish_time": "2024-01-01 13:00:00"
  }
}
```

---

### 2.10 获取实验依赖

获取实验的 Python 依赖列表（requirements.txt）。

**接口地址**: `GET /api/v1/experiment/{experiment_id}/requirements`

**路径参数**:

- `experiment_id`: 实验 ID

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "requirements": [
      "torch==1.9.0",
      "numpy==1.21.0",
      "pandas==1.3.0",
      ""
    ]
  }
}
```

**字段说明**:

- `requirements`: 依赖列表，每行一个依赖项

---

### 2.11 修改实验可见性

设置实验在多实验对比图表中的可见性。

**接口地址**: `PATCH /api/v1/experiment/{experiment_id}/show`

**路径参数**:

- `experiment_id`: 实验 ID

**请求参数**:

```json
{
  "show": true
}
```

**字段说明**:

- `show`: true-显示，false-隐藏

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "experiment": {
      "id": 1,
      "name": "experiment-1",
      "show": 1
    }
  }
}
```

---

### 2.12 根据名称获取实验日志

根据项目名称和实验名称获取实验日志（支持跨工作空间查询）。

**接口地址**: `GET /api/v1/experiment/by-name/logs`

**查询参数**:

- `project_name` (必填): 项目名称
- `experiment_name` (必填): 实验名称
- `workspace` (可选): 工作空间名称，默认为 None

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "recent": ["2024-01-01", "2024-01-01"],
    "logs": [
      "2024-01-01 12:00:00 Training started...",
      "2024-01-01 12:00:01 Epoch 1/10",
      "2024-01-01 12:00:02 Loss: 0.5"
    ],
    "error": []
  }
}
```

**字段说明**:

- `recent`: 日志时间范围 [开始日期, 结束日期]
- `logs`: 日志内容列表（每行一个元素）
- `error`: 错误日志（如果存在 error.log 文件）

**使用场景**:

此接口用于通过项目名和实验名直接获取日志，无需先查询实验 ID，适用于：
- 外部平台集成（如通过 API Key 访问）
- 命令行工具快速查询日志
- 多工作空间环境下的日志检索

---

## 3. Chart API

图表相关接口，用于管理图表的显示状态。

### 3.1 修改图表状态

修改图表的置顶/隐藏状态。

**接口地址**: `PATCH /api/v1/chart/{chart_id}/status`

**路径参数**:

- `chart_id`: 图表 ID

**请求参数**:

```json
{
  "status": 1
}
```

**字段说明**:

- `status`: 1-置顶，0-正常，-1-隐藏

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "groups": [
      {
        "id": -1,
        "name": "pinned",
        "sort": -1,
        "opened": 1,
        "charts": [
          {
            "id": 1,
            "name": "loss",
            "type": "default",
            "status": 1
          }
        ]
      },
      {
        "id": 1,
        "name": "default",
        "sort": 0,
        "opened": 1,
        "charts": []
      }
    ]
  }
}
```

**字段说明**:

- `groups`: 更新后的命名空间列表（包含完整的图表对象）

---

## 4. Namespace API

命名空间相关接口，用于管理图表分组的展开/折叠状态。

### 4.1 修改命名空间展开状态

修改命名空间的展开/折叠状态。

**接口地址**: `PATCH /api/v1/namespace/{namespace_id}/opened`

**路径参数**:

- `namespace_id`: 命名空间 ID（-1 表示 pinned，-2 表示 hidden）

**请求参数**:

```json
{
  "opened": true,
  "experiment_id": 1,
  "project_id": null
}
```

**字段说明**:

- `opened`: true-展开，false-折叠
- `experiment_id`: 实验 ID（实验级别命名空间时需要）
- `project_id`: 项目 ID（项目级别命名空间时需要）

**注意**: `experiment_id` 和 `project_id` 至少提供一个。

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

### 4.2 分页查询命名空间列表

分页查询命名空间列表，支持关键词搜索。

**接口地址**: `GET /api/v1/namespace/`

**查询参数**:

- `page` (可选): 页码，从 1 开始，默认为 1
- `size` (可选): 每页大小，最大 100，默认为 20
- `keyword` (可选): 搜索关键词，用于模糊匹配 namespace 名称

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 50,
    "page": 1,
    "size": 20,
    "items": [
      {
        "id": 1,
        "name": "default",
        "description": "Default namespace",
        "sort": 0,
        "opened": 1,
        "create_time": "2024-01-01 12:00:00",
        "update_time": "2024-01-01 12:00:00"
      },
      {
        "id": 2,
        "name": "training",
        "description": "Training metrics",
        "sort": 1,
        "opened": 1,
        "create_time": "2024-01-01 12:30:00",
        "update_time": "2024-01-01 12:30:00"
      }
    ]
  }
}
```

**字段说明**:

- `total`: 总记录数
- `page`: 当前页码
- `size`: 每页大小
- `items`: namespace 列表

---

### 4.3 创建命名空间

创建新的命名空间。

**接口地址**: `POST /api/v1/namespace/`

**请求参数**:

```json
{
  "name": "validation",
  "sort_order": 2
}
```

**字段说明**:

- `name` (必填): namespace 名称
- `sort_order` (可选): 排序顺序，数字越小越靠前

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 3,
    "name": "validation",
    "description": null,
    "sort": 2,
    "opened": 1,
    "create_time": "2024-01-01 13:00:00",
    "update_time": "2024-01-01 13:00:00"
  }
}
```

**错误响应**:

```json
{
  "code": 3422,
  "message": "Request parameter 'name' is required"
}
```

---

## 5. Media API

媒体文件相关接口，用于获取实验生成的媒体文件（图片、音频等）。

### 5.1 获取媒体文件

获取指定的媒体文件（返回二进制数据，而非 JSON）。

**接口地址**: `GET /api/v1/media/{path}`

**路径参数**:

- `path`: 媒体文件的相对路径（如 `image_001.png`）

**查询参数**:

- `tag`: Tag 名称（需要 URL 编码）
- `experiment_id`: 实验 ID

**请求示例**:

```
GET /api/v1/media/image_001.png?tag=loss%2Fvalidation&experiment_id=1
```

**响应**:

- Content-Type: 根据文件类型自动设置（如 image/png, audio/wav）
- Body: 二进制文件内容

**错误响应**:

如果文件不存在或其他错误，返回 JSON 格式的错误信息：

```json
{
  "code": 3404,
  "message": "File not found"
}
```

**前端使用示例**:

```javascript
// 获取媒体文件为 Blob 对象
const blob = await http.get('/media/' + fileName, {
  params: { tag: tagName, experiment_id: expId },
  responseType: 'blob'
})

// 创建预览 URL
const url = URL.createObjectURL(blob)
```

---

## 6. 数据库结构

数据库使用 SQLite，采用 Peewee ORM。以下是所有数据表的详细结构。

### 6.1 Project 表（项目表）

存储项目基本信息。通常一个工程中只有一个项目（DEFAULT_PROJECT_ID = 1）。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|------|--------|------|
| id | INTEGER | PRIMARY KEY | 自增 | 项目ID |
| name | VARCHAR(100) | NOT NULL, UNIQUE | - | 项目名称，唯一 |
| description | VARCHAR(255) | NULL | NULL | 项目描述 |
| sum | INTEGER | NULL | NULL | 项目下实验数量（包括已删除），只增不减 |
| charts | INTEGER | NOT NULL | 0 | 是否已生成项目级别图表（0-未生成，1-已生成） |
| pinned_opened | INTEGER | NOT NULL | 1 | 多实验图表置顶部分是否展开（0-关闭，1-展开） |
| hidden_opened | INTEGER | NOT NULL | 0 | 多实验图表隐藏部分是否展开（0-关闭，1-展开） |
| more | VARCHAR | NULL | NULL | 更多信息配置（JSON 字符串） |
| version | VARCHAR(30) | NOT NULL | - | 创建时的版本号 |
| create_time | VARCHAR(30) | NOT NULL | auto | 创建时间 |
| update_time | VARCHAR(30) | NOT NULL | auto | 更新时间 |

**Mock 数据示例**:

```python
{
    "id": 1,
    "name": "SwanLab Project",
    "description": "My ML Project",
    "sum": 5,
    "charts": 1,
    "pinned_opened": 1,
    "hidden_opened": 0,
    "more": null,
    "version": "0.1.9",
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 15:30:00"
}
```

---

### 6.2 Experiment 表（实验表）

存储实验信息。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|------|--------|------|
| id | INTEGER | PRIMARY KEY | 自增 | 实验ID |
| project_id | INTEGER | FOREIGN KEY, NOT NULL | 1 | 关联的项目ID（外键 → Project.id） |
| run_id | TEXT | UNIQUE, NOT NULL | - | 运行时ID，用于文件夹名称 |
| name | VARCHAR(100) | NOT NULL | - | 实验名称 |
| description | VARCHAR(255) | NULL | NULL | 实验描述 |
| sort | INTEGER | NOT NULL, >= 0 | auto | 实验排序索引（越小越靠前） |
| status | INTEGER | NOT NULL | 0 | 实验状态（-1:失败, 0:运行中, 1:完成, 2:停止） |
| show | INTEGER | NOT NULL | 1 | 多实验对比中是否显示（0-隐藏，1-显示） |
| light | VARCHAR(20) | NULL | NULL | 亮色主题颜色 |
| dark | VARCHAR(20) | NULL | NULL | 暗色主题颜色 |
| pinned_opened | INTEGER | NOT NULL | 1 | 实验图表置顶部分是否展开 |
| hidden_opened | INTEGER | NOT NULL | 0 | 实验图表隐藏部分是否展开 |
| more | TEXT | NULL | NULL | 更多信息配置（JSON 字符串） |
| version | VARCHAR(30) | NOT NULL | - | 创建时的版本号 |
| create_time | VARCHAR(30) | NOT NULL | auto | 创建时间 |
| finish_time | VARCHAR(30) | NULL | NULL | 完成时间 |
| update_time | VARCHAR(30) | NOT NULL | auto | 更新时间 |

**唯一性约束**:
- `(name, project_id)` 组合唯一
- `(sort, project_id)` 组合唯一

**Mock 数据示例**:

```python
{
    "id": 1,
    "project_id": 1,
    "run_id": "exp-abc123def456",
    "name": "experiment-1",
    "description": "First training run",
    "sort": 0,
    "status": 1,
    "show": 1,
    "light": "#1f77b4",
    "dark": "#aec7e8",
    "pinned_opened": 1,
    "hidden_opened": 0,
    "more": null,
    "version": "0.1.9",
    "create_time": "2024-01-01 12:00:00",
    "finish_time": "2024-01-01 15:00:00",
    "update_time": "2024-01-01 15:00:00"
}
```

---

### 6.3 Tag 表（指标标签表）

存储实验的指标数据（如 loss、accuracy 等）。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|------|--------|------|
| id | INTEGER | PRIMARY KEY | 自增 | Tag ID |
| experiment_id | INTEGER | FOREIGN KEY, NOT NULL | - | 关联的实验ID（外键 → Experiment.id） |
| name | VARCHAR(255) | NOT NULL | - | Tag 名称 |
| folder | VARCHAR(255) | NULL | NULL | Tag 存储目录名（通常为 sort 值） |
| type | VARCHAR(10) | NOT NULL | - | Tag 类型（如 default、image、audio） |
| description | VARCHAR(100) | NULL | NULL | Tag 描述 |
| system | INTEGER | NOT NULL | 0 | 是否由系统生成（0-用户，1-系统） |
| sort | INTEGER | NOT NULL | 0 | Tag 在实验中的排序（越小越靠前） |
| more | TEXT | NULL | NULL | 更多信息配置（JSON 字符串） |
| create_time | VARCHAR(30) | NOT NULL | auto | 创建时间 |
| update_time | VARCHAR(30) | NOT NULL | auto | 更新时间 |

**唯一性约束**:
- `(name, experiment_id)` 组合唯一

**Mock 数据示例**:

```python
{
    "id": 1,
    "experiment_id": 1,
    "name": "loss",
    "folder": "0",
    "type": "default",
    "description": "Training loss",
    "system": 0,
    "sort": 0,
    "more": null,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 15:00:00"
}
```

---

### 6.4 Chart 表（图表表）

存储图表配置信息。一个 Chart 可以属于实验级别或项目级别。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|------|--------|------|
| id | INTEGER | PRIMARY KEY | 自增 | 图表ID |
| experiment_id | INTEGER | FOREIGN KEY, NULL | NULL | 关联的实验ID（外键 → Experiment.id） |
| project_id | INTEGER | FOREIGN KEY, NULL | 1 | 关联的项目ID（外键 → Project.id） |
| name | VARCHAR(100) | NOT NULL | - | 图表名称 |
| description | VARCHAR(255) | NULL | NULL | 图表描述 |
| system | INTEGER | NOT NULL | 1 | 是否为系统图表（-1:已删除, 0:用户, 1:系统） |
| type | VARCHAR(10) | NOT NULL | - | 图表类型（如 default、line、bar） |
| reference | VARCHAR(10) | NOT NULL | "step" | 参考轴（step 或 time） |
| status | INTEGER | NOT NULL | 0 | 图表状态（-1:隐藏, 0:正常, 1:置顶） |
| sort | INTEGER | NULL | NULL | 置顶/隐藏时的排序索引 |
| config | TEXT | NULL | NULL | 图表其他配置（JSON 字符串） |
| more | TEXT | NULL | NULL | 更多信息配置（JSON 字符串） |
| create_time | VARCHAR(30) | NOT NULL | auto | 创建时间 |
| update_time | VARCHAR(30) | NOT NULL | auto | 更新时间 |

**约束条件**:
- `experiment_id` 和 `project_id` 有且仅有一个为 NULL
- `(name, experiment_id)` 组合唯一
- `(name, project_id)` 组合唯一

**Mock 数据示例**:

```python
# 实验级别图表
{
    "id": 1,
    "experiment_id": 1,
    "project_id": null,
    "name": "loss",
    "description": "Loss curve",
    "system": 1,
    "type": "default",
    "reference": "step",
    "status": 0,
    "sort": null,
    "config": null,
    "more": null,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 15:00:00"
}

# 项目级别图表（多实验对比）
{
    "id": 2,
    "experiment_id": null,
    "project_id": 1,
    "name": "loss",
    "description": "Multi-experiment loss comparison",
    "system": 1,
    "type": "default",
    "reference": "step",
    "status": 0,
    "sort": null,
    "config": null,
    "more": null,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 15:00:00"
}
```

---

### 6.5 Namespace 表（命名空间表）

存储图表分组信息。一个 Namespace 可以属于实验级别或项目级别。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|------|--------|------|
| id | INTEGER | PRIMARY KEY | 自增 | 命名空间ID |
| experiment_id | INTEGER | FOREIGN KEY, NULL | NULL | 关联的实验ID（外键 → Experiment.id） |
| project_id | INTEGER | FOREIGN KEY, NULL | NULL | 关联的项目ID（外键 → Project.id） |
| name | VARCHAR(100) | NOT NULL | - | 命名空间名称 |
| description | VARCHAR(255) | NULL | NULL | 命名空间描述 |
| sort | INTEGER | NOT NULL, >= 0 | auto | 排序索引（越小越靠前） |
| opened | INTEGER | NOT NULL | 1 | 是否展开（0-折叠，1-展开） |
| more | TEXT | NULL | NULL | 更多信息配置（JSON 字符串） |
| create_time | VARCHAR(30) | NOT NULL | auto | 创建时间 |
| update_time | VARCHAR(30) | NOT NULL | auto | 更新时间 |

**约束条件**:
- `experiment_id` 和 `project_id` 有且仅有一个为 NULL
- `(name, experiment_id)` 组合唯一
- `(name, project_id)` 组合唯一

**Mock 数据示例**:

```python
{
    "id": 1,
    "experiment_id": 1,
    "project_id": null,
    "name": "default",
    "description": "Default namespace",
    "sort": 0,
    "opened": 1,
    "more": null,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 15:00:00"
}
```

---

### 6.6 Source 表（图表-标签关联表）

多对多关系表，关联 Chart 和 Tag。一个 Chart 可以包含多个 Tag 的数据。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|------|--------|------|
| id | INTEGER | PRIMARY KEY | 自增 | 关联ID |
| tag_id | INTEGER | FOREIGN KEY, NOT NULL | - | 关联的 Tag ID（外键 → Tag.id） |
| chart_id | INTEGER | FOREIGN KEY, NOT NULL | - | 关联的 Chart ID（外键 → Chart.id） |
| sort | INTEGER | NOT NULL | 0 | Tag 在 Chart 中的排序 |
| error | TEXT | NULL | NULL | 数据转换错误信息（JSON 字符串） |
| more | TEXT | NULL | NULL | 更多信息配置（JSON 字符串） |
| create_time | VARCHAR(30) | NOT NULL | auto | 创建时间 |
| update_time | VARCHAR(30) | NOT NULL | auto | 更新时间 |

**唯一性约束**:
- `(tag_id, chart_id)` 组合唯一

**Mock 数据示例**:

```python
{
    "id": 1,
    "tag_id": 1,
    "chart_id": 1,
    "sort": 0,
    "error": null,
    "more": null,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 15:00:00"
}
```

---

### 6.7 Display 表（命名空间-图表关联表）

多对多关系表，关联 Namespace 和 Chart。定义图表在命名空间中的展示顺序。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|-----|------|------|--------|------|
| id | INTEGER | PRIMARY KEY | 自增 | 关联ID |
| chart_id | INTEGER | FOREIGN KEY, NOT NULL | - | 关联的 Chart ID（外键 → Chart.id） |
| namespace_id | INTEGER | FOREIGN KEY, NOT NULL | - | 关联的 Namespace ID（外键 → Namespace.id） |
| sort | INTEGER | NOT NULL, >= 0 | auto | Chart 在 Namespace 中的排序 |
| more | TEXT | NULL | NULL | 更多信息配置（JSON 字符串） |
| create_time | VARCHAR(30) | NOT NULL | auto | 创建时间 |
| update_time | VARCHAR(30) | NOT NULL | auto | 更新时间 |

**唯一性约束**:
- `(chart_id, namespace_id)` 组合唯一

**Mock 数据示例**:

```python
{
    "id": 1,
    "chart_id": 1,
    "namespace_id": 1,
    "sort": 0,
    "more": null,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 15:00:00"
}
```

---

### 6.8 数据库关系图

```
Project (1) ──< Experiment (N)
  │                │
  │                ├──< Tag (N)
  │                │     │
  │                │     └──< Source (N) ──> Chart (N)
  │                │                            │
  │                └──< Chart (N) ─────────────┤
  │                      │                      │
  └──< Chart (N) ────────┘                      │
        │                                       │
        └──< Display (N) ──> Namespace (N) ────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
             Experiment (1)              Project (1)
```

**关系说明**:

1. **Project → Experiment**: 一对多，一个项目包含多个实验
2. **Experiment → Tag**: 一对多，一个实验包含多个指标标签
3. **Experiment → Chart**: 一对多，一个实验包含多个图表
4. **Project → Chart**: 一对多，一个项目包含多个多实验对比图表
5. **Tag ↔ Chart**: 多对多（通过 Source 表），一个图表可以展示多个标签的数据
6. **Chart ↔ Namespace**: 多对多（通过 Display 表），一个命名空间可以包含多个图表
7. **Experiment → Namespace**: 一对多，一个实验可以有多个命名空间
8. **Project → Namespace**: 一对多，一个项目可以有多个命名空间

---

### 6.9 生成 Mock 数据的完整示例

以下是一个完整的 mock 数据生成示例，展示了如何创建关联的数据：

```python
# 1. 创建项目
project = {
    "id": 1,
    "name": "SwanLab Project",
    "description": "Test Project",
    "sum": 1,
    "charts": 0,
    "pinned_opened": 1,
    "hidden_opened": 0,
    "more": None,
    "version": "0.1.9",
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 12:00:00"
}

# 2. 创建实验
experiment = {
    "id": 1,
    "project_id": 1,
    "run_id": "exp-abc123",
    "name": "experiment-1",
    "description": "First experiment",
    "sort": 0,
    "status": 0,  # 运行中
    "show": 1,
    "light": "#1f77b4",
    "dark": "#aec7e8",
    "pinned_opened": 1,
    "hidden_opened": 0,
    "more": None,
    "version": "0.1.9",
    "create_time": "2024-01-01 12:00:00",
    "finish_time": None,
    "update_time": "2024-01-01 12:00:00"
}

# 3. 创建 Tag
tag = {
    "id": 1,
    "experiment_id": 1,
    "name": "loss",
    "folder": "0",
    "type": "default",
    "description": "Training loss",
    "system": 0,
    "sort": 0,
    "more": None,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 12:00:00"
}

# 4. 创建 Chart
chart = {
    "id": 1,
    "experiment_id": 1,
    "project_id": None,
    "name": "loss",
    "description": None,
    "system": 1,
    "type": "default",
    "reference": "step",
    "status": 0,
    "sort": None,
    "config": None,
    "more": None,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 12:00:00"
}

# 5. 创建 Namespace
namespace = {
    "id": 1,
    "experiment_id": 1,
    "project_id": None,
    "name": "default",
    "description": None,
    "sort": 0,
    "opened": 1,
    "more": None,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 12:00:00"
}

# 6. 创建 Source（关联 Tag 和 Chart）
source = {
    "id": 1,
    "tag_id": 1,
    "chart_id": 1,
    "sort": 0,
    "error": None,
    "more": None,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 12:00:00"
}

# 7. 创建 Display（关联 Chart 和 Namespace）
display = {
    "id": 1,
    "chart_id": 1,
    "namespace_id": 1,
    "sort": 0,
    "more": None,
    "create_time": "2024-01-01 12:00:00",
    "update_time": "2024-01-01 12:00:00"
}
```

---

## 7. 数据存储结构

### 7.1 文件系统结构

```
swanlog/
├── runs.swanlab                    # SQLite 数据库
├── {run_id}/                       # 实验目录
│   ├── logs/                       # Tag 数据目录
│   │   ├── {tag_folder}/          # Tag 文件夹（按 sort 字段命名）
│   │   │   ├── 0001.log           # 数据文件（JSONL 格式）
│   │   │   ├── 0002.log
│   │   │   └── _summary.json      # 汇总信息（max, min 等）
│   ├── media/                      # 媒体文件目录
│   │   └── {tag_folder}/          # 按 tag folder 组织
│   │       ├── image_001.png
│   │       └── audio_001.wav
│   ├── console/                    # 控制台日志目录
│   │   ├── 2024-01-01.log         # 按日期分割的日志
│   │   └── error.log              # 错误日志（如果有）
│   └── files/                      # 元数据目录
│       ├── swanlab-metadata.json  # 系统元信息
│       ├── requirements.txt       # Python 依赖
│       └── config.yaml            # 实验配置
```

### 7.2 Tag 数据格式

Tag 数据存储在 `.log` 文件中，采用 JSONL 格式（每行一个 JSON 对象）：

```json
{"index": 0, "data": 0.5, "create_time": 1704096000.123}
{"index": 1, "data": 0.45, "create_time": 1704096001.456}
{"index": 2, "data": 0.40, "create_time": 1704096002.789}
```

### 7.3 Summary 文件格式

`_summary.json` 文件包含 tag 数据的汇总信息：

```json
{
  "max": 0.5,
  "min": 0.001,
  "sum": 1000
}
```

---

## 8. 前端调用示例

### 8.1 获取项目实验列表

```javascript
import http from '@/api/http'

// 获取项目信息
const response = await http.get('/project')
const { data } = response
console.log(data.experiments)
```

### 8.2 获取实验 Tag 数据

```javascript
// Tag 名称需要 URL 编码
const tagName = encodeURIComponent('loss/train')
const response = await http.get(`/experiment/${experimentId}/tag/${tagName}`)
const { data } = response
console.log(data.list) // 数据点列表
```

### 8.3 更新实验信息

```javascript
const response = await http.patch(`/experiment/${experimentId}`, {
  name: '新实验名称',
  description: '新的描述'
})
```

### 8.4 修改图表状态

```javascript
import { updateChartStatus } from '@/api/chart'

// 置顶图表
const result = await updateChartStatus(chart, 1)
console.log(result.groups) // 更新后的命名空间结构
```

### 8.5 修改命名空间展开状态

```javascript
import { updateNamespaceStatus } from '@/api/chart'

await updateNamespaceStatus(true, {
  id: namespaceId,
  experiment_id: { id: experimentId }
})
```

### 8.6 获取媒体文件

```javascript
import { media } from '@/api/chart'

try {
  const blob = await media.get(fileName, experimentId, tagName)
  const url = URL.createObjectURL(blob)
  // 使用 url 显示图片或播放音频
} catch (error) {
  console.error('获取媒体文件失败:', error)
}
```

---

## 9. 注意事项

1. **URL 编码**: Tag 名称可能包含 `/` 等特殊字符，在作为 URL 路径参数时必须进行 URL 编码（`encodeURIComponent`）。

2. **实验状态**:
   - `0`: 运行中
   - `1`: 已完成
   - `-1`: 失败/错误
   - `2`: 已停止

3. **实验可见性（show 字段）**:
   - **必须存在**: 前端依赖 `show` 字段判断实验是否在图表中显示
   - **默认值**: 如果后端未返回 `show` 字段，前端会默认设置为 `1`（可见）
   - **取值**: `1`-显示，`0`-隐藏
   - **影响**: 图表的 `source` 数组中的实验名称会在 `projectStore.showMap` 中查找，如果 `show` 为 `0` 或 `undefined`，该图表可能被过滤掉

4. **轮询更新**: 前端通常通过轮询 `/experiment/{id}/status` 接口来实时更新实验状态和图表配置。

5. **数据降采样**: `/experiment/{id}/tag/{tag}` 接口返回的数据可能经过 LTTB 降采样算法处理，以减少数据传输量。

6. **命名空间 ID**:
   - `-1`: pinned（置顶区域）- 已弃用，现在通过 chart.status=1 实现
   - `-2`: hidden（隐藏区域）- 已弃用，现在通过 chart.status=-1 实现
   - 正数: 普通命名空间

7. **并发访问**: 所有修改操作都使用数据库事务保证原子性。

8. **错误处理**: 前端应根据 HTTP 状态码和响应中的 `code` 字段进行适当的错误处理。

9. **媒体文件**: 媒体文件 API 返回二进制数据，而不是 JSON，需要在请求时设置 `responseType: 'blob'`。

10. **字段名称兼容性**:
    - 后端返回 `key` 和 `chart_type`，前端会自动规范化为 `name` 和 `type`
    - 后端返回 `source`（数组），不是 `sources`（对象数组）
    - namespace.charts 是整数数组，不是对象数组
