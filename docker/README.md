# SwanLab-Server Docker 部署指南

本文档介绍如何使用 Docker Compose 部署 SwanLab-Server 及其相关组件。

## 架构概览

SwanLab-Server 架构，包含以下组件：

```
┌─────────────┐
│   Nginx     │ ← 统一入口 (端口 22224)
└──────┬──────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌─────────────┐                      ┌──────────────┐
│  SwanLab    │                      │  Fluent Bit  │
│  Server     │                      │  (日志收集)   │
└──────┬──────┘                      └──────┬───────┘
       │                                    │
       ├────────┬──────────┬────────────────┤
       ▼        ▼          ▼                ▼
   ┌──────┐ ┌──────┐  ┌──────┐      ┌────────────┐
   │ MySQL│ │ MinIO│  │ Redis│      │ ClickHouse │
   └──────┘ └──────┘  └──────┘      └────────────┘
```

## 组件说明

### 1. Nginx (反向代理)
- **端口**: 22224 (HTTP)
- **功能**:
  - 作为统一入口，代理所有服务
  - 路由 `/api/*` 到 SwanLab Server
  - 路由 `/fluent-bit` 到 Fluent Bit
  - 提供负载均衡和 SSL 终止（可选）
- **配置文件**: `nginx/nginx.conf`

### 2. SwanLab Server (核心服务)
- **端口**: 5173
- **功能**:
  - 提供训练可视化 Web 界面
  - REST API 服务
  - 实验管理和数据查询
- **环境变量**:
  - `MYSQL_HOST`: MySQL 主机地址
  - `CLICKHOUSE_HOST`: ClickHouse 主机地址
  - `MINIO_ENDPOINT`: MinIO API 地址
  - `SWANLAB_BASE_URL`: 统一服务基础地址

### 3. MySQL (主数据库)
- **端口**: 3306
- **功能**:
  - 存储项目、实验、用户等结构化数据
  - 事务性数据持久化
- **数据卷**: `mysql_data`
- **配置**:
  - 默认用户: `swanlab_user`
  - 默认数据库: `swanlab_cloud`
  - 字符集: `utf8mb4`

### 4. ClickHouse (时序数据库)
- **端口**:
  - 22225 (HTTP Interface)
  - 19000 (Native Interface)
- **功能**:
  - 存储实验指标、日志等时序数据
  - 高性能查询和聚合分析
- **数据卷**: `clickhouse_data`
- **初始化脚本**: `clickhouse/init/`

### 5. Fluent Bit (日志收集器)
- **端口**:
  - 24224 (HTTP Input，内部)
  - 2020 (Monitoring)
- **功能**:
  - 接收训练日志
  - 数据过滤和转换
  - 写入 ClickHouse
- **配置文件**:
  - `fluent-bit/fluent-bit.conf`
  - `fluent-bit/parsers.conf`
- **通过 Nginx 访问**: `http://localhost:22224/fluent-bit`

### 6. MinIO (对象存储)
- **端口**:
  - 9100 (API)
  - 9101 (Console)
- **功能**:
  - 存储媒体文件（图片、音频、视频等）
  - S3 兼容的对象存储服务
- **数据卷**: `minio_data`
- **默认凭证**:
  - Access Key: `minioadmin`
  - Secret Key: `minioadmin`

### 7. Redis (缓存)
- **端口**: 16379
- **功能**:
  - 会话存储
  - 缓存热点数据
  - 分布式锁
- **数据卷**: `redis_data`

## 快速开始

### 1. 环境准备

确保已安装：
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### 2. 配置环境变量

复制并编辑 `.env` 文件：

```bash
cd docker
cp .env.example .env
# 根据需要修改配置
vim .env
```

关键配置项：

```bash
# MySQL 配置
MYSQL_ROOT_PASSWORD=swanlab123
MYSQL_USER=swanlab_user
MYSQL_PASSWORD=swanlab456
MYSQL_DATABASE=swanlab_cloud

# ClickHouse 配置
CLICKHOUSE_USER=default
CLICKHOUSE_PASS=password123

# MinIO 配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# 服务端口
NGINX_HTTP_PORT=22224
DASHBOARD_PORT=5173
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 访问服务

- **SwanLab Dashboard**: http://localhost:22224
- **MinIO Console**: http://localhost:9101
- **ClickHouse HTTP**: http://localhost:22225

### 5. 停止服务

```bash
# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和数据卷（慎用）
docker-compose down -v
```

## 使用 Host 模式

Host 模式允许本地训练程序将数据实时同步到 SwanLab-Server。

### 1. 配置环境变量

在训练机器上设置：

```bash
# 统一服务地址（Nginx 端口）
export SWANLAB_BASE_URL=http://localhost:22224

# 可选：启用云端同步
export SWANLAB_CLOUD_SYNC=true
export SWANLAB_API_KEY=your_api_key
export SWANLAB_WORKSPACE=default
```

### 2. 训练代码

```python
import swanlab

# 初始化 host 模式
run = swanlab.init(
    project="my-project",
    mode="host",  # 启用 host 模式
)

# 记录训练指标
for epoch in range(100):
    loss = train_one_epoch()
    swanlab.log({"loss": loss, "epoch": epoch})
```

### 3. 数据流向

```
训练程序 (swanlab.init(mode="host"))
    │
    ├─→ 日志数据 → Nginx:22224/fluent-bit → Fluent Bit → ClickHouse
    ├─→ 媒体文件 → MinIO:9100
    └─→ 实验元数据 → Nginx:22224/api → SwanLab Server → MySQL
```

## 目录结构

```
docker/
├── README.md                    # 本文档
├── docker-compose.yml           # Docker Compose 配置
├── .env                         # 环境变量配置
│
├── nginx/                       # Nginx 配置
│   └── nginx.conf              # Nginx 主配置文件
│
├── mysql/                       # MySQL 配置
│   ├── init/                   # 初始化 SQL 脚本
│   └── conf.d/                 # MySQL 配置文件
│
├── clickhouse/                  # ClickHouse 配置
│   └── init/                   # 初始化脚本
│
├── fluent-bit/                  # Fluent Bit 配置
│   ├── fluent-bit.conf         # 主配置文件
│   └── parsers.conf            # 解析器配置
│
└── [data volumes]               # 数据卷（由 Docker 管理）
    ├── mysql_data/
    ├── clickhouse_data/
    ├── minio_data/
    ├── redis_data/
    ├── fluent_bit_data/
    ├── swanlab_data/
    └── swanlab_logs/
```

## 常见问题

### 1. 服务启动失败

**问题**: 某个服务一直重启

**解决方案**:
```bash
# 查看具体服务日志
docker-compose logs <service-name>

# 例如查看 MySQL 日志
docker-compose logs mysql

# 检查端口占用
netstat -an | grep <port>
```

### 2. Fluent Bit 连接失败

**问题**: 训练程序报告 "Failed to connect to fluent-bit"

**解决方案**:
```bash
# 1. 检查 Nginx 是否正常运行
docker-compose ps nginx

# 2. 测试 Fluent Bit 端点
curl -X POST http://localhost:22224/fluent-bit \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# 3. 查看 Nginx 日志
docker logs swanlab-nginx

# 4. 重启 Nginx
docker-compose restart nginx
```

### 3. 数据持久化

**问题**: 重启后数据丢失

**解决方案**:
- 确保使用了命名卷（已在 docker-compose.yml 中配置）
- 避免使用 `docker-compose down -v`
- 定期备份重要数据

### 4. 性能优化

**MySQL 优化**:
```yaml
# 在 docker-compose.yml 中调整
command: >
  --max_connections=1000
  --innodb-buffer-pool-size=512M
```

**ClickHouse 优化**:
```yaml
environment:
  CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
  # 增加内存限制
volumes:
  - ./clickhouse/config.xml:/etc/clickhouse-server/config.xml
```

## 监控和维护

### 健康检查

所有服务都配置了健康检查：

```bash
# 查看服务健康状态
docker-compose ps

# 检查特定服务健康
docker inspect --format='{{json .State.Health}}' swanlab-server
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f swanlab-server

# 查看最近 100 行日志
docker-compose logs --tail=100 fluent-bit
```

### 数据备份

```bash
# 备份 MySQL
docker exec swanlab-mysql mysqldump -u root -p swanlab_cloud > backup.sql

# 备份 ClickHouse
docker exec swanlab-clickhouse clickhouse-client --query "BACKUP DATABASE swanlab"

# 备份 MinIO
docker exec swanlab-minio mc mirror /data /backup
```

## 生产环境建议

1. **安全性**:
   - 修改所有默认密码
   - 启用 HTTPS（配置 SSL 证书）
   - 限制网络访问（使用防火墙）
   - 定期更新镜像版本

2. **高可用**:
   - 使用外部数据库集群
   - 配置 MinIO 分布式模式
   - 添加负载均衡器
   - 设置服务自动重启

3. **监控**:
   - 集成 Prometheus + Grafana
   - 配置告警规则
   - 监控磁盘使用率
   - 设置日志采集

4. **备份策略**:
   - 定期备份数据库
   - 备份配置文件
   - 测试恢复流程
   - 异地存储备份

## 故障排查

### 查看完整的系统信息

```bash
# 查看 Docker 版本
docker --version
docker-compose --version

# 查看容器资源使用
docker stats

# 查看网络配置
docker network inspect docker_swanlab-network

# 查看数据卷
docker volume ls
docker volume inspect docker_mysql_data
```

### 重置服务

```bash
# 完全重置（删除所有数据）
docker-compose down -v
docker volume prune -f
docker-compose up -d
```

## 更新服务

```bash
# 拉取最新镜像
docker-compose pull

# 重启服务
docker-compose up -d

# 清理旧镜像
docker image prune -a
```

