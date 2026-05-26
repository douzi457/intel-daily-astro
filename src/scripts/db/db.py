"""数据库操作层"""
import sqlite3, hashlib, os
from datetime import datetime, date

# 动态定位 DB 路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'intel.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if os.path.exists(schema_path):
        schema = open(schema_path, encoding='utf-8').read()
        with get_conn() as conn:
            conn.executescript(schema)
    
    # 动态检查并补全列 (针对 2026 升级)
    with get_conn() as conn:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(items)").fetchall()]
        if 'ai_summary' not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN ai_summary TEXT")
        if 'en_title' not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN en_title TEXT")
        if 'en_summary' not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN en_summary TEXT")
        if 'zh_title' not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN zh_title TEXT")
        if 'category' not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN category TEXT DEFAULT '其他'")

        # 迁移：UNIQUE(hash) → UNIQUE(hash, date_key)，支持跨日去重
        schema_check = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='items'").fetchone()
        if schema_check and 'UNIQUE(hash)' in schema_check[0] and 'date_key' not in schema_check[0].split('UNIQUE')[1]:
            conn.executescript("""
                CREATE TABLE items_new (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    title           TEXT NOT NULL,
                    url             TEXT,
                    description     TEXT,
                    source_type     TEXT NOT NULL DEFAULT 'unknown',
                    original_source TEXT,
                    hot_value       REAL DEFAULT 0,
                    score           REAL DEFAULT 0,
                    frequency       REAL DEFAULT 1,
                    pub_time        TEXT,
                    date_key        TEXT NOT NULL,
                    hash            TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    ai_summary      TEXT,
                    comments        INTEGER,
                    en_title        TEXT,
                    en_summary      TEXT,
                    zh_title        TEXT,
                    UNIQUE(hash, date_key)
                );
                INSERT OR IGNORE INTO items_new SELECT * FROM items;
                DROP TABLE items;
                ALTER TABLE items_new RENAME TO items;
                CREATE INDEX IF NOT EXISTS idx_date_key ON items(date_key);
                CREATE INDEX IF NOT EXISTS idx_source ON items(source_type);
                CREATE INDEX IF NOT EXISTS idx_pub_time ON items(pub_time);
            """)

        conn.commit()

def _hash(title, url=''):
    s = f"{title}|{url}".encode('utf-8')
    return hashlib.md5(s).hexdigest()

def upsert_item(item, date_key):
    """写入单条item，同一天内去重，返回 (added, skipped)"""
    title = item.get('title', '')
    url   = item.get('url', '')
    h     = _hash(title, url)
    now   = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.execute("SELECT id FROM items WHERE hash = ? AND date_key = ?", (h, date_key))
        if cur.fetchone():
            return 0, 1  # 同一天已存在，跳过
        
        conn.execute("""
            INSERT INTO items (title,url,description,source_type,original_source,
                               hot_value,score,frequency,pub_time,date_key,hash,created_at,
                               ai_summary, en_title, en_summary, zh_title, category)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            title, url,
            item.get('description','') or item.get('desc',''),
            item.get('source_type','unknown'),
            item.get('original_source',''),
            item.get('hot_value',0),
            item.get('score',0),
            item.get('frequency',1),
            item.get('time','') or item.get('pub_time',''),
            date_key, h, now,
            item.get('ai_summary', ''),
            item.get('en_title', ''),
            item.get('en_summary', ''),
            item.get('zh_title', ''),
            item.get('category', '其他')
        ))
        conn.commit()
        return 1, 0

def get_items_by_date(date_key):
    """获取指定日期的所有数据"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM items
            WHERE date_key = ?
            ORDER BY hot_value DESC, score DESC
        """, (date_key,)).fetchall()
        return [dict(r) for r in rows]

def get_items_range(start_date, end_date):
    """获取日期范围内的数据"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM items
            WHERE date_key BETWEEN ? AND ?
            ORDER BY date_key, hot_value DESC
        """, (start_date, end_date)).fetchall()
        return [dict(r) for r in rows]

def get_all_dates():
    """获取有数据的日期列表"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT DISTINCT date_key, COUNT(*) as cnt
            FROM items
            GROUP BY date_key
            ORDER BY date_key DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_stats(date_key):
    """获取某天的统计"""
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM daily_stats WHERE date_key = ?", (date_key,)).fetchone()
        return dict(r) if r else None

def upsert_stats(date_key, total):
    with get_conn() as conn:
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO daily_stats (date_key,total,collected_at)
            VALUES (?,?,?)
            ON CONFLICT(date_key) DO UPDATE SET total=?, collected_at=?
        """, (date_key,total,now,total,now))
        conn.commit()

def log_collect(source, added, skipped, note=''):
    with get_conn() as conn:
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO collect_log (run_at,source,added,skipped,note)
            VALUES (?,?,?,?,?)
        """, (now, source, added, skipped, note))
        conn.commit()

def get_recent_collects(limit=20):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM collect_log ORDER BY run_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

# ── Source Health Monitoring ──

def init_source_health_table():
    """创建 source_health 表（如果不存在）"""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS source_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_key TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'unknown',
                items_found INTEGER DEFAULT 0,
                items_added INTEGER DEFAULT 0,
                error_message TEXT,
                duration_ms INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_health_date
            ON source_health(date_key)
        """)
        conn.commit()

def record_source_health(date_key, source, status, items_found=0, items_added=0, error_message='', duration_ms=0):
    """记录单个来源的采集健康状态"""
    now = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO source_health (date_key, source, status, items_found, items_added, error_message, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_key, source, status, items_found, items_added, error_message[:500], duration_ms, now))
        conn.commit()

def get_source_health(date_key=None, limit=30):
    """获取来源健康状态，可按日期筛选"""
    with get_conn() as conn:
        if date_key:
            rows = conn.execute("""
                SELECT * FROM source_health
                WHERE date_key = ?
                ORDER BY source
            """, (date_key,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM source_health
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_source_success_rates(days=7):
    """获取各来源近 N 天的成功率统计"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT
                source,
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                SUM(items_found) as total_items_found,
                SUM(items_added) as total_items_added,
                ROUND(AVG(duration_ms)) as avg_duration_ms
            FROM source_health
            WHERE date_key >= date('now', ? || ' days', '+8 hours')
            GROUP BY source
            ORDER BY source
        """, (f'-{days}',)).fetchall()
        return [dict(r) for r in rows]

# 初始化
init_db()
init_source_health_table()
