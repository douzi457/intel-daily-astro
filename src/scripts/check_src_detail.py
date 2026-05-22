import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute("""
    SELECT original_source, COUNT(*) as cnt
    FROM items
    WHERE DATE(created_at) = DATE('now')
    GROUP BY original_source
    ORDER BY cnt DESC
""")
rows = c.fetchall()
print("今日各源数据量：")
total = 0
for r in rows:
    print(f"  {r[0]:30s} {r[1]}条")
    total += r[1]
print(f"  总计: {total}条")
conn.close()
