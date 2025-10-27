-- SwanLab-Dashboard MySQL AUTO_INCREMENT 修复脚本
-- 此脚本用于修复现有数据库中的 AUTO_INCREMENT 问题
-- 运行方式: mysql -u swanlab_user -p swanlab_cloud < 02-fix-auto-increment.sql

-- 使用SwanLab数据库
USE ${MYSQL_DATABASE:-swanlab_cloud};

-- 禁用外键检查以允许修改表结构
SET FOREIGN_KEY_CHECKS = 0;

-- 修复 cloud_runtime_info 表
-- 如果存在 id=0 的记录，更新为 id=1
UPDATE cloud_runtime_info SET id = 1 WHERE id = 0;
-- 添加 AUTO_INCREMENT
ALTER TABLE cloud_runtime_info MODIFY id INT AUTO_INCREMENT;

-- 修复 cloud_charts 表
-- 如果存在 id=0 的记录，更新为 id=1
UPDATE cloud_charts SET id = 1 WHERE id = 0;
-- 添加 AUTO_INCREMENT
ALTER TABLE cloud_charts MODIFY id INT AUTO_INCREMENT;

-- 修复 cloud_tags 表
-- 如果存在 id=0 的记录，更新为 id=1
UPDATE cloud_tags SET id = 1 WHERE id = 0;
-- 更新依赖表中的外键引用
UPDATE cloud_sources SET tag_id = 1 WHERE tag_id = 0;
-- 添加 AUTO_INCREMENT
ALTER TABLE cloud_tags MODIFY id INT AUTO_INCREMENT;

-- 修复 cloud_sources 表
-- 如果存在 id=0 的记录，更新为 id=1
UPDATE cloud_sources SET id = 1 WHERE id = 0;
-- 添加 AUTO_INCREMENT
ALTER TABLE cloud_sources MODIFY id INT AUTO_INCREMENT;

-- 修复 cloud_displays 表
-- 如果存在 id=0 的记录，更新为 id=1
UPDATE cloud_displays SET id = 1 WHERE id = 0;
-- 添加 AUTO_INCREMENT
ALTER TABLE cloud_displays MODIFY id INT AUTO_INCREMENT;

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 显示修复后的表状态
SELECT
    TABLE_NAME,
    AUTO_INCREMENT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '${MYSQL_DATABASE:-swanlab_cloud}'
AND TABLE_NAME LIKE 'cloud_%';

-- 显示修复后的记录示例
SELECT 'cloud_runtime_info' as table_name, id FROM cloud_runtime_info ORDER BY id DESC LIMIT 1;
SELECT 'cloud_charts' as table_name, id FROM cloud_charts ORDER BY id DESC LIMIT 1;
SELECT 'cloud_tags' as table_name, id FROM cloud_tags ORDER BY id DESC LIMIT 1;
SELECT 'cloud_sources' as table_name, id FROM cloud_sources ORDER BY id DESC LIMIT 1;
SELECT 'cloud_displays' as table_name, id FROM cloud_displays ORDER BY id DESC LIMIT 1;