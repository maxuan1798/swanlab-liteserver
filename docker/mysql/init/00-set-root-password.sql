-- 设置MySQL root用户密码
-- 这个脚本会在MySQL第一次启动时执行

-- 设置root@localhost密码
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD:-swanlab_root_123}';

-- 创建root@%用户（如果不存在）并设置密码
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD:-swanlab_root_123}';

-- 授予所有权限
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

-- 刷新权限
FLUSH PRIVILEGES;