from db.db import get_conn
conn = get_conn()
c = conn.cursor()

# 检查有描述的条目的评分情况
c.execute("""
    SELECT id, title, description, score, date_key
    FROM items
    WHERE description IS NOT NULL AND description != ''
    LIMIT 10
""")
rows = c.fetchall()
print(f"有描述的条目数：{len(rows)}")
for r in rows:
    print(f"  id={r[0]}, score={r[3]}, date={r[4]}, desc={r[2][:50]}")

conn.close()
