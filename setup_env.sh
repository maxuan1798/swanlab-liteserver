#!/bin/bash
# 设置虚拟环境并安装依赖

set -e

echo "============================================================"
echo "SwanLab-Server 虚拟环境设置"
echo "============================================================"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo ""
echo "升级 pip..."
pip install --upgrade pip -q

# 安装依赖
echo ""
echo "安装项目依赖..."
pip install -r requirements.txt -q

# 安装 swanlab
echo ""
echo "安装 swanlab..."
pip install swanlab -q

echo ""
echo "============================================================"
echo "✅ 环境设置完成！"
echo "============================================================"
echo ""
echo "使用方法:"
echo "  source venv/bin/activate     # 激活虚拟环境"
echo "  python examples/train_with_verify.py  # 运行训练脚本"
echo ""
echo "或者直接运行:"
echo "  ./run_train.sh               # 自动激活环境并运行训练"
echo ""
