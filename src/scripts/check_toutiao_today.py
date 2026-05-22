import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()
today = '2026-05-20'

rows = c.execute("""
    SELECT title, url FROM items
    WHERE DATE(created_at) = ? AND original_source = 'toutiao'
    LIMIT 10
""", (today,)).fetchall()

print(f"今日头条今天共 {c.execute('SELECT COUNT(*) FROM items WHERE DATE(created_at)=? AND original_source=?', (today,'toutiao')).fetchone()[0]} 条")
for title, url in rows:
    print(f"  [{url[:60] if url else 'NO_URL'}] {title[:40]}")
