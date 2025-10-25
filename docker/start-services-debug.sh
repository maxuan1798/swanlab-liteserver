#!/bin/bash
set -e

echo "🚀 Starting SwanLab All-in-One Container (Debug Mode)..."

# 显示系统信息
echo "📊 System Information:"
echo "- Container OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo "- Available services:"
which mysql mysqld 2>/dev/null && echo "  ✅ MySQL installed" || echo "  ❌ MySQL not found"
which clickhouse-server 2>/dev/null && echo "  ✅ ClickHouse installed" || echo "  ❌ ClickHouse not found"
which redis-server 2>/dev/null && echo "  ✅ Redis installed" || echo "  ❌ Redis not found"
which nginx 2>/dev/null && echo "  ✅ Nginx installed" || echo "  ❌ Nginx not found"
which minio 2>/dev/null && echo "  ✅ MinIO installed" || echo "  ❌ MinIO not found"

# 创建必要的目录和设置权限
echo "📁 Creating directories..."
mkdir -p /var/lib/mysql /var/log/mysql /var/lib/redis /var/log/redis
mkdir -p /var/lib/clickhouse /var/log/clickhouse-server /etc/clickhouse-server
mkdir -p /var/run/clickhouse-server
mkdir -p /data/minio /var/log/minio
mkdir -p /app/data /app/logs /var/log/supervisor
mkdir -p /var/log/nginx /var/run/nginx

# 检查配置文件
echo "🔍 Checking configuration files..."
echo "- Supervisor config: $(ls -la /etc/supervisor/conf.d/supervisord.conf 2>/dev/null || echo 'NOT FOUND')"
echo "- Nginx config: $(ls -la /etc/nginx/nginx.conf 2>/dev/null || echo 'NOT FOUND')"

# 测试Nginx配置
echo "🔧 Testing Nginx configuration..."
if nginx -t 2>/dev/null; then
    echo "  ✅ Nginx config is valid"
else
    echo "  ❌ Nginx config has errors:"
    nginx -t 2>&1 || true
fi

# 初始化ClickHouse目录
if [ ! -d "/var/lib/clickhouse/data" ]; then
    echo "🔄 Initializing ClickHouse directories..."
    mkdir -p /var/lib/clickhouse/{data,metadata,tmp,user_files,access}
    chown -R clickhouse:clickhouse /var/lib/clickhouse /var/log/clickhouse-server /etc/clickhouse-server 2>/dev/null || true
fi

# 初始化MySQL (如果需要)
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "🔄 Initializing MySQL database..."
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
fi

# 设置权限
echo "🔐 Setting permissions..."
chown -R mysql:mysql /var/lib/mysql /var/log/mysql 2>/dev/null || true
chown -R clickhouse:clickhouse /var/lib/clickhouse /var/log/clickhouse-server /var/run/clickhouse-server 2>/dev/null || true
chown -R redis:redis /var/lib/redis /var/log/redis 2>/dev/null || true

# 创建基本的ClickHouse配置（如果不存在）
if [ ! -f "/etc/clickhouse-server/config.xml" ]; then
    echo "📝 Creating basic ClickHouse config..."
    cat > /etc/clickhouse-server/config.xml << 'EOF'
<?xml version="1.0"?>
<clickhouse>
    <logger>
        <level>information</level>
        <log>/var/log/clickhouse-server/clickhouse-server.log</log>
        <errorlog>/var/log/clickhouse-server/clickhouse-server.err.log</errorlog>
        <size>1000M</size>
        <count>10</count>
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
    chown clickhouse:clickhouse /etc/clickhouse-server/config.xml
fi

# 创建基本的ClickHouse用户配置（如果不存在）
if [ ! -f "/etc/clickhouse-server/users.xml" ]; then
    echo "📝 Creating basic ClickHouse users config..."
    cat > /etc/clickhouse-server/users.xml << 'EOF'
<?xml version="1.0"?>
<clickhouse>
    <profiles>
        <default>
            <max_memory_usage>10000000000</max_memory_usage>
            <use_uncompressed_cache>0</use_uncompressed_cache>
            <load_balancing>random</load_balancing>
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
                <queries>0</queries>
                <errors>0</errors>
                <result_rows>0</result_rows>
                <read_rows>0</read_rows>
                <execution_time>0</execution_time>
            </interval>
        </default>
    </quotas>
</clickhouse>
EOF
    chown clickhouse:clickhouse /etc/clickhouse-server/users.xml
fi

echo "🚀 Starting supervisord to manage all services..."
echo "📋 Services to be started:"
echo "  1. MySQL (priority 100)"
echo "  2. Redis (priority 200)" 
echo "  3. ClickHouse (priority 300)"
echo "  4. MinIO (priority 400)"
echo "  5. Nginx (priority 500)"
echo "  6. SwanLab (priority 600)"

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf