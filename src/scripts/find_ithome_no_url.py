import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()
today = '2026-05-19'
row = c.execute("""
    SELECT title, url, original_source FROM items
    WHERE DATE(created_at) = ? AND original_source = 'ithome'
    AND (url IS NULL OR url = '')
    LIMIT 5
""", (today,)).fetchone()
if row:
    print(f"IT之家无链接: 标题=[{row[0]}] URL=[{row[1]}]")
else:
    print("没找到IT之家无链接的条目，可能已修复")
