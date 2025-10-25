#!/bin/bash
set -e

echo "🚀 Starting SwanLab All-in-One Container..."

# 创建必要的目录和设置权限
mkdir -p /var/lib/mysql /var/log/mysql /var/lib/redis /var/log/redis
mkdir -p /var/lib/clickhouse /var/log/clickhouse-server
mkdir -p /data/minio /var/log/minio
mkdir -p /app/data /app/logs

# 初始化MySQL (如果需要)
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "Initializing MySQL database..."
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
fi

# 设置权限
chown -R mysql:mysql /var/lib/mysql /var/log/mysql 2>/dev/null || true
chown -R clickhouse:clickhouse /var/lib/clickhouse /var/log/clickhouse-server 2>/dev/null || true
chown -R redis:redis /var/lib/redis /var/log/redis 2>/dev/null || true

echo "Starting supervisord to manage all services..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf