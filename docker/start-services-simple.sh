#!/bin/bash
set -e

echo "🚀 Starting SwanLab All-in-One Container (Simple Mode)..."

# 显示系统信息
echo "📊 System Information:"
echo "- Container OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "- Available Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "- Available Disk: $(df -h / | tail -1 | awk '{print $4}')"

# 检查服务是否安装
echo "🔍 Checking installed services:"
command -v mysql >/dev/null 2>&1 && echo "  ✅ MySQL" || echo "  ❌ MySQL"
command -v clickhouse-server >/dev/null 2>&1 && echo "  ✅ ClickHouse" || echo "  ❌ ClickHouse" 
command -v redis-server >/dev/null 2>&1 && echo "  ✅ Redis" || echo "  ❌ Redis"
command -v nginx >/dev/null 2>&1 && echo "  ✅ Nginx" || echo "  ❌ Nginx"
command -v minio >/dev/null 2>&1 && echo "  ✅ MinIO" || echo "  ❌ MinIO"

# 创建必要的目录和设置权限
echo "📁 Creating directories..."
mkdir -p /var/lib/mysql /var/log/mysql 
mkdir -p /var/lib/redis /var/log/redis
mkdir -p /var/lib/clickhouse /var/log/clickhouse-server /etc/clickhouse-server
mkdir -p /var/run/clickhouse-server
mkdir -p /data/minio /var/log/minio
mkdir -p /app/data /app/logs 
mkdir -p /var/log/supervisor /var/run/supervisor
mkdir -p /var/log/nginx /var/run/nginx

# 设置基本权限
echo "🔐 Setting permissions..."
chown -R mysql:mysql /var/lib/mysql /var/log/mysql 2>/dev/null || true
chown -R redis:redis /var/lib/redis /var/log/redis 2>/dev/null || true

# 初始化MySQL (如果需要)
MYSQL_NEEDS_INIT=false
MYSQL_DATA_EXISTS=false

if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "🔄 MySQL data directory not found, initializing MySQL..."
    MYSQL_NEEDS_INIT=true

    # 初始化MySQL数据库
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
else
    echo "ℹ️  MySQL data directory exists, checking if SwanLab database is initialized..."
    MYSQL_DATA_EXISTS=true
fi

# 启动MySQL临时实例（用于初始化或迁移）
echo "🔧 Starting temporary MySQL instance..."
mysqld --user=mysql --datadir=/var/lib/mysql --skip-networking --socket=/var/run/mysqld/mysqld.sock &
MYSQL_PID=$!

# 等待MySQL启动（使用重试机制）
echo "⏳ Waiting for MySQL to be ready..."
for i in {1..30}; do
    if mysql -S /var/run/mysqld/mysqld.sock -u root -e "SELECT 1" >/dev/null 2>&1; then
        echo "✅ MySQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ MySQL failed to start in time"
        kill $MYSQL_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 设置环境变量默认值
export MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-swanlab_root_123}"
export MYSQL_DATABASE="${MYSQL_DATABASE:-swanlab_cloud}"
export MYSQL_USER="${MYSQL_USER:-swanlab_user}"
export MYSQL_PASSWORD="${MYSQL_PASSWORD:-swanlab_user_456}"
export CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"
export CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-password123}"

# 检查SwanLab数据库是否需要初始化
RUN_INIT_SCRIPTS=false
if [ "$MYSQL_NEEDS_INIT" = true ]; then
    echo "📝 New MySQL installation detected, running all initialization scripts..."
    RUN_INIT_SCRIPTS=true
elif [ "$MYSQL_DATA_EXISTS" = true ]; then
    # 检查SwanLab数据库是否存在
    if ! mysql -S /var/run/mysqld/mysqld.sock -u root -e "USE ${MYSQL_DATABASE}" 2>/dev/null; then
        echo "📝 SwanLab database '${MYSQL_DATABASE}' not found, running initialization scripts..."
        RUN_INIT_SCRIPTS=true
    else
        # 检查关键表是否存在
        TABLE_COUNT=$(mysql -S /var/run/mysqld/mysqld.sock -u root -D "${MYSQL_DATABASE}" -e "SHOW TABLES LIKE 'cloud_projects'" 2>/dev/null | wc -l)
        if [ "$TABLE_COUNT" -lt 2 ]; then
            echo "📝 SwanLab tables not found, running initialization scripts..."
            RUN_INIT_SCRIPTS=true
        else
            echo "✅ SwanLab database is already initialized, skipping init scripts"
            # 仍然检查api_keys表（可能是新增的）
            API_KEYS_EXISTS=$(mysql -S /var/run/mysqld/mysqld.sock -u root -D "${MYSQL_DATABASE}" -e "SHOW TABLES LIKE 'api_keys'" 2>/dev/null | wc -l)
            if [ "$API_KEYS_EXISTS" -lt 2 ]; then
                echo "📝 Running 02-add-api-keys-table.sql migration..."
                if [ -f "/docker-entrypoint-initdb.d/02-add-api-keys-table.sql" ]; then
                    eval "echo \"$(cat /docker-entrypoint-initdb.d/02-add-api-keys-table.sql)\"" | mysql -S /var/run/mysqld/mysqld.sock -u root
                    echo "✅ API keys table migration completed"
                fi
            fi
        fi
    fi
fi

# 执行初始化脚本
if [ "$RUN_INIT_SCRIPTS" = true ] && [ -d "/docker-entrypoint-initdb.d" ]; then
    echo "📝 Running MySQL initialization scripts..."
    for sql_file in /docker-entrypoint-initdb.d/*.sql; do
        if [ -f "$sql_file" ]; then
            echo "  - Executing: $(basename "$sql_file")"
            # 使用 eval echo 进行环境变量替换，然后传递给 mysql
            if eval "echo \"$(cat "$sql_file")\"" | mysql -S /var/run/mysqld/mysqld.sock -u root 2>&1; then
                echo "    ✅ Success: $(basename "$sql_file")"
            else
                echo "    ⚠️  Warning: $(basename "$sql_file") had errors (may be normal if already exists)"
            fi
        fi
    done
    echo "✅ MySQL initialization completed"
fi

# 停止临时MySQL实例
echo "🛑 Stopping temporary MySQL instance..."
kill $MYSQL_PID
wait $MYSQL_PID 2>/dev/null || true

# 使用nginx-all-in-one.conf配置
echo "📝 Copying nginx-all-in-one config..."
if [ -f "/app/docker/nginx/nginx-all-in-one.conf" ]; then
    cp /app/docker/nginx/nginx-all-in-one.conf /etc/nginx/nginx.conf
    echo "✅ Nginx config copied from nginx-all-in-one.conf"
else
    echo "⚠️  nginx-all-in-one.conf not found, using default config"
    # 如果找不到配置文件，使用简单的回退配置
    cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    server {
        listen 8800 default_server;
        server_name _;

        location /health {
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }

        location / {
            proxy_pass http://127.0.0.1:5173;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
EOF
fi

# 测试nginx配置
echo "🔧 Testing nginx configuration..."
if nginx -t 2>/dev/null; then
    echo "✅ Nginx config is valid"
else
    echo "❌ Nginx config has errors:"
    nginx -t
    exit 1
fi

# 初始化ClickHouse目录和配置
if [ ! -d "/var/lib/clickhouse/data" ]; then
    echo "🔄 Initializing ClickHouse..."
    mkdir -p /var/lib/clickhouse/{data,metadata,tmp,user_files,access}
    
    # 创建最小的ClickHouse配置
    cat > /etc/clickhouse-server/config.xml << 'EOF'
<?xml version="1.0"?>
<clickhouse>
    <logger>
        <level>warning</level>
        <log>/var/log/clickhouse-server/clickhouse-server.log</log>
        <errorlog>/var/log/clickhouse-server/clickhouse-server.err.log</errorlog>
    </logger>
    <http_port>8123</http_port>
    <tcp_port>9000</tcp_port>
    <listen_host>0.0.0.0</listen_host>
    <path>/var/lib/clickhouse/</path>
    <tmp_path>/var/lib/clickhouse/tmp/</tmp_path>
    <users_config>users.xml</users_config>
    <default_profile>default</default_profile>
    <default_database>default</default_database>
</clickhouse>
EOF

    cat > /etc/clickhouse-server/users.xml << EOF
<?xml version="1.0"?>
<clickhouse>
    <profiles>
        <default>
            <max_memory_usage>10000000000</max_memory_usage>
        </default>
    </profiles>
    <users>
        <default>
            <password>${CLICKHOUSE_PASSWORD}</password>
            <networks incl="networks" replace="replace">
                <ip>::/0</ip>
            </networks>
            <profile>default</profile>
            <quota>default</quota>
        </default>
    </users>
    <quotas>
        <default>
            <interval>
                <duration>3600</duration>
            </interval>
        </default>
    </quotas>
</clickhouse>
EOF

    # 设置所有ClickHouse相关目录的权限
    chown -R clickhouse:clickhouse /var/lib/clickhouse /var/log/clickhouse-server /etc/clickhouse-server /var/run/clickhouse-server 2>/dev/null || true
    echo "✅ ClickHouse initialized"
fi

# 确保ClickHouse权限正确（即使目录已存在）
echo "🔐 Setting ClickHouse permissions..."
chown -R clickhouse:clickhouse /var/lib/clickhouse /var/log/clickhouse-server /etc/clickhouse-server /var/run/clickhouse-server 2>/dev/null || true

# 始终更新ClickHouse用户密码（防止密码不一致）
echo "🔐 Updating ClickHouse password from environment..."
if [ -f "/etc/clickhouse-server/users.xml" ]; then
    cat > /etc/clickhouse-server/users.xml << EOF
<?xml version="1.0"?>
<clickhouse>
    <profiles>
        <default>
            <max_memory_usage>10000000000</max_memory_usage>
        </default>
    </profiles>
    <users>
        <default>
            <password>${CLICKHOUSE_PASSWORD}</password>
            <networks incl="networks" replace="replace">
                <ip>::/0</ip>
            </networks>
            <profile>default</profile>
            <quota>default</quota>
        </default>
    </users>
    <quotas>
        <default>
            <interval>
                <duration>3600</duration>
            </interval>
        </default>
    </quotas>
</clickhouse>
EOF
    chown clickhouse:clickhouse /etc/clickhouse-server/users.xml 2>/dev/null || true
    echo "✅ ClickHouse password updated"
fi

echo "🚀 Starting supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf