# SwanLab All-in-One Docker Image

这个Docker镜像包含了SwanLab平台的所有服务组件，可以在单个容器中运行完整的SwanLab环境。

## 包含的服务

- **SwanLab服务器** - 主要的Web应用和API服务 (端口: 5173)
- **MySQL 8.0** - 主数据库 (端口: 3306)
- **ClickHouse** - 时序数据库，用于实验数据存储 (端口: 8123, 9000)
- **Redis** - 缓存和会话存储 (端口: 6379)
- **MinIO** - 对象存储服务 (端口: 9000, 9001)
- **Nginx** - 反向代理和静态文件服务 (端口: 80)
- **Fluent Bit** - 日志收集和处理 (端口: 24224)

## 构建镜像

```bash
# 在项目根目录下构建
docker build -f Dockerfile.all-in-one -t swanlab-all-in-one:latest .
```

## 运行容器

### 基本运行

```bash
docker run -d \
  --name swanlab-all-in-one \
  -p 5173:5173 \
  -p 3306:3306 \
  -p 8123:8123 \
  -p 9000:9000 \
  -p 9001:9001 \
  -p 6379:6379 \
  -p 80:80 \
  -v swanlab_data:/app/data \
  -v swanlab_logs:/app/logs \
  -v swanlab_storage:/data \
  swanlab-all-in-one:latest
```

### 使用自定义环境变量

```bash
docker run -d \
  --name swanlab-all-in-one \
  -p 5173:5173 \
  -p 3306:3306 \
  -p 8123:8123 \
  -p 9000:9000 \
  -p 9001:9001 \
  -p 6379:6379 \
  -p 80:80 \
  -e MYSQL_ROOT_PASSWORD=your_mysql_password \
  -e MYSQL_DATABASE=your_database_name \
  -e MYSQL_USER=your_mysql_user \
  -e MYSQL_PASSWORD=your_mysql_password \
  -e CLICKHOUSE_USER=your_clickhouse_user \
  -e CLICKHOUSE_PASSWORD=your_clickhouse_password \
  -e MINIO_ROOT_USER=your_minio_user \
  -e MINIO_ROOT_PASSWORD=your_minio_password \
  -v swanlab_data:/app/data \
  -v swanlab_logs:/app/logs \
  -v swanlab_storage:/data \
  swanlab-all-in-one:latest
```

## 环境变量

### MySQL配置
- `MYSQL_ROOT_PASSWORD` - MySQL root密码 (默认: swanlab123)
- `MYSQL_DATABASE` - 数据库名称 (默认: swanlab_cloud)
- `MYSQL_USER` - MySQL用户名 (默认: swanlab_user)
- `MYSQL_PASSWORD` - MySQL用户密码 (默认: swanlab456)

### ClickHouse配置
- `CLICKHOUSE_USER` - ClickHouse用户名 (默认: default)
- `CLICKHOUSE_PASSWORD` - ClickHouse密码 (默认: password123)

### MinIO配置
- `MINIO_ROOT_USER` - MinIO管理员用户名 (默认: minioadmin)
- `MINIO_ROOT_PASSWORD` - MinIO管理员密码 (默认: minioadmin)

### SwanLab配置
- `SWANLAB_CLOUD_SYNC` - 启用云同步 (默认: 1)
- `SWANLAB_LOG_DIR` - 日志目录 (默认: /app/logs)
- `SWANLAB_DATA_DIR` - 数据目录 (默认: /app/data)

## 访问服务

启动容器后，可以通过以下地址访问各个服务：

- **SwanLab Web界面**: http://localhost:5173
- **MinIO控制台**: http://localhost:9001
- **Nginx状态页**: http://localhost/health

## 数据持久化

建议挂载以下目录来持久化数据：

```bash
-v /host/path/to/data:/app/data        # SwanLab应用数据
-v /host/path/to/logs:/app/logs        # 应用日志
-v /host/path/to/storage:/data         # 数据库和存储数据
```

## 健康检查

容器包含健康检查功能，会定期检查SwanLab服务的运行状态：

```bash
# 检查容器健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"

# 查看健康检查日志
docker inspect swanlab-all-in-one --format='{{.State.Health.Log}}'
```

## 服务管理

容器使用supervisord来管理所有服务。可以通过以下方式查看和管理服务：

```bash
# 进入容器
docker exec -it swanlab-all-in-one bash

# 查看所有服务状态
supervisorctl status

# 重启特定服务
supervisorctl restart swanlab
supervisorctl restart mysql
supervisorctl restart clickhouse

# 查看服务日志
supervisorctl tail swanlab
supervisorctl tail mysql
```

## 故障排除

### 查看日志

```bash
# 查看容器日志
docker logs swanlab-all-in-one

# 查看特定服务日志
docker exec swanlab-all-in-one supervisorctl tail swanlab
docker exec swanlab-all-in-one supervisorctl tail mysql
docker exec swanlab-all-in-one supervisorctl tail clickhouse
```

### 常见问题

1. **端口冲突**: 确保宿主机上的端口没有被其他服务占用
2. **内存不足**: 建议至少分配4GB内存给Docker
3. **磁盘空间**: 确保有足够的磁盘空间存储数据和日志

### 重置数据

如果需要重置所有数据：

```bash
# 停止并删除容器
docker stop swanlab-all-in-one
docker rm swanlab-all-in-one

# 删除数据卷
docker volume rm swanlab_data swanlab_logs swanlab_storage

# 重新运行容器
# ... (使用上面的运行命令)
```

## 生产环境部署建议

1. **资源配置**: 建议至少4GB内存和20GB磁盘空间
2. **备份策略**: 定期备份数据卷
3. **监控**: 设置容器和服务监控
4. **安全**: 修改默认密码，配置防火墙规则
5. **更新**: 定期更新镜像到最新版本

## Docker Compose示例

如果你更喜欢使用Docker Compose：

```yaml
version: '3.8'

services:
  swanlab-all-in-one:
    image: swanlab-all-in-one:latest
    container_name: swanlab-all-in-one
    restart: unless-stopped
    ports:
      - "5173:5173"
      - "3306:3306"
      - "8123:8123"
      - "9000:9000"
      - "9001:9001"
      - "6379:6379"
      - "80:80"
    environment:
      MYSQL_ROOT_PASSWORD: swanlab123
      MYSQL_DATABASE: swanlab_cloud
      MYSQL_USER: swanlab_user
      MYSQL_PASSWORD: swanlab456
      CLICKHOUSE_USER: default
      CLICKHOUSE_PASSWORD: password123
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - swanlab_data:/app/data
      - swanlab_logs:/app/logs
      - swanlab_storage:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5173/api/v1/cloud/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

volumes:
  swanlab_data:
  swanlab_logs:
  swanlab_storage:
```

保存为 `docker-compose.all-in-one.yml` 并运行：

```bash
docker-compose -f docker-compose.all-in-one.yml up -d
```