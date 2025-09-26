#!/bin/bash
# SwanLab-Dashboard Docker重启脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

main() {
    print_message $BLUE "🔄 重启SwanLab-Dashboard服务..."
    echo "=================================================="

    # 解析命令行参数
    local production=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --production)
                production=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --production  重启生产环境配置"
                echo "  -h, --help    显示此帮助信息"
                exit 0
                ;;
            *)
                print_message $RED "未知参数: $1"
                exit 1
                ;;
        esac
    done

    # 停止服务
    ./scripts/stop.sh

    # 等待一下
    sleep 2

    # 重新启动服务
    if [ "$production" = true ]; then
        ./scripts/start.sh --production
    else
        ./scripts/start.sh
    fi

    print_message $GREEN "✅ SwanLab-Dashboard服务重启完成"
}

main "$@"