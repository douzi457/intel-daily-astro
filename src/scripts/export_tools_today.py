import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date

c = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
rows = c.execute("""
    SELECT title, url, original_source, description, hot_value
    FROM items
    WHERE DATE(created_at) = ?
    AND original_source IN ('producthunt','github','hackernews')
    AND url IS NOT NULL AND url != ''
    ORDER BY original_source, hot_value DESC
""", (str(date.today()),)).fetchall()

print(f"今日数据：{len(rows)} 条")
print("="*60)

current_src = None
for title, url, src, desc, hv in rows:
    if src != current_src:
        current_src = src
        print(f"\n【{src}】")
    print(f"  {title[:50]}")
    print(f"  {url}")
    if desc:
        print(f"  简介：{desc[:80]}")
    print()

c.close()
