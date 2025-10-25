#!/bin/bash
set -e

echo "Starting SwanLab All-in-One Container..."

# 初始化MySQL数据目录
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "Initializing MySQL database..."
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
    
    # 启动MySQL临时实例进行初始化
    mysqld --user=mysql --skip-networking --socket=/tmp/mysql_init.sock &
    MYSQL_PID=$!
    
    # 等待MySQL启动
    while ! mysqladmin ping --socket=/tmp/mysql_init.sock --silent; do
        sleep 1
    done
    
    # 执行初始化SQL
    mysql --socket=/tmp/mysql_init.sock << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
EOF
    
    # 如果有初始化SQL文件，执行它们
    for f in /docker-entrypoint-initdb.d/*.sql; do
        if [ -f "$f" ]; then
            echo "Executing $f"
            mysql --socket=/tmp/mysql_init.sock "${MYSQL_DATABASE}" < "$f"
        fi
    done
    
    # 停止临时MySQL实例
    kill $MYSQL_PID
    wait $MYSQL_PID
    echo "MySQL initialization completed."
fi

# 初始化ClickHouse数据目录
if [ ! -d "/var/lib/clickhouse" ]; then
    echo "Initializing ClickHouse..."
    mkdir -p /var/lib/clickhouse /var/log/clickhouse-server
    chown -R clickhouse:clickhouse /var/lib/clickhouse /var/log/clickhouse-server
fi

# 初始化Redis数据目录
mkdir -p /var/lib/redis
chown -R redis:redis /var/lib/redis

# 初始化MinIO数据目录
mkdir -p /data/minio
chown -R root:root /data/minio

# 创建日志目录
mkdir -p /var/log/{mysql,clickhouse-server,redis,nginx,minio,fluent-bit,supervisor}

# 设置权限
chown -R mysql:mysql /var/lib/mysql /var/log/mysql
chown -R clickhouse:clickhouse /var/lib/clickhouse /var/log/clickhouse-server
chown -R redis:redis /var/lib/redis /var/log/redis
chown -R root:root /var/log/{nginx,minio,fluent-bit,supervisor}

# 等待网络就绪
echo "Waiting for network to be ready..."
sleep 2

# 启动supervisord来管理所有服务
echo "Starting all services with supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf