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
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "🔄 Initializing MySQL database..."
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
    echo "✅ MySQL initialized"
fi

# 创建最小的nginx配置
echo "📝 Creating simple nginx config..."
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
        listen 80 default_server;
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

    cat > /etc/clickhouse-server/users.xml << 'EOF'
<?xml version="1.0"?>
<clickhouse>
    <profiles>
        <default>
            <max_memory_usage>10000000000</max_memory_usage>
        </default>
    </profiles>
    <users>
        <default>
            <password></password>
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

echo "🚀 Starting supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf