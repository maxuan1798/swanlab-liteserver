#!/bin/bash
# 激活虚拟环境并运行训练脚本

set -e

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: ./setup_env.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 加载环境变量
if [ -f ".envrc" ]; then
    source .envrc
elif [ -f ".env" ]; then
    # 从 .env 文件加载（如果存在）
    export $(grep -v '^#' .env | grep -E '^(SWANLAB_|MYSQL_|CLICKHOUSE_)' | xargs)
    echo "✅ 从 .env 文件加载环境变量"
else
    # 使用默认值
    export SWANLAB_BASE_URL=${SWANLAB_BASE_URL:-http://localhost:22224}
    export SWANLAB_API_KEY="${SWANLAB_API_KEY:-Omyoi_DlU_9xFKR3S3EKTBGlc6_VXUMM47J6V-MEaq0}"
    echo "⚠️  使用默认环境变量"
fi

# 配置 SwanLab SDK 云端 API 主机，指向本地服务
export SWANLAB_API_HOST="${SWANLAB_BASE_URL%/}/api/v1/cloud"

echo ""
echo "环境变量:"
echo "  SWANLAB_BASE_URL: $SWANLAB_BASE_URL"
echo "  SWANLAB_API_HOST: $SWANLAB_API_HOST"
echo "  SWANLAB_CLOUD_SYNC: $SWANLAB_CLOUD_SYNC"
echo "  SWANLAB_API_KEY: ${SWANLAB_API_KEY:0:20}..."
echo ""

# 运行训练脚本（显式使用虚拟环境的 Python）
./venv/bin/python examples/train_with_verify.py "$@"
