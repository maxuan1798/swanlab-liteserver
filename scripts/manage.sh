#!/bin/bash
# SwanLab-Server Docker管理脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

show_help() {
    cat << EOF
SwanLab-Dashboard Docker管理工具

用法: $0 <命令> [选项]

命令:
  start                启动所有服务
  stop                 停止所有服务
  restart              重启所有服务
  logs                 查看日志
  status               查看服务状态
  ps                   查看容器状态
  exec                 进入容器
  backup               备份数据
  restore              恢复数据
  cleanup              清理未使用的资源
  update               更新服务
  init-mysql           初始化MySQL数据库
  test                 运行测试

管理选项:
  --production         使用生产环境配置
  --dev                使用开发环境配置（默认）
  -h, --help           显示帮助信息

示例:
  $0 start --production     # 启动生产环境
  $0 logs mysql -f          # 跟踪MySQL日志
  $0 exec swanlab-dashboard # 进入Dashboard容器
  $0 backup --output backup.tar.gz
  $0 test api                # 运行API测试

EOF
}

# 检查Docker环境
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_message $RED "❌ Docker未安装"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "❌ Docker Compose未安装"
        exit 1
    fi
}

# 启动服务
start_services() {
    local production=${1:-false}

    if [ "$production" = true ]; then
        ./scripts/start.sh --production
    else
        ./scripts/start.sh
    fi
}

# 停止服务
stop_services() {
    ./scripts/stop.sh "$@"
}

# 重启服务
restart_services() {
    local production=${1:-false}

    if [ "$production" = true ]; then
        ./scripts/restart.sh --production
    else
        ./scripts/restart.sh
    fi
}

# 查看日志
view_logs() {
    shift # 移除 'logs' 命令
    ./scripts/logs.sh "$@"
}

# 查看服务状态
show_status() {
    print_message $BLUE "📊 SwanLab-Dashboard服务状态"
    echo "=================================================="

    docker-compose ps

    echo
    print_message $BLUE "🔗 连接信息:"
    print_message $GREEN "  SwanLab-Dashboard: http://localhost:5173"
    print_message $GREEN "  MySQL: localhost:3306"
    print_message $GREEN "  Redis: localhost:6379"

    # 检查服务健康状态
    echo
    print_message $BLUE "🏥 健康检查:"

    # 检查Dashboard
    if curl -sf http://localhost:5173/api/v1/cloud/health > /dev/null 2>&1; then
        print_message $GREEN "  ✅ SwanLab-Dashboard: 健康"
    else
        print_message $RED "  ❌ SwanLab-Dashboard: 不可访问"
    fi

    # 检查MySQL
    if docker-compose exec -T mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
        print_message $GREEN "  ✅ MySQL: 健康"
    else
        print_message $RED "  ❌ MySQL: 不可访问"
    fi
}

# 进入容器
exec_container() {
    local service=${2:-swanlab-dashboard}
    local shell=${3:-/bin/bash}

    print_message $BLUE "🚪 进入 $service 容器..."

    # 检查容器是否在运行
    if ! docker-compose ps | grep -q "$service.*Up"; then
        print_message $RED "❌ 容器 $service 未运行"
        exit 1
    fi

    # 尝试bash，如果失败则尝试sh
    if ! docker-compose exec "$service" bash -c "exit" 2>/dev/null; then
        shell="/bin/sh"
    fi

    docker-compose exec "$service" "$shell"
}

# 备份数据
backup_data() {
    local output=${2:-"swanlab-backup-$(date +%Y%m%d_%H%M%S).tar.gz"}

    print_message $BLUE "💾 备份SwanLab-Dashboard数据..."

    # 创建备份目录
    local backup_dir="/tmp/swanlab-backup-$$"
    mkdir -p "$backup_dir"

    # 备份MySQL数据
    print_message $YELLOW "备份MySQL数据..."
    docker-compose exec -T mysql mysqldump \
        --user=root \
        --password="${MYSQL_ROOT_PASSWORD:-swanlab123}" \
        --single-transaction \
        --routines \
        --triggers \
        swanlab_cloud > "$backup_dir/mysql-dump.sql"

    # 备份应用数据
    print_message $YELLOW "备份应用数据..."
    docker cp $(docker-compose ps -q swanlab-dashboard):/app/data "$backup_dir/app-data" 2>/dev/null || true

    # 备份配置文件
    print_message $YELLOW "备份配置文件..."
    cp -r .env "$backup_dir/" 2>/dev/null || true
    cp -r docker/ "$backup_dir/" 2>/dev/null || true

    # 创建压缩包
    print_message $YELLOW "创建备份文件..."
    tar -czf "$output" -C "$backup_dir" .

    # 清理临时目录
    rm -rf "$backup_dir"

    print_message $GREEN "✅ 备份完成: $output"
}

# 恢复数据
restore_data() {
    local backup_file=${2}

    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        print_message $RED "❌ 请指定有效的备份文件"
        exit 1
    fi

    print_message $BLUE "🔄 恢复SwanLab-Dashboard数据..."
    print_message $YELLOW "⚠️  此操作将覆盖现有数据，请确认继续"
    read -p "继续恢复吗？ (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message $YELLOW "取消恢复操作"
        exit 0
    fi

    # 解压备份文件
    local restore_dir="/tmp/swanlab-restore-$$"
    mkdir -p "$restore_dir"
    tar -xzf "$backup_file" -C "$restore_dir"

    # 恢复MySQL数据
    if [ -f "$restore_dir/mysql-dump.sql" ]; then
        print_message $YELLOW "恢复MySQL数据..."
        docker-compose exec -T mysql mysql \
            --user=root \
            --password="${MYSQL_ROOT_PASSWORD:-swanlab123}" \
            swanlab_cloud < "$restore_dir/mysql-dump.sql"
    fi

    # 恢复应用数据
    if [ -d "$restore_dir/app-data" ]; then
        print_message $YELLOW "恢复应用数据..."
        docker cp "$restore_dir/app-data" $(docker-compose ps -q swanlab-dashboard):/app/
    fi

    # 清理临时目录
    rm -rf "$restore_dir"

    print_message $GREEN "✅ 恢复完成"
}

# 清理资源
cleanup_resources() {
    print_message $BLUE "🧹 清理Docker资源..."

    # 停止服务
    docker-compose down

    # 清理未使用的镜像
    print_message $YELLOW "清理未使用的镜像..."
    docker image prune -f

    # 清理未使用的网络
    print_message $YELLOW "清理未使用的网络..."
    docker network prune -f

    # 清理未使用的卷（可选）
    read -p "是否清理未使用的数据卷？这将删除所有数据 (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message $YELLOW "清理未使用的数据卷..."
        docker volume prune -f
    fi

    print_message $GREEN "✅ 清理完成"
}

# 更新服务
update_services() {
    print_message $BLUE "🔄 更新SwanLab-Dashboard服务..."

    # 拉取最新镜像
    print_message $YELLOW "拉取最新镜像..."
    docker-compose pull

    # 重新构建自定义镜像
    print_message $YELLOW "重新构建应用镜像..."
    docker-compose build --no-cache swanlab-dashboard

    # 重启服务
    print_message $YELLOW "重启服务..."
    docker-compose down
    docker-compose up -d

    print_message $GREEN "✅ 更新完成"
}

# 初始化MySQL
init_mysql() {
    print_message $BLUE "🗄️  初始化MySQL数据库..."

    # 检查MySQL是否运行
    if ! docker-compose ps | grep -q "mysql.*Up"; then
        print_message $RED "❌ MySQL容器未运行，请先启动服务"
        exit 1
    fi

    # 执行初始化脚本
    if [ -f "docker/mysql/init/01-init-database.sql" ]; then
        print_message $YELLOW "执行数据库初始化脚本..."
        docker-compose exec -T mysql mysql \
            --user=root \
            --password="${MYSQL_ROOT_PASSWORD:-swanlab123}" \
            < docker/mysql/init/01-init-database.sql

        print_message $GREEN "✅ MySQL初始化完成"
    else
        print_message $RED "❌ 未找到初始化脚本"
    fi
}

# 运行测试
run_tests() {
    local test_type=${2:-all}

    print_message $BLUE "🧪 运行测试..."

    case $test_type in
        api)
            print_message $YELLOW "运行API测试..."
            python test/test_cloud_api.py
            ;;
        unit)
            print_message $YELLOW "运行单元测试..."
            docker-compose exec swanlab-dashboard python -m pytest
            ;;
        integration)
            print_message $YELLOW "运行集成测试..."
            # 运行集成测试
            ;;
        all|*)
            print_message $YELLOW "运行所有测试..."
            python test/test_cloud_api.py
            ;;
    esac

    print_message $GREEN "✅ 测试完成"
}

# 主函数
main() {
    # 检查Docker环境
    check_docker

    # 解析全局参数
    local production=false
    local command=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --production)
                production=true
                shift
                ;;
            --dev)
                production=false
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            start|stop|restart|logs|status|ps|exec|backup|restore|cleanup|update|init-mysql|test)
                command=$1
                break
                ;;
            *)
                print_message $RED "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    if [ -z "$command" ]; then
        show_help
        exit 1
    fi

    # 执行命令
    case $command in
        start)
            start_services $production
            ;;
        stop)
            shift
            stop_services "$@"
            ;;
        restart)
            restart_services $production
            ;;
        logs)
            view_logs "$@"
            ;;
        status|ps)
            show_status
            ;;
        exec)
            exec_container "$@"
            ;;
        backup)
            backup_data "$@"
            ;;
        restore)
            restore_data "$@"
            ;;
        cleanup)
            cleanup_resources
            ;;
        update)
            update_services
            ;;
        init-mysql)
            init_mysql
            ;;
        test)
            run_tests "$@"
            ;;
        *)
            print_message $RED "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
