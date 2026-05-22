"""Delete and re-collect garbled sources: bilibili, ithome, v2ex"""
import subprocess, json, time, sys
from pathlib import Path
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
from db.db import get_conn

WORKSPACE    = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
SKILLS_DIR   = Path(r"C:\Users\douzi457\.qclaw\workspace\skills")
FETCH_SCRIPT = SKILLS_DIR / "news-aggregator-skill" / "scripts" / "fetch_news.py"

SOURCES = ['bilibili', 'ithome', 'v2ex']

def run_py(script, *args):
    cmd = [sys.executable, str(script)] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                          encoding='utf-8', errors='replace')
        if r.returncode == 0 and r.stdout.strip():
            try:
                return json.loads(r.stdout.strip())
            except json.JSONDecodeError as e:
                print(f"  [WARN] JSON parse failed: {e}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    return None

today = date.today().strftime("%Y-%m-%d")
new_total = 0

# 1. Delete old garbled data
for src in SOURCES:
    with get_conn() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM items WHERE original_source = ?", (src,))
        cnt = cur.fetchone()[0]
        conn.execute("DELETE FROM items WHERE original_source = ?", (src,))
        print(f"[DEL] {src}: {cnt} items removed")

# 2. Re-collect with correct encoding
for src in SOURCES:
    print(f"[SRC] Collecting {src}...")
    res = run_py(FETCH_SCRIPT, "--source", src, "--limit", "10")
    added = 0
    if isinstance(res, list):
        with get_conn() as conn:
            for it in res:
                it['source_type'] = 'news_aggregator'
                it['original_source'] = src
                item = {
                    'title':          it.get('title', ''),
                    'url':            it.get('url', '') or it.get('link', ''),
                    'description':    it.get('description', '') or it.get('desc', ''),
                    'pub_time':       it.get('pub_time') or it.get('time', ''),
                    'hot_value':      it.get('hot_value', 0),
                    'frequency':      it.get('frequency', 1),
                    'source_type':    'news_aggregator',
                    'original_source': src,
                }
                conn.execute("""
                    INSERT OR IGNORE INTO items
                    (title, url, description, pub_time, hot_value, frequency,
                     source_type, original_source, date_key, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (item['title'], item['url'], item['description'],
                      item['pub_time'], item['hot_value'], item['frequency'],
                      item['source_type'], item['original_source'], today))
                added += 1
        print(f"  -> Added {added} items")
        new_total += added
    else:
        print(f"  -> No data returned")
    time.sleep(0.5)

print(f"\n[DONE] Total re-collected: {new_total} items")
