import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date

c = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")

sources = ('producthunt', 'github', 'hackernews')
rows = c.execute("""
    SELECT title, url, original_source, description
    FROM items
    WHERE DATE(created_at) = ?
    AND original_source IN (?,?,?)
    AND url IS NOT NULL AND url != ''
    ORDER BY ROWID DESC
    LIMIT 40
""", (str(date.today()),) + sources).fetchall()

print(f"今日PH/GH/HN共 {len(rows)} 条")
print("="*50)
for title, url, src, desc in rows:
    print(f"[{src}] {title[:60]}")
    print(f"  {url}")
    if desc:
        print(f"  {desc[:80]}")
    print()

c.close()
