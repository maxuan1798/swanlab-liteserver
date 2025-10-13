# SwanLab-Server

SwanLab - 训练可视化服务

该仓库用于维护 SwanLab 训练可视化服务的相关代码和文档，包含前后端代码以及完整的 Docker 部署方案。

## 快速开始

### Docker 部署（推荐）

使用 Docker Compose 一键部署完整的 SwanLab-Server 服务栈：

```bash
# 克隆仓库
git clone https://github.com/swanhubx/swanlab-server.git
cd swanlab-server/docker

# 启动所有服务
docker-compose up -d

# 访问服务
open http://localhost:22224
```

详细部署说明请参考：[Docker 部署文档](docker/README.md)

### 服务架构

SwanLab-Server 采用微服务架构，包含以下组件：

- **Nginx** - 反向代理和负载均衡 (端口 22224)
- **SwanLab Server** - 核心可视化服务 (端口 5173)
- **MySQL** - 主数据库，存储结构化数据
- **ClickHouse** - 时序数据库，存储实验指标和日志
- **Fluent Bit** - 日志收集器，处理训练日志
- **MinIO** - 对象存储，存储媒体文件
- **Redis** - 缓存和会话存储

```
┌─────────────┐
│   Nginx     │ ← http://localhost:22224
└──────┬──────┘
       │
       ├─────────────────────┐
       ▼                     ▼
┌─────────────┐      ┌──────────────┐
│  SwanLab    │      │  Fluent Bit  │
│  Server     │      │              │
└──────┬──────┘      └──────┬───────┘
       │                    │
       ├────────┬───────────┤
       ▼        ▼           ▼
   ┌──────┐ ┌──────┐  ┌────────────┐
   │ MySQL│ │ MinIO│  │ ClickHouse │
   └──────┘ └──────┘  └────────────┘
```

### Host 模式使用

支持本地训练程序实时同步数据到 SwanLab-Server：

```bash
# 配置环境变量
export SWANLAB_BASE_URL=http://localhost:22224
export SWANLAB_CLOUD_SYNC=true
```

```python
import swanlab

# 使用 host 模式
run = swanlab.init(
    project="my-project",
    mode="host",
)

# 记录指标
swanlab.log({"loss": 0.1, "accuracy": 0.95})
```

更多使用方式请查看 [Docker 部署文档](docker/README.md)。

## 目录结构

```
├── swanboard/          # 后端代码
│   ├── controller/     # 控制器层
│   ├── db/            # 数据库层
│   ├── middleware/    # 中间件
│   ├── module/        # 业务模块
│   ├── router/        # 路由配置
│   ├── run/           # 运行时
│   ├── settings.py    # 配置文件
│   ├── template/      # 前端构建产物
│   └── utils/         # 工具函数
│
├── vue/               # 前端代码
│   ├── src/          # 源代码
│   ├── public/       # 静态资源
│   └── package.json  # 依赖配置
│
├── docker/           # Docker 部署
│   ├── docker-compose.yml
│   ├── nginx/       # Nginx 配置
│   ├── mysql/       # MySQL 配置
│   ├── clickhouse/  # ClickHouse 配置
│   ├── fluent-bit/  # Fluent Bit 配置
│   └── README.md    # 部署文档
│
├── test/            # 测试代码
└── tutils/          # 测试工具
```

## 开发指南

### 后端开发

后端使用 Python + FastAPI 开发：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python -m swanboard.run
```

### 前端开发

前端使用 Vue.js 开发：

```bash
cd vue

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build.release
```

构建产物会自动输出到 `swanboard/template/` 目录。

### 测试

```bash
# 运行测试
python -m pytest test/

# 运行特定测试
python -m pytest test/test_api.py
```

## 工作流程

1. **后端开发**: 在 `swanboard/` 目录下开发，完成后端功能
2. **前端开发**: 在 `vue/` 目录下开发，完成后运行 `npm run build.release`
3. **测试**: 在 `test/` 目录下编写和运行测试
4. **发布**: 在 main 分支发布新版本，打上 tag，触发自动构建和 PyPI 发布

## SwanLab 与 SwanBoard

**SwanBoard** 是 SwanLab 的可视化组件，负责提供 Web 界面和数据可视化服务，但不参与训练过程。

- 作为 Python 包依赖被 SwanLab 导入
- 通过 `swanlab watch` 命令启动轻量级本地服务
- 支持离线使用，查看本地训练数据

**SwanLab-Server** 是完整的服务端部署方案，提供：

- 云端数据存储和管理
- 多用户协作
- 实时数据同步（Host 模式）
- 企业级部署能力

## 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MYSQL_HOST` | MySQL 主机地址 | `mysql` |
| `MYSQL_PORT` | MySQL 端口 | `3306` |
| `MYSQL_USER` | MySQL 用户名 | `swanlab_user` |
| `MYSQL_PASSWORD` | MySQL 密码 | `swanlab456` |
| `MYSQL_DATABASE` | MySQL 数据库名 | `swanlab_cloud` |
| `CLICKHOUSE_HOST` | ClickHouse 主机 | `clickhouse` |
| `CLICKHOUSE_PORT` | ClickHouse 端口 | `9000` |
| `MINIO_ENDPOINT` | MinIO API 地址 | `http://minio:9000` |
| `MINIO_ACCESS_KEY` | MinIO Access Key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO Secret Key | `minioadmin` |
| `SWANLAB_BASE_URL` | 统一服务地址 | `http://localhost:5173` |

更多配置选项请参考 [docker/.env](docker/.env)。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 技术支持

- **文档**: https://docs.swanlab.cn
- **GitHub Issues**: https://github.com/swanhubx/swanlab-server/issues
- **社区支持**: https://docs.swanlab.cn/guide_cloud/community/online-support.html

## 协议

本项目遵循 [Apache 2.0 License](LICENSE) 开源协议。
