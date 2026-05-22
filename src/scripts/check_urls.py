import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()

today = '2026-05-19'
rows = c.execute(f"""
    SELECT original_source, source_type,
           SUM(CASE WHEN url IS NULL OR url = '' THEN 1 ELSE 0 END) as no_url,
           COUNT(*) as total
    FROM items
    WHERE DATE(created_at) = ?
    GROUP BY original_source, source_type
    ORDER BY no_url DESC
""", (today,)).fetchall()

print(f"{'平台':<30} {'无链接':<8} {'总数':<8} {'比例'}")
print("-" * 55)
for o, st, no, tot in rows:
    label = o or st or '?'
    print(f"{label:<30} {no:<8} {tot:<8} {no/tot*100:.0f}%")
