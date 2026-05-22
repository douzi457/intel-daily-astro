"""重新采集 bilibili, ithome, v2ex（使用 upsert_item 正确写入）"""
import subprocess, json, time, sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn, upsert_item

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

for src in SOURCES:
    # 1. 删除旧数据
    with get_conn() as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM items WHERE original_source = ?", (src,)).fetchone()[0]
        conn.execute("DELETE FROM items WHERE original_source = ?", (src,))
        conn.commit()
    print(f"[DEL] {src}: {cnt} items deleted")

    # 2. 重新采集
    print(f"[SRC] Re-collecting {src}...")
    res = run_py(FETCH_SCRIPT, "--source", src, "--limit", "10")
    added = skipped = 0
    if isinstance(res, list):
        for it in res:
            it['source_type'] = 'news_aggregator'
            it['original_source'] = src
            a, s = upsert_item(it, today)
            added += a; skipped += s
        print(f"  -> added={added}, skipped={skipped}")
    else:
        print(f"  -> No data returned")
    time.sleep(0.5)

# 验证
print("\n[VERIFY]")
with get_conn() as conn:
    for src in SOURCES:
        cnt = conn.execute("SELECT COUNT(*) FROM items WHERE original_source = ?", (src,)).fetchone()[0]
        title = conn.execute("SELECT title FROM items WHERE original_source = ? LIMIT 1", (src,)).fetchone()
        print(f"  {src}: {cnt} items | sample: {title[0][:40] if title else 'NONE'}")
