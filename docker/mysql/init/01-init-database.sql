-- SwanLab-Dashboard MySQL初始化脚本
-- 此脚本在MySQL容器首次启动时自动执行

-- 创建SwanLab云端数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS swanlab_cloud
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 创建SwanLab用户（如果不存在）
CREATE USER IF NOT EXISTS 'swanlab_user'@'%' IDENTIFIED BY 'swanlab_user_456';

-- 授予权限
GRANT ALL PRIVILEGES ON swanlab_cloud.* TO 'swanlab_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用SwanLab数据库
USE swanlab_cloud;

-- 创建云端项目表
CREATE TABLE IF NOT EXISTS cloud_projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    workspace VARCHAR(100) NOT NULL,
    owner VARCHAR(100) NOT NULL,
    visibility VARCHAR(20) DEFAULT 'private',
    experiment_count INT DEFAULT 0,
    settings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_workspace (workspace),
    INDEX idx_owner (owner),
    UNIQUE KEY unique_workspace_name (workspace, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建云端实验表
CREATE TABLE IF NOT EXISTS cloud_experiments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    status INT DEFAULT 0,
    visibility BOOLEAN DEFAULT TRUE,
    sort_order INT NOT NULL,
    light_color VARCHAR(20),
    dark_color VARCHAR(20),
    pinned_opened BOOLEAN DEFAULT TRUE,
    hidden_opened BOOLEAN DEFAULT FALSE,
    settings TEXT,
    version VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    finished_at TIMESTAMP NULL,

    INDEX idx_project (project_id),
    INDEX idx_run_id (run_id),
    INDEX idx_status (status),
    UNIQUE KEY unique_project_name (project_id, name),
    UNIQUE KEY unique_project_sort (project_id, sort_order),
    CONSTRAINT check_sort_order CHECK (sort_order >= 0),
    FOREIGN KEY (project_id) REFERENCES cloud_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建云端命名空间表
CREATE TABLE IF NOT EXISTS cloud_namespaces (
    id INT PRIMARY KEY AUTO_INCREMENT,
    experiment_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    sort_order INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_experiment (experiment_id),
    UNIQUE KEY unique_experiment_name (experiment_id, name),
    FOREIGN KEY (experiment_id) REFERENCES cloud_experiments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建云端图表表
CREATE TABLE IF NOT EXISTS cloud_charts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    experiment_id INT NOT NULL,
    chart_key VARCHAR(255) NOT NULL,
    chart_type VARCHAR(50) NOT NULL,
    reference VARCHAR(20) NOT NULL,
    config TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_experiment (experiment_id),
    INDEX idx_chart_key (chart_key),
    UNIQUE KEY unique_experiment_key (experiment_id, chart_key),
    FOREIGN KEY (experiment_id) REFERENCES cloud_experiments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建云端标签表
CREATE TABLE IF NOT EXISTS cloud_tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    experiment_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    tag_type VARCHAR(50) NOT NULL,
    folder VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_experiment (experiment_id),
    INDEX idx_name (name),
    FOREIGN KEY (experiment_id) REFERENCES cloud_experiments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建云端数据源表
CREATE TABLE IF NOT EXISTS cloud_sources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tag_id INT NOT NULL,
    chart_id INT NOT NULL,
    error_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_tag (tag_id),
    INDEX idx_chart (chart_id),
    FOREIGN KEY (tag_id) REFERENCES cloud_tags(id) ON DELETE CASCADE,
    FOREIGN KEY (chart_id) REFERENCES cloud_charts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建云端显示配置表
CREATE TABLE IF NOT EXISTS cloud_displays (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chart_id INT NOT NULL,
    namespace_id INT NOT NULL,
    sort_order INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_chart (chart_id),
    INDEX idx_namespace (namespace_id),
    FOREIGN KEY (chart_id) REFERENCES cloud_charts(id) ON DELETE CASCADE,
    FOREIGN KEY (namespace_id) REFERENCES cloud_namespaces(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入示例数据（可选）
INSERT IGNORE INTO cloud_projects (id, name, description, workspace, owner, visibility) VALUES
(1, 'demo_project', 'Demo project for testing', 'default', 'admin', 'public');

-- 显示创建的表
SHOW TABLES;

-- 显示权限
SHOW GRANTS FOR 'swanlab_user'@'%';