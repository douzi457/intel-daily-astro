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
        conn.commit()

def _hash(title, url=''):
    s = f"{title}|{url}".encode('utf-8')
    return hashlib.md5(s).hexdigest()

def upsert_item(item, date_key):
    """写入单条item，去重，返回 (added, skipped)"""
    title = item.get('title', '')
    url   = item.get('url', '')
    h     = _hash(title, url)
    now   = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.execute("SELECT id FROM items WHERE hash = ?", (h,))
        if cur.fetchone():
            return 0, 1  # 已存在，跳过
        
        conn.execute("""
            INSERT INTO items (title,url,description,source_type,original_source,
                               hot_value,score,frequency,pub_time,date_key,hash,created_at,
                               ai_summary, en_title, en_summary, zh_title)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
            item.get('zh_title', '')
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

# 初始化
init_db()
