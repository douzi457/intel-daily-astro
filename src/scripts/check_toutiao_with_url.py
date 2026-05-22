import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()
today = '2026-05-20'

rows = c.execute("SELECT title, url FROM items WHERE DATE(created_at)=? AND original_source='toutiao' AND url != '' LIMIT 10", (today,)).fetchall()
print(f"今天有URL的头条({len(rows)}条):")
for title, url in rows:
    print(f"  {title[:35]}")
    print(f"    → {url}")
    print()
