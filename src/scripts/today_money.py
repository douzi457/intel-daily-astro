import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date

c = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")

# 找今天可商业化利用的情报
sources = ('producthunt', 'github', 'reddit/LocalLLaMA', '36kr', 'v2ex', 'hackernews')
rows = c.execute("""
    SELECT title, url, original_source, description 
    FROM items 
    WHERE DATE(created_at) = ?
    AND original_source IN ({})
    AND url IS NOT NULL AND url != ''
    ORDER BY ROWID DESC
""".format(','.join('?' * len(sources))), [str(date.today())] + list(sources)).fetchall()

print(f"=== 今日可商业化情报 ({len(rows)}条) ===\n")
for title, url, src, desc in rows:
    d = (desc or '')[:80]
    print(f"[{src[:20]:<20}] {title[:65]}")
    if d:
        print(f"                    {d}")
    print(f"                    {url}")
    print()

c.close()