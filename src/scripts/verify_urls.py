import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()
today = '2026-05-20'

rows = c.execute(f"""
    SELECT original_source, source_type,
           SUM(CASE WHEN url IS NULL OR url = '' THEN 1 ELSE 0 END) as no_url,
           COUNT(*) as total
    FROM items
    WHERE DATE(created_at) = ?
    GROUP BY original_source, source_type
    ORDER BY no_url DESC
""", (today,)).fetchall()

print(f"平台{' '*20} 无链接 总数  比例")
print("-" * 50)
for o, st, no, tot in rows:
    label = (o or st or '?')[:22]
    print(f"{label:<22} {no:>4}  {tot:>4}  {no/tot*100:.0f}%")
