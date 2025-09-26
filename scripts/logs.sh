#!/bin/bash
# SwanLab-Dashboard Docker日志查看脚本

set -e

# 颜色输出
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

show_help() {
    echo "用法: $0 [服务名] [选项]"
    echo
    echo "服务名:"
    echo "  mysql              显示MySQL日志"
    echo "  swanlab-dashboard  显示SwanLab-Dashboard日志"
    echo "  redis              显示Redis日志"
    echo "  nginx              显示Nginx日志"
    echo "  all                显示所有服务日志（默认）"
    echo
    echo "选项:"
    echo "  -f, --follow       跟踪日志输出"
    echo "  -t, --tail N       显示最后N行日志（默认100）"
    echo "  --since TIME       显示指定时间后的日志（如：2023-01-01T10:00:00）"
    echo "  -h, --help         显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 mysql -f                    # 跟踪MySQL日志"
    echo "  $0 swanlab-dashboard --tail 50 # 显示最后50行Dashboard日志"
    echo "  $0 all --since 1h              # 显示最近1小时的所有日志"
}

main() {
    local service="all"
    local follow=""
    local tail="100"
    local since=""

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            mysql|swanlab-dashboard|redis|nginx|all)
                service=$1
                shift
                ;;
            -f|--follow)
                follow="-f"
                shift
                ;;
            -t|--tail)
                tail="$2"
                shift 2
                ;;
            --since)
                since="--since $2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_message $RED "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_message $BLUE "📋 查看SwanLab-Dashboard日志"
    echo "=================================================="

    if [ "$service" = "all" ]; then
        print_message $GREEN "显示所有服务日志（最后${tail}行）"
        docker-compose logs --tail="$tail" $follow $since
    else
        print_message $GREEN "显示 $service 服务日志（最后${tail}行）"
        docker-compose logs --tail="$tail" $follow $since $service
    fi
}

main "$@"