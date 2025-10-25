#!/bin/bash

# SwanLab All-in-One 快速启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 SwanLab All-in-One 快速启动脚本"
echo "======================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装或未在PATH中找到"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo "❌ 错误: Docker daemon 未运行"
    echo "请启动Docker服务"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 设置镜像名称
IMAGE_NAME="swanlab-all-in-one"
CONTAINER_NAME="swanlab-all-in-one"

# 检查是否已有运行的容器
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "⚠️  发现已运行的容器: $CONTAINER_NAME"
    read -p "是否停止并重新创建? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 停止现有容器..."
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    else
        echo "取消操作"
        exit 0
    fi
fi

# 检查镜像是否存在
if ! docker images -q "$IMAGE_NAME" | grep -q .; then
    echo "📦 镜像不存在，开始构建..."
    echo "这可能需要几分钟时间，请耐心等待..."
    
    cd "$PROJECT_ROOT"
    docker build -f Dockerfile.all-in-one -t "$IMAGE_NAME:latest" .
    
    if [ $? -eq 0 ]; then
        echo "✅ 镜像构建成功"
    else
        echo "❌ 镜像构建失败"
        exit 1
    fi
else
    echo "✅ 发现已存在的镜像: $IMAGE_NAME"
    read -p "是否重新构建镜像? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 重新构建镜像..."
        cd "$PROJECT_ROOT"
        docker build -f Dockerfile.all-in-one -t "$IMAGE_NAME:latest" . --no-cache
    fi
fi

# 创建数据卷
echo "📁 创建数据卷..."
docker volume create swanlab_data 2>/dev/null || true
docker volume create swanlab_logs 2>/dev/null || true
docker volume create swanlab_storage 2>/dev/null || true

# 启动容器
echo "🏃 启动SwanLab All-in-One容器..."

docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p 5173:5173 \
  -p 3306:3306 \
  -p 8123:8123 \
  -p 9000:9000 \
  -p 9001:9001 \
  -p 6379:6379 \
  -p 80:80 \
  -p 24224:24224 \
  -v swanlab_data:/app/data \
  -v swanlab_logs:/app/logs \
  -v swanlab_storage:/data \
  "$IMAGE_NAME:latest"

if [ $? -eq 0 ]; then
    echo "✅ 容器启动成功"
    echo ""
    echo "🎉 SwanLab All-in-One 已成功启动!"
    echo "======================================"
    echo "📍 服务访问地址:"
    echo "   SwanLab Web界面:  http://localhost:5173"
    echo "   MinIO控制台:      http://localhost:9001"
    echo "   Nginx状态:        http://localhost/health"
    echo ""
    echo "🔑 默认账户信息:"
    echo "   MySQL root密码:   swanlab123"
    echo "   MySQL用户:        swanlab_user / swanlab456"
    echo "   ClickHouse:       default / password123"
    echo "   MinIO:           minioadmin / minioadmin"
    echo ""
    echo "📊 容器管理命令:"
    echo "   查看状态:        docker ps -f name=$CONTAINER_NAME"
    echo "   查看日志:        docker logs $CONTAINER_NAME"
    echo "   进入容器:        docker exec -it $CONTAINER_NAME bash"
    echo "   停止容器:        docker stop $CONTAINER_NAME"
    echo "   删除容器:        docker rm $CONTAINER_NAME"
    echo ""
    echo "🚀 容器正在初始化，请等待1-2分钟后访问Web界面"
    echo "   可以使用 'docker logs -f $CONTAINER_NAME' 查看启动进度"
else
    echo "❌ 容器启动失败"
    echo "请检查日志: docker logs $CONTAINER_NAME"
    exit 1
fi