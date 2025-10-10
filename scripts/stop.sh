#!/bin/bash
# SwanLab-Server Docker停止脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

main() {
    print_message $BLUE "🛑 停止SwanLab-Dashboard服务..."
    echo "=================================================="

    # 解析命令行参数
    local remove_volumes=false
    local force=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --remove-volumes)
                remove_volumes=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --remove-volumes  同时删除数据卷"
                echo "  --force          强制停止并删除容器"
                echo "  -h, --help       显示此帮助信息"
                exit 0
                ;;
            *)
                print_message $RED "未知参数: $1"
                exit 1
                ;;
        esac
    done

    if [ "$force" = true ]; then
        print_message $YELLOW "强制停止所有服务..."
        docker-compose kill
        docker-compose rm -f
    else
        print_message $YELLOW "优雅停止所有服务..."
        docker-compose down
    fi

    if [ "$remove_volumes" = true ]; then
        print_message $YELLOW "删除数据卷..."
        docker-compose down -v
        print_message $RED "⚠️  所有数据已删除！"
    fi

    print_message $GREEN "✅ SwanLab-Dashboard服务已停止"
}

main "$@"
