#!/bin/bash
# SwanLab-Server Docker启动脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_message $RED "❌ Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "❌ Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    print_message $GREEN "✅ Docker和Docker Compose已安装"
}

# 检查环境配置文件
check_env() {
    if [ ! -f .env_test ]; then
        if [ -f .env_test.example ]; then
            print_message $YELLOW "⚠️  未找到.env文件，正在从.env.example创建..."
            cp .env_test.example .env_test
            print_message $GREEN "✅ 已创建.env文件，请根据需要修改配置"
        else
            print_message $RED "❌ 未找到.env.example文件"
            exit 1
        fi
    else
        print_message $GREEN "✅ 环境配置文件存在"
    fi
}

# 创建必要的目录
create_directories() {
    print_message $BLUE "📁 创建必要的目录..."

    mkdir -p docker/mysql/init
    mkdir -p docker/mysql/conf.d
    mkdir -p docker/nginx/ssl
    mkdir -p logs
    mkdir -p data

    print_message $GREEN "✅ 目录创建完成"
}

# 启动服务
start_services() {
    local profile=${1:-""}

    print_message $BLUE "🚀 启动SwanLab-Dashboard服务..."

    if [ "$profile" = "production" ]; then
        print_message $YELLOW "启动生产环境配置（包含Nginx）..."
        docker-compose --profile production up -d
    else
        print_message $YELLOW "启动开发环境配置..."
        docker-compose up -d mysql redis swanlab-dashboard
    fi

    print_message $GREEN "✅ 服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    print_message $BLUE "⏳ 等待服务就绪..."

    # 等待MySQL
    print_message $YELLOW "等待MySQL服务..."
    while ! docker-compose exec mysql mysqladmin ping -h localhost --silent; do
        sleep 2
        echo -n "."
    done
    echo

    # 等待SwanLab-Dashboard
    print_message $YELLOW "等待SwanLab-Dashboard服务..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:5173/api/v1/cloud/health > /dev/null 2>&1; then
            break
        fi
        sleep 2
        ((attempt++))
        echo -n "."
    done
    echo

    if [ $attempt -eq $max_attempts ]; then
        print_message $RED "❌ SwanLab-Dashboard服务启动超时"
        return 1
    fi

    print_message $GREEN "✅ 所有服务已就绪"
}

# 显示服务状态
show_status() {
    print_message $BLUE "📊 服务状态："
    docker-compose ps

    echo
    print_message $BLUE "🌐 访问地址："
    print_message $GREEN "  SwanLab-Dashboard: http://localhost:5173"
    print_message $GREEN "  API健康检查: http://localhost:5173/api/v1/cloud/health"
    print_message $GREEN "  MySQL: localhost:3306"

    echo
    print_message $BLUE "📋 管理命令："
    print_message $YELLOW "  查看日志: ./scripts/logs.sh"
    print_message $YELLOW "  停止服务: ./scripts/stop.sh"
    print_message $YELLOW "  重启服务: ./scripts/restart.sh"
}

# 主函数
main() {
    print_message $BLUE "🐋 SwanLab-Dashboard Docker启动脚本"
    echo "=================================================="

    # 解析命令行参数
    local profile=""
    local wait_ready=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --production)
                profile="production"
                shift
                ;;
            --no-wait)
                wait_ready=false
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --production  启动生产环境配置（包含Nginx）"
                echo "  --no-wait     不等待服务就绪"
                echo "  -h, --help    显示此帮助信息"
                exit 0
                ;;
            *)
                print_message $RED "未知参数: $1"
                exit 1
                ;;
        esac
    done

    # 执行启动流程
    check_docker
    check_env
    create_directories
    start_services "$profile"

    if [ "$wait_ready" = true ]; then
        wait_for_services
    fi

    show_status

    print_message $GREEN "🎉 SwanLab-Dashboard启动完成！"
}

# 执行主函数
main "$@"
