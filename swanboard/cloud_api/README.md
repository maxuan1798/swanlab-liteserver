# SwanLab MySQL-based Cloud API

基于MySQL数据库的SwanLab云端同步API，提供本地SQLite数据库与MySQL云端数据库的双向同步功能。

## 功能特性

- **双数据库支持**：本地SQLite + 云端MySQL
- **自动同步**：项目、实验、图表等数据自动同步到云端
- **线程安全**：支持多线程环境下的安全操作
- **配置灵活**：支持环境变量和代码配置
- **错误处理**：完善的异常处理和日志记录
- **CLI工具**：提供命令行管理工具

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SwanBoard     │    │   Enhanced      │    │   MySQL Cloud  │
│   (Local)       │───▶│   Callback      │───▶│   Database      │
│   SQLite        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 快速开始

### 1. 环境配置

创建环境变量配置：

```bash
# 启用云端同步
export SWANLAB_CLOUD_SYNC=true

# MySQL数据库配置
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=swanlab_user
export MYSQL_PASSWORD=your_secure_password
export MYSQL_DATABASE=swanlab_cloud

# 工作空间配置
export SWANLAB_WORKSPACE=my_workspace
export SWANLAB_USER=my_username
```

### 2. 安装依赖

```bash
pip install PyMySQL>=1.0.0
```

### 3. 初始化数据库

```bash
python -m swanboard.cloud_api.cli init-db --host localhost --user root --database swanlab_cloud
```

### 4. 使用增强回调

```python
from swanboard.enhanced_callback import EnhancedSwanBoardCallback

# 使用环境变量配置
callback = EnhancedSwanBoardCallback(enable_cloud=True)

# 或者手动配置MySQL
from swanboard.cloud_api import MySQLConfig

mysql_config = MySQLConfig(
    host='localhost',
    port=3306,
    user='swanlab_user',
    password='password',
    database='swanlab_cloud'
)

callback = EnhancedSwanBoardCallback(
    enable_cloud=True,
    mysql_config=mysql_config
)
```

## 数据库模型

### 云端数据库表结构

| 表名 | 说明 | 对应本地表 |
|------|------|-----------|
| `cloud_projects` | 云端项目表 | `projects` |
| `cloud_experiments` | 云端实验表 | `experiments` |
| `cloud_charts` | 云端图表表 | `charts` |
| `cloud_tags` | 云端标签表 | `tags` |
| `cloud_namespaces` | 云端命名空间表 | `namespaces` |
| `cloud_sources` | 云端数据源表 | `sources` |
| `cloud_displays` | 云端显示配置表 | `displays` |

### 主要字段说明

#### CloudProject (云端项目)
- `id`: 主键
- `name`: 项目名称（在同一工作空间内唯一）
- `workspace`: 工作空间名称
- `owner`: 项目所有者
- `visibility`: 可见性 (public/private/internal)
- `experiment_count`: 实验数量统计

#### CloudExperiment (云端实验)
- `id`: 主键
- `project`: 关联项目外键
- `run_id`: 运行ID（全局唯一）
- `name`: 实验名称
- `status`: 实验状态 (-1:crashed, 0:running, 1:finished)
- `light_color`, `dark_color`: 主题颜色

## 同步机制

### 同步流程

1. **项目同步**：`on_init` → `sync_project`
2. **实验同步**：`before_init_experiment` → `sync_experiment`
3. **指标同步**：`on_column_create` → `sync_column`
4. **状态同步**：`on_stop` → `sync_experiment_status`

### 同步策略

- **增量同步**：只同步新增和变更的数据
- **冲突处理**：本地数据优先，云端数据作为备份
- **失败重试**：网络异常时优雅降级，不影响本地功能
- **数据完整性**：使用事务确保数据一致性

## API接口

### CloudSyncManager

主要同步管理类，提供以下接口：

```python
from swanboard.cloud_api import CloudSyncManager

manager = CloudSyncManager(workspace='my_workspace', user='username')

# 同步项目
project_id = manager.sync_project('project_name', 'description')

# 同步实验
experiment_id = manager.sync_experiment('run_id', 'exp_name', 'description', colors=('light', 'dark'))

# 同步列信息
column_id = manager.sync_column(column_info)

# 同步实验状态
success = manager.sync_experiment_status(status=1)

# 获取统计信息
stats = manager.get_stats()
```

### MySQLConfig

数据库配置类：

```python
from swanboard.cloud_api import MySQLConfig

# 从环境变量加载
config = MySQLConfig.from_env()

# 手动创建
config = MySQLConfig(
    host='localhost',
    port=3306,
    user='username',
    password='password',
    database='swanlab_cloud'
)

# 验证配置
if config.validate():
    connection_string = config.get_connection_string()
```

## CLI工具

提供命令行管理工具：

```bash
# 测试数据库连接
python -m swanboard.cloud_api.cli test-connection -h localhost -u root -d swanlab_cloud

# 初始化数据库
python -m swanboard.cloud_api.cli init-db -h localhost -u root -d swanlab_cloud

# 查看同步统计
python -m swanboard.cloud_api.cli stats -w my_workspace -n my_user

# 列出项目
python -m swanboard.cloud_api.cli list-projects -w my_workspace

# 显示环境变量示例
python -m swanboard.cloud_api.cli env-example
```

## 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `SWANLAB_CLOUD_SYNC` | 否 | false | 是否启用云端同步 |
| `MYSQL_HOST` | 是 | localhost | MySQL主机地址 |
| `MYSQL_PORT` | 否 | 3306 | MySQL端口 |
| `MYSQL_USER` | 是 | root | MySQL用户名 |
| `MYSQL_PASSWORD` | 是 | - | MySQL密码 |
| `MYSQL_DATABASE` | 否 | swanlab_cloud | MySQL数据库名 |
| `MYSQL_CHARSET` | 否 | utf8mb4 | 字符集 |
| `MYSQL_MAX_CONNECTIONS` | 否 | 20 | 最大连接数 |
| `SWANLAB_WORKSPACE` | 否 | default | 工作空间名称 |
| `SWANLAB_USER` | 否 | anonymous | 用户名 |

### 数据库要求

- MySQL 5.7+ 或 8.0+
- 支持UTF-8字符集
- 支持InnoDB存储引擎
- 建议启用慢查询日志

## 安全考虑

1. **连接安全**：使用SSL连接（推荐）
2. **权限控制**：为SwanLab创建专用数据库用户
3. **密码管理**：使用环境变量存储敏感信息
4. **网络安全**：配置防火墙规则
5. **数据加密**：敏感字段可考虑加密存储

## 故障排除

### 常见问题

1. **连接失败**
   - 检查MySQL服务是否运行
   - 验证用户名密码是否正确
   - 确认网络连接和防火墙设置

2. **同步失败**
   - 查看日志输出获取详细错误信息
   - 检查数据库权限
   - 验证表结构是否正确

3. **性能问题**
   - 监控数据库连接数
   - 优化MySQL配置
   - 考虑增加连接池大小

### 日志记录

系统使用 `swanlog` 记录日志：

- `DEBUG`: 详细同步信息
- `INFO`: 重要操作信息
- `WARNING`: 非致命错误
- `ERROR`: 严重错误

## 开发指南

### 添加新的模型

1. 在 `mysql_models.py` 中定义模型
2. 添加到 `CLOUD_MODELS` 列表
3. 在 `CloudSyncManager` 中实现同步逻辑
4. 更新文档和测试

### 扩展同步功能

1. 继承 `CloudSyncManager` 类
2. 实现自定义同步方法
3. 在 `EnhancedSwanBoardCallback` 中集成

## 版本兼容性

- Python 3.7+
- MySQL 5.7+
- Peewee ORM 3.14+
- PyMySQL 1.0+

## 许可证

本项目采用与SwanLab相同的许可证。