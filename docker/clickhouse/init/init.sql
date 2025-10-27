-- 创建数据库
CREATE DATABASE IF NOT EXISTS app;

-- 创建日志表
CREATE TABLE IF NOT EXISTS app.log (
    timestamp DateTime64(3),
    log_type String,
    run_id String,
    level String,
    epoch Nullable(UInt64),
    message String DEFAULT '',
    contents Array(String)
) ENGINE = MergeTree()
ORDER BY (run_id, timestamp);

-- 创建运行时信息表
CREATE TABLE IF NOT EXISTS app.runtime (
    timestamp DateTime64(3),
    log_type String,
    run_id String,
    python_version Nullable(String),
    platform Nullable(String),
    cuda_version Nullable(String),
    requirements Nullable(String),
    metadata Nullable(String),
    config Nullable(String),
    conda Nullable(String)
) ENGINE = MergeTree()
ORDER BY (run_id, timestamp);

-- 创建列信息表
CREATE TABLE IF NOT EXISTS app.column (
    timestamp DateTime64(3),
    log_type String,
    run_id String,
    column_id String,
    key Nullable(String),
    name Nullable(String),
    cls Nullable(String),
    typ Nullable(String),
    config Nullable(String),
    section_name Nullable(String),
    section_type Nullable(String),
    error Nullable(String),
    chart_type Nullable(String),
    y_range Nullable(String),
    chart_name Nullable(String),
    chart_index Nullable(Int32),
    metric_name Nullable(String),
    metric_color Nullable(String)
) ENGINE = MergeTree()
ORDER BY (run_id, column_id, timestamp);

-- 创建指标表（支持标量和媒体）
CREATE TABLE IF NOT EXISTS app.metric (
    timestamp DateTime64(3),
    log_type String,
    metric_type String,  -- 'scalar' or 'media'
    run_id String,
    column_id String,
    key Nullable(String),
    step Nullable(UInt64),
    epoch Nullable(UInt64),
    -- 标量字段
    value Nullable(Float64),
    -- 媒体字段
    chart_type Nullable(String),
    media_dir Nullable(String),
    file_count Nullable(UInt32),
    metric_data Array(String)
) ENGINE = MergeTree()
ORDER BY (run_id, column_id, step, timestamp)
SETTINGS allow_nullable_key = 1;

