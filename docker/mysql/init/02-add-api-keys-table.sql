-- SwanLab API Keys Table Migration
-- This script adds the api_keys table for platform-level API key management
-- Created: 2025-01-23

USE swanlab_cloud;

-- 创建 API Keys 表
CREATE TABLE IF NOT EXISTS api_keys (
    -- 主键：API Key 的唯一标识符
    id VARCHAR(36) PRIMARY KEY,

    -- API Key 名称和描述
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- API Key 公开标识符和密钥哈希
    key_id VARCHAR(32) UNIQUE NOT NULL,
    key_secret_hash VARCHAR(255) NOT NULL,
    key_secret_salt VARCHAR(255) NOT NULL,

    -- 权限范围: read_only, read_write, admin
    scope VARCHAR(20) NOT NULL DEFAULT 'read_write',
    permissions TEXT,  -- JSON format for fine-grained permissions

    -- 状态: active, inactive, revoked
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- 所有者信息（可选，用于用户级别的 API Key）
    owner_id VARCHAR(36) NULL,

    -- 速率限制 (请求数/小时)
    rate_limit INT NOT NULL DEFAULT 1000,

    -- 过期时间（NULL 表示永不过期）
    expires_at TIMESTAMP NULL,

    -- 使用统计
    last_used_at TIMESTAMP NULL,
    last_used_ip VARCHAR(50) NULL,
    usage_count INT NOT NULL DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_name (name),
    INDEX idx_key_id (key_id),
    INDEX idx_owner_id (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建 API Key 使用日志表（用于审计和速率限制）
CREATE TABLE IF NOT EXISTS api_key_usage_logs (
    -- 主键
    id VARCHAR(36) PRIMARY KEY,

    -- 外键：关联到 api_keys 表
    api_key_id VARCHAR(36) NOT NULL,

    -- 请求信息
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    ip_address VARCHAR(50) NULL,
    user_agent VARCHAR(500) NULL,

    -- 响应信息
    status_code INT NULL,
    response_time INT NULL,  -- in milliseconds

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_api_key_id (api_key_id),
    INDEX idx_api_key_created (api_key_id, created_at),

    -- 外键约束
    CONSTRAINT fk_usage_logs_api_key_id
        FOREIGN KEY (api_key_id)
        REFERENCES api_keys(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用于安全检查的存储过程
DELIMITER //

-- 检查 API Key 是否有效
CREATE PROCEDURE IF NOT EXISTS check_api_key_valid(
    IN p_key_id VARCHAR(32),
    OUT p_is_valid BOOLEAN,
    OUT p_owner_id VARCHAR(36)
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_expires_at TIMESTAMP;

    -- 查询 API Key 信息
    SELECT
        status,
        expires_at,
        owner_id
    INTO
        v_status,
        v_expires_at,
        p_owner_id
    FROM
        api_keys
    WHERE
        key_id = p_key_id;

    -- 检查状态和过期时间
    IF v_status = 'active' AND (v_expires_at IS NULL OR v_expires_at > NOW()) THEN
        SET p_is_valid = TRUE;
    ELSE
        SET p_is_valid = FALSE;
    END IF;
END //

-- 更新 API Key 使用统计
CREATE PROCEDURE IF NOT EXISTS update_api_key_usage(
    IN p_key_id VARCHAR(32),
    IN p_ip_address VARCHAR(50)
)
BEGIN
    UPDATE api_keys
    SET
        usage_count = usage_count + 1,
        last_used_at = NOW(),
        last_used_ip = COALESCE(p_ip_address, last_used_ip)
    WHERE
        key_id = p_key_id;
END //

DELIMITER ;

-- 显示创建的表结构
DESCRIBE api_keys;

-- 显示表的索引
SHOW INDEX FROM api_keys;