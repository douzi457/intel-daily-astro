from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute("""
    SELECT id, title, url, source_type, original_source
    FROM items
    WHERE (description IS NULL OR description = '')
      AND source_type IN ('hackernews', 'github', 'producthunt')
    ORDER BY source_type, id
""")
rows = c.fetchall()
c.close()
conn.close()

items = [{'id': r[0], 'title': r[1], 'url': r[2], 'source': r[3], 'sub': r[4]} for r in rows]
print(f"共 {len(items)} 条待翻译")
for it in items[:3]:
    print(f"id={it['id']}, source={it['source']}, title={it['title'][:80]}")
