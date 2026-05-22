-- 情报系统数据库 schema
CREATE TABLE IF NOT EXISTS items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    url             TEXT,
    description     TEXT,
    source_type     TEXT NOT NULL DEFAULT 'unknown',
    original_source TEXT,
    hot_value       REAL DEFAULT 0,
    score           REAL DEFAULT 0,
    frequency       REAL DEFAULT 1,
    pub_time        TEXT,          -- ISO 8601 时间
    date_key        TEXT NOT NULL,  -- YYYY-MM-DD，用于按天查询
    hash            TEXT NOT NULL, -- 标题+URL 的 hash，用于去重
    created_at      TEXT NOT NULL,  -- 入库时间
    UNIQUE(hash)
);

CREATE INDEX IF NOT EXISTS idx_date_key ON items(date_key);
CREATE INDEX IF NOT EXISTS idx_source  ON items(source_type);
CREATE INDEX IF NOT EXISTS idx_pub_time ON items(pub_time);

-- 每日统计
CREATE TABLE IF NOT EXISTS daily_stats (
    date_key    TEXT PRIMARY KEY,
    total       INTEGER DEFAULT 0,
    collected_at TEXT NOT NULL
);

-- 采集日志
CREATE TABLE IF NOT EXISTS collect_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at      TEXT NOT NULL,
    source      TEXT,
    added       INTEGER DEFAULT 0,
    skipped     INTEGER DEFAULT 0,
    note        TEXT
);
