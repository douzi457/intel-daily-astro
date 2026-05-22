from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute("""
    SELECT id, title, description, original_source
    FROM items
    WHERE original_source IN ('github', 'hackernews', 'producthunt')
    LIMIT 10
""")
rows = c.fetchall()
c.close()
conn.close()
print(f"HackerNews/GitHub/ProductHunt 总数: {len(rows)}")
for r in rows:
    desc_preview = (r[2] or 'NULL')[:50]
    print(f"  id={r[0]}, {r[3]}, desc={desc_preview}")
