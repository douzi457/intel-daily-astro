from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute("""
    SELECT original_source,
           COUNT(*) as total,
           SUM(CASE WHEN description IS NOT NULL AND description != '' THEN 1 ELSE 0 END) as has_desc
    FROM items
    GROUP BY original_source
    ORDER BY total DESC
""")
rows = c.fetchall()
print(f"{'来源':<30} {'总数':>6} {'已翻译':>8} {'待翻':>6}")
print("-" * 55)
for r in rows:
    pending = r[1] - r[2]
    print(f"{r[0]:<30} {r[1]:>6} {r[2]:>8} {pending:>6}")
conn.close()
