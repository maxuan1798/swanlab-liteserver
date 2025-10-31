#!/bin/bash

# SwanLab All-in-One ARM64 Docker 构建脚本
# 用于构建支持Linux/arm64架构的Docker镜像

set -e

echo "🚀 开始构建 SwanLab All-in-One ARM64 Docker 镜像..."

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装或不在PATH中"
    exit 1
fi

# 检查是否在ARM64机器上运行
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "arm64" ]; then
    echo "⚠️  警告: 当前运行在 $ARCH 架构上，建议在ARM64机器上构建以获得最佳性能"
    echo "   如果使用x86_64机器，Docker将使用QEMU模拟器构建ARM64镜像"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 构建已取消"
        exit 1
    fi
fi

# 设置镜像标签
IMAGE_NAME="swanlab-all-in-one"
IMAGE_TAG="arm64-latest"

# 检查Docker Buildx是否可用
if docker buildx version &> /dev/null; then
    echo "📦 使用 Docker Buildx 构建多架构镜像..."

    # 创建并使用buildx构建器
    docker buildx create --name multiarch --use 2>/dev/null || true
    docker buildx inspect --bootstrap

    # 构建ARM64镜像
    docker buildx build \
        --platform linux/arm64 \
        -f Dockerfile.all-in-one.arm64 \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        --load \
        .
else
    echo "📦 使用标准 Docker 构建ARM64镜像..."

    # 使用标准Docker构建
    docker build \
        --platform linux/arm64 \
        -f Dockerfile.all-in-one.arm64 \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        .
fi

echo "✅ ARM64 Docker 镜像构建完成!"
echo ""
echo "📋 镜像信息:"
echo "   镜像名称: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "   架构: linux/arm64"
echo ""
echo "🚀 运行命令:"
echo "   docker run -d -p 8800:8800 ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "🔍 检查镜像架构:"
echo "   docker inspect ${IMAGE_NAME}:${IMAGE_TAG} | grep Architecture"